"""
Automated Test Suite for Portable Agent Kit (PRINCIPLE-011, PRINCIPLE-016)
Validates principle synchronization, disruption recovery atomicity,
knowledge base AST generation, and operational dogfooding.
"""

import contextlib
import io
import os
import re
import sys
import json
import shutil
import tempfile
import unittest
from pathlib import Path

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import scripts.sync_principles as sync_principles_module
from scripts.sync_principles import (
    parse_principles,
    sync_all,
    validate_triad_consistency,
    load_tier_1b_domain_rules,
    append_domain_rules,
    AGENTS_MD,
    GUIDELINES_MD,
    README_MD,
    TARGET_TOKEN_BUDGET,
    TIER1_TARGETS,
    SSOT_MD,
    audit_tier1_budget,
    estimate_tokens,
    render_tier1_target,
    is_generated_target,
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
from scripts.check_secrets import (
    scan_text,
    shannon_entropy,
    run_scan,
    STRONG_ALLOWLIST,
    WEAK_ALLOWLIST,
)
from scripts.check_reachability import (
    find_unreachable,
    find_phantom_keys,
    collect_definitions,
    production_modules,
    PUBLIC_API_ALLOWLIST,
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


def not_a_git_repo(workspace):
    """In-process stand-in for `git status` in a non-repository: exactly what real git returns
    (exit 128) without spawning a process, keeping the unit tier spawn-free (PRINCIPLE-014 R3)."""
    return 128, "", "fatal: not a git repository (or any of the parent directories): .git"


# Single source of truth for the principle count, so adding a principle updates one place.
EXPECTED_PRINCIPLE_COUNT = 19


class TestPrincipleSync(unittest.TestCase):
    """Verifies that all 19 principles are maintained and synchronized (PRINCIPLE-001, PRINCIPLE-017)."""

    def test_parse_all_principles(self):
        principles = parse_principles(SSOT_MD)
        self.assertEqual(len(principles), EXPECTED_PRINCIPLE_COUNT,
                         f"Expected {EXPECTED_PRINCIPLE_COUNT} principles, got {len(principles)}")
        p_ids = [p["id"] for p in principles]
        for i in range(1, 19):
            expected_id = f"PRINCIPLE-{i:03d}"
            self.assertIn(expected_id, p_ids, f"Missing {expected_id} in {SSOT_MD.name}")
        for p in principles:
            self.assertTrue(p["invariant"], f"Principle {p['id']} is missing an invariant capsule")

    def test_monotonic_lifecycle_phase_alignment(self):
        # Enforces PRINCIPLE-002: principles must belong to monotonic phases 1 through 5
        principles = parse_principles(SSOT_MD)
        self.assertEqual(len(principles), EXPECTED_PRINCIPLE_COUNT)
        current_phase = 1
        for p in principles:
            self.assertIn("phase_num", p)
            self.assertGreaterEqual(p["phase_num"], current_phase, f"Phase inversion detected at {p['id']}")
            current_phase = p["phase_num"]
        self.assertEqual(current_phase, 5, "Principles did not reach Phase 5")

    def test_targets_in_sync_and_budgeted(self):
        # Every generated Tier 1 target must be fresh against the SSOT and within budget (PRINCIPLE-001)
        principles = parse_principles(SSOT_MD)
        self.assertEqual(len(principles), EXPECTED_PRINCIPLE_COUNT)
        targets = [ROOT_DIR / rel for rel in TIER1_TARGETS]
        for target in targets:
            self.assertTrue(target.exists(), f"Target file missing: {target}")
            content = target.read_text(encoding="utf-8")
            # Every principle, not a sample of them.
            for p in principles:
                self.assertIn(p["id"], content, f"{p['id']} missing from {target.name}")
            # The deterministic grep contract itself (PRINCIPLE-001 R5), not a label naming it.
            self.assertIn("### PRINCIPLE-XXX:", content, f"Grep anchor missing from {target.name}")
            self.assertIn("GUIDELINES.md", content, f"Tier 2 pointer missing from {target.name}")
            # PRINCIPLE-001 R3 lives in the header now that it is no longer duplicated in a capsule;
            # this is what stops the retrieval-trigger protocol from silently vanishing.
            for trigger in ("contract change", "failure", "ambiguity"):
                self.assertIn(trigger, content, f"R3 '{trigger}' trigger missing from {target.name}")
            self.assertIn("never the whole file", content,
                          f"{target.name} no longer forbids loading Tier 2 wholesale")
            self.assertIn("wins on conflict", content,
                          f"{target.name} does not state that GUIDELINES.md wins on conflict (R1)")
            self.assertIn("Generated from", content,
                          f"{target.name} is not marked as generated; hand edits would be lost")
            # The enforced token budget, which is stricter than the old 8,000-char cap.
            self.assertLessEqual(
                len(content) // 4, TARGET_TOKEN_BUDGET,
                f"Governance bloat in {target.name}: ~{len(content) // 4} tokens > {TARGET_TOKEN_BUDGET}",
            )

    def test_principle_003_anti_hallucination_capsule(self):
        # Enforces PRINCIPLE-003: verified invariant capsule with slice freshness, call-sites, and platform parity
        principles = parse_principles(SSOT_MD)
        p3 = next((p for p in principles if p["id"] == "PRINCIPLE-003"), None)
        self.assertIsNotNone(p3)
        self.assertIn("slice freshness", p3["invariant"].lower())
        self.assertIn("call-site", p3["invariant"].lower())
        self.assertIn("platform parity", p3["invariant"].lower())
        self.assertIn("ast syntax gate", p3["invariant"].lower())

    def test_principle_004_compaction_resilience_capsule(self):
        # Enforces PRINCIPLE-004: verified invariant capsule with task_ledger, living plan SSOT, anti-repetition
        principles = parse_principles(SSOT_MD)
        p4 = next((p for p in principles if p["id"] == "PRINCIPLE-004"), None)
        self.assertIsNotNone(p4)
        self.assertIn("task_ledger.json", p4["invariant"].lower())
        self.assertIn("living plan ssot", p4["invariant"].lower())
        self.assertIn("anti-repetition", p4["invariant"].lower())
        self.assertIn("ast-first", p4["invariant"].lower())
        self.assertIn("bounded rolling ledger", p4["invariant"].lower())

    def test_principle_005_cold_start_capsule(self):
        # Enforces PRINCIPLE-005: verified invariant capsule with 30s orientation, token ceiling, command parity, whole-tree drift shield
        principles = parse_principles(SSOT_MD)
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
        principles = parse_principles(SSOT_MD)
        p6 = next((p for p in principles if p["id"] == "PRINCIPLE-006"), None)
        self.assertIsNotNone(p6)
        self.assertIn("incremental atomic micro-commits", p6["invariant"].lower())
        self.assertIn("pre-flight disruption audit", p6["invariant"].lower())
        self.assertIn("disruption_recovery.py", p6["invariant"].lower())
        self.assertIn("explicit micro-staging", p6["invariant"].lower())

    def test_principle_014_regression_shield_capsule(self):
        # Enforces PRINCIPLE-014: verified invariant capsule with 100% test pass gate, sub-second execution, test sanctity, RAII fixture reversion, anti-tautology, and negative path coverage
        principles = parse_principles(SSOT_MD)
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
        principles = parse_principles(SSOT_MD)
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
        principles = parse_principles(SSOT_MD)
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
        principles = parse_principles(SSOT_MD)
        p17 = next((p for p in principles if p["id"] == "PRINCIPLE-017"), None)
        self.assertIsNotNone(p17)
        self.assertIn("sync_principles.py", p17["invariant"].lower())
        self.assertIn("context budget check", p17["invariant"].lower())
        self.assertIn("schema compliance", p17["invariant"].lower())
        self.assertIn("freshness test gate", p17["invariant"].lower())
        self.assertIn("tier 1b domain rules", p17["invariant"].lower())

    def test_principle_018_git_workflow_capsule(self):
        # Enforces PRINCIPLE-018: verified invariant capsule with conventional commits, adaptive push, explicit staging, pre-commit triad, and non-destructive recoil
        principles = parse_principles(SSOT_MD)
        p18 = next((p for p in principles if p["id"] == "PRINCIPLE-018"), None)
        self.assertIsNotNone(p18)
        self.assertIn("automatic conventional commits", p18["invariant"].lower())
        self.assertIn("adaptive push", p18["invariant"].lower())
        self.assertIn("explicit staging", p18["invariant"].lower())
        self.assertIn("zero `git add .`", p18["invariant"].lower())
        self.assertIn("pre-commit delivery triad", p18["invariant"].lower())
        self.assertIn("non-destructive recoil", p18["invariant"].lower())

    def test_guideline_targets_freshness_gate(self):
        # Enforces PRINCIPLE-017: every generated Tier 1 target must be 100% in sync with the SSOT.
        # Diagnostics are buffered (PRINCIPLE-012 R3) and replayed only on failure.
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            mismatches = sync_all(check_only=True, exit_on_mismatch=False)
        self.assertEqual(
            mismatches,
            0,
            f"{mismatches} AI guideline targets are out of sync with {SSOT_MD.name}. "
            f"Run 'py scripts/sync_principles.py' to synchronize. "
            f"Diagnostics: {buffer.getvalue()}"
        )

    def test_triad_consistency_gate(self):
        # Enforces PRINCIPLE-017 R4: README.md, the triad's public leg, lists every principle in the
        # single SSOT. (The former AGENTS.md <-> GUIDELINES.md title-parity check is gone because
        # the second copy is gone, by design - see ADR-048.)
        principles = parse_principles(SSOT_MD)
        errors = validate_triad_consistency(principles)
        self.assertEqual(errors, [], f"Triad documentation drift detected: {errors}")

        # Negative path: a README that omits a principle must be caught.
        temp_dir = Path(tempfile.mkdtemp(prefix="test_triad_drift_"))
        self.addCleanup(shutil.rmtree, temp_dir, ignore_errors=True)
        partial_readme = temp_dir / "README.md"
        partial_readme.write_text(
            "\n".join(p["id"] for p in principles if p["id"] != "PRINCIPLE-019"), encoding="utf-8"
        )
        drift_errors = validate_triad_consistency(principles, readme_file=partial_readme)
        self.assertEqual(drift_errors, ["PRINCIPLE-019 missing from README.md"])

        missing = validate_triad_consistency(principles, readme_file=temp_dir / "absent.md")
        self.assertTrue(any("README.md missing" in e for e in missing))

    def test_checklists_cover_every_principle(self):
        # Red-green pin: PRINCIPLE-019 shipped absent from both checklists, and no test noticed.
        text = SSOT_MD.read_text(encoding="utf-8")
        pre_start = text.index("Pre-Flight Checklist")
        post_start = text.index("Post-Flight Checklist")
        pre, post = text[pre_start:post_start], text[post_start:]
        post = post[: post.find("\n## ")] if "\n## " in post else post
        for p in parse_principles(SSOT_MD):
            with self.subTest(pid=p["id"]):
                self.assertIn(p["id"], pre, f"{p['id']} missing from the Pre-Flight checklist")
                self.assertIn(p["id"], post, f"{p['id']} missing from the Post-Flight checklist")

    def test_no_stale_principle_counts_in_docs(self):
        # Red-green pin: seven prose references still said "18" after PRINCIPLE-019 landed,
        # including PRINCIPLE-001's own "immutable 18". Any count phrase must match reality.
        actual = len(parse_principles(SSOT_MD))
        pattern = re.compile(
            r"\b(\d+)\s+(?:universal\s+|engineering\s+|core\s+|active\s+)?(?:principles|invariants)\b",
            re.IGNORECASE,
        )
        for doc in (SSOT_MD, README_MD):
            for match in pattern.finditer(doc.read_text(encoding="utf-8")):
                with self.subTest(doc=doc.name, phrase=match.group(0)):
                    self.assertEqual(int(match.group(1)), actual,
                                     f"{doc.name} says '{match.group(0)}' but there are {actual}")

    def test_principle_count_constants_agree(self):
        # Adding a principle means raising both constants; if they disagree, one was forgotten.
        actual = len(parse_principles(SSOT_MD))
        self.assertEqual(sync_principles_module.MIN_PRINCIPLES, actual,
                         "MIN_PRINCIPLES in scripts/sync_principles.py is stale")
        self.assertEqual(EXPECTED_PRINCIPLE_COUNT, actual,
                         "EXPECTED_PRINCIPLE_COUNT in tests/test_kit.py is stale")

    def test_adopter_readme_without_principles_is_not_drift(self):
        # Red-green pin: forcing every adopting project's product README to list AIKit's principle
        # IDs failed their very first sync with 19 TRIAD DRIFT errors. A README that documents no
        # principles is an adopter's choice; only a partial listing is drift.
        principles = parse_principles(SSOT_MD)
        readme = Path(tempfile.mkdtemp(prefix="test_adopter_readme_")) / "README.md"
        self.addCleanup(shutil.rmtree, readme.parent, ignore_errors=True)
        readme.write_text("# Acme Widget Service\n\nOur product README.\n", encoding="utf-8")
        self.assertEqual(validate_triad_consistency(principles, readme_file=readme), [])

    def test_aikit_readme_lists_every_principle_strictly(self):
        # The adopter rule above must never let AIKit itself drop its principles table: AIKit's
        # own README is held to the full listing independently of the tool's leniency.
        readme = README_MD.read_text(encoding="utf-8")
        for p in parse_principles(SSOT_MD):
            with self.subTest(pid=p["id"]):
                self.assertIn(p["id"], readme, f"{p['id']} missing from AIKit's README.md")

    def test_single_ssot_and_generated_agents_md(self):
        # ADR-048: the rules live in exactly one hand-edited file. AGENTS.md - auto-loaded by
        # AGENTS.md-convention agents - is a generated, budgeted Tier 1 target, not a second copy.
        agents = (ROOT_DIR / "AGENTS.md").read_text(encoding="utf-8")
        self.assertTrue(is_generated_target(agents), "AGENTS.md is not a generated target")
        self.assertNotIn("- **Rules**:", agents, "AGENTS.md carries the full rule bodies again")
        self.assertLessEqual(len(agents) // 4, TARGET_TOKEN_BUDGET)
        self.assertIn("AGENTS.md", TIER1_TARGETS)
        self.assertEqual(SSOT_MD.name, "GUIDELINES.md")
        guidelines = SSOT_MD.read_text(encoding="utf-8")
        for p in parse_principles(SSOT_MD):
            with self.subTest(pid=p["id"]):
                self.assertEqual(guidelines.count(f"### {p['id']}:"), 1,
                                 f"{p['id']} must have exactly one heading in the SSOT")

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

    def test_last_principle_block_stops_at_next_section(self):
        # Red-green pin: the final principle's block used to run to end-of-file, so a field in a
        # trailing appendix could satisfy that principle's schema. Here the last principle lacks an
        # Invariant and only the appendix has one; strict parsing must reject it.
        doc = Path(tempfile.mkdtemp(prefix="test_bounds_")) / "ssot.md"
        self.addCleanup(shutil.rmtree, doc.parent, ignore_errors=True)
        doc.write_text(
            "## Phase 5: Delivery\n"
            "### PRINCIPLE-001: Complete\n- **Concept**: A\n- **Invariant**: B\n- **Rules**:\n  1. R\n\n"
            "### PRINCIPLE-002: Missing Invariant\n- **Concept**: C\n- **Rules**:\n  1. R\n\n"
            "## Appendix\n- **Invariant**: belongs to no principle\n",
            encoding="utf-8",
        )
        with self.assertRaises(ValueError) as ctx:
            parse_principles(doc, strict=True)
        self.assertIn("PRINCIPLE-002", str(ctx.exception))
        self.assertIn("Invariant", str(ctx.exception))

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
            "scripts/dogfood.py",
            "scripts/check_reachability.py",
            "scripts/check_secrets.py",
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


class TestPrinciple001Unambiguity(unittest.TestCase):
    """
    PRINCIPLE-001 must say the same thing to every model. These tests make that mechanical:
    no hedge words, every rule states who it binds, and the Tier 1 header uses the exact trigger
    and precedence wording of the Tier 2 rules it summarises.
    """

    HEDGES = ("e.g.", "etc.", "relevant", "proactively", "essential", "excessive", "concise",
              "dense", "appropriate", "as needed", "~", "should", "where possible", "mentally")

    @classmethod
    def setUpClass(cls):
        text = SSOT_MD.read_text(encoding="utf-8")
        start = text.index("### PRINCIPLE-001:")
        end = text.index("\n### PRINCIPLE-002:")
        cls.section = text[start:end]
        cls.rules = cls.section[cls.section.index("- **Rules**:"):]

    def test_rules_contain_no_hedge_words(self):
        lowered = self.rules.lower()
        found = [h for h in self.HEDGES if h in lowered]
        self.assertEqual(found, [], f"PRINCIPLE-001 rules contain open-ended wording: {found}")

    def test_every_rule_names_its_audience(self):
        numbered = re.findall(r"^  (\d+)\. \*\*([^*]+)\*\*([^\n]*)", self.rules, re.M)
        self.assertEqual(len(numbered), 9, "PRINCIPLE-001 must keep rules R1-R9 (cited elsewhere)")
        for number, title, rest in numbered:
            with self.subTest(rule=f"R{number}"):
                self.assertRegex(rest, r"\*\[(Agent|Maintainer|Agent \+ Maintainer)\]\*",
                                 f"R{number} {title} does not say whom it binds")

    def test_rules_use_normative_keywords(self):
        # RFC 2119 keywords, declared once in the GUIDELINES.md header, carry the obligations.
        self.assertIn("RFC 2119", SSOT_MD.read_text(encoding="utf-8").split("### PRINCIPLE-001:")[0])
        for keyword in ("MUST", "MUST NOT", "MAY"):
            self.assertIn(keyword, self.rules)

    def test_tier1_header_mirrors_r3_triggers_and_r1_precedence(self):
        # The header is what most agents actually read; it must use R3's own trigger names.
        triggers = re.findall(r"\*([A-Za-z-]+) trigger\*", self.rules)
        self.assertEqual(triggers, ["Contract-change", "Failure", "Ambiguity"])
        header = render_tier1_target("# probe", parse_principles(SSOT_MD)).split("## Core Principles")[0]
        for trigger in triggers:
            with self.subTest(trigger=trigger):
                self.assertIn(trigger.lower().replace("-", " "), header.lower())
        self.assertIn("wins on conflict", header)
        self.assertIn("GUIDELINES.md", self.rules.split("*Precedence*")[1].split("\n")[0])

    def test_tool_neutral_retrieval(self):
        # IDE-specific tool names make other agents guess an equivalent.
        for tool_name in ("view_file", "grep_search", "Query="):
            self.assertNotIn(tool_name, self.section, f"tool-specific term '{tool_name}' in P001")


class TestSyncWriteSafety(unittest.TestCase):
    """
    ADR-048. Sync now writes AGENTS.md, which older layouts used as the hand-authored rule source,
    and adopters often keep their own CLAUDE.md. Sync must therefore never overwrite a file it did
    not generate, must decide that for every target before writing any, and must explain an
    unmigrated layout instead of crashing. Each test runs the real sync_all in a sandbox.
    """

    def setUp(self):
        self.sandbox = Path(tempfile.mkdtemp(prefix="test_sync_safety_"))
        self.addCleanup(shutil.rmtree, self.sandbox, ignore_errors=True)
        (self.sandbox / "README.md").write_text(README_MD.read_text(encoding="utf-8"), encoding="utf-8")
        (self.sandbox / "GUIDELINES.md").write_text(SSOT_MD.read_text(encoding="utf-8"), encoding="utf-8")
        for name, value in (
            ("ROOT_DIR", self.sandbox),
            ("SSOT_MD", self.sandbox / "GUIDELINES.md"),
            ("AGENTS_MD", self.sandbox / "AGENTS.md"),
            ("DOMAIN_RULES_PATH", self.sandbox / ".agents" / "rules" / "domain.md"),
        ):
            self.addCleanup(setattr, sync_principles_module, name, getattr(sync_principles_module, name))
            setattr(sync_principles_module, name, value)

    def _sync(self, check_only=False):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            result = sync_principles_module.sync_all(
                check_only=check_only, exit_on_mismatch=False, readme_file=self.sandbox / "README.md"
            )
        return result, out.getvalue()

    def _written_targets(self):
        return [rel for rel in TIER1_TARGETS if (self.sandbox / rel).exists()]

    def test_clean_sandbox_generates_every_target(self):
        result, _ = self._sync()
        self.assertEqual(result, 0)
        self.assertEqual(sorted(self._written_targets()), sorted(TIER1_TARGETS))

    def test_hand_authored_file_is_never_overwritten(self):
        own = "# My project's own Claude rules\n- Use tabs, never spaces.\n"
        (self.sandbox / "CLAUDE.md").write_text(own, encoding="utf-8")
        result, output = self._sync()
        self.assertGreater(result, 0, "sync overwrote or ignored a hand-authored target")
        self.assertEqual((self.sandbox / "CLAUDE.md").read_text(encoding="utf-8"), own,
                         "an adopter's own CLAUDE.md was modified")
        self.assertIn("[PROTECTED]", output)
        self.assertIn("CLAUDE.md", output)
        self.assertIn("Fix:", output, "protection message lacks a remediation step")
        self.assertNotIn("Traceback", output)

    def test_protection_is_all_or_nothing(self):
        # PRINCIPLE-013 R6: one protected file must not leave the other targets half-written.
        (self.sandbox / "CLAUDE.md").write_text("# hand written\n", encoding="utf-8")
        self._sync()
        self.assertEqual(self._written_targets(), ["CLAUDE.md"],
                         "other targets were written despite a protected conflict")

    def test_legacy_generated_target_is_upgraded(self):
        # Files written by pre-ADR-048 AIKit carry "(Tier 1 Invariants)" and must stay upgradable.
        (self.sandbox / "CLAUDE.md").write_text(
            "# Claude AI Assistant Guidelines\n\n## Core Principles (Tier 1 Invariants):\n1. old\n",
            encoding="utf-8",
        )
        result, _ = self._sync()
        self.assertEqual(result, 0)
        self.assertIn("Generated from `GUIDELINES.md`",
                      (self.sandbox / "CLAUDE.md").read_text(encoding="utf-8"))

    def test_unmigrated_layout_gets_migration_guidance_not_a_traceback(self):
        # The pre-ADR-048 layout: full rules in AGENTS.md, a Problem/Guideline GUIDELINES.md.
        (self.sandbox / "AGENTS.md").write_text(SSOT_MD.read_text(encoding="utf-8"), encoding="utf-8")
        (self.sandbox / "GUIDELINES.md").write_text(
            "### PRINCIPLE-001: Legacy\n- **Problem**: p\n- **Guideline**:\n  - g\n", encoding="utf-8"
        )
        legacy_agents = (self.sandbox / "AGENTS.md").read_text(encoding="utf-8")
        result, output = self._sync()
        self.assertEqual(result, 1)
        self.assertIn("[MIGRATION REQUIRED]", output)
        self.assertIn("Fix:", output)
        self.assertNotIn("Traceback", output)
        self.assertEqual((self.sandbox / "AGENTS.md").read_text(encoding="utf-8"), legacy_agents,
                         "the legacy rule source was modified before migration")
        self.assertEqual(self._written_targets(), ["AGENTS.md"], "targets written before migration")

    def test_generated_marker_detection(self):
        self.assertTrue(is_generated_target("> Generated from `GUIDELINES.md` by ..."))
        self.assertTrue(is_generated_target("## Core Principles (Tier 1 Invariants):"))
        self.assertFalse(is_generated_target("# Our team's Claude notes\n- prefer small PRs\n"))
        self.assertFalse(is_generated_target(""))


class TestTier1ContextBudget(unittest.TestCase):
    """
    PRINCIPLE-001 R6/R9. Always-injected rules cost context on every turn in every IDE, so the
    token target must be enforced rather than advisory - an advisory warning is exactly how it
    came to be silently breached while reporting BUDGET PASS.
    """

    TARGETS = tuple(ROOT_DIR / rel for rel in TIER1_TARGETS)

    def test_every_target_is_within_the_token_target(self):
        for target in self.TARGETS:
            with self.subTest(target=target.name):
                chars = len(target.read_text(encoding="utf-8"))
                est_tokens = chars // 4
                self.assertLessEqual(
                    est_tokens, TARGET_TOKEN_BUDGET,
                    f"{target.name} is {chars} chars (~{est_tokens} tokens), over the "
                    f"{TARGET_TOKEN_BUDGET}-token Tier 1 target. PRINCIPLE-001 R9: condense "
                    f"existing capsules to pay for any expansion.",
                )

    def test_token_overage_blocks_rather_than_warns(self):
        # Red-green pin: tighten the target so the current corpus becomes an overage and assert
        # the gate returns non-zero. Previously this path only printed a warning and passed.
        original = sync_principles_module.TARGET_TOKEN_BUDGET
        self.addCleanup(setattr, sync_principles_module, "TARGET_TOKEN_BUDGET", original)
        sync_principles_module.TARGET_TOKEN_BUDGET = 1
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            result = sync_all(check_only=True, exit_on_mismatch=False)
        self.assertGreater(result, 0, "token overage did not block the gate")
        self.assertIn("TOKEN EXCEEDED", buffer.getvalue())
        self.assertIn("Fix: condense capsule narrative", buffer.getvalue(),
                      "budget failure lacks a remediation step (PRINCIPLE-011 R6)")
        self.assertIn("never mechanisms", buffer.getvalue(),
                      "remediation does not protect mechanisms from compression (PRINCIPLE-001 R2)")

    def test_shipped_domain_template_syncs_within_budget(self):
        # Red-green pin. Once the token target became enforced, copying the shipped template to
        # domain.md - exactly what PRINCIPLE-017 R6 instructs adopters to do - blocked sync on all
        # five targets. The universal rules must leave the full Tier 1B allowance free.
        template = ROOT_DIR / ".agents" / "rules" / "domain.md.template"
        domain = load_tier_1b_domain_rules(template)
        self.assertTrue(domain, "shipped template is empty")
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            violations = audit_tier1_budget(parse_principles(SSOT_MD), domain)
        self.assertEqual(
            violations, 0,
            f"Adopters cannot use the shipped Tier 1B template:\n{buffer.getvalue()}",
        )

    def test_universal_rules_reserve_full_tier1b_headroom(self):
        # The check that would have caught the regression above before any adopter hit it.
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            violations = audit_tier1_budget(parse_principles(SSOT_MD), "")
        self.assertEqual(violations, 0, f"Tier 1B headroom breached:\n{buffer.getvalue()}")
        self.assertNotIn("TIER 1B HEADROOM", buffer.getvalue())

    def test_headroom_breach_is_detected(self):
        # Prove the reservation check bites: shrink the budget until universal rules fit but a
        # full Tier 1B block would not.
        principles = parse_principles(SSOT_MD)
        tier1a = max(len(render_tier1_target(h, principles)) for h in TIER1_TARGETS.values()) // 4
        original = sync_principles_module.TARGET_TOKEN_BUDGET
        self.addCleanup(setattr, sync_principles_module, "TARGET_TOKEN_BUDGET", original)
        sync_principles_module.TARGET_TOKEN_BUDGET = tier1a + 50  # fits 1A, not 1A + 300-token 1B
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            violations = audit_tier1_budget(principles, "")
        self.assertGreater(violations, 0, "reservation check did not detect a Tier 1B shortfall")
        self.assertIn("TIER 1B HEADROOM", buffer.getvalue())

    def test_advisory_warning_cannot_shadow_a_violation(self):
        # Red-green pin. A 7,200-char "warn" branch sat ahead of the token check in an if/elif
        # chain, so a ~1,860-token target printed BUDGET WARN and passed.
        principles = parse_principles(SSOT_MD)
        principles[0] = dict(principles[0], invariant=principles[0]["invariant"] + " " + "x" * 2700)
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(buffer):
            violations = audit_tier1_budget(principles, "")
        self.assertEqual(violations, len(TIER1_TARGETS),
                         "an over-budget target must be exactly one violation per target")
        self.assertNotIn("BUDGET WARN", buffer.getvalue(),
                         "an over-budget target was downgraded to an advisory warning")

    def test_token_estimate_is_conservative(self):
        # chars // 4 was calibrated at ~4.2 chars/token against cl100k_base and o200k_base on this
        # corpus, i.e. it over-counts. Pin the ratio so a future estimator cannot under-count.
        sample = "x" * 4200
        self.assertEqual(estimate_tokens(sample), 1050)
        self.assertGreaterEqual(estimate_tokens(sample), 4200 / 4.2,
                                "estimator under-counts relative to the measured ratio")

    def test_grep_anchor_contract_survives_in_every_target(self):
        # Per-principle markdown anchors were removed to pay down the budget; the deterministic
        # grep contract (PRINCIPLE-001 R5) is what replaces them and must be present in each.
        for target in self.TARGETS:
            with self.subTest(target=target.name):
                content = target.read_text(encoding="utf-8")
                self.assertIn("### PRINCIPLE-XXX:", content,
                              f"{target.name} lost the deterministic grep anchor contract")
                self.assertIn("GUIDELINES.md", content,
                              f"{target.name} no longer points at Tier 2 knowledge")

    def test_capsules_retain_their_mechanisms_after_condensation(self):
        # PRINCIPLE-001 R2: compression targets narrative, never hard mechanical constraints.
        content = (ROOT_DIR / ".agents" / "rules" / "principles.md").read_text(encoding="utf-8")
        for mechanism in ("os.replace", "fsync", "100% test pass gate", "<1s",
                          "scripts/sync_principles.py", "task_ledger.json",
                          "advisory locking", "exit"):
            with self.subTest(mechanism=mechanism):
                self.assertIn(mechanism, content,
                              f"condensation stripped the mechanism '{mechanism}'")


class TestSecretHygieneScanner(unittest.TestCase):
    """
    PRINCIPLE-019. Secret leakage is the one defect class with no clean rollback, so the scanner
    must be proven against real credential shapes rather than trusted. Each fixture below is a
    syntactically valid credential *shape* using published documentation values or invented
    strings - no live secret appears in this repository.
    """

    def test_detects_known_credential_shapes(self):
        cases = {
            "AWS access key id": 'AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7NOTREAL"',  # aikit:allow-secret
            "GitHub token": 'tok = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"',  # aikit:allow-secret
            "Slack token": 'tok = "xoxb-1234567890-abcdefghijklmnop"',  # aikit:allow-secret
            "Google API key": 'k = "AIzaSyB1cD3fG5hJ7kL9mN1pQ3rS5tU7vW9xY2z"',  # aikit:allow-secret
            "Stripe secret key": 'k = "sk_live_abcdefghijklmnopqrstuvwx"',  # aikit:allow-secret
            "Password in URL": 'dsn = "postgres://admin:s3cretPassw0rd@db.internal:5432/app"',  # aikit:allow-secret
            "Private key block": "-----BEGIN RSA PRIVATE KEY-----",  # aikit:allow-secret
            "Hardcoded password assignment": 'password = "correcthorsebattery"',  # aikit:allow-secret
        }
        for detector, line in cases.items():
            with self.subTest(detector=detector):
                findings = scan_text("fixture.py", line)
                self.assertTrue(findings, f"{detector} was not detected in: {line}")
                self.assertEqual(findings[0][2], detector, f"misclassified: {findings[0]}")

    def test_does_not_flag_indirection_or_placeholders(self):
        safe = [
            'api_key = os.getenv("API_KEY")',
            'token = os.environ.get("TOKEN")',
            'API_KEY=<your-key-here>',
            'password = "changeme"',
            'secret = "${VAULT_SECRET}"',  # aikit:allow-secret
            'key = "placeholder"',
            'hard_coded = "short"',
        ]
        for line in safe:
            with self.subTest(line=line):
                self.assertEqual(scan_text("fixture.py", line), [],
                                 f"false positive on safe line: {line}")

    def test_weak_allowlist_cannot_veto_a_pattern_match(self):
        # Red-green pin: the scanner first MISSED "AKIAIOSFODNN7EXAMPLE" purely because the line  # aikit:allow-secret
        # contained the word "example". A weak hint must never suppress a high-confidence match,
        # or a live key on an "# example usage" line would sail through.
        line = '# example usage: AWS_KEY = "AKIAIOSFODNN7NOTREAL"'  # aikit:allow-secret
        findings = scan_text("fixture.py", line)
        self.assertTrue(findings, "a weak allowlist word suppressed a pattern match")
        self.assertEqual(findings[0][2], "AWS access key id")

    def test_weak_allowlist_still_suppresses_entropy_fallback(self):
        # The low-confidence detector should defer to an "example" hint.
        line = 'example_token = "a9f3c81e2b7d45069af13c2e8b5d7049"'
        self.assertEqual(scan_text("fixture.py", line), [],
                         "weak allowlist should suppress the entropy fallback")

    def test_explicit_pragma_suppresses_everything(self):
        line = 'tok = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"  # aikit:allow-secret'
        self.assertEqual(scan_text("fixture.py", line), [],
                         "explicit pragma did not suppress the finding")

    def test_entropy_separates_random_from_prose(self):
        self.assertGreater(shannon_entropy("f3a9c81e2b7d45069af13c2e8b5d7049"), 3.5)
        self.assertLess(shannon_entropy("aaaaaaaaaaaaaaaaaaaaaaaa"), 1.0)
        self.assertEqual(shannon_entropy(""), 0.0)

    def test_agent_memory_free_text_is_scanned(self):
        # PRINCIPLE-019 R3: the ledger's impact fields are git-tracked, so a credential quoted
        # while explaining reasoning becomes permanent history.
        leaky = 'why = "rotate ghp_abcdefghijklmnopqrstuvwxyz0123456789 after deploy"'  # aikit:allow-secret
        self.assertTrue(scan_text("agent-memory:task_ledger.json", leaky),
                        "a credential in ledger free-text was not detected")

    # The whole-repository scan (`run_scan(mode="all")`) shells out to `git ls-files`, so it lives
    # in tests/test_integration.py; the unit tier may not spawn processes, even indirectly.

    def test_gitignore_carries_the_credential_baseline(self):
        # PRINCIPLE-019 R2: protection added after a leak is protection that already failed.
        ignore = (ROOT_DIR / ".gitignore").read_text(encoding="utf-8")
        for surface in (".env", "*.pem", "*.key", "id_rsa*", "credentials", "secrets.*", "*.tfvars"):
            with self.subTest(surface=surface):
                self.assertIn(surface, ignore, f".gitignore does not exclude {surface}")


class TestInvariantReachabilityShield(unittest.TestCase):
    """
    PRINCIPLE-014 R7. A passing test proves a mechanism works, never that it is used. These
    tests reconstruct the two real defects the shield was written for, so the shield itself
    cannot rot into a checker that only ever reports OK.
    """

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="test_reach_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)

    def _write(self, name, source):
        (self.dir / name).write_text(source, encoding="utf-8")
        return sorted(self.dir.glob("*.py"))

    def test_detects_capability_with_zero_production_call_sites(self):
        # Reconstruction of the real defect: file_lock() was defined, exported and unit-tested
        # with no production caller, so parallel agents erased each other's checkpoints.
        files = self._write("mod_a.py", '''"""Ledger."""
import contextlib
import sys

@contextlib.contextmanager
def my_advisory_lock(path):
    """Defined, exported and unit-tested - but wired into nothing."""
    yield True

def do_work(task):
    return {"task": task}

if __name__ == "__main__":
    do_work(sys.argv[1])
''')
        unreachable = [name for name, _ in find_unreachable(files)]
        self.assertIn(
            "my_advisory_lock", unreachable,
            "shield failed to detect a tested-but-unwired safety mechanism",
        )
        self.assertNotIn("do_work", unreachable, "shield flagged a referenced function")

    def test_detects_state_key_read_with_no_producer(self):
        # Reconstruction of the real defect: format_resume_report() read 'last_phase_num',
        # which no writer ever produced, so every resumption returned a default phase.
        files = self._write("mod_b.py", '''"""Reports."""
def build(active):
    return active.get("last_phase_num", 2)
''')
        phantom = [key for key, _ in find_phantom_keys(files)]
        self.assertIn(
            "last_phase_num", phantom,
            "shield failed to detect a reader keyed to a field nothing writes",
        )

    def test_key_with_a_producer_is_not_flagged(self):
        files = self._write("mod_c.py", '''"""Round trip."""
def write(v):
    return {"active_phase": v}

def read(d):
    return d.get("active_phase", 1)
''')
        phantom = [key for key, _ in find_phantom_keys(files)]
        self.assertNotIn("active_phase", phantom, "shield flagged a key that round-trips")

    def test_this_repository_passes_the_shield(self):
        # The live invariant: AIKit's own production modules must stay reachable.
        files = production_modules()
        self.assertGreaterEqual(len(files), 4, "no production modules discovered")
        unreachable = find_unreachable(files)
        self.assertEqual(
            unreachable, [],
            f"Unwired capabilities in scripts/: {unreachable}. Wire them into the path they "
            f"protect, delete them, or allowlist them as deliberate public API.",
        )
        phantom = find_phantom_keys(files)
        self.assertEqual(phantom, [], f"State keys read with no producer: {phantom}")

    def test_allowlist_entries_still_exist(self):
        # An allowlist that outlives its symbols silently stops shielding anything.
        defined = set(collect_definitions(production_modules()))
        stale = sorted(name for name in PUBLIC_API_ALLOWLIST if name not in defined)
        self.assertEqual(
            stale, [],
            f"PUBLIC_API_ALLOWLIST names symbols that no longer exist: {stale}",
        )


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

    def test_workflow_yaml_has_no_unquoted_colon_scalars(self):
        # Red-green pin (PRINCIPLE-014 R6): the first CI push was rejected outright because
        # `run: python -c "...'stdlib-only: no install step required'"` is a plain YAML scalar
        # containing ": ", which the parser reads as a nested mapping. A stdlib-only repo has no
        # PyYAML to validate with, so pin the exact failure mode instead of trusting review.
        offenders = []
        for lineno, line in enumerate(self.workflow_text.splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("#") or not stripped:
                continue
            match = re.match(r"^(?:- )?(run|name|if|shell):\s+(.*)$", stripped)
            if not match:
                continue
            value = match.group(2)
            # Block scalars and fully quoted values are safe; plain scalars are not.
            if value in ("|", ">", "|-", ">-") or value.startswith(("'", '"')):
                continue
            if ": " in value:
                offenders.append(f"line {lineno}: {stripped[:70]}")
        self.assertEqual(
            offenders, [],
            "Unquoted YAML scalar contains ': ' and will be parsed as a mapping, rejecting the "
            f"whole workflow. Use a block scalar (run: |) or quote the value. Offenders: {offenders}",
        )

    def test_workflow_uses_no_tabs(self):
        # Tabs are illegal for YAML indentation and reject the workflow at parse time.
        self.assertNotIn("\t", self.workflow_text, "TAB character in workflow YAML is illegal")


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
        audit = run_disruption_audit(workspace_dir=self.test_dir, git_status=not_a_git_repo)
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
        audit = run_disruption_audit(workspace_dir=self.test_dir, git_status=not_a_git_repo)
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
        audit = run_disruption_audit(workspace_dir=self.test_dir, git_status=not_a_git_repo)
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
        audit = run_disruption_audit(workspace_dir=self.test_dir, git_status=not_a_git_repo)
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
