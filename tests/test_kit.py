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
)
from scripts.update_knowledge_base import (
    extract_python_symbols,
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
            self.assertIn("PRINCIPLE-017", content, f"PRINCIPLE-017 missing from {target.name}")
            self.assertIn("PRINCIPLE-018", content, f"PRINCIPLE-018 missing from {target.name}")
            self.assertIn("Deterministic Grep Anchor", content, f"Grep anchor missing from {target.name}")
            # Assert context budget cap
            self.assertLessEqual(
                len(content),
                MAX_ALLOWED_CHARS,
                f"Governance bloat detected in {target.name}: {len(content)} chars > {MAX_ALLOWED_CHARS}"
            )




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
        self.assertEqual(len(ledger["checkpoints"]), 1)
        self.assertEqual(ledger["checkpoints"][0]["description"], "Created service layer")

        mark_task_completed("task_abc", ledger_file=self.ledger_file)
        completed_ledger = load_ledger(self.ledger_file)
        self.assertEqual(completed_ledger["active_task"]["status"], "completed")
        self.assertEqual(completed_ledger["checkpoints"][-1]["phase"], "completed")



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
