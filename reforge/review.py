"""The review packet: the change a stage makes, and the findings a reviewer returns.

Reforge plans the work and keeps the record; the reviewing is done by the operator, or by the agent
driving the session, reading the packet. Nothing here spawns a model, so there is no key, quota or
command-line limit: the packet is a file, and the findings are a file.

The answer is untrusted input. A finding's path must be one the stage changed, its line must exist,
its quoted evidence must be in the file, and a replacement must occur exactly once, overlap a line
the stage added, and leave a Python file parsable. `reforge.repair` applies only what survives that,
inside the normal snapshot, test, gate and diff-review transaction.
"""

from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

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

# The `reforge.` prefix makes the packet one of Reforge's own artifacts: the clean-tree check and
# delivery ignore it, so a review can never be committed by mistake.
PACKET_DIR = Path(".aikit") / "reforge.reviews"
MAX_FINDINGS = 200
MAX_MESSAGE_CHARS = 400
MAX_PATCH_CHARS = 4_000
SEVERITIES = ("low", "medium", "high")
CODE_RE = re.compile(r"^[a-z][a-z0-9-]{2,39}$")
FENCE_RE = re.compile(r"^```[a-zA-Z0-9_-]*\s*$")

PROMPT_PREFIX = """Review one Git audit stage. Report two kinds of item, both tied to the change.

kind "defect": something the change introduces or leaves in a worse state. A bug, a wrong condition,
a missing guard, a swallowed error, a documented promise the code does not keep.

kind "improvement": a concrete gap or better implementation in the code the change touches. A case
the new code does not handle, a missing test for a new branch, a simpler correct approach, an API
that forces callers to repeat work. Improvements must be specific and actionable, with a line you
can point at. Never report pure style or naming taste.

Do not invent files or lines. Do not propose work unrelated to the diff.

Return one JSON object:
{"findings": [{"path": "relative/path", "line": 12, "severity": "high|medium|low",
  "kind": "defect|improvement",
  "code": "short-kebab-case", "message": "what is wrong or missing, and why it matters",
  "evidence": "the exact changed line or a short quote",
  "fix": {"old": "exact text that appears once in the file", "new": "replacement text"}}]}

`fix` is optional. Include it only when the replacement is exact, minimal and safe. Use the file's
real line endings and whitespace in `old`. An empty findings list is a valid answer.

Read the unified diff as it is: a line starting with `+` exists after the commit, a line starting
with `-` was removed by it and is NOT in the file, and a leading space marks unchanged context.
Every `evidence` must quote a line that exists in the file after the change, verbatim. Never report
a removed line as a current problem.

The diff is the stage's net change: from the commit before the stage to its last commit, each file
once. Every changed text file is included. A binary file is named at the end because it cannot be
reviewed as text.
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


def _binary_paths(repo: Path, plan: StagePlan) -> List[str]:
    """Changed paths that cannot be reviewed as text, named so the packet is honest about them."""
    if not plan.new_shas:
        return []
    head = plan.new_shas[0]
    base = _stage_base(repo, plan)
    binary: List[str] = []
    for status, path in changed_files_range(repo, base, head):
        if status == "D" or is_bookkeeping(path):
            continue
        source = file_at(repo, head, path)
        if source is not None and not is_text(source):
            binary.append(path)
    return binary


def _file_diff(repo: Path, plan: StagePlan, path: str) -> str:
    """The path's net diff across the whole stage."""
    if not plan.new_shas:
        return ""
    return range_diff(repo, _stage_base(repo, plan), plan.new_shas[0], path)


def _scrub(text: str) -> Tuple[str, int]:
    """The diff with credential-shaped spans redacted, and how many detectors fired.

    The packet is a local file, but it is meant to be read, quoted and handed to an agent, so a
    credential that was committed is masked here instead of being copied into the review. A missing
    scanner is not fatal: the packet never leaves the machine, and the findings file is the only
    thing the reviewer returns.
    """
    try:
        from scripts.check_secrets import scrub_text
    except ImportError:
        return text, 0
    scrubbed, detectors = scrub_text(text)
    return scrubbed, len(detectors)


def packet_text(repo: Path, plan: StagePlan,
                files: Optional[List[str]] = None) -> Tuple[str, int]:
    """The full review packet for one stage, and how many credential spans were masked."""
    pairs = _changed_paths(repo, plan)
    blocks: List[str] = []
    redactions = 0
    for _, path in pairs:
        diff = _file_diff(repo, plan, path)
        if diff.strip():
            diff, masked = _scrub(diff)
            redactions += masked
            blocks.append(f"--- {path} ---\n{diff}")
        else:
            blocks.append(f"--- {path} ---\n(no text diff; the file was rewritten or renamed)")
        if files is not None:
            files.append(path)
    head = plan.new_shas[0] if plan.new_shas else ""
    base = _stage_base(repo, plan) or "(root commit)"
    binary = _binary_paths(repo, plan)
    tail = (f"\nBinary files (not reviewed as text): {', '.join(binary)}" if binary else "")
    packet = (PROMPT_PREFIX
              + f"\nStage {plan.stage} (window {plan.window}), commits {base}..{head[:12]}\n"
              + f"Changed text files: {', '.join(files or []) or 'none'}\n\n"
              + "\n".join(blocks) + tail)
    return packet, redactions


def packet_path(root: Path, plan: StagePlan) -> Path:
    """Where the packet for this stage is written, inside the git-ignored state folder."""
    head = plan.new_shas[0][:12] if plan.new_shas else "empty"
    return Path(root) / PACKET_DIR / f"stage-{plan.stage}-{head}.md"


def _write_text(path: Path, text: str) -> None:
    """Write a generated packet through a temp file and an atomic replace."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp_{os.getpid()}_{int(time.time() * 1000)}")
    try:
        with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if tmp.exists():
            try:
                tmp.unlink()
            except OSError:  # hygiene: allow cleanup is best-effort after a completed write
                pass


def write_packet(root: Path, plan: StagePlan,
                 files: Optional[List[str]] = None) -> Tuple[Path, int]:
    """Write the packet and return (path, redacted span count)."""
    packet, redactions = packet_text(Path(root), plan, files)
    path = packet_path(root, plan)
    _write_text(path, packet)
    return path, redactions


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


def read_findings_file(path: Path) -> object:
    """Read a findings file, raising ValueError with a clear message when it holds no JSON."""
    text = Path(path).read_text(encoding="utf-8")
    payload = _json_payload(text)
    if payload is None:
        raise ValueError(f"{path} holds no JSON object or array")
    return payload


def _patch_problem(repo: Path, relative: str, old: str, new: str,
                   touched: Optional[set] = None) -> str:
    """Why a proposed replacement cannot be applied, or an empty string when it can.

    `touched` is the set of line numbers the stage added to this path. When it is given, the quoted
    text must overlap one of them: validating the path alone would let a review steer an edit into
    any uniquely quotable line of a staged file.
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
            import ast

            ast.parse(text.replace(old, new, 1), filename=relative)
        except SyntaxError as exc:
            return f"the replacement does not parse: {exc.msg}"
    return ""


def _line_set(text: str) -> set:
    """Every non-blank line of a file, stripped, for verifying a quoted evidence line."""
    return {line.strip() for line in text.splitlines() if line.strip()}


def findings_from_payload(repo: Path, payload: object, plan: StagePlan,
                          files: Optional[Sequence[str]] = None
                          ) -> Tuple[List[Finding], List[str]]:
    """Validate a findings answer against the stage; returns (findings, rejected reasons)."""
    repo = Path(repo)
    items = payload.get("findings") if isinstance(payload, dict) else payload
    if not isinstance(items, list):
        return [], ["the answer has no findings list"]
    changed = _changed_paths(repo, plan)
    allowed = set(files if files is not None else [path for _, path in changed])
    commit_of = {path: sha for sha, path in changed}
    base, head = _stage_base(repo, plan), (plan.new_shas[0] if plan.new_shas else "")
    touched = {path: added_lines_range(repo, base, head, path) for path in allowed}
    findings: List[Finding] = []
    rejected: List[str] = []
    for raw in items[:MAX_FINDINGS]:
        if not isinstance(raw, dict):
            rejected.append("an entry is not an object")
            continue
        relative = str(raw.get("path", "")).replace("\\", "/")
        if relative not in allowed:
            rejected.append(f"{relative or '(no path)'}: not a file this stage changed")
            continue
        try:
            line = int(raw.get("line", 0))
            text = (repo / relative).read_text(encoding="utf-8")
        except (TypeError, ValueError):
            rejected.append(f"{relative}: line is not a number")
            continue
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
            rejected.append(f"{relative}:{line}: the evidence is not in the current file "
                            "(it may quote a removed line)")
            continue
        severity = str(raw.get("severity", "medium")).lower()
        if severity not in SEVERITIES:
            severity = "medium"
        kind = "improvement" if str(raw.get("kind", "")).lower() == "improvement" else "defect"
        code = re.sub(r"[^a-z0-9-]", "-", str(raw.get("code", "")).lower()).strip("-")
        if not code:
            code = "review"
        if not code.startswith("review-"):
            code = f"review-{code}"
        if not CODE_RE.match(code):
            code = "review"
        old = new = ""
        fixable = False
        fix = raw.get("fix")
        if isinstance(fix, dict):
            old = str(fix.get("old", ""))
            new = str(fix.get("new", ""))
            problem = _patch_problem(repo, relative, old, new, touched.get(relative, set()))
            if problem:
                rejected.append(f"{relative}:{line}: suggestion dropped ({problem})")
                old = new = ""
            else:
                fixable = True
        findings.append(Finding(
            code=code,
            category="improvement" if kind == "improvement" else "review",
            severity=severity,
            path=relative,
            line=line,
            message=message,
            evidence=" ".join(raw_evidence.split())[:MAX_MESSAGE_CHARS]
                     or f"{relative}:{line}: (review)",
            commit=commit_of.get(relative, ""),
            symbol="",
            reproducible=False,
            fixable=fixable,
            source="review",
            patch_old=old,
            patch_new=new,
        ))
    return findings, rejected


def merge_findings(proven: Sequence[Finding], reviewed: Sequence[Finding]) -> List[Finding]:
    """Rule findings first, then review findings the rules did not already name."""
    merged: List[Finding] = list(proven)
    seen = {(item.path, item.line, item.code) for item in proven}
    for item in reviewed:
        if (item.path, item.line, item.code) in seen:
            continue
        merged.append(item)
        seen.add((item.path, item.line, item.code))
    return merged
