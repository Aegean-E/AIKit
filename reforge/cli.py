"""The Reforge command grammar, shared by `python -m reforge` and `aikit.py reforge`."""

import argparse
import json
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from reforge.errors import ReforgeError

GateRunner = Callable[[], Tuple[bool, Sequence[str]]]


def _add_run_selection(command) -> None:
    command.add_argument("--run", dest="run_id", metavar="ID",
                         help="audit run id (default: active run, else the latest)")


def _add_window_settings(command, defaults: bool) -> None:
    command.add_argument("--start", type=int, default=3 if defaults else None,
                         help="first window size, at least 2 (default 3)")
    command.add_argument("--step", type=int, default=3 if defaults else None,
                         help="commits added per stage, at least 1 (default 3)")
    command.add_argument("--stop", type=int, default=None,
                         help="stop after this window size; 0 means unlimited")


def add_commands(subparsers) -> None:
    """Declare every Reforge command once, for either top-level CLI."""
    audit = subparsers.add_parser("audit", help="analyse the next window of a run")
    audit.add_argument("target", help="registered project name or repository path")
    audit.add_argument("--json", action="store_true", help="print one machine-readable result")
    audit.add_argument("--run", dest="run_id", metavar="ID",
                       help="audit run id (default: active run, else a new run)")
    _add_window_settings(audit, defaults=False)

    for name, text in (("fix", "repair the active run's safe findings"),
                       ("run", "audit the next window, then repair it")):
        command = subparsers.add_parser(name, help=text)
        command.add_argument("target", help="registered project name or repository path")
        command.add_argument("--json", action="store_true", help="print one machine-readable result")
        _add_run_selection(command)
        command.add_argument("--no-tests", action="store_true",
                             help="do not run the project's tests after a repair")
        command.add_argument("--test-command", metavar="CMD",
                             help="run this command instead of detected unittest discovery")
        command.add_argument("--allow-dirty", action="store_true",
                             help="repair even when the tree has unrelated uncommitted work")
        command.add_argument("--gates", action="store_true",
                             help="also run the AIKit project gates when invoked from AIKit")
        command.add_argument("--commit", action="store_true",
                             help="commit the repair and audit state (explicit paths only)")
        command.add_argument("--push", action="store_true",
                             help="commit, then push without force (implies --commit)")
        if name == "run":
            _add_window_settings(command, defaults=False)

    start = subparsers.add_parser("start", help="start an independent audit run")
    start.add_argument("target")
    start.add_argument("--json", action="store_true")
    _add_window_settings(start, defaults=True)
    stop = subparsers.add_parser("stop", help="stop the active audit run and keep its history")
    stop.add_argument("target")
    stop.add_argument("--json", action="store_true")
    _add_run_selection(stop)
    resume = subparsers.add_parser("resume", help="resume a stopped audit run")
    resume.add_argument("target")
    resume.add_argument("--json", action="store_true")
    _add_run_selection(resume)
    settings = subparsers.add_parser("settings", help="change a run's step or stop window")
    settings.add_argument("target")
    settings.add_argument("--json", action="store_true")
    _add_run_selection(settings)
    _add_window_settings(settings, defaults=False)
    runs = subparsers.add_parser("runs", help="list every audit run and its status")
    runs.add_argument("target")
    runs.add_argument("--json", action="store_true")

    status = subparsers.add_parser("status", help="show the active run, next window and pending findings")
    status.add_argument("target")
    status.add_argument("--json", action="store_true")
    report = subparsers.add_parser("report", help="show every audit run and stage")
    report.add_argument("target")
    report.add_argument("--json", action="store_true")

    repo = subparsers.add_parser("repo", help="and manage Reforge's own standalone Git repository")
    actions = repo.add_subparsers(dest="repo_action", required=True)
    init = actions.add_parser("init", help="create the standalone repository from AIKit's shipped source")
    init.add_argument("path", nargs="?", type=Path, help="target folder (default: projects/aegean-reforge)")
    init.add_argument("--force", action="store_true", help="overwrite Reforge's own files in place")
    sync = actions.add_parser("sync", help="copy shipped source in one direction")
    sync.add_argument("path", nargs="?", type=Path, help="standalone repository (default: projects/aegean-reforge)")
    sync.add_argument("--direction", choices=("push", "pull"), default="push",
                      help="push: AIKit to standalone; pull: standalone to AIKit")
    sync.add_argument("--force", action="store_true", help="discard the receiving side on a conflict")
    state = actions.add_parser("status", help="compare the standalone repository with AIKit")
    state.add_argument("path", nargs="?", type=Path, help="standalone repository")
    release = actions.add_parser("release", help="create a local annotated release tag")
    release.add_argument("path", nargs="?", type=Path, help="standalone repository")
    release.add_argument("--tag", required=True, help="release tag, e.g. v0.2.0")
    release.add_argument("--message", default="", help="annotation message")
    for command in (init, sync, state, release):
        command.add_argument("--json", action="store_true", help="print one machine-readable result")


class ReforgeArgumentParser(argparse.ArgumentParser):
    """argparse whose usage errors carry the AIKit What/Why/Fix triad (PRINCIPLE-011)."""

    def error(self, message: str):
        self.print_usage(sys.stderr)
        print(f"Error: {message}", file=sys.stderr)
        print("Why: the command line does not match any Reforge command.", file=sys.stderr)
        print(f"Fix: run `{self.prog} --help` to list the valid forms.", file=sys.stderr)
        raise SystemExit(2)


def build_parser() -> argparse.ArgumentParser:
    parser = ReforgeArgumentParser(
        prog="python reforge.py",
        description="Progressive Git history auditing and autonomous safe repair. Each project "
                    "has independent runs; window N is start + step*(N-1), capped by --stop.",
    )
    commands = parser.add_subparsers(dest="command", required=True,
                                     parser_class=ReforgeArgumentParser)
    add_commands(commands)
    return parser


def _report_error(error: ReforgeError, as_json: bool) -> int:
    if as_json:
        print(json.dumps({"ok": False, "error": {
            "code": "reforge.error", "message": error.message,
            "why": error.why, "fix": error.fix,
        }}, indent=2))
    else:
        print(error.triad(), file=sys.stderr)
    return error.exit_code


def _run_line(run: Dict[str, object]) -> str:
    return (f"{run.get('id')} [{run.get('status')}] start={run.get('start')} "
            f"step={run.get('step')} stop={run.get('stop') or 'none'} "
            f"stage={run.get('stage')} pending={run.get('pending_fixable')}")


def _print_runs(runs: Sequence[Dict[str, object]]) -> None:
    if not runs:
        print("  no audit runs yet")
    for run in runs:
        print(f"  {_run_line(run)}")


def _print_findings(payload: Dict[str, object]) -> None:
    findings = payload.get("findings") or []
    plan = payload.get("plan") or {}
    print(f"Reforge {payload['mode']} {payload.get('run')} stage {payload['stage']} "
          f"(window {plan.get('window')}, {len(plan.get('new_commits') or [])} new commit(s))")
    for item in findings:
        interaction = f" [{item['interaction']}]" if item.get("interaction") else ""
        print(f"  [{item['category']}/{item['severity']}] {item['path']}:{item['line']} "
              f"{item['code']}: {item['message']}{interaction}")
        if item.get("evidence"):
            print(f"      evidence: {item['evidence']}")
    for repair in payload.get("repairs") or []:
        mark = "OK" if repair.get("applied") else "SKIP"
        print(f"  [{mark}] {repair['path']}:{repair['line']} {repair['summary']}")
    tests = payload.get("tests") or {}
    if tests:
        print(f"  [{'PASS' if tests.get('passed') else 'FAIL'}] tests: {tests.get('command')}")
    if not findings:
        print("  no introduced findings")
    if payload["mode"] == "audit" and findings:
        print(f"Next: python reforge.py fix {payload['root']} --run {payload.get('run')}")
    elif payload["mode"] in {"run", "fix"} and payload.get("repaired"):
        print(f"Next: review the patch in {payload['root']}, then commit with --commit/--push.")
    elif payload["mode"] in {"run", "fix"}:
        print("No safe automatic repair: review the evidence above and fix by hand.")
    if payload.get("run_status") == "completed":
        print(f"Run {payload.get('run')} reached its stop and is complete.")


def _start_payload(payload: Dict[str, object]) -> None:
    print(f"[OK] Started {payload['run']['id']} (start={payload['run']['start']}, "
          f"step={payload['run']['step']}, stop={payload['run']['stop'] or 'none'}).")
    _print_runs(payload.get("runs") or [])


def _workspace(args, root: Path, gate_runner: Optional[GateRunner]) -> int:
    import reforge.pipeline as pipeline
    from reforge.delivery import deliver

    action = getattr(args, "reforge_action", None) or args.command
    as_json = bool(getattr(args, "json", False))
    if action == "status":
        payload = pipeline.status_payload(root)
        if as_json:
            print(json.dumps({"ok": True, "result": payload}, indent=2))
        else:
            print(f"Repository: {payload['root']}")
            print(f"HEAD:       {payload['head'][:12] or 'none'}")
            run = payload.get("run")
            print(f"Active run: {payload.get('active_run') or 'none'}"
                  + (f" ({run['status']})" if run else ""))
            if run:
                print(f"Settings:   start={run['start']} step={run['step']} "
                      f"stop={run['stop'] or 'none'}")
            print(f"Stage:      {payload['stage']} completed; next {payload['next_stage']} "
                  f"(window {payload['next_window'] or 'none'})")
            print(f"Audited:    {payload['audited_commits']} commit(s)")
            print(f"Pending:    {payload['pending_findings']} fixable finding(s)")
            print("Runs:")
            _print_runs(payload.get("runs") or [])
        return 0
    if action == "runs":
        payload = pipeline.runs_payload(root)
        if as_json:
            print(json.dumps({"ok": True, "result": payload}, indent=2))
        else:
            print(f"Audit runs for {payload['root']}:")
            _print_runs(payload.get("runs") or [])
        return 0
    if action == "report":
        payload = pipeline.report_payload(root)
        if as_json:
            print(json.dumps({"ok": True, "result": payload}, indent=2))
        else:
            print(f"Reforge report for {payload['root']}: {len(payload['runs'])} run(s)")
            for run in payload["runs"]:
                pending = len(pipeline.pending_fixable(run))
                print(f"  {_run_line({**run, 'pending_fixable': pending})}")
                for entry in run.get("history") or []:
                    counts = ", ".join(f"{k}={v}" for k, v in
                                       sorted((entry.get("counts") or {}).items()))
                    print(f"    stage {entry['stage']} window {entry['window']}: "
                          f"{len(entry.get('new_commits') or [])} new, "
                          f"{len(entry.get('repairs') or [])} repair(s)"
                          f"{' (' + counts + ')' if counts else ''}")
        return 0
    if action == "start":
        payload = pipeline.start_audit(root, start=args.start, step=args.step, stop=args.stop)
        if as_json:
            print(json.dumps({"ok": True, "result": payload}, indent=2))
        else:
            _start_payload(payload)
        return 0
    if action == "stop":
        payload = pipeline.stop_audit(root, run_id=getattr(args, "run_id", None))
        if as_json:
            print(json.dumps({"ok": True, "result": payload}, indent=2))
        else:
            print(f"[OK] Stopped {payload['run']['id']}; its history is kept.")
            _print_runs(payload.get("runs") or [])
        return 0
    if action == "resume":
        payload = pipeline.resume_audit(root, run_id=getattr(args, "run_id", None))
        if as_json:
            print(json.dumps({"ok": True, "result": payload}, indent=2))
        else:
            print(f"[OK] Resumed {payload['run']['id']} at stage {payload['run']['stage']}.")
        return 0
    if action == "settings":
        payload = pipeline.configure_audit(root, run_id=getattr(args, "run_id", None),
                                           start=args.start, step=args.step, stop=args.stop)
        if as_json:
            print(json.dumps({"ok": True, "result": payload}, indent=2))
        else:
            print(f"[OK] {_run_line(payload['run'])}")
        return 0

    payload = pipeline.run_pipeline(
        root, mode=action, add_tests=True, run_tests=not getattr(args, "no_tests", False),
        test_command=getattr(args, "test_command", None), gate_runner=gate_runner,
        allow_dirty=getattr(args, "allow_dirty", False), run_id=getattr(args, "run_id", None),
        start=getattr(args, "start", None), step=getattr(args, "step", None),
        stop=getattr(args, "stop", None),
    )
    do_commit = bool(getattr(args, "commit", False) or getattr(args, "push", False))
    if do_commit:
        if action == "audit":
            raise ReforgeError(
                "--commit is not valid with audit.",
                "an audit changes no code; only its state file could be committed.",
                "run `fix` or `run`, then commit the repair patch.",
                exit_code=2,
            )
        run_name = payload.get("run") or "active"
        if payload.get("repaired"):
            message = f"fix(reforge): repair {run_name} stage {payload['stage']} findings"
        else:
            message = f"chore(reforge): record {run_name} stage {payload['stage']} audit"
        delivery = deliver(root, message, bool(getattr(args, "push", False)))
        payload["delivery"] = delivery[0]
        payload["delivery_lines"] = delivery[1]
    if as_json:
        print(json.dumps({"ok": True, "result": payload}, indent=2))
    else:
        _print_findings(payload)
        for line in payload.get("delivery_lines") or []:
            print(line)
    return 0


def _repo(args, aikit_root: Path) -> int:
    import reforge.repo_sync as repo_sync
    target = getattr(args, "path", None)
    source = Path(aikit_root)
    if args.repo_action == "init":
        result = repo_sync.init_repo(source, target, force=args.force)
    elif args.repo_action == "sync":
        result = repo_sync.sync_repo(source, target, direction=args.direction, force=args.force)
    elif args.repo_action == "status":
        result = repo_sync.repo_status(source, target)
    else:
        result = repo_sync.create_release(target, args.tag, args.message)
    if getattr(args, "json", False):
        print(json.dumps({"ok": True, "result": result}, indent=2))
        return 0
    if args.repo_action == "init":
        print(f"[OK] Created standalone Aegean Reforge at {result['path']} "
              f"({result['files']} files, commit {result['commit']}).")
    elif args.repo_action == "sync":
        print(f"[OK] {result['direction']} sync from {result['path']}: "
              f"{len(result['copied'])} copied, {len(result['ahead'])} already ahead.")
        for relative in result["copied"]:
            print(f"  copied {relative}")
    elif args.repo_action == "status":
        print(f"Standalone: {result['path']} (version {result['version']})")
        print(f"Differing:  {len(result['differing'])} file(s)")
        for relative in result["differing"]:
            print(f"  {relative}")
        print(f"Stale marker: {len(result['stale_marker'])}; dirty: {result['dirty']}")
    else:
        print(f"[OK] Created release tag {result['tag']}.")
        print(f"Publish it deliberately: {result['publish']}")
    return 0


def dispatch(args, aikit_root: Optional[Path] = None, project_root: Optional[Path] = None,
             gate_runner: Optional[GateRunner] = None) -> int:
    """Run one parsed request; every failure is reported as a triad or a JSON envelope."""
    as_json = bool(getattr(args, "json", False))
    try:
        command = getattr(args, "command", None)
        reforge_action = getattr(args, "reforge_action", None)
        if command == "repo" or (command == "reforge" and reforge_action == "repo"):
            return _repo(args, Path(aikit_root) if aikit_root else Path.cwd())
        root = Path(project_root) if project_root else Path(getattr(args, "target", ""))
        if not root.is_dir():
            raise ReforgeError(
                f"{root} is not a directory.",
                "Reforge audits a repository root or an AIKit project name.",
                "pass the repository path, or register the project with `aikit attach`.",
                exit_code=2,
            )
        return _workspace(args, root, gate_runner)
    except ReforgeError as error:
        if as_json:
            return _report_error(error, True)
        return _report_error(error, False)
    except OSError as error:
        return _report_error(ReforgeError(
            "a filesystem operation failed",
            f"the operating system denied or interrupted it: {error}",
            "check the path permissions and free space, then retry.",
        ), as_json)


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    return dispatch(args, aikit_root=Path(__file__).resolve().parent.parent)
