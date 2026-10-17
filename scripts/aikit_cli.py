"""
`aikit` command line: create, attach, list, report on and check the projects AIKit builds
(ADR-119, ADR-120, ADR-122).

Run through the root shim: `python aikit.py <command>`. Exit codes: 0 success, 1 the request
could not be carried out, 2 the command line was wrong (PRINCIPLE-011).
"""

import argparse
import sys
from pathlib import Path
from typing import List, NoReturn, Optional

from scripts.disruption_recovery import (
    ROOT_DIR,
    clean_dangling_temp_files,
    format_resume_report,
    run_disruption_audit,
)
from scripts.project_gates import failure_tail, resolve_gates, run_gates
from scripts.project_registry import (
    ProjectError,
    attach_project,
    create_project,
    Project,
    find_project,
    latest_decision,
    list_projects,
    write_memory,
    AGENTS_FILENAME,
    AGENTS_TEMPLATE,
)
from scripts.update_knowledge_base import generate_codebase_map


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

    check = commands.add_parser("check", help="run every gate of a project (its Phase 4)")
    check.add_argument("name", help="project name, as `list` shows it")

    fix = commands.add_parser("fix", help="self-heal project memory, clean stale temporary buffers, and sync codebase map")
    fix.add_argument("name", help="project name, as `list` shows it")
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
    # PRINCIPLE-011 R8: for project work, the project is the workspace of every lifecycle command.
    print("Ledger commands for this project add the workspace flag, e.g.")
    print(f'  python scripts/disruption_recovery.py --workspace "{project.path}" --checkpoint <task> ...')
    gates = ", ".join(gate.name for gate in resolve_gates(project))
    print(f"Phase 4 gates ({gates}): python aikit.py check {project.name}")
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

    agents_path = project.path / AGENTS_FILENAME
    had_agents = agents_path.exists()
    created = write_memory(project.path, project.name, project.test_command)
    if created:
        fixes.append("initialized missing .aikit/project.json")
    if not had_agents and agents_path.exists():
        fixes.append("seeded AGENTS.md guidelines")

    cleaned = clean_dangling_temp_files(project.path, min_age_seconds=0)
    if cleaned:
        fixes.append(f"cleaned {len(cleaned)} dangling temporary buffer(s)")

    if any(project.path.glob("**/*.py")):
        map_content = generate_codebase_map(root=project.path, strict=False)
        map_path = project.path / ".aikit" / "codebase_map.md"
        with open(map_path, "w", encoding="utf-8") as f:
            f.write(map_content)
        fixes.append("synchronized .aikit/codebase_map.md")

    if fixes:
        for fix in fixes:
            print(f"  [FIXED] {fix}")
    else:
        print("  [CLEAN] No memory or temporary buffer anomalies detected.")

    print(f"Running Phase 4 verification for '{project.name}':")
    return cmd_check(args)


HANDLERS = {"new": cmd_new, "attach": cmd_attach, "list": cmd_list, "status": cmd_status,
            "check": cmd_check, "fix": cmd_fix}


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return HANDLERS[args.command](args)
    except ProjectError as error:
        return report_error(error)
