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
from typing import Dict, List, Optional

from scripts.aikit_parser import TriadArgumentParser, build_parser, report_error  # re-exported
from scripts.disruption_recovery import (
    UnsupportedLedgerVersion,
    LedgerOwnershipError,
    checkpoint_command,
    clean_dangling_temp_files,
    format_resume_report,
    mark_task_completed,
    report_ownership,
    resolve_agent,
    run_disruption_audit,
    workspace_ledger_path,
)
from scripts.project_license import (
    TIER_RESTRICTED,
    license_state,
    public_remote_refusal,
    restrict_project,
)
from scripts.project_publish import (
    auto_push_project,
    get_project_repo_url,
    publish_project,
)

from scripts.project_registry import (
    Project,
    ProjectError,
    add_aikit_badge,
    add_guideline,
    attach_project,
    create_project,
    find_project,
    latest_decision,
    list_projects,
    load_config,
    migrate_aikit_links,
    normalize_topics,
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
    Whether the project's tree and ledger are delivery-ready, decided once for every surface.

    `status --exit-code` and `status --json` both read this. Computing the same verdict twice is
    the defect class ADR-155 and ADR-161 each had to repair, where two readiness surfaces
    disagreed about one tree and auto-push followed the laxer one (ADR-172). A ledger error is a
    failed audit, not a clean tree, so it is part of the verdict (ADR-177).
    """
    dirty = (audit.get("modified_files") or audit.get("untracked_files")
             or audit.get("conflicted_files"))
    return not (audit.get("git_missing") or audit.get("ledger_error") or dirty or open_ui_task)


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
    # Checked before anything is created: alone, --public was silently ignored (ADR-192).
    if getattr(args, "public", False) and not getattr(args, "publish", False):
        return report_error(ProjectError(
            "--public needs --publish.",
            "--public sets the visibility of the GitHub repository that --publish creates; "
            "without --publish no repository is created.",
            f"add --publish, or create the project now and run `python aikit.py publish {args.name} "
            "--public` later.",
            exit_code=2,
        ))
    # `new --publish` uploads only AIKit's starter files, so it skips publish's gates, which the
    # seed's <FILL: markers would always fail; a repository still never starts undescribed (ADR-205).
    if getattr(args, "publish", False) and not getattr(args, "description", None):
        return report_error(ProjectError(
            "--publish needs --description.",
            "the GitHub repository --publish creates takes its description from the new README, "
            "which has none until --description gives it one.",
            f'add --description "<one line, 10-350 characters>", or create the project now and run '
            f"`python aikit.py publish {args.name}` once its README is filled.",
            exit_code=2,
        ))
    root = create_project(args.name, args.test, workspace=args.workspace,
                          description=args.description, topics=args.topic)
    print(f"[OK] Created project '{args.name}' at {root}")
    if getattr(args, "publish", False):
        print(f"Publishing '{args.name}' to GitHub:")
        code, report = publish_project(root, args.name, public=getattr(args, "public", False),
                                       topics=normalize_topics(args.topic))
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
    # The gates are the project's own commands; a process boundary is no security boundary (ADR-207).
    print("     Note: check, fix and publish run this project's own commands under your account, "
          "unsandboxed; attach only repositories you trust.")
    # An integrated project says so and links to AIKit; the edit is the user's to commit (ADR-202).
    if migrate_aikit_links(folder):
        print("     Updated the README's pre-move AIKit link (uncommitted; review and commit it).")
    elif add_aikit_badge(folder):
        print("     Added the AIKit Integrated badge under the README title (uncommitted; review and "
              "commit it).")
    elif not (folder / "README.md").is_file():
        print(f"     No README.md: `python aikit.py fix {name}` writes one with the AIKit Integrated badge.")
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
        clean = project_is_clean(audit, open_ui_task)
        print(json.dumps({
            "ok": True,
            "clean": clean,
            "project": project_payload(project),
            "disruption": audit,
            "ui_task_open": open_ui_task,
            "gates": [gate.name for gate in resolve_gates(project)],
        }, indent=2, default=str))
        if audit.get("ledger_error"):
            return 1
        if getattr(args, "exit_code", False) and not clean:
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
                              handoff=args.handoff, agent=args.agent, take_over=args.take_over)


def cmd_complete(args: argparse.Namespace) -> int:
    project = present_project(args.name, args.workspace)
    try:
        writer = resolve_agent(args.agent)
    except ValueError as error:
        return report_error(ProjectError(str(error), "the ledger names the agent behind every write (ADR-209).",
                                         "pass --agent <host>:<session>, or set AIKIT_AGENT.", exit_code=2))
    try:
        completed = mark_task_completed(args.task, ledger_file=workspace_ledger_path(project.path),
                                        agent=writer, take_over=args.take_over)
    except LedgerOwnershipError as error:
        return report_ownership(error)
    if completed:
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
    # A restricted project may be pushed only to a private repository (ADR-214); checked before the
    # gates so a refused push costs nothing.
    if getattr(args, "push", False):
        refusal = public_remote_refusal(project.path, project.name)
        if refusal:
            return report_error(refusal)
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
    # Pushing is opt-in. check is the documented Phase 4, and it used to publish unpushed commits
    # whenever its gates passed, so an agent whose host allows a push only on request pushed
    # without one (PRINCIPLE-018 R4, ADR-185).
    # A push that was asked for and did not happen is an operational failure, exit 1: while the push
    # was implicit a warning was enough, but a caller that passed --push reads exit 0 as "pushed"
    # (PRINCIPLE-011 R5, ADR-187).
    if getattr(args, "push", False):
        if dirty:
            print("Error: uncommitted changes or unresolved conflicts exist; skipping the push.",
                  file=sys.stderr)
            print("Why: a push must upload the tree the gates verified, not a working copy that "
                  "differs from it.", file=sys.stderr)
            print("Fix: commit or resolve the changes and run `check --strict` before pushing.",
                  file=sys.stderr)
            return 1
        push_code, push_report = auto_push_project(project.path, project.name)
        if push_code != 0:
            print(push_report, file=sys.stderr)
            return 1
        if push_report:
            print(push_report)
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
    if seed_readme(project.path, project.name, project.test_command, integrated=project.attached):
        fixes.append("seeded README.md from the project template (complete it by hand)")
    if migrate_aikit_links(project.path):
        fixes.append("updated the README's pre-move AIKit link")
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
    # A restricted project is not distributed: a public repository would hand it out (ADR-214).
    if args.public and license_state(project.path).tier == TIER_RESTRICTED:
        return report_error(ProjectError(
            f"'{project.name}' is in the restricted tier; publish --public is refused.",
            "a restricted project is All Rights Reserved and must not be made available to the public.",
            "publish it without --public to a private repository, or keep it local.",
            exit_code=2,
        ))
    # An existing origin is pushed as it is, so its visibility must be private too.
    if get_project_repo_url(project.path):
        refusal = public_remote_refusal(project.path, project.name)
        if refusal:
            return report_error(refusal)
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
    # `new` records the topics; a project.json from before ADR-199 has none (ADR-200).
    config = load_config(project.path)
    code, report = publish_project(project.path, project.name, public=args.public,
                                   topics=config.get("topics") or ["aikit"])
    print(report, file=sys.stdout if code == 0 else sys.stderr)
    return code


def cmd_license(args: argparse.Namespace) -> int:
    project = present_project(args.name, args.workspace)
    already = license_state(project.path).tier == TIER_RESTRICTED
    state = restrict_project(project.path, project.name) if args.restrict else license_state(project.path)
    print(f"License tier of '{project.name}': {state.tier}")
    if state.tier != TIER_RESTRICTED:
        if not args.restrict:
            print(f"     Restrict it with `python aikit.py license {project.name} --restrict`.")
        return 0
    print(f"     Cutoff: commit {state.since_commit[:12]} on {state.since}.")
    print("     Versions up to that commit stay under the license they were released with.")
    if args.restrict and not already:
        print("Next, outside AIKit:")
        print(f"  1. Review and commit LICENSE, README.md and the removed COMMERCIAL.md in {project.path}.")
        print("  2. Make the GitHub repository private: `gh repo edit --visibility private "
              "--accept-visibility-change-consequences`.")
        print("  3. Remove public releases, packages and download links of later versions.")
        print("  4. Tell Aegean Commercial License (ACL-1.0) holders whether later versions are covered.")
    return 0


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
        # finish() reports a missing review only after verify() found nothing, so when that is the
        # sole finding the change is inside its contract. The contract advice below would say the
        # opposite and lead with `ui abort`, which reverts valid work. Keyed on the stable finding
        # code, not the message text, so the JSON contract and this branch cannot drift apart.
        if findings and all(ui_contract.finding_code(f) == "ui.review-missing" for f in findings):
            print("Error: the UI change passed verification; only the human review is missing.",
                  file=sys.stderr)
            print("Why: a UI task closes only after a person has looked at the running surface.",
                  file=sys.stderr)
            print(f"Fix: look at the running UI, then run `python aikit.py ui finish "
                  f"{project.name} --reviewed` (add --reviewer <name> to record who).",
                  file=sys.stderr)
            return 1
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
    "license": cmd_license,
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
