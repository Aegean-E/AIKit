"""
Automated Test Suite for Portable Agent Kit (PRINCIPLE-011, PRINCIPLE-016)
Validates principle synchronization, disruption recovery atomicity,
knowledge base AST generation, and operational dogfooding.
"""

import contextlib
import io
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

from scripts.sync_principles import (
    parse_principles,
    sync_all,
    validate_triad_consistency,
    load_tier_1b_domain_rules,
    append_domain_rules,
    AGENTS_MD,
    GUIDELINES_MD,
    README_MD,
)
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
    locked_ledger,
    resolve_active_phase,
    classify_git_status,
    UNMERGED_CODES,
    fsync_dir,
    check_disk_headroom,
    migrate_ledger_schema,
    validate_conventional_commit,
)
from scripts.update_knowledge_base import (
    extract_python_symbols,
    generate_codebase_map,
    update_and_validate,
    validate_knowledge_links,
    check_codebase_map_freshness,
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

    def test_principle_014_regression_shield_capsule(self):
        # Enforces PRINCIPLE-014: verified invariant capsule with 100% test pass gate, sub-second execution, test sanctity, RAII fixture reversion, anti-tautology, and negative path coverage
        principles = parse_principles(AGENTS_MD)
        p14 = next((p for p in principles if p["id"] == "PRINCIPLE-014"), None)
        self.assertIsNotNone(p14)
        self.assertIn("100% test pass gate", p14["invariant"].lower())
        self.assertIn("<1s", p14["invariant"].lower())
        self.assertIn("test sanctity invariant", p14["invariant"].lower())
        self.assertIn("raii fixture reversion", p14["invariant"].lower())
        self.assertIn("anti-tautological observable contracts", p14["invariant"].lower())
        self.assertIn("hostile & negative path coverage", p14["invariant"].lower())

    def test_principle_015_operational_dogfooding_capsule(self):
        # Enforces PRINCIPLE-015: verified invariant capsule with domain-specific dogfooding, portable process tree teardown, safety jail, non-interactive stdin parity, golden path + chaos perturbation, and terse reporting
        principles = parse_principles(AGENTS_MD)
        p15 = next((p for p in principles if p["id"] == "PRINCIPLE-015"), None)
        self.assertIsNotNone(p15)
        self.assertIn("domain-specific interactive dogfooding", p15["invariant"].lower())
        self.assertIn("portable raii process tree teardown", p15["invariant"].lower())
        self.assertIn("ephemeral safety jail", p15["invariant"].lower())
        self.assertIn("non-interactive stdin parity", p15["invariant"].lower())
        self.assertIn("golden path + chaos perturbation", p15["invariant"].lower())
        self.assertIn("terse reporting", p15["invariant"].lower())

    def test_principle_016_knowledge_base_capsule(self):
        # Enforces PRINCIPLE-016: verified invariant capsule with canonical sync, atomic code-and-doc pairing, append-only ADRs, AST gating, link shield, and update_knowledge_base.py
        principles = parse_principles(AGENTS_MD)
        p16 = next((p for p in principles if p["id"] == "PRINCIPLE-016"), None)
        self.assertIsNotNone(p16)
        self.assertIn("canonical `knowledge/` sync", p16["invariant"].lower())
        self.assertIn("atomic code-and-doc pairing", p16["invariant"].lower())
        self.assertIn("monotonic append-only adr register", p16["invariant"].lower())
        self.assertIn("strict ast syntax validation", p16["invariant"].lower())
        self.assertIn("link integrity shield", p16["invariant"].lower())
        self.assertIn("update_knowledge_base.py", p16["invariant"].lower())

    def test_principle_017_auto_sync_capsule(self):
        # Enforces PRINCIPLE-017: verified invariant capsule with automated sync, budget check, schema compliance, freshness test gate, and Tier 1B domain rules
        principles = parse_principles(AGENTS_MD)
        p17 = next((p for p in principles if p["id"] == "PRINCIPLE-017"), None)
        self.assertIsNotNone(p17)
        self.assertIn("sync_principles.py", p17["invariant"].lower())
        self.assertIn("context budget check", p17["invariant"].lower())
        self.assertIn("schema compliance", p17["invariant"].lower())
        self.assertIn("freshness test gate", p17["invariant"].lower())
        self.assertIn("tier 1b domain rules", p17["invariant"].lower())

    def test_principle_018_git_workflow_capsule(self):
        # Enforces PRINCIPLE-018: verified invariant capsule with conventional commits, adaptive push, explicit staging, pre-commit triad, and non-destructive recoil
        principles = parse_principles(AGENTS_MD)
        p18 = next((p for p in principles if p["id"] == "PRINCIPLE-018"), None)
        self.assertIsNotNone(p18)
        self.assertIn("automatic conventional commits", p18["invariant"].lower())
        self.assertIn("adaptive push", p18["invariant"].lower())
        self.assertIn("explicit staging", p18["invariant"].lower())
        self.assertIn("zero `git add .`", p18["invariant"].lower())
        self.assertIn("pre-commit delivery triad", p18["invariant"].lower())
        self.assertIn("non-destructive recoil", p18["invariant"].lower())

    def test_guideline_targets_freshness_gate(self):
        # Enforces PRINCIPLE-017: all 5 IDE prompt files must be 100% in sync with AGENTS.md.
        # Diagnostics are buffered (PRINCIPLE-012 R3) and replayed only on failure.
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            mismatches = sync_all(check_only=True, exit_on_mismatch=False)
        self.assertEqual(
            mismatches,
            0,
            f"{mismatches} AI guideline targets are out of sync with AGENTS.md. "
            f"Run 'py scripts/sync_principles.py' to synchronize. "
            f"Diagnostics: {buffer.getvalue()}"
        )

    def test_triad_consistency_gate(self):
        # Enforces PRINCIPLE-017: AGENTS.md, GUIDELINES.md, and README.md must have 100% principle and title parity
        principles = parse_principles(AGENTS_MD)
        errors = validate_triad_consistency(principles)
        self.assertEqual(errors, [], f"Triad documentation drift detected: {errors}")

        # Negative path: verify that mismatched heading title in GUIDELINES.md is caught
        temp_dir = Path(tempfile.mkdtemp(prefix="test_triad_drift_"))
        try:
            bad_guidelines = temp_dir / "GUIDELINES.md"
            bad_guidelines.write_text("### PRINCIPLE-001: Wrong Mismatched Title\n", encoding="utf-8")
            drift_errors = validate_triad_consistency(principles[:1], guidelines_file=bad_guidelines, readme_file=README_MD)
            self.assertTrue(any("does not match AGENTS.md" in e for e in drift_errors))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_principle_schema_strictness(self):
        # Enforces PRINCIPLE-017: principles with missing schema components or duplicate IDs must raise ValueError
        temp_dir = Path(tempfile.mkdtemp(prefix="test_schema_"))
        try:
            # Missing concept
            bad_doc = temp_dir / "bad1.md"
            bad_doc.write_text("### PRINCIPLE-099: Broken Schema\n- **Invariant**: Test\n- **Rules**:\n  1. Do something.\n", encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                parse_principles(bad_doc, strict=True)
            self.assertIn("[PRINCIPLE-017 SCHEMA VIOLATION]", str(ctx.exception))

            # Missing invariant
            bad_doc = temp_dir / "bad2.md"
            bad_doc.write_text("### PRINCIPLE-099: Broken Schema\n- **Concept**: Test\n- **Rules**:\n  1. Do something.\n", encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                parse_principles(bad_doc, strict=True)
            self.assertIn("[PRINCIPLE-017 SCHEMA VIOLATION]", str(ctx.exception))

            # Missing rules
            bad_doc = temp_dir / "bad3.md"
            bad_doc.write_text("### PRINCIPLE-099: Broken Schema\n- **Concept**: Test\n- **Invariant**: Test\n", encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                parse_principles(bad_doc, strict=True)
            self.assertIn("[PRINCIPLE-017 SCHEMA VIOLATION]", str(ctx.exception))

            # Duplicate principle ID
            bad_doc = temp_dir / "bad4.md"
            bad_doc.write_text(
                "### PRINCIPLE-001: First\n- **Concept**: A\n- **Invariant**: B\n- **Rules**:\n  1. R1\n\n"
                "### PRINCIPLE-001: Duplicate\n- **Concept**: C\n- **Invariant**: D\n- **Rules**:\n  1. R2\n",
                encoding="utf-8"
            )
            with self.assertRaises(ValueError) as ctx:
                parse_principles(bad_doc, strict=True)
            self.assertIn("[PRINCIPLE-017 SCHEMA VIOLATION] Duplicate principle ID detected: PRINCIPLE-001", str(ctx.exception))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_tier_1b_domain_rules_injection(self):
        # Enforces PRINCIPLE-001 & PRINCIPLE-017: Tier 1B domain rules can be loaded and appended within budget
        temp_dir = Path(tempfile.mkdtemp(prefix="test_domain_"))
        try:
            domain_file = temp_dir / "domain.md"
            domain_file.write_text("- Framework: React 19\n- Database: SQLite\n- Strict linting enabled\n", encoding="utf-8")
            loaded = load_tier_1b_domain_rules(domain_file)
            self.assertIn("React 19", loaded)

            # Test appending
            lines = ["# Title", ""]
            append_domain_rules(lines, loaded)
            content = "\n".join(lines)
            self.assertIn("Project Domain Invariants (Tier 1B)", content)
            self.assertIn("React 19", content)

            # Test budget ceiling overflow (>1200 chars)
            oversized = "x" * 1205
            domain_file.write_text(oversized, encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                load_tier_1b_domain_rules(domain_file)
            self.assertIn("[PRINCIPLE-001 BUDGET EXCEEDED]", str(ctx.exception))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_domain_rules_template_validity(self):
        # Enforces PRINCIPLE-001 & PRINCIPLE-017: domain.md.template must exist and stay strictly within token budget
        template_path = ROOT_DIR / ".agents" / "rules" / "domain.md.template"
        self.assertTrue(template_path.exists(), "domain.md.template is missing in .agents/rules/")
        content = template_path.read_text(encoding="utf-8")
        self.assertLessEqual(len(content), 1200, f"domain.md.template exceeds 1,200 chars ({len(content)} chars)")
        self.assertIn("Stack & Runtime Constraints", content)
        self.assertIn("Domain Architectural Invariants", content)

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
            ".github/workflows/ci.yml",
            ".agents/rules/principles.md",
            ".agents/task_ledger.json",
            "scripts/sync_principles.py",
            "scripts/disruption_recovery.py",
            "scripts/update_knowledge_base.py",
            "tests/test_kit.py",
            "tests/test_integration.py",
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


class TestContinuousVerificationGate(unittest.TestCase):
    """
    The CI workflow must enforce the same gates the principles declare, using the same
    canonical commands the README documents (PRINCIPLE-005 R3, PRINCIPLE-018 R3). Without
    this shield, CI and the docs drift and the gates become decorative.
    """

    WORKFLOW = ROOT_DIR / ".github" / "workflows" / "ci.yml"

    @classmethod
    def setUpClass(cls):
        cls.workflow_text = cls.WORKFLOW.read_text(encoding="utf-8") if cls.WORKFLOW.exists() else ""

    def test_workflow_exists(self):
        self.assertTrue(
            self.WORKFLOW.exists(),
            "No CI workflow: every verification gate would run only on an agent's machine",
        )

    def test_workflow_runs_every_declared_gate(self):
        required = {
            "unit tier gate (PRINCIPLE-014)": "python -m unittest tests.test_kit",
            "integration tier (PRINCIPLE-015)": "python -m unittest tests.test_integration",
            "canonical suite (README)": "python -m unittest discover tests",
            "rule freshness (PRINCIPLE-017 R3)": "python scripts/sync_principles.py --check",
            "AST map freshness (PRINCIPLE-016 R4)": "python scripts/update_knowledge_base.py --check",
        }
        for label, command in required.items():
            with self.subTest(gate=label):
                self.assertIn(
                    command, self.workflow_text,
                    f"CI does not run the {label} gate via '{command}'",
                )

    def test_workflow_commands_match_documented_commands(self):
        # Executable command parity: anything CI runs must also be documented in README.md.
        readme = (ROOT_DIR / "README.md").read_text(encoding="utf-8")
        for command in (
            "python -m unittest discover tests",
            "python -m unittest tests.test_kit",
            "python -m unittest tests.test_integration",
            "python scripts/sync_principles.py --check",
            "python scripts/update_knowledge_base.py --check",
        ):
            with self.subTest(command=command):
                self.assertIn(command, readme, f"CI runs '{command}' but README.md never documents it")

    def test_workflow_covers_posix_and_windows(self):
        # PRINCIPLE-003 R4 / PRINCIPLE-011 R4: platform parity is only a claim until a POSIX
        # runner actually executes the paths this Windows-developed repo cannot exercise.
        for runner in ("ubuntu-latest", "windows-latest"):
            with self.subTest(runner=runner):
                self.assertIn(runner, self.workflow_text, f"CI matrix omits {runner}")

    def test_workflow_is_bounded_and_least_privileged(self):
        # PRINCIPLE-010 R3: bounded execution. No unbounded CI job.
        self.assertIn("timeout-minutes:", self.workflow_text, "CI job declares no timeout")
        self.assertIn("contents: read", self.workflow_text, "CI does not drop to read-only permissions")

    def test_workflow_asserts_pristine_tree(self):
        # PRINCIPLE-014 R4: running the suite must leave the tree bit-for-bit clean.
        self.assertIn("git status --porcelain", self.workflow_text,
                      "CI never verifies the suite left the working tree clean")


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
            # Nested attempt on same file must fail acquisition within its bounded timeout.
            # The timeout is kept short deliberately: the contract under test is refusal, and a
            # longer wall-clock wait only inflates the sub-second suite gate (PRINCIPLE-014 R3).
            with file_lock(test_file, timeout_seconds=0.03) as acquired2:
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

    def test_conventional_commit_validation(self):
        # Enforces PRINCIPLE-018: conventional commit syntax validation with milestone support
        valid_samples = [
            "feat(principles): add Principle 18 git workflow",
            "fix(auth): resolve token expiration bug",
            "refactor(core): streamline AST parser",
            "docs(readme): update quickstart guide",
            "chore(deps): update test fixtures",
            "test(kit): add regression test for recovery",
            "feat(pipeline): [milestone 1/3] create initial schema",
            "feat!: breaking change in public API contract",
        ]
        for msg in valid_samples:
            valid, reason = validate_conventional_commit(msg)
            self.assertTrue(valid, f"Expected '{msg}' to be valid, got: {reason}")

        invalid_samples = [
            "",
            "   ",
            "random commit message",
            "feat: ",
            "feat: wip",
            "fix: update",
            "unknown(core): something",
            "feat: " + ("a" * 80),  # exceeds 72 chars
        ]
        for msg in invalid_samples:
            valid, reason = validate_conventional_commit(msg)
            self.assertFalse(valid, f"Expected '{msg}' to be invalid")


class TestKnowledgeBase(unittest.TestCase):
    """Verifies AST parsing and documentation completeness (PRINCIPLE-003, PRINCIPLE-016)."""

    def test_core_docs_exist(self):
        for doc in CORE_DOCS:
            path = KNOWLEDGE_DIR / doc
            self.assertTrue(path.exists(), f"Core knowledge base doc missing: {doc}")

    def test_update_and_validate_runs(self):
        # Run update and validate hermetically in a mock knowledge directory (PRINCIPLE-014, PRINCIPLE-016)
        temp_k_dir = Path(tempfile.mkdtemp(prefix="test_k_dir_"))
        try:
            for doc in CORE_DOCS:
                doc_path = temp_k_dir / doc
                if doc == "INDEX.md":
                    doc_path.write_text("# Index\n[Architecture](architecture.md)\n", encoding="utf-8")
                else:
                    doc_path.write_text(f"# {doc}\n", encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                update_and_validate(knowledge_dir=temp_k_dir, strict=True)
            codebase_map = temp_k_dir / "codebase_map.md"
            self.assertTrue(codebase_map.exists())
            content = codebase_map.read_text(encoding="utf-8")
            self.assertIn("Codebase Metrics", content)
        finally:
            shutil.rmtree(temp_k_dir, ignore_errors=True)

    def test_codebase_map_freshness_gate(self):
        # Enforces PRINCIPLE-016: codebase_map.md must be 100% synchronized with physical codebase AST
        self.assertTrue(
            check_codebase_map_freshness(strict=True),
            "knowledge/codebase_map.md must be fresh and match current AST"
        )

    def test_codebase_map_freshness_stale_detection(self):
        # Negative path (PRINCIPLE-014): verify that stale codebase_map is detected and rejected
        temp_k_dir = Path(tempfile.mkdtemp(prefix="test_freshness_"))
        try:
            stale_map = temp_k_dir / "codebase_map.md"
            stale_map.write_text("# Stale Codebase Map\nNo metrics here.\n", encoding="utf-8")
            # In lenient mode, returns False
            self.assertFalse(check_codebase_map_freshness(knowledge_dir=temp_k_dir, strict=False))
            # In strict mode, raises ValueError
            with self.assertRaises(ValueError) as ctx:
                check_codebase_map_freshness(knowledge_dir=temp_k_dir, strict=True)
            self.assertIn("[PRINCIPLE-016 CODEBASE MAP STALE]", str(ctx.exception))
        finally:
            shutil.rmtree(temp_k_dir, ignore_errors=True)

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

    def test_link_integrity_shield(self):
        # Enforces PRINCIPLE-016: all links in INDEX.md physically exist on disk
        broken = validate_knowledge_links(KNOWLEDGE_DIR)
        self.assertEqual(broken, [], f"Broken links found in knowledge/INDEX.md: {broken}")



class TestConcurrencyAndResumptionCorrectness(unittest.TestCase):
    """
    Red-green defect pins for four invariants that reported green while broken in production
    (PRINCIPLE-014 R6). Each test reproduces a proven failure, not a restatement of the code.
    """

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="test_concurrency_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.ledger = self.dir / ".agents" / "task_ledger.json"

    def test_locked_ledger_serializes_read_modify_write(self):
        # The mutation must be visible on disk after the context exits, and the lock released.
        with locked_ledger(self.ledger) as ledger:
            ledger["checkpoints"].append({"task_id": "x", "timestamp": 1.0})
        self.assertEqual(len(load_ledger(self.ledger)["checkpoints"]), 1)
        lock = self.ledger.with_suffix(self.ledger.suffix + ".lock")
        self.assertFalse(lock.exists(), "advisory lock leaked after the context closed")

    def test_locked_ledger_surfaces_contention_instead_of_writing_unprotected(self):
        # PRINCIPLE-013 R3 + PRINCIPLE-011 R6: contention must raise an actionable error rather
        # than silently proceeding without the lock.
        self.ledger.parent.mkdir(parents=True, exist_ok=True)
        with file_lock(self.ledger, timeout_seconds=1.0) as held:
            self.assertTrue(held)
            with self.assertRaises(TimeoutError) as ctx:
                with locked_ledger(self.ledger, timeout_seconds=0.05):
                    pass
        message = str(ctx.exception)
        self.assertIn("LOCK CONTENTION", message)
        self.assertIn("Fix:", message, "contention error lacks a remediation step")

    def test_resume_reports_the_phase_actually_recorded(self):
        # PRINCIPLE-002 R4 / PRINCIPLE-004 R2: readers looked for a 'last_phase_num' key that was
        # never written, so every resumption reported Phase 2 and could send agents backwards.
        for recorded, label in ((3, "implementation"), (4, "verification"), (5, "delivery")):
            with self.subTest(phase=recorded):
                # Record through the real write path, then read the phase back off disk.
                led = self.dir / f"p{recorded}" / "task_ledger.json"
                record_checkpoint("t", label, "interrupted", phase_num=recorded, ledger_file=led)
                active = load_ledger(led)["active_task"]
                self.assertEqual(active["active_phase"], recorded)

                report = format_resume_report({"interrupted_task": active})
                self.assertIn(
                    f"Phase {recorded} ({label})", report,
                    f"resume report lost the recorded phase {recorded}",
                )
                self.assertNotIn("Phase 2 (verification)", report)

    def test_resume_never_recommends_an_earlier_phase(self):
        # PRINCIPLE-002 R1 monotonicity: resumption must not travel backwards through the lifecycle.
        for recorded in (1, 2, 3, 4, 5):
            with self.subTest(phase=recorded):
                active = {"task_id": "t", "active_phase": recorded, "status": "in_progress"}
                self.assertGreaterEqual(resolve_active_phase(active), recorded)

    def test_resolve_active_phase_honours_legacy_and_label_fallbacks(self):
        # Ledgers written before the fix, and ledgers with only a textual phase, stay recoverable.
        self.assertEqual(resolve_active_phase({"last_phase_num": 4}), 4)
        self.assertEqual(resolve_active_phase({"last_phase": "verification"}), 4)
        self.assertEqual(resolve_active_phase({"active_phase": 99, "last_phase": "delivery"}), 5)
        self.assertEqual(resolve_active_phase(None), 1)
        self.assertEqual(resolve_active_phase({}), 1)

    def test_fsync_dir_is_safe_and_platform_portable(self):
        # PRINCIPLE-013 R1 durability barrier; PRINCIPLE-003 R4 platform parity.
        self.assertTrue(fsync_dir(self.dir))
        self.assertTrue(fsync_dir(self.dir / "does-not-exist") or sys.platform != "win32")

    def test_ledger_paths_accept_strings_without_raw_tracebacks(self):
        # PRINCIPLE-011 R6: a str path previously raised a raw AttributeError from deep inside.
        led = self.dir / "str_path" / "task_ledger.json"
        led.parent.mkdir(parents=True, exist_ok=True)
        record_checkpoint("s", "phase 1", "string path", ledger_file=str(led))
        self.assertEqual(len(load_ledger(str(led))["checkpoints"]), 1)


class TestPorcelainClassification(unittest.TestCase):
    """
    Exhaustive table-driven coverage of `git status --porcelain` v1 classification
    (PRINCIPLE-006 R2, PRINCIPLE-014 R6). Pure function, no process spawns.
    """

    # (porcelain XY code, expected bucket) across every state git actually emits.
    CASES = (
        (" M", "modified"), ("M ", "modified"), ("MM", "modified"), ("AM", "modified"),
        ("A ", "modified"), (" D", "modified"), ("D ", "modified"), ("R ", "modified"),
        ("RM", "modified"), ("C ", "modified"), ("MD", "modified"), ("T ", "modified"),
        (" T", "modified"), ("AD", "modified"),
        ("??", "untracked"),
        ("UU", "conflicted"), ("AA", "conflicted"), ("DD", "conflicted"),
        ("AU", "conflicted"), ("UA", "conflicted"), ("DU", "conflicted"),
        ("UD", "conflicted"),
    )

    def test_every_porcelain_state_is_classified(self):
        for code, bucket in self.CASES:
            with self.subTest(code=code, expected=bucket):
                out = classify_git_status(f"{code} path/to/file.txt")
                self.assertEqual(
                    len(out[bucket]), 1,
                    f"porcelain state {code!r} was not classified as {bucket}; got {out}",
                )
                for other in ("modified", "untracked", "conflicted"):
                    if other != bucket:
                        self.assertEqual(out[other], [], f"{code!r} leaked into {other}")

    def test_no_real_state_is_silently_dropped(self):
        # The original defect: states absent from a whitelist vanished entirely.
        lines = "\n".join(f"{code} f{i}.txt" for i, (code, _) in enumerate(self.CASES))
        out = classify_git_status(lines)
        total = len(out["modified"]) + len(out["untracked"]) + len(out["conflicted"])
        self.assertEqual(
            total, len(self.CASES),
            f"{len(self.CASES) - total} porcelain state(s) silently dropped",
        )

    def test_conflict_states_carry_their_code_for_diagnostics(self):
        out = classify_git_status("UU merged.txt")
        self.assertEqual(out["conflicted"], ["UU merged.txt"])

    def test_ignored_and_blank_lines_are_skipped(self):
        out = classify_git_status("!! build/\n\n   \nM  real.txt")
        self.assertEqual(out["modified"], ["real.txt"])
        self.assertEqual(out["untracked"], [])
        self.assertEqual(out["conflicted"], [])

    def test_empty_output_is_clean(self):
        self.assertEqual(
            classify_git_status(""), {"modified": [], "untracked": [], "conflicted": []}
        )

    def test_paths_with_spaces_survive_classification(self):
        out = classify_git_status("?? my new file.txt")
        self.assertEqual(out["untracked"], ["my new file.txt"])


class TestAstSignatureFidelity(unittest.TestCase):
    """
    The symbol catalog is what agents consult before verifying call-sites (PRINCIPLE-004 R3), so
    omissions and partial signatures are anti-hallucination failures (PRINCIPLE-003 R1).
    """

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="test_ast_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def _probe(self, source):
        path = self.dir / "probe.py"
        path.write_text(source, encoding="utf-8")
        return extract_python_symbols(path, strict=True)

    def test_async_functions_and_methods_are_catalogued(self):
        info = self._probe(
            '"""M."""\n'
            "async def fetch(url):\n    return url\n\n"
            "def plain(a):\n    return a\n\n"
            "class S:\n"
            "    async def run(self, payload):\n        return payload\n"
            "    def stop(self):\n        return None\n"
        )
        names = {f["name"]: f for f in info["functions"]}
        self.assertIn("fetch", names, "async def was omitted from the symbol catalog")
        self.assertTrue(names["fetch"]["is_async"])
        self.assertFalse(names["plain"]["is_async"])

        methods = {m["name"]: m for m in info["classes"][0]["methods"]}
        self.assertIn("run", methods, "async method was omitted from the symbol catalog")
        self.assertTrue(methods["run"]["is_async"])
        self.assertFalse(methods["stop"]["is_async"])

    def test_full_signature_includes_varargs_kwonly_and_posonly(self):
        info = self._probe(
            '"""M."""\n'
            "def f(a, *args, kwonly, other=1, **kwargs):\n    return a\n\n"
            "def g(a, b, /, c):\n    return a\n\n"
            "def h(a, *, only_kw):\n    return a\n"
        )
        sigs = {fn["name"]: fn["args"] for fn in info["functions"]}
        self.assertEqual(sigs["f"], ["a", "*args", "kwonly", "other", "**kwargs"])
        self.assertEqual(sigs["g"], ["a", "b", "/", "c"])
        self.assertEqual(sigs["h"], ["a", "*", "only_kw"])

    def test_self_and_cls_are_dropped_from_method_signatures_only(self):
        info = self._probe(
            '"""M."""\n'
            "class S:\n"
            "    def m(self, a):\n        return a\n"
            "    @classmethod\n    def c(cls, b):\n        return b\n"
            "    @staticmethod\n    def s(x):\n        return x\n"
        )
        methods = {m["name"]: m["args"] for m in info["classes"][0]["methods"]}
        self.assertEqual(methods["m"], ["a"])
        self.assertEqual(methods["c"], ["b"])
        self.assertEqual(methods["s"], ["x"], "staticmethod first arg must be preserved")

    def test_generated_map_renders_async_keyword(self):
        # The rendered artifact, not just the extractor, must expose awaitability.
        (self.dir / "mod.py").write_text(
            '"""M."""\nasync def pull(src):\n    return src\n', encoding="utf-8"
        )
        with contextlib.redirect_stdout(io.StringIO()):
            rendered = generate_codebase_map(root=self.dir, strict=True)
        self.assertIn("async def pull(src)", rendered)


if __name__ == "__main__":
    unittest.main()
