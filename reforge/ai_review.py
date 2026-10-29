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
from reforge.git_history import changed_files, file_at, parent_sha, run_git
from reforge.model import Finding, StagePlan
from reforge.textdetect import is_text

DEFAULT_AI_MODEL = "opencode/deepseek-v4.1-flash-free"
AI_AGENT_ROLE = "architect"
# The sub-agent profiles live in AIKit's `.opencode/agents/`. The review therefore runs from the
# AIKit checkout and receives the audited diff in its brief, instead of running inside a foreign
# repository that has no agent configuration.
AIKIT_ROOT = Path(__file__).resolve().parent.parent
AI_TIMEOUT_SECONDS = 300
MAX_FILES = 12
MAX_FILE_CHARS = 6_000
MAX_BRIEF_CHARS = 14_000
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
Every path must be one of the changed files below. Respond with JSON only.
"""


def _changed_paths(repo: Path, plan: StagePlan,
                   reviewed: Optional[List[str]] = None) -> List[Tuple[str, str]]:
    """(commit, path) for every readable text file the stage's new commits changed."""
    pairs: List[Tuple[str, str]] = []
    seen = set()
    for sha in reversed(plan.new_shas):
        for status, path in changed_files(repo, sha):
            if status == "D" or is_bookkeeping(path) or path in seen:
                continue
            source = file_at(repo, sha, path)
            if source is None or not is_text(source):
                continue
            seen.add(path)
            pairs.append((sha, path))
    if reviewed is not None:
        reviewed.extend(path for _, path in pairs)
    return pairs


def _file_diff(repo: Path, sha: str, path: str) -> str:
    parent = parent_sha(repo, sha)
    if parent:
        code, out = run_git(repo, "diff", "--unified=3", parent, sha, "--", path)
    else:
        code, out = run_git(repo, "show", "--format=", "--unified=3", sha, "--", path)
    return out if code == 0 else ""


def build_brief(repo: Path, plan: StagePlan,
                reviewed: Optional[List[str]] = None) -> Tuple[str, bool]:
    """A bounded prompt holding the stage diff; `truncated` says a file or the total was cut."""
    blocks: List[str] = []
    total = 0
    truncated = False
    for sha, path in _changed_paths(repo, plan, reviewed)[:MAX_FILES]:
        diff = _file_diff(repo, sha, path)
        if not diff.strip():
            continue
        budget = min(MAX_FILE_CHARS, MAX_BRIEF_CHARS - total)
        if budget <= 200:
            truncated = True
            break
        if len(diff) > budget:
            diff = diff[:budget] + "\n[truncated]\n"
            truncated = True
        block = f"--- {path} (commit {sha[:12]}) ---\n{diff}"
        blocks.append(block)
        total += len(block)
    files = ", ".join(path for _, path in _changed_paths(repo, plan))
    brief = (PROMPT_PREFIX
             + f"\nAudited repository: {repo}\nChanged files: {files or 'none'}\n\n"
             + "\n".join(blocks))
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


def _patch_problem(repo: Path, relative: str, old: str, new: str) -> str:
    """Why a proposed replacement cannot be applied, or an empty string when it can."""
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
    if relative.lower().endswith(".py"):
        try:
            ast.parse(text.replace(old, new, 1), filename=relative)
        except SyntaxError as exc:
            return f"the replacement does not parse: {exc.msg}"
    return ""


def findings_from_payload(repo: Path, payload: object, allowed: Sequence[str],
                          commit_of: Dict[str, str]) -> Tuple[List[Finding], List[str]]:
    """Validate the model's answer against the stage; returns (findings, rejected reasons)."""
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
            length = len((Path(repo) / relative).read_text(encoding="utf-8").splitlines())
        except (OSError, UnicodeDecodeError):
            rejected.append(f"{relative}: the file cannot be read")
            continue
        if not 1 <= line <= max(length, 1):
            rejected.append(f"{relative}:{line}: line is outside the file")
            continue
        message = " ".join(str(raw.get("message", "")).split())[:MAX_MESSAGE_CHARS]
        if not message:
            rejected.append(f"{relative}:{line}: no message")
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
            problem = _patch_problem(repo, relative, old, new)
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
    reviewed: List[str] = []
    brief, truncated = build_brief(repo, plan, reviewed)
    result: Dict[str, object] = {
        "status": "skipped",
        "model": model or DEFAULT_AI_MODEL,
        "agent": AI_AGENT_ROLE,
        "findings": [],
        "rejected": [],
        "files": reviewed,
        "truncated": truncated,
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
    findings, rejected = findings_from_payload(repo, payload, reviewed, commit_of)
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
