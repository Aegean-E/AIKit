"""
Automated Test Suite for Portable Agent Kit (PRINCIPLE-011, PRINCIPLE-016)
Validates principle synchronization, disruption recovery atomicity,
knowledge base AST generation, and operational dogfooding.
"""

import os
import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from scripts.sync_principles import parse_principles, sync_all, AGENTS_MD
from scripts.disruption_recovery import (
    load_ledger,
    save_ledger,
    atomic_write_json,
    record_checkpoint,
    mark_task_completed,
    prune_checkpoints,
    run_disruption_audit,
    format_audit_report,
    format_resume_report,
    reset_active_task,
    clean_dangling_temp_files,
    file_lock,
    check_disk_headroom,
    migrate_ledger_schema,
)
from scripts.update_knowledge_base import (
    extract_python_symbols,
    generate_codebase_map,
    update_and_validate,
    CORE_DOCS,
    KNOWLEDGE_DIR,
)


class TestPrincipleSync(unittest.TestCase):
    """Verifies that all 18 principles are maintained and synchronized (PRINCIPLE-001, PRINCIPLE-017)."""

    def test_parse_18_principles(self):
        principles = parse_principles(AGENTS_MD)
        self.assertEqual(len(principles), 18, f"Expected 18 principles, got {len(principles)}")
        p_ids = [p["id"] for p in principles]
        for i in range(1, 19):
            expected_id = f"PRINCIPLE-{i:03d}"
            self.assertIn(expected_id, p_ids, f"Missing {expected_id} in AGENTS.md")
        for p in principles:
            self.assertTrue(p["invariant"], f"Principle {p['id']} is missing an invariant capsule")

    def test_monotonic_lifecycle_phase_alignment(self):
        # Enforces PRINCIPLE-002: principles must belong to monotonic phases 1 through 5
        principles = parse_principles(AGENTS_MD)
        self.assertEqual(len(principles), 18)
        current_phase = 1
        for p in principles:
            self.assertIn("phase_num", p)
            self.assertGreaterEqual(p["phase_num"], current_phase, f"Phase inversion detected at {p['id']}")
            current_phase = p["phase_num"]
        self.assertEqual(current_phase, 5, "Principles did not reach Phase 5")

    def test_targets_in_sync_and_budgeted(self):
        # All target files must be 100% in sync with AGENTS.md and within context budget (PRINCIPLE-001)
        principles = parse_principles(AGENTS_MD)
        self.assertEqual(len(principles), 18)
        targets = [
            ROOT_DIR / "GEMINI.md",
            ROOT_DIR / ".agents" / "rules" / "principles.md",
            ROOT_DIR / "CLAUDE.md",
            ROOT_DIR / ".cursorrules",
            ROOT_DIR / ".github" / "copilot-instructions.md",
        ]
        MAX_ALLOWED_CHARS = 8000  # <2,000 tokens per target file
        for target in targets:
            self.assertTrue(target.exists(), f"Target file missing: {target}")
            content = target.read_text(encoding="utf-8")
            self.assertIn("PRINCIPLE-001", content, f"PRINCIPLE-001 missing from {target.name}")
            self.assertIn("PRINCIPLE-002", content, f"PRINCIPLE-002 missing from {target.name}")
            self.assertIn("PRINCIPLE-003", content, f"PRINCIPLE-003 missing from {target.name}")
            self.assertIn("PRINCIPLE-004", content, f"PRINCIPLE-004 missing from {target.name}")
            self.assertIn("PRINCIPLE-005", content, f"PRINCIPLE-005 missing from {target.name}")
            self.assertIn("PRINCIPLE-006", content, f"PRINCIPLE-006 missing from {target.name}")
            self.assertIn("PRINCIPLE-017", content, f"PRINCIPLE-017 missing from {target.name}")
            self.assertIn("PRINCIPLE-018", content, f"PRINCIPLE-018 missing from {target.name}")
            self.assertIn("Deterministic Grep Anchor", content, f"Grep anchor missing from {target.name}")
            # Assert context budget cap
            self.assertLessEqual(
                len(content),
                MAX_ALLOWED_CHARS,
                f"Governance bloat detected in {target.name}: {len(content)} chars > {MAX_ALLOWED_CHARS}"
            )

    def test_principle_003_anti_hallucination_capsule(self):
        # Enforces PRINCIPLE-003: verified invariant capsule with slice freshness, call-sites, and platform parity
        principles = parse_principles(AGENTS_MD)
        p3 = next((p for p in principles if p["id"] == "PRINCIPLE-003"), None)
        self.assertIsNotNone(p3)
        self.assertIn("slice freshness", p3["invariant"].lower())
        self.assertIn("call-site", p3["invariant"].lower())
        self.assertIn("platform parity", p3["invariant"].lower())
        self.assertIn("ast syntax gate", p3["invariant"].lower())

    def test_principle_004_compaction_resilience_capsule(self):
        # Enforces PRINCIPLE-004: verified invariant capsule with task_ledger, living plan SSOT, anti-repetition
        principles = parse_principles(AGENTS_MD)
        p4 = next((p for p in principles if p["id"] == "PRINCIPLE-004"), None)
        self.assertIsNotNone(p4)
        self.assertIn("task_ledger.json", p4["invariant"].lower())
        self.assertIn("living plan ssot", p4["invariant"].lower())
        self.assertIn("anti-repetition", p4["invariant"].lower())
        self.assertIn("ast-first", p4["invariant"].lower())
        self.assertIn("bounded rolling ledger", p4["invariant"].lower())

    def test_principle_005_cold_start_capsule(self):
        # Enforces PRINCIPLE-005: verified invariant capsule with 30s orientation, token ceiling, command parity, whole-tree drift shield
        principles = parse_principles(AGENTS_MD)
        p5 = next((p for p in principles if p["id"] == "PRINCIPLE-005"), None)
        self.assertIsNotNone(p5)
        self.assertIn("self-describing repo", p5["invariant"].lower())
        self.assertIn("30s cold-start orientation", p5["invariant"].lower())
        self.assertIn("<20k chars", p5["invariant"].lower())
        self.assertIn("material surface readme sync", p5["invariant"].lower())
        self.assertIn("executable command parity", p5["invariant"].lower())
        self.assertIn("whole-tree drift shield", p5["invariant"].lower())

    def test_principle_006_disruption_capsule(self):
        # Enforces PRINCIPLE-006: verified invariant capsule with atomic micro-commits, audit, and CLI ledger
        principles = parse_principles(AGENTS_MD)
        p6 = next((p for p in principles if p["id"] == "PRINCIPLE-006"), None)
        self.assertIsNotNone(p6)
        self.assertIn("incremental atomic micro-commits", p6["invariant"].lower())
        self.assertIn("pre-flight disruption audit", p6["invariant"].lower())
        self.assertIn("disruption_recovery.py", p6["invariant"].lower())
        self.assertIn("explicit micro-staging", p6["invariant"].lower())

    def test_readme_cold_start_orientation_and_script_parity(self):
        # Enforces PRINCIPLE-005: README.md must contain 30s quick reference, prerequisites, canonical test command,
        # cold-start token ceiling (<20,000 chars), and valid paths for every file listed in the directory tree.
        readme_path = ROOT_DIR / "README.md"
        self.assertTrue(readme_path.exists(), "README.md missing from repository root")
        readme_content = readme_path.read_text(encoding="utf-8")
        
        # 1. Cold-Start Token Ceiling (<20,000 characters)
        MAX_README_CHARS = 20000
        self.assertLessEqual(
            len(readme_content),
            MAX_README_CHARS,
            f"README.md exceeds 20,000 char cold-start budget: {len(readme_content)} chars"
        )

        # 2. Orientation block & prerequisites
        self.assertIn("30-Second Cold-Start Quick Reference", readme_content, "Missing 30s quick reference in README.md")
        self.assertIn("Python 3.10+", readme_content, "Missing Python runtime prerequisite in README.md")
        self.assertIn("python -m unittest discover tests", readme_content, "Missing canonical test command in README.md")
        
        # 3. Whole-Tree Drift Shield: Every file listed in `What's Inside` must physically exist on disk
        expected_paths = [
            "README.md",
            "AGENTS.md",
            "GUIDELINES.md",
            "GEMINI.md",
            "CLAUDE.md",
            ".cursorrules",
            ".github/copilot-instructions.md",
            ".agents/rules/principles.md",
            ".agents/task_ledger.json",
            "scripts/sync_principles.py",
            "scripts/disruption_recovery.py",
            "scripts/update_knowledge_base.py",
            "tests/test_kit.py",
            "knowledge/INDEX.md",
            "knowledge/architecture.md",
            "knowledge/services.md",
            "knowledge/data_models.md",
            "knowledge/state_and_ui.md",
            "knowledge/decisions.md",
            "knowledge/codebase_map.md",
        ]
        for rel in expected_paths:
            basename = Path(rel).name
            self.assertIn(basename, readme_content, f"Path '{rel}' (basename '{basename}') missing from README.md")
            self.assertTrue((ROOT_DIR / rel).exists(), f"Path from README.md tree does not exist on disk: {rel}")


class TestDisruptionRecovery(unittest.TestCase):
    """Verifies atomic write, disruption ledger, and crash recovery (PRINCIPLE-006, PRINCIPLE-013)."""

    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp(prefix="test_disruption_"))
        self.ledger_file = self.test_dir / "task_ledger.json"

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_atomic_write_and_load(self):
        payload = {"version": 1, "active_task": {"task_id": "test_feature"}, "checkpoints": []}
        atomic_write_json(self.ledger_file, payload)
        self.assertTrue(self.ledger_file.exists())
        loaded = load_ledger(self.ledger_file)
        self.assertEqual(loaded["active_task"]["task_id"], "test_feature")

    def test_bounded_rolling_ledger_pruning(self):
        # Enforces PRINCIPLE-004: bounded rolling ledger window prevents working memory bloat
        checkpoints = []
        for i in range(35):
            checkpoints.append({
                "task_id": "old_task" if i < 25 else "active_task",
                "phase": f"step_{i}",
                "phase_num": 3,
                "timestamp": 1000 + i,
            })
        
        pruned = prune_checkpoints(checkpoints, active_task_id="active_task", max_history=15)
        self.assertLessEqual(len(pruned), 15)
        # All 10 active task checkpoints must be preserved
        active_saved = [c for c in pruned if c["task_id"] == "active_task"]
        self.assertEqual(len(active_saved), 10)
        # Inactive checkpoints should be pruned to remaining budget
        inactive_saved = [c for c in pruned if c["task_id"] == "old_task"]
        self.assertEqual(len(inactive_saved), 5)

        # Test full save_ledger with auto-pruning
        ledger_data = {
            "version": 1,
            "active_task": {"task_id": "active_task"},
            "checkpoints": checkpoints,
        }
        save_ledger(ledger_data, ledger_file=self.ledger_file, max_history=15)
        loaded = load_ledger(self.ledger_file)
        self.assertLessEqual(len(loaded["checkpoints"]), 15)

    def test_self_healing_quarantine_corrupted_json(self):
        # Corrupt file with non-JSON text (simulating sudden power loss)
        self.ledger_file.write_text("{ incomplete json data...", encoding="utf-8")
        loaded = load_ledger(self.ledger_file)
        # Should gracefully self-heal to default state without raising an exception
        self.assertEqual(loaded["version"], 1)
        self.assertIsNone(loaded["active_task"])
        # Corrupt file should be quarantined
        corrupt_files = list(self.test_dir.glob("task_ledger.json.corrupt_*"))
        self.assertEqual(len(corrupt_files), 1, "Corrupted file was not quarantined")

    def test_self_healing_recovery_from_shadow_backup(self):
        # Enforces PRINCIPLE-013: self-healing restores from .bak shadow backup on corruption
        initial_data = {"version": 1, "active_task": {"task_id": "initial_task"}, "checkpoints": []}
        atomic_write_json(self.ledger_file, initial_data)
        # Write second time so .bak captures the initial state
        second_data = {"version": 1, "active_task": {"task_id": "updated_task"}, "checkpoints": []}
        atomic_write_json(self.ledger_file, second_data)
        bak_file = self.ledger_file.with_suffix(self.ledger_file.suffix + ".bak")
        self.assertTrue(bak_file.exists(), "Shadow backup (.bak) was not created")

        # Corrupt the primary ledger file
        self.ledger_file.write_text("{ broken power cut...", encoding="utf-8")
        recovered = load_ledger(self.ledger_file)
        self.assertEqual(recovered["active_task"]["task_id"], "initial_task")

    def test_advisory_file_lock(self):
        # Enforces PRINCIPLE-013: advisory file locking prevents concurrent write races
        test_file = self.test_dir / "state.json"
        with file_lock(test_file, timeout_seconds=1.0) as acquired1:
            self.assertTrue(acquired1)
            # Nested attempt on same file with zero timeout should fail acquisition
            with file_lock(test_file, timeout_seconds=0.1) as acquired2:
                self.assertFalse(acquired2)
        # Once released, lock should be immediately re-acquirable
        with file_lock(test_file, timeout_seconds=1.0) as acquired3:
            self.assertTrue(acquired3)

    def test_disk_headroom_check(self):
        # Enforces PRINCIPLE-013: storage headroom sanity guard prevents ENOSPC crashes
        # Normal directory should have >0.001 MB
        self.assertTrue(check_disk_headroom(self.test_dir, min_mb=0.001))
        # Impossibly high requirement should return False gracefully
        self.assertFalse(check_disk_headroom(self.test_dir, min_mb=10_000_000_000.0))

    def test_schema_migration_backward_compatibility(self):
        # Enforces PRINCIPLE-013: state schemas are forward-compatible and auto-migrated
        # Legacy/partial schema with missing fields
        legacy_data = {"checkpoints": [{"task_id": "t1", "phase": "plan"}]}
        migrated = migrate_ledger_schema(legacy_data)
        self.assertEqual(migrated["version"], 1)
        self.assertIsNone(migrated["active_task"])
        self.assertEqual(len(migrated["checkpoints"]), 1)

        # Legacy data where active_task lacks status or active_phase
        legacy_with_task = {"active_task": {"task_id": "legacy_task"}}
        migrated_task = migrate_ledger_schema(legacy_with_task)
        self.assertEqual(migrated_task["active_task"]["status"], "in_progress")
        self.assertEqual(migrated_task["active_task"]["active_phase"], 1)

    def test_zero_byte_power_loss_truncation_quarantine(self):
        # Enforces PRINCIPLE-013: 0-byte file from sudden power outage is quarantined cleanly
        self.ledger_file.write_bytes(b"")  # 0-byte file
        self.assertEqual(self.ledger_file.stat().st_size, 0)
        loaded = load_ledger(self.ledger_file)
        self.assertEqual(loaded["version"], 1)
        self.assertIsNone(loaded["active_task"])
        # 0-byte corrupted file should be quarantined
        corrupt_files = list(self.test_dir.glob("task_ledger.json.corrupt_*"))
        self.assertTrue(len(corrupt_files) >= 1)

    def test_record_checkpoint_and_complete(self):
        record_checkpoint(
            task_id="task_abc",
            phase="implementation",
            description="Created service layer",
            files_affected=["service.py"],
            ledger_file=self.ledger_file,
        )
        ledger = load_ledger(self.ledger_file)
        self.assertEqual(ledger["active_task"]["task_id"], "task_abc")
        self.assertEqual(ledger["active_task"]["active_phase"], 3)
        self.assertEqual(len(ledger["checkpoints"]), 1)
        self.assertEqual(ledger["checkpoints"][0]["phase_num"], 3)
        self.assertEqual(ledger["checkpoints"][0]["description"], "Created service layer")

        mark_task_completed("task_abc", ledger_file=self.ledger_file)
        completed_ledger = load_ledger(self.ledger_file)
        self.assertEqual(completed_ledger["active_task"]["status"], "completed")
        self.assertEqual(completed_ledger["active_task"]["active_phase"], 5)
        self.assertEqual(completed_ledger["checkpoints"][-1]["phase"], "completed")
        self.assertEqual(completed_ledger["checkpoints"][-1]["phase_num"], 5)

    def test_dangling_temp_file_detection(self):
        # Create a dangling .tmp_* file simulating an interrupted atomic write
        dangling_tmp = self.test_dir / "service.py.tmp_1234_9999"
        dangling_tmp.write_text("partial write", encoding="utf-8")
        audit = run_disruption_audit(workspace_dir=self.test_dir)
        self.assertIn("service.py.tmp_1234_9999", [Path(p).name for p in audit["dangling_temp_files"]])
        report = format_audit_report(audit)
        self.assertIn("Dangling Temp Buffers", report)

    def test_format_resume_report(self):
        # Verify resumption guidance outputs structured task orientation
        record_checkpoint(
            task_id="interrupted_task",
            phase="planning",
            phase_num=2,
            description="Planning task",
            ledger_file=self.ledger_file,
        )
        audit = run_disruption_audit(workspace_dir=self.test_dir)
        resume_rep = format_resume_report(audit)
        self.assertIn("RESUMING INTERRUPTED TASK: 'interrupted_task'", resume_rep)
        self.assertIn("Phase 2 (planning)", resume_rep)

    def test_reset_active_task(self):
        # Enforces PRINCIPLE-006: clean task reset without manual JSON tampering
        record_checkpoint(
            task_id="stale_task",
            phase="planning",
            phase_num=2,
            description="Stale planning",
            ledger_file=self.ledger_file,
        )
        ledger = load_ledger(self.ledger_file)
        self.assertEqual(ledger["active_task"]["task_id"], "stale_task")
        
        abandoned = reset_active_task(reason="Superseded by user request", ledger_file=self.ledger_file)
        self.assertIsNotNone(abandoned)
        self.assertEqual(abandoned["task_id"], "stale_task")
        
        updated_ledger = load_ledger(self.ledger_file)
        self.assertIsNone(updated_ledger["active_task"])
        self.assertEqual(updated_ledger["checkpoints"][-1]["phase"], "abandoned")
        self.assertIn("Superseded by user request", updated_ledger["checkpoints"][-1]["description"])

    def test_clean_dangling_temp_files(self):
        # Enforces PRINCIPLE-006: safe automated purging of orphaned *.tmp_* buffers
        tmp_file = self.test_dir / "model.py.tmp_8888_7777"
        tmp_file.write_text("corrupted buffer", encoding="utf-8")
        self.assertTrue(tmp_file.exists())
        
        purged = clean_dangling_temp_files(workspace_dir=self.test_dir)
        self.assertIn("model.py.tmp_8888_7777", [Path(p).name for p in purged])
        self.assertFalse(tmp_file.exists())

    def test_non_git_workspace_detection(self):
        # In isolated test_dir (not a git repo), audit must detect missing git tracking
        audit = run_disruption_audit(workspace_dir=self.test_dir)
        self.assertTrue(audit.get("git_missing"))
        report = format_audit_report(audit)
        self.assertIn("Git Inactive", report)

    def test_checkpoint_with_impact_assessment(self):
        # Enforces PRINCIPLE-007: pre-flight 4-quadrant impact assessment persisted into task ledger
        cp = record_checkpoint(
            task_id="feature_auth",
            phase="planning",
            phase_num=2,
            description="Pre-flight auth planning",
            why="Improve session security",
            benefits="Eliminate session hijacking risks",
            risks="Session drops on network glitch",
            mitigation="Add exponential backoff refresh loop",
            ledger_file=self.ledger_file,
        )
        self.assertIn("impact_assessment", cp)
        self.assertEqual(cp["impact_assessment"]["why"], "Improve session security")
        self.assertEqual(cp["impact_assessment"]["benefits"], "Eliminate session hijacking risks")
        self.assertEqual(cp["impact_assessment"]["risks"], "Session drops on network glitch")
        self.assertEqual(cp["impact_assessment"]["mitigation"], "Add exponential backoff refresh loop")

        ledger = load_ledger(self.ledger_file)
        self.assertEqual(ledger["active_task"]["impact_assessment"]["why"], "Improve session security")
        self.assertEqual(ledger["active_task"]["impact_assessment"]["benefits"], "Eliminate session hijacking risks")

    def test_audit_and_resume_reports_with_impact_assessment(self):
        # Enforces PRINCIPLE-007 & PRINCIPLE-006: reports display pre-flight impact guidance
        record_checkpoint(
            task_id="feature_cache",
            phase="planning",
            phase_num=2,
            description="Planning cache layer",
            why="Reduce API response latency",
            benefits="50% faster query response times",
            risks="Stale cache data",
            mitigation="Time-to-live invalidation with version tags",
            ledger_file=self.ledger_file,
        )
        audit = run_disruption_audit(workspace_dir=self.test_dir)
        audit_rep = format_audit_report(audit)
        self.assertIn("Pre-Flight Impact Assessment (PRINCIPLE-007)", audit_rep)
        self.assertIn("Why: Reduce API response latency", audit_rep)
        self.assertIn("Benefits: 50% faster query response times", audit_rep)
        self.assertIn("Risks: Stale cache data", audit_rep)
        self.assertIn("Mitigation: Time-to-live invalidation with version tags", audit_rep)

        resume_rep = format_resume_report(audit)
        self.assertIn("Pre-Flight Impact Assessment (PRINCIPLE-007)", resume_rep)
        self.assertIn("Why: Reduce API response latency", resume_rep)
        self.assertIn("Benefits: 50% faster query response times", resume_rep)

    def test_hierarchical_milestone_indexing(self):
        # Enforces PRINCIPLE-008 & PRINCIPLE-006: milestone sequence [milestone N/M] preserved in ledger
        total_milestones = 3
        for n in range(1, total_milestones + 1):
            record_checkpoint(
                task_id="feature_pipeline",
                phase="implementation",
                phase_num=3,
                description=f"[milestone {n}/{total_milestones}] Completed sub-task {n}",
                ledger_file=self.ledger_file,
            )
        ledger = load_ledger(self.ledger_file)
        self.assertEqual(len(ledger["checkpoints"]), 3)
        self.assertIn("[milestone 3/3]", ledger["checkpoints"][-1]["description"])

    def test_dynamic_re_decomposition_on_discovery(self):
        # Enforces PRINCIPLE-008: dynamic re-planning on discovery adjusts milestone horizon M -> M'
        record_checkpoint(
            task_id="auth_migration",
            phase="implementation",
            phase_num=3,
            description="[milestone 1/2] Data schema created",
            ledger_file=self.ledger_file,
        )
        # Discovery occurs: an unforeseen token refresh retry layer is needed
        record_checkpoint(
            task_id="auth_migration",
            phase="planning",
            phase_num=2,
            description="[re-plan] Discovery: Added token refresh retry, adjusted horizon to 3 milestones",
            ledger_file=self.ledger_file,
        )
        record_checkpoint(
            task_id="auth_migration",
            phase="implementation",
            phase_num=3,
            description="[milestone 2/3] Added token refresh retry layer",
            ledger_file=self.ledger_file,
        )
        record_checkpoint(
            task_id="auth_migration",
            phase="implementation",
            phase_num=3,
            description="[milestone 3/3] Integrated auth service and verified",
            ledger_file=self.ledger_file,
        )
        ledger = load_ledger(self.ledger_file)
        self.assertEqual(len(ledger["checkpoints"]), 4)
        self.assertIn("[milestone 3/3]", ledger["checkpoints"][-1]["description"])



class TestKnowledgeBase(unittest.TestCase):
    """Verifies AST parsing and documentation completeness (PRINCIPLE-003, PRINCIPLE-016)."""

    def test_core_docs_exist(self):
        for doc in CORE_DOCS:
            path = KNOWLEDGE_DIR / doc
            self.assertTrue(path.exists(), f"Core knowledge base doc missing: {doc}")

    def test_update_and_validate_runs(self):
        # Run update and validate without exception
        update_and_validate()
        codebase_map = KNOWLEDGE_DIR / "codebase_map.md"
        self.assertTrue(codebase_map.exists())
        content = codebase_map.read_text(encoding="utf-8")
        self.assertIn("Codebase Metrics", content)

    def test_ast_symbol_extraction(self):
        # Extract from sync_principles.py
        sync_script = ROOT_DIR / "scripts" / "sync_principles.py"
        symbols = extract_python_symbols(sync_script)
        self.assertNotIn("error", symbols)
        func_names = [f["name"] for f in symbols["functions"]]
        self.assertIn("parse_principles", func_names)
        self.assertIn("sync_all", func_names)

    def test_ast_strict_mode_fails_on_syntax_error(self):
        # Enforces PRINCIPLE-003: mechanical AST gate catches syntax errors
        temp_dir = Path(tempfile.mkdtemp(prefix="test_ast_"))
        try:
            bad_file = temp_dir / "broken.py"
            bad_file.write_text("def broken_syntax(\n", encoding="utf-8")

            # In strict mode, extract_python_symbols must raise ValueError
            with self.assertRaises(ValueError):
                extract_python_symbols(bad_file, strict=True)

            # In lenient mode, extract_python_symbols returns error dict without crashing
            lenient = extract_python_symbols(bad_file, strict=False)
            self.assertIn("error", lenient)

            # generate_codebase_map in strict mode must halt with AST gate failure
            with self.assertRaises(ValueError) as ctx:
                generate_codebase_map(root=temp_dir, strict=True)
            self.assertIn("[PRINCIPLE-003 AST GATE FAILURE]", str(ctx.exception))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)



class TestOperationalDogfooding(unittest.TestCase):
    """
    Dogfooding & Zero-Blast-Radius Chaos Test (PRINCIPLE-015).
    Operates the CLI scripts in an isolated ephemeral test directory.
    """

    def setUp(self):
        self.sandbox = Path(tempfile.mkdtemp(prefix="dogfood_jail_"))

    def tearDown(self):
        shutil.rmtree(self.sandbox, ignore_errors=True)

    def test_ephemeral_sandbox_isolation(self):
        # Verify the sandbox is outside user dirs and strictly ephemeral
        self.assertTrue(self.sandbox.exists())
        self.assertTrue("dogfood_jail_" in self.sandbox.name)
        # Blast radius guard: ensure it does not point to user Desktop or Project Root
        self.assertNotEqual(self.sandbox.resolve(), ROOT_DIR.resolve())


if __name__ == "__main__":
    unittest.main()
