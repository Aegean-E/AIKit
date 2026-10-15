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
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

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


def atomic_write_json(file_path: Path, data: Any) -> None:
    """Atomically write JSON data using fsync and temporary replacement (PRINCIPLE-013)."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = file_path.with_suffix(file_path.suffix + f".tmp_{os.getpid()}_{int(time.time() * 1000)}")
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, file_path)
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
    Quarantines corrupted files from power outages and restores safe empty state.
    """
    path = ledger_file or LEDGER_PATH
    if not path.exists():
        return {"version": 1, "active_task": None, "checkpoints": []}

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
        # Quarantine corrupted artifact
        corrupt_name = f"{path.name}.corrupt_{int(time.time())}"
        corrupt_path = path.parent / corrupt_name
        try:
            os.replace(path, corrupt_path)
            sys.stderr.write(f"[WARN] Corrupted task ledger quarantined to {corrupt_name}: {e}\n")
        except OSError:
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
) -> None:
    """Save the task ledger atomically to disk with bounded rolling history (PRINCIPLE-004)."""
    path = ledger_file or LEDGER_PATH
    active_id = ledger.get("active_task", {}).get("task_id") if ledger.get("active_task") else None
    if "checkpoints" in ledger:
        ledger["checkpoints"] = prune_checkpoints(
            ledger["checkpoints"], active_task_id=active_id, max_history=max_history
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
    for key, num in PHASE_MAPPING.items():
        if key in normalized:
            return num
    return 1


def record_checkpoint(
    task_id: str,
    phase: str,
    description: str,
    files_affected: Optional[List[str]] = None,
    status: str = "in_progress",
    ledger_file: Optional[Path] = None,
    phase_num: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Record an atomic micro-checkpoint in the task ledger (PRINCIPLE-002, PRINCIPLE-006).
    Tracks active_phase to allow instant phase-accurate resumption after conversation compaction.
    """
    resolved_phase = resolve_phase_num(phase, phase_num)
    ledger = load_ledger(ledger_file)
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

    ledger["active_task"] = {
        "task_id": task_id,
        "last_phase": phase,
        "active_phase": resolved_phase,
        "status": status,
        "updated_at": checkpoint_entry["timestamp"],
    }
    ledger.setdefault("checkpoints", []).append(checkpoint_entry)
    save_ledger(ledger, ledger_file)
    return checkpoint_entry


def mark_task_completed(task_id: str, ledger_file: Optional[Path] = None) -> None:
    """Mark the active task as successfully completed in the ledger."""
    ledger = load_ledger(ledger_file)
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
    save_ledger(ledger, ledger_file)


def run_disruption_audit(workspace_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Execute a comprehensive pre-flight disruption audit (PRINCIPLE-006, PRINCIPLE-007).
    Evaluates Git working tree status, surviving uncommitted files, and ledger state.
    """
    ws = workspace_dir or ROOT_DIR
    audit: Dict[str, Any] = {
        "workspace": str(ws),
        "has_uncommitted_changes": False,
        "modified_files": [],
        "untracked_files": [],
        "interrupted_task": None,
        "last_checkpoint": None,
        "clean_shutdown": True,
        "quarantined_files": [],
        "dangling_temp_files": [],
    }

    # 1. Check Git Status
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(ws),
            capture_output=True,
            text=True,
            timeout=5,
        )
        if proc.returncode == 0:
            for raw_line in proc.stdout.splitlines():
                if not raw_line or len(raw_line) < 4:
                    continue
                status_code = raw_line[:2].strip()
                file_rel = raw_line[3:].strip()
                if status_code in ("M", "A", "D", "R", "MM", "AM"):
                    audit["modified_files"].append(file_rel)
                elif status_code == "??":
                    audit["untracked_files"].append(file_rel)
            audit["has_uncommitted_changes"] = bool(audit["modified_files"] or audit["untracked_files"])
    except Exception as e:
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

    if audit.get("clean_shutdown") and not audit.get("has_uncommitted_changes") and not audit.get("dangling_temp_files"):
        lines.append("🟢 Status: Clean state. No interrupted tasks or uncommitted drift detected.")
    else:
        lines.append("🟡 Status: Potential disruption / in-flight state detected!")

    if audit.get("interrupted_task"):
        it = audit["interrupted_task"]
        lines.append(f"⚠️  Interrupted Task: '{it.get('task_id')}' in phase '{it.get('last_phase')}'")
    
    if audit.get("last_checkpoint"):
        lc = audit["last_checkpoint"]
        lines.append(f"📌 Last Checkpoint: [{lc.get('timestamp_str')}] {lc.get('phase')} - {lc.get('description')}")

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
    interrupted = audit.get("interrupted_task")
    if not interrupted:
        lines.append("🟢 No interrupted task detected. Ready for a new task.")
        lines.append("============================================================")
        return "\n".join(lines)

    task_id = interrupted.get("task_id", "unknown")
    phase = interrupted.get("last_phase", "unknown")
    phase_num = interrupted.get("last_phase_num", 2)
    next_phase_num = min(5, phase_num if audit.get("has_uncommitted_changes") else phase_num + 1)
    
    lines.append(f"⚠️  RESUMING INTERRUPTED TASK: '{task_id}'")
    lines.append(f"📌 Last Active Phase: Phase {phase_num} ({phase})")
    lines.append(f"🚀 Recommended Resumption Phase: Phase {next_phase_num}")
    if audit.get("modified_files"):
        lines.append(f"📝 Surviving Modified Files ({len(audit['modified_files'])}):")
        for f in audit["modified_files"]:
            lines.append(f"   • {f}")
    if audit.get("dangling_temp_files"):
        lines.append(f"🧹 Action Needed: Purge {len(audit['dangling_temp_files'])} dangling .tmp_* files")
    lines.append(f"💡 Next Action: Inspect surviving files, run unit tests, and resume at Phase {next_phase_num}")
    lines.append("============================================================")
    return "\n".join(lines)


if __name__ == "__main__":
    if "--checkpoint" in sys.argv:
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
                
        cp = record_checkpoint(task_id=task_id, phase=phase, phase_num=phase_num, description=desc)
        print(f"[OK] Checkpoint recorded: Task '{task_id}', Phase {cp.get('phase_num')} ({phase}) - {desc}")
    elif "--complete" in sys.argv:
        idx = sys.argv.index("--complete")
        tid = sys.argv[idx + 1] if len(sys.argv) > idx + 1 and not sys.argv[idx + 1].startswith("--") else "active"
        mark_task_completed(tid)
        print(f"[OK] Task '{tid}' marked as completed.")
    elif "--resume" in sys.argv:
        report = run_disruption_audit()
        print(format_resume_report(report))
    elif "--audit" in sys.argv:
        report = run_disruption_audit()
        print(format_audit_report(report))
    else:
        report = run_disruption_audit()
        print(format_audit_report(report))

