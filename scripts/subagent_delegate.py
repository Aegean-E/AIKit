"""
Sub-agent delegation: run one OpenCode sub-agent on a bounded brief (ADR-126, ADR-128).

The sub-agent runs as a supervised process with stdin closed and a timeout (PRINCIPLE-011 R5,
PRINCIPLE-015 R2). Its permissions in `.opencode/agents/<role>.md` already deny writing any task
ledger; the ledger check here detects a ledger that changed during the run and reports it, and
never writes the ledger back: another session may have checkpointed during the run, and
overwriting the file would erase that work (PRINCIPLE-006 R6, PRINCIPLE-013).
"""

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from scripts.disruption_recovery import ROOT_DIR, workspace_ledger_path
from scripts.project_registry import ProjectError, find_project

AGENTS_DIR = ROOT_DIR / ".opencode" / "agents"


def subagent_roles(agents_dir: Path = AGENTS_DIR) -> Tuple[str, ...]:
    """The roles OpenCode can run: one per profile in `.opencode/agents/` (the single source)."""
    return tuple(sorted(p.stem for p in agents_dir.glob("*.md")))


def _triad(what: str, why: str, fix: str) -> str:
    return f"Error: {what}\nWhy: {why}\nFix: {fix}"


def opencode_command(runner_bin: str, role: str, prompt: str, file: Optional[str],
                     model: Optional[str]) -> List[str]:
    """The `opencode run` argv for one headless sub-agent call."""
    cmd = [runner_bin, "run", "--standalone", "--format", "json", "--agent", role]
    if file:
        cmd += ["--file", str(file)]
    if model:
        cmd += ["--model", str(model)]
    return cmd + [prompt]


def _run_supervised(cmd: List[str], cwd: Path, timeout: int) -> subprocess.CompletedProcess:
    from scripts.dogfood import supervised  # lazy: `aikit --help` stays inside its budget
    with supervised(cmd, cwd) as proc:
        stdout, stderr = proc.communicate(timeout=timeout)
    return subprocess.CompletedProcess(cmd, proc.returncode, stdout or "", stderr or "")


def delegate_subagent(
    role: str,
    prompt: str,
    file: Optional[str] = None,
    project_name: Optional[str] = None,
    model: Optional[str] = None,
    timeout: int = 120,
    output_format: str = "text",
    runner: Optional[Callable[..., subprocess.CompletedProcess]] = None,
    workspace: Path = ROOT_DIR,
) -> Tuple[int, str]:
    """
    Run `role` on `prompt` in AIKit or in project `project_name`; returns (exit code, report).
    `runner(cmd, cwd=, timeout=)` defaults to a supervised OpenCode process (PRINCIPLE-009 R4).
    """
    roles = subagent_roles()
    if role not in roles:
        return 2, _triad(f"unknown subagent role '{role}'.",
                         f"roles are the profiles in .opencode/agents/: {', '.join(roles)}.",
                         'name one of them, e.g. `python aikit.py delegate worker "..."`.')
    if not prompt.strip():
        return 2, _triad("empty prompt provided.",
                         "a sub-agent needs a bounded brief (PRINCIPLE-008 R6).",
                         "pass the task as a non-empty quoted prompt.")
    target = workspace
    if project_name:
        try:
            target = find_project(project_name, workspace).path
        except ProjectError as exc:
            return exc.exit_code, _triad(str(exc), exc.why, exc.fix)
    if file and not (Path(file) if Path(file).is_absolute() else target / file).exists():
        return 2, _triad(f"target file '{file}' does not exist.",
                         "the sub-agent cannot inspect a file that is not there.",
                         "check the path (relative to the project), or omit --file.")

    runner_bin = "opencode"
    if runner is None:
        found = shutil.which("opencode")
        if not found:
            return 1, _triad("the `opencode` CLI was not found on PATH.",
                             "delegation runs OpenCode sub-agents (PRINCIPLE-009 R6).",
                             "install OpenCode and make `opencode` callable, then retry.")
        runner_bin, runner = found, _run_supervised

    ledgers = {workspace_ledger_path(workspace), workspace_ledger_path(target)}
    before = {path: path.read_bytes() if path.is_file() else None for path in ledgers}
    started = time.perf_counter()
    try:
        proc = runner(opencode_command(runner_bin, role, prompt, file, model), cwd=target, timeout=timeout)
    except subprocess.TimeoutExpired:
        return 1, _triad(f"subagent timed out after {timeout}s; its process tree was killed.",
                         "an unbounded run holds the session (PRINCIPLE-010 R3).",
                         "narrow the brief (PRINCIPLE-008 R1) or raise --timeout.")
    except OSError as exc:
        return 1, _triad(f"the subagent process could not start: {exc}",
                         "the OpenCode binary failed to launch.",
                         "run `opencode --version` to check the installation.")
    seconds = time.perf_counter() - started

    changed = [path for path, data in before.items()
               if (path.read_bytes() if path.is_file() else None) != data]
    if changed:
        return 1, _triad(f"a task ledger changed during the subagent run: {', '.join(map(str, changed))}",
                         "sub-agents must never write a ledger (PRINCIPLE-008 R6); a parallel session "
                         "may also have checkpointed, so AIKit does not overwrite it.",
                         "compare the file with `git diff`, keep the session's own entries, and remove "
                         "any the sub-agent wrote.")

    if output_format == "json":
        return proc.returncode, json.dumps({
            "status": "success" if proc.returncode == 0 else "error",
            "agent": role,
            "exit_code": proc.returncode,
            "duration_seconds": round(seconds, 3),
            "output": proc.stdout.strip(),
            "ledger_shield": "unmutated",
        }, indent=2)
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or f"exit code {proc.returncode}"
        return proc.returncode, f"[SUBAGENT ERROR ({role}, {seconds:.1f}s)]\n{detail}"
    return 0, f"[SUBAGENT OK ({role}, {seconds:.1f}s)]\n{proc.stdout.strip()}"
