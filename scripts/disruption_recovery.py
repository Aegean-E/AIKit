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
import fnmatch
import shutil
import contextlib
import copy
import subprocess
from pathlib import Path
from typing import Callable, Dict, Any, Optional, List, Tuple

# The ledger's write boundary needs the hygiene rules PRINCIPLE-019 R3 already points at it.
# check_secrets imports nothing from this module, so the edge adds no cycle (ADR-173).
#
# Two import forms, because this module is both imported as `scripts.disruption_recovery` and run
# as `python scripts/disruption_recovery.py`, where only `scripts/` is on sys.path. Every other
# directly-runnable script in this repository is a standalone leaf for exactly that reason; this
# one keeps that property rather than requiring a sys.path bootstrap (PRINCIPLE-011 R1). If both
# forms fail the ImportError propagates, so a missing module is still a loud failure.
try:
    from scripts.check_secrets import scrub_text
except ImportError:  # pragma: no cover - exercised by the standalone CLI contract, not the tier
    from check_secrets import scrub_text

# Safe terminal encoding on Windows (cp1254/cp1252)
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError, OSError):  # hygiene: allow console encoding is cosmetic and no input is read
        pass  # documented default: keep the console's own encoding (cosmetic; no input is read)

ROOT_DIR = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT_DIR / ".agents"
LEDGER_PATH = AGENTS_DIR / "task_ledger.json"
LEDGER_SCHEMA_VERSION = 1


class UnsupportedLedgerVersion(Exception):
    """
    A ledger declares a schema this build cannot read (PRINCIPLE-013 R4, PRINCIPLE-016 R5).

    Deliberately neither OSError nor ValueError: load_ledger() treats those as corruption and
    would quarantine or replace the file. A newer format is valid data, so it is refused in place.
    """

    def __init__(self, path: Path, found: Any, supported: int) -> None:
        self.path = Path(path)
        self.found = found
        self.supported = supported
        self.why = ("the ledger was written by a different AIKit whose format this build does not "
                    "understand; reading or rewriting it could lose task history")
        self.fix = ("open it with the AIKit version that wrote it, or restore a ledger written in "
                    "schema version " + str(supported) + "; the file was not modified")
        super().__init__(
            f"{self.path} declares ledger schema version {found!r}; this AIKit reads version {supported}\n"
            f"Why: {self.why}\nFix: {self.fix}"
        )


def empty_ledger() -> Dict[str, Any]:
    """A fresh in-memory ledger; load_ledger() never creates the file for this."""
    return {"version": LEDGER_SCHEMA_VERSION, "active_task": None, "checkpoints": []}


# A project AIKit builds keeps its memory, ledger included, in this folder (ADR-119, ADR-120).
PROJECT_MEMORY_DIRNAME = ".aikit"


def workspace_ledger_path(workspace: Path) -> Path:
    """
    The ledger of `workspace`: `<workspace>/.aikit/task_ledger.json` for a project AIKit builds,
    otherwise `<workspace>/.agents/task_ledger.json` (AIKit itself and sandboxed dogfood runs).
    """
    memory = workspace / PROJECT_MEMORY_DIRNAME
    if memory.is_dir():
        return memory / "task_ledger.json"
    return workspace / ".agents" / "task_ledger.json"


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
        except PermissionError:
            # Windows: creating a file another process is deleting raises EACCES, not EEXIST.
            # It is contention, so retry; a real permission fault ends as locked_ledger's
            # TimeoutError. It crashed a parallel checkpoint under suite load (ADR-077).
            time.sleep(poll_interval)
            continue
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
                    except OSError:  # hygiene: allow best-effort claim cleanup; the loop retries and a timeout raises
                        pass
                    continue
            except OSError:  # hygiene: allow the poll loop retries; a lock timeout raises the triad
                pass
            time.sleep(poll_interval)

    try:
        yield acquired
    finally:
        if acquired:
            try:
                lock_file.unlink(missing_ok=True)
            except OSError:  # hygiene: allow best-effort unlink; a stale lock is broken by age
                pass


LOCK_TIMEOUT_SECONDS = 3.0


@contextlib.contextmanager
def locked_ledger(
    ledger_file: Optional[Path] = None,
    timeout_seconds: float = LOCK_TIMEOUT_SECONDS,
    poll_interval: float = 0.05,
):
    """
    Serialize a full read-modify-write cycle on the task ledger (PRINCIPLE-013 Rule 3).

    Yields the loaded ledger; the caller mutates it in place and the ledger is saved on clean
    exit, all while holding the advisory lock. Without this, parallel subagents interleave
    load/save cycles and silently erase each other's checkpoints (lost-update race).

    Contention is surfaced, never swallowed: if the lock cannot be acquired within the bounded
    timeout the mutation is abandoned with a diagnostic rather than written unprotected.
    """
    path = Path(ledger_file) if ledger_file is not None else LEDGER_PATH
    with file_lock(path, timeout_seconds=timeout_seconds, poll_interval=poll_interval) as acquired:
        if not acquired:
            raise TimeoutError(
                f"[PRINCIPLE-013 LOCK CONTENTION] Could not acquire advisory lock on "
                f"{path.name} within {timeout_seconds}s. "
                f"Why: another agent or process is mid-write on the ledger. "
                f"Fix: retry shortly, or remove a stale '{path.name}.lock' if no process is active."
            )
        ledger = load_ledger(path)
        before = copy.deepcopy(ledger)
        yield ledger
        if ledger != before:
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
            except OSError:  # hygiene: allow the fd is discarded here; the write already succeeded or raised
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
    except OSError as e:
        # Documented default: proceed with the write. Announced, never silent (PRINCIPLE-003 R6).
        sys.stderr.write(f"[WARN] Could not measure free space in {target_dir} ({e}); "
                         f"proceeding without the {min_mb}MB headroom check.\n")
        return True


def validate_ledger_version(data: Any, path: Path) -> None:
    """Refuse a ledger whose declared schema this build does not read (PRINCIPLE-013 R4)."""
    if not isinstance(data, dict) or "version" not in data:
        return
    version = data.get("version")
    if type(version) is not int or version != LEDGER_SCHEMA_VERSION:
        raise UnsupportedLedgerVersion(path, version, LEDGER_SCHEMA_VERSION)


def _read_ledger_file(path: Path) -> Dict[str, Any]:
    """Parse one ledger file, validate its version, then normalize it in memory."""
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("ledger root is not a JSON object")
    validate_ledger_version(data, path)
    return migrate_ledger_schema(data)


def _quarantine_ledger(path: Path) -> Path:
    """Move a corrupt ledger aside without overwriting an earlier quarantine in the same second."""
    stamp = int(time.time())
    wreck = path.parent / f"{path.name}.corrupt_{stamp}"
    index = 1
    while wreck.exists():
        wreck = path.parent / f"{path.name}.corrupt_{stamp}-{index}"
        index += 1
    os.replace(path, wreck)
    return wreck


def migrate_ledger_schema(data: Any) -> Dict[str, Any]:
    """
    Ensure recovered or loaded ledger conforms to current schema specification (PRINCIPLE-013).
    Performs forward-compatible, idempotent schema upgrades.
    """
    if not isinstance(data, dict):
        return empty_ledger()

    # Ensure mandatory fields
    if "version" not in data:
        data["version"] = LEDGER_SCHEMA_VERSION
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
            except OSError as e:
                # The write still proceeds, but losing the PRINCIPLE-013 shadow copy is reported.
                sys.stderr.write(f"[WARN] Shadow backup {bak_path.name} not written: {e}\n")

        # Windows lock-contention retry loop on os.replace
        for attempt in range(max_retries):
            try:
                os.replace(tmp_path, file_path)
                break
            except PermissionError:
                # Only lock contention is worth retrying (another process holds the file on
                # Windows). A full or read-only disk fails the same way five times, so it raises
                # at once and the caller sees the real cause (ADR-146).
                if attempt == max_retries - 1:
                    raise
                time.sleep(0.02 * (2 ** attempt))

        # Durability barrier: make the rename itself survive a power cut (PRINCIPLE-013 R1)
        fsync_dir(file_path.parent)
    except Exception:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except OSError:  # hygiene: allow temp cleanup only; the original failure re-raises
                pass
        raise


def load_ledger(ledger_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    Safely load the task ledger with startup self-healing (PRINCIPLE-013).

    A newer schema is refused in place: it is valid data, not corruption, so it is neither
    quarantined nor replaced by an older backup. A missing version is a legacy ledger and is
    normalized in memory only; read-only callers never write it back.
    """
    path = Path(ledger_file) if ledger_file is not None else LEDGER_PATH
    bak_path = path.with_suffix(path.suffix + ".bak")
    if not path.exists():
        if bak_path.exists():
            try:
                return _read_ledger_file(bak_path)
            except UnsupportedLedgerVersion:
                raise
            except OSError:
                raise  # the backup is there but unreadable: an I/O fault, not corruption (ADR-146)
            except ValueError:  # hygiene: allow nothing readable remains to recover or report
                # Corrupt backup and no main file: nothing is left to recover from, so the
                # caller starts fresh.
                pass
        return empty_ledger()

    try:
        return _read_ledger_file(path)
    except UnsupportedLedgerVersion:
        raise
    except OSError:
        # An I/O failure (locked, permission denied, unreadable device) says nothing about the
        # content: the file may be perfectly valid. Quarantining it renamed a healthy ledger and
        # started an empty one, losing the active task; the CLI reports this instead (ADR-146).
        raise
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as e:
        try:
            wreck = _quarantine_ledger(path)
            sys.stderr.write(f"[WARN] Corrupted task ledger quarantined to {wreck.name}: {e}\n")
        except OSError as move_error:
            sys.stderr.write(f"[WARN] Corrupted task ledger {path.name} could not be quarantined "
                             f"({move_error}); it will be read again on the next load.\n")

        # Attempt recovery from shadow backup (.bak) before falling back to empty state
        if bak_path.exists():
            try:
                recovered = _read_ledger_file(bak_path)
                sys.stderr.write(f"[INFO] Recovered task ledger from shadow backup {bak_path.name}\n")
                return recovered
            except UnsupportedLedgerVersion:
                raise
            except OSError:
                raise  # the backup exists but could not be read: an I/O fault, not corruption
            except ValueError as e:
                sys.stderr.write(f"[WARN] Shadow backup {bak_path.name} is corrupt too ({e}); "
                                 f"starting an empty ledger. Task history was not recovered.\n")

        return empty_ledger()


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

    # The bound applies to the active task too: it used to be exempt, so one long task kept every
    # checkpoint (60 against a cap of 20). Its plan - the Phase 2 checkpoint (PRINCIPLE-004 R1) -
    # is always kept, so pruning can never lose what resumption needs.
    min_inactive = min(5, len(inactive_cps))
    active_budget = max(1, max_history - min_inactive)
    if len(active_cps) > active_budget:
        plan = task_plan_checkpoint(active_cps)
        recent = active_cps[-(active_budget - (1 if plan else 0)):] if active_budget > 1 else []
        active_cps = ([plan] if plan and plan not in recent else []) + recent
    keep_inactive = max(min_inactive, max_history - len(active_cps))
    pruned_inactive = inactive_cps[-keep_inactive:] if keep_inactive else []
    combined = active_cps + pruned_inactive
    return sorted(combined, key=lambda x: x.get("timestamp", 0))


PLAN_MARKER = "[1/"


def task_plan_checkpoint(task_checkpoints: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    The task's plan (PRINCIPLE-004 R1): its latest Phase 2 checkpoint whose description starts
    with `[1/`, the first milestone. Latest, so a revised plan replaces the old one; marker, so a
    user's answer recorded in Phase 2 is not mistaken for the plan. None when no plan exists.
    """
    for cp in reversed(task_checkpoints):
        if cp.get("phase_num") == 2 and str(cp.get("description", "")).startswith(PLAN_MARKER):
            return cp
    return None


def _refuse_newer_ledger_on_disk(path: Path) -> None:
    """Re-check both slots under the lock before replacing either (PRINCIPLE-013 R3)."""
    for candidate in (path, path.with_suffix(path.suffix + ".bak")):
        if not candidate.exists():
            continue
        try:
            with open(candidate, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except ValueError:
            # A corrupt file is recoverable: atomic_write_json keeps it as the .bak shadow.
            continue
        validate_ledger_version(data, candidate)


def save_ledger(
    ledger: Dict[str, Any],
    ledger_file: Optional[Path] = None,
    max_history: int = DEFAULT_MAX_CHECKPOINTS,
    _locked: bool = False,
) -> None:
    """
    Save the task ledger atomically to disk with bounded rolling history (PRINCIPLE-004).

    Acquires the advisory lock unless the caller already holds it (`_locked=True`, set by
    `locked_ledger`), since the lock is not reentrant. Contention is an error: writing without
    the lock could overwrite a newer ledger written by another process (PRINCIPLE-013 R3).
    """
    path = Path(ledger_file) if ledger_file is not None else LEDGER_PATH
    version = ledger.get("version")
    if version is None:
        ledger["version"] = LEDGER_SCHEMA_VERSION
    elif type(version) is not int or version != LEDGER_SCHEMA_VERSION:
        raise UnsupportedLedgerVersion(path, version, LEDGER_SCHEMA_VERSION)
    active_id = ledger.get("active_task", {}).get("task_id") if ledger.get("active_task") else None
    if "checkpoints" in ledger:
        ledger["checkpoints"] = prune_checkpoints(
            ledger["checkpoints"], active_task_id=active_id, max_history=max_history
        )
    if _locked:
        _refuse_newer_ledger_on_disk(path)
        atomic_write_json(path, ledger)
        return
    with file_lock(path, timeout_seconds=LOCK_TIMEOUT_SECONDS) as acquired:
        if not acquired:
            raise TimeoutError(
                f"[PRINCIPLE-013 LOCK CONTENTION] Could not acquire advisory lock on "
                f"{path.name} within {LOCK_TIMEOUT_SECONDS}s. "
                f"Why: another agent or process is mid-write on the ledger. "
                f"Fix: retry shortly, or remove a stale '{path.name}.lock' if no process is active."
            )
        _refuse_newer_ledger_on_disk(path)
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


def repo_relative(path: Any) -> str:
    """
    A path as the ledger stores it (PRINCIPLE-012 R5): repository-relative with `/` separators
    when it lies inside the repository, unchanged otherwise. Absolute paths used to be stored as
    given, writing the user's home directory into a tracked file.
    """
    candidate = Path(path)
    if candidate.is_absolute():
        try:
            return candidate.resolve().relative_to(ROOT_DIR.resolve()).as_posix()
        except ValueError:
            return str(path)
    return candidate.as_posix()


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
    handoff: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Record an atomic micro-checkpoint in the task ledger (PRINCIPLE-002, PRINCIPLE-006, PRINCIPLE-007).
    Tracks active_phase to allow instant phase-accurate resumption after conversation compaction.
    Optionally persists pre-flight 4-quadrant impact assessment metadata (why, benefits, risks, mitigation).
    An optional `handoff` packet carries what the plan cannot: progress, dead ends, open questions
    and evidence (ADR-174). It is written only when given, so a ledger's shape is unchanged without
    one and no schema version bump is needed.
    """
    resolved_phase = resolve_phase_num(phase, phase_num)
    checkpoint_entry = {
        "task_id": task_id,
        "phase": phase,
        "phase_num": resolved_phase,
        "description": description,
        "files_affected": [repo_relative(f) for f in (files_affected or [])],
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

    if handoff:
        # Written key by key, not comprehended over HANDOFF_KEYS: `check_reachability.py` proves a
        # persisted key has a producer by finding it in a dict literal, and a comprehension hides
        # every one of them. The schema is also readable at the point it is written.
        packet = {
            "state": handoff.get("state", ""),
            "next": handoff.get("next", ""),
            "failed": handoff.get("failed", ""),
            "open": handoff.get("open", ""),
            "evidence": handoff.get("evidence", ""),
        }
        checkpoint_entry["handoff"] = {key: value for key, value in packet.items() if value}

    # Locked read-modify-write: parallel subagents must not interleave here (PRINCIPLE-013 R3)
    with locked_ledger(ledger_file) as ledger:
        previous = ledger.get("active_task") or {}
        if previous.get("status") == "in_progress" and previous.get("task_id") != task_id:
            # PRINCIPLE-006 R5: a task left without --complete or --reset used to vanish from
            # --resume silently. Its last state is kept and the switch is reported.
            ledger.setdefault("checkpoints", []).append({
                "task_id": previous.get("task_id"),
                "phase": "superseded",
                "phase_num": previous.get("active_phase"),
                "description": f"Superseded by '{task_id}' without --complete or --reset",
                "status": "superseded",
                "timestamp": checkpoint_entry["timestamp"],
                "timestamp_str": checkpoint_entry["timestamp_str"],
            })
            sys.stderr.write(f"[WARN] Task '{previous.get('task_id')}' was still in progress; recorded as "
                             f"superseded by '{task_id}'. Use --complete or --reset before switching.\n")
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


def mark_task_completed(task_id: str, ledger_file: Optional[Path] = None) -> bool:
    """
    Mark the active task completed (locked, PRINCIPLE-013 R3). Returns False, changing nothing,
    when `task_id` is not the active task: a mistyped id used to print [OK] and leave the task
    in progress, so the next `--resume` reopened finished work.
    """
    with locked_ledger(ledger_file) as ledger:
        if ledger.get("active_task", {}).get("task_id") != task_id:
            return False
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
    return True


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


TEMP_STALE_SECONDS = 60
# Not AIKit's state: git internals, and the projects AIKit builds, which keep their own (ADR-119).
SWEEP_PRUNED_DIRS = {".git", "projects"}


def _reraise(error: OSError) -> None:
    raise error


def sweep_files(workspace_dir: Path, pattern: str) -> List[Path]:
    """
    Files under `workspace_dir` matching `pattern`, pruning `SWEEP_PRUNED_DIRS` while walking, so a
    project's `node_modules` is never descended. Walk errors raise, as `rglob` did, so callers
    still report an unscanned tree instead of a clean one.
    """
    found: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(workspace_dir, onerror=_reraise):
        dirnames[:] = [d for d in dirnames if d not in SWEEP_PRUNED_DIRS]
        found += [Path(dirpath) / name for name in fnmatch.filter(filenames, pattern)]
    return found


def clean_dangling_temp_files(workspace_dir: Optional[Path] = None, min_age_seconds: float = TEMP_STALE_SECONDS) -> List[str]:
    """
    Purge orphaned *.tmp_* files left by interrupted writes (PRINCIPLE-006 R6, PRINCIPLE-013).
    Only files older than `min_age_seconds`: an atomic write lives milliseconds, and deleting a
    younger buffer could destroy a write a parallel agent or sync run is making right now.
    """
    ws = workspace_dir or ROOT_DIR
    deleted = []
    now = time.time()
    try:
        for pat in ("*.tmp_*", "*.steal_*"):
            for p in sweep_files(ws, pat):
                if p.is_file() and now - p.stat().st_mtime >= min_age_seconds:
                    try:
                        rel = str(p.relative_to(ws))
                        p.unlink()
                        deleted.append(rel)
                    except OSError as e:
                        sys.stderr.write(f"[WARN] Could not delete {p}: {e}\n")
    except OSError as e:
        sys.stderr.write(f"[WARN] Temp-buffer scan of {ws} stopped early ({e}); list is partial.\n")
    return deleted


def git_porcelain_status(workspace: Path) -> Tuple[int, str, str]:
    """Default git adapter: run `git status --porcelain` in `workspace` (bounded, PRINCIPLE-010 R3)."""
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=str(workspace),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
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
        "scan_errors": [],
        "ledger_error": None,
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
    ledger_path = workspace_ledger_path(ws)
    if not ledger_path.exists() and (ws / "task_ledger.json").exists():
        ledger_path = ws / "task_ledger.json"
    elif not ledger_path.exists():
        ledger_path = get_ledger_path(ledger_path.parent)
    try:
        ledger = load_ledger(ledger_path)
    except UnsupportedLedgerVersion as error:
        audit["ledger_error"] = {
            "found": error.found,
            "supported": error.supported,
            "why": error.why,
            "fix": error.fix,
        }
        audit["clean_shutdown"] = False
        ledger = None
    if ledger is not None:
        active = ledger.get("active_task")
        if active and active.get("status") == "in_progress":
            audit["interrupted_task"] = active
            audit["clean_shutdown"] = False

        checkpoints = ledger.get("checkpoints", [])
        if checkpoints:
            audit["last_checkpoint"] = checkpoints[-1]
            if active and active.get("status") == "in_progress":
                own = [c for c in checkpoints if c.get("task_id") == active.get("task_id")]
                plan = task_plan_checkpoint(own)
                if plan:
                    audit["plan"] = plan.get("description")
                # The latest packet wins: an older one describes a state already moved past.
                for cp in reversed(own):
                    if isinstance(cp.get("handoff"), dict) and cp["handoff"]:
                        audit["handoff"] = cp["handoff"]
                        break

    # 3. Check for Quarantined Corrupted Artifacts (.corrupt_ files)
    try:
        for p in sweep_files(ws, "*.corrupt_*"):
            audit["quarantined_files"].append(str(p.relative_to(ws)))
    except OSError as e:
        audit["scan_errors"].append(f"quarantine scan: {e}")

    # 4. Check for Dangling Temporary Files (*.tmp_*) from interrupted atomic writes
    try:
        for p in sweep_files(ws, "*.tmp_*"):
            audit["dangling_temp_files"].append(str(p.relative_to(ws)))
    except OSError as e:
        audit["scan_errors"].append(f"temp-buffer scan: {e}")

    return audit


REPORT_LIST_CAP = 20


def append_file_list(lines: List[str], title: str, files: List[str], cap: int = REPORT_LIST_CAP) -> None:
    """Append a titled file list of at most `cap` entries, so a huge tree stays bounded (PRINCIPLE-004 R5)."""
    if not files:
        return
    lines.append(f"{title} ({len(files)}):")
    lines.extend(f"   • {f}" for f in files[:cap])
    if len(files) > cap:
        lines.append(f"   … and {len(files) - cap} more (run 'git status --short' for the full list)")


def audit_body_lines(audit: Dict[str, Any]) -> List[str]:
    """Findings shared by --audit and --resume, so neither report hides what the other shows."""
    lines: List[str] = []

    if audit.get("has_conflicts"):
        lines.append("🔴 Status: UNRESOLVED MERGE CONFLICTS - resolve before any edit or commit!")
    elif audit.get("ledger_error"):
        lines.append("🔴 Status: LEDGER FORMAT UNSUPPORTED - the file was not modified; resume is blocked.")
    elif audit.get("scan_errors"):
        lines.append("🟡 Status: Audit incomplete - some scans failed, so 'clean' cannot be claimed.")
    elif audit.get("clean_shutdown") and not audit.get("has_uncommitted_changes") and not audit.get("dangling_temp_files") and not audit.get("git_missing"):
        lines.append("🟢 Status: Clean state. No interrupted tasks or uncommitted drift detected.")
    else:
        lines.append("🟡 Status: Potential disruption / in-flight state detected!")

    if audit.get("conflicted_files"):
        append_file_list(lines, "⛔ Conflicted Files - interrupted merge/rebase", audit["conflicted_files"])
        lines.append("   Fix: resolve, then 'git add <file>' — or abort via 'git merge --abort' / 'git rebase --abort'")

    ledger_error = audit.get("ledger_error")
    if ledger_error:
        lines.append(f"🔴 Ledger: schema version {ledger_error['found']!r} is not supported; "
                     f"this AIKit reads version {ledger_error['supported']}.")
        lines.append(f"   Why: {ledger_error['why']}")
        lines.append(f"   Fix: {ledger_error['fix']}")

    for err in audit.get("scan_errors", []):
        lines.append(f"⚠️  Scan failed: {err}")

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

    append_file_list(lines, "📝 Modified Files", audit.get("modified_files", []))
    append_file_list(lines, "📁 Untracked Files", audit.get("untracked_files", []))
    append_file_list(lines, "🛡️  Quarantined Corrupted Files", audit.get("quarantined_files", []))
    append_file_list(lines, "🧹 Dangling Temp Buffers", audit.get("dangling_temp_files", []))
    return lines


def format_audit_report(audit: Dict[str, Any]) -> str:
    """Generate human and AI-readable disruption recovery audit report."""
    lines = [
        "============================================================",
        "⚡ DISRUPTION & PROGRESS RECOVERY AUDIT (PRINCIPLE-006)",
        "============================================================",
    ]
    lines += audit_body_lines(audit)
    lines.append("============================================================")
    return "\n".join(lines)


def format_resume_report(audit: Dict[str, Any]) -> str:
    """
    The one cold-start report (PRINCIPLE-004 R2): every --audit finding, then where to resume.
    It used to print only the interrupted task, so with no active task it said "Ready for a new
    task" over uncommitted, untracked or quarantined files that --audit would have shown.
    """
    lines = [
        "============================================================",
        "⚡ DISRUPTION RESUMPTION GUIDANCE (PRINCIPLE-006)",
        "============================================================",
    ]
    lines += audit_body_lines(audit)
    if audit.get("conflicted_files"):
        lines.append("⛔ BLOCKED: resolve the conflicts above before any other action.")

    if audit.get("ledger_error"):
        lines.append("⛔ BLOCKED: this ledger cannot be read by this AIKit; no task state was changed.")
        lines.append("============================================================")
        return "\n".join(lines)

    interrupted = audit.get("interrupted_task")
    if not interrupted:
        if audit.get("modified_files") or audit.get("untracked_files") or audit.get("dangling_temp_files"):
            lines.append("🟡 No interrupted task, but the files above are uncommitted: inspect them before a new task and never overwrite them.")
        elif not audit.get("conflicted_files"):
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
    if audit.get("plan"):
        lines.append(f"🗺️  Plan (Phase 2 checkpoint): {audit['plan']}")
    if audit.get("dangling_temp_files"):
        lines.append(f"🧹 Action Needed: Purge {len(audit['dangling_temp_files'])} dangling .tmp_* files (run 'python scripts/disruption_recovery.py --clean')")
    # The handoff packet (ADR-174): what the plan cannot say. Its `next` replaces the generic
    # line below, which told every task to inspect files and run the unit tier.
    handoff = audit.get("handoff") or {}
    for key, label in (("state", "📊 State"), ("failed", "🚫 Tried and rejected"),
                       ("open", "❓ Open question"), ("evidence", "🧾 Verified")):
        if handoff.get(key):
            lines.append(f"{label}: {handoff[key]}")
    lines.append(f"💡 Next Action: {handoff['next']}" if handoff.get("next") else
                 f"💡 Next Action: Inspect surviving files, run unit tests, and resume at Phase {next_phase_num}")
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
    pattern = r"^([a-z]+)(?:\(([a-zA-Z0-9_\-\./,@]+)\))?(!)?:\s+(.+)$"
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

    # A milestone tag must be well-formed and inside PRINCIPLE-008's horizon (PRINCIPLE-006 R1);
    # "[milestone 3/2]" or "[milestone 1/9]" used to pass as plain description text.
    if "[milestone" in desc:
        tag = re.match(r"\[milestone (\d+)/(\d+)\] \S", desc)
        if not tag:
            return False, "Milestone tag must open the description as '[milestone N/M] <text>'."
        n, m = int(tag.group(1)), int(tag.group(2))
        if not (2 <= m <= 6 and 1 <= n <= m):
            return False, f"Milestone tag [milestone {n}/{m}] needs 2 <= M <= 6 and 1 <= N <= M; a one-milestone plan commits untagged."

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
BOOKKEEPING_PATHS = frozenset({".agents/task_ledger.json", ".aikit/task_ledger.json",
                               ".aikit/ui_task.json", ".aikit/ui_task.json.bak",
                               ".aikit/ui_history.json"})


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
        rename_source = None
        if "R" in xy or "C" in xy:
            if i < len(entries):
                rename_source = entries[i]
                i += 1  # -z puts the rename/copy source in the next field
        if path in BOOKKEEPING_PATHS:
            continue
        if xy == "??":
            old = None
        else:
            head = git("show", f"HEAD:{path}")
            old = head.stdout if head.returncode == 0 else None
        target = workspace / path
        new = target.read_text(encoding="utf-8", errors="replace") if target.is_file() else None
        changes.append((path, old, new))
        if rename_source and "R" in xy and rename_source not in BOOKKEEPING_PATHS:
            source = git("show", f"HEAD:{rename_source}")
            changes.append((rename_source,
                            source.stdout if source.returncode == 0 else None, None))
    return changes


VALUE_FLAGS = {
    "--validate-commit", "--checkpoint", "--phase", "--phase-num", "--desc",
    "--why", "--benefits", "--benefit", "--risks", "--mitigation", "--handoff",
    "--complete", "--reset", "--workspace",
}
# Standalone action flags.
ACTION_FLAGS = {"--clean", "--resume", "--audit", "--track", "--help", "-h"}
# Valueless flags that modify an action rather than being one.
MODIFIER_FLAGS = {"--redact"}
KNOWN_FLAGS = VALUE_FLAGS | ACTION_FLAGS | MODIFIER_FLAGS

HELP_TEXT = """AIKit Disruption Recovery & Task Ledger (PRINCIPLE-006, PRINCIPLE-013)

Usage:
  python scripts/disruption_recovery.py [ACTION] [OPTIONS]

Actions (default: --audit):
  --audit                    Report working-tree drift, dangling buffers, and ledger state
  --resume                   Print the resumption report for an interrupted task
  --clean                    Purge orphaned temporary buffers (*.tmp_*) older than 60 s; younger
                             ones may belong to a write in progress and are kept
  --checkpoint <task_id>     Record a task checkpoint in .agents/task_ledger.json; a task's
                             first plan (--phase-num 2, --desc starting '[1/') needs --why,
                             --benefits, --mitigation and --risks with 'contract:', 'dependency:',
                             'concurrency:' and 'state:' verdicts, else exit 2 (PRINCIPLE-007 R6);
                             a task reaching Phase 3+ with no assessment gets a warning
  --complete <task_id>       Mark a task as completed
  --reset [reason]           Abandon and clear the active task
  --validate-commit <msg>    Validate a Conventional Commit message (PRINCIPLE-018)
  --track                    Print the lifecycle track (A/B/C) of the current changes (PRINCIPLE-002 R3)

Workspace:
  --workspace <dir>          Operate on <dir>'s ledger instead of this repository's:
                             <dir>/.aikit/task_ledger.json for a project (ADR-120), else
                             <dir>/.agents/task_ledger.json. Required for sandboxed
                             dogfooding, which must never mutate the host repo (PRINCIPLE-015 R4).

Checkpoint options:
  --phase <name>             Lifecycle phase label (e.g. planning, implementation)
  --phase-num <1-5>          Numeric lifecycle phase for compaction resumption
  --desc <text>              Checkpoint description
  --why <text>               Pre-flight impact: root cause / user goal (PRINCIPLE-007)
  --benefits <text>          Pre-flight impact: expected benefits
  --risks <text>             Pre-flight impact: blast-radius risks
  --mitigation <text>        Pre-flight impact: risk mitigations
  --handoff <text>           Cold-start packet as `key: value` segments separated by ';':
                             next (required), state, failed, open, evidence (PRINCIPLE-004 R2)
  --redact                   With --checkpoint: record credential-shaped free text as
                             [REDACTED] instead of refusing the write (PRINCIPLE-019 R3)
  -h, --help                 Show this help message and exit

Exit codes:
  0  success    1  operational failure (an unwritable, full or locked ledger prints
                    What/Why/Fix, never a traceback)    2  CLI argument misuse
"""


def report_operational_error(exc_type, exc, tb) -> None:
    """
    `sys.excepthook` for the CLI (PRINCIPLE-011 R6, PRINCIPLE-013 R2/R5): an operational failure
    - an unwritable or full disk, a lock timeout - prints the triad and the process exits 1, as an
    uncaught exception does. It used to print a raw traceback. Other exceptions are bugs and keep
    Python's traceback.
    """
    if issubclass(exc_type, UnsupportedLedgerVersion):
        print(f"[LEDGER VERSION REFUSED] {exc}", file=sys.stderr)
        return
    if not issubclass(exc_type, (OSError, TimeoutError)):
        sys.__excepthook__(exc_type, exc, tb)
        return
    print(f"[LEDGER WRITE FAILED] {exc}", file=sys.stderr)
    print("Why: the task ledger could not be read or written (disk full, read-only, locked or "
          "permission denied).", file=sys.stderr)
    print("Fix: free disk space or fix permissions on .agents/, or wait for the other process "
          "holding the lock, then re-run the command.", file=sys.stderr)


def validate_argv(argv: List[str]) -> List[str]:
    """Return unrecognized options, skipping values of known value-taking flags (PRINCIPLE-011)."""
    unknown: List[str] = []
    i = 0
    while i < len(argv):
        token = argv[i]
        if token.startswith("-"):
            if token not in KNOWN_FLAGS:
                unknown.append(token)
            elif token in VALUE_FLAGS and i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                i += 1  # consume this flag's value; a `--` token is a flag, never a value
        i += 1
    return unknown


RISK_DIMENSIONS = ("contract:", "dependency:", "concurrency:", "state:")

# The handoff packet (PRINCIPLE-004 R2, ADR-174). `--resume` already prints the plan; these are
# the things it could not know: progress against that plan, a dead end not worth retrying, a
# question still owed to the user, and what has already been verified.
HANDOFF_KEYS = ("state", "next", "failed", "open", "evidence")
MAX_HANDOFF_CHARS = 2000


def parse_handoff(text: str) -> Tuple[Dict[str, str], List[str]]:
    """
    One `--handoff` string as `{key: value}`, plus the reasons it is unusable.

    The format is `--risks`' own: `key: value` segments separated by `;`, so an agent that can
    write one can write the other. A value may contain `:` - only the first one in a segment
    separates the key - and empty segments are ignored, so a trailing `;` is not an error.
    """
    if len(text) > MAX_HANDOFF_CHARS:
        return {}, [f"--handoff is {len(text)} characters; the limit is {MAX_HANDOFF_CHARS} "
                    f"so a packet stays readable after a compaction"]
    packet: Dict[str, str] = {}
    errors: List[str] = []
    for segment in text.split(";"):
        if not segment.strip():
            continue
        key, separator, value = segment.partition(":")
        key = key.strip().lower()
        if not separator or key not in HANDOFF_KEYS:
            errors.append(f"--handoff does not know the key '{key or segment.strip()}'; "
                          f"it accepts {', '.join(HANDOFF_KEYS)}")
            continue
        if value.strip():
            packet[key] = value.strip()
    if not errors and "next" not in packet:
        errors.append("--handoff must give a 'next:' value: the one action that resumes this task")
    return packet, errors


def impact_errors(description: str, phase_num: Optional[int], fields: Dict[str, Optional[str]],
                  has_prior_impact: bool) -> List[str]:
    """
    PRINCIPLE-007 R6: a task's first plan checkpoint (Phase 2, `--desc` starting `[1/`) carries the
    whole impact assessment, and `--risks` gives a verdict for each blast-radius dimension of R2.
    Plans used to be recorded with `--why` alone, or nothing, and nothing noticed.
    """
    if phase_num != 2 or not description.startswith("[1/") or has_prior_impact:
        return []
    errors = [f"--{name} is required on the first plan checkpoint" for name, value in fields.items()
              if not (value or "").strip()]
    risks = (fields.get("risks") or "").lower()
    if risks.strip():
        errors += [f"--risks must give a verdict for '{label}' (write 'none' when there is no risk)"
                   for label in RISK_DIMENSIONS if label not in risks]
    return errors


def missing_impact_warning(task_id: str, phase_num: Optional[int], has_prior_impact: bool,
                           has_impact_now: bool) -> Optional[str]:
    """
    PRINCIPLE-007 R1: a Track C task records its impact assessment before its first edit. A task
    that reaches Phase 3+ with none skipped that step, unless it is Track B (PRINCIPLE-002 R4), which
    this CLI cannot tell without git; so this warns instead of refusing.
    """
    if phase_num is None or phase_num < 3 or has_prior_impact or has_impact_now:
        return None
    return (f"[WARN] Task '{task_id}' entered Phase {phase_num} with no impact assessment on record. "
            f"A Track C task records it on its first plan checkpoint (PRINCIPLE-007 R1, R6); "
            f"a Track B task has none.")


def scrub_checkpoint_text(desc: str, impact: Dict[str, Optional[str]], redact: bool,
                          handoff: str = "") -> Tuple[str, Dict[str, Optional[str]], str, List[str]]:
    """
    The checkpoint's free text, scrubbed when `redact` is set, plus the detectors that fired.

    PRINCIPLE-019 R3 makes the ledger a secret-scanning surface because `--why`, `--benefits`,
    `--risks`, `--mitigation` and `--handoff` are written into a git-tracked file; R5 makes such a
    leak unrecoverable. Checking here, in the one path both CLIs take (ADR-128), refuses the write
    instead of reporting it afterwards (ADR-173).
    """
    detectors: List[str] = []
    scrubbed_desc, hits = scrub_text(desc or "")
    detectors.extend(hits)
    scrubbed_impact: Dict[str, Optional[str]] = {}
    for field, value in impact.items():
        if not value:
            scrubbed_impact[field] = value
            continue
        scrubbed_value, hits = scrub_text(value)
        detectors.extend(f"{name} in --{field}" for name in hits)
        scrubbed_impact[field] = scrubbed_value
    scrubbed_handoff, hits = scrub_text(handoff or "")
    detectors.extend(f"{name} in --handoff" for name in hits)
    if not redact:
        return desc, impact, handoff, detectors
    return scrubbed_desc, scrubbed_impact, scrubbed_handoff, detectors


def checkpoint_command(task_id: str, phase: str, phase_num: Optional[int], desc: str,
                       impact: Dict[str, Optional[str]], ledger_file: Optional[Path] = None,
                       redact: bool = False, handoff: str = "") -> int:
    """
    Record a checkpoint behind the PRINCIPLE-007 R1/R6 impact gate; returns the exit code. The one
    path for every CLI that records checkpoints (`--checkpoint` here, `aikit checkpoint`): a second
    copy recorded first plans with no impact assessment (ADR-128).
    """
    desc, impact, handoff, leaked = scrub_checkpoint_text(desc, impact, redact, handoff)
    if leaked and not redact:
        print(f"[CREDENTIAL IN CHECKPOINT TEXT] {'; '.join(sorted(set(leaked)))}", file=sys.stderr)
        print("Why: checkpoint free text is written into a git-tracked ledger, and a committed "
              "credential must be rotated, not reverted (PRINCIPLE-019 R3, R5).", file=sys.stderr)
        print("Fix: remove the value from the text, or rerun with --redact to record it as "
              "[REDACTED]; rotate the credential either way.", file=sys.stderr)
        return 1
    packet, handoff_errors = parse_handoff(handoff) if handoff.strip() else ({}, [])
    if handoff_errors:
        print(f"[UNUSABLE HANDOFF] {'; '.join(handoff_errors)}", file=sys.stderr)
        print("Why: a handoff packet is read on the next cold start, so a malformed one is "
              "silently lost exactly when it is needed (PRINCIPLE-004 R2).", file=sys.stderr)
        print(f'Fix: pass --handoff "next: <the one action that resumes this task>", adding any '
              f'of {", ".join(k for k in HANDOFF_KEYS if k != "next")} as `key: value` segments '
              f'separated by ";".', file=sys.stderr)
        return 2
    prior = any(c.get("task_id") == task_id and c.get("impact_assessment")
                for c in load_ledger(ledger_file).get("checkpoints", []))
    resolved = resolve_phase_num(phase, phase_num)
    errors = impact_errors(desc, resolved, impact, prior)
    warning = missing_impact_warning(task_id, resolved, prior, any(impact.values()))
    if warning:
        print(warning, file=sys.stderr)
    if errors:
        print(f"[INCOMPLETE IMPACT] {'; '.join(errors)}", file=sys.stderr)
        print("Why: the first plan of a Track C task records why, benefits, risks and mitigation "
              "(PRINCIPLE-007 R6) so they survive compaction.", file=sys.stderr)
        print('Fix: add --why, --benefits, --mitigation and --risks "contract: ...; dependency: ...; '
              'concurrency: ...; state: ..."', file=sys.stderr)
        return 2
    cp = record_checkpoint(task_id=task_id, phase=phase, phase_num=phase_num, description=desc,
                           why=impact.get("why"), benefits=impact.get("benefits"),
                           risks=impact.get("risks"), mitigation=impact.get("mitigation"),
                           ledger_file=ledger_file, handoff=packet)
    print(f"[OK] Checkpoint recorded: Task '{task_id}', Phase {cp.get('phase_num')} ({phase}) - {desc}")
    return 0


def argv_value_errors(argv: List[str]) -> List[str]:
    """
    Value flags given without a value, or with an invalid one (PRINCIPLE-003 R6). These used to
    fall back silently: `--checkpoint --task-id x` recorded task 'task', `--phase-num six` was
    dropped, `--complete` with no id completed nothing and still printed [OK].
    """
    errors: List[str] = []
    for i, token in enumerate(argv):
        if token not in VALUE_FLAGS or token == "--reset":  # --reset [reason] is optional
            continue
        value = argv[i + 1] if i + 1 < len(argv) else None
        if value is None or value.startswith("--"):
            errors.append(f"{token} requires a value")
        elif token == "--phase-num" and value not in {"1", "2", "3", "4", "5"}:
            errors.append(f"--phase-num must be 1-5, got '{value}'")
    return errors


if __name__ == "__main__":
    sys.excepthook = report_operational_error
    if "-h" in sys.argv or "--help" in sys.argv:
        print(HELP_TEXT, end="")
        sys.exit(0)

    _unknown = validate_argv(sys.argv[1:])
    if _unknown:
        print(f"[INVALID USAGE] Unrecognized option(s): {', '.join(_unknown)}", file=sys.stderr)
        print("Why: the requested action is not part of this tool's CLI contract.", file=sys.stderr)
        print("Fix: run 'python scripts/disruption_recovery.py --help' to list valid actions.", file=sys.stderr)
        sys.exit(2)
    _value_errors = argv_value_errors(sys.argv[1:])
    if _value_errors:
        print(f"[INVALID USAGE] {'; '.join(_value_errors)}", file=sys.stderr)
        print("Why: a missing value used to be replaced by a silent default.", file=sys.stderr)
        print("Fix: e.g. --checkpoint <task_id> --phase-num 2 --desc \"<text>\"", file=sys.stderr)
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
    _ledger = workspace_ledger_path(_ws_dir) if _ws_dir else None
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
        task_id = sys.argv[idx + 1]  # presence and shape checked by argv_value_errors
        
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
                except ValueError:  # hygiene: allow argv_value_errors already refused a non-numeric value with exit 2
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

        handoff = ""
        if "--handoff" in sys.argv:
            hidx = sys.argv.index("--handoff")
            if len(sys.argv) > hidx + 1 and not sys.argv[hidx + 1].startswith("--"):
                handoff = sys.argv[hidx + 1]

        sys.exit(checkpoint_command(task_id, phase, phase_num, desc,
                                    {"why": why, "benefits": benefits, "risks": risks,
                                     "mitigation": mitigation}, _ledger,
                                    redact="--redact" in sys.argv, handoff=handoff))
    elif "--complete" in sys.argv:
        idx = sys.argv.index("--complete")
        tid = sys.argv[idx + 1]
        if not mark_task_completed(tid, ledger_file=_ledger):
            print(f"[NOT COMPLETED] Task '{tid}' is not the active task.", file=sys.stderr)
            print("Why: only the active task can be completed; nothing was changed.", file=sys.stderr)
            print("Fix: run --resume to see the active task id, then --complete <that id>.", file=sys.stderr)
            sys.exit(1)
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
        if report.get("ledger_error"):
            sys.exit(1)
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
        if report.get("ledger_error"):
            sys.exit(1)
    else:
        report = run_disruption_audit(workspace_dir=_audit_root)
        print(format_audit_report(report))
        if report.get("ledger_error"):
            sys.exit(1)

