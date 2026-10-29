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
from typing import Dict, List, Optional, Sequence, Tuple

from reforge.audit import is_bookkeeping
from reforge.git_history import (
    added_lines_range,
    changed_files,
    changed_files_range,
    commit_info,
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
HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

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
  "kind": "defect|improvement", "commit": "commit sha", "hunk": "hunk id",
  "code": "short-kebab-case", "message": "what is wrong or missing, and why it matters",
  "evidence": "the exact changed line or a short quote",
  "fix": {"old": "exact text that appears once in the file", "new": "replacement text"}}],
 "reviewed_hunks": ["hunk id", "..."]}

`reviewed_hunks` is optional; when supplied it records which packet hunks were actually read.
`commit` and `hunk` are optional; when present they must name a commit and hunk shown in this
packet. They keep a finding attributed to the change that introduced it. `fix` is optional. Include it only when the replacement is exact, minimal and safe. Use the file's
real line endings and whitespace in `old`. An empty findings list is a valid answer.

Read the unified diff as it is: a line starting with `+` exists after the commit, a line starting
with `-` was removed by it and is NOT in the file, and a leading space marks unchanged context.
Every `evidence` must quote a line that exists in the file after the change, verbatim. Never report
a removed line as a current problem.

The packet lists every new commit oldest to newest, with that commit's own hunks. A later commit
may correct or replace an earlier hunk, so judge the current file: every `evidence` must quote a
line that still exists, verbatim, and a suggested replacement must land on a line one of these
commits added. A binary file is named at the end because it cannot be reviewed as text.
"""


def _stage_base(repo: Path, plan: StagePlan) -> str:
    """The commit just before the stage, so one diff shows the whole stage as it now stands."""
    if not plan.new_shas:
        return ""
    return parent_sha(repo, plan.new_shas[-1])


def _new_paths(repo: Path, plan: StagePlan) -> set:
    """Paths at least one new commit touched; files only an earlier stage changed stay out."""
    paths: set = set()
    for sha in plan.new_shas:
        for status, path in changed_files(repo, sha):
            if status != "D":
                paths.add(path)
    return paths


def _new_added_lines(repo: Path, plan: StagePlan, path: str) -> set:
    """Lines the stage's new commits add to a path, ignoring an earlier stage's lines."""
    lines: set = set()
    for sha in plan.new_shas:
        lines |= added_lines_range(repo, parent_sha(repo, sha), sha, path)
    return lines


def _changed_paths(repo: Path, plan: StagePlan) -> List[Tuple[str, str]]:
    """(head, path) for every readable text file the new commits changed, once each."""
    if not plan.new_shas:
        return []
    head = plan.new_shas[0]
    base = _stage_base(repo, plan)
    new_paths = _new_paths(repo, plan)
    pairs: List[Tuple[str, str]] = []
    for status, path in changed_files_range(repo, base, head):
        if status == "D" or is_bookkeeping(path) or path not in new_paths:
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
    new_paths = _new_paths(repo, plan)
    binary: List[str] = []
    for status, path in changed_files_range(repo, base, head):
        if status == "D" or is_bookkeeping(path) or path not in new_paths:
            continue
        source = file_at(repo, head, path)
        if source is not None and not is_text(source):
            binary.append(path)
    return binary


def _commit_diff(repo: Path, sha: str, path: str) -> str:
    """One commit's hunks for a path, against its first parent (root commits included)."""
    return range_diff(repo, parent_sha(repo, sha), sha, path)


def _split_hunks(diff: str, sha: str, path: str) -> List[Dict[str, object]]:
    """Split one commit's file diff into stable hunk records for the packet and attribution."""
    lines = diff.splitlines(keepends=True)
    starts = [index for index, line in enumerate(lines) if line.startswith("@@ ")]
    hunks: List[Dict[str, object]] = []
    for number, start in enumerate(starts, 1):
        end = starts[number] if number < len(starts) else len(lines)
        match = HUNK_RE.match(lines[start])
        new_start = int(match.group(1)) if match else 0
        if match and match.group(2) is not None:
            new_count = int(match.group(2))
        else:
            new_count = 1 if match else 0
        hunks.append({
            "id": f"{sha[:12]}:{path}#{number}",
            "commit": sha,
            "path": path,
            "start": new_start,
            "count": new_count,
            "text": "".join(lines[start:end]),
        })
    return hunks


def _stage_hunks(repo: Path, plan: StagePlan,
                 scrub: bool = True) -> Tuple[List[Dict[str, object]], int]:
    """Every hunk in every new commit, oldest first, with stable IDs and optional redaction."""
    if not plan.new_shas:
        return [], 0
    current = {path for _, path in _changed_paths(repo, plan)}
    hunks: List[Dict[str, object]] = []
    redactions = 0
    for sha in reversed(plan.new_shas):
        for status, path in changed_files(repo, sha):
            if status == "D" or is_bookkeeping(path) or path not in current:
                continue
            diff = _commit_diff(repo, sha, path)
            if not diff.strip():
                continue
            if scrub:
                diff, masked = _scrub(diff)
                redactions += masked
            hunks.extend(_split_hunks(diff, sha, path))
    return hunks, redactions


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
    """The full hunk-by-hunk review packet for one stage, and credential spans masked."""
    hunks, redactions = _stage_hunks(repo, plan)
    by_sha = {commit.sha: commit for commit in plan.commits}
    ordered: List[str] = []
    by_commit: Dict[str, List[Dict[str, object]]] = {}
    current: List[str] = []
    for hunk in hunks:
        sha = str(hunk["commit"])
        if sha not in by_commit:
            ordered.append(sha)
            by_commit[sha] = []
        by_commit[sha].append(hunk)
        if hunk["path"] not in current:
            current.append(str(hunk["path"]))
    if files is not None:
        files.extend(path for path in current if path not in files)
    manifest: List[str] = ["### Hunk manifest"]
    blocks: List[str] = []
    for sha in ordered:
        info = by_sha.get(sha) or commit_info(repo, sha)
        subject = info.subject if info else ""
        group = by_commit[sha]
        manifest.append(f"- {sha[:12]} {subject}: {len(group)} hunk(s)")
        lines = [f"### commit {sha[:12]} {subject}".rstrip()]
        last_path = ""
        for hunk in group:
            path = str(hunk["path"])
            if path != last_path:
                lines.append(f"--- {path} ---")
                last_path = path
            end = int(hunk["start"]) + max(int(hunk["count"]) - 1, 0)
            span = (f"new lines {hunk['start']}..{end}" if int(hunk["count"])
                    else f"deletes after line {hunk['start']}")
            lines.append(f"hunk {hunk['id']} ({span})")
            lines.append(str(hunk["text"]).rstrip("\n"))
        blocks.append("\n".join(lines))
    head = plan.new_shas[0] if plan.new_shas else ""
    base = _stage_base(repo, plan) or "(root commit)"
    binary = _binary_paths(repo, plan)
    tail = (f"\nBinary files (not reviewed as text): {', '.join(binary)}" if binary else "")
    packet = (PROMPT_PREFIX
              + f"\nStage {plan.stage} (window {plan.window}), commits {base}..{head[:12]}\n"
              + f"Changed text files: {', '.join(files or []) or 'none'}\n"
              + "\n".join(manifest) + "\n\n"
              + "\n\n".join(blocks) + tail)
    return packet, redactions


def packet_path(root: Path, plan: StagePlan) -> Path:
    """Where the packet for this stage is written, inside the git-ignored state folder."""
    head = plan.new_shas[0][:12] if plan.new_shas else "empty"
    run = plan.run_id or "run"
    return Path(root) / PACKET_DIR / f"stage-{run}-{plan.stage}-{head}.md"


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


def coverage_for_payload(repo: Path, plan: StagePlan, payload: object) -> Dict[str, object]:
    """Compare a reviewer's `reviewed_hunks` list with the packet's hunk IDs, when supplied."""
    if not isinstance(payload, dict):
        return {}
    reported = payload.get("reviewed_hunks")
    if not isinstance(reported, list):
        return {}
    hunks = _stage_hunks(repo, plan, scrub=False)[0]
    known = {str(hunk["id"]) for hunk in hunks}
    seen = {str(item) for item in reported}
    return {
        "reported": len(seen & known),
        "total": len(known),
        "missing": sorted(known - seen),
        "unknown": sorted(seen - known),
    }


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
    touched = {path: _new_added_lines(repo, plan, path) for path in allowed}
    needs_hunks = any(isinstance(raw, dict) and (raw.get("hunk") or raw.get("commit"))
                      for raw in items)
    hunks = _stage_hunks(repo, plan, scrub=False)[0] if needs_hunks else []
    hunk_by_id = {str(hunk["id"]): hunk for hunk in hunks}
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
        commit = str(raw.get("commit", "")).strip()
        hunk_id = str(raw.get("hunk", "")).strip()
        if hunk_id:
            hunk = hunk_by_id.get(hunk_id)
            if hunk is None:
                rejected.append(f"{relative}: hunk {hunk_id!r} is not in this packet")
                continue
            if hunk["path"] != relative:
                rejected.append(f"{relative}: hunk {hunk_id!r} belongs to {hunk['path']}")
                continue
            if commit:
                matches = [sha for sha in plan.new_shas if sha.startswith(commit)]
                if len(matches) != 1 or matches[0] != hunk["commit"]:
                    rejected.append(f"{relative}: hunk {hunk_id!r} is in another commit")
                    continue
            commit = str(hunk["commit"])
        elif commit:
            matches = [sha for sha in plan.new_shas if sha.startswith(commit)]
            if len(matches) != 1:
                rejected.append(f"{relative}: {commit!r} is not one new commit")
                continue
            commit = matches[0]
            if not any(hunk["commit"] == commit and hunk["path"] == relative
                       for hunk in hunks):
                rejected.append(f"{relative}: commit {commit[:12]} did not change this file")
                continue
        else:
            commit = commit_of.get(relative, "")
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
            commit=commit,
            hunk=hunk_id,
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
