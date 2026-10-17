"""
`aikit` command line: create, attach, list, report on and check the projects AIKit builds
(ADR-119, ADR-120, ADR-122).

Run through the root shim: `python aikit.py <command>`. Exit codes: 0 success, 1 the request
could not be carried out, 2 the command line was wrong (PRINCIPLE-011).
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable, Dict, List, NoReturn, Optional, Tuple

from scripts.disruption_recovery import (
    ROOT_DIR,
    clean_dangling_temp_files,
    format_resume_report,
    load_ledger,
    mark_task_completed,
    record_checkpoint,
    run_disruption_audit,
)
from scripts.project_gates import failure_tail, resolve_gates, run_gates
from scripts.project_registry import (
    ProjectError,
    attach_project,
    config_path,
    create_project,
    Project,
    find_project,
    latest_decision,
    list_projects,
    write_memory,
    AGENTS_FILENAME,
    AGENTS_TEMPLATE,
    DECISIONS_FILENAME,
    PROJECT_INSTRUCTION_TARGETS,
    PROJECT_MEMORY_DIRNAME,
)
from scripts.update_knowledge_base import (
    find_python_files,
    generate_codebase_map,
    write_generated_file,
)


def report_error(error: ProjectError) -> int:
    """Print the error triad to stderr and return its exit code."""
    print(f"Error: {error}", file=sys.stderr)
    print(f"Why: {error.why}", file=sys.stderr)
    print(f"Fix: {error.fix}", file=sys.stderr)
    return error.exit_code


class TriadArgumentParser(argparse.ArgumentParser):
    """argparse whose usage errors carry Why/Fix like every other AIKit error."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        sys.exit(report_error(ProjectError(
            message,
            "the command line does not match any `aikit` command.",
            f"run `{self.prog} --help` to list the valid forms.",
            exit_code=2,
        )))


VALID_SUBAGENT_ROLES: Tuple[str, ...] = ("worker", "architect", "coder", "tester", "reviewer", "explorer")


def build_parser() -> argparse.ArgumentParser:
    parser = TriadArgumentParser(
        prog="python aikit.py",
        description="Create and manage the projects AIKit builds. Each project is its own folder "
                    "and git repository with its memory in .aikit/.",
    )
    commands = parser.add_subparsers(dest="command", required=True, parser_class=TriadArgumentParser)

    new = commands.add_parser("new", help="create projects/<name>/ as a new git repository")
    new.add_argument("name", help="folder name: lowercase letters, digits, '-' or '_'")
    new.add_argument("--test", metavar="CMD", help="test command, when it cannot be detected")

    attach = commands.add_parser("attach", help="register an existing project folder")
    attach.add_argument("path", type=Path, help="the project's top folder")
    attach.add_argument("--name", help="project name (default: the folder name)")
    attach.add_argument("--test", metavar="CMD", help="test command, when it cannot be detected")

    commands.add_parser("list", help="show every project, its stacks and test command")

    status = commands.add_parser("status", help="a project's task, uncommitted work and next step")
    status.add_argument("name", help="project name, as `list` shows it")

    resume = commands.add_parser("resume", help="show disruption recovery guidance and active task status for a project")
    resume.add_argument("name", help="project name, as `list` shows it")

    checkpoint = commands.add_parser("checkpoint", help="record an atomic milestone checkpoint in project task ledger")
    checkpoint.add_argument("name", help="project name, as `list` shows it")
    checkpoint.add_argument("--task", default=None, help="task ID (default: active task in ledger or 'project-work')")
    checkpoint.add_argument("--phase-num", type=int, default=2, choices=[1, 2, 3, 4, 5], help="lifecycle phase 1-5 (default: 2)")
    checkpoint.add_argument("--desc", required=True, help="description of the milestone / task step")
    checkpoint.add_argument("--why", default=None, help="rationale (Pre-Flight Impact Assessment)")
    checkpoint.add_argument("--benefits", default=None, help="expected benefits")
    checkpoint.add_argument("--risks", default=None, help="identified risks across contract/dependency/concurrency/state")
    checkpoint.add_argument("--mitigation", default=None, help="risk mitigation strategy")

    complete = commands.add_parser("complete", help="mark active task completed in project task ledger")
    complete.add_argument("name", help="project name, as `list` shows it")
    complete.add_argument("--task", default=None, help="task ID (default: active task in ledger)")

    clean = commands.add_parser("clean", help="purge dangling temporary files in project workspace")
    clean.add_argument("name", help="project name, as `list` shows it")
    clean.add_argument("--force", action="store_true", help="delete buffers immediately regardless of age")

    check = commands.add_parser("check", help="run every gate of a project (its Phase 4)")
    check.add_argument("name", help="project name, as `list` shows it")

    fix = commands.add_parser("fix", help="self-heal project memory, clean stale temporary buffers, and sync codebase map")
    fix.add_argument("name", help="project name, as `list` shows it")

    delegate = commands.add_parser("delegate",
                                   help="safely delegate a background task to a subagent",
                                   description="safely delegate a background task to a subagent")
    delegate.add_argument("role", help=f"subagent role: {', '.join(VALID_SUBAGENT_ROLES)}")
    delegate.add_argument("prompt", help="task prompt or instruction for the subagent")
    delegate.add_argument("--file", "-f", dest="file", default=None,
                          help="target file to attach or inspect")
    delegate.add_argument("--project", "-p", dest="project", default=None,
                          help="target registered project name")
    delegate.add_argument("--model", "-m", dest="model", default=None,
                          help="model identifier (e.g. ollama/qwen2.5-coder:latest)")
    delegate.add_argument("--timeout", type=int, default=120,
                          help="execution timeout in seconds (default: 120)")
    delegate.add_argument("--format", dest="format", choices=["text", "json"], default="text",
                          help="output format (default: text)")
    return parser


def _active_workspace() -> Path:
    cwd = Path.cwd()
    return cwd if (cwd / "projects").is_dir() else ROOT_DIR


def cmd_new(args: argparse.Namespace) -> int:
    root, warning = create_project(args.name, args.test, workspace=_active_workspace())
    print(f"[OK] Created project '{args.name}' at {root}")
    if warning:
        print(f"[WARN] {warning}", file=sys.stderr)
    print(f"     Next: describe what to build; work happens inside {root}.")
    return 0


def cmd_attach(args: argparse.Namespace) -> int:
    name, folder, created = attach_project(args.path, args.name, args.test, workspace=_active_workspace())
    state = "new .aikit/ memory created" if created else "existing .aikit/ memory kept"
    print(f"[OK] Attached '{name}' at {folder} ({state})")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    projects = list_projects(_active_workspace())
    if not projects:
        print("No projects yet. Create one with `python aikit.py new <name>`.")
        return 0
    for project in projects:
        if not project.present:
            print(f"{project.name}  MISSING  {project.path}  (folder or .aikit/project.json gone)")
            continue
        stacks = ",".join(s.name for s in project.stacks) or "no stack detected"
        test = project.test_command or "no test command"
        kind = "attached" if project.attached else "local"
        print(f"{project.name}  [{stacks}]  test: {test}  ({kind}: {project.path})")
    return 0


def present_project(name: str) -> Project:
    """The registered project `name`, refusing one whose folder or record is gone."""
    project = find_project(name, _active_workspace())
    if not project.present:
        raise ProjectError(
            f"Project '{project.name}' is missing at {project.path}.",
            "its folder or .aikit/project.json is gone, so there is no memory to use.",
            "restore the folder, or attach its new location with `python aikit.py attach <path>`.",
        )
    return project


def cmd_status(args: argparse.Namespace) -> int:
    project = present_project(args.name)
    stacks = ",".join(s.name for s in project.stacks) or "none detected"
    print(f"Project:   {project.name}  ({project.path})")
    print(f"Stacks:    {stacks}")
    print(f"Tests:     {project.test_command or 'none; set one with .aikit/project.json test_command'}")
    print(f"Decision:  {latest_decision(project.path) or 'none recorded yet'}")
    print(format_resume_report(run_disruption_audit(workspace_dir=project.path)))
    # PRINCIPLE-011 R8: project cockpit lifecycle commands
    print("Project cockpit lifecycle commands:")
    print(f"  python aikit.py resume {project.name}")
    print(f'  python aikit.py checkpoint {project.name} --desc "[1/M] <plan>"')
    print(f"  python aikit.py complete {project.name}")
    print(f"  python aikit.py clean {project.name}")
    gates = ", ".join(gate.name for gate in resolve_gates(project))
    print(f"Phase 4 gates ({gates}): python aikit.py check {project.name}")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    project = present_project(args.name)
    report = format_resume_report(run_disruption_audit(workspace_dir=project.path))
    print(report)
    return 0


def cmd_checkpoint(args: argparse.Namespace) -> int:
    project = present_project(args.name)
    ledger_path = project.path / PROJECT_MEMORY_DIRNAME / "task_ledger.json"
    task_id = args.task
    if not task_id:
        ledger = load_ledger(ledger_path)
        active = ledger.get("active_task")
        if active and active.get("task_id"):
            task_id = active["task_id"]
        else:
            task_id = "project-work"
    record_checkpoint(
        task_id=task_id,
        phase=f"phase {args.phase_num}",
        description=args.desc,
        phase_num=args.phase_num,
        ledger_file=ledger_path,
        why=args.why,
        benefits=args.benefits,
        risks=args.risks,
        mitigation=args.mitigation,
    )
    print(f"[OK] Checkpoint recorded for '{project.name}': Task '{task_id}', Phase {args.phase_num} - {args.desc}")
    return 0


def cmd_complete(args: argparse.Namespace) -> int:
    project = present_project(args.name)
    ledger_path = project.path / PROJECT_MEMORY_DIRNAME / "task_ledger.json"
    task_id = args.task
    if not task_id:
        ledger = load_ledger(ledger_path)
        active = ledger.get("active_task")
        if active and active.get("task_id"):
            task_id = active["task_id"]
        else:
            print(f"Error: No active task in '{project.name}' ledger to complete.", file=sys.stderr)
            print("Why: complete requires an active task or an explicit --task ID.", file=sys.stderr)
            print("Fix: pass --task <task_id> or start a task with checkpoint first.", file=sys.stderr)
            return 1
    success = mark_task_completed(task_id, ledger_file=ledger_path)
    if success:
        print(f"[OK] Marked task '{task_id}' completed for project '{project.name}'.")
        return 0
    else:
        print(f"Error: Task '{task_id}' is not the active task for project '{project.name}'.", file=sys.stderr)
        print("Why: only an active task can be completed.", file=sys.stderr)
        print(f"Fix: check active task with `python aikit.py status {project.name}`.", file=sys.stderr)
        return 1


def cmd_clean(args: argparse.Namespace) -> int:
    project = present_project(args.name)
    min_age = 0.0 if args.force else 60.0
    cleaned = clean_dangling_temp_files(project.path, min_age_seconds=min_age)
    if cleaned:
        print(f"[CLEAN] Purged {len(cleaned)} temporary file(s) in '{project.name}':")
        for f in cleaned:
            print(f"  • {f}")
    else:
        print(f"[OK] No dangling temporary files found in '{project.name}'.")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    project = present_project(args.name)
    results = run_gates(project.path, resolve_gates(project))
    for result in results:
        mark = "PASS" if result.passed else "FAIL"
        print(f"[{mark}] {result.gate.name} ({result.seconds:.1f}s, {result.gate.source}): {result.gate.command}")
        if not result.passed:
            for line in failure_tail(result.output):
                print(f"       {line}")
    passed = sum(result.passed for result in results)
    print(f"{passed}/{len(results)} gates passed for '{project.name}'")
    failed = [result.gate.name for result in results if not result.passed]
    sys.stdout.flush()  # the report above, then the triad, in that order when both are piped
    if failed:
        print(f"Error: gate(s) failed: {', '.join(failed)}", file=sys.stderr)
        print("Why: a project commits only when every gate passes (PRINCIPLE-011 R8, PRINCIPLE-014 R1).",
              file=sys.stderr)
        print(f"Fix: fix the cause in the output above, then rerun `python aikit.py check {project.name}`.",
              file=sys.stderr)
        return 1
    if not any(result.gate.name == "test" for result in results):
        print("Error: the project has no test gate.", file=sys.stderr)
        print("Why: without tests the gates prove nothing about behaviour (PRINCIPLE-014 R1).", file=sys.stderr)
        print("Fix: write tests, and set `test_command` in .aikit/project.json when it is not detected.",
              file=sys.stderr)
        return 1
    return 0


def cmd_fix(args: argparse.Namespace) -> int:
    """Self-heal project memory, clean dangling temporary buffers, and sync codebase map."""
    project = present_project(args.name)
    print(f"Self-checking & fixing project '{project.name}' ({project.path}):")
    fixes: List[str] = []

    had_config = config_path(project.path).exists()
    had_gitignore = (project.path / ".gitignore").exists()
    had_decisions = (project.path / PROJECT_MEMORY_DIRNAME / DECISIONS_FILENAME).exists()
    had_ledger = (project.path / PROJECT_MEMORY_DIRNAME / "task_ledger.json").exists()
    had_readme = (project.path / "README.md").exists()
    had_claude = (project.path / ".claude" / "skills" / "aikit" / "SKILL.md").exists()
    missing_targets = [rel for rel in PROJECT_INSTRUCTION_TARGETS if not (project.path / rel).exists()]

    created = write_memory(project.path, project.name, project.test_command)
    if created or (not had_config and config_path(project.path).exists()):
        fixes.append("initialized missing .aikit/project.json")
    if not had_gitignore and (project.path / ".gitignore").exists():
        fixes.append("created .gitignore with transient state patterns")
    if not had_decisions and (project.path / PROJECT_MEMORY_DIRNAME / DECISIONS_FILENAME).exists():
        fixes.append("seeded .aikit/decisions.md register")
    if not had_ledger and (project.path / PROJECT_MEMORY_DIRNAME / "task_ledger.json").exists():
        fixes.append("seeded .aikit/task_ledger.json")
    for rel in missing_targets:
        if (project.path / rel).exists():
            fixes.append(f"seeded {rel} guidelines")
    if not had_readme and (project.path / "README.md").exists():
        fixes.append("seeded README.md quick-reference")
    if not had_claude and (project.path / ".claude" / "skills" / "aikit" / "SKILL.md").exists():
        fixes.append("seeded .claude/skills/aikit/SKILL.md")

    cleaned = clean_dangling_temp_files(project.path, min_age_seconds=0)
    if cleaned:
        fixes.append(f"cleaned {len(cleaned)} dangling temporary buffer(s)")

    if find_python_files(project.path):
        map_content = generate_codebase_map(root=project.path, strict=False)
        map_path = project.path / ".aikit" / "codebase_map.md"
        write_generated_file(map_path, map_content)
        fixes.append("synchronized .aikit/codebase_map.md")

    if fixes:
        for fix in fixes:
            print(f"  [FIXED] {fix}")
    else:
        print("  [CLEAN] No memory or temporary buffer anomalies detected.")

    print(f"Running Phase 4 verification for '{project.name}':")
    return cmd_check(args)


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
    Safely delegate a background task to a subagent under PRINCIPLE-008 R1/R6, PRINCIPLE-011 R5,
    and PRINCIPLE-012 R8. Enforces closed stdin, timeout, and verifies task ledgers are unmutated.
    """
    if role not in VALID_SUBAGENT_ROLES:
        err = (
            f"Error: unknown subagent role '{role}'.\n"
            f"Why: role must be one of: {', '.join(VALID_SUBAGENT_ROLES)}.\n"
            f"Fix: specify a valid role (e.g. `python aikit.py delegate worker \"...\"`)."
        )
        return 2, err

    if not prompt or not prompt.strip():
        err = (
            "Error: empty prompt provided.\n"
            "Why: subagent delegation requires a clear task description (PRINCIPLE-008 R6).\n"
            "Fix: supply non-empty prompt text in quotes."
        )
        return 2, err

    target_cwd = workspace
    if project_name:
        project = find_project(project_name, workspace=workspace)
        target_cwd = project.path

    ledgers = [
        workspace / ".agents" / "task_ledger.json",
        target_cwd / ".aikit" / "task_ledger.json",
    ]
    snapshots = {lp: lp.read_bytes() for lp in ledgers if lp.is_file()}

    if runner is None:
        runner_bin = shutil.which("opencode") or shutil.which("opencode.cmd") or shutil.which("opencode.ps1")
        if not runner_bin:
            err = (
                "Error: OpenCode subagent runner not found.\n"
                "Why: the `opencode` CLI is required for native subagent process execution (PRINCIPLE-009 R6).\n"
                "Fix: install OpenCode via npm (`npm install -g opencode`) or configure an alternative runner."
            )
            return 1, err

    cmd = [
        "opencode", "run", "--standalone",
        "--format", "json",
        "--agent", role,
    ]
    if file:
        cmd.extend(["--file", str(file)])
    if model:
        cmd.extend(["--model", str(model)])
    cmd.append(prompt)

    t0 = time.time()
    try:
        if runner is not None:
            proc = runner(cmd, cwd=str(target_cwd), timeout=timeout)
        else:
            proc = subprocess.run(
                cmd,
                cwd=str(target_cwd),
                stdin=subprocess.DEVNULL,
                timeout=timeout,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=(sys.platform == "win32"),
            )
    except subprocess.TimeoutExpired:
        err = (
            f"Error: subagent execution timed out after {timeout} seconds.\n"
            "Why: long-running tasks without bounds exhaust process resources (PRINCIPLE-010 R3).\n"
            "Fix: bound the brief scope (<=50 files, PRINCIPLE-008 R1) or increase --timeout."
        )
        return 1, err
    except OSError as exc:
        err = (
            f"Error: failed to execute subagent process: {exc}\n"
            "Why: system error while spawning process.\n"
            "Fix: check runner permissions and environment."
        )
        return 1, err
    duration = time.time() - t0

    # Invariant: sub-agents NEVER write the ledger (PRINCIPLE-008 R6)
    for lp, original_data in snapshots.items():
        if lp.is_file() and lp.read_bytes() != original_data:
            lp.write_bytes(original_data)
            err = (
                f"Error: subagent attempted to mutate protected ledger at {lp}!\n"
                "Why: subagents are strictly forbidden from writing to task ledgers (PRINCIPLE-008 R6).\n"
                "Fix: the ledger was automatically restored; review the subagent brief and permissions."
            )
            return 1, err

    for lp in ledgers:
        if lp not in snapshots and lp.is_file():
            lp.unlink(missing_ok=True)
            err = (
                f"Error: subagent attempted to create protected ledger at {lp}!\n"
                "Why: subagents are strictly forbidden from writing to task ledgers (PRINCIPLE-008 R6).\n"
                "Fix: the newly created ledger was purged; review subagent permissions."
            )
            return 1, err

    if output_format == "json":
        payload = {
            "status": "success" if proc.returncode == 0 else "error",
            "agent": role,
            "exit_code": proc.returncode,
            "duration_seconds": round(duration, 3),
            "output": proc.stdout.strip(),
            "ledger_shield": "unmutated",
        }
        return proc.returncode, json.dumps(payload, indent=2)
    else:
        out = proc.stdout.strip()
        if proc.returncode != 0:
            err_msg = proc.stderr.strip() or out or f"Subagent exited with code {proc.returncode}"
            return proc.returncode, f"[SUBAGENT ERROR ({role}, {duration:.1f}s)]\n{err_msg}"
        return 0, f"[SUBAGENT OK ({role}, {duration:.1f}s)]\n{out}"


def cmd_delegate(args: argparse.Namespace) -> int:
    exit_code, output = delegate_subagent(
        role=args.role,
        prompt=args.prompt,
        file=args.file,
        project_name=args.project,
        model=args.model,
        timeout=args.timeout,
        output_format=args.format,
        workspace=_active_workspace(),
    )
    if exit_code == 0:
        print(output)
    else:
        print(output, file=sys.stderr)
    return exit_code


HANDLERS = {
    "new": cmd_new,
    "attach": cmd_attach,
    "list": cmd_list,
    "status": cmd_status,
    "resume": cmd_resume,
    "checkpoint": cmd_checkpoint,
    "complete": cmd_complete,
    "clean": cmd_clean,
    "check": cmd_check,
    "fix": cmd_fix,
    "delegate": cmd_delegate,
}


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return HANDLERS[args.command](args)
    except ProjectError as error:
        return report_error(error)
