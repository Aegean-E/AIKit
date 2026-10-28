"""Orchestrates one independent audit run, its safe repairs and their verification."""

import dataclasses
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from reforge.audit import audit_window, plan_next_stage, summarize, window_for_stage
from reforge.errors import ReforgeError
from reforge.git_history import dirty_paths, head_sha
from reforge.locking import LOCK_REL, run_lock
from reforge.model import Finding, Repair, StagePlan
from reforge.repair import regression_test_path, repair_findings, repair_paths
from reforge.state import (
    DEFAULT_START,
    DEFAULT_STEP,
    STATE_REL,
    create_run,
    current_run,
    entry_from_stage,
    find_run,
    is_reforge_artifact,
    load_state,
    mark_repairs,
    pending_fixable,
    record_stage,
    resume_run,
    run_summary,
    runs_summary,
    save_state,
    stop_run,
    unrepaired_findings,
    update_settings,
)
from reforge.verification import (
    default_test_command,
    recheck_repairs,
    review_patch,
    run_test_command,
)

GateRunner = Callable[[], Tuple[bool, Sequence[str]]]


def finding_from_dict(item: Dict[str, object]) -> Finding:
    fields = {field.name for field in dataclasses.fields(Finding)}
    return Finding(**{key: value for key, value in item.items() if key in fields})


def _scanner(label: str, text: str):
    try:
        from scripts.check_secrets import scan_diff
    except ImportError:
        return []
    return scan_diff(text, label)


def _stop_value(stop: Optional[int]) -> Optional[int]:
    return None if stop in (None, 0) else int(stop)


def _snapshot(root: Path, findings: Sequence[Finding]) -> Dict[str, Optional[bytes]]:
    paths = {finding.path for finding in findings if finding.fixable}
    paths.add(str(regression_test_path(root).relative_to(root)).replace("\\", "/"))
    snapshots: Dict[str, Optional[bytes]] = {}
    for relative in paths:
        path = root / relative
        try:
            snapshots[relative] = path.read_bytes() if path.is_file() else None
        except OSError:
            snapshots[relative] = None
    return snapshots


def _restore(root: Path, snapshots: Dict[str, Optional[bytes]]) -> None:
    for relative, original in snapshots.items():
        path = root / relative
        try:
            if original is None:
                if path.exists():
                    path.unlink()
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(original)
        except OSError:
            continue


def _clean_before_repair(root: Path, allow_dirty: bool) -> None:
    if allow_dirty:
        return
    dirty = {path for path in dirty_paths(root)
             if path.replace("\\", "/") != STATE_REL.as_posix()
             and not is_reforge_artifact(path)}
    if dirty:
        shown = ", ".join(sorted(dirty)[:8])
        raise ReforgeError(
            "The working tree is not clean enough to repair.",
            f"these paths hold uncommitted work Reforge did not make: {shown}",
            "commit or stash them, then run the audit again; the audit itself changed nothing.",
        )


def _execute_repairs(root: Path, findings: Sequence[Finding], add_tests: bool,
                     run_tests: bool, test_command: Optional[str],
                     gate_runner: Optional[GateRunner]) -> Tuple[List[Repair], Dict[str, object],
                                                                  Dict[str, object]]:
    targets = [finding for finding in findings if finding.fixable and not finding.repaired]
    if not targets:
        return [], {}, {}
    snapshots = _snapshot(root, targets)
    try:
        repairs = repair_findings(root, targets, add_tests=add_tests)
        applied = [repair for repair in repairs if repair.applied]
        tests: Dict[str, object] = {}
        gates: Dict[str, object] = {}
        if applied:
            issues = recheck_repairs(root, applied)
            allowed = repair_paths(repairs, root) + [STATE_REL.as_posix(), LOCK_REL.as_posix()]
            allowed += [path for path in dirty_paths(root) if is_reforge_artifact(path)]
            issues += review_patch(root, allowed, _scanner)
            if issues:
                raise ReforgeError(
                    "The repair patch failed review.",
                    "; ".join(issues[:6]),
                    "review the listed paths and re-run; the working tree was restored.",
                )
            command = test_command or default_test_command(root)
            if run_tests and command:
                tests = run_test_command(command, root)
                if not tests.get("passed"):
                    raise ReforgeError(
                        "The repaired tree failed its tests.",
                        f"`{command}` exited {tests.get('code')}: " +
                        " | ".join(str(line) for line in (tests.get("tail") or [])[-3:]),
                        "review the test output; the repair was rolled back.",
                    )
            if gate_runner is not None:
                passed, lines = gate_runner()
                gates = {"passed": passed, "lines": list(lines)}
                if not passed:
                    raise ReforgeError(
                        "The repaired tree failed the project's quality gates.",
                        " | ".join(str(line) for line in list(lines)[-4:]),
                        "review the gates; the repair was rolled back.",
                    )
        return repairs, tests, gates
    except ReforgeError:
        _restore(root, snapshots)
        raise
    except Exception as exc:
        _restore(root, snapshots)
        raise ReforgeError(
            "The repair could not be applied.",
            f"the repair engine stopped before a reviewable patch existed: {exc}",
            "review the finding evidence, fix the source or the generated test file by hand, "
            "then run the audit again; the working tree was restored.",
        ) from exc


def _payload(root: Path, mode: str, plan: StagePlan, run: Dict[str, object],
             findings: Sequence[Finding], repairs: Sequence[Repair], tests: Dict[str, object],
             gates: Dict[str, object]) -> Dict[str, object]:
    applied = sum(1 for repair in repairs if repair.applied)
    return {
        "mode": mode,
        "root": str(root),
        "run": plan.run_id,
        "run_status": run.get("status"),
        "stage": plan.stage,
        "plan": plan.as_dict(),
        "counts": summarize(findings),
        "findings": [finding.as_dict() for finding in findings],
        "repairs": [repair.as_dict() for repair in repairs],
        "commit_paths": sorted(set(repair_paths(repairs, root)) | {STATE_REL.as_posix()}),
        "repaired": applied,
        "pending_fixable": len(pending_fixable(run)),
        "tests": tests,
        "gates": gates,
        "summary": (f"{plan.run_id} stage {plan.stage}: {len(findings)} finding(s), "
                    f"{applied} repaired, window {plan.window}"),
    }


def _review_error(run: Dict[str, object], pending: Sequence[Dict[str, object]]) -> ReforgeError:
    return ReforgeError(
        f"Audit run {run.get('id')} has {len(pending)} fixable finding(s) awaiting repair.",
        "an audit is a review in progress; starting the next stage would move its history past "
        "findings that were never repaired.",
        f"run `reforge fix <project> --run {run.get('id')}`, or `reforge stop <project> --run "
        f"{run.get('id')}` to abandon this review and start a new audit later.",
    )


def run_pipeline(root: Path, mode: str = "run", add_tests: bool = True,
                 run_tests: bool = True, test_command: Optional[str] = None,
                 gate_runner: Optional[GateRunner] = None,
                 allow_dirty: bool = False, run_id: Optional[str] = None,
                 start: Optional[int] = None, step: Optional[int] = None,
                 stop: Optional[int] = None) -> Dict[str, object]:
    """Audit the next stage (`audit`), repair the last one (`fix`), or do both (`run`)."""
    root = Path(root)
    with run_lock(root):
        state = load_state(root)
        if mode == "fix":
            run = current_run(state, run_id)
            last = run.get("last_audit")
            if not isinstance(last, dict):
                raise ReforgeError(
                    f"Audit run {run.get('id')} has no audit to fix.",
                    "`fix` repairs the findings of a run's latest completed stage.",
                    "run `audit` or `run` first; nothing was changed.",
                )
            all_findings = [finding_from_dict(item) for item in unrepaired_findings(run)]
            fixable = [item for item in all_findings if item.fixable]
            if not fixable:
                raise ReforgeError(
                    f"Audit run {run.get('id')} has no safe automatic repair left.",
                    "every remaining finding needs a human decision, or every repair is complete.",
                    f"review the evidence, then start the next audit or `reforge stop <project> "
                    f"--run {run.get('id')}`.",
                )
            plan = StagePlan(stage=int(last.get("stage") or 0), window=int(last.get("window") or 0),
                             commits=(), new_shas=tuple(last.get("new_commits") or []),
                             prior_shas=tuple(last.get("prior_commits") or []),
                             run_id=str(run.get("id") or ""),
                             start=int(run.get("start") or DEFAULT_START),
                             step=int(run.get("step") or DEFAULT_STEP),
                             stop=run.get("stop") if isinstance(run.get("stop"), int) else None)
            _clean_before_repair(root, allow_dirty)
            repairs, tests, gates = _execute_repairs(root, all_findings, add_tests, run_tests,
                                                     test_command, gate_runner)
            last["repairs"] = [repair.as_dict() for repair in repairs]
            last["tests"] = tests
            last["gates"] = gates
            save_state(root, state)
            mark_repairs(root, state, run, repairs)
            return _payload(root, mode, plan, run, all_findings, repairs, tests, gates)

        if mode not in {"audit", "run"}:
            raise ReforgeError(
                f"Unknown mode '{mode}'.",
                "Reforge supports audit, fix and run.",
                "run `--help` to list the valid commands.",
                exit_code=2,
            )
        run = find_run(state, run_id)
        if run is None:
            run = create_run(state, start if start is not None else DEFAULT_START,
                             step if step is not None else DEFAULT_STEP,
                             _stop_value(stop))
            save_state(root, state)
        elif any(value is not None for value in (start, step, stop)):
            raise ReforgeError(
                f"Audit run {run.get('id')} already has its window settings.",
                "a run keeps the start/step/stop it was created with so its stages stay explainable.",
                f"change them with `reforge settings <project> --run {run.get('id')}`, "
                "or start a new run.",
                exit_code=2,
            )
        pending = pending_fixable(run)
        if pending:
            raise _review_error(run, pending)
        plan = plan_next_stage(root, run)
        findings = audit_window(root, plan, run.get("history") or [])
        if mode == "audit":
            entry = entry_from_stage(plan, findings, [])
            record_stage(root, state, run, entry)
            return _payload(root, mode, plan, run, findings, [], {}, {})
        _clean_before_repair(root, allow_dirty)
        repairs, tests, gates = _execute_repairs(root, findings, add_tests, run_tests,
                                                 test_command, gate_runner)
        entry = entry_from_stage(plan, findings, repairs, tests, gates)
        record_stage(root, state, run, entry)
        mark_repairs(root, state, run, repairs)
        return _payload(root, mode, plan, run, findings, repairs, tests, gates)


def start_audit(root: Path, start: Optional[int] = None, step: Optional[int] = None,
                stop: Optional[int] = None) -> Dict[str, object]:
    """Create a new independent run, refusing while another run is still active."""
    root = Path(root)
    with run_lock(root):
        state = load_state(root)
        active = find_run(state)
        if active is not None and active.get("status") == "active":
            raise ReforgeError(
                f"Audit run {active.get('id')} is still active.",
                "two runs in one project would interleave their stage windows and patches.",
                f"finish or stop it first: `reforge stop <project> --run {active.get('id')}`, "
                "or use a different project; each project has its own lock and state.",
            )
        run = create_run(state, start if start is not None else DEFAULT_START,
                             step if step is not None else DEFAULT_STEP, _stop_value(stop))
        save_state(root, state)
        return {"mode": "start", "root": str(root), "run": run_summary(run),
                "runs": runs_summary(state)}


def stop_audit(root: Path, run_id: Optional[str] = None) -> Dict[str, object]:
    root = Path(root)
    with run_lock(root):
        state = load_state(root)
        run = current_run(state, run_id)
        stopped = stop_run(root, state, run)
        return {"mode": "stop", "root": str(root), "run": run_summary(stopped),
                "runs": runs_summary(state)}


def resume_audit(root: Path, run_id: Optional[str] = None) -> Dict[str, object]:
    root = Path(root)
    with run_lock(root):
        state = load_state(root)
        run = current_run(state, run_id)
        resumed = resume_run(root, state, run)
        return {"mode": "resume", "root": str(root), "run": run_summary(resumed),
                "runs": runs_summary(state)}


def configure_audit(root: Path, run_id: Optional[str] = None, start: Optional[int] = None,
                    step: Optional[int] = None, stop: Optional[int] = None) -> Dict[str, object]:
    root = Path(root)
    with run_lock(root):
        state = load_state(root)
        run = current_run(state, run_id)
        changes: Dict[str, object] = {}
        if start is not None:
            changes["start"] = start
        if step is not None:
            changes["step"] = step
        if stop is not None:
            changes["stop"] = _stop_value(stop)
        updated = update_settings(root, state, run, **changes)
        return {"mode": "settings", "root": str(root), "run": run_summary(updated),
                "runs": runs_summary(state)}


def runs_payload(root: Path) -> Dict[str, object]:
    root = Path(root)
    state = load_state(root)
    return {"root": str(root), "active_run": state.get("active_run"),
            "last_run": state.get("last_run"), "runs": runs_summary(state)}


def status_payload(root: Path) -> Dict[str, object]:
    root = Path(root)
    state = load_state(root)
    run = find_run(state)
    stage = int((run or {}).get("stage") or 0)
    pending = len(pending_fixable(run)) if run else 0
    next_window = None
    if run and run.get("status") == "active":
        next_window = window_for_stage(stage + 1, int(run.get("start") or DEFAULT_START),
                                       int(run.get("step") or DEFAULT_STEP),
                                       run.get("stop") if isinstance(run.get("stop"), int) else None)
    return {
        "root": str(root),
        "head": head_sha(root),
        "stage": stage,
        "next_stage": stage + 1,
        "next_window": next_window,
        "audited_commits": len((run or {}).get("audited_commits") or []),
        "pending_findings": pending,
        "active_run": state.get("active_run"),
        "last_run": state.get("last_run"),
        "run": run_summary(run) if run else None,
        "runs": runs_summary(state),
        "last_audit": (run or {}).get("last_audit"),
        "history": len((run or {}).get("history") or []),
    }


def report_payload(root: Path) -> Dict[str, object]:
    root = Path(root)
    state = load_state(root)
    return {
        "root": str(root),
        "active_run": state.get("active_run"),
        "last_run": state.get("last_run"),
        "runs": list(state.get("runs") or []),
    }
