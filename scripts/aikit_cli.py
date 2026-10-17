"""
`aikit` command line: create, attach, list and report on the projects AIKit builds (ADR-119, ADR-120).

Run through the root shim: `python aikit.py <command>`. Exit codes: 0 success, 1 the request
could not be carried out, 2 the command line was wrong (PRINCIPLE-011).
"""

import argparse
import sys
from pathlib import Path
from typing import List, NoReturn, Optional

from scripts.disruption_recovery import format_resume_report, run_disruption_audit
from scripts.project_registry import (
    ProjectError,
    attach_project,
    create_project,
    find_project,
    latest_decision,
    list_projects,
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
    return parser


def cmd_new(args: argparse.Namespace) -> int:
    root, warning = create_project(args.name, args.test)
    print(f"[OK] Created project '{args.name}' at {root}")
    if warning:
        print(f"[WARN] {warning}", file=sys.stderr)
    print(f"     Next: describe what to build; work happens inside {root}.")
    return 0


def cmd_attach(args: argparse.Namespace) -> int:
    name, folder, created = attach_project(args.path, args.name, args.test)
    state = "created .aikit/project.json" if created else "kept its existing .aikit/ memory"
    print(f"[OK] Attached '{name}' at {folder} ({state})")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    projects = list_projects()
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


def cmd_status(args: argparse.Namespace) -> int:
    project = find_project(args.name)
    if not project.present:
        raise ProjectError(
            f"Project '{project.name}' is missing at {project.path}.",
            "its folder or .aikit/project.json is gone, so there is no memory to report.",
            "restore the folder, or attach its new location with `python aikit.py attach <path>`.",
        )
    stacks = ",".join(s.name for s in project.stacks) or "none detected"
    print(f"Project:   {project.name}  ({project.path})")
    print(f"Stacks:    {stacks}")
    print(f"Tests:     {project.test_command or 'none; set one with .aikit/project.json test_command'}")
    print(f"Decision:  {latest_decision(project.path) or 'none recorded yet'}")
    print(format_resume_report(run_disruption_audit(workspace_dir=project.path)))
    print("Ledger commands for this project add the workspace flag, e.g.")
    print(f'  python scripts/disruption_recovery.py --workspace "{project.path}" --checkpoint <task> ...')
    return 0


HANDLERS = {"new": cmd_new, "attach": cmd_attach, "list": cmd_list, "status": cmd_status}


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return HANDLERS[args.command](args)
    except ProjectError as error:
        return report_error(error)
