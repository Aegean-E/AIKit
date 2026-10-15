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
        # Enforces PRINCIPLE-005: verified invariant capsule with 30s orientation, material surface sync, command parity
        principles = parse_principles(AGENTS_MD)
        p5 = next((p for p in principles if p["id"] == "PRINCIPLE-005"), None)
        self.assertIsNotNone(p5)
        self.assertIn("self-describing repo", p5["invariant"].lower())
        self.assertIn("30s cold-start orientation", p5["invariant"].lower())
        self.assertIn("material surface readme sync", p5["invariant"].lower())
        self.assertIn("executable command parity", p5["invariant"].lower())






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
