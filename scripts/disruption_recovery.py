#!/usr/bin/env python3
"""
Disruption Recovery & Task Progress Ledger (PRINCIPLE-006, PRINCIPLE-013)
Maintains persistent, atomic task checkpoints to prevent progress loss
during sudden electricity outages, OS crashes, or abrupt session terminations.
Zero external dependencies (uses standard library only).
"""

import os
import sys
import json
import time
import shutil
import contextlib
import subprocess
from pathlib import Path
from typing import Callable, Dict, Any, Optional, List, Tuple

# Safe terminal encoding on Windows (cp1254/cp1252)
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT_DIR / ".agents"
LEDGER_PATH = AGENTS_DIR / "task_ledger.json"


def get_ledger_path(custom_dir: Optional[Path] = None) -> Path:
    """Return path to task ledger, creating parent directories if needed."""
    target_dir = custom_dir or AGENTS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir / "task_ledger.json"


@contextlib.contextmanager
def file_lock(lock_path: Path, timeout_seconds: float = 3.0, poll_interval: float = 0.05):
    """
    Cross-platform cooperative advisory lock (PRINCIPLE-013).
    Uses an atomic lockfile with PID and timestamp; automatically breaks stale locks older than 30s.
    """
    lock_file = lock_path.with_suffix(lock_path.suffix + ".lock")
    # The lock may be taken before the state file's directory exists (first run / fresh adopter)
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    start_time = time.time()
    acquired = False

    while time.time() - start_time < timeout_seconds:
        try:
            fd = os.open(str(lock_file), os.O_CREAT | os.O_EXCL | os.O_RDWR)
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(f"{os.getpid()}:{int(time.time())}\n")
                f.flush()
            acquired = True
            break
        except FileExistsError:
            try:
                mtime = lock_file.stat().st_mtime
                if time.time() - mtime > 30.0:
                    # Steal the stale lock via an atomic rename so that two processes racing to
                    # break the same lock cannot both declare themselves the winner.
                    claim = lock_file.with_suffix(lock_file.suffix + f".steal_{os.getpid()}")
                    try:
                        os.replace(lock_file, claim)
                    except OSError:
                        time.sleep(poll_interval)
                        continue
                    # Exactly one racer wins the rename; the winner clears its claim and retries.
                    try:
                        claim.unlink(missing_ok=True)
                    except OSError:
                        pass
                    continue
            except OSError:
                pass
            time.sleep(poll_interval)

    try:
        yield acquired
    finally:
        if acquired:
            try:
                lock_file.unlink(missing_ok=True)
            except OSError:
                pass


LOCK_TIMEOUT_SECONDS = 3.0


@contextlib.contextmanager
def locked_ledger(ledger_file: Optional[Path] = None, timeout_seconds: float = LOCK_TIMEOUT_SECONDS):
    """
    Serialize a full read-modify-write cycle on the task ledger (PRINCIPLE-013 Rule 3).

    Yields the loaded ledger; the caller mutates it in place and the ledger is saved on clean
    exit, all while holding the advisory lock. Without this, parallel subagents interleave
    load/save cycles and silently erase each other's checkpoints (lost-update race).

    Contention is surfaced, never swallowed: if the lock cannot be acquired within the bounded
    timeout the mutation is abandoned with a diagnostic rather than written unprotected.
    """
    path = Path(ledger_file) if ledger_file is not None else LEDGER_PATH
    with file_lock(path, timeout_seconds=timeout_seconds) as acquired:
        if not acquired:
            raise TimeoutError(
                f"[PRINCIPLE-013 LOCK CONTENTION] Could not acquire advisory lock on "
                f"{path.name} within {timeout_seconds}s. "
                f"Why: another agent or process is mid-write on the ledger. "
                f"Fix: retry shortly, or remove a stale '{path.name}.lock' if no process is active."
            )
        ledger = load_ledger(path)
        yield ledger
        save_ledger(ledger, path, _locked=True)


def fsync_dir(dir_path: Path) -> bool:
    """
    Flush a directory entry so a completed `os.replace` survives power loss (PRINCIPLE-013 R1).

    Fsyncing the file alone is not enough on POSIX journalling filesystems (ext4 `data=ordered`,
    XFS): the data is durable but the *rename* may still sit in an unflushed directory entry, so
    a crash can revert the file to its previous contents. Windows exposes no directory handle to
    sync and `os.replace` is already metadata-atomic there, so this is a no-op on win32.

    Returns True when the directory was synced or syncing is not applicable.
    """
    if sys.platform == "win32":
        return True
    fd = None
    try:
        fd = os.open(str(dir_path), os.O_RDONLY)
        os.fsync(fd)
        return True
    except OSError as e:
        # Some filesystems (network mounts, overlayfs) refuse directory fsync; the replace has
        # already happened, so degrade with a diagnostic rather than failing the write.
        sys.stderr.write(f"[WARN] Could not fsync directory {dir_path} for durability: {e}\n")
        return False
    finally:
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass


def check_disk_headroom(target_dir: Path, min_mb: float = 10.0) -> bool:
    """Check whether sufficient disk headroom exists before writing (PRINCIPLE-013)."""
    try:
        usage = shutil.disk_usage(str(target_dir.resolve()))
        free_mb = usage.free / (1024 * 1024)
        if free_mb < min_mb:
            sys.stderr.write(f"[WARN] Low disk space: {free_mb:.1f}MB remaining (minimum {min_mb}MB required)\n")
            return False
        return True
    except Exception:
        return True


def migrate_ledger_schema(data: Any) -> Dict[str, Any]:
    """
    Ensure recovered or loaded ledger conforms to current schema specification (PRINCIPLE-013).
    Performs forward-compatible, idempotent schema upgrades.
    """
    if not isinstance(data, dict):
        return {"version": 1, "active_task": None, "checkpoints": []}

    # Ensure mandatory fields
    if "version" not in data:
        data["version"] = 1
    if "active_task" not in data:
        data["active_task"] = None
    if "checkpoints" not in data or not isinstance(data["checkpoints"], list):
        data["checkpoints"] = []

    # In-place normalization of active_task
    if isinstance(data.get("active_task"), dict):
        at = data["active_task"]
        if "status" not in at:
            at["status"] = "in_progress"
        if "active_phase" not in at:
            at["active_phase"] = 1

    return data


def atomic_write_json(file_path: Path, data: Any, max_retries: int = 5, min_headroom_mb: float = 10.0) -> None:
    """Atomically write JSON data using fsync, shadow backup, and temporary replacement (PRINCIPLE-013)."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    if not check_disk_headroom(file_path.parent, min_mb=min_headroom_mb):
        sys.stderr.write(f"[WARN] Insufficient storage headroom for atomic write: {file_path.name}\n")
        raise OSError(28, "No space left on device (ENOSPC headroom guard)")

    tmp_path = file_path.with_suffix(file_path.suffix + f".tmp_{os.getpid()}_{int(time.time() * 1000)}")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())

        # Rotate existing valid file to shadow backup (.bak) prior to replacement
        if file_path.exists():
            bak_path = file_path.with_suffix(file_path.suffix + ".bak")
            try:
                shutil.copy2(file_path, bak_path)
            except OSError:
                pass

        # Windows lock-contention retry loop on os.replace
        for attempt in range(max_retries):
            try:
                os.replace(tmp_path, file_path)
                break
            except (PermissionError, OSError):
                if attempt == max_retries - 1:
                    raise
                time.sleep(0.02 * (2 ** attempt))

        # Durability barrier: make the rename itself survive a power cut (PRINCIPLE-013 R1)
        fsync_dir(file_path.parent)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:
                pass
        raise


def load_ledger(ledger_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    Safely load the task ledger with startup self-healing (PRINCIPLE-013).
    Quarantines corrupted files from power outages, restores from shadow backup, and migrates schema.
    """
    path = Path(ledger_file) if ledger_file is not None else LEDGER_PATH
    if not path.exists():
        return {"version": 1, "active_task": None, "checkpoints": []}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return migrate_ledger_schema(data)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
        # Quarantine corrupted artifact
        corrupt_name = f"{path.name}.corrupt_{int(time.time())}"
        corrupt_path = path.parent / corrupt_name
        try:
            os.replace(path, corrupt_path)
            sys.stderr.write(f"[WARN] Corrupted task ledger quarantined to {corrupt_name}: {e}\n")
        except OSError:
            pass

        # Attempt recovery from shadow backup (.bak) before falling back to empty state
        bak_path = path.with_suffix(path.suffix + ".bak")
        if bak_path.exists():
            try:
                with open(bak_path, "r", encoding="utf-8") as f_bak:
                    recovered = json.load(f_bak)
                    sys.stderr.write(f"[INFO] Recovered task ledger from shadow backup {bak_path.name}\n")
                    return migrate_ledger_schema(recovered)
            except Exception:
                pass

        return {"version": 1, "active_task": None, "checkpoints": []}


DEFAULT_MAX_CHECKPOINTS = 20


def prune_checkpoints(
    checkpoints: List[Dict[str, Any]],
    active_task_id: Optional[str] = None,
    max_history: int = DEFAULT_MAX_CHECKPOINTS,
) -> List[Dict[str, Any]]:
    """Prune checkpoints to maintain a bounded rolling memory window (PRINCIPLE-004)."""
    if len(checkpoints) <= max_history:
        return checkpoints

    active_cps = [c for c in checkpoints if active_task_id and c.get("task_id") == active_task_id]
    inactive_cps = [c for c in checkpoints if not active_task_id or c.get("task_id") != active_task_id]

    keep_inactive = max(5, max_history - len(active_cps))
    pruned_inactive = inactive_cps[-keep_inactive:]
    combined = active_cps + pruned_inactive
    return sorted(combined, key=lambda x: x.get("timestamp", 0))


def save_ledger(
    ledger: Dict[str, Any],
    ledger_file: Optional[Path] = None,
    max_history: int = DEFAULT_MAX_CHECKPOINTS,
    _locked: bool = False,
) -> None:
    """
    Save the task ledger atomically to disk with bounded rolling history (PRINCIPLE-004).

    Acquires the advisory lock unless the caller already holds it (`_locked=True`, set by
    `locked_ledger`), since the lock is not reentrant.
    """
    path = Path(ledger_file) if ledger_file is not None else LEDGER_PATH
    active_id = ledger.get("active_task", {}).get("task_id") if ledger.get("active_task") else None
    if "checkpoints" in ledger:
        ledger["checkpoints"] = prune_checkpoints(
            ledger["checkpoints"], active_task_id=active_id, max_history=max_history
        )
    if _locked:
        atomic_write_json(path, ledger)
        return
    with file_lock(path, timeout_seconds=LOCK_TIMEOUT_SECONDS) as acquired:
        if not acquired:
            sys.stderr.write(
                f"[WARN] Writing {path.name} without the advisory lock after "
                f"{LOCK_TIMEOUT_SECONDS}s of contention (PRINCIPLE-013 Rule 3).\n"
            )
        atomic_write_json(path, ledger)



PHASE_MAPPING = {
    "phase 1": 1,
    "grounding": 1,
    "phase 2": 2,
    "orientation": 2,
    "planning": 2,
    "phase 3": 3,
    "architecture": 3,
    "implementation": 3,
    "phase 4": 4,
    "verification": 4,
    "testing": 4,
    "dogfooding": 4,
    "phase 5": 5,
    "delivery": 5,
    "sync": 5,
    "completed": 5,
}


def resolve_phase_num(phase: str, explicit_num: Optional[int] = None) -> int:
    """Resolve lifecycle phase number 1..5 for compaction orientation (PRINCIPLE-002)."""
    if explicit_num is not None and 1 <= explicit_num <= 5:
        return explicit_num
    normalized = phase.strip().lower()
    # A bare digit is the phase itself. PRINCIPLE-007 R6 documents `--phase 2`, and "2" matched
    # none of the phase words below, so that checkpoint was recorded as Phase 1.
    if normalized in {"1", "2", "3", "4", "5"}:
        return int(normalized)
    for key, num in PHASE_MAPPING.items():
        if key in normalized:
            return num
    return 1


# git-status(1) unmerged (conflict) codes. Closed set: 'AA' and 'DD' contain no 'U'.
UNMERGED_CODES = frozenset({"DD", "AU", "UD", "UA", "DU", "AA", "UU"})


def classify_git_status(porcelain_output: str) -> Dict[str, List[str]]:
    """
    Classify `git status --porcelain` v1 output into disruption categories (PRINCIPLE-006 R2).

    Pure domain logic, kept free of subprocess I/O so every porcelain state can be verified
    deterministically. Porcelain v1 emits a two-character XY code (X = index, Y = worktree). A
    closed whitelist of codes silently dropped 10 of 16 real states - every merge-conflict state
    among them - which made the mandatory cold-start audit report a conflicted tree as clean.

    Classification is therefore exhaustive by construction:
      '??' -> untracked, '!!' -> ignored (skipped), one of git's 7 unmerged codes -> unresolved
      conflict, any other non-blank code -> surviving uncommitted work.

    The unmerged set is closed and taken from git-status(1); note that 'AA' (both added) and
    'DD' (both deleted) are conflicts despite containing no 'U', so a 'U'-substring test is not
    sufficient. The modified bucket stays open-ended so future codes can never vanish.
    """
    result: Dict[str, List[str]] = {"modified": [], "untracked": [], "conflicted": []}
    for raw_line in porcelain_output.splitlines():
        if not raw_line or len(raw_line) < 4:
            continue
        xy = raw_line[:2]
        file_rel = raw_line[3:].strip()
        if xy == "??":
            result["untracked"].append(file_rel)
        elif xy == "!!":
            continue
        elif xy in UNMERGED_CODES:
            result["conflicted"].append(f"{xy} {file_rel}")
        elif xy.strip():
            result["modified"].append(file_rel)
    return result


def resolve_active_phase(active_task: Optional[Dict[str, Any]], default: int = 1) -> int:
    """
    Read the recorded lifecycle phase of a task (PRINCIPLE-002 R4, PRINCIPLE-004 R2).

    `record_checkpoint` persists the phase under `active_phase`. Readers previously looked for a
    `last_phase_num` key that was never written, so every resumption silently defaulted to a
    fixed phase and could send an agent *backwards* through the monotonic lifecycle. The legacy
    key is still honoured for ledgers written before this fix, and the textual phase label is the
    last resort so a phase is always recoverable.
    """
    if not active_task:
        return default
    for key in ("active_phase", "last_phase_num", "phase_num"):
        value = active_task.get(key)
        if isinstance(value, int) and 1 <= value <= 5:
            return value
    label = active_task.get("last_phase") or active_task.get("phase")
    if isinstance(label, str) and label.strip():
        return resolve_phase_num(label)
    return default


def record_checkpoint(
    task_id: str,
    phase: str,
    description: str,
    files_affected: Optional[List[str]] = None,
    status: str = "in_progress",
    ledger_file: Optional[Path] = None,
    phase_num: Optional[int] = None,
    why: Optional[str] = None,
    benefits: Optional[str] = None,
    risks: Optional[str] = None,
    mitigation: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Record an atomic micro-checkpoint in the task ledger (PRINCIPLE-002, PRINCIPLE-006, PRINCIPLE-007).
    Tracks active_phase to allow instant phase-accurate resumption after conversation compaction.
    Optionally persists pre-flight 4-quadrant impact assessment metadata (why, benefits, risks, mitigation).
    """
    resolved_phase = resolve_phase_num(phase, phase_num)
    checkpoint_entry = {
        "task_id": task_id,
        "phase": phase,
        "phase_num": resolved_phase,
        "description": description,
        "files_affected": [str(f) for f in (files_affected or [])],
        "status": status,
        "timestamp": time.time(),
        "timestamp_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
    }

    if why or benefits or risks or mitigation:
        impact = {}
        if why:
            impact["why"] = why
        if benefits:
            impact["benefits"] = benefits
        if risks:
            impact["risks"] = risks
        if mitigation:
            impact["mitigation"] = mitigation
        checkpoint_entry["impact_assessment"] = impact

    # Locked read-modify-write: parallel subagents must not interleave here (PRINCIPLE-013 R3)
    with locked_ledger(ledger_file) as ledger:
        ledger["active_task"] = {
            "task_id": task_id,
            "last_phase": phase,
            "active_phase": resolved_phase,
            "status": status,
            "updated_at": checkpoint_entry["timestamp"],
        }
        if why or benefits or risks or mitigation:
            ledger["active_task"]["impact_assessment"] = checkpoint_entry.get("impact_assessment")

        ledger.setdefault("checkpoints", []).append(checkpoint_entry)
    return checkpoint_entry


def mark_task_completed(task_id: str, ledger_file: Optional[Path] = None) -> None:
    """Mark the active task as successfully completed in the ledger (locked, PRINCIPLE-013 R3)."""
    with locked_ledger(ledger_file) as ledger:
        if ledger.get("active_task", {}).get("task_id") == task_id:
            ledger["active_task"]["status"] = "completed"
            ledger["active_task"]["active_phase"] = 5
            ledger["active_task"]["completed_at"] = time.time()

        # Also record completion checkpoint
        ledger.setdefault("checkpoints", []).append({
            "task_id": task_id,
            "phase": "completed",
            "phase_num": 5,
            "description": f"Task '{task_id}' completed successfully.",
            "status": "completed",
            "timestamp": time.time(),
            "timestamp_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        })


def reset_active_task(reason: str = "Reset by user/agent", ledger_file: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Abandon or reset the active in-progress task in the ledger (locked, PRINCIPLE-006)."""
    with locked_ledger(ledger_file) as ledger:
        active = ledger.get("active_task")
        if not active or active.get("status") != "in_progress":
            return None

        task_id = active.get("task_id", "unknown")
        active["status"] = "abandoned"
        active["abandoned_reason"] = reason
        active["abandoned_at"] = time.time()

        ledger.setdefault("checkpoints", []).append({
            "task_id": task_id,
            "phase": "abandoned",
            "phase_num": resolve_active_phase(active),
            "description": f"Task '{task_id}' abandoned: {reason}",
            "status": "abandoned",
            "timestamp": time.time(),
            "timestamp_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        })
        ledger["active_task"] = None
    return active


def clean_dangling_temp_files(workspace_dir: Optional[Path] = None) -> List[str]:
    """Scan and safely purge orphaned *.tmp_* files left by interrupted writes (PRINCIPLE-006, PRINCIPLE-013)."""
    ws = workspace_dir or ROOT_DIR
    deleted = []
    try:
        for p in ws.rglob("*.tmp_*"):
            if ".git" not in str(p) and p.is_file():
                try:
                    rel = str(p.relative_to(ws))
                    p.unlink()
                    deleted.append(rel)
                except OSError:
                    pass
    except Exception:
        pass
    return deleted


def git_porcelain_status(workspace: Path) -> Tuple[int, str, str]:
    """Default git adapter: run `git status --porcelain` in `workspace` (bounded, PRINCIPLE-010 R3)."""
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        timeout=5,
    )
    return proc.returncode, proc.stdout, proc.stderr


def run_disruption_audit(
    workspace_dir: Optional[Path] = None,
    git_status: Optional[Callable[[Path], Tuple[int, str, str]]] = None,
) -> Dict[str, Any]:
    """
    Execute a comprehensive pre-flight disruption audit (PRINCIPLE-006, PRINCIPLE-007).
    Evaluates Git working tree status, surviving uncommitted files, and ledger state.

    `git_status` is injectable (PRINCIPLE-009 R4 zero-config DI) so in-process tests can supply a
    fake instead of spawning `git`; it returns (returncode, stdout, stderr).
    """
    ws = workspace_dir or ROOT_DIR
    run_git = git_status or git_porcelain_status
    audit: Dict[str, Any] = {
        "workspace": str(ws),
        "has_uncommitted_changes": False,
        "has_conflicts": False,
        "modified_files": [],
        "untracked_files": [],
        "conflicted_files": [],
        "interrupted_task": None,
        "last_checkpoint": None,
        "clean_shutdown": True,
        "quarantined_files": [],
        "dangling_temp_files": [],
    }

    # 1. Check Git Status
    audit["git_missing"] = False
    try:
        returncode, stdout, stderr = run_git(ws)
        if returncode == 0:
            classified = classify_git_status(stdout)
            audit["modified_files"] = [f for f in classified["modified"] if f not in BOOKKEEPING_PATHS]
            audit["untracked_files"] = [f for f in classified["untracked"] if f not in BOOKKEEPING_PATHS]
            audit["conflicted_files"] = classified["conflicted"]
            audit["has_conflicts"] = bool(audit["conflicted_files"])
            audit["has_uncommitted_changes"] = bool(
                audit["modified_files"] or audit["untracked_files"] or audit["conflicted_files"]
            )
        else:
            audit["git_missing"] = True
            audit["git_error"] = stderr.strip() or f"git exit code {returncode}"
    except Exception as e:
        audit["git_missing"] = True
        audit["git_error"] = str(e)

    # 2. Check Task Ledger for Interrupted Tasks
    ledger_path = ws / ".agents" / "task_ledger.json"
    if not ledger_path.exists() and (ws / "task_ledger.json").exists():
        ledger_path = ws / "task_ledger.json"
    elif not ledger_path.exists():
        ledger_path = get_ledger_path(ws / ".agents")
    ledger = load_ledger(ledger_path)
    active = ledger.get("active_task")
    if active and active.get("status") == "in_progress":
        audit["interrupted_task"] = active
        audit["clean_shutdown"] = False

    checkpoints = ledger.get("checkpoints", [])
    if checkpoints:
        audit["last_checkpoint"] = checkpoints[-1]

    # 3. Check for Quarantined Corrupted Artifacts (.corrupt_ files)
    try:
        for p in ws.rglob("*.corrupt_*"):
            if ".git" not in str(p):
                audit["quarantined_files"].append(str(p.relative_to(ws)))
    except Exception:
        pass

    # 4. Check for Dangling Temporary Files (*.tmp_*) from interrupted atomic writes
    try:
        for p in ws.rglob("*.tmp_*"):
            if ".git" not in str(p):
                audit["dangling_temp_files"].append(str(p.relative_to(ws)))
    except Exception:
        pass

    return audit


def format_audit_report(audit: Dict[str, Any]) -> str:
    """Generate human and AI-readable disruption recovery audit report."""
    lines = [
        "============================================================",
        "⚡ DISRUPTION & PROGRESS RECOVERY AUDIT (PRINCIPLE-006)",
        "============================================================",
    ]

    if audit.get("has_conflicts"):
        lines.append("🔴 Status: UNRESOLVED MERGE CONFLICTS - resolve before any edit or commit!")
    elif audit.get("clean_shutdown") and not audit.get("has_uncommitted_changes") and not audit.get("dangling_temp_files") and not audit.get("git_missing"):
        lines.append("🟢 Status: Clean state. No interrupted tasks or uncommitted drift detected.")
    else:
        lines.append("🟡 Status: Potential disruption / in-flight state detected!")

    if audit.get("conflicted_files"):
        lines.append(f"⛔ Conflicted Files ({len(audit['conflicted_files'])}) - interrupted merge/rebase:")
        for f in audit["conflicted_files"]:
            lines.append(f"   • {f}")
        lines.append("   Fix: resolve, then 'git add <file>' — or abort via 'git merge --abort' / 'git rebase --abort'")

    if audit.get("git_missing"):
        lines.append("⚠️  Git Inactive: Not a git repository (run 'git init' to enable full tracking)")

    if audit.get("interrupted_task"):
        it = audit["interrupted_task"]
        lines.append(f"⚠️  Interrupted Task: '{it.get('task_id')}' in phase '{it.get('last_phase')}'")
    
    if audit.get("last_checkpoint"):
        lc = audit["last_checkpoint"]
        lines.append(f"📌 Last Checkpoint: [{lc.get('timestamp_str')}] {lc.get('phase')} - {lc.get('description')}")

    impact = None
    if audit.get("interrupted_task") and audit["interrupted_task"].get("impact_assessment"):
        impact = audit["interrupted_task"]["impact_assessment"]
    elif audit.get("last_checkpoint") and audit["last_checkpoint"].get("impact_assessment"):
        impact = audit["last_checkpoint"]["impact_assessment"]

    if impact:
        lines.append("🎯 Pre-Flight Impact Assessment (PRINCIPLE-007):")
        if impact.get("why"):
            lines.append(f"   • Why: {impact['why']}")
        if impact.get("benefits"):
            lines.append(f"   • Benefits: {impact['benefits']}")
        if impact.get("risks"):
            lines.append(f"   • Risks: {impact['risks']}")
        if impact.get("mitigation"):
            lines.append(f"   • Mitigation: {impact['mitigation']}")

    if audit.get("modified_files"):
        lines.append(f"📝 Modified Files ({len(audit['modified_files'])}):")
        for f in audit["modified_files"]:
            lines.append(f"   • {f}")

    if audit.get("untracked_files"):
        lines.append(f"📁 Untracked Files ({len(audit['untracked_files'])}):")
        for f in audit["untracked_files"]:
            lines.append(f"   • {f}")

    if audit.get("quarantined_files"):
        lines.append(f"🛡️  Quarantined Corrupted Files ({len(audit['quarantined_files'])}):")
        for f in audit["quarantined_files"]:
            lines.append(f"   • {f}")

    if audit.get("dangling_temp_files"):
        lines.append(f"🧹 Dangling Temp Buffers ({len(audit['dangling_temp_files'])}):")
        for f in audit["dangling_temp_files"]:
            lines.append(f"   • {f}")

    lines.append("============================================================")
    return "\n".join(lines)


def format_resume_report(audit: Dict[str, Any]) -> str:
    """Generate structured guidance for cold-starting AI agents to resume an interrupted task."""
    lines = [
        "============================================================",
        "⚡ DISRUPTION RESUMPTION GUIDANCE (PRINCIPLE-006)",
        "============================================================",
    ]
    if audit.get("conflicted_files"):
        lines.append(f"⛔ BLOCKED: {len(audit['conflicted_files'])} unresolved conflict(s) must be resolved first:")
        for f in audit["conflicted_files"]:
            lines.append(f"   • {f}")
        lines.append("   Fix: resolve and 'git add <file>', or 'git merge --abort' / 'git rebase --abort'")

    interrupted = audit.get("interrupted_task")
    if not interrupted:
        if not audit.get("conflicted_files"):
            lines.append("🟢 No interrupted task detected. Ready for a new task.")
        lines.append("============================================================")
        return "\n".join(lines)

    task_id = interrupted.get("task_id", "unknown")
    phase = interrupted.get("last_phase", "unknown")
    phase_num = resolve_active_phase(interrupted, default=2)
    # PRINCIPLE-002 R4 records a checkpoint on ENTERING a phase, so the recorded phase is the one
    # in progress: resume there. Guessing "phase + 1" when the tree was clean skipped work - after
    # a PRINCIPLE-006 milestone commit during Phase 3, it sent the agent straight to Phase 4.
    next_phase_num = phase_num
    
    lines.append(f"⚠️  RESUMING INTERRUPTED TASK: '{task_id}'")
    lines.append(f"📌 Last Active Phase: Phase {phase_num} ({phase})")
    lines.append(f"🚀 Recommended Resumption Phase: Phase {next_phase_num}")

    impact = interrupted.get("impact_assessment")
    if impact:
        lines.append("🎯 Pre-Flight Impact Assessment (PRINCIPLE-007):")
        if impact.get("why"):
            lines.append(f"   • Why: {impact['why']}")
        if impact.get("benefits"):
            lines.append(f"   • Benefits: {impact['benefits']}")
        if impact.get("risks"):
            lines.append(f"   • Risks: {impact['risks']}")
        if impact.get("mitigation"):
            lines.append(f"   • Mitigation: {impact['mitigation']}")

    if audit.get("modified_files"):
        lines.append(f"📝 Surviving Modified Files ({len(audit['modified_files'])}):")
        for f in audit["modified_files"]:
            lines.append(f"   • {f}")
    if audit.get("dangling_temp_files"):
        lines.append(f"🧹 Action Needed: Purge {len(audit['dangling_temp_files'])} dangling .tmp_* files (run 'python scripts/disruption_recovery.py --clean')")
    lines.append(f"💡 Next Action: Inspect surviving files, run unit tests, and resume at Phase {next_phase_num}")
    lines.append("============================================================")
    return "\n".join(lines)


VALID_COMMIT_TYPES = {
    "feat",
    "fix",
    "refactor",
    "docs",
    "chore",
    "test",
    "perf",
    "build",
    "ci",
}


def validate_conventional_commit(message: str) -> Tuple[bool, str]:
    """
    Validate that a commit message conforms to Conventional Commits (PRINCIPLE-018).
    Pattern: <type>[(<scope>)]: <description>
    Optionally allows milestone prefix in description: [milestone N/M]
    Returns (is_valid, reason).
    """
    if not message or not message.strip():
        return False, "Commit message cannot be empty."

    lines = message.strip().split("\n")
    subject = lines[0].strip()

    if len(subject) > 72:
        return False, f"Subject line exceeds 72 characters ({len(subject)} chars)."

    import re
    pattern = r"^([a-z]+)(?:\(([a-zA-Z0-9_\-\./]+)\))?(!)?:\s+(.+)$"
    match = re.match(pattern, subject)
    if not match:
        return False, "Message does not match Conventional Commits format: '<type>[(<scope>)]: <description>'."

    ctype, scope, breaking, desc = match.groups()
    if ctype not in VALID_COMMIT_TYPES:
        allowed = ", ".join(sorted(VALID_COMMIT_TYPES))
        return False, f"Invalid commit type '{ctype}'. Allowed types: {allowed}."

    desc = desc.strip()
    if not desc:
        return False, "Commit description cannot be empty."

    # Reject lazy anti-patterns
    anti_patterns = {"wip", "update", "fix", "fixed", "changes", "stuff", "test"}
    if desc.lower() in anti_patterns or desc.lower().rstrip(".") in anti_patterns:
        return False, f"Description '{desc}' is too generic. Provide a descriptive explanation."

    return True, "Valid conventional commit."


# Flags that consume the following argv token as their value.
# ---------------------------------------------------------------------------------------------
# Lifecycle track classification (PRINCIPLE-002 R3). Computed from the actual change set so every
# agent assigns the same track: the word lists it replaced ("typo fixes", "comment updates",
# "executable code") put the same comment-only edit in Track B for one model and C for another.
# ---------------------------------------------------------------------------------------------
TRACK_B_SUFFIXES = frozenset({".md", ".txt", ".rst"})
# Text files that are nevertheless rule text or generated from it: editing them changes how every
# agent behaves, so they are never "trivial".
TRACK_C_DOC_NAMES = frozenset({
    "GUIDELINES.md", "AGENTS.md", "CLAUDE.md", "GEMINI.md", ".cursorrules",
    "copilot-instructions.md", "principles.md", "domain.md",
})


# Bookkeeping written by AIKit's own lifecycle commands. PRINCIPLE-002 R4 requires these writes,
# so they must not move the track: before this, recording the mandated checkpoint alone turned a
# documentation-only task into Track C.
BOOKKEEPING_PATHS = frozenset({".agents/task_ledger.json"})


def _ast_without_docstrings(source: str) -> str:
    """AST dump with docstrings removed; comments and formatting never reach the AST."""
    import ast  # lazy: keeps `--help` inside the startup budget (PRINCIPLE-010 R5)
    tree = ast.parse(source)
    for node in ast.walk(tree):
        body = getattr(node, "body", None)
        if (isinstance(body, list) and body and isinstance(body[0], ast.Expr)
                and isinstance(getattr(body[0], "value", None), ast.Constant)
                and isinstance(body[0].value.value, str)):
            node.body = body[1:] or [ast.Pass()]
    return ast.dump(tree)


def classify_change(path: str, old: Optional[str], new: Optional[str]) -> Tuple[str, str]:
    """Return (track, reason) for one changed file. Pure: no I/O."""
    name = Path(path).name
    suffix = Path(path).suffix.lower()
    if name in TRACK_C_DOC_NAMES:
        return "C", "rule text or a file generated from it"
    if suffix in TRACK_B_SUFFIXES:
        return "B", "documentation"
    if suffix == ".py" and old is not None and new is not None:
        try:
            same = _ast_without_docstrings(old) == _ast_without_docstrings(new)
        except SyntaxError:
            return "C", "Python that does not parse"
        return ("B", "comments/docstrings/formatting only") if same else ("C", "code change")
    if suffix == ".py":
        return "C", "Python file added or deleted"
    return "C", "code, config, schema or test file"


def classify_track(changes: List[Tuple[str, Optional[str], Optional[str]]]) -> Tuple[str, List[str]]:
    """
    Classify a change set into Track A, B or C (PRINCIPLE-002 R3). Pure: no I/O.

    `changes` holds (path, old_text_or_None, new_text_or_None). No changes is Track A; the task's
    track is the highest track of any file; the reasons list one line per file.
    """
    if not changes:
        return "A", []
    reasons = []
    track = "B"
    for path, old, new in changes:
        file_track, reason = classify_change(path, old, new)
        reasons.append(f"{file_track}  {path}  ({reason})")
        if file_track == "C":
            track = "C"
    return track, reasons


def collect_working_changes(workspace: Path) -> List[Tuple[str, Optional[str], Optional[str]]]:
    """Read every changed, staged or untracked file versus HEAD (git adapter for --track)."""
    def git(*args):
        return subprocess.run(["git", *args], cwd=str(workspace), capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=10)
    # -z: NUL-separated and never quoted. Without it git octal-escapes non-ASCII paths, the file is
    # then "missing", and a comment-only edit to such a .py file was misread as a deletion (Track C).
    listing = git("status", "--porcelain", "-z", "--untracked-files=all")
    if listing.returncode != 0:
        raise RuntimeError(listing.stderr.strip() or "not a git repository")
    changes = []
    entries = listing.stdout.split("\0")
    i = 0
    while i < len(entries):
        raw = entries[i]
        i += 1
        if len(raw) < 4:
            continue
        xy, path = raw[:2], raw[3:]
        if "R" in xy or "C" in xy:
            i += 1  # -z puts the rename/copy source in the next field; we classify the new path
        if path in BOOKKEEPING_PATHS:
            continue
        head = git("show", f"HEAD:{path}")
        old = head.stdout if head.returncode == 0 else None
        target = workspace / path
        new = target.read_text(encoding="utf-8", errors="replace") if target.is_file() else None
        changes.append((path, old, new))
    return changes


VALUE_FLAGS = {
    "--validate-commit", "--checkpoint", "--phase", "--phase-num", "--desc",
    "--why", "--benefits", "--benefit", "--risks", "--mitigation",
    "--complete", "--reset", "--workspace",
}
# Standalone action flags.
ACTION_FLAGS = {"--clean", "--resume", "--audit", "--track", "--help", "-h"}
KNOWN_FLAGS = VALUE_FLAGS | ACTION_FLAGS

HELP_TEXT = """AIKit Disruption Recovery & Task Ledger (PRINCIPLE-006, PRINCIPLE-013)

Usage:
  py scripts/disruption_recovery.py [ACTION] [OPTIONS]

Actions (default: --audit):
  --audit                    Report working-tree drift, dangling buffers, and ledger state
  --resume                   Print the resumption report for an interrupted task
  --clean                    Purge orphaned temporary buffers (*.tmp_*)
  --checkpoint <task_id>     Record a task checkpoint in .agents/task_ledger.json
  --complete <task_id>       Mark a task as completed
  --reset [reason]           Abandon and clear the active task
  --validate-commit <msg>    Validate a Conventional Commit message (PRINCIPLE-018)
  --track                    Print the lifecycle track (A/B/C) of the current changes (PRINCIPLE-002 R3)

Workspace:
  --workspace <dir>          Operate on <dir>/.agents/task_ledger.json instead of this
                             repository's ledger. Required for sandboxed dogfooding, which
                             must never mutate the host repo (PRINCIPLE-015 R4).

Checkpoint options:
  --phase <name>             Lifecycle phase label (e.g. planning, implementation)
  --phase-num <1-5>          Numeric lifecycle phase for compaction resumption
  --desc <text>              Checkpoint description
  --why <text>               Pre-flight impact: root cause / user goal (PRINCIPLE-007)
  --benefits <text>          Pre-flight impact: expected benefits
  --risks <text>             Pre-flight impact: blast-radius risks
  --mitigation <text>        Pre-flight impact: risk mitigations
  -h, --help                 Show this help message and exit

Exit codes:
  0  success    1  operational failure    2  CLI argument misuse
"""


def validate_argv(argv: List[str]) -> List[str]:
    """Return unrecognized options, skipping values of known value-taking flags (PRINCIPLE-011)."""
    unknown: List[str] = []
    i = 0
    while i < len(argv):
        token = argv[i]
        if token.startswith("-"):
            if token not in KNOWN_FLAGS:
                unknown.append(token)
            elif token in VALUE_FLAGS:
                i += 1  # consume this flag's value, whatever it looks like
        i += 1
    return unknown


if __name__ == "__main__":
    if "-h" in sys.argv or "--help" in sys.argv:
        print(HELP_TEXT, end="")
        sys.exit(0)

    _unknown = validate_argv(sys.argv[1:])
    if _unknown:
        print(f"[INVALID USAGE] Unrecognized option(s): {', '.join(_unknown)}", file=sys.stderr)
        print("Why: the requested action is not part of this tool's CLI contract.", file=sys.stderr)
        print("Fix: run 'py scripts/disruption_recovery.py --help' to list valid actions.", file=sys.stderr)
        sys.exit(2)

    # Resolve the target workspace once. Default stays repository-anchored so an agent in a
    # subdirectory still finds the real ledger; --workspace redirects it for sandboxed runs.
    _ws_dir: Optional[Path] = None
    if "--workspace" in sys.argv:
        _widx = sys.argv.index("--workspace")
        if len(sys.argv) > _widx + 1 and not sys.argv[_widx + 1].startswith("--"):
            _ws_dir = Path(sys.argv[_widx + 1]).expanduser()
        else:
            print("[INVALID USAGE] --workspace requires a directory path.", file=sys.stderr)
            print("Why: the ledger location cannot be inferred without it.", file=sys.stderr)
            print("Fix: pass '--workspace <dir>', e.g. --workspace ./sandbox", file=sys.stderr)
            sys.exit(2)
    _ledger = (_ws_dir / ".agents" / "task_ledger.json") if _ws_dir else None
    _audit_root = _ws_dir if _ws_dir else None

    if "--validate-commit" in sys.argv:
        idx = sys.argv.index("--validate-commit")
        if len(sys.argv) > idx + 1 and not sys.argv[idx + 1].startswith("--"):
            commit_msg = sys.argv[idx + 1]
        else:
            sys.stderr.write("Error: --validate-commit requires a commit message argument.\n")
            sys.exit(1)
        valid, reason = validate_conventional_commit(commit_msg)
        if valid:
            print(f"[OK] {reason}")
            sys.exit(0)
        else:
            sys.stderr.write(f"[INVALID] {reason}\n")
            sys.exit(1)
    elif "--checkpoint" in sys.argv:
        idx = sys.argv.index("--checkpoint")
        task_id = sys.argv[idx + 1] if len(sys.argv) > idx + 1 and not sys.argv[idx + 1].startswith("--") else "task"
        
        phase = "in_progress"
        if "--phase" in sys.argv:
            pidx = sys.argv.index("--phase")
            if len(sys.argv) > pidx + 1 and not sys.argv[pidx + 1].startswith("--"):
                phase = sys.argv[pidx + 1]
                
        phase_num = None
        if "--phase-num" in sys.argv:
            pnidx = sys.argv.index("--phase-num")
            if len(sys.argv) > pnidx + 1 and not sys.argv[pnidx + 1].startswith("--"):
                try:
                    phase_num = int(sys.argv[pnidx + 1])
                except ValueError:
                    pass
                    
        desc = ""
        if "--desc" in sys.argv:
            didx = sys.argv.index("--desc")
            if len(sys.argv) > didx + 1 and not sys.argv[didx + 1].startswith("--"):
                desc = sys.argv[didx + 1]

        why = None
        if "--why" in sys.argv:
            widx = sys.argv.index("--why")
            if len(sys.argv) > widx + 1 and not sys.argv[widx + 1].startswith("--"):
                why = sys.argv[widx + 1]

        benefits = None
        if "--benefits" in sys.argv:
            bidx = sys.argv.index("--benefits")
            if len(sys.argv) > bidx + 1 and not sys.argv[bidx + 1].startswith("--"):
                benefits = sys.argv[bidx + 1]
        elif "--benefit" in sys.argv:
            bidx = sys.argv.index("--benefit")
            if len(sys.argv) > bidx + 1 and not sys.argv[bidx + 1].startswith("--"):
                benefits = sys.argv[bidx + 1]

        risks = None
        if "--risks" in sys.argv:
            ridx = sys.argv.index("--risks")
            if len(sys.argv) > ridx + 1 and not sys.argv[ridx + 1].startswith("--"):
                risks = sys.argv[ridx + 1]

        mitigation = None
        if "--mitigation" in sys.argv:
            midx = sys.argv.index("--mitigation")
            if len(sys.argv) > midx + 1 and not sys.argv[midx + 1].startswith("--"):
                mitigation = sys.argv[midx + 1]
                
        cp = record_checkpoint(
            task_id=task_id,
            phase=phase,
            phase_num=phase_num,
            description=desc,
            why=why,
            benefits=benefits,
            risks=risks,
            mitigation=mitigation,
            ledger_file=_ledger,
        )
        print(f"[OK] Checkpoint recorded: Task '{task_id}', Phase {cp.get('phase_num')} ({phase}) - {desc}")
    elif "--complete" in sys.argv:
        idx = sys.argv.index("--complete")
        tid = sys.argv[idx + 1] if len(sys.argv) > idx + 1 and not sys.argv[idx + 1].startswith("--") else "active"
        mark_task_completed(tid, ledger_file=_ledger)
        print(f"[OK] Task '{tid}' marked as completed.")
    elif "--reset" in sys.argv:
        idx = sys.argv.index("--reset")
        reason = sys.argv[idx + 1] if len(sys.argv) > idx + 1 and not sys.argv[idx + 1].startswith("--") else "Reset by user/agent"
        res = reset_active_task(reason=reason, ledger_file=_ledger)
        if res:
            print(f"[OK] Active task '{res.get('task_id')}' abandoned and reset: {reason}")
        else:
            print("[OK] No active task was in progress.")
    elif "--clean" in sys.argv:
        purged = clean_dangling_temp_files(workspace_dir=_audit_root)
        if purged:
            print(f"[OK] Purged {len(purged)} dangling temporary buffer(s):")
            for f in purged:
                print(f"   • {f}")
        else:
            print("[OK] Workspace clean. No dangling temporary buffers found.")
    elif "--resume" in sys.argv:
        report = run_disruption_audit(workspace_dir=_audit_root)
        print(format_resume_report(report))
    elif "--track" in sys.argv:
        try:
            _track, _reasons = classify_track(collect_working_changes(_audit_root or ROOT_DIR))
        except (RuntimeError, OSError, subprocess.SubprocessError) as _e:
            print(f"[TRACK UNKNOWN] {_e}", file=sys.stderr)
            print("Why: the track is computed from git changes versus HEAD.", file=sys.stderr)
            print("Fix: run inside a git repository, or pass --workspace <repo>.", file=sys.stderr)
            sys.exit(1)
        print(f"Track {_track}")
        for _r in _reasons:
            print(f"  {_r}")
    elif "--audit" in sys.argv:
        report = run_disruption_audit(workspace_dir=_audit_root)
        print(format_audit_report(report))
    else:
        report = run_disruption_audit(workspace_dir=_audit_root)
        print(format_audit_report(report))

