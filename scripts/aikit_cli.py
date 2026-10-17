"""
`aikit` command line: create, attach, list, report on, check, fix and delegate for the projects
AIKit builds (ADR-119 to ADR-128).

Run through the root shim: `python aikit.py <command>`. Exit codes: 0 success, 1 the request
could not be carried out, 2 the command line was wrong (PRINCIPLE-011).
"""

import argparse
import sys
from pathlib import Path
from typing import List, NoReturn, Optional

from scripts.disruption_recovery import (
    ROOT_DIR,
    TEMP_STALE_SECONDS,
    checkpoint_command,
    clean_dangling_temp_files,
    format_resume_report,
    mark_task_completed,
    run_disruption_audit,
    workspace_ledger_path,
)
from scripts.project_gates import failure_tail, resolve_gates, run_gates
from scripts.project_publish import publish_project
from scripts.project_registry import (
    Project,
    ProjectError,
    add_guideline,
    attach_project,
    create_project,
    find_project,
    latest_decision,
    list_projects,
    project_guidelines,
    seed_readme,
    write_memory,
)
from scripts.subagent_delegate import delegate_subagent
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


def build_parser() -> argparse.ArgumentParser:
    parser = TriadArgumentParser(
        prog="python aikit.py",
        description="Create and manage the projects AIKit builds. Each project is its own folder "
                    "and git repository with its memory in .aikit/.",
    )
    # Explicit, never guessed from the working directory: a stray `projects/` folder elsewhere
    # must not become the registry (ADR-128).
    parser.add_argument("--workspace", type=Path, default=ROOT_DIR, metavar="DIR",
                        help="AIKit checkout whose projects/ to use (default: this one; for sandboxes)")
    commands = parser.add_subparsers(dest="command", required=True, parser_class=TriadArgumentParser)

    def project_command(name: str, help_text: str) -> argparse.ArgumentParser:
        sub = commands.add_parser(name, help=help_text)
        sub.add_argument("name", help="project name, as `list` shows it")
        return sub

    new = commands.add_parser("new", help="create projects/<name>/ as a new git repository")
    new.add_argument("name", help="folder name: lowercase letters, digits, '-' or '_'")
    new.add_argument("--test", metavar="CMD", help="test command, when it cannot be detected")

    attach = commands.add_parser("attach", help="register an existing project folder")
    attach.add_argument("path", type=Path, help="the project's top folder")
    attach.add_argument("--name", help="project name (default: the folder name)")
    attach.add_argument("--test", metavar="CMD", help="test command, when it cannot be detected")

    commands.add_parser("list", help="show every project, its stacks and test command")
    project_command("status", "a project's task, uncommitted work, latest decision and gates")
    project_command("resume", "the cold-start report for a project (PRINCIPLE-004 R2)")

    checkpoint = project_command("checkpoint", "record a checkpoint in the project's ledger")
    checkpoint.add_argument("--task", required=True, help="task ID")
    checkpoint.add_argument("--phase-num", type=int, required=True, choices=[1, 2, 3, 4, 5],
                            help="lifecycle phase 1-5")
    checkpoint.add_argument("--desc", required=True, help="what was done; a plan starts '[1/M]'")
    for field in ("why", "benefits", "risks", "mitigation"):
        checkpoint.add_argument(f"--{field}", default=None,
                                help="impact assessment, required on a task's first plan (PRINCIPLE-007 R6)")

    complete = project_command("complete", "mark the project's active task completed")
    complete.add_argument("--task", required=True, help="the active task's ID")

    project_command("clean", f"delete the project's temp buffers older than {TEMP_STALE_SECONDS}s")
    guideline = project_command("guideline", "add a rule to the project's guidelines (below the principles)")
    guideline.add_argument("rule", help="the rule, one line")
    guideline.add_argument("--source", required=True, help="where it comes from: user, ADR-NNN or a person")

    project_command("check", "run every gate of a project (its Phase 4)")
    project_command("fix", "restore missing project memory and README, refresh its map, then check")
    publish = project_command("publish", "upload the project to its own GitHub repository (private by default)")
    publish.add_argument("--public", action="store_true", help="create the repository as public")

    delegate = commands.add_parser("delegate", help="run an OpenCode sub-agent on a bounded brief")
    delegate.add_argument("role", help="a profile name in .opencode/agents/")
    delegate.add_argument("prompt", help="the brief for the sub-agent")
    delegate.add_argument("--file", "-f", default=None, help="file to attach to the brief")
    delegate.add_argument("--project", "-p", default=None, help="run inside this registered project")
    delegate.add_argument("--model", "-m", default=None, help="model ID, e.g. ollama/qwen2.5-coder")
    delegate.add_argument("--timeout", type=int, default=120, help="seconds before the run is killed")
    delegate.add_argument("--format", choices=["text", "json"], default="text", help="report format")
    return parser


def present_project(name: str, workspace: Path) -> Project:
    """The registered project `name`, refusing one whose folder or record is gone."""
    project = find_project(name, workspace)
    if not project.present:
        raise ProjectError(
            f"Project '{project.name}' is missing at {project.path}.",
            "its folder or .aikit/project.json is gone, so there is no memory to use.",
            "restore the folder, or attach its new location with `python aikit.py attach <path>`.",
        )
    return project


def print_guidelines(project: Project) -> None:
    """The project's own rules, with their rank, in every cold-start report (PRINCIPLE-004 R2)."""
    rules = project_guidelines(project.path)
    print(f"Guidelines: {len(rules)} rule(s) in .aikit/guidelines.md; they add to and rank below "
          f"AIKit's principles (PRINCIPLE-000 R6).")
    for rule in rules:
        print(f"  {rule}")


def cmd_new(args: argparse.Namespace) -> int:
    root, warning = create_project(args.name, args.test, workspace=args.workspace)
    print(f"[OK] Created project '{args.name}' at {root}")
    if warning:
        print(f"[WARN] {warning}", file=sys.stderr)
    print(f"     Next: describe what to build; work happens inside {root}.")
    return 0


def cmd_attach(args: argparse.Namespace) -> int:
    name, folder, created = attach_project(args.path, args.name, args.test, workspace=args.workspace)
    state = "created .aikit/ memory" if created else "kept its existing .aikit/ memory"
    print(f"[OK] Attached '{name}' at {folder} ({state})")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    projects = list_projects(args.workspace)
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
    project = present_project(args.name, args.workspace)
    stacks = ",".join(s.name for s in project.stacks) or "none detected"
    print(f"Project:   {project.name}  ({project.path})")
    print(f"Stacks:    {stacks}")
    print(f"Tests:     {project.test_command or 'none; set one with .aikit/project.json test_command'}")
    print(f"Decision:  {latest_decision(project.path) or 'none recorded yet'}")
    print_guidelines(project)
    print(format_resume_report(run_disruption_audit(workspace_dir=project.path)))
    # PRINCIPLE-011 R8: for project work, the project is the workspace of every lifecycle command.
    print(f'Ledger:    python aikit.py checkpoint {project.name} --task <id> --phase-num <1-5> --desc "..."')
    gates = ", ".join(gate.name for gate in resolve_gates(project))
    print(f"Phase 4 gates ({gates}): python aikit.py check {project.name}")
    return 0


def cmd_resume(args: argparse.Namespace) -> int:
    project = present_project(args.name, args.workspace)
    print_guidelines(project)
    print(format_resume_report(run_disruption_audit(workspace_dir=project.path)))
    return 0


def cmd_guideline(args: argparse.Namespace) -> int:
    project = present_project(args.name, args.workspace)
    gid = add_guideline(project.path, args.rule, args.source)
    print(f"[OK] {gid} added to the guidelines of '{project.name}'; it ranks below AIKit's principles.")
    return 0


def cmd_checkpoint(args: argparse.Namespace) -> int:
    project = present_project(args.name, args.workspace)
    impact = {"why": args.why, "benefits": args.benefits, "risks": args.risks,
              "mitigation": args.mitigation}
    return checkpoint_command(args.task, f"phase {args.phase_num}", args.phase_num, args.desc, impact,
                              workspace_ledger_path(project.path))


def cmd_complete(args: argparse.Namespace) -> int:
    project = present_project(args.name, args.workspace)
    if mark_task_completed(args.task, ledger_file=workspace_ledger_path(project.path)):
        print(f"[OK] Task '{args.task}' marked as completed in '{project.name}'.")
        return 0
    print(f"Error: task '{args.task}' is not the active task of '{project.name}'.", file=sys.stderr)
    print("Why: only the active task can be completed; nothing was changed.", file=sys.stderr)
    print(f"Fix: run `python aikit.py resume {project.name}` to see the active task's ID.", file=sys.stderr)
    return 1


def cmd_clean(args: argparse.Namespace) -> int:
    project = present_project(args.name, args.workspace)
    # Only stale buffers: a younger one may be another agent's atomic write in flight (PRINCIPLE-013).
    cleaned = clean_dangling_temp_files(project.path)
    for rel in cleaned:
        print(f"[CLEAN] {rel}")
    print(f"[OK] {len(cleaned)} stale temporary file(s) removed from '{project.name}'.")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    project = present_project(args.name, args.workspace)
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
        print(f"Fix: run `python aikit.py fix {project.name}` for memory and map drift; fix any other "
              "cause shown above by hand, then rerun the check.", file=sys.stderr)
        return 1
    if not any(result.gate.name == "test" for result in results):
        print("Error: the project has no test gate.", file=sys.stderr)
        print("Why: without tests the gates prove nothing about behaviour (PRINCIPLE-014 R1).", file=sys.stderr)
        print("Fix: write tests, and set `test_command` in .aikit/project.json when it is not detected.",
              file=sys.stderr)
        return 1
    return 0


def cmd_fix(args: argparse.Namespace) -> int:
    """
    Repair what AIKit can repair mechanically, then run the gates: everything left is the
    agent's to fix by hand, guided by each gate's output.
    """
    project = present_project(args.name, args.workspace)
    fixes: List[str] = []
    memory = project.path / ".aikit"
    expected = ["project.json", "guidelines.md", "decisions.md", "task_ledger.json"]
    missing = [name for name in expected if not (memory / name).is_file()]
    write_memory(project.path, project.name, project.test_command)
    fixes += [f"restored .aikit/{name}" for name in missing if (memory / name).is_file()]
    if seed_readme(project.path, project.name, project.test_command):
        fixes.append("seeded README.md from the project template (complete it by hand)")
    fixes += [f"removed stale buffer {rel}" for rel in clean_dangling_temp_files(project.path)]
    if find_python_files(project.path):
        write_generated_file(memory / "codebase_map.md", generate_codebase_map(root=project.path, strict=False))
        fixes.append("regenerated .aikit/codebase_map.md")
    for fix in fixes:
        print(f"[FIXED] {fix}")
    print(f"Checking '{project.name}' after {len(fixes)} repair(s):")
    return cmd_check(args)


def cmd_publish(args: argparse.Namespace) -> int:
    project = present_project(args.name, args.workspace)
    code, report = publish_project(project.path, project.name, public=args.public)
    print(report, file=sys.stdout if code == 0 else sys.stderr)
    return code


def cmd_delegate(args: argparse.Namespace) -> int:
    code, report = delegate_subagent(args.role, args.prompt, file=args.file, project_name=args.project,
                                     model=args.model, timeout=args.timeout, output_format=args.format,
                                     workspace=args.workspace)
    print(report, file=sys.stdout if code == 0 else sys.stderr)
    return code


HANDLERS = {
    "new": cmd_new,
    "attach": cmd_attach,
    "list": cmd_list,
    "status": cmd_status,
    "resume": cmd_resume,
    "checkpoint": cmd_checkpoint,
    "complete": cmd_complete,
    "clean": cmd_clean,
    "guideline": cmd_guideline,
    "check": cmd_check,
    "fix": cmd_fix,
    "publish": cmd_publish,
    "delegate": cmd_delegate,
}


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return HANDLERS[args.command](args)
    except ProjectError as error:
        return report_error(error)
