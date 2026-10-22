"""
`aikit` command line: create, attach, list, report on, check, fix and delegate for the projects
AIKit builds (ADR-119 to ADR-128).

Run through the root shim: `python aikit.py <command>`. Exit codes: 0 success, 1 the request
could not be carried out, 2 the command line was wrong (PRINCIPLE-011).
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, NoReturn, Optional

from scripts.disruption_recovery import (
    ROOT_DIR,
    TEMP_STALE_SECONDS,
    UnsupportedLedgerVersion,
    checkpoint_command,
    clean_dangling_temp_files,
    format_resume_report,
    mark_task_completed,
    run_disruption_audit,
    workspace_ledger_path,
)
from scripts.project_publish import (
    auto_push_project,
    get_project_repo_url,
    publish_project,
)

from scripts.project_registry import (
    Project,
    ProjectError,
    add_guideline,
    attach_project,
    create_project,
    find_project,
    latest_decision,
    list_projects,
    load_config,
    project_guidelines,
    reconcile_readme_tree,
    seed_readme,
    write_memory,
)
from scripts.subagent_delegate import delegate_subagent
from scripts import ui_contract
from scripts.update_knowledge_base import (
    find_python_files,
    generate_codebase_map,
    write_generated_file,
)


def failure_tail(output):
    from scripts.project_gates import failure_tail as _failure_tail
    return _failure_tail(output)


def resolve_gates(project):
    from scripts.project_gates import resolve_gates as _resolve_gates
    return _resolve_gates(project)


def run_gates(path, gates):
    from scripts.project_gates import run_gates as _run_gates
    return _run_gates(path, gates)


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
    new.add_argument("--publish", action="store_true", help="publish to GitHub immediately after creation")
    new.add_argument("--public", action="store_true", help="make the GitHub repository public (default: private)")

    attach = commands.add_parser("attach", help="register an existing project folder")
    attach.add_argument("path", type=Path, help="the project's top folder")
    attach.add_argument("--name", help="project name (default: the folder name)")
    attach.add_argument("--test", metavar="CMD", help="test command, when it cannot be detected")

    commands.add_parser("list", help="show every project, its stacks and test command")
    status = project_command("status",
                             "a project's task, uncommitted work, latest decision and gates")
    status.add_argument("--exit-code", action="store_true",
                        help="exit 1 when the project is dirty, conflicted, has an open UI task, or cannot be audited")
    status.add_argument("--json", action="store_true",
                        help="print the report as JSON instead of text; `clean` is the --exit-code verdict")
    resume = project_command("resume", "the cold-start report for a project (PRINCIPLE-004 R2)")
    resume.add_argument("--json", action="store_true",
                        help="print the cold-start report as JSON instead of text")

    checkpoint = project_command("checkpoint", "record a checkpoint in the project's ledger")
    checkpoint.add_argument("--task", required=True, help="task ID")
    checkpoint.add_argument("--phase-num", type=int, required=True, choices=[1, 2, 3, 4, 5],
                            help="lifecycle phase 1-5")
    checkpoint.add_argument("--desc", required=True, help="what was done; a plan starts '[1/M]'")
    for field in ("why", "benefits", "risks", "mitigation"):
        checkpoint.add_argument(f"--{field}", default=None,
                                help="impact assessment, required on a task's first plan (PRINCIPLE-007 R6)")
    checkpoint.add_argument("--handoff", default="",
                            help="cold-start packet: 'next: ...' plus optional state, failed, "
                                 "open, evidence, separated by ';' (PRINCIPLE-004 R2)")
    checkpoint.add_argument("--redact", action="store_true",
                            help="record credential-shaped text as [REDACTED] instead of refusing it")

    complete = project_command("complete", "mark the project's active task completed")
    complete.add_argument("--task", required=True, help="the active task's ID")

    project_command("clean", f"delete the project's temp buffers older than {TEMP_STALE_SECONDS}s")
    guideline = project_command("guideline", "add a rule to the project's guidelines (below the principles)")
    guideline.add_argument("rule", help="the rule, one line")
    guideline.add_argument("--source", required=True, help="where it comes from: user, ADR-NNN or a person")

    check = project_command("check", "run every gate of a project (its Phase 4)")
    check.add_argument("--no-push", action="store_true", help="skip pushing commits to remote origin after gates pass")
    check.add_argument("--strict", action="store_true",
                       help="require a clean non-bookkeeping tree and a codebase map before passing")
    project_command("fix", "restore missing project memory and README, refresh its map, then check")
    publish = project_command("publish", "upload the project to its own GitHub repository (private by default)")
    publish.add_argument("--public", action="store_true", help="create the repository as public")

    ui = commands.add_parser("ui", help="bound edits to one UI surface declared in .aikit/ui.json")
    ui_commands = ui.add_subparsers(dest="ui_action", required=True, parser_class=TriadArgumentParser)
    for action, text in (("init", "write a UI contract (React/Vite auto, or --fast/--paths)"),
                         ("begin", "open a bounded task from a clean green baseline"),
                         ("verify", "check scope, budget, the fast and snapshot proofs, style"),
                         ("finish", "verify, then close the task (needs --reviewed)"),
                         ("allow", "record an intended inventory removal pattern"),
                         ("abort", "restore only the surface to its baseline"),
                         ("status", "show the open task and its changed paths")):
        sub = ui_commands.add_parser(action, help=text)
        sub.add_argument("name", help="project name, as `list` shows it")
        if action == "begin":
            sub.add_argument("--surface", required=True,
                             help="surface name declared in .aikit/ui.json")
        if action == "init":
            sub.add_argument("--surface", default="app",
                             help="surface name for the generated contract")
            sub.add_argument("--fast", default="",
                             help="manual proof command for a non-React/Vite stack")
            sub.add_argument("--paths", action="append", default=None,
                             help="surface path pattern for a manual contract; repeatable")
            sub.add_argument("--snapshot", default="",
                             help="optional inventory command for a manual contract")
        if action == "allow":
            sub.add_argument("pattern",
                             help="glob matching the inventory entries this task removes")
            sub.add_argument("--reason", required=True,
                             help="why the removal is intended; recorded with the allow entry")
        if action == "finish":
            sub.add_argument("--reviewed", action="store_true",
                             help="confirm a human looked at the running UI")
            sub.add_argument("--reviewer", metavar="NAME",
                             help="who reviewed the running UI, recorded in the task history")
        if action == "verify":
            sub.add_argument("--json", action="store_true",
                             help="emit stable finding codes as JSON for CI")


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


def project_is_clean(audit: Dict[str, object], open_ui_task: bool) -> bool:
    """
    Whether the project's tree is delivery-ready, decided once for every surface that reports it.

    `status --exit-code` and `status --json` both read this. Computing the same verdict twice is
    the defect class ADR-155 and ADR-161 each had to repair, where two readiness surfaces
    disagreed about one tree and auto-push followed the laxer one (ADR-172).
    """
    dirty = (audit.get("modified_files") or audit.get("untracked_files")
             or audit.get("conflicted_files"))
    return not (audit.get("git_missing") or dirty or open_ui_task)


def project_payload(project: Project) -> Dict[str, object]:
    """The project half of a `--json` report: what `status` prints as its header lines."""
    return {
        "name": project.name,
        "path": str(project.path),
        "repo_url": get_project_repo_url(project.path),
        "stacks": [stack.name for stack in project.stacks],
        "test_command": project.test_command or None,
        "latest_decision": latest_decision(project.path) or None,
        # The rules themselves, not a count: PRINCIPLE-004 R2 requires them in every cold-start
        # report, and a JSON reader that got only a number would silently lose them (ADR-172).
        "guidelines": project_guidelines(project.path),
    }


def error_envelope(error: ProjectError) -> str:
    """The stable `--json` failure shape shared by every project command (ADR-167, ADR-172)."""
    return json.dumps({"ok": False,
                       "error": {"code": "project.error", "message": str(error)}}, indent=2)


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
    if getattr(args, "publish", False):
        print(f"Publishing '{args.name}' to GitHub:")
        code, report = publish_project(root, args.name, public=getattr(args, "public", False))
        print(report, file=sys.stdout if code == 0 else sys.stderr)
        if code != 0:
            print(f"[WARN] Project created locally at {root}, but GitHub publication failed.", file=sys.stderr)
            return code
    else:
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
        repo_url = get_project_repo_url(project.path)
        repo_note = f"  repo: {repo_url}" if repo_url else ""
        print(f"{project.name}  [{stacks}]  test: {test}  ({kind}: {project.path}){repo_note}")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    if getattr(args, "json", False):
        try:
            project = present_project(args.name, args.workspace)
        except ProjectError as exc:
            print(error_envelope(exc))
            return exc.exit_code
        audit = run_disruption_audit(workspace_dir=project.path)
        open_ui_task = (project.path / ui_contract.TASK_REL).is_file()
        print(json.dumps({
            "ok": True,
            "clean": project_is_clean(audit, open_ui_task),
            "project": project_payload(project),
            "disruption": audit,
            "ui_task_open": open_ui_task,
            "gates": [gate.name for gate in resolve_gates(project)],
        }, indent=2, default=str))
        if audit.get("ledger_error"):
            return 1
        return 0
    project = present_project(args.name, args.workspace)
    stacks = ",".join(s.name for s in project.stacks) or "none detected"
    repo_url = get_project_repo_url(project.path)
    print(f"Project:   {project.name}  ({project.path})")
    print(f"Repo:      {repo_url or f'none (local only; publish with python aikit.py publish {project.name})'}")
    print(f"Stacks:    {stacks}")
    print(f"Tests:     {project.test_command or 'none; set one with .aikit/project.json test_command'}")
    print(f"Decision:  {latest_decision(project.path) or 'none recorded yet'}")
    print_guidelines(project)
    audit = run_disruption_audit(workspace_dir=project.path)
    print(format_resume_report(audit))
    if audit.get("ledger_error"):
        return 1
    open_ui_task = (project.path / ui_contract.TASK_REL).is_file()
    if open_ui_task:
        print(f"UI task:   open at {ui_contract.TASK_REL}; "
              f"run `python aikit.py ui status {project.name}`")
    # PRINCIPLE-011 R8: for project work, the project is the workspace of every lifecycle command.
    print(f'Ledger:    python aikit.py checkpoint {project.name} --task <id> --phase-num <1-5> --desc "..."')
    gates = ", ".join(gate.name for gate in resolve_gates(project))
    print(f"Phase 4 gates ({gates}): python aikit.py check {project.name}")
    if getattr(args, "exit_code", False) and not project_is_clean(audit, open_ui_task):
        return 1
    return 0



def cmd_resume(args: argparse.Namespace) -> int:
    if getattr(args, "json", False):
        try:
            project = present_project(args.name, args.workspace)
        except ProjectError as exc:
            print(error_envelope(exc))
            return exc.exit_code
        audit = run_disruption_audit(workspace_dir=project.path)
        print(json.dumps({"ok": True, "project": project_payload(project),
                          "disruption": audit}, indent=2, default=str))
        return 1 if audit.get("ledger_error") else 0
    project = present_project(args.name, args.workspace)
    print_guidelines(project)
    audit = run_disruption_audit(workspace_dir=project.path)
    print(format_resume_report(audit))
    return 1 if audit.get("ledger_error") else 0


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
                              workspace_ledger_path(project.path), redact=args.redact,
                              handoff=args.handoff)


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


def project_baseline_errors(project: Project, audit: dict) -> List[str]:
    """The delivery baseline `--strict` requires; ordinary check reports these as warnings."""
    errors: List[str] = []
    if audit.get("ledger_error"):
        errors.append("the project ledger declares a schema this AIKit cannot read")
    if audit.get("git_missing"):
        errors.append("the project is not a git repository, so a clean tree cannot be verified")
    if audit.get("modified_files") or audit.get("untracked_files"):
        errors.append("the project has uncommitted non-bookkeeping changes")
    if audit.get("conflicted_files"):
        errors.append("the project has unresolved merge conflicts")
    if (project.path / ui_contract.TASK_REL).is_file():
        errors.append("a UI task is open; finish or abort it before delivery")
    config = load_config(project.path)
    required = config.get("ui_required") is True
    contract_path = project.path / ui_contract.CONTRACT_REL
    if required or contract_path.is_file():
        try:
            ui_contract.load_contract(project.path)
        except ProjectError as exc:
            prefix = ("ui_required is true but the UI contract is unusable" if required
                      else "the UI contract is unusable")
            errors.append(f"{prefix}: {exc}")
        else:
            if required and not audit.get("git_missing"):
                try:
                    errors.extend(ui_contract.surface_evidence_errors(project.path))
                except ProjectError as exc:
                    errors.append(f"the UI evidence is unusable: {exc}")
    if find_python_files(project.path) and not (project.path / ".aikit" / "codebase_map.md").is_file():
        errors.append("Python sources exist but .aikit/codebase_map.md is missing")
    return errors


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
    print("Manual: record 'checklists: passed' or the failed or skipped item IDs in the task's"
          " latest checkpoint before the next commit (PRINCIPLE-001 R8, PRINCIPLE-011 R8).")
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

    audit = run_disruption_audit(workspace_dir=project.path)
    baseline_errors = project_baseline_errors(project, audit)
    strict = bool(getattr(args, "strict", False))
    for error in baseline_errors:
        print(f"[{'FAIL' if strict else 'WARN'}] {error}")
    if audit.get("ledger_error") or (strict and baseline_errors):
        print("Error: the project is not delivery-ready.", file=sys.stderr)
        print("Why: a passing gate run must describe the committed tree, not an unverified working copy.",
              file=sys.stderr)
        print("Fix: commit the non-bookkeeping changes, resolve any merge conflicts, finish or "
              "abort any open UI task, run `python aikit.py fix <name>` for a missing map, or "
              "open the ledger with the AIKit version that wrote it; then rerun with --strict.",
              file=sys.stderr)
        return 1

    open_ui_task = (project.path / ui_contract.TASK_REL).is_file()
    ui_unready = any(error.startswith(("ui_required is true", "the UI contract is unusable",
                                       "UI surface", "the UI evidence is unusable"))
                     for error in baseline_errors)
    dirty = bool(audit.get("modified_files") or audit.get("untracked_files")
                 or audit.get("conflicted_files")) or open_ui_task or ui_unready
    if dirty:
        detail = (f"{len(audit.get('modified_files', []))} modified, "
                  f"{len(audit.get('untracked_files', []))} untracked, "
                  f"{len(audit.get('conflicted_files', []))} conflicted")
        if open_ui_task:
            detail += ", 1 open UI task"
        if ui_unready:
            detail += ", UI contract not delivery-ready"
        print(f"[DELIVERY] NOT READY: {detail}; run `check --strict` before pushing.")
    if not getattr(args, "no_push", False):
        if dirty:
            print("[WARN] Uncommitted changes or unresolved conflicts exist; skipping auto-push. "
                  "Commit or resolve them and run `check --strict` before pushing.", file=sys.stderr)
        else:
            push_code, push_report = auto_push_project(project.path, project.name)
            if push_code == 0:
                if push_report:
                    print(push_report)
            else:
                print(f"[WARN] {push_report}", file=sys.stderr)
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
    fixes += reconcile_readme_tree(project.path)
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
    audit = run_disruption_audit(workspace_dir=project.path)
    errors = project_baseline_errors(project, audit)
    if errors:
        print("[FAIL] the project is not delivery-ready:", file=sys.stderr)
        for error in errors:
            print(f"       {error}", file=sys.stderr)
        print("Why: publish uploads the committed tree; a tree that fails the delivery baseline "
              "must not be published.", file=sys.stderr)
        print("Fix: commit the work, finish or abort any open UI task, add the missing map or "
              "UI contract, then retry the publish.", file=sys.stderr)
        return 1
    results = run_gates(project.path, resolve_gates(project))
    print(f"{sum(1 for result in results if result.passed)}/{len(results)} gates passed before publish.")
    if any(not result.passed for result in results):
        for result in results:
            if not result.passed:
                print(f"[FAIL] {result.gate.name}: {result.gate.command}", file=sys.stderr)
                for line in failure_tail(result.output):
                    print(f"       {line}", file=sys.stderr)
        print("Error: the project's gates failed; publish refuses an unverified tree.",
              file=sys.stderr)
        print("Why: a published commit must carry the same verified tree that check requires.",
              file=sys.stderr)
        print(f"Fix: run `python aikit.py check {project.name}` and repair the failed gates, "
              "then retry the publish.", file=sys.stderr)
        return 1
    if not any(result.gate.name == "test" for result in results):
        print("Error: the project has no test gate.", file=sys.stderr)
        print("Why: publish must not upload a tree without a behavioural test gate.",
              file=sys.stderr)
        print("Fix: write tests, and set `test_command` in .aikit/project.json when it is not "
              "detected.", file=sys.stderr)
        return 1
    code, report = publish_project(project.path, project.name, public=args.public)
    print(report, file=sys.stdout if code == 0 else sys.stderr)
    return code


def cmd_delegate(args: argparse.Namespace) -> int:
    code, report = delegate_subagent(args.role, args.prompt, file=args.file, project_name=args.project,
                                     model=args.model, timeout=args.timeout, output_format=args.format,
                                     workspace=args.workspace)
    print(report, file=sys.stdout if code == 0 else sys.stderr)
    return code


def cmd_ui(args: argparse.Namespace) -> int:
    """Bound a UI task to one declared surface and keep it inside that contract."""
    project = present_project(args.name, args.workspace)
    if args.ui_action == "init":
        contract = ui_contract.scaffold_contract(project.path, args.surface,
                                                 fast=args.fast, paths=args.paths,
                                                 snapshot=args.snapshot)
        command = contract["commands"]["fast"]
        print(f"[OK] Wrote {ui_contract.CONTRACT_REL} for surface '{args.surface}' "
              f"with fast proof '{command}'. Review and commit it, then run `ui begin`.")
        return 0
    if args.ui_action == "begin":
        task = ui_contract.begin(project.path, args.surface)
        print(f"[OK] UI task opened on '{args.surface}' from "
              f"{str(task['baseline_commit'])[:12]}; edit only the contract surface.")
        return 0
    if args.ui_action == "allow":
        ui_contract.allow(project.path, args.pattern, args.reason)
        print(f"[OK] Inventory removals matching '{args.pattern}' are intended: {args.reason}")
        return 0
    if args.ui_action in ("verify", "finish"):
        before = None
        if args.ui_action == "finish":
            try:
                before = ui_contract.read_task(project.path)
            except ProjectError:
                before = None
            findings = ui_contract.finish(project.path, reviewed=args.reviewed,
                                          reviewer=getattr(args, "reviewer", "") or "")
        else:
            try:
                findings = ui_contract.verify(project.path)
            except ProjectError as exc:
                if getattr(args, "json", False):
                    print(json.dumps({"ok": False, "surface": None,
                                      "error": {"code": "ui.error", "message": str(exc)}},
                                     indent=2))
                    return getattr(exc, "exit_code", 1)
                raise
        if args.ui_action == "verify":
            contract = ui_contract.load_contract(project.path)
            style_lint = "on" if contract.theme_paths else "off"
        else:
            style_lint = ""
        if args.ui_action == "verify" and getattr(args, "json", False):
            payload = {"ok": not findings, "findings": ui_contract.findings_payload(findings),
                       "style_lint": style_lint}
            try:
                payload["surface"] = ui_contract.read_task(project.path).get("surface")
            except ProjectError:
                payload["surface"] = None
            print(json.dumps(payload, indent=2))
            return 0 if not findings else 1
        if args.ui_action == "verify" and style_lint == "off":
            print("[INFO] style lint: off (no style.theme_paths declared).")
        for finding in findings:
            print(f"[FAIL] {finding}")
        if findings:
            print("Error: the UI change is outside its contract.", file=sys.stderr)
            print("Why: a UI task proves one reviewed surface, not an unbounded rewrite.",
                  file=sys.stderr)
            print(f"Fix: revert the listed paths, record intended removals with "
                  f"`python aikit.py ui allow {project.name} <pattern> --reason <why>`, or run "
                  f"`python aikit.py ui abort {project.name}` to restore the surface; "
                  "then rerun.", file=sys.stderr)
            if args.ui_action == "finish":
                print("Fix: `ui finish` also needs --reviewed after a human looked at "
                      "the running UI.", file=sys.stderr)
            return 1
        print(f"[OK] UI surface verified for '{project.name}'." if args.ui_action == "verify"
              else f"[OK] UI task closed for '{project.name}'.")
        # The closing report names what the task was allowed to remove: an allow decision that is
        # never read back is an unreviewed control loss (ADR-171).
        for entry in ui_contract.allowed_removal_entries(before or {}):
            print(f"[NOTE] allowed removal '{entry['pattern']}': {entry['reason']}")
        return 0
    if args.ui_action == "abort":
        result = ui_contract.abort(project.path)
        if result["backup"]:
            print(f"[OK] Restored {len(result['restored'])} path(s); backup: {result['backup']}")
        else:
            print("[OK] Restored 0 path(s); there was nothing to back up.")
        if result["skipped"]:
            print("[WARN] Left outside the surface: " + ", ".join(result["skipped"]),
                  file=sys.stderr)
        return 0
    info = ui_contract.status(project.path)
    print(f"Surface:  {info['surface']}")
    print(f"Baseline: {str(info['baseline_commit'])[:12]}")
    print(f"Strikes:  {info['strikes']}")
    print("Changed:  " + (", ".join(info["changed"]) if info["changed"] else "none"))
    return 0


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
    "ui": cmd_ui,
}


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return HANDLERS[args.command](args)
    except ProjectError as error:
        return report_error(error)
    except UnsupportedLedgerVersion as error:
        print(f"[LEDGER VERSION REFUSED] {error}", file=sys.stderr)
        return 1
    except OSError as error:
        return report_error(ProjectError(
            "a filesystem operation failed",
            f"the operating system denied or interrupted it: {error}",
            "check the path permissions and free space, then retry; never delete a state file "
            "that cannot be read.",
        ))
