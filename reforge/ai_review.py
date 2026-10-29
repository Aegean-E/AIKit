"""AI review of the changes one audit stage introduces, then validated fixes.

Reforge's detectors prove what a grammar or a diff can prove. This module adds the second pair of
eyes the workflow actually needs: a read-only AI sub-agent reads the stage's diff and reports what
a reviewer would (a wrong condition, a missing guard, a doc claim that no longer matches the code),
and may propose an exact text replacement for a finding it is sure about.

The model's answer is untrusted input. Every path must be one the stage changed, every line must
exist, every replacement must occur exactly once, and a Python replacement must parse; anything
else is dropped with a recorded reason. The fix is applied by `reforge.repair`, then the normal
tests, gates and patch review decide whether it survives. The sub-agent is read-only: it never
edits, commits or writes a ledger.

The call is optional. Without the `opencode` CLI or a reachable free model the stage is still
audited by the deterministic detectors, and the result says the AI review was skipped and why.
"""

from __future__ import annotations

import ast
import json
import re
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from reforge.audit import is_bookkeeping
from reforge.git_history import (
    added_lines_range,
    changed_files_range,
    file_at,
    parent_sha,
    range_diff,
)
from reforge.model import Finding, StagePlan
from reforge.textdetect import is_text

DEFAULT_AI_MODEL = "opencode/deepseek-v4.1-flash-free"
AI_AGENT_ROLE = "architect"
# The sub-agent profiles live in AIKit's `.opencode/agents/`. The review therefore runs from the
# AIKit checkout and receives the audited diff in its brief, instead of running inside a foreign
# repository that has no agent configuration.
AIKIT_ROOT = Path(__file__).resolve().parent.parent
AI_TIMEOUT_SECONDS = 300
MAX_FILES = 10
MAX_FILE_CHARS = 8_000
MAX_BRIEF_CHARS = 24_000
MAX_FINDINGS = 25
MAX_MESSAGE_CHARS = 400
MAX_PATCH_CHARS = 4_000
SEVERITIES = ("low", "medium", "high")
CODE_RE = re.compile(r"^[a-z][a-z0-9-]{2,39}$")
FENCE_RE = re.compile(r"^```[a-zA-Z0-9_-]*\s*$")
AiRunner = Callable[[str, Optional[str]], Tuple[int, str]]

PROMPT_PREFIX = """You review one Git audit stage for a repository. Report only problems that
the change under review introduces or leaves in a worse state. Do not restate style preferences,
do not propose unrelated refactors, and do not invent files or lines.

The diff below is the complete input. Do not read or search other files; the stage's text is all
you have. Paths are relative to the audited repository.

Return one JSON object and nothing else:
{"findings": [{"path": "relative/path", "line": 12, "severity": "high|medium|low",
  "code": "short-kebab-case", "message": "what is wrong and why it matters",
  "evidence": "the exact changed line or a short quote",
  "fix": {"old": "exact text that appears once in the file", "new": "replacement text"}}]}

`fix` is optional. Include it only when the replacement is exact, minimal and safe. Use the file's
real line endings and whitespace in `old`. An empty findings list is a valid answer: {"findings": []}.

Read the unified diff as it is: a line starting with `+` exists after the commit, a line starting
with `-` was removed by it and is NOT in the file, and a leading space marks unchanged context.
Every `evidence` must quote a line that exists in the file after the change (a `+` line or context),
verbatim. Never report a removed line as a current problem.

The diff is the stage's net change: it compares the commit before the stage with its last commit, so
each file appears once, complete. The diff may still cover only some of the changed files, because
the brief is bounded: a file that is not shown is unknown to you. Never claim that a feature, check
or field is unimplemented, missing or unchanged outside the lines you were given. If the only way to
judge a claim is to read code you were not given, do not report it.

Every path must be one of the changed files below. Respond with JSON only.
"""


def _stage_base(repo: Path, plan: StagePlan) -> str:
    """The commit just before the stage, so one diff shows the whole stage as it now stands."""
    if not plan.new_shas:
        return ""
    return parent_sha(repo, plan.new_shas[-1])


def _changed_paths(repo: Path, plan: StagePlan) -> List[Tuple[str, str]]:
    """(head, path) for every readable text file the stage changed, once each, from the net diff."""
    if not plan.new_shas:
        return []
    head = plan.new_shas[0]
    base = _stage_base(repo, plan)
    pairs: List[Tuple[str, str]] = []
    for status, path in changed_files_range(repo, base, head):
        if status == "D" or is_bookkeeping(path):
            continue
        source = file_at(repo, head, path)
        if source is None or not is_text(source):
            continue
        pairs.append((head, path))
    return pairs


def _file_diff(repo: Path, plan: StagePlan, path: str) -> str:
    """The path's net diff across the whole stage."""
    if not plan.new_shas:
        return ""
    return range_diff(repo, _stage_base(repo, plan), plan.new_shas[0], path)


def scrubber_available() -> bool:
    """Whether the project's secret scanner can redact the brief.

    Redaction is a precondition, not a nicety: without the scanner the diff is not sent at all, so
    a standalone checkout degrades to "AI review skipped" instead of silently leaking history.
    """
    try:
        from scripts.check_secrets import scrub_text  # noqa: F401
    except ImportError:
        return False
    return True


def _scrub(text: str) -> Tuple[str, int]:
    """The diff with credential-shaped spans redacted, and how many detectors fired."""
    from scripts.check_secrets import scrub_text

    scrubbed, detectors = scrub_text(text)
    return scrubbed, len(detectors)


def build_brief(repo: Path, plan: StagePlan,
                reviewed: Optional[List[str]] = None,
                redacted: Optional[List[int]] = None) -> Tuple[str, bool]:
    """A bounded, redacted prompt holding the stage's net diff.

    A file is included whole or not at all, because a half-shown hunk invites a confident wrong
    finding about code the model never saw. `truncated` says some changed file was omitted,
    `reviewed` collects the files really included and `redacted` one count per detector hit.
    """
    blocks: List[str] = []
    included: List[str] = []
    total = 0
    pairs = _changed_paths(repo, plan)
    truncated = False
    for sha, path in pairs:
        if len(included) >= MAX_FILES:
            truncated = True
            break
        diff = _file_diff(repo, plan, path)
        if not diff.strip():
            continue
        diff, redactions = _scrub(diff)
        if redactions and redacted is not None:
            redacted.append(redactions)
        if len(diff) > MAX_FILE_CHARS:
            truncated = True
            continue
        if total + len(diff) > MAX_BRIEF_CHARS:
            truncated = True
            break
        block = f"--- {path} (stage {sha[:12]}) ---\n{diff}"
        blocks.append(block)
        included.append(path)
        total += len(block)
    if reviewed is not None:
        reviewed.extend(included)
    files = ", ".join(path for _, path in pairs) or "none"
    omitted = [path for _, path in pairs if path not in included]
    note = ("\nOmitted from the diff (unknown to you): " + ", ".join(omitted)) if omitted else ""
    brief = (PROMPT_PREFIX
             + f"\nAudited repository: {repo}\nChanged files: {files}\n\n"
             + "\n".join(blocks) + note)
    return brief, truncated


def _json_payload(text: str) -> Optional[object]:
    """The first JSON value in the answer, tolerating a code fence or a short explanation."""
    cleaned = "\n".join(line for line in text.splitlines() if not FENCE_RE.match(line.strip()))
    decoder = json.JSONDecoder()
    for index, char in enumerate(cleaned):
        if char not in "[{":
            continue
        try:
            value, _ = decoder.raw_decode(cleaned[index:])
        except ValueError:
            continue
        return value
    return None


def _patch_problem(repo: Path, relative: str, old: str, new: str,
                   touched: Optional[set] = None) -> str:
    """Why a proposed replacement cannot be applied, or an empty string when it can.

    `touched` is the set of line numbers the stage added to this path. When it is given, the
    quoted text must overlap one of them: validating the path alone would let a hostile diff
    steer an edit into any uniquely quotable line of a staged file.
    """
    if not old or old == new:
        return "the replacement is empty or unchanged"
    if len(old) > MAX_PATCH_CHARS or len(new) > MAX_PATCH_CHARS:
        return "the replacement is too large"
    if "\x00" in old or "\x00" in new:
        return "the replacement holds a NUL byte"
    path = Path(repo) / relative
    try:
        text = path.read_text(encoding="utf-8", newline="")
    except (OSError, UnicodeDecodeError) as exc:
        return f"the file cannot be read: {exc}"
    count = text.count(old)
    if count != 1:
        return f"the quoted text occurs {count} times in the file"
    if touched is not None:
        start = text.find(old)
        first = text.count("\n", 0, start) + 1
        span = range(first, first + old.count("\n") + 1)
        if not touched.intersection(span):
            return "the quoted text is outside the lines this stage added"
    if relative.lower().endswith(".py"):
        try:
            ast.parse(text.replace(old, new, 1), filename=relative)
        except SyntaxError as exc:
            return f"the replacement does not parse: {exc.msg}"
    return ""


def _line_set(text: str) -> set:
    """Every non-blank line of a file, stripped, for verifying a quoted evidence line."""
    return {line.strip() for line in text.splitlines() if line.strip()}


def findings_from_payload(repo: Path, payload: object, allowed: Sequence[str],
                          commit_of: Dict[str, str],
                          touched: Optional[Dict[str, set]] = None,
                          omitted: Sequence[str] = (),
                          ) -> Tuple[List[Finding], List[str]]:
    """Validate the model's answer against the stage; returns (findings, rejected reasons).

    `touched` maps each changed path to the line numbers the stage added; a replacement must
    overlap them, so the model's help stays inside the change under review. `omitted` names changed
    files the bounded brief did not carry: a finding that reasons about one of them is guessing, so
    it is dropped rather than shown as work.
    """
    items = payload.get("findings") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return [], ["the answer has no findings list"]
    findings: List[Finding] = []
    rejected: List[str] = []
    allowed_set = set(allowed)
    for raw in items[:MAX_FINDINGS]:
        if not isinstance(raw, dict):
            rejected.append("an entry is not an object")
            continue
        relative = str(raw.get("path", "")).replace("\\", "/")
        if relative not in allowed_set:
            rejected.append(f"{relative or '(no path)'}: not a file this stage changed")
            continue
        try:
            line = int(raw.get("line", 0))
        except (TypeError, ValueError):
            rejected.append(f"{relative}: line is not a number")
            continue
        try:
            text = (Path(repo) / relative).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            rejected.append(f"{relative}: the file cannot be read")
            continue
        if not 1 <= line <= max(len(text.splitlines()), 1):
            rejected.append(f"{relative}:{line}: line is outside the file")
            continue
        message = " ".join(str(raw.get("message", "")).split())[:MAX_MESSAGE_CHARS]
        if not message:
            rejected.append(f"{relative}:{line}: no message")
            continue
        raw_evidence = str(raw.get("evidence", "")).strip()
        if raw_evidence and raw_evidence not in _line_set(text):
            # A model reading a diff often quotes a `-` line as though it were the file. The fix
            # it describes does not exist, so the finding is dropped rather than shown as work.
            rejected.append(f"{relative}:{line}: the evidence is not in the current file "
                            "(it may quote a removed line)")
            continue
        claim = f"{message} {raw_evidence}"
        unseen = next((path for path in omitted
                       if path in claim or Path(path).name in claim), "")
        if unseen:
            rejected.append(f"{relative}:{line}: reasons about {unseen}, which the brief omitted")
            continue
        severity = str(raw.get("severity", "medium")).lower()
        if severity not in SEVERITIES:
            severity = "medium"
        code = re.sub(r"[^a-z0-9-]", "-", str(raw.get("code", "")).lower()).strip("-")
        if not code:
            code = "ai-review"
        if not code.startswith("ai-"):
            code = f"ai-{code}"
        if not CODE_RE.match(code):
            code = "ai-review"
        evidence = " ".join(str(raw.get("evidence", "")).split())[:MAX_MESSAGE_CHARS]
        old = new = ""
        fixable = False
        fix = raw.get("fix")
        if isinstance(fix, dict):
            old = str(fix.get("old", ""))
            new = str(fix.get("new", ""))
            problem = _patch_problem(repo, relative, old, new,
                                     None if touched is None else touched.get(relative, set()))
            if problem:
                rejected.append(f"{relative}:{line}: suggestion dropped ({problem})")
                old = new = ""
            else:
                fixable = True
        findings.append(Finding(
            code=code,
            category="review",
            severity=severity,
            path=relative,
            line=line,
            message=message,
            evidence=evidence or f"{relative}:{line}: (AI review)",
            commit=commit_of.get(relative, ""),
            symbol="",
            reproducible=False,
            fixable=fixable,
            source="ai",
            patch_old=old,
            patch_new=new,
        ))
    return findings, rejected


def _delegate_runner(repo: Path, timeout: int) -> AiRunner:
    """The default runner: one read-only `architect` sub-agent on a free model."""
    def run(prompt: str, model: Optional[str]) -> Tuple[int, str]:
        from scripts.subagent_delegate import answer_text, delegate_subagent

        code, report = delegate_subagent(
            AI_AGENT_ROLE, prompt, model=model or DEFAULT_AI_MODEL,
            timeout=timeout, output_format="json", workspace=AIKIT_ROOT,
        )
        try:
            envelope = json.loads(report)
        except ValueError:
            return code, report
        if envelope.get("status") != "success":
            return code or 1, str(envelope.get("output", ""))
        return code, answer_text(str(envelope.get("output", "")))
    return run


def review_stage(repo: Path, plan: StagePlan, model: Optional[str] = None,
                 timeout: int = AI_TIMEOUT_SECONDS,
                 runner: Optional[AiRunner] = None) -> Dict[str, object]:
    """Ask the AI to review this stage; never raises, and always says what happened."""
    repo = Path(repo)
    if not scrubber_available():
        return {"status": "skipped", "findings": [], "rejected": [], "files": [],
                "model": model or DEFAULT_AI_MODEL, "agent": AI_AGENT_ROLE, "truncated": False,
                "redacted": 0, "prompt_chars": 0, "seconds": 0.0,
                "reason": "the secret scanner is unavailable, so the diff is not sent unredacted"}
    reviewed: List[str] = []
    redacted: List[int] = []
    brief, truncated = build_brief(repo, plan, reviewed, redacted)
    result: Dict[str, object] = {
        "status": "skipped",
        "model": model or DEFAULT_AI_MODEL,
        "agent": AI_AGENT_ROLE,
        "findings": [],
        "rejected": [],
        "files": reviewed,
        "truncated": truncated,
        "redacted": sum(redacted),
        "prompt_chars": len(brief),
        "seconds": 0.0,
        "reason": "",
    }
    if not reviewed:
        result["reason"] = "the stage changed no text file"
        return result
    runner = runner or _delegate_runner(repo, timeout)
    started = time.perf_counter()
    try:
        code, answer = runner(brief, model)
    except Exception as exc:  # a review that cannot run must not stop the audit (PRINCIPLE-011)
        result.update(status="failed", seconds=round(time.perf_counter() - started, 2),
                      reason=f"{type(exc).__name__}: {exc}")
        return result
    result["seconds"] = round(time.perf_counter() - started, 2)
    if code != 0:
        result.update(status="failed", reason=(answer.strip()[-300:] or f"exit code {code}"))
        return result
    payload = _json_payload(answer)
    if payload is None:
        result.update(status="failed", reason="the answer held no JSON object")
        return result
    commit_of = {path: sha for sha, path in _changed_paths(repo, plan)}
    base, head = _stage_base(repo, plan), plan.new_shas[0]
    touched: Dict[str, set] = {path: added_lines_range(repo, base, head, path)
                               for path in reviewed}
    omitted = [path for _, path in _changed_paths(repo, plan) if path not in reviewed]
    findings, rejected = findings_from_payload(repo, payload, reviewed, commit_of, touched,
                                               omitted)
    result.update(status="reviewed", findings=findings, rejected=rejected)
    if not findings:
        result["reason"] = "the review found nothing it could prove"
    return result


def merge_findings(proven: Sequence[Finding], reviewed: Sequence[Finding]) -> List[Finding]:
    """Deterministic findings first, then AI findings the detectors did not already name."""
    merged: List[Finding] = list(proven)
    seen = {(item.path, item.line, item.code) for item in proven}
    for item in reviewed:
        if (item.path, item.line, item.code) in seen:
            continue
        merged.append(item)
        seen.add((item.path, item.line, item.code))
    return merged
