"""
Automated Test Suite for Portable Agent Kit (PRINCIPLE-011, PRINCIPLE-016)
Validates principle synchronization, disruption recovery atomicity,
knowledge base AST generation, and operational dogfooding.
"""

import ast
import contextlib
import hashlib
import io
import os
import re
import sys
import json
import shutil
import subprocess  # imported only to refuse process spawns; see setUpModule
import tempfile
import time
import unittest
from unittest import mock
from pathlib import Path

# The unit tier must never start a process (PRINCIPLE-014 R3), directly or indirectly. While this
# module's tests run, any attempt fails the offending test immediately and names the command.
_REAL_POPEN_INIT = subprocess.Popen.__init__


def _refuse_spawn(popen_self, args, *unused_args, **unused_kwargs):
    raise AssertionError(
        f"unit tier tried to start a process: {args!r}. Inject a fake adapter "
        f"(PRINCIPLE-009 R4) or move the test to tests/test_integration.py."
    )


_REAL_FSYNC = os.fsync


def setUpModule():
    subprocess.Popen.__init__ = _refuse_spawn
    # A unit test cannot observe durability (only a power cut could), and a real fsync costs ~4ms
    # on Windows; the atomic-write tests check temp file, replace and .bak, which stay real.
    os.fsync = lambda fd: None


def tearDownModule():
    subprocess.Popen.__init__ = _REAL_POPEN_INIT
    os.fsync = _REAL_FSYNC

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

import scripts.sync_principles as sync_principles_module
from scripts.sync_principles import (
    parse_principles,
    citing_principles,
    principle_sections,
    MAX_DOMAIN_CHARS,
    changed_principles,
    cross_check_errors,
    render_readme_table,
    sync_readme_table,
    README_TABLE_BEGIN,
    README_TABLE_END,
    sync_all,
    validate_triad_consistency,
    load_tier_1b_domain_rules,
    append_domain_rules,
    AGENTS_MD,
    GUIDELINES_MD,
    README_MD,
    TARGET_TOKEN_BUDGET,
    TIER1_TARGETS,
    CLAUDE_AGENT_ROLES,
    render_claude_agent,
    SSOT_MD,
    audit_tier1_budget,
    estimate_tokens,
    render_tier1_target,
    is_generated_target,
    involved_principles,
)
from scripts.disruption_recovery import (
    LEDGER_SCHEMA_VERSION,
    UnsupportedLedgerVersion,
    LedgerOwnershipError,
    agent_history,
    UNIDENTIFIED_AGENT,
    load_ledger,
    resolve_agent,
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
    checkpoint_command,
    classify_track,
    parse_handoff,
    resolve_phase_num,
    task_plan_checkpoint,
    validate_argv,
    argv_value_errors,
    impact_errors,
    missing_impact_warning,
    report_operational_error,
    RISK_DIMENSIONS,
    sweep_files,
    workspace_ledger_path,
)
from scripts.aikit_cli import build_parser, main as aikit_main
from scripts.verify_commit import scanned_range, verify_commit
from scripts.subagent_delegate import (answer_text, delegate_subagent, direct_executable, is_free_model,
                                       opencode_command, subagent_roles)
from scripts.project_publish import (
    auto_push_project,
    extract_readme_description,
    get_project_repo_url,
    publish_project,
)


from scripts.project_gates import Gate, failure_tail, resolve_gates, run_gates
from scripts.project_license import license_state, public_remote_refusal, restrict_project
from scripts.project_registry import (
    GUIDELINES_TEMPLATE,
    _run_git,
    add_guideline,
    project_guidelines,
    ProjectError,
    Stack,
    attach_project,
    create_project,
    detect_stacks,
    find_project,
    latest_decision,
    list_projects,
    load_attached,
    load_config,
    AIKIT_BADGE,
    AIKIT_INTEGRATED_BADGE,
    AIKIT_URL,
    LEGACY_AIKIT_URL,
    add_aikit_badge,
    migrate_aikit_links,
    render_project_readme,
    validate_name,
)
from scripts.check_secrets import (
    scan_diff,
    scan_text,
    scrub_text,
    shannon_entropy,
    run_scan,
    STRONG_ALLOWLIST,
    WEAK_ALLOWLIST,
)
from scripts.check_project_hygiene import (
    check_asset_source,
    check_python_source,
    classify_artifacts,
    scan_artifacts,
    scan_tree,
)
from scripts.dogfood import repo_fingerprint
from scripts import ui_contract
from scripts import ui_proof
from scripts.check_test_budgets import (
    TIER_BUDGETS_MS,
    budget_errors,
    parse_tier_output,
    run_check as run_budget_check,
)
from scripts.check_reachability import (
    find_unreachable,
    find_phantom_keys,
    collect_definitions,
    production_modules,
    PUBLIC_API_ALLOWLIST,
)
from scripts.update_knowledge_base import (
    guideline_errors,
    extract_python_symbols,
    generate_codebase_map,
    update_and_validate,
    validate_knowledge_links,
    check_codebase_map_freshness,
    CORE_DOCS,
    KNOWLEDGE_DIR,
    MIN_PYTHON,
    README_LABELS,
    README_MAX_CHARS,
    README_TEMPLATE,
    audit_readme,
    check_readme,
    audit_adr_register,
    audit_lazy_code,
    audit_architecture,
    check_lazy_code,
    check_architecture,
    parse_source,
    find_python_files,
    parse_readme_tree,
    write_generated_file,
)


def not_a_git_repo(workspace):
    """In-process stand-in for `git status` in a non-repository: exactly what real git returns
    (exit 128) without spawning a process, keeping the unit tier spawn-free (PRINCIPLE-014 R3)."""
    return 128, "", "fatal: not a git repository (or any of the parent directories): .git"


# Single source of truth for the principle count, so adding a principle updates one place.
EXPECTED_PRINCIPLE_COUNT = 20


class TestPrincipleSync(unittest.TestCase):
    """Verifies that all 20 principles are maintained and synchronized (PRINCIPLE-001, PRINCIPLE-017)."""

    def test_parse_all_principles(self):
        principles = parse_principles(SSOT_MD)
        self.assertEqual(len(principles), EXPECTED_PRINCIPLE_COUNT,
                         f"Expected {EXPECTED_PRINCIPLE_COUNT} principles, got {len(principles)}")
        p_ids = [p["id"] for p in principles]
        for i in range(0, EXPECTED_PRINCIPLE_COUNT):
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
            self.assertIn("### PRINCIPLE-NNN:", content, f"Grep anchor missing from {target.name}")
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

    def test_agent_facing_role_texts_match_gate_limits(self):
        # ADR-157/159 raised the gates; a hand-written role file or runbook must not keep the old
        # number and make a sub-agent enforce a different contract.
        integration = TIER_BUDGETS_MS["tests.test_integration"]
        for rel in (".agents/skills/aikit/SKILL.md", ".claude/skills/aikit/SKILL.md"):
            text = (ROOT_DIR / rel).read_text(encoding="utf-8")
            self.assertIn(f"integration <={integration:g}ms", text, rel)
            self.assertNotIn("integration <=200ms", text, rel)
        for rel in (".opencode/agents/tester.md", ".claude/agents/tester.md"):
            text = (ROOT_DIR / rel).read_text(encoding="utf-8")
            self.assertIn(f"at most {integration:g}ms", text, rel)
            self.assertNotIn("at most 200ms", text, rel)
        for rel in (".opencode/agents/reviewer.md", ".claude/agents/reviewer.md"):
            text = (ROOT_DIR / rel).read_text(encoding="utf-8")
            self.assertIn(f"{README_MAX_CHARS:,} characters", text, rel)
            self.assertNotIn("20,000 characters", text, rel)

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
        # Enforces PRINCIPLE-004: the capsule names where the plan lives and how it is read back
        principles = parse_principles(SSOT_MD)
        p4 = next((p for p in principles if p["id"] == "PRINCIPLE-004"), None)
        self.assertIsNotNone(p4)
        self.assertIn("task_ledger.json", p4["invariant"].lower())
        # Mechanisms, not labels (ADR-061): which checkpoint is the plan, the cold-start
        # command, the anti-repetition rule, and the read/output cap.
        self.assertIn("plan = latest `[1/` phase 2 `--desc`", p4["invariant"].lower())
        self.assertIn("cold start `--resume`", p4["invariant"].lower())
        self.assertIn("never re-ask recorded answers", p4["invariant"].lower())
        self.assertIn("reads/output <=100 lines", p4["invariant"].lower())
        # "bounded rolling ledger" was removed under PRINCIPLE-001 R2's deletion test (the tool
        # bounds the ledger; no agent action follows). The capsule now names the mechanisms:
        self.assertIn("phase 2 `--desc`", p4["invariant"].lower())
        self.assertIn("`--resume`", p4["invariant"])
        self.assertIn("adr before commit", p4["invariant"].lower())
        self.assertIn("<=100 lines", p4["invariant"])

    def test_principle_005_cold_start_capsule(self):
        # Enforces PRINCIPLE-005: the capsule names what README holds and which command checks it
        principles = parse_principles(SSOT_MD)
        p5 = next((p for p in principles if p["id"] == "PRINCIPLE-005"), None)
        self.assertIsNotNone(p5)
        # Mechanisms, not labels (ADR-063): the size limit, the checked items, the trigger, the gate.
        for mechanism in ("readme <=22.5k chars", "prerequisites, test command, tree",
                          "user-visible changes update it same commit",
                          "`update_knowledge_base.py --check` gates it"):
            with self.subTest(mechanism=mechanism):
                self.assertIn(mechanism, p5["invariant"].lower())

    def test_principle_006_disruption_capsule(self):
        # Enforces PRINCIPLE-006: the capsule states when to commit and how a task ends
        principles = parse_principles(SSOT_MD)
        p6 = next((p for p in principles if p["id"] == "PRINCIPLE-006"), None)
        self.assertIsNotNone(p6)
        # Mechanisms, not labels (ADR-078).
        for mechanism in ("commit `[milestone n/m]` once phase 4 passes under principle-018 r1",
                          "failing work uncommitted via `--checkpoint`",
                          "`--complete`/`--reset` before switching tasks", "`--clean` stale `.tmp_*`",
                          # ADR-209: every host learns to name itself and not to take another's task.
                          "ledger writes name `--agent`; another agent's task needs `--take-over`"):
            with self.subTest(mechanism=mechanism):
                self.assertIn(mechanism, p6["invariant"].lower())

    def test_principle_014_regression_shield_capsule(self):
        # Enforces PRINCIPLE-014: the capsule states when a test is required and when it may change
        principles = parse_principles(SSOT_MD)
        p14 = next((p for p in principles if p["id"] == "PRINCIPLE-014"), None)
        self.assertIsNotNone(p14)
        # Mechanisms, not labels (ADR-087; the label pins were replaced under PRINCIPLE-014 R2's
        # exception: the user approved rewriting the principle text, and ADR-087 names this test).
        for mechanism in ("100% test pass gate", "behaviour change = failing-first test",
                          "weakening a test needs user approval + adr naming it",
                          "unit <=10ms/test, no spawns/sleeps", "integ <=350ms/test",
                          "tempdir + addcleanup", "scripts/check_reachability.py"):
            with self.subTest(mechanism=mechanism):
                self.assertIn(mechanism, p14["invariant"].lower())

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
        self.assertIn("conventional commits", p18["invariant"].lower())
        self.assertIn("only if authorized (r1)", p18["invariant"].lower())
        self.assertIn("adaptive push", p18["invariant"].lower())
        self.assertIn("explicit staging", p18["invariant"].lower())
        self.assertIn("no `git add .`", p18["invariant"].lower())
        self.assertIn("pre-commit triad", p18["invariant"].lower())
        self.assertIn("non-destructive recoil", p18["invariant"].lower())

    def test_principle_000_meta_principle_capsule(self):
        # Enforces PRINCIPLE-000: the capsule states the five meta-rules as mechanisms
        principles = parse_principles(SSOT_MD)
        p0 = next((p for p in principles if p["id"] == "PRINCIPLE-000"), None)
        self.assertIsNotNone(p0)
        # Mechanisms, not labels (ADR-070).
        for mechanism in ("every rule binds", "conflicts follow r6 order",
                          "rule edits re-check every citing principle",
                          "gaming a gate is a violation", "quality doubts go to the user"):
            with self.subTest(mechanism=mechanism):
                self.assertIn(mechanism, p0["invariant"].lower())

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
        # Anchor on the checklist HEADINGS: rule text (P001 R8) also mentions these names.
        pre_start = re.search(r"^###[^\n]*Pre-Flight Checklist", text, re.M).start()
        post_start = re.search(r"^###[^\n]*Post-Flight Checklist", text, re.M).start()
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
            bad_doc.write_text("### PRINCIPLE-099: Broken Schema\n- **Problem**: P\n- **Invariant**: Test\n- **Rules**:\n  1. Do something.\n", encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                parse_principles(bad_doc, strict=True)
            self.assertIn("[PRINCIPLE-017 SCHEMA VIOLATION]", str(ctx.exception))

            # Missing invariant
            bad_doc = temp_dir / "bad2.md"
            bad_doc.write_text("### PRINCIPLE-099: Broken Schema\n- **Problem**: P\n- **Concept**: Test\n- **Rules**:\n  1. Do something.\n", encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                parse_principles(bad_doc, strict=True)
            self.assertIn("[PRINCIPLE-017 SCHEMA VIOLATION]", str(ctx.exception))

            # Missing rules
            bad_doc = temp_dir / "bad3.md"
            bad_doc.write_text("### PRINCIPLE-099: Broken Schema\n- **Problem**: P\n- **Concept**: Test\n- **Invariant**: Test\n", encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                parse_principles(bad_doc, strict=True)
            self.assertIn("[PRINCIPLE-017 SCHEMA VIOLATION]", str(ctx.exception))

            # Duplicate principle ID
            bad_doc = temp_dir / "bad4.md"
            bad_doc.write_text(
                "### PRINCIPLE-001: First\n- **Problem**: P\n- **Concept**: A\n- **Invariant**: B\n- **Rules**:\n  1. R1\n\n"
                "### PRINCIPLE-001: Duplicate\n- **Problem**: P\n- **Concept**: C\n- **Invariant**: D\n- **Rules**:\n  1. R2\n",
                encoding="utf-8"
            )
            with self.assertRaises(ValueError) as ctx:
                parse_principles(bad_doc, strict=True)
            self.assertIn("[PRINCIPLE-017 SCHEMA VIOLATION] Duplicate principle ID detected: PRINCIPLE-001", str(ctx.exception))
            # Missing problem (ADR-090): every principle states why it exists
            bad_doc = temp_dir / "bad5.md"
            bad_doc.write_text("### PRINCIPLE-099: Broken Schema\n- **Concept**: C\n- **Invariant**: I\n- **Rules**:\n  1. R.\n", encoding="utf-8")
            with self.assertRaises(ValueError) as ctx:
                parse_principles(bad_doc, strict=True)
            self.assertIn("missing required '- **Problem**:' section", str(ctx.exception))
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def test_only_level_two_headings_set_the_phase(self):
        # Red-green pin (ADR-118): the phase pattern also matched the `##` inside a `###` heading,
        # so a sub-heading mentioning "Phase 5" silently re-assigned the next principle's phase.
        doc = Path(tempfile.mkdtemp(prefix="test_phase_")) / "ssot.md"
        self.addCleanup(shutil.rmtree, doc.parent, ignore_errors=True)
        body = "- **Problem**: P\n- **Concept**: C\n- **Invariant**: I\n- **Rules**:\n  1. **R** *[Agent]*: r.\n\n"
        doc.write_text("## Phase 1: Start\n### PRINCIPLE-001: A\n" + body
                       + "### Notes on Phase 5 work\n\n### PRINCIPLE-002: B\n" + body, encoding="utf-8")
        phases = {p["id"]: p["phase_num"] for p in parse_principles(doc, strict=False)}
        self.assertEqual(phases, {"PRINCIPLE-001": 1, "PRINCIPLE-002": 1})

    def test_last_principle_block_stops_at_next_section(self):
        # Red-green pin: the final principle's block used to run to end-of-file, so a field in a
        # trailing appendix could satisfy that principle's schema. Here the last principle lacks an
        # Invariant and only the appendix has one; strict parsing must reject it.
        doc = Path(tempfile.mkdtemp(prefix="test_bounds_")) / "ssot.md"
        self.addCleanup(shutil.rmtree, doc.parent, ignore_errors=True)
        doc.write_text(
            "## Phase 5: Delivery\n"
            "### PRINCIPLE-001: Complete\n- **Problem**: P\n- **Concept**: A\n- **Invariant**: B\n- **Rules**:\n  1. R\n\n"
            "### PRINCIPLE-002: Missing Invariant\n- **Problem**: P\n- **Concept**: C\n- **Rules**:\n  1. R\n\n"
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
        # cold-start token ceiling (<22,500 chars), and valid paths for every file listed in the directory tree.
        readme_path = ROOT_DIR / "README.md"
        self.assertTrue(readme_path.exists(), "README.md missing from repository root")
        readme_content = readme_path.read_text(encoding="utf-8")
        
        # 1. Cold-Start Token Ceiling (<22,500 characters)
        MAX_README_CHARS = 22500
        self.assertLessEqual(
            len(readme_content),
            MAX_README_CHARS,
            f"README.md exceeds 22,500 char cold-start budget: {len(readme_content)} chars"
        )

        # 2. Orientation block & prerequisites
        self.assertIn("30-Second Cold-Start Quick Reference", readme_content, "Missing 30s quick reference in README.md")
        self.assertIn("Python 3.10+", readme_content, "Missing Python runtime prerequisite in README.md")
        self.assertIn("python -m unittest discover tests", readme_content, "Missing canonical test command in README.md")
        
        # 3. Whole-Tree Drift Shield and command parity, by the same check the gate runs. This
        # replaced a fixed list of 25 AIKit paths that never saw a new file missing from the tree
        # (it missed `.gitignore`). Completeness against git is the integration tier's job.
        def script_source(rel):
            path = ROOT_DIR / rel
            return path.read_text(encoding="utf-8") if path.is_file() else None
        self.assertEqual(audit_readme(readme_content, None, lambda rel: (ROOT_DIR / rel).exists(),
                                      script_source), [])
        self.assertIn(".gitignore", parse_readme_tree(readme_content))


class TestPrinciple005ReadmeGate(unittest.TestCase):
    """PRINCIPLE-005: every README rule a program can decide is decided by `audit_readme`."""

    TREE = (
        "## ⚡ 30-Second Cold-Start Quick Reference\n- **Runtime Prerequisites**: Python 3.10+\n"
        "- **Canonical Regression Shield Gate**:\n  ```bash\n  make test\n  ```\n"
        "## 📦 What's Inside\n```text\nrepo/\n"
        "├── README.md\n├── scripts/\n│   └── tool.py      <- a tool\n└── docs/\n```\n"
    )
    SOURCES = {"scripts/tool.py": 'FLAGS = {"--check"}'}
    TRACKED = ["README.md", "scripts/tool.py", "docs/a.md", "docs/deep/b.md"]

    def audit(self, readme, tracked=TRACKED, exists=None):
        on_disk = set(self.TRACKED) | {"scripts", "docs", "docs/deep"}
        return audit_readme(readme, tracked, exists or (lambda rel: rel in on_disk), self.SOURCES.get)

    def test_a_correct_readme_passes(self):
        self.assertEqual(self.audit(self.TREE), [])

    def test_aikit_commands_without_their_grammar_file_fail_loudly(self):
        # A rename of the grammar file used to switch the command check off without a word.
        readme = self.TREE + "\nRun `python aikit.py list`.\n"
        on_disk = set(self.TRACKED) | {"scripts", "docs", "docs/deep", "aikit.py"}
        errors = self.audit(readme, exists=on_disk.__contains__)
        self.assertTrue(any("scripts/aikit_parser.py" in error for error in errors), errors)

    def test_a_project_without_aikit_py_still_skips_the_command_check(self):
        # An adopter project documents `aikit.py` commands but runs them from the AIKit folder.
        self.assertEqual(self.audit(self.TREE + "\nRun `python aikit.py list`.\n"), [])

    def test_check_readme_uses_utf8_with_replace_on_git_listing(self):
        folder = Path(tempfile.mkdtemp(prefix="test_check_readme_"))
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        (folder / "README.md").write_text("# title\n", encoding="utf-8")
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(["git", "ls-files", "-z"], 0, "README.md\0", "")
            check_readme(folder)
            mock_run.assert_called_once_with(
                ["git", "ls-files", "-z"],
                cwd=folder,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=10,
            )

    def test_tree_paths_and_directories(self):
        self.assertEqual(parse_readme_tree(self.TREE), ["README.md", "scripts/", "scripts/tool.py", "docs/"])

    def test_a_dead_tree_path_fails(self):
        errors = self.audit(self.TREE.replace("tool.py", "gone.py"))
        self.assertIn("README.md tree lists 'scripts/gone.py', which does not exist (R5)", errors)

    def test_a_missing_top_level_entry_fails(self):
        on_disk = set(self.TRACKED) | {"scripts", "docs", "docs/deep", ".gitignore"}
        errors = self.audit(self.TREE, tracked=self.TRACKED + [".gitignore"], exists=on_disk.__contains__)
        self.assertEqual(errors, ["README.md tree omits tracked '.gitignore' (R5)"])

    def test_a_tracked_file_deleted_in_the_working_copy_need_not_be_listed(self):
        # ADR-214: `license --restrict` deletes COMMERCIAL.md; until that deletion is committed
        # it is still tracked, and requiring it in the tree blocked the check that must pass first.
        self.assertEqual(self.audit(self.TREE, tracked=self.TRACKED + ["COMMERCIAL.md"]), [])

    def test_an_expanded_directory_must_be_complete_and_a_collapsed_one_need_not(self):
        # scripts/ shows children, so every tracked child must be listed; docs/ shows none.
        on_disk = set(self.TRACKED) | {"scripts", "docs", "docs/deep", "scripts/new.py"}
        errors = self.audit(self.TREE, tracked=self.TRACKED + ["scripts/new.py"], exists=on_disk.__contains__)
        self.assertEqual(errors, ["README.md tree omits tracked 'scripts/new.py' (R5)"])

    def test_documented_commands_must_exist(self):
        readme = self.TREE + "`python scripts/tool.py --check --nope` `python scripts/x.py` `python -m unittest tests.test_none`"
        self.assertEqual(self.audit(readme), [
            "README.md passes --nope to scripts/tool.py, which does not declare it (R3)",
            "README.md runs 'scripts/x.py', which does not exist (R3)",
            "README.md runs test module 'tests.test_none', which does not exist (R3)",
        ])

    def test_size_labels_and_tree_are_required(self):
        errors = self.audit("# x\n" + "y" * 22_501)
        self.assertIn("README.md has 22,505 chars; the limit is 22,500 (R1)", errors)
        self.assertIn("README.md has no heading containing 'Cold-Start Quick Reference' (R1)", errors)
        self.assertIn("README.md has no ```text directory tree after \"What's Inside\" (R5)", errors)

    def test_a_prose_mention_is_not_the_tree_heading(self):
        prose = "See What's Inside below.\n```text\nrepo/\n├── fake.md\n```\n"
        self.assertEqual(parse_readme_tree(prose + self.TREE)[0], "README.md")

    def test_quick_reference_is_checked_by_structure_not_words(self):
        # Red-green pin (second pass): labels anywhere in prose passed; R1 states a heading, a
        # prerequisites line naming a version and a fenced command after the test-gate label.
        prose = ("We follow the Cold-Start Quick Reference idea. **Runtime Prerequisites**: Python. "
                 "**Canonical Regression Shield Gate**: run the tests.\n")
        self.assertIn("README.md has no heading containing 'Cold-Start Quick Reference' (R1)",
                      self.audit(prose + self.TREE.split("## 📦")[1].join(["## 📦", ""])))
        no_version = self.TREE.replace("Python 3.10+", "Python")
        self.assertIn("'- **Runtime Prerequisites**:' names no minimum version (R1)", self.audit(no_version))
        no_command = self.TREE.replace("  ```bash\n  make test\n  ```\n", "")
        self.assertIn("the Quick Reference has no fenced command right after "
                      "'**Canonical Regression Shield Gate**:' (R1)", self.audit(no_command))

    def test_the_adopter_template_fails_unfilled_and_passes_filled(self):
        # Red-green pin: "paste the Quick Reference section" carried AIKit's own test modules into
        # adopter READMEs, and an unfilled placeholder satisfied the label check.
        template = (ROOT_DIR / README_TEMPLATE).read_text(encoding="utf-8")
        tracked = ["README.md", "pyproject.toml", ".gitignore", ".aikit/project.json",
                   ".aikit/guidelines.md", ".aikit/decisions.md", ".aikit/task_ledger.json",
                   "src/app.py", "tests/test_app.py", "docs/usage.md"]
        on_disk = set(tracked) | {".aikit", "src", "tests", "docs"}

        def script_source(rel):
            path = ROOT_DIR / rel
            return path.read_text(encoding="utf-8") if path.is_file() else None

        def audit(readme):
            return audit_readme(readme, tracked, on_disk.__contains__, script_source)

        unfilled = audit(template)
        self.assertIn("README.md still holds an unfilled '<FILL:' placeholder (R1); "
                      "only the project's own facts can replace it", unfilled)
        filled = re.sub(r"<FILL: every runtime[^>]*>", "Python 3.11+ and `git`", template)
        filled = re.sub(r"<FILL: the one command[^>]*>", "python -m unittest discover tests", filled)
        filled = filled.replace("<FILL: repository name>/", "app/")
        filled = filled.replace("<package>/", "src/")
        filled = re.sub(r"└── <FILL:[^>]*>", "└── docs/", filled)
        self.assertEqual(audit(filled), [])


class TestGeneratedReadmeTable(unittest.TestCase):
    """PRINCIPLE-005 R4 / PRINCIPLE-017 R4: README's principle table is generated (ADR-076)."""

    PRINCIPLES = [
        {"id": "PRINCIPLE-000", "title": "Meta (Sub)", "invariant": "a | b", "phase_name": "Phase 1: X"},
        {"id": "PRINCIPLE-001", "title": "One", "invariant": "c", "phase_name": "Phase 1: X"},
        {"id": "PRINCIPLE-002", "title": "Two", "invariant": "d", "phase_name": "Phase 2: Y"},
    ]

    def test_table_groups_by_phase_and_escapes_cells(self):
        self.assertEqual(render_readme_table(self.PRINCIPLES), "\n".join([
            "### Phase 1: X", "| Principle | Title | Capsule |", "|---|---|---|",
            "| **PRINCIPLE-000** | Meta | a \\| b |", "| **PRINCIPLE-001** | One | c |", "",
            "### Phase 2: Y", "| Principle | Title | Capsule |", "|---|---|---|",
            "| **PRINCIPLE-002** | Two | d |"]))

    def test_only_the_block_between_markers_is_rewritten(self):
        readme = f"intro\n{README_TABLE_BEGIN}\nstale row\n{README_TABLE_END}\noutro\n"
        refreshed = sync_readme_table(readme, self.PRINCIPLES)
        self.assertTrue(refreshed.startswith("intro\n") and refreshed.endswith(f"{README_TABLE_END}\noutro\n"))
        self.assertNotIn("stale row", refreshed)
        self.assertIsNone(sync_readme_table("an adopter README\n", self.PRINCIPLES))

    def test_this_readme_table_is_generated_and_fresh(self):
        # Red-green pin: the hand-written rows differed from 19 of 20 capsules.
        readme = README_MD.read_text(encoding="utf-8")
        self.assertEqual(sync_readme_table(readme, parse_principles(SSOT_MD)), readme)


class TestPrinciple007Tooling(unittest.TestCase):
    """PRINCIPLE-007 R3 and R6 as checks every model meets the same way (ADR-079)."""

    FULL = {"why": "w", "benefits": "b", "mitigation": "m",
            "risks": "contract: none; dependency: none; concurrency: none; state: none"}

    def test_first_plan_needs_the_whole_assessment(self):
        # Red-green pin: plans were recorded with --why alone and nothing noticed.
        self.assertEqual(impact_errors("[1/2] a; [2/2] b", 2, self.FULL, False), [])
        partial = dict(self.FULL, benefits=None, risks="contract: none")
        self.assertEqual(impact_errors("[1/2] a", 2, partial, False), [
            "--benefits is required on the first plan checkpoint",
            "--risks must give a verdict for 'dependency:' (write 'none' when there is no risk)",
            "--risks must give a verdict for 'concurrency:' (write 'none' when there is no risk)",
            "--risks must give a verdict for 'state:' (write 'none' when there is no risk)",
        ])

    def test_reaching_phase_3_without_an_assessment_warns(self):
        # Red-green pin (ADR-112): a Track C task that never recorded a plan bypassed R6 silently.
        self.assertIn("entered Phase 3 with no impact assessment", missing_impact_warning("t", 3, False, False))
        self.assertIsNone(missing_impact_warning("t", 2, False, False))   # planning itself
        self.assertIsNone(missing_impact_warning("t", 4, True, False))    # assessment on record
        self.assertIsNone(missing_impact_warning("t", 3, False, True))    # recorded now

    def test_only_the_first_plan_checkpoint_is_checked(self):
        empty = {"why": None, "benefits": None, "risks": None, "mitigation": None}
        self.assertEqual(impact_errors("[1/3] revised", 2, empty, True), [])   # revision
        self.assertEqual(impact_errors("User chose JSON", 2, empty, False), [])  # a note, not a plan
        self.assertEqual(impact_errors("[1/2] a", 3, empty, False), [])      # not Phase 2

    def test_lazy_code_markers_stubs_and_unnamed_suppressions_fail(self):
        source = (
            "import typing\n"
            "# TODO: finish\n"
            "x = 1  # type: ignore\n"
            "y = 2  # noqa\n"
            "def stub():\n    pass\n"
            "def later():\n    raise NotImplementedError\n"
            "def dots():\n    '''Doc.'''\n    ...\n"
        )
        self.assertEqual(audit_lazy_code(source, "m.py"), [
            "m.py:2: '# TODO: finish' marks unfinished code",
            "m.py:3: suppression names no error code",
            "m.py:4: suppression names no error code",
            "m.py:5: function 'stub' is a stub",
            "m.py:7: function 'later' is a stub",
            "m.py:9: function 'dots' is a stub",
        ])
        source_inline = (
            "# Note: TODO: fix inline\n"
            "# Urgent: FIXME(alice): check this\n"
        )
        self.assertEqual(audit_lazy_code(source_inline, "inline.py"), [
            "inline.py:1: '# Note: TODO: fix inline' marks unfinished code",
            "inline.py:2: '# Urgent: FIXME(alice): check this' marks unfinished code",
        ])

    def test_protocols_abstract_methods_and_named_suppressions_pass(self):
        source = (
            "from abc import ABC, abstractmethod\n"
            "from typing import Protocol, overload\n"
            "class Port(Protocol):\n    def read(self) -> str: ...\n"
            "class Base(ABC):\n    def run(self):\n        raise NotImplementedError\n"
            "class Other:\n    @abstractmethod\n    def go(self): ...\n"
            "@overload\ndef f(x: int) -> int: ...\n"
            "import os  # noqa: E402\n"
            "z = 3  # type: ignore[assignment]\n"
            "# Two placeholders (\"XXX\" in prose) are not a marker.\n"
            "def real():\n    try:\n        return 1\n    except OSError:\n        pass\n"
        )
        self.assertEqual(audit_lazy_code(source, "ok.py"), [])


class TestArchitectureGate(unittest.TestCase):
    """PRINCIPLE-009's checkable parts (ADR-082)."""

    def test_junk_drawers_fat_roles_and_cycles_fail(self):
        modules = {"pkg.a": "import pkg.b", "pkg.b": "from pkg.a import x", "pkg.utils": "",
                   "m": "from typing import Protocol\nclass R(Protocol):\n    pass\n",
                   "n": "import abc\nclass Big(abc.ABC):\n" + "".join(f"    def f{i}(self): ...\n" for i in range(6))}
        self.assertEqual(sorted(audit_architecture(modules)), sorted([
            "pkg.utils: 'utils' is a junk-drawer module name; name it after what it holds",
            "m: role 'R' declares 0 methods; a role declares 1 to 5",
            "n: role 'Big' declares 6 methods; a role declares 1 to 5",
            "import cycle: pkg.a -> pkg.b -> pkg.a",
        ]))

    def test_untimed_subprocess_and_unmanaged_open_fail(self):
        # PRINCIPLE-010 R3/R4 (ADR-083): both rules existed with nothing checking them.
        source = ("import subprocess\nsubprocess.run(['x'])\nf = open('a')\n"
                  "with open('b') as g:\n    pass\nsubprocess.check_output(['y'], timeout=5)\n")
        self.assertEqual(audit_architecture({"m": source}), [
            "m:2: subprocess.run without timeout= (PRINCIPLE-010 R3)",
            "m:3: open() outside a with statement (PRINCIPLE-010 R4)",
        ])

    def test_method_style_open_outside_with_fails_and_os_open_passes(self):
        # PRINCIPLE-010 R4 second pass (ADR-095): Path.open() escaped the builtin-only check.
        source = ("import os\nfrom pathlib import Path\nf = Path('a').open('w')\n"
                  "with Path('b').open() as g:\n    pass\nfd = os.open('c', os.O_RDONLY)\n")
        self.assertEqual(audit_architecture({"m": source}),
                         ["m:3: open() outside a with statement (PRINCIPLE-010 R4)"])

    def test_raw_environ_reads_fail_and_writes_and_getenv_pass(self):
        # PRINCIPLE-011 R3 (ADR-084).
        source = "import os\nx = os.environ['K']\nos.environ['K'] = 'v'\ny = os.getenv('K', 'd')\n"
        self.assertEqual(audit_architecture({"m": source}),
                         ["m:2: os.environ[...] read; use os.getenv() with a default (PRINCIPLE-011 R3)"])

    def test_focused_names_narrow_roles_and_one_way_imports_pass(self):
        modules = {"app.date_parsing": "", "app.service": "import app.domain",
                   "app.domain": "from typing import Protocol\nclass Store(Protocol):\n    def get(self) -> str: ...\n"}
        self.assertEqual(audit_architecture(modules), [])


class TestKnowledgeBaseWorkspaceAudits(unittest.TestCase):
    """PRINCIPLE-016 and PRINCIPLE-011 R8: update_knowledge_base audits external project workspaces."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="test_kb_ws_"))
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_workspace_audits_lazy_code_architecture_and_adr_register(self):
        # A project with a stub, a junk-drawer module and broken ADRs
        (self.tmp / "app.py").write_text("def todo(): pass\n", encoding="utf-8")
        (self.tmp / "utils.py").write_text("x = 1\n", encoding="utf-8")
        (self.tmp / ".aikit").mkdir(parents=True)
        (self.tmp / ".aikit" / "decisions.md").write_text(
            "# Decisions\n\n### ADR-001: First\n\n### ADR-003: Third (skips 2)\n", encoding="utf-8"
        )
        lazy = check_lazy_code(self.tmp)
        self.assertEqual(len(lazy), 1)
        self.assertIn("function 'todo' is a stub", lazy[0])

        arch = check_architecture(self.tmp)
        self.assertEqual(len(arch), 1)
        self.assertIn("'utils' is a junk-drawer module name", arch[0])

        adr_errors = audit_adr_register((self.tmp / ".aikit" / "decisions.md").read_text(encoding="utf-8"))
        self.assertEqual(len(adr_errors), 1)
        self.assertIn("ADR-003 skips after ADR-001", adr_errors[0])

    def test_clean_workspace_passes_lazy_and_architecture(self):
        (self.tmp / "domain.py").write_text("def solve() -> int:\n    return 42\n", encoding="utf-8")
        (self.tmp / ".aikit").mkdir(parents=True)
        (self.tmp / ".aikit" / "decisions.md").write_text(
            "# Decisions\n\n### ADR-001: First\n\n### ADR-002: Second\n", encoding="utf-8"
        )
        self.assertEqual(check_lazy_code(self.tmp), [])
        self.assertEqual(check_architecture(self.tmp), [])
        self.assertEqual(audit_adr_register((self.tmp / ".aikit" / "decisions.md").read_text(encoding="utf-8")), [])

    def test_aikit_dir_is_ignored_by_python_file_discovery(self):
        (self.tmp / ".aikit").mkdir(parents=True)
        (self.tmp / ".aikit" / "helper.py").write_text("def stub(): pass\n", encoding="utf-8")
        (self.tmp / "main.py").write_text("def ok() -> None:\n    return None\n", encoding="utf-8")
        py_files = find_python_files(self.tmp)
        self.assertEqual([p.name for p in py_files], ["main.py"])

    def test_write_generated_file_persists_atomically(self):
        dest = self.tmp / "sub" / "output.txt"
        write_generated_file(dest, "atomic-content")
        self.assertTrue(dest.is_file())
        self.assertEqual(dest.read_text(encoding="utf-8"), "atomic-content")

    def test_workspace_codebase_map_freshness(self):
        (self.tmp / "service.py").write_text("class Worker:\n    def run(self): pass\n", encoding="utf-8")
        map_content = generate_codebase_map(root=self.tmp, strict=False)
        (self.tmp / ".aikit").mkdir(parents=True)
        write_generated_file(self.tmp / ".aikit" / "codebase_map.md", map_content)
        self.assertTrue(check_codebase_map_freshness(self.tmp / ".aikit", root=self.tmp, strict=False))
        # Modify service.py to make it stale
        (self.tmp / "service.py").write_text("class Worker:\n    def run(self): pass\n    def stop(self): pass\n", encoding="utf-8")
        self.assertFalse(check_codebase_map_freshness(self.tmp / ".aikit", root=self.tmp, strict=False))


class TestSecretBaselineAndRuleSchema(unittest.TestCase):
    """PRINCIPLE-019 R2 and PRINCIPLE-017 R1 (ADR-092)."""

    def test_gitignore_holds_every_baseline_pattern_the_rule_lists(self):
        # Red-green pin: R2 listed `credentials*`/`secrets*` while .gitignore shipped other patterns.
        section = principle_sections(SSOT_MD.read_text(encoding="utf-8"))["PRINCIPLE-019"]
        rule = next(line for line in section.splitlines() if "**Ignore-List Baseline" in line)
        listed = rule.split("before any such file exists:")[1].split("A unit test")[0]
        patterns = re.findall(r"`([^`]+)`", listed)
        ignored = set((ROOT_DIR / ".gitignore").read_text(encoding="utf-8").split())
        self.assertGreater(len(patterns), 10)
        self.assertEqual([p for p in patterns if p not in ignored], [])

    def test_a_rule_without_audience_is_rejected(self):
        doc = Path(tempfile.mkdtemp(prefix="test_tags_")) / "ssot.md"
        self.addCleanup(shutil.rmtree, doc.parent, ignore_errors=True)
        doc.write_text("## Phase 5: X\n### PRINCIPLE-001: T\n- **Problem**: P\n- **Concept**: C\n- **Invariant**: I\n"
                       "- **Rules**:\n  1. **Tagged** *[Agent]*: a.\n  2. **Untagged**: b.\n", encoding="utf-8")
        with self.assertRaises(ValueError) as ctx:
            parse_principles(doc, strict=True)
        self.assertIn("PRINCIPLE-001 rule(s) R2 name no audience", str(ctx.exception))


class TestRuleNumberParity(unittest.TestCase):
    """
    Every number a rule states equals the constant the code enforces (ADR-113). The budget moved
    from 1,500 to 1,600 in code while documents kept the old number; this fails on the next drift
    in either direction.
    """

    def test_rule_numbers_match_code_constants(self):
        import scripts.disruption_recovery as ledger
        import scripts.sync_principles as sync
        import scripts.update_knowledge_base as kb
        dogfood_budget = int(re.search(r"budget_ms = (\d+)", (ROOT_DIR / "scripts" / "dogfood.py")
                                       .read_text(encoding="utf-8")).group(1))
        sections = principle_sections(SSOT_MD.read_text(encoding="utf-8"))
        cases = [
            ("PRINCIPLE-001", f"{sync.TARGET_TOKEN_BUDGET:,} estimated tokens"),
            ("PRINCIPLE-001",
             f"{int(sync.TARGET_TOKEN_BUDGET * sync.WARN_TOKEN_RATIO):,} estimated tokens (90%)"),
            ("PRINCIPLE-001", f"{sync.MAX_DOMAIN_CHARS:,}-character"),
            ("PRINCIPLE-017", f"at most {sync.MAX_DOMAIN_CHARS:,} characters"),
            ("PRINCIPLE-004", f"at most {ledger.DEFAULT_MAX_CHECKPOINTS} checkpoints"),
            ("PRINCIPLE-005", f"MUST NOT exceed {kb.README_MAX_CHARS:,} characters"),
            ("PRINCIPLE-006", f"older than {ledger.TEMP_STALE_SECONDS} seconds"),
            ("PRINCIPLE-009", f"1 to {kb.ROLE_METHOD_LIMIT} methods"),
            ("PRINCIPLE-010", f"under {dogfood_budget}ms as a fresh process"),
        ]
        for pid, phrase in cases:
            with self.subTest(pid=pid, phrase=phrase):
                self.assertIn(phrase, sections[pid])


class TestAgentOwnership(unittest.TestCase):
    """
    Every ledger write names its agent, and an agent cannot write another agent's task without an
    explicit take-over (ADR-209). Another agent once finished an active task, committed its
    half-done work under its own messages and pushed it, and the ledger did not notice.
    """

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix="test_ownership_"))
        self.addCleanup(shutil.rmtree, self.dir, ignore_errors=True)
        self.ledger = self.dir / ".agents" / "task_ledger.json"
        record_checkpoint("t", "planning", "[1/1] plan", ledger_file=self.ledger, phase_num=2, agent="a")

    def test_every_write_names_its_agent(self):
        record_checkpoint("t", "implementation", "work", ledger_file=self.ledger, phase_num=3, agent="a")
        self.assertTrue(mark_task_completed("t", ledger_file=self.ledger, agent="a"))
        ledger = load_ledger(self.ledger)
        self.assertEqual([c["agent"] for c in ledger["checkpoints"]], ["a", "a", "a"])
        self.assertEqual(ledger["active_task"]["owner"], "a")

    def test_another_agent_cannot_write_an_owned_task(self):
        before = self.ledger.read_bytes()
        for attempt in (lambda: record_checkpoint("t", "implementation", "x", ledger_file=self.ledger,
                                                  phase_num=3, agent="b"),
                        lambda: record_checkpoint("u", "planning", "x", ledger_file=self.ledger,
                                                  phase_num=2, agent="b"),
                        lambda: mark_task_completed("t", ledger_file=self.ledger, agent="b"),
                        lambda: reset_active_task("x", ledger_file=self.ledger, agent="b"),
                        lambda: record_checkpoint("t", "implementation", "x", ledger_file=self.ledger,
                                                  phase_num=3, agent=UNIDENTIFIED_AGENT)):
            with self.subTest(attempt=attempt), self.assertRaises(LedgerOwnershipError) as caught:
                attempt()
            self.assertEqual(caught.exception.owner, "a")
            self.assertEqual(self.ledger.read_bytes(), before, "nothing was written")

    def test_a_take_over_records_who_continued(self):
        record_checkpoint("t", "implementation", "x", ledger_file=self.ledger, phase_num=3, agent="b",
                          take_over=True)
        ledger = load_ledger(self.ledger)
        self.assertEqual(ledger["checkpoints"][-1]["continued_from"], "a")
        self.assertEqual(ledger["active_task"]["owner"], "b")
        with self.assertRaises(LedgerOwnershipError):
            mark_task_completed("t", ledger_file=self.ledger, agent="a")
        report = format_resume_report(run_disruption_audit(workspace_dir=self.dir))
        self.assertIn("Owner: b", report)
        self.assertIn("started by a; continued by b", report)

    def test_an_unidentified_owner_is_claimed_with_a_record(self):
        record_checkpoint("v", "planning", "[1/1] plan", ledger_file=self.ledger, phase_num=2,
                          agent="a", take_over=True)
        record_checkpoint("v", "implementation", "x", ledger_file=self.ledger, phase_num=3,
                          agent=UNIDENTIFIED_AGENT, take_over=True)
        record_checkpoint("v", "implementation", "y", ledger_file=self.ledger, phase_num=3, agent="c")
        ledger = load_ledger(self.ledger)
        self.assertEqual(ledger["active_task"]["owner"], "c")
        self.assertEqual(ledger["checkpoints"][-1]["continued_from"], UNIDENTIFIED_AGENT)

    def test_the_agent_is_named_explicitly_or_by_its_host(self):
        self.assertEqual(resolve_agent("me", {"AIKIT_AGENT": "env", "AI_AGENT": "claude-code_2_agent"}), "me")
        self.assertEqual(resolve_agent(None, {"AIKIT_AGENT": "env", "AI_AGENT": "x_1"}), "env")
        self.assertEqual(resolve_agent(None, {"AI_AGENT": "claude-code_2-1-309_agent",
                                              "CLAUDE_CODE_SESSION_ID": "850bdc47-c6a3"}), "claude-code:850bdc47")
        self.assertEqual(resolve_agent(None, {"AI_AGENT": "claude-code_2_agent"}), "claude-code")
        self.assertEqual(resolve_agent(None, {}), UNIDENTIFIED_AGENT)
        for bad in ("two words", "x" * 65, "-lead", "semi;colon"):
            with self.subTest(name=bad), self.assertRaises(ValueError):
                resolve_agent(bad, {})

    def test_replacing_another_agents_task_records_whose_it_was(self):
        # ADR-210: the superseded entry named only the new agent, not the owner it replaced.
        record_checkpoint("u", "planning", "[1/1] plan", ledger_file=self.ledger, phase_num=2,
                          agent="b", take_over=True)
        superseded = [c for c in load_ledger(self.ledger)["checkpoints"] if c["status"] == "superseded"]
        self.assertEqual(superseded[-1]["agent"], "b")
        self.assertEqual(superseded[-1]["continued_from"], "a")

    def test_history_of_a_task_older_than_attribution(self):
        # ADR-210: a task begun before ADR-209 was said to be "started by" its first named writer.
        self.assertEqual(agent_history([{"task_id": "t"}, {"task_id": "t", "agent": "a"}]),
                         "started by an unrecorded agent")
        self.assertEqual(agent_history([{"agent": "a"}, {"agent": "b", "continued_from": "a"}]),
                         "started by a; continued by b")
        self.assertEqual(agent_history([]), "")

    def test_who_continued_survives_checkpoint_pruning(self):
        # ADR-211: the ledger keeps 20 checkpoints, so a long task's take-over entry was pruned and
        # --resume no longer said who continued; the active task now keeps the chain itself.
        record_checkpoint("t", "implementation", "x", ledger_file=self.ledger, phase_num=3, agent="b",
                          take_over=True)
        for n in range(30):
            record_checkpoint("t", "implementation", f"step {n}", ledger_file=self.ledger, phase_num=3, agent="b")
        ledger = load_ledger(self.ledger)
        self.assertFalse(any(c.get("continued_from") for c in ledger["checkpoints"]), "the entry was pruned")
        report = format_resume_report(run_disruption_audit(workspace_dir=self.dir))
        self.assertIn("Owner: b (started by a; continued by b)", report)

    def test_a_refused_write_prints_no_warning(self):
        # ADR-211: the impact warning was printed before the ownership refusal, for a write that
        # never happened.
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            self.assertEqual(checkpoint_command("t", "implementation", 3, "x", {}, self.ledger, agent="b"), 1)
        self.assertNotIn("[WARN]", err.getvalue())

    def test_only_a_bad_agent_name_is_reported_as_one(self):
        # ADR-210: the ValueError catch wrapped record_checkpoint, so any ValueError inside it
        # would have been reported as an invalid agent name.
        with mock.patch("scripts.disruption_recovery.record_checkpoint", side_effect=ValueError("disk says no")), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()), \
             self.assertRaisesRegex(ValueError, "disk says no"):
            checkpoint_command("t", "implementation", 3, "x", {}, self.ledger, agent="a")

    def test_checkpoint_command_reports_the_owner_and_the_take_over(self):
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            code = checkpoint_command("t", "implementation", 3, "x", {}, self.ledger, agent="b")
        self.assertEqual(code, 1)
        self.assertIn("belongs to agent 'a'", err.getvalue())
        self.assertIn("--take-over", err.getvalue())
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(checkpoint_command("t", "implementation", 3, "x", {}, self.ledger,
                                                agent="b", take_over=True), 0)


class TestPythonFileDiscovery(unittest.TestCase):
    """`find_python_files` prunes ignored directories relative to the root (ADR-115)."""

    def test_a_repository_under_an_ignored_name_is_still_scanned(self):
        # Red-green pin: ignored names were matched anywhere in the absolute path, so a clone
        # under a directory called `build` or `env` catalogued nothing.
        root = Path(tempfile.mkdtemp(prefix="test_discovery_")) / "build" / "repo"
        self.addCleanup(shutil.rmtree, root.parent.parent, ignore_errors=True)
        (root / "pkg").mkdir(parents=True)
        (root / "pkg" / "mod.py").write_text("x = 1\n", encoding="utf-8")
        (root / "venv").mkdir()
        (root / "venv" / "skip.py").write_text("x = 1\n", encoding="utf-8")
        self.assertEqual([p.relative_to(root).as_posix() for p in find_python_files(root)], ["pkg/mod.py"])

    def test_top_level_directories_the_root_gitignore_lists_are_skipped(self):
        # ADR-201: an untracked `references/` of another project's code entered AIKit's map and
        # failed its structure gate, though it is no part of the repository.
        root = Path(tempfile.mkdtemp(prefix="test_discovery_"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        for rel in ("pkg/mod.py", "references/other.py", "vendored/lib.py", "keep/references/x.py",
                    "notes/n.py"):
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text("x = 1\n", encoding="utf-8")
        (root / ".gitignore").write_text("# local material\nreferences/\n/vendored/\n*.log\nnotes\n",
                                         encoding="utf-8")
        found = [p.relative_to(root).as_posix() for p in find_python_files(root)]
        self.assertEqual(found, ["keep/references/x.py", "notes/n.py", "pkg/mod.py"],
                         "only `name/` or `/name/` entries prune, and only at the top level")

    def test_this_repository_ignores_references(self):
        self.assertIn("references/", (ROOT_DIR / ".gitignore").read_text(encoding="utf-8").splitlines())


class TestOpenCodePermissionBoundaries(unittest.TestCase):
    """
    PRINCIPLE-008 R6 / PRINCIPLE-009 R6 (ADR-116): replay OpenCode v2's documented evaluation
    (global rules, then agent rules; the last matching rule wins; `*` crosses `/`) over the shipped
    config. A later `edit *.md allow` had silently re-opened GUIDELINES.md to the worker, and no
    sub-agent was denied `git reset --hard`, `rm -rf` or `git add .`.
    """

    PROTECTED = ["GUIDELINES.md", ".agents/task_ledger.json", ".agents/rules/domain.md", "CLAUDE.md",
                 "AGENTS.md", "opencode.jsonc", "knowledge/decisions.md", ".windsurfrules", ".clinerules"]
    FORBIDDEN_SHELL = ["git add .", "git add -A", "git commit -m x", "git push", "git reset --hard",
                       "git clean -fdx", "git checkout -- x.py", "git stash drop", "rm -rf knowledge"]
    EDITS = {"architect": [], "explorer": [], "reviewer": ["knowledge/architecture.md", "README.md"],
             "coder": ["scripts/sync_principles.py", "tests/test_kit.py"], "tester": ["tests/test_kit.py"],
             "worker": ["knowledge/architecture.md", "README.md"]}
    READ_ONLY = ("architect", "explorer")

    @staticmethod
    def decide(rules, action, resource):
        def match(pattern, value):
            return re.fullmatch(re.escape(pattern).replace(r"\*", ".*").replace(r"\?", "."), value) is not None
        effect = "ask"
        for rule in rules:
            if match(rule["action"], action) and match(rule["resource"], resource):
                effect = rule["effect"]
        return effect

    @classmethod
    def setUpClass(cls):
        config = json.loads((ROOT_DIR / "opencode.jsonc").read_text(encoding="utf-8"))
        cls.global_rules = [{"action": "*", "resource": "*", "effect": "allow"}] + config["permissions"]
        cls.agents = {}
        for name in cls.EDITS:
            text = (ROOT_DIR / ".opencode" / "agents" / f"{name}.md").read_text(encoding="utf-8")
            front = text.split("---")[1]
            cls.agents[name] = [{"action": a, "resource": r, "effect": e} for a, r, e in re.findall(
                r'- action: (\S+)\s+resource: "([^"]+)"\s+effect: (\S+)', front)]

    def test_protected_files_and_destructive_commands_are_denied_to_every_subagent(self):
        for name, rules in self.agents.items():
            chain = self.global_rules + rules
            for path in self.PROTECTED:
                with self.subTest(agent=name, edit=path):
                    self.assertEqual(self.decide(chain, "edit", path), "deny")
            for command in self.FORBIDDEN_SHELL:
                with self.subTest(agent=name, shell=command):
                    self.assertEqual(self.decide(chain, "shell", command), "deny")

    def test_each_subagent_edits_only_its_own_area(self):
        probes = ["scripts/sync_principles.py", "tests/test_kit.py", "knowledge/architecture.md", "README.md"]
        for name, rules in self.agents.items():
            chain = self.global_rules + rules
            for path in probes:
                expected = "allow" if path in self.EDITS[name] else "deny"
                with self.subTest(agent=name, edit=path):
                    self.assertEqual(self.decide(chain, "edit", path), expected)
            # ADR-206: the read-only roles run no command, as on Claude Code; the others run tests.
            expected = "deny" if name in self.READ_ONLY else "allow"
            with self.subTest(agent=name, shell="tests"):
                self.assertEqual(self.decide(chain, "shell", "python -m unittest discover tests"), expected)

    def test_read_only_subagents_cannot_write_through_the_shell(self):
        # ADR-206: `edit` was denied, but `echo > f`, `python -c` or `Set-Content` wrote anyway.
        for name in self.READ_ONLY:
            chain = self.global_rules + self.agents[name]
            for command in ("echo x > notes.md", 'python -c "open(1)"', "Set-Content f x", "mv a b",
                            "git log", "git grep -w -e name"):
                with self.subTest(agent=name, shell=command):
                    self.assertEqual(self.decide(chain, "shell", command), "deny")


class TestKnowledgeCitations(unittest.TestCase):
    """PRINCIPLE-016 R2 drift made mechanical (ADR-101): citations in living documents resolve."""

    LIVING = ["GUIDELINES.md", "README.md"] + [f"knowledge/{n}" for n in
              ("INDEX.md", "architecture.md", "services.md", "data_models.md", "state_and_ui.md",
               "host_clients.md", "model_benchmarks.md")]
    # Rule citations only: these also name environment variables and abbreviations (ADR-117).
    CITATIONS_ONLY = [".agents/skills/aikit/SKILL.md", ".agents/agents/opencode_worker.md",
                      "knowledge/principles_audit_ledger.md"]

    def test_every_rule_citation_names_an_existing_rule(self):
        sections = principle_sections(SSOT_MD.read_text(encoding="utf-8"))
        counts = {pid: len(re.findall(r"^  \d+\. \*\*", s[s.index("- **Rules**:"):], re.M)) for pid, s in sections.items()}
        stale = []
        agents = [f".opencode/agents/{p.name}" for p in (ROOT_DIR / ".opencode" / "agents").glob("*.md")]
        for rel in (self.LIVING + self.CITATIONS_ONLY + agents
                    + [f"scripts/{p.name}" for p in (ROOT_DIR / "scripts").glob("*.py")]):
            text = (ROOT_DIR / rel).read_text(encoding="utf-8")
            for m in re.finditer(r"PRINCIPLE-(\d{3})(?:\*\*)?\s+(?:Rule\s+|R)(\d+)", text):
                pid, number = f"PRINCIPLE-{m.group(1)}", int(m.group(2))
                if number > counts.get(pid, 0):
                    stale.append(f"{rel}: {pid} R{number}")
        self.assertEqual(stale, [])

    def test_required_documents_equal_the_ones_principle_016_names(self):
        # Red-green pin (ADR-117): three AIKit-only documents were added to CORE_DOCS, failing every
        # adopter who replaced knowledge/ and contradicting PRINCIPLE-016 R1's list of seven.
        section = principle_sections(SSOT_MD.read_text(encoding="utf-8"))["PRINCIPLE-016"]
        rule = next(line for line in section.splitlines() if "**Canonical Structure" in line)
        listed = set(re.findall(r"`([A-Za-z_]+\.md)`", rule.split("python scripts/")[0]))
        self.assertEqual(listed, set(CORE_DOCS))

    def test_audit_ledger_labels_predictions_as_predictions(self):
        # Red-green pin (ADR-117): the ledger reported cross-model results no evaluation produced.
        text = (ROOT_DIR / "knowledge" / "principles_audit_ledger.md").read_text(encoding="utf-8")
        self.assertIn("**Status: snapshot, not an evaluation (ADR-117).**", text)
        self.assertNotIn("- **Cross-LLM Behavior**:", text)
        self.assertNotIn("### Cross-Model Interpretability Matrix", text)
        self.assertNotIn('hasattr(os, "O_DIRECTORY")', text)

    def test_every_benchmark_row_names_its_source_or_says_unverified(self):
        # PRINCIPLE-009 R6 (ADR-114): scores were presented as verified with no per-row source.
        text = (ROOT_DIR / "knowledge" / "model_benchmarks.md").read_text(encoding="utf-8")
        table = text[text.index("| Model Identifier |"):].split("\n\n")[0].splitlines()
        self.assertTrue(table[0].rstrip().endswith("Source |"))
        rows = [r for r in table[2:] if r.startswith("|")]
        self.assertGreater(len(rows), 0)
        for row in rows:
            with self.subTest(row=row[:40]):
                source = row.rstrip().rstrip("|").rsplit("|", 1)[1].strip()
                self.assertTrue(source == "`unverified`" or source.startswith(("http://", "https://")), source)

    def test_every_code_name_a_knowledge_document_cites_exists(self):
        # architecture.md had restated rules and cited numbers long after they changed.
        code = "".join((ROOT_DIR / "scripts" / p.name).read_text(encoding="utf-8")
                       for p in (ROOT_DIR / "scripts").glob("*.py"))
        code += (ROOT_DIR / "tests" / "test_kit.py").read_text(encoding="utf-8")
        code += (ROOT_DIR / "tests" / "test_integration.py").read_text(encoding="utf-8")
        missing = []
        for rel in self.LIVING[2:]:
            text = (ROOT_DIR / rel).read_text(encoding="utf-8")
            for name in set(re.findall(r"`([A-Za-z_][A-Za-z0-9_]*)\(\)`", text)) | set(
                    re.findall(r"`([A-Z][A-Z0-9_]{3,})`", text)):
                if not re.search(rf"\b{re.escape(name)}\b", code):
                    missing.append(f"{rel}: {name}")
        self.assertEqual(missing, [])


class TestChaosCoverage(unittest.TestCase):
    """
    PRINCIPLE-013 R7 (ADR-086, ADR-148): each named fault has a test that drives it. The map holds
    exact test names, not regexes: a regex matched any name containing "bak" or "corrupt", so
    renaming or deleting the real test left the fault silently uncovered.
    """

    FAULTS = {
        "0-byte state file": "test_zero_byte_power_loss_truncation_quarantine",
        "malformed JSON": "test_self_healing_quarantine_corrupted_json",
        "insufficient disk space": "test_a_full_disk_refuses_the_write_and_keeps_the_old_state",
        "recovery from .bak": "test_self_healing_recovery_from_shadow_backup",
        "concurrent writers": "test_parallel_checkpoints_do_not_lose_updates",
        "unreadable state file": "test_an_io_error_is_reported_not_quarantined",
        "failed rename": "test_failed_replace_keeps_the_old_ledger_and_removes_temp",
    }

    def test_every_named_fault_has_a_test(self):
        names = set()
        for module in ("test_kit.py", "test_integration.py"):
            names |= set(re.findall(r"def (test_\w+)", (ROOT_DIR / "tests" / module).read_text(encoding="utf-8")))
        for fault, test in self.FAULTS.items():
            with self.subTest(fault=fault):
                self.assertIn(test, names, f"the test named for {fault} is gone; the fault is uncovered")


class TestDogfoodFingerprint(unittest.TestCase):
    """The blast-radius hash reads only paths git status names, but still sees dirty content."""

    def test_verbose_trace_reconfigures_legacy_console_encoding(self):
        # Verbose mode replays emoji-bearing child output; cp1254/cp1252 consoles raise
        # UnicodeEncodeError unless stdout/stderr replace unsupported code points.
        source = (ROOT_DIR / "scripts" / "dogfood.py").read_text(encoding="utf-8")
        self.assertIn('sys.stdout.reconfigure(encoding="utf-8", errors="replace")', source)
        self.assertIn('sys.stderr.reconfigure(encoding="utf-8", errors="replace")', source)

    def test_dirty_content_changes_fingerprint_with_identical_status(self):
        root = Path(tempfile.mkdtemp(prefix="test_fingerprint_"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        dirty = root / "dirty.txt"
        dirty.write_text("one\n", encoding="utf-8")

        def status_only(command, **kwargs):
            return subprocess.CompletedProcess(command, 0, " M dirty.txt\0", "")

        with mock.patch("scripts.dogfood.ROOT_DIR", root), \
             mock.patch("scripts.dogfood.subprocess.run", side_effect=status_only):
            first = repo_fingerprint()
            dirty.write_text("two\n", encoding="utf-8")
            second = repo_fingerprint()
        self.assertIsNotNone(first)
        self.assertNotEqual(first, second)

    def test_rename_entry_hashes_the_new_path_and_consumes_the_old(self):
        root = Path(tempfile.mkdtemp(prefix="test_fingerprint_rename_"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        renamed = root / "new.txt"
        renamed.write_text("one\n", encoding="utf-8")
        # A Y-column entry is the only shape where `entry[0]` alone misses the second path;
        # `.txt` is the path the old parser would misread from "old.txt" if it did not consume it.
        decoy = root / ".txt"
        decoy.write_text("one\n", encoding="utf-8")

        def rename_status(command, **kwargs):
            return subprocess.CompletedProcess(command, 0, " R new.txt\0old.txt\0", "")

        with mock.patch("scripts.dogfood.ROOT_DIR", root), \
             mock.patch("scripts.dogfood.subprocess.run", side_effect=rename_status):
            first = repo_fingerprint()
            second = repo_fingerprint()
            decoy.write_text("two\n", encoding="utf-8")
            third = repo_fingerprint()
            renamed.write_text("two\n", encoding="utf-8")
            fourth = repo_fingerprint()
        self.assertEqual(first, second)
        self.assertEqual(first, third, "the old path must be consumed, not read as a path")
        self.assertNotEqual(first, fourth, "the new path's content is still hashed")

    def test_fingerprint_reads_dirty_content_across_chunks(self):
        root = Path(tempfile.mkdtemp(prefix="test_fingerprint_chunks_"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        dirty = root / "dirty.txt"
        dirty.write_text("abcdefghij\n", encoding="utf-8")

        def status_only(command, **kwargs):
            return subprocess.CompletedProcess(command, 0, " M dirty.txt\0", "")

        with mock.patch("scripts.dogfood.ROOT_DIR", root), \
             mock.patch("scripts.dogfood.FINGERPRINT_CHUNK", 3), \
             mock.patch("scripts.dogfood.subprocess.run", side_effect=status_only):
            first = repo_fingerprint()
            dirty.write_text("abcdXfghij\n", encoding="utf-8")
            second = repo_fingerprint()
        self.assertNotEqual(first, second, "a change after the first chunk must be hashed")


class TestAdrRegister(unittest.TestCase):
    """PRINCIPLE-016 R3 / PRINCIPLE-000 R3: ADR IDs are unique and consecutive (ADR-069)."""

    @staticmethod
    def register(*numbers):
        return "".join(f"### ADR-{n:03d}: t\n- body\n" for n in numbers)

    def test_consecutive_ids_pass(self):
        self.assertEqual(audit_adr_register(self.register(1, 2, 3)), [])

    def test_a_duplicate_fails(self):
        # Red-green pin: two sessions each appended ADR-064 and ADR-065 after ADR-066.
        self.assertEqual(audit_adr_register(self.register(64, 65, 66, 64)),
                         ["ADR-064 duplicates or precedes ADR-066; the next ID must be ADR-067"])

    def test_a_gap_fails(self):
        self.assertEqual(audit_adr_register(self.register(1, 3)),
                         ["ADR-003 skips after ADR-001; the next ID must be ADR-002"])

    def test_this_register_is_clean(self):
        self.assertEqual(audit_adr_register((KNOWLEDGE_DIR / "decisions.md").read_text(encoding="utf-8")), [])

    def test_commented_template_is_not_an_entry(self):
        text = ("<!-- Entry format:\n### ADR-001: template\n-->\n\n"
                "### ADR-001: real decision\n")
        self.assertEqual(audit_adr_register(text), [])


class TestPrinciple005Unambiguity(unittest.TestCase):
    """PRINCIPLE-005 must say the same thing to every model: exact labels, triggers and homes."""

    @classmethod
    def setUpClass(cls):
        cls.text = SSOT_MD.read_text(encoding="utf-8")
        cls.section = cls.text[cls.text.index("### PRINCIPLE-005:"):cls.text.index("\n### PRINCIPLE-006:")]
        cls.rules = cls.section[cls.section.index("- **Rules**:"):]

    def test_rules_contain_no_hedge_words(self):
        found = [h for h in TestPrinciple002Unambiguity.HEDGES if h in self.section]
        self.assertEqual(found, [], f"PRINCIPLE-005 contains open-ended wording: {found}")
        for vague in ("high-visibility", "speculative", "zero-ambiguity", "instant", "factual"):
            with self.subTest(word=vague):
                self.assertNotIn(vague, self.section)

    def test_every_rule_names_its_audience(self):
        numbered = re.findall(r"^  (\d+)\. \*\*([^*]+)\*\*([^\n]*)", self.rules, re.M)
        self.assertEqual(len(numbered), 6, "PRINCIPLE-005 must keep rules R1-R6 (cited elsewhere)")
        for number, _, rest in numbered:
            with self.subTest(rule=f"R{number}"):
                self.assertRegex(rest, r"\*\[(Agent|Maintainer|Agent \+ Maintainer)\]\*")

    def test_rule_labels_are_the_ones_the_gate_checks(self):
        # Red-green pin: R1 asked for an "orientation block" no program could recognise.
        for label in README_LABELS:
            with self.subTest(label=label):
                self.assertIn(label.rstrip(":").strip("*"), self.rules)
        self.assertIn(f"MUST NOT exceed {README_MAX_CHARS:,} characters", self.rules)

    def test_every_trigger_and_home_is_defined(self):
        for definition in (
            "in the same commit as a change that",
            "For any other change the agent MUST NOT edit `README.md`",
            "the agent MUST run it, in a temporary directory when it copies, moves or deletes files",
            "a directory shown with none is collapsed and exempt",
            "The R1 check compares the tree with `git ls-files`",
            "`README.md` MUST NOT restate a principle's rules anywhere",
            # Third pass (ADR-076): a changed exit condition matched no trigger, and the
            # hand-written principle table had drifted from 19 of 20 capsules.
            "changes what a command documented in `README.md` checks, writes or prints, or a condition under which it exits non-zero",
            "the same commit also updates that script's `--help`",
            "README's principle table needs no hand edit",
            "`--check` fails while that table is stale",
            # Second pass (ADR-068): "under it" had two readings, and the adopter had none.
            "inside the section it opens (up to the next heading of the same or a higher level)",
            "No `<FILL:` placeholder from the R6 template may remain",
            "MUST start its Quick Reference and tree from `.agents/rules/readme_quickref.md.template`",
            "MUST NOT copy AIKit's own Quick Reference",
            "the build and run commands the project has",
        ):
            with self.subTest(definition=definition):
                self.assertIn(definition, self.rules)

    def test_checklists_match_the_rules(self):
        # Red-green pin: Post-Flight demanded README reflect "all changes" (R2 forbids that) and
        # Pre-Flight demanded reviewing "every active principle" (PRINCIPLE-001 R3 forbids that).
        self.assertNotIn("to reflect all changes", self.text)
        self.assertNotIn("reviewed every active principle", self.text)
        self.assertIn("Did every change listed in **PRINCIPLE-005** R2 update **README.md**", self.text)


class TestPrinciple000Unambiguity(unittest.TestCase):
    """PRINCIPLE-000 must pass its own R7: every meta-rule is decidable, none licenses skipping."""

    @classmethod
    def setUpClass(cls):
        cls.text = SSOT_MD.read_text(encoding="utf-8")
        cls.section = cls.text[cls.text.index("### PRINCIPLE-000:"):cls.text.index("\n### PRINCIPLE-001:")]
        cls.rules = cls.section[cls.section.index("- **Rules**:"):]
        cls.word_list = re.search(r"It MUST NOT use these words: ([^\n]*)", cls.rules).group(1)

    def test_r7_word_list_is_the_hedge_list(self):
        # One list, two readers: the rule agents obey and the tests that check every principle.
        self.assertEqual(tuple(re.findall(r"`([^`]+)`", self.word_list)), TestPrinciple002Unambiguity.HEDGES)

    def test_principle_000_obeys_its_own_r7(self):
        # Red-green pin: P000 R2/R4 named no decidable condition ("systemic harmony", "degrades
        # code quality") while R7 forbade exactly that.
        body = self.section.replace(self.word_list, "")
        found = [h for h in TestPrinciple002Unambiguity.HEDGES if h in body]
        self.assertEqual(found, [], f"PRINCIPLE-000 uses its own banned words: {found}")
        for phrase in ("harmony", "appear in friction", "procedural formalism", "trumps", "craftsmanship, never"):
            with self.subTest(phrase=phrase):
                self.assertNotIn(phrase, self.section)

    def test_every_rule_names_its_audience(self):
        numbered = re.findall(r"^  (\d+)\. \*\*([^*]+)\*\*([^\n]*)", self.rules, re.M)
        self.assertEqual(len(numbered), 7, "PRINCIPLE-000 must keep rules R1-R7 (cited elsewhere)")
        for number, _, rest in numbered:
            with self.subTest(rule=f"R{number}"):
                self.assertRegex(rest, r"\*\[(Agent|Maintainer|Agent \+ Maintainer)\]\*")

    def test_every_meta_rule_is_decidable(self):
        for definition in (
            "an agent's own judgment that a rule does not fit is never one (R4)",
            "Two rules *conflict* when, at the same step, obeying one requires an action the other forbids",
            "report the conflict to the user in one line naming both rules",
            "a line starting `Cross-principle check:`",
            "The ADR's ID is read from the register, never recalled",
            "Code quality never licenses skipping a rule",
            "an assertion that cannot fail",
            "the rule that cites the other rule wins",
            "decided by PRINCIPLE-001 R1, not by this order",
        ):
            with self.subTest(definition=definition):
                self.assertIn(definition, self.rules)

    def test_second_pass_definitions(self):
        # Red-green pins (ADR-072): "principles the search found" mapped files to principles
        # differently per model; "hide a failure" did not separate cleanup from hiding; mutual
        # citation had no winner.
        for definition in (
            "names every principle `python scripts/sync_principles.py --citing PRINCIPLE-NNN` prints",
            "except those in `knowledge/decisions.md`",
            "an `except` block that neither re-raises, returns or exits with an error, nor writes a warning",
            "unless it only cleans up after an error that is already raised or reported",
            "when neither cites the other or each cites the other",
            # Third pass (ADR-074): "a change to a principle" and "the change's ADR" had no definition.
            "A principle is *changed* when its `### PRINCIPLE-NNN:` section in `GUIDELINES.md` differs from the last commit",
            "`python scripts/sync_principles.py --check` fails while a changed principle has no ADR added since the last commit",
            "A rule cites another when its text contains that rule's `PRINCIPLE-NNN RN`",
        ):
            with self.subTest(definition=definition):
                self.assertIn(definition, self.rules)

    def test_citing_set_is_computed_from_sections_only(self):
        text = ("### PRINCIPLE-001: A\n- cites PRINCIPLE-002.\n"
                "### PRINCIPLE-002: B\n- plain.\n"
                "### PRINCIPLE-003: C\n- cites PRINCIPLE-001 R2.\n"
                "## Checklist\n- PRINCIPLE-001 PRINCIPLE-002 PRINCIPLE-003\n")
        self.assertEqual(citing_principles(text, "PRINCIPLE-001"), ["PRINCIPLE-002", "PRINCIPLE-003"])
        self.assertEqual(citing_principles(text, "PRINCIPLE-002"), ["PRINCIPLE-001"])  # checklist ignored
        # ADR-137: P011 R8 cites PRINCIPLE-000 R5 (the silent-`except` clause the scan enforces).
        self.assertEqual(citing_principles(self.text, "PRINCIPLE-000"),
                         ["PRINCIPLE-001", "PRINCIPLE-002", "PRINCIPLE-003", "PRINCIPLE-004", "PRINCIPLE-007", "PRINCIPLE-009",
                          "PRINCIPLE-011", "PRINCIPLE-012", "PRINCIPLE-013", "PRINCIPLE-014", "PRINCIPLE-016", "PRINCIPLE-017",
                          "PRINCIPLE-019"])

    def test_r3_completeness_is_decided_by_the_gate(self):
        # Red-green pin (third pass, ADR-073): whether the ADR named every principle --citing
        # prints rested on the agent. cross_check_errors decides it from HEAD vs the tree.
        old = ("### PRINCIPLE-001: A\n- cites PRINCIPLE-002.\n"
               "### PRINCIPLE-002: B\n- plain.\n## Checklist\n")
        new = old.replace("- cites PRINCIPLE-002.", "- cites PRINCIPLE-002 R1.")
        adr = "### ADR-001: t\n- body\n"
        self.assertEqual(changed_principles(old, new), ["PRINCIPLE-001"])
        self.assertEqual(changed_principles(old, old.replace("plain.", "plain.  ")), [])  # whitespace only
        # Pre-Flight or Post-Flight checklist changes attribute to PRINCIPLE-001
        checklist_old = "### PRINCIPLE-001: A\n- body\n### Pre-Flight Checklist\n- [ ] item 1\n"
        checklist_new = "### PRINCIPLE-001: A\n- body\n### Pre-Flight Checklist\n- [ ] item 1 modified\n"
        self.assertEqual(changed_principles(checklist_old, checklist_new), ["PRINCIPLE-001"])
        self.assertEqual(cross_check_errors(old, old, adr, adr), [])
        self.assertEqual(cross_check_errors(old, new, adr, adr),
                         ["PRINCIPLE-001 changed but no ADR was added to knowledge/decisions.md (PRINCIPLE-004 R4)"])
        no_line = adr + "### ADR-002: rule\n- body\n"
        self.assertEqual(cross_check_errors(old, new, adr, no_line),
                         ["PRINCIPLE-001 changed but no added ADR has a 'Cross-principle check:' line"])
        incomplete = adr + "### ADR-002: rule\n- Cross-principle check: none\n"
        self.assertEqual(cross_check_errors(old, new, adr, incomplete),
                         ["PRINCIPLE-001 changed; its Cross-principle check line omits PRINCIPLE-002 "
                          "(python scripts/sync_principles.py --citing PRINCIPLE-001)"])
        complete = adr + "### ADR-002: rule\n- Cross-principle check: PRINCIPLE-002 (no conflict).\n"
        self.assertEqual(cross_check_errors(old, new, adr, complete), [])

    def test_capsule_does_not_license_skipping_procedure(self):
        # Red-green pin: "code quality primacy over procedural formalism" read, alone in Tier 1,
        # as permission to skip checkpoints and gates (contradicting PRINCIPLE-002 R5).
        capsule = re.search(r"- \*\*Invariant\*\*: ([^\n]*)", self.section).group(1)
        self.assertNotIn("formalism", capsule)
        self.assertIn("quality doubts go to the user", capsule)

    def test_rule_changes_carry_a_cross_principle_check(self):
        # R3 from ADR-070 on: every ADR whose title names a principle records the check.
        decisions = (KNOWLEDGE_DIR / "decisions.md").read_text(encoding="utf-8")
        for number, title, body in re.findall(r"^### ADR-(\d+): ([^\n]*)\n(.*?)(?=^### ADR-|\Z)",
                                              decisions, re.M | re.S):
            if int(number) >= 70 and "PRINCIPLE-" in title:
                with self.subTest(adr=number):
                    self.assertIn("Cross-principle check:", body)


class TestPrinciple006Unambiguity(unittest.TestCase):
    """PRINCIPLE-006 must say the same thing to every model: when to commit, what to do with failing work."""

    @classmethod
    def setUpClass(cls):
        cls.text = SSOT_MD.read_text(encoding="utf-8")
        cls.section = cls.text[cls.text.index("### PRINCIPLE-006:"):cls.text.index("\n### PRINCIPLE-007:")]
        cls.rules = cls.section[cls.section.index("- **Rules**:"):]

    def test_rules_contain_no_hedge_words(self):
        # Red-green pin (ADR-078): R1 used "e.g." and "$\rightarrow$", banned by PRINCIPLE-000 R7.
        found = [h for h in TestPrinciple002Unambiguity.HEDGES if h in self.section]
        self.assertEqual(found, [], f"PRINCIPLE-006 contains banned words: {found}")
        for vague in ("non-trivial", "logical, verified sub-task", "cleanly"):
            with self.subTest(phrase=vague):
                self.assertNotIn(vague, self.section)

    def test_every_rule_names_its_audience(self):
        numbered = re.findall(r"^  (\d+)\. \*\*([^*]+)\*\*([^\n]*)", self.rules, re.M)
        # R1-R6 are cited elsewhere and keep their numbers; R7 was appended by ADR-209.
        self.assertEqual([int(n) for n, _, _ in numbered], list(range(1, 8)),
                         "PRINCIPLE-006 must keep rules R1-R6 (cited elsewhere) and R7 after them")
        for number, _, rest in numbered:
            with self.subTest(rule=f"R{number}"):
                self.assertRegex(rest, r"\*\[(Agent|Maintainer|Agent \+ Maintainer)\]\*")

    def test_every_duty_is_defined(self):
        for definition in (
            "commit once per milestone as soon as that milestone's Phase 4 commands pass",
            "When commit delivery is not authorized, it MUST, once that milestone's Phase 4 commands pass, record the milestone as a `--checkpoint`",
            "whose `--desc` opens with `[milestone N/M]`",
            "A plan with one milestone is committed once, without a tag, under the same authorization test",
            "unless the informed override of PRINCIPLE-002 R5 applies",
            "the ledger holds the description, never the code",
            "--phase-num <1-5> --desc <text>",
            "A task is *abandoned* when the user cancels it",
            "that warning means this rule was skipped",
            "Staging follows PRINCIPLE-018 R2",
            # Second pass (ADR-111): a concurrent session committed another's uncommitted work.
            "a change it did not make (another session, the user) MUST stay unstaged",
            "when `HEAD` moved since the task began, the agent re-reads every file it will commit and the ADR register",
            "`--clean` deletes only buffers older than 60 seconds",
            "MUST write it as PRINCIPLE-013 R1 specifies",
        ):
            with self.subTest(definition=definition):
                self.assertIn(definition, self.rules)

    def test_no_second_home_for_rules_owned_elsewhere(self):
        # Red-green pin: R4 required only unit tests (P002 R1 requires every Phase 4 gate) and
        # forbade the commit P002 R5 allows; R3 restated P013 without fsync; R5 used --phase.
        for stale in ("passing unit tests (`PRINCIPLE-014`)", "buffer it in `.agents/task_ledger.json`",
                      "--phase <phase>", "never execute blind"):
            with self.subTest(stale=stale):
                self.assertNotIn(stale, self.rules)


class TestPrinciple007Unambiguity(unittest.TestCase):
    """PRINCIPLE-007 must say the same thing to every model: fixed fields, fixed labels, a scope test."""

    @classmethod
    def setUpClass(cls):
        cls.text = SSOT_MD.read_text(encoding="utf-8")
        cls.section = cls.text[cls.text.index("### PRINCIPLE-007:"):cls.text.index("\n### PRINCIPLE-008:")]
        cls.rules = cls.section[cls.section.index("- **Rules**:"):]

    def test_rules_contain_no_hedge_words(self):
        found = [h for h in TestPrinciple002Unambiguity.HEDGES if h in self.section]
        self.assertEqual(found, [], f"PRINCIPLE-007 contains banned words: {found}")
        # Red-green pin (ADR-080): undefined or unfalsifiable phrases of the previous text.
        for vague in ("4-quadrant", "micro-sanity", "non-trivial", "polished UI", "ultra-terse", "strictly bounded"):
            with self.subTest(phrase=vague):
                self.assertNotIn(vague, self.section)

    def test_every_rule_names_its_audience(self):
        numbered = re.findall(r"^  (\d+)\. \*\*([^*]+)\*\*([^\n]*)", self.rules, re.M)
        self.assertEqual(len(numbered), 6, "PRINCIPLE-007 must keep rules R1-R6 (cited elsewhere)")
        for number, _, rest in numbered:
            with self.subTest(rule=f"R{number}"):
                self.assertRegex(rest, r"\*\[(Agent|Maintainer|Agent \+ Maintainer)\]\*")

    def test_rules_match_the_checks(self):
        for label in RISK_DIMENSIONS:
            with self.subTest(label=label):
                self.assertIn(f"`{label}`", self.rules)
        for definition in (
            "The *impact assessment* is four fields: why, benefits, risks and mitigation",
            "`--checkpoint` warns when a task reaches Phase 3 or later with no assessment on record",
            "every concrete risk MUST have an entry in the mitigation field",
            "unless it is abstract, an overload, or declared in a Protocol or ABC",
            "`python scripts/update_knowledge_base.py` fails on each of them",
            "A change is *in scope* when a milestone of the recorded plan needs it",
            "it lists each one to the user as a suggestion in its final message",
            "--phase-num 2 --desc \"[1/M] ...\"",
            "The command exits 2 while a field or a risk verdict is missing",
            "at most 4 lines, one per field",
        ):
            with self.subTest(definition=definition):
                self.assertIn(definition, self.rules)

    def test_no_ban_contradicts_principle_000_r5(self):
        # Red-green pin: R3 banned every `pass`, including the cleanup blocks P000 R5 allows.
        self.assertNotIn("`pass`, or mock placeholders in production code paths", self.rules)

    def test_capsule_states_the_mechanisms(self):
        capsule = re.search(r"- \*\*Invariant\*\*: ([^\n]*)", self.section).group(1)
        for mechanism in ("first plan checkpoint carries --why --benefits --risks",
                          "(contract, dependency, concurrency, state) --mitigation",
                          "no todo or stub", "no change outside the plan"):
            with self.subTest(mechanism=mechanism):
                self.assertIn(mechanism, capsule.lower())


class TestRewrittenPrincipleWording(unittest.TestCase):
    """
    One data-driven check for every principle rewritten to a single reading (PRINCIPLE-000 R7):
    no banned word, every rule tagged with its audience, its definitions present and the vague
    phrases it replaced gone. A table instead of a class per principle keeps the unit tier fast.
    """

    REWRITTEN = {
        "PRINCIPLE-008": {
            "rules": 6,
            "present": [
                "the agent the user talks to is level 0",
                "no sub-agent MAY run at a level deeper than 3",
                "when it must change more than one layer, its plan entry states why",
                "When M' would exceed 6, the milestones after the current one become a separate task",
                "no milestone may use a class, function, flag or file that a later milestone creates",
                "When the decomposition yields more than 6, the agent MUST split the work into separate tasks",
                "A milestone changes one PRINCIPLE-009 layer together with its tests and documentation",
                "MUST record the revised plan as a new `[1/M']` Phase 2 checkpoint",
                # ADR-131: both ledgers, and the Claude Code deny rule that enforces it.
                "It MUST NOT write a task ledger (`.agents/task_ledger.json`, or a project's `.aikit/task_ledger.json`",
                "`.claude/settings.json` denies that edit to every agent",
                "sub-agents never write the ledger",
                "A sub-agent process MUST run non-interactively with closed stdin",
            ],
            "gone": ["non-trivial", "Target a bounded", "type(task)", "back to the parent task ledger",
                     "update the active task ledger (`.agents/task_ledger.json`) with refined sub-tasks"],
        },
        "PRINCIPLE-009": {
            "rules": 7,
            "present": [
                "A *pluggable boundary* is a role with two or more production implementations",
                "a test double alone does not make one",
                "when it has exactly one operation, as a `Callable` type",
                "The layers MAY share one module of at most 300 lines",
                "No module, at a boundary or not, MAY be named `utils`",
                "with 1 to 5 methods",
                "never by an `if`/`elif` chain on the name",
                "a constructor parameter that defaults to `None`",
                "Code MUST NOT assign to another module's or object's `_private` attribute",
                "fails on a junk-drawer module name, a role outside 1 to 5 methods and an import cycle",
                # ADR-114 replaced two pins of the concurrent session's R6 wording under PRINCIPLE-014
                # R2's exception (user approval to fix the principles; the ADR names them).
                "A project that calls an external AI model provider MUST",
                "for every benchmark score, the URL the score was read from",
                "A score without that URL is marked `unverified` and is never a reason to choose a model",
                "Agent Host Environment & Client Portability",
            ],

            "gone": ["Anti-Junk-Drawer Invariant", "100% of the declared contract", "e.g. `CliParser`",
                     "date_utils.py"],
        },
        "PRINCIPLE-010": {
            "rules": 7,
            "present": [
                "timeout= on subprocess, with on open(); one fsync per file; `--help` <250ms",
                "A membership test inside a loop MUST use a `set` or `dict`",
                "Input whose size the program does not control",
                "only when that step, measured single-threaded, takes 200ms or more",
                "a pool of at most `os.cpu_count()` workers",
                "fails on a blocking subprocess call without `timeout=` and on `open()` outside a `with`",
                "one fsync per file written is PRINCIPLE-013 R1, not a violation",
                "in under 250ms as a fresh process, interpreter start included",
                "MUST state its before and after measurement",
                "`open()` and `Path.open()` run only as a `with` item",
                "measured on the machine that runs Phase 4, and a breach there is fixed before the commit",
            ],
            "gone": ["<100ms", "under 20ms", "genuinely", "High-frequency", "tight loops", "(`timeout=30`)",
                     "without measurable profiling justification"],
        },
        "PRINCIPLE-011": {
            "rules": 8,
            "present": [
                "MUST run with only the dependencies declared under PRINCIPLE-003 R3",
                "A dependency that only one adapter uses is imported inside that adapter",
                "MUST NOT read the keyboard (`input()`, a confirmation prompt) unless the user passed `--interactive`",
                "never `os.environ[...]`; `python scripts/update_knowledge_base.py` fails on such a read",
                "it prints one line naming that mode before its output",
                "follow PRINCIPLE-003 R4",
                "a line whose first non-blank text is `Why:` with the cause",
                "A usage error (exit `2`) prints its message on stderr",
                "In AIKit these are `python scripts/disruption_recovery.py --audit` and `python scripts/dogfood.py`",
                # R8 (ADR-121): software other than AIKit is built in a registered project.
                "is built in a project registered with `python aikit.py`, never in AIKit's own tree",
                "ledger commands take `--workspace <project path>`",
                # ADR-123: one command is the project's Phase 4; it includes the secret scan.
                "its Phase 4 gate is `python aikit.py check <name>`",
                "which runs the project's test command, the checks its own configuration declares and the secret scan",
                # ADR-128: the guidelines gate holds a project to AIKit's own audits, README included.
                "the README rules, unfinished code, code structure and the decision register exactly as for AIKit",
                "fails when a task ledger changed during the run",
                "asks the user which project, or the name of a new one, before writing code",
                "apply only to changes to AIKit itself",
                # ADR-137: every project check also scans source and asset hygiene.
                "a built-in hygiene scan of the project's source and static assets",
                # ADR-139: the checklist outcome is recorded with the task before the commit.
                "`checklists: passed` or the failed or skipped item IDs, in the task's latest checkpoint description",
                # ADR-130: the project's own guidelines are read before code and recorded with `guideline`.
                "Before writing code in a project, the agent reads its guidelines",
                "records it with `python aikit.py guideline <name>",
                # ADR-134: publishing is outward-facing, private by default, scanned first.
                "`python aikit.py publish <name>` uploads the project's commits to its own GitHub repository",
                "the agent runs it only when the user asks",
            ],
            "gone": ["Third-party packages must be strictly optional", "sensible", "Systems should embed",
                     "banning hardcoded"],
        },
        "PRINCIPLE-012": {
            "rules": 8,
            "present": [
                "Rules R1, R2, R4, R6 bind code that calls an LLM API; R3, R5, R7 and R8 bind the agent",
                # ADR-131: the Claude Code delegation path.
                "In Claude Code the sub-agents are the generated `.claude/agents/<role>.md` profiles",
                "elsewhere `python aikit.py delegate <role>` runs the role through OpenCode",
                # ADR-132: free models only, refused before any call; keys from the environment.
                "`aikit delegate` refuses any other model before it calls one",
                "a provider's key is read only from its environment variable",
                "at or below 16,000 characters",
                "the variable tail of one request (R2)",
                "These limits apply together with PRINCIPLE-004 R5's 100 lines per command",
                "The ledger converts absolute paths inside the repository itself (`repo_relative`)",
                "the prefix MUST be byte-identical across requests",
                "at most 3 lines of context per hunk",
                "a search shows at most 50 matches",
                "validate the reply before use",
                "store repository-relative paths",
                "MUST define a maximum step count and a maximum token count as named parameters",
                "a function whose body only calls another function with the same arguments",
                # ADR-114 replaced three pins of R8's earlier wording (PRINCIPLE-014 R2 exception).
                "MAY delegate pattern searches, file indexing, boilerplate drafting or linting",
                "whose context window, as listed in `knowledge/model_benchmarks.md`, holds the brief",
                "it compares only sourced benchmark scores (PRINCIPLE-009 R6)",
            ],

            "gone": ["target <4,000 tokens", "guaranteeing", "top-k relevant", "~70%", "maximize syntactic density",
                     "excessive class hierarchies", "($K$ turns)"],
        },
        "PRINCIPLE-013": {
            "rules": 7,
            "present": [
                "A *state file* is a file the program writes and a later run reads back",
                "A *generated file* is rebuilt by a command from tracked sources",
                "retried up to 5 times with exponential backoff",
                "at least 10MB are free",
                "acquired with a 3-second timeout; a lock older than 30 seconds is broken",
                # ADR-146: an unreadable file is not a corrupt one.
                "A file the process cannot read at all (locked, permission denied, unreadable device) has "
                "not failed to parse",
                "A *long-running* process runs until stopped",
                "a command that ends after one action exits 1 with PRINCIPLE-011 R6's message, never a traceback",
                "removed by `--clean` as PRINCIPLE-006 R6 specifies, never by an automatic sweep at startup",
                "at least one test for each fault",
            ],
            "gone": ["non-trivial", "$2\\text{s}$", "guaranteeing 100%", "Startup self-healing must actively sweep",
                     "$3 \\le"],
        },
        "PRINCIPLE-014": {
            "rules": 7,
            "present": [
                "MUST add or change a test in `tests/` that fails on the code before the change and passes after it",
                "*Weakening* a test is any change after which it accepts a behaviour it rejected before",
                "Rewording a test so that it rejects the same behaviours, or more, is not weakening",
                "It MAY weaken a test only when the user approved the contract change the test encodes",
                "is *flaky* and blocks every commit until fixed",
                "Every test asserts at least one observable result",
                "a unit test checks that every test method calls an assertion",
                "a unit test checks that no test module imports `socket`",
                "at least one test with invalid input",
            ],
            "gone": ["e.g. changing strict checks", "critical paths", "Avoid over-mocking", "Prioritize hostile",
                     "unless the user explicitly requested a breaking contract overhaul"],
        },
        "PRINCIPLE-015": {
            "rules": 8,
            "present": [
                "AIKit's runner is `python scripts/dogfood.py`, for AIKit's CLIs; an adopting project writes its own",
                "within 500ms",
                "kills the whole process tree",
                "the duty itself is PRINCIPLE-011 R2 and R5",
                "fails when it changed; it MUST NOT write to the user's home folders",
                "Running `--help` alone is not a dogfood run",
                "the one exception is R7's run log, which MUST be listed in `.gitignore`",
                "a content fingerprint of the repository's tracked files",
                "The runner prints at most 15 lines",
                "It is one of PRINCIPLE-018 R3's commit gates",
                "obeys the step and token caps of PRINCIPLE-012 R6",
            ],
            "gone": ["remain concise", "(<15 lines)", "strictly prohibited", "bit-for-bit clean"],
        },
        "PRINCIPLE-016": {
            "rules": 6,
            "present": [
                "a section that does not apply says \"Not applicable\" and why, never template text",
                "`architecture.md` when a module, layer or process boundary is added, removed or moved",
                "`codebase_map.md` is never edited by hand",
                "they MUST NOT restate rule text (PRINCIPLE-001 R7)",
                "A unit test fails when a `PRINCIPLE-NNN RN` citation names a rule that does not exist",
                "An ADR MAY be edited until the commit that adds it; after that its text is fixed",
                "The one exception is a heading ID that `python scripts/update_knowledge_base.py` reports as duplicate or skipped",
                "A persisted schema has a version key",
                "A reader refuses a version it does not support without modifying, quarantining or overwriting the file",
                "read in slices (PRINCIPLE-004 R3)",
            ],
            "gone": ["high-density", "instant cold-start", "`schema_version`", "`view_file`", "strictly prohibited"],
        },
        "PRINCIPLE-017": {
            "rules": 6,
            "present": [
                "`- **Problem**:`, `- **Concept**:`, `- **Invariant**:` (its capsule) and `- **Rules**:`",
                "each tagged with its audience and written as PRINCIPLE-000 R7 requires",
                "exits 1 on a missing section, a rule without an audience tag, an empty title or a duplicate ID",
                "a host is supported by adding its file to this generator's target list (`TIER1_TARGETS`)",
                "exits 1 with PRINCIPLE-011 R6's message when the file is longer",
                "A commit MUST NOT be made while either fails (PRINCIPLE-018 R3)",
                "A principle belongs to the nearest `## ... Phase N:` heading above it",
                "at most 1,200 characters",
            ],
            "gone": ["~300 tokens", "plus an optional `- **Problem**:`", "without rigid hardcoded range limits",
                     "strictly prohibited"],
        },
        "PRINCIPLE-018": {
            "rules": 7,
            "present": [
                # ADR-149: the commit is verified on its own before it is pushed.
                "the agent runs `python scripts/verify_commit.py`; the push follows only when it exits 0",
                "the commit is a different tree whenever staging is a subset of it",
                # ADR-162: a host that forbids unrequested git operations makes delivery unauthorized.
                "Commit delivery* is authorized when the user asked in this task for a commit or a pull request",
                "Push delivery* is authorized when the user asked in this task for a push or a pull request",
                "Commit delivery is not authorized when the user said not to commit",
                "push delivery is not authorized when the user said not to push",
                "The agent MUST check its host platform's standing instructions before deciding to commit or push",
                "when it is not authorized, it stops after Phase 4 and reports the uncommitted files",
                "when push delivery is authorized (R1); otherwise it reports the commit as local only",
                "MUST pass before the commit",
                "It MUST NOT run `git add .`, `git add -A`, `git add --all`, `git add -u` or `git commit -a`",
                "except when the informed override of PRINCIPLE-002 R5 applies, the agent MUST NOT commit until all three hold",
                "it runs `git rebase --abort` and asks the user",
                "A branch without an upstream is pushed with `git push -u origin <branch>`",
                "with remotes but none named `origin` it asks the user which to use",
                "to undo a pushed commit, `git revert <hash>`",
                "says whether it was pushed",
            ],
            "gone": ["mechanically locked", "concise status summary", "(<10 lines)",
                     "always use non-destructive rollbacks"],
        },
        "PRINCIPLE-019": {
            "rules": 7,
            "present": [
                "Credentials live only in the environment or a secret store",
                # ADR-145: a push is scanned for what it uploads, not for the working tree.
                "`--commits <range>` scans the lines the commits in a range add",
                "push nothing past a finding",
                # ADR-133: a real key, split in a test fixture, was committed.
                "a secret detector's test sample is fabricated or generated at run time",
                "A unit test checks that each is present",
                "MUST NOT contain its value, an authorization header or a raw provider response",
                "shows at most its first 4 characters followed by `***`",
                "This binds the secret scanner too: its findings print the redacted line (`redact`)",
                "A false positive is allowed only by a `# aikit:allow-secret` comment",
                "It MUST NOT present `git reset`, a force-push or a deleted file as the remedy",
                "A step that only reads uses a read-only credential",
            ],
            "gone": ["`credentials*`", "`secrets*`", "cloud CLI config directories", "prefer read-only",
                     "narrowest scope"],
        },
        "PRINCIPLE-001": {
            "rules": 9,
            # ADR-130: the project tier, below Tier 1B and every principle.
            "present": ["*Project tier* is one project's own rules in its `.aikit/guidelines.md`",
                        "never enter a Tier 1 file"],
            "gone": [],
            "skip_words": True,
        },
        "PRINCIPLE-000": {
            "rules": 7,
            "present": ["weakening a test (as PRINCIPLE-014 R2 defines it) without the user approval and ADR that rule requires",
                        # ADR-130: a project's own rules rank below every principle.
                        "A project guideline (PRINCIPLE-001 R4) ranks below every principle",
                        "the principle applies and the agent tells the user"],
            "gone": ["skipping, deleting or loosening a test, threshold, allowlist entry or budget to make a check pass without an ADR"],
            # R7 lists the banned words themselves; TestPrinciple000Unambiguity checks the rest.
            "skip_words": True,
        },
    }

    @classmethod
    def setUpClass(cls):
        cls.sections = principle_sections(SSOT_MD.read_text(encoding="utf-8"))

    def test_rewritten_principles_have_one_reading(self):
        for pid, spec in self.REWRITTEN.items():
            section = self.sections[pid]
            rules = section[section.index("- **Rules**:"):]
            with self.subTest(pid=pid, check="banned words"):
                # Whole words for alphabetic entries: "mentally" must not match "incrementally".
                found = [h for h in TestPrinciple002Unambiguity.HEDGES
                         if (re.search(rf"(?<![A-Za-z]){re.escape(h)}(?![A-Za-z])", section)
                             if h[0].isalpha() else h in section)]
                self.assertEqual([] if spec.get("skip_words") else found, [])
            numbered = re.findall(r"^  (\d+)\. \*\*([^*]+)\*\*([^\n]*)", rules, re.M)
            with self.subTest(pid=pid, check="rule count"):
                self.assertEqual(len(numbered), spec["rules"], "rule numbers are cited elsewhere")
            for number, _, rest in numbered:
                with self.subTest(pid=pid, rule=f"R{number}"):
                    self.assertRegex(rest, r"\*\[(Agent|Maintainer|Agent \+ Maintainer)\]\*")
            for text in spec["present"]:
                with self.subTest(pid=pid, present=text):
                    self.assertIn(text, section)
            for text in spec["gone"]:
                with self.subTest(pid=pid, gone=text):
                    self.assertNotIn(text, section)


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

    def test_every_agent_rule_reaches_tier1(self):
        # An [Agent] rule that only exists in Tier 2 is invisible to an agent that reads only its
        # Tier 1 file. R8 (checklists) was exactly that until this pass.
        rendered = render_tier1_target("# probe", parse_principles(SSOT_MD))
        required = {
            "R1 hand-edit ban": "do not edit",
            "R1 precedence": "wins on conflict",
            "R3 contract trigger": "contract change",
            "R3 failure trigger": "failure",
            "R3 ambiguity trigger": "ambiguity",
            "R3 involved principles": "sync_principles.py --involved",
            "R3 no full load": "never the whole file unless asked",
            "R8 Pre-Flight": "Pre-Flight checklist before the first Track C edit",
            "R8 Post-Flight": "Post-Flight checklist before any Track B or C commit",
            "R8 reporting": "report only failed items",
        }
        for rule, phrase in required.items():
            with self.subTest(rule=rule):
                self.assertIn(phrase, rendered, f"{rule} does not reach Tier 1")

    def test_every_tier1_target_names_the_operational_runbook(self):
        # The runbook is auto-discovered by 2 of the 8 supported hosts (.agents/skills/ and
        # .claude/skills/); the other 6 read only their Tier 1 file, so without this line every
        # rule placed in the skill is invisible to them (ADR-176). A capsule that merely mentions
        # the path must not satisfy this, so the assertion requires a pointer line.
        runbook = ".agents/skills/aikit/SKILL.md"
        principles = parse_principles(SSOT_MD)
        for rel, heading in TIER1_TARGETS.items():
            with self.subTest(target=rel):
                rendered = render_tier1_target(heading, principles)
                self.assertTrue(any(line.startswith("> Runbook: ") and runbook in line
                                    for line in rendered.splitlines()),
                                f"{rel} has no runbook pointer line")
        self.assertTrue((ROOT_DIR / ".agents" / "skills" / "aikit" / "SKILL.md").is_file(),
                        "the Tier 1 header points at a runbook that does not exist")

    def test_tier1_header_does_not_repeat_the_generator_name(self):
        # The header spent 32 of the budget's last characters naming its own generator, which the
        # same file already names twice. Removing it is safe only while all three hold (ADR-175).
        rendered = render_tier1_target("# probe", parse_principles(SSOT_MD))
        self.assertNotIn("by `scripts/sync_principles.py`", rendered)
        self.assertIn("Generated from `GUIDELINES.md`", rendered)
        self.assertIn("do not edit", rendered)
        self.assertIn("scripts/sync_principles.py", rendered,
                      "the PRINCIPLE-017 capsule must still name the generator")
        self.assertIn("sync_principles.py --involved", rendered)
        self.assertTrue(is_generated_target(rendered),
                        "sync would stop recognizing its own output and refuse to rewrite it")

    def test_precedence_never_contradicts_another_principle(self):
        # Red-green pin: "an explicit user instruction overrides both" contradicted PRINCIPLE-002
        # R5 ("skip tests" must not bypass the gate), so models split on which rule to obey.
        precedence = self.rules.split("*Precedence*")[1].split("\n     - ")[0]
        self.assertNotIn("overrides both", precedence)
        self.assertIn("does not override another principle", precedence)
        self.assertIn("PRINCIPLE-002 R5", precedence)

    def test_open_terms_are_defined(self):
        # Terms a model would otherwise resolve its own way must be defined in the rule text.
        for definition in ("A principle is *involved* when a backtick-quoted name in its capsule",
                           "other than those needed to compute the involved principles",
                           "overrides exactly two things in this principle",
                           "An item that does not apply to the task counts as passed",
                           "a public function (a module-level name not starting with `_`)",
                           "counts as loading it in full",
                           "Track A tasks evaluate neither"):
            with self.subTest(definition=definition):
                self.assertIn(definition, self.rules)

    def test_involvement_is_deterministic(self):
        # Red-green pin: "involved" used to hinge on undefined "terms"; common words like "test"
        # occur in most capsules, so models built different reading lists. Now it is computed.
        principles = parse_principles(SSOT_MD)
        cases = {
            "edit README.md typo": ["PRINCIPLE-003"],
            "FAIL: python scripts/dogfood.py exited 1": ["PRINCIPLE-015"],
            "python scripts/check_secrets.py --all failed": ["PRINCIPLE-019"],
            "[TOKEN EXCEEDED] (PRINCIPLE-001)": ["PRINCIPLE-001"],
            "PRINCIPLE-999 is not a principle": ["PRINCIPLE-003"],
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertEqual(involved_principles(principles, text), expected)
                # Same input, same answer: no model judgement involved.
                self.assertEqual(involved_principles(principles, text),
                                 involved_principles(principles, text))

    def test_common_words_do_not_involve_principles(self):
        # Only backtick-quoted names count, so prose words never trigger involvement.
        text = "test gate tier budget capsule commit checklist schema"
        self.assertEqual(involved_principles(parse_principles(SSOT_MD), text), ["PRINCIPLE-003"])

    def test_single_id_placeholder(self):
        # Two placeholders for one thing ("XXX" in Tier 1, "NNN" in R5) invite two readings.
        retired = "PRINCIPLE-" + "XXX"
        files = [SSOT_MD, ROOT_DIR / "scripts" / "sync_principles.py", ROOT_DIR / "README.md"]
        files += [ROOT_DIR / rel for rel in TIER1_TARGETS]
        for path in files:
            with self.subTest(file=path.name):
                self.assertNotIn(retired, path.read_text(encoding="utf-8"))

    def test_tool_neutral_retrieval(self):
        # IDE-specific tool names make other agents guess an equivalent.
        for tool_name in ("view_file", "grep_search", "Query="):
            self.assertNotIn(tool_name, self.section, f"tool-specific term '{tool_name}' in P001")


class TestPrinciple002Unambiguity(unittest.TestCase):
    """
    PRINCIPLE-002 must give every model the same track, the same phase gates and the same
    answer to "commit now, skip the tests". Its cross-references must point at text that exists.
    """

    HEDGES = TestPrinciple001Unambiguity.HEDGES + ("$\\rightarrow$", "zero-friction", "instantly")

    @classmethod
    def setUpClass(cls):
        text = SSOT_MD.read_text(encoding="utf-8")
        cls.text = text
        cls.section = text[text.index("### PRINCIPLE-002:"):text.index("\n### PRINCIPLE-003:")]
        cls.rules = cls.section[cls.section.index("- **Rules**:"):]

    def _rule(self, pid, number):
        start = self.text.index(f"### {pid}:")
        end = self.text.index("\n### PRINCIPLE-", start + 5)
        match = re.search(rf"^  {number}\. \*\*([^*]+)\*\*(.*?)(?=^  \d+\. \*\*|\Z)",
                          self.text[start:end], re.M | re.S)
        self.assertIsNotNone(match, f"{pid} R{number} not found")
        return match.group(1), match.group(2)

    def test_rules_contain_no_hedge_words(self):
        found = [h for h in self.HEDGES if h in self.section.lower() or h in self.section]
        self.assertEqual(found, [], f"PRINCIPLE-002 contains open-ended wording: {found}")

    def test_every_rule_names_its_audience(self):
        numbered = re.findall(r"^  (\d+)\. \*\*([^*]+)\*\*([^\n]*)", self.rules, re.M)
        self.assertEqual(len(numbered), 7, "PRINCIPLE-002 must keep rules R1-R7 (cited elsewhere)")
        for number, title, rest in numbered:
            with self.subTest(rule=f"R{number}"):
                self.assertRegex(rest, r"\*\[(Agent|Maintainer|Agent \+ Maintainer)\]\*")

    def test_open_decisions_are_defined(self):
        for definition in (
            "`python scripts/disruption_recovery.py --track`",       # track is computed
            "Phase 2 is skipped",                                     # Track B phases
            "Phase 4 is the same full gate set for Track B and Track C",
            "when the fix adds, removes or renames a public contract",  # recoil target
            "run every Phase 4 command again, not only the one that failed",
            "any file edit after Phase 4 passed requires running Phase 4 again",
            "`Unverified: <the gates named>`",                        # informed override
            "--phase-num <1-5>",                                      # how phase is recorded
            "are bookkeeping: they never require re-running Phase 4",  # no ledger loop
            "or when `--track` now reports a higher track",           # recoil is checkable
            "on a Track B task, one checkpoint on entering Phase 3",   # proportionate
            "--complete <task_id>",                                   # task is closed
            "R2 applies and the agent reports the failure",           # failure under pressure
        ):
            with self.subTest(definition=definition):
                self.assertIn(definition, self.rules)

    def test_cross_references_resolve(self):
        # Every rule P002 leans on must exist and say what P002 assumes it says.
        _, p018_r3 = self._rule("PRINCIPLE-018", 3)
        self.assertIn("(1)", p018_r3)
        self.assertIn("(2)", p018_r3)
        title, p014_r2 = self._rule("PRINCIPLE-014", 2)
        self.assertIn("Test Sanctity", title)
        title, _ = self._rule("PRINCIPLE-001", 3)
        self.assertIn("Retrieval Triggers", title)
        _, p001_r8 = self._rule("PRINCIPLE-001", 8)
        self.assertIn("Track C", p001_r8)  # Pre-Flight = Phase 2, which only Track C runs
        self.assertIn("Track A tasks evaluate neither", p001_r8)

    def test_p001_precedence_points_at_this_r5(self):
        # PRINCIPLE-001 R1 defers user-vs-principle conflicts to PRINCIPLE-002 R5 by number.
        title, body = self._rule("PRINCIPLE-002", 5)
        self.assertIn("Immunity to Late-Stage User Priming", title)
        self.assertIn("explicitly instructs it to deliver anyway", body)
        self.assertIn("MAY commit and push", body)  # push is covered, not left open

    def test_checklists_are_in_principle_order(self):
        # R6: checklist items appear in ascending principle-ID order.
        for heading in ("Pre-Flight Checklist", "Post-Flight Checklist"):
            start = re.search(rf"^###[^\n]*{heading}", self.text, re.M).end()
            nxt = re.search(r"^(#|---)", self.text[start:], re.M)  # next heading or rule
            block = self.text[start:start + nxt.start()] if nxt else self.text[start:]
            ids = re.findall(r"PRINCIPLE-(\d{3})", block)
            with self.subTest(checklist=heading):
                self.assertEqual(ids, sorted(ids), f"{heading} items are out of principle order")


class TestPrinciple003Unambiguity(unittest.TestCase):
    """
    PRINCIPLE-003 must give every model the same grounding steps and the same answer to "is this
    ambiguity mine to resolve or the program's?". Its claims about this repository must be true.
    """

    @classmethod
    def setUpClass(cls):
        cls.text = SSOT_MD.read_text(encoding="utf-8")
        cls.section = cls.text[cls.text.index("### PRINCIPLE-003:"):cls.text.index("\n### PRINCIPLE-004:")]
        cls.rules = cls.section[cls.section.index("- **Rules**:"):]

    def test_rules_contain_no_hedge_words(self):
        found = [h for h in TestPrinciple002Unambiguity.HEDGES
                 if h in self.section.lower() or h in self.section]
        self.assertEqual(found, [], f"PRINCIPLE-003 contains open-ended wording: {found}")

    def test_every_rule_names_its_audience(self):
        numbered = re.findall(r"^  (\d+)\. \*\*([^*]+)\*\*([^\n]*)", self.rules, re.M)
        self.assertEqual(len(numbered), 7, "PRINCIPLE-003 must keep rules R1-R7 (cited elsewhere)")
        for number, _, rest in numbered:
            with self.subTest(rule=f"R{number}"):
                self.assertRegex(rest, r"\*\[(Agent|Maintainer|Agent \+ Maintainer)\]\*")

    def test_ambiguity_split_is_decided_by_one_question(self):
        # Red-green pin: "data/runtime" vs "architectural/intent" had no deciding criterion.
        self.assertIn("The deciding question for any ambiguity is who faces it", self.rules)
        self.assertIn("*Runtime ambiguity* (the running program faces it)", self.rules)
        self.assertIn("*Intent ambiguity* (the agent faces it)", self.rules)
        self.assertIn("MUST NOT take a destructive action: deleting or overwriting", self.rules)

    def test_open_terms_are_defined(self):
        for definition in (
            "the file MUST NOT have been written since that read",
            "`git grep -n -w -e <name>`",
            "Hits in `knowledge/decisions.md` always stay unchanged",
            "Declaring a new dependency requires the user's explicit approval",
            "An optional argument the user simply did not give is not missing input",
            "it MAY continue work that does not depend on the answer",
            "including overwriting the whole file",
            "does not satisfy this rule unless that check passes",
            "MUST NOT use syntax or standard-library APIs introduced after that version",
            "or what a function returns or raises",
            "including tests and documentation",
            "A *dependency* is any import outside the language's standard library",
            "MUST NOT use `shell=True` or `os.system`",
            "listing the options numbered, each with its observable difference",
        ):
            with self.subTest(definition=definition):
                self.assertIn(definition, self.rules)

    def test_cross_references_resolve(self):
        for pid, number, expected in (("PRINCIPLE-011", 6, "Remediation Triad"),
                                      ("PRINCIPLE-014", 7, "Reachability"),
                                      ("PRINCIPLE-016", 2, "Code-and-Doc Pairing"),
                                      ("PRINCIPLE-001", 3, "Retrieval Triggers")):
            start = self.text.index(f"### {pid}:")
            block = self.text[start:self.text.index("\n### PRINCIPLE-", start + 5)]
            title = re.search(rf"^  {number}\. \*\*([^*]+)\*\*", block, re.M)
            with self.subTest(ref=f"{pid} R{number}"):
                self.assertIsNotNone(title)
                self.assertIn(expected, title.group(1))

    def test_every_external_program_the_scripts_run_is_declared(self):
        # Red-green pin: R3 requires declared dependencies, yet the scripts ran `git` while the
        # README prerequisites said "Standard Library only".
        os_bundled = {"taskkill"}  # ships with Windows; governed by R4, not R3
        prerequisites = next(l for l in README_MD.read_text(encoding="utf-8").splitlines()
                             if "Runtime Prerequisites" in l)
        for script in sorted((ROOT_DIR / "scripts").glob("*.py")):
            source = script.read_text(encoding="utf-8")
            # What actually executes: the first element of a list handed straight to
            # subprocess.run/Popen, or a wrapper's ["<program>", *args]. Wrapper arguments such as
            # git_output(["diff", ...]) are subcommands, not programs.
            executed = set(re.findall(r'subprocess\.(?:run|Popen)\(\s*\[\s*"([a-z][\w.-]*)"', source))
            executed |= set(re.findall(r'\[\s*"([a-z][\w.-]*)",\s*\*args\]', source))
            for program in executed:
                if program in os_bundled or program.startswith("-"):
                    continue
                with self.subTest(script=script.name, program=program):
                    self.assertIn(f"`{program}`", prerequisites,
                                  f"{script.name} runs undeclared program {program!r}")

    def test_no_silent_broad_exception_handlers(self):
        # Red-green pin (R6, PRINCIPLE-007 R3): six `except Exception: pass/return` blocks made the
        # scripts continue on silent guesses - e.g. an unreadable backup silently became an empty
        # ledger, and a failed audit scan reported "clean".
        import ast
        for script in sorted((ROOT_DIR / "scripts").glob("*.py")):
            # The shared content-keyed cache: the knowledge-base tests parse these same files.
            tree = parse_source(script.read_text(encoding="utf-8"), str(script))
            for node in ast.walk(tree):
                if not isinstance(node, ast.ExceptHandler) or node.type is None:
                    continue
                broad = "Exception" in ast.dump(node.type) and "Error" not in ast.dump(node.type)
                silent = all(isinstance(b, (ast.Pass, ast.Return, ast.Continue)) for b in node.body)
                with self.subTest(script=script.name, line=node.lineno):
                    self.assertFalse(broad and silent,
                                     f"{script.name}:{node.lineno} swallows Exception silently")

    def test_user_facing_commands_use_python_not_py(self):
        # R4 + PRINCIPLE-011 R6: a remediation command must work when copy-pasted on any OS; the
        # `py` launcher exists only on Windows.
        for path in [*sorted((ROOT_DIR / "scripts").glob("*.py")), SSOT_MD, README_MD]:
            with self.subTest(file=path.name):
                self.assertNotRegex(path.read_text(encoding="utf-8"), r"(?<![\w-])py scripts/")

    def test_unmeasurable_disk_space_is_announced(self):
        real = shutil.disk_usage
        self.addCleanup(setattr, shutil, "disk_usage", real)

        def fail(path):
            raise OSError("statvfs unavailable")
        shutil.disk_usage = fail
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertTrue(check_disk_headroom(Path(tempfile.gettempdir())))
        self.assertIn("[WARN] Could not measure free space", err.getvalue())

    def test_unreadable_backup_is_announced(self):
        led = Path(tempfile.mkdtemp(prefix="test_bak_")) / "task_ledger.json"
        self.addCleanup(shutil.rmtree, led.parent, ignore_errors=True)
        led.write_text("{ corrupt", encoding="utf-8")
        led.with_suffix(".json.bak").write_text("{ also corrupt", encoding="utf-8")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            self.assertEqual(load_ledger(led)["checkpoints"], [])
        self.assertIn("Task history was not recovered", err.getvalue())

    def test_failed_audit_scan_is_never_reported_clean(self):
        report = format_audit_report({"clean_shutdown": True, "scan_errors": ["temp-buffer scan: denied"]})
        self.assertNotIn("Clean state", report)
        self.assertIn("Audit incomplete", report)
        self.assertIn("temp-buffer scan: denied", report)

    def test_ast_gate_rejects_syntax_newer_than_the_minimum(self):
        # R4/R7: the developer's interpreter is newer than the declared minimum (3.14 vs 3.10), so
        # newer syntax would pass locally and fail for users. The gate parses at MIN_PYTHON.
        self.assertEqual(MIN_PYTHON, (3, 10))
        prereq = next(l for l in README_MD.read_text(encoding="utf-8").splitlines()
                      if "Runtime Prerequisites" in l)
        self.assertIn(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+", prereq, "MIN_PYTHON drifted from README")
        probe = Path(tempfile.mkdtemp(prefix="test_minver_")) / "m.py"
        self.addCleanup(shutil.rmtree, probe.parent, ignore_errors=True)
        for name, source in (("except* (3.11)", "try:\n    pass\nexcept* ValueError:\n    pass\n"),
                             ("PEP 695 (3.12)", "def f[T](x: T) -> T:\n    return x\n")):
            with self.subTest(syntax=name):
                probe.write_text(source, encoding="utf-8")
                with self.assertRaises(ValueError):
                    extract_python_symbols(probe, strict=True)
        probe.write_text("match 1:\n    case 1:\n        pass\n", encoding="utf-8")
        self.assertNotIn("error", extract_python_symbols(probe))  # 3.10 syntax is fine

    def test_no_standard_library_apis_newer_than_the_minimum(self):
        # The parser cannot see API age; these are the post-3.10 stdlib names most often reached for.
        # Names are assembled from fragments so this test's own source never matches itself.
        names = ["toml" + "lib", "itertools." + "batched", ".walk" + "()", "datetime." + "UTC",
                 "typing." + "Self", "Exception" + "Group", "Task" + "Group", "contextlib." + "chdir",
                 "Str" + "Enum", "file_" + "digest"]
        newer = "|".join(re.escape(n) for n in names)
        for path in [*sorted((ROOT_DIR / "scripts").glob("*.py")), *sorted((ROOT_DIR / "tests").glob("*.py"))]:
            source = path.read_text(encoding="utf-8")
            with self.subTest(file=path.name):
                self.assertNotRegex(source, newer, f"{path.name} uses a standard-library API newer than 3.10")

    def test_scripts_follow_platform_parity(self):
        # R4, mechanically: no shell strings, no hardcoded interpreter names.
        for script in sorted((ROOT_DIR / "scripts").glob("*.py")):
            source = script.read_text(encoding="utf-8")
            with self.subTest(script=script.name):
                self.assertNotRegex(source, r"shell\s*=\s*True")
                self.assertNotRegex(source, r"\bos\.system\(")
                self.assertNotRegex(source, r"""\[\s*["'](?:python3?|py)["']""")


class TestPrinciple004Unambiguity(unittest.TestCase):
    """
    PRINCIPLE-004 must name where each kind of state is written and how it is read back, so no
    two models keep a plan or a decision in different places (or only in chat).
    """

    @classmethod
    def setUpClass(cls):
        cls.text = SSOT_MD.read_text(encoding="utf-8")
        cls.section = cls.text[cls.text.index("### PRINCIPLE-004:"):cls.text.index("\n### PRINCIPLE-005:")]
        cls.rules = cls.section[cls.section.index("- **Rules**:"):]

    def test_rules_contain_no_hedge_words(self):
        found = [h for h in TestPrinciple002Unambiguity.HEDGES
                 if h in self.section.lower() or h in self.section]
        self.assertEqual(found, [], f"PRINCIPLE-004 contains open-ended wording: {found}")
        self.assertNotIn("StartLine", self.section, "IDE-specific tool parameter names")

    def test_every_rule_names_its_audience(self):
        numbered = re.findall(r"^  (\d+)\. \*\*([^*]+)\*\*([^\n]*)", self.rules, re.M)
        self.assertEqual(len(numbered), 5, "PRINCIPLE-004 must keep rules R1-R5 (cited elsewhere)")
        for number, _, rest in numbered:
            with self.subTest(rule=f"R{number}"):
                self.assertRegex(rest, r"\*\[(Agent|Maintainer|Agent \+ Maintainer)\]\*")

    def test_every_kind_of_state_has_one_home(self):
        for definition in (
            "The plan is the `--desc` text of the task's latest `--phase-num 2` checkpoint",
            "whose `--desc` starts with `[1/`",
            "MUST record a new such checkpoint with the full revised plan",
            "MUST record the answer as the `--desc` of a checkpoint in the current phase before its next file edit",
            "MUST run `python scripts/disruption_recovery.py --resume` before any other action",
            "MUST NOT overwrite or discard them and MUST tell the user they exist",
            "search `knowledge/decisions.md` for the subject",
            "when records disagree the newest wins",
            "A user who changes a recorded decision is followed",
            "A *read* is any tool call or command that prints file contents",
            "One read MUST NOT print more than 100 lines of a file",
            "or is a user instruction the user says applies to future tasks or to the whole project",
            "A schema's fields are written only to `knowledge/data_models.md`",
            "MUST NOT put more than 100 lines into the conversation",
            "before the final message of its turn MUST be at most 15 lines, code blocks included",
            "Checklist timing is set by PRINCIPLE-001 R8",
        ):
            with self.subTest(definition=definition):
                self.assertIn(definition, self.rules)

    def test_no_second_resumption_procedure(self):
        # Red-green pin: R2 told agents to hand-inspect `active_phase` in the JSON while P002 R4
        # said to run --resume - two procedures for one event. R2 now defers to P002 R4.
        self.assertIn("`Recommended Resumption Phase` with the printed plan (PRINCIPLE-002 R4)", self.rules)
        self.assertNotIn("Inspect `.agents/task_ledger.json` for `active_task`", self.rules)

    def test_one_cold_start_command_everywhere(self):
        # Red-green pin (third pass): P002 R1 said `--audit` on a cold start, P006 R2 said
        # `--audit` or `--resume`, P004 R2 said `--resume` - three answers to one question.
        self.assertNotIn("`--audit` on a cold start", self.text)
        self.assertNotIn("`--audit` or `--resume`", self.text)
        self.assertIn("--resume` on a cold start per PRINCIPLE-004 R2", self.text)

    def test_fifteen_line_limit_has_one_owner(self):
        # Red-green pin: P004 allowed 15 lines ("within 15") while P012 R4 demanded "<15".
        p012 = self.text[self.text.index("### PRINCIPLE-012:"):self.text.index("\n### PRINCIPLE-013:")]
        self.assertNotIn("<15 lines", p012)
        self.assertIn("limited to 15 lines by PRINCIPLE-004 R5", p012)

    def test_no_unobservable_obligation(self):
        # Red-green pin: "the agent MUST know its current phase" cannot be checked by anyone.
        self.assertNotIn("MUST know", self.rules)

    def test_resume_never_says_ready_over_uncommitted_files(self):
        # Red-green pin: with no interrupted task, --resume printed only "Ready for a new task"
        # and hid the modified and untracked files that --audit showed.
        report = format_resume_report({"modified_files": ["a.py"], "untracked_files": ["b.py"]})
        self.assertIn("a.py", report)
        self.assertIn("b.py", report)
        self.assertNotIn("Ready for a new task", report)
        self.assertIn("Ready for a new task", format_resume_report({}))

    def test_report_file_lists_are_bounded(self):
        # Red-green pin: 500 untracked files printed 500 lines into the conversation (R5).
        report = format_audit_report({"untracked_files": [f"f{i}.py" for i in range(500)]})
        self.assertLessEqual(len(report.splitlines()), 30)
        self.assertIn("… and 480 more", report)

    def test_schemas_are_not_sent_to_adrs(self):
        # Red-green pin: R4 sent data schemas to decisions.md, contradicting PRINCIPLE-016 R5.
        self.assertNotIn("and data schemas immediately to `knowledge/decisions.md`", self.rules)
        p016 = self.text[self.text.index("### PRINCIPLE-016:"):self.text.index("\n### PRINCIPLE-017:")]
        self.assertIn("`data_models.md` is the sole Single Source of Truth for schemas", p016)

    def test_active_task_is_bounded_and_keeps_its_plan(self):
        # Red-green pin: the active task was exempt from the bound - 60 checkpoints kept vs 20.
        # prune_checkpoints is pure, so the bound is tested without 40 fsynced ledger writes.
        history = [{"task_id": "old", "phase_num": 5, "description": f"old {i}", "timestamp": i}
                   for i in range(10)]
        history.append({"task_id": "t", "phase_num": 2, "description": "[1/2] a; [2/2] b", "timestamp": 10})
        history += [{"task_id": "t", "phase_num": 3, "description": f"step {i}", "timestamp": 11 + i}
                    for i in range(40)]
        checkpoints = prune_checkpoints(history, active_task_id="t", max_history=20)
        self.assertLessEqual(len(checkpoints), 20)
        self.assertTrue(any(c["phase_num"] == 2 for c in checkpoints), "pruning dropped the plan")
        self.assertEqual(checkpoints[-1]["description"], "step 39", "pruning dropped the newest work")

    def test_parse_handoff_reads_the_declared_keys(self):
        packet, errors = parse_handoff(
            "state: milestones 1-3 landed; next: wire the CLI flag; "
            "failed: a schema bump breaks v1 ledgers; open: should --handoff be required?; "
            "evidence: 420 unit tests green")
        self.assertEqual(errors, [])
        self.assertEqual(packet["state"], "milestones 1-3 landed")
        self.assertEqual(packet["next"], "wire the CLI flag")
        self.assertEqual(packet["failed"], "a schema bump breaks v1 ledgers")
        self.assertEqual(packet["open"], "should --handoff be required?")
        self.assertEqual(packet["evidence"], "420 unit tests green")

    def test_parse_handoff_requires_next_and_refuses_an_unknown_key(self):
        _, errors = parse_handoff("state: halfway")
        self.assertEqual(errors, ["--handoff must give a 'next:' value: the one action that "
                                  "resumes this task"])
        _, errors = parse_handoff("next: go on; blockers: none")
        self.assertEqual(errors, ["--handoff does not know the key 'blockers'; it accepts "
                                  "state, next, failed, open, evidence"])

    def test_parse_handoff_is_bounded_and_ignores_empty_segments(self):
        _, errors = parse_handoff("next: " + "x" * 2100)
        self.assertEqual(errors, ["--handoff is 2106 characters; the limit is 2000 so a packet "
                                  "stays readable after a compaction"])
        packet, errors = parse_handoff("next: ship it;  ; ")
        self.assertEqual((packet, errors), ({"next": "ship it"}, []))

    def test_checkpoint_command_rejects_a_malformed_handoff_before_writing(self):
        workspace = Path(tempfile.mkdtemp(prefix="test_hoff_cli_"))
        self.addCleanup(shutil.rmtree, workspace, ignore_errors=True)
        ledger = workspace / ".agents" / "task_ledger.json"
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = checkpoint_command("t", "implementation", 3, "work", {}, ledger_file=ledger,
                                      handoff="state: halfway")
        self.assertEqual(code, 2, "a malformed --handoff is a usage error")
        self.assertIn("must give a 'next:' value", err.getvalue())
        self.assertFalse(ledger.exists(), "nothing is written when the packet is rejected")

    def test_checkpoint_command_scrubs_the_handoff_like_other_free_text(self):
        workspace = Path(tempfile.mkdtemp(prefix="test_hoff_sec_"))
        self.addCleanup(shutil.rmtree, workspace, ignore_errors=True)
        ledger = workspace / ".agents" / "task_ledger.json"
        leak = "next: rotate glpat\x2daB3dE5gH7jK9mN1pQ3rS"  # aikit:allow-secret
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = checkpoint_command("t", "implementation", 3, "w", {}, ledger_file=ledger,
                                      handoff=leak)
        self.assertEqual(code, 1, "the handoff is a credential surface like every other field")
        self.assertIn("GitLab personal access token", err.getvalue())
        with contextlib.redirect_stdout(io.StringIO()):
            code = checkpoint_command("t", "implementation", 3, "w", {}, ledger_file=ledger,
                                      handoff=leak, redact=True)
        self.assertEqual(code, 0)
        written = json.loads(ledger.read_text(encoding="utf-8"))
        self.assertEqual(written["checkpoints"][-1]["handoff"]["next"], "rotate [REDACTED]")

    def test_resume_prints_the_handoff_and_its_next_action(self):
        workspace = Path(tempfile.mkdtemp(prefix="test_hoff_res_"))
        self.addCleanup(shutil.rmtree, workspace, ignore_errors=True)
        ledger = workspace / ".agents" / "task_ledger.json"
        record_checkpoint("t", "planning", "[1/2] model; [2/2] cli", phase_num=2,
                          ledger_file=ledger)
        record_checkpoint("t", "implementation", "milestone 1 done", phase_num=3,
                          ledger_file=ledger,
                          handoff={"state": "model landed", "next": "wire the CLI flag",
                                   "failed": "a schema bump breaks v1 ledgers",
                                   "open": "should the flag be required?"})
        report = format_resume_report(run_disruption_audit(workspace, git_status=not_a_git_repo))
        self.assertIn("State: model landed", report)
        self.assertIn("Tried and rejected: a schema bump breaks v1 ledgers", report)
        self.assertIn("Open question: should the flag be required?", report)
        self.assertIn("Next Action: wire the CLI flag", report)
        self.assertNotIn("Inspect surviving files", report,
                         "a recorded next action replaces the generic line")
        self.assertLessEqual(len(report.splitlines()), 100, "PRINCIPLE-004 R5 output budget")

    def test_resume_keeps_the_generic_next_action_without_a_handoff(self):
        workspace = Path(tempfile.mkdtemp(prefix="test_hoff_gen_"))
        self.addCleanup(shutil.rmtree, workspace, ignore_errors=True)
        ledger = workspace / ".agents" / "task_ledger.json"
        record_checkpoint("t", "implementation", "work", phase_num=3, ledger_file=ledger)
        report = format_resume_report(run_disruption_audit(workspace, git_status=not_a_git_repo))
        self.assertIn("Inspect surviving files", report)

    def test_handoff_round_trips_through_a_version_1_ledger(self):
        # Additive by design: no schema bump, because validate_ledger_version refuses any version
        # that is not exactly current, so a bump would make every existing v1 ledger unreadable.
        workspace = Path(tempfile.mkdtemp(prefix="test_handoff_"))
        self.addCleanup(shutil.rmtree, workspace, ignore_errors=True)
        ledger = workspace / ".agents" / "task_ledger.json"
        record_checkpoint("t", "implementation", "milestone 2", phase_num=3, ledger_file=ledger,
                          handoff={"next": "wire the CLI", "failed": "a schema bump"})
        written = json.loads(ledger.read_text(encoding="utf-8"))
        self.assertEqual(written["version"], 1, "the handoff needs no schema version bump")
        self.assertEqual(written["checkpoints"][-1]["handoff"],
                         {"next": "wire the CLI", "failed": "a schema bump"})
        # A checkpoint without one carries no key at all, so old readers see an unchanged shape.
        record_checkpoint("t", "implementation", "milestone 3", phase_num=3, ledger_file=ledger)
        written = json.loads(ledger.read_text(encoding="utf-8"))
        self.assertNotIn("handoff", written["checkpoints"][-1])

    def test_parse_handoff_keeps_colons_inside_a_value(self):
        packet, errors = parse_handoff("next: run `aikit check app`: it gates the commit")
        self.assertEqual(errors, [])
        self.assertEqual(packet["next"], "run `aikit check app`: it gates the commit")

    def test_checkpoint_refuses_a_credential_in_free_text_unless_redacting(self):
        workspace = Path(tempfile.mkdtemp(prefix="test_cpsecret_"))
        self.addCleanup(shutil.rmtree, workspace, ignore_errors=True)
        ledger = workspace / ".agents" / "task_ledger.json"
        leak = "rotated glpat\x2daB3dE5gH7jK9mN1pQ3rS today"  # aikit:allow-secret
        impact = {"why": leak, "benefits": None, "risks": None, "mitigation": None}

        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            code = checkpoint_command("t", "implementation", 3, "work", impact,
                                      ledger_file=ledger)
        self.assertEqual(code, 1, "a credential in free text is an operational failure")
        self.assertIn("GitLab personal access token", err.getvalue())
        self.assertIn("--redact", err.getvalue())
        self.assertFalse(ledger.exists(), "the refusal happens before any write")

        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = checkpoint_command("t", "implementation", 3, "work", impact,
                                      ledger_file=ledger, redact=True)
        self.assertEqual(code, 0)
        written = json.loads(ledger.read_text(encoding="utf-8"))
        recorded = written["checkpoints"][-1]["impact_assessment"]["why"]
        self.assertNotIn("glpat\x2daB3dE5gH7jK9mN1pQ3rS", recorded)  # aikit:allow-secret
        self.assertIn("[REDACTED]", recorded)
        self.assertIn("rotated", recorded, "the surrounding prose survives")

    def test_checkpoint_scrubs_the_description_too(self):
        workspace = Path(tempfile.mkdtemp(prefix="test_cpdesc_"))
        self.addCleanup(shutil.rmtree, workspace, ignore_errors=True)
        ledger = workspace / ".agents" / "task_ledger.json"
        desc = "hit npm\x5faB3dE5gH7jK9mN1pQ3rS5tU7vW9xY1zA3bC5 in the log"  # aikit:allow-secret
        with contextlib.redirect_stdout(io.StringIO()):
            code = checkpoint_command("t", "implementation", 3, desc, {}, ledger_file=ledger,
                                      redact=True)
        self.assertEqual(code, 0)
        written = json.loads(ledger.read_text(encoding="utf-8"))
        self.assertIn("[REDACTED]", written["checkpoints"][-1]["description"])

    def test_resume_prints_the_plan(self):
        workspace = Path(tempfile.mkdtemp(prefix="test_plan_"))
        self.addCleanup(shutil.rmtree, workspace, ignore_errors=True)
        ledger = workspace / ".agents" / "task_ledger.json"
        record_checkpoint("t", "planning", "[1/2] model; [2/2] cli", phase_num=2, ledger_file=ledger)
        record_checkpoint("t", "implementation", "building", phase_num=3, ledger_file=ledger)
        report = format_resume_report(run_disruption_audit(workspace, git_status=not_a_git_repo))
        self.assertIn("Plan (Phase 2 checkpoint): [1/2] model; [2/2] cli", report)

    def test_revised_plan_replaces_the_old_one_and_answers_do_not(self):
        # Red-green pin (second R1 pass): the earliest Phase 2 checkpoint was returned, so a
        # revised plan never reached --resume, and any Phase 2 note could count as the plan.
        history = [
            {"task_id": "t", "phase_num": 2, "description": "[1/2] model; [2/2] cli"},
            {"task_id": "t", "phase_num": 2, "description": "[1/3] model; [2/3] service; [3/3] cli"},
            {"task_id": "t", "phase_num": 2, "description": "User chose option 2: keep JSON"},
            {"task_id": "t", "phase_num": 3, "description": "[1/3] done"},
        ]
        self.assertEqual(task_plan_checkpoint(history)["description"],
                         "[1/3] model; [2/3] service; [3/3] cli")
        self.assertIsNone(task_plan_checkpoint(history[2:3]))

    def test_cli_never_replaces_a_missing_value_with_a_default(self):
        # Red-green pin: `--checkpoint --task-id x` recorded task 'task' and printed [OK];
        # `--complete` with no id completed nothing and printed [OK].
        self.assertEqual(validate_argv(["--checkpoint", "--task-id", "x"]), ["--task-id"])
        self.assertEqual(argv_value_errors(["--complete"]), ["--complete requires a value"])
        self.assertEqual(argv_value_errors(["--checkpoint", "t", "--phase-num", "six"]),
                         ["--phase-num must be 1-5, got 'six'"])
        self.assertEqual(argv_value_errors(["--reset"]), [])  # its reason is optional
        self.assertEqual(argv_value_errors(["--checkpoint", "t", "--phase-num", "2", "--desc", "d"]), [])

    def test_completing_a_task_that_is_not_active_changes_nothing(self):
        workspace = Path(tempfile.mkdtemp(prefix="test_complete_"))
        self.addCleanup(shutil.rmtree, workspace, ignore_errors=True)
        ledger = workspace / ".agents" / "task_ledger.json"
        record_checkpoint("real", "implementation", "x", phase_num=3, ledger_file=ledger)
        self.assertFalse(mark_task_completed("typo", ledger_file=ledger))
        after = load_ledger(ledger)
        self.assertEqual(after["active_task"]["status"], "in_progress")
        self.assertEqual(len(after["checkpoints"]), 1)
        self.assertTrue(mark_task_completed("real", ledger_file=ledger))


class TestLifecycleToolSemantics(unittest.TestCase):
    """
    PRINCIPLE-002 delegates decisions to commands; each command must mean what the rule says.
    These pins come from running P002's commands literally (ADR-055).
    """

    def test_bare_digit_phase_is_that_phase(self):
        # PRINCIPLE-007 R6 documents `--phase 2`; it used to be recorded as Phase 1.
        for digit in "12345":
            with self.subTest(phase=digit):
                self.assertEqual(resolve_phase_num(digit), int(digit))
        self.assertEqual(resolve_phase_num("planning"), 2)

    def test_resume_stays_in_the_recorded_phase_on_a_clean_tree(self):
        # R4 records phases on ENTRY. After a PRINCIPLE-006 milestone commit during Phase 3 the
        # tree is clean, and resume used to recommend Phase 4, skipping the remaining milestones.
        for dirty in (False, True):
            with self.subTest(uncommitted=dirty):
                report = format_resume_report({
                    "interrupted_task": {"task_id": "t", "active_phase": 3, "last_phase": "build",
                                         "status": "in_progress"},
                    "has_uncommitted_changes": dirty,
                })
                self.assertIn("Recommended Resumption Phase: Phase 3", report)

    def test_audit_ignores_the_ledger(self):
        # The ledger is bookkeeping; counting it made every checkpointed task look disrupted.
        root = Path(tempfile.mkdtemp(prefix="test_bookkeeping_"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        audit = run_disruption_audit(
            root,
            git_status=lambda ws: (0, " M .agents/task_ledger.json\n?? notes.md\n", ""),
        )
        self.assertEqual(audit["modified_files"], [])
        self.assertEqual(audit["untracked_files"], ["notes.md"])

    def test_p002_names_one_resume_line_and_defines_cold_start(self):
        text = SSOT_MD.read_text(encoding="utf-8")
        p002 = text[text.index("### PRINCIPLE-002:"):text.index("\n### PRINCIPLE-003:")]
        self.assertIn("`Recommended Resumption Phase` line", p002)
        self.assertIn("A recorded phase means the phase was entered, not finished", p002)
        self.assertIn("a cold start is the first turn of a session", p002)
        self.assertIn("not rule files", p002, "capsule must not imply rule-file edits are Track B")

    def test_caches_never_leak_or_go_stale(self):
        # Both parse caches are keyed on file content and hand out copies (PRINCIPLE-014 R4).
        first = parse_principles(SSOT_MD)
        first[0]["invariant"] = "MUTATED"
        self.assertNotEqual(parse_principles(SSOT_MD)[0]["invariant"], "MUTATED")
        doc = Path(tempfile.mkdtemp(prefix="test_cache_")) / "m.py"
        self.addCleanup(shutil.rmtree, doc.parent, ignore_errors=True)
        doc.write_text('"""A."""\ndef one():\n    pass\n', encoding="utf-8")
        symbols = extract_python_symbols(doc)
        symbols["functions"].clear()
        self.assertEqual([f["name"] for f in extract_python_symbols(doc)["functions"]], ["one"])
        doc.write_text('"""A."""\ndef two():\n    pass\n', encoding="utf-8")
        self.assertEqual([f["name"] for f in extract_python_symbols(doc)["functions"]], ["two"])

    def test_every_command_in_the_rules_exists(self):
        # Executable command parity for rule text (PRINCIPLE-005 R3): each quoted script exists and
        # each flag it is given is one that script declares.
        text = SSOT_MD.read_text(encoding="utf-8")
        commands = re.findall(r"`((?:python |py )?scripts/\w+\.py[^`]*)`", text)
        self.assertGreater(len(commands), 10)
        for cmd in commands:
            script = ROOT_DIR / "scripts" / re.search(r"scripts/(\w+\.py)", cmd).group(1)
            with self.subTest(command=cmd):
                self.assertTrue(script.exists(), f"rule cites a missing script: {cmd}")
                source = script.read_text(encoding="utf-8")
                for flag in re.findall(r"(?<![\w-])(--[a-z][a-z-]*)", cmd):
                    self.assertIn(f'"{flag}"', source, f"rule cites unknown flag {flag}: {cmd}")


class TestTrackClassification(unittest.TestCase):
    """PRINCIPLE-002 R3: the track is computed, so every model assigns the same one."""

    CODE = "def f(x):\n    return x + 1\n"

    def test_no_changes_is_track_a(self):
        self.assertEqual(classify_track([]), ("A", []))

    def test_documentation_is_track_b(self):
        self.assertEqual(classify_track([("README.md", "a", "b"), ("docs/x.txt", None, "new")])[0], "B")

    def test_comment_and_docstring_edits_are_track_b(self):
        edited = '# a comment\ndef f(x):\n    """Docstring."""\n    return x + 1  # inline\n'
        self.assertEqual(classify_track([("m.py", self.CODE, edited)])[0], "B")

    def test_logic_change_is_track_c(self):
        self.assertEqual(classify_track([("m.py", self.CODE, self.CODE.replace("+ 1", "+ 2"))])[0], "C")

    def test_rule_text_and_generated_files_are_track_c(self):
        for path in ("GUIDELINES.md", "CLAUDE.md", "AGENTS.md", ".agents/rules/domain.md"):
            with self.subTest(path=path):
                self.assertEqual(classify_track([(path, "a", "b")])[0], "C")

    def test_config_tests_and_new_python_are_track_c(self):
        for change in ((".github/workflows/ci.yml", "a", "b"), ("tests/test_x.py", None, self.CODE),
                       ("old.py", self.CODE, None), ("bad.py", self.CODE, "def (:\n")):
            with self.subTest(path=change[0]):
                self.assertEqual(classify_track([change])[0], "C")

    def test_unplanned_files_criterion_is_gone(self):
        # "a file outside the Phase 2 plan" was uncheckable (and meaningless on Track B).
        section = SSOT_MD.read_text(encoding="utf-8")
        self.assertNotIn("outside the Phase 2 plan", section)

    def test_highest_track_wins(self):
        self.assertEqual(classify_track([("README.md", "a", "b"), ("m.py", self.CODE, "x = 1\n")])[0], "C")

    def test_rename_source_is_classified_with_the_new_path(self):
        # ADR-163: a rename from code to docs deletes Python; classifying only the new path lost it.
        from scripts.disruption_recovery import collect_working_changes
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("x = 1\n", encoding="utf-8")

            def run(argv, **kwargs):
                if argv[1] == "status":
                    return subprocess.CompletedProcess(argv, 0, "R  README.md\0code.py\0", "")
                if argv[1] == "show" and argv[-1] == "HEAD:code.py":
                    return subprocess.CompletedProcess(argv, 0, "x = 1\n", "")
                return subprocess.CompletedProcess(argv, 128, "", "not found")

            with mock.patch("scripts.disruption_recovery.subprocess.run", side_effect=run):
                changes = collect_working_changes(root)
        self.assertEqual([change[0] for change in changes], ["README.md", "code.py"])
        self.assertEqual(classify_track(changes)[0], "C")


class TestSyncWriteSafety(unittest.TestCase):
    """
    ADR-048. Sync now writes AGENTS.md, which older layouts used as the hand-authored rule source,
    and adopters often keep their own CLAUDE.md. Sync must therefore never overwrite a file it did
    not generate, must decide that for every target before writing any, and must explain an
    unmigrated layout instead of crashing. Each test runs the real sync_all in a sandbox.
    """

    def setUp(self):
        # These tests verify WHICH files sync writes, not power-loss durability (covered by the
        # PRINCIPLE-013 tests), so fsync is a no-op here. RAII-restored (PRINCIPLE-014 R4).
        self.addCleanup(setattr, os, "fsync", os.fsync)
        os.fsync = lambda fd: None
        self.sandbox = Path(tempfile.mkdtemp(prefix="test_sync_safety_"))
        self.addCleanup(shutil.rmtree, self.sandbox, ignore_errors=True)
        # Sync only READS its sources, so the real GUIDELINES.md and README.md are used in place;
        # copying them cost two slow file creations per test (~3.4ms each on Windows). Every
        # file sync WRITES still lands in the sandbox, because ROOT_DIR points there.
        for name, value in (
            ("ROOT_DIR", self.sandbox),
            ("SSOT_MD", SSOT_MD),
            ("AGENTS_MD", self.sandbox / "AGENTS.md"),
            ("DOMAIN_RULES_PATH", self.sandbox / ".agents" / "rules" / "domain.md"),
        ):
            self.addCleanup(setattr, sync_principles_module, name, getattr(sync_principles_module, name))
            setattr(sync_principles_module, name, value)

    def _sync(self, check_only=False):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            result = sync_principles_module.sync_all(
                check_only=check_only, exit_on_mismatch=False, readme_file=README_MD
            )
        return result, out.getvalue()

    def _written_targets(self):
        return [rel for rel in TIER1_TARGETS if (self.sandbox / rel).exists()]

    def test_oversized_domain_rules_report_the_triad(self):
        # Red-green pin (ADR-108): a domain.md over the limit ended sync in a raw traceback.
        domain = self.sandbox / "domain.md"
        domain.write_text("x" * (MAX_DOMAIN_CHARS + 1), encoding="utf-8")
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            result = sync_principles_module.sync_all(check_only=True, exit_on_mismatch=False,
                                                     readme_file=README_MD, domain_path=domain)
        self.assertEqual(result, 1)
        self.assertIn("[DOMAIN RULES TOO LONG]", err.getvalue())
        self.assertIn("Fix:", err.getvalue())

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
        sync_principles_module.SSOT_MD = self.sandbox / "GUIDELINES.md"  # restored by setUp cleanup
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
                self.assertIn("### PRINCIPLE-NNN:", content,
                              f"{target.name} lost the deterministic grep anchor contract")
                self.assertIn("GUIDELINES.md", content,
                              f"{target.name} no longer points at Tier 2 knowledge")

    def test_capsules_retain_their_mechanisms_after_condensation(self):
        # PRINCIPLE-001 R2: compression targets narrative, never hard mechanical constraints.
        content = (ROOT_DIR / ".agents" / "rules" / "principles.md").read_text(encoding="utf-8")
        for mechanism in ("os.replace", "fsync", "100% test pass gate", "<=10ms",
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

    def test_findings_never_echo_the_secret(self):
        # Red-green pin (ADR-110): the scanner printed each caught credential in full (P019 R4).
        lines = {
            'AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7NOTREAL"': "AKIAIOSFODNN7NOTREAL",  # aikit:allow-secret
            'token_value = "q8Zx3LmP0vR7tK2wY9nB4cH6jF1dS5aE"': "q8Zx3LmP0vR7tK2wY9nB4cH6jF1dS5aE",  # aikit:allow-secret
        }
        for line, secret in lines.items():
            with self.subTest(line=line):
                findings = scan_text("fixture.py", line)
                self.assertEqual(len(findings), 1)
                self.assertNotIn(secret, findings[0][3])
                self.assertIn(secret[:4] + "***", findings[0][3])

    def test_detects_the_widened_prefixed_credential_shapes(self):
        cases = {
            "GitLab personal access token": 'k = "glpat\x2daB3dE5gH7jK9mN1pQ3rS"',  # aikit:allow-secret
            "npm access token": 'k = "npm\x5faB3dE5gH7jK9mN1pQ3rS5tU7vW9xY1zA3bC5"',  # aikit:allow-secret
            "PyPI upload token": 'k = "pypi\x2dAgEIcHlwaS5vcmcaB3dE5gH7jK9mN1pQ3rS5tU7vW9xY1zA3bC5dF7gJ9kL1mP3qR"',  # aikit:allow-secret
            "SendGrid API key": 'k = "SG\x2eaB3dE5gH7jK9mN1pQ3rS5t.aB3dE5gH7jK9mN1pQ3rS5tU7vW9xY1zA3bC5dF7gJ9k"',  # aikit:allow-secret
            "Hugging Face token": 'k = "hf\x5faB3dE5gH7jK9mN1pQ3rS5tU7vW9xY1zA3b"',  # aikit:allow-secret
            "Google OAuth client secret": 'k = "GOCSPX\x2daB3dE5gH7jK9mN1pQ3rS5tU7vW9x"',  # aikit:allow-secret
            "Mailgun API key": 'k = "key\x2da1b2c3d4a1b2c3d4a1b2c3d4a1b2c3d4"',  # aikit:allow-secret
            "Telegram bot token": 'k = "123456789\x3aAAaB3dE5gH7jK9mN1pQ3rS5tU7vW9xY1zA3"',  # aikit:allow-secret
            "Docker Hub access token": 'k = "dckr_pat\x5faB3dE5gH7jK9mN1pQ3rS5t"',  # aikit:allow-secret
            "Notion integration token": 'k = "secret\x5faB3dE5gH7jK9mN1pQ3rS5tU7vW9xY1zA3bC5dF7gJ9k"',  # aikit:allow-secret
            "Linear API key": 'k = "lin_api\x5faB3dE5gH7jK9mN1pQ3rS5tU7vW9xY1zA3bC5dF7g"',  # aikit:allow-secret
            "Slack incoming webhook": 'u = "https\x3a//hooks.slack.com/services/T00000000/B00000000/aB3dE5gH7jK9mN1pQ3rS5tU7"',  # aikit:allow-secret
            "Azure storage account key": 'c = "AccountKey\x3daB3dE5gH7jK9mN1pQ3rS5tU7vW9xY1zA3bC5dF7gJ9kL1mP3qR5sT7uV9wX1=="',  # aikit:allow-secret
            "Private key block": "-----BEGIN ENCRYPTED PRIVATE KEY\x2d----",  # aikit:allow-secret
        }
        for detector, line in cases.items():
            with self.subTest(detector=detector):
                findings = scan_text("fixture.py", line)
                self.assertEqual([f[2] for f in findings], [detector])

    def test_scrub_text_replaces_every_credential_and_names_the_detectors(self):
        text = ('note: deploy used glpat\x2daB3dE5gH7jK9mN1pQ3rS\n'  # aikit:allow-secret
                'and npm\x5faB3dE5gH7jK9mN1pQ3rS5tU7vW9xY1zA3bC5 for the registry\n'  # aikit:allow-secret
                'commit e6e708b1e499c95f33a033f3f9c4e54f01a68231 is unaffected\n')
        scrubbed, detectors = scrub_text(text)
        self.assertEqual(sorted(detectors),
                         ["GitLab personal access token", "npm access token"])
        self.assertNotIn("glpat\x2daB3dE5gH7jK9mN1pQ3rS", scrubbed)  # aikit:allow-secret
        self.assertNotIn("npm\x5faB3dE5gH7jK9mN1pQ3rS", scrubbed)  # aikit:allow-secret
        self.assertIn("e6e708b1e499c95f33a033f3f9c4e54f01a68231", scrubbed,
                      "a commit hash in prose is not a credential")
        self.assertIn("note: deploy used", scrubbed)
        # A scrubbed field must be clean on rescan, or the gate would fail on its own output.
        self.assertEqual(scan_text("scrubbed", scrubbed), [])

    def test_subagent_answer_text_scrubs_credentials_from_the_stream(self):
        # A sub-agent's answer reaches the lead agent's context and any log downstream of it;
        # there is no reason to want a leaked key verbatim, so this needs no opt-in.
        leak = "use hf\x5faB3dE5gH7jK9mN1pQ3rS5tU7vW9xY1zA3b for the model"  # aikit:allow-secret
        stream = "\n".join(json.dumps({"type": "text", "part": {"text": chunk}})
                           for chunk in ("checked the config, ", leak))
        answer = answer_text(stream)
        self.assertNotIn("hf\x5faB3dE5gH7jK9mN1pQ3rS", answer)  # aikit:allow-secret
        self.assertIn("[REDACTED]", answer)
        self.assertIn("checked the config", answer)

    def test_subagent_answer_text_leaves_clean_output_unchanged(self):
        stream = json.dumps({"type": "text", "part": {"text": "all three gates pass"}})
        self.assertEqual(answer_text(stream), "all three gates pass")

    def test_scrub_text_leaves_clean_prose_byte_identical(self):
        prose = "Risks: contract: --checkpoint gains a refusal path; state: no schema change."
        self.assertEqual(scrub_text(prose), (prose, []))

    def test_prose_keeps_its_digests_and_identifiers(self):
        # The widened table must not cost the near-zero false-positive property the gate's
        # trust rests on: a risk note citing a commit or a digest has to stay clean.
        prose = [
            "Risks: state: the fingerprint changed from e6e708b1e499c95f33a033f3f9c4e54f01a68231.",
            "The surface digest is sha256:9f2b7c4e1a8d3f6b5c0e7a2d4f8b1c3e5a7d9f0b2c4e6a8d.",
            "Benefits: ADR-171 records all nine decisions; see knowledge/decisions.md.",
            "secret_key_rotation is scheduled; no value is quoted here.",
        ]
        for line in prose:
            with self.subTest(line=line[:40]):
                self.assertEqual(scan_text("note.md", line), [])

    def test_a_scan_that_skipped_a_surface_never_reports_clean(self):
        # Red-green pin (PRINCIPLE-000 R5): with git failing, --staged and --all printed [OK] and
        # exited 0 having scanned nothing, so the pre-commit gate passed blind. git_output is
        # replaced, so no process is spawned.
        import scripts.check_secrets as secrets_module
        original = secrets_module.git_output
        secrets_module.git_output = lambda args, repo=None: None
        self.addCleanup(setattr, secrets_module, "git_output", original)
        for mode in ("staged", "all"):
            with self.subTest(mode=mode), contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(run_scan(mode=mode), 1)
                self.assertIn("[FAIL] Scan incomplete", out.getvalue())
                self.assertNotIn("[OK]", out.getvalue())

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

    def test_rule_and_doc_files_are_scanned_except_the_scanner_itself(self):
        # ADR-163: a credential pasted into a rule or doc file is still a credential.
        from scripts.check_secrets import should_skip
        for filename in (".windsurfrules", ".clinerules", "AGENTS.md", "GEMINI.md",
                         "GUIDELINES.md", "README.md", "knowledge/decisions.md"):
            with self.subTest(filename=filename):
                self.assertFalse(should_skip(filename))
        self.assertTrue(should_skip("scripts/check_secrets.py"))

    def test_all_scan_includes_the_scanner_file(self):
        # The file is skipped in commit-diff mode, but --all must still scan its own code; its two
        # detector examples carry line pragmas.
        from scripts.check_secrets import scan_all
        root = Path(tempfile.mkdtemp(prefix="test_scanner_self_"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        (root / "scripts").mkdir()
        shutil.copyfile(ROOT_DIR / "scripts" / "check_secrets.py",
                        root / "scripts" / "check_secrets.py")
        with mock.patch("scripts.check_secrets.git_output",
                        return_value="scripts/check_secrets.py\n"):
            findings = scan_all(repo=root)
        self.assertEqual(findings, [])



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

    def test_detects_self_recursive_function_with_no_external_callers(self):
        # A function calling itself recursively but having zero external callers is unreachable
        files = self._write("mod_recur.py", '''"""Recursion."""
def dead_recursive(n):
    if n <= 0:
        return 0
    return dead_recursive(n - 1)

def main():
    return 42

if __name__ == "__main__":
    main()
''')
        unreachable = [name for name, _ in find_unreachable(files)]
        self.assertIn("dead_recursive", unreachable)
        self.assertNotIn("main", unreachable)


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

    def test_a_key_produced_only_by_setdefault_is_not_flagged(self):
        # `setdefault("k", v)` creates "k" when it is missing, so it is a producer as well as a
        # read; counting it only as a read flagged a key whose sole writer is setdefault.
        files = self._write("mod_e.py", '''"""Setdefault producer."""
def record(ledger, entry):
    ledger.setdefault("history", []).append(entry)

def report(ledger):
    return ledger.get("history", [])
''')
        phantom = [key for key, _ in find_phantom_keys(files)]
        self.assertNotIn("history", phantom, "setdefault produced this key")

    def test_a_producer_hidden_in_a_comprehension_is_flagged(self):
        # Pins the strict behaviour. A deleted fallback's comment promised to excuse any key that
        # appears more than once as a string literal; that would pass this module, whose only
        # producer hides every key inside a comprehension - the exact defect this shield caught in
        # the ADR-174 handoff work. The fix is to write the keys literally, never to relax this.
        files = self._write("mod_d.py", '''"""Hidden producer."""
KEYS = ("state", "next")

def write(h):
    return {key: h[key] for key in KEYS if h.get(key)}

def read(packet):
    if "next" not in packet:
        return None
    return packet.get("next")
''')
        phantom = [key for key, _ in find_phantom_keys(files)]
        self.assertIn("next", phantom,
                      "a key that is only ever written through a comprehension has no visible "
                      "producer; counting its literal mentions must not excuse it")

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
        # These tests check ledger content, never power-loss durability, which no unit test can
        # observe; real fsyncs (~3ms each on Windows) pushed the unit tier to 0.95s of its 1s
        # limit. RAII-restored (PRINCIPLE-014 R4), as in TestSyncWriteSafety.
        self.addCleanup(setattr, os, "fsync", os.fsync)
        os.fsync = lambda fd: None

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
            # longer wall-clock wait only inflates the unit tier's per-test budget (PRINCIPLE-014 R3).
            with file_lock(test_file, timeout_seconds=0.005, poll_interval=0.001) as acquired2:
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

    def test_a_full_disk_refuses_the_write_and_keeps_the_old_state(self):
        # ADR-148: the only disk-space test called check_disk_headroom() and asserted its boolean.
        # Nothing drove a write under a full disk, so the refusal path itself was never exercised.
        kept = {"version": 1, "active_task": {"task_id": "kept"}, "checkpoints": []}
        atomic_write_json(self.ledger_file, kept)
        before = self.ledger_file.read_bytes()
        full = shutil.disk_usage(self.test_dir)._replace(free=1024)  # 1 KiB, under the 10MB floor
        warning = io.StringIO()
        with mock.patch("scripts.disruption_recovery.shutil.disk_usage", return_value=full), \
                contextlib.redirect_stderr(warning):
            with self.assertRaises(OSError) as caught:
                atomic_write_json(self.ledger_file, {"version": 1, "active_task": {"task_id": "new"},
                                                     "checkpoints": []})
        self.assertEqual(caught.exception.errno, 28, "a full disk raises ENOSPC")
        self.assertIn("headroom", warning.getvalue().lower())
        self.assertEqual(self.ledger_file.read_bytes(), before, "the previous state survives")
        self.assertEqual(list(self.test_dir.glob("*.tmp_*")), [], "no partial buffer is left")
        # PRINCIPLE-011 R6: the CLI turns that refusal into the triad rather than a traceback.
        triad = io.StringIO()
        with contextlib.redirect_stderr(triad):
            report_operational_error(OSError, caught.exception, None)
        for part in ("Why:", "Fix:"):
            self.assertIn(part, triad.getvalue())

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

    def test_newer_ledger_is_refused_without_mutation(self):
        payload = {"version": 2, "active_task": {"task_id": "future"}, "checkpoints": []}
        self.ledger_file.write_text(json.dumps(payload), encoding="utf-8")
        before = self.ledger_file.read_bytes()
        with self.assertRaises(UnsupportedLedgerVersion):
            load_ledger(self.ledger_file)
        self.assertEqual(self.ledger_file.read_bytes(), before)
        self.assertEqual(list(self.test_dir.glob("*.corrupt_*")), [])
        self.assertEqual(list(self.test_dir.glob("*.tmp_*")), [])
        self.assertEqual(list(self.test_dir.glob("*.lock")), [])

    def test_newer_backup_is_not_used_when_primary_is_missing(self):
        backup = self.ledger_file.with_suffix(self.ledger_file.suffix + ".bak")
        backup.write_text(json.dumps({"version": 2, "active_task": {"task_id": "future"}}),
                          encoding="utf-8")
        before = backup.read_bytes()
        with self.assertRaises(UnsupportedLedgerVersion):
            load_ledger(self.ledger_file)
        self.assertEqual(backup.read_bytes(), before)
        self.assertFalse(self.ledger_file.exists())

    def test_legacy_ledger_is_migrated_in_memory_only(self):
        self.ledger_file.write_text(
            json.dumps({"active_task": {"task_id": "legacy"}, "checkpoints": []}),
            encoding="utf-8",
        )
        before = self.ledger_file.read_bytes()
        loaded = load_ledger(self.ledger_file)
        self.assertEqual(loaded["version"], LEDGER_SCHEMA_VERSION)
        self.assertEqual(loaded["active_task"]["task_id"], "legacy")
        self.assertEqual(self.ledger_file.read_bytes(), before)

    def test_invalid_ledger_versions_are_refused(self):
        for version in (True, "2", 2.0, 0, -1):
            with self.subTest(version=version):
                payload = {"version": version, "active_task": None, "checkpoints": []}
                self.ledger_file.write_text(json.dumps(payload), encoding="utf-8")
                before = self.ledger_file.read_bytes()
                with self.assertRaises(UnsupportedLedgerVersion):
                    load_ledger(self.ledger_file)
                self.assertEqual(self.ledger_file.read_bytes(), before)

    def test_a_later_build_reads_and_upgrades_an_older_valid_ledger(self):
        # Every ledger in existence is version 1 (27 of them when ADR-178 was written). A build
        # with a higher schema version used to refuse all of them, because the check was `!=`
        # rather than "newer", and migrate_ledger_schema never ran.
        payload = {"version": 1, "active_task": {"task_id": "old"}, "checkpoints": []}
        self.ledger_file.write_text(json.dumps(payload), encoding="utf-8")
        before = self.ledger_file.read_bytes()
        with mock.patch("scripts.disruption_recovery.LEDGER_SCHEMA_VERSION", 2):
            loaded = load_ledger(self.ledger_file)
        self.assertEqual(loaded["version"], 2, "the older ledger is upgraded in memory")
        self.assertEqual(loaded["active_task"]["task_id"], "old")
        self.assertEqual(self.ledger_file.read_bytes(), before, "loading never rewrites the file")

    def test_a_later_build_writes_an_older_valid_ledger_as_current(self):
        with mock.patch("scripts.disruption_recovery.LEDGER_SCHEMA_VERSION", 2):
            save_ledger({"version": 1, "active_task": None, "checkpoints": []}, self.ledger_file)
        self.assertEqual(json.loads(self.ledger_file.read_text(encoding="utf-8"))["version"], 2)

    def test_a_later_build_still_refuses_invalid_and_newer_versions(self):
        with mock.patch("scripts.disruption_recovery.LEDGER_SCHEMA_VERSION", 2):
            for version in (0, -1, 3, True, "1", 1.0):
                with self.subTest(version=version):
                    payload = {"version": version, "active_task": None, "checkpoints": []}
                    self.ledger_file.write_text(json.dumps(payload), encoding="utf-8")
                    before = self.ledger_file.read_bytes()
                    with self.assertRaises(UnsupportedLedgerVersion):
                        load_ledger(self.ledger_file)
                    self.assertEqual(self.ledger_file.read_bytes(), before)
                    with self.assertRaises(UnsupportedLedgerVersion):
                        save_ledger(dict(payload), self.ledger_file.with_name("w.json"))

    def test_refusal_names_the_versions_this_build_reads(self):
        # ADR-178 made a build read every version from 1 to its own, so a message naming only the
        # current version would tell a user their valid older ledger cannot be used.
        today = str(UnsupportedLedgerVersion(self.ledger_file, 7, 1))
        self.assertIn("this AIKit reads version 1\n", today, "text is unchanged while only 1 exists")
        self.assertIn("schema version 1;", today)
        with mock.patch("scripts.disruption_recovery.LEDGER_SCHEMA_VERSION", 2):
            payload = {"version": 3, "active_task": None, "checkpoints": []}
            self.ledger_file.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(UnsupportedLedgerVersion) as caught:
                load_ledger(self.ledger_file)
        message = str(caught.exception)
        self.assertIn("this AIKit reads versions 1 to 2", message)
        self.assertIn("schema versions 1 to 2", message)

    def test_an_invalid_version_is_not_blamed_on_a_different_aikit(self):
        # 0, -1, True, "2" and 2.0 are not schema versions any AIKit writes; blaming "a different
        # AIKit" sent the user looking for a build that does not exist.
        for found in (0, -1, True, "2", 2.0):
            with self.subTest(found=found):
                error = UnsupportedLedgerVersion(self.ledger_file, found, 1)
                self.assertIn("not a schema version", error.why)
                self.assertNotIn("different AIKit", error.why)
                self.assertIn(".bak", error.fix)
                self.assertIn("the file was not modified", error.fix)
        newer = UnsupportedLedgerVersion(self.ledger_file, 2, 1)
        self.assertIn("written by a different AIKit", newer.why, "a newer version keeps its text")
        self.assertIn("open it with the AIKit version that wrote it", newer.fix)

    def test_resume_report_blocks_a_newer_ledger(self):
        workspace = self.test_dir / "workspace"
        (workspace / ".agents").mkdir(parents=True)
        (workspace / ".agents" / "task_ledger.json").write_text(
            json.dumps({"version": 2, "active_task": {"task_id": "future"}}),
            encoding="utf-8",
        )
        audit = run_disruption_audit(workspace_dir=workspace, git_status=not_a_git_repo)
        self.assertIsNotNone(audit["ledger_error"])
        report = format_resume_report(audit)
        self.assertIn("BLOCKED", report)
        self.assertIn("schema version 2", report)
        self.assertNotIn("Ready for a new task", report)

    def test_save_refuses_a_newer_ledger_on_disk(self):
        payload = {"version": 2, "active_task": {"task_id": "future"}, "checkpoints": []}
        self.ledger_file.write_text(json.dumps(payload), encoding="utf-8")
        before = self.ledger_file.read_bytes()
        with self.assertRaises(UnsupportedLedgerVersion):
            save_ledger({"version": 1, "active_task": None, "checkpoints": []},
                        ledger_file=self.ledger_file)
        self.assertEqual(self.ledger_file.read_bytes(), before)

    def test_save_refuses_a_newer_backup(self):
        atomic_write_json(self.ledger_file,
                          {"version": 1, "active_task": {"task_id": "old"}, "checkpoints": []})
        backup = self.ledger_file.with_suffix(self.ledger_file.suffix + ".bak")
        backup.write_text(json.dumps({"version": 2, "active_task": {"task_id": "future"},
                                      "checkpoints": []}), encoding="utf-8")
        before_primary = self.ledger_file.read_bytes()
        before_backup = backup.read_bytes()
        with self.assertRaises(UnsupportedLedgerVersion):
            save_ledger({"version": 1, "active_task": {"task_id": "new"}, "checkpoints": []},
                        ledger_file=self.ledger_file)
        self.assertEqual(self.ledger_file.read_bytes(), before_primary)
        self.assertEqual(backup.read_bytes(), before_backup)

    def test_save_refuses_an_unreadable_ledger_instead_of_overwriting_it(self):
        payload = {"version": 1, "active_task": {"task_id": "old"}, "checkpoints": []}
        self.ledger_file.write_text(json.dumps(payload), encoding="utf-8")
        before = self.ledger_file.read_bytes()
        real_open = open

        def guarded(path, *args, **kwargs):
            if Path(path) == self.ledger_file:
                raise PermissionError("ledger is unreadable")
            return real_open(path, *args, **kwargs)

        with mock.patch("builtins.open", side_effect=guarded):
            with self.assertRaises(PermissionError):
                save_ledger({"version": 1, "active_task": {"task_id": "new"}, "checkpoints": []},
                            ledger_file=self.ledger_file, _locked=True)
        self.assertEqual(self.ledger_file.read_bytes(), before)

    def test_save_does_not_write_after_lock_timeout(self):
        with mock.patch("scripts.disruption_recovery.file_lock",
                        return_value=contextlib.nullcontext(False)):
            with self.assertRaises(TimeoutError):
                save_ledger({"version": 1, "active_task": None, "checkpoints": []},
                            ledger_file=self.ledger_file)
        self.assertFalse(self.ledger_file.exists())

    def test_noop_completion_does_not_rewrite_the_ledger(self):
        atomic_write_json(self.ledger_file,
                          {"version": 1, "active_task": {"task_id": "active",
                                                         "status": "in_progress"},
                           "checkpoints": []})
        with mock.patch("scripts.disruption_recovery.atomic_write_json") as write:
            self.assertFalse(mark_task_completed("other", ledger_file=self.ledger_file))
        write.assert_not_called()

    def test_an_io_error_is_reported_not_quarantined(self):
        # ADR-146: a locked or permission-denied ledger is valid data this process cannot read.
        # Quarantining it renamed a healthy file and started an empty ledger, losing the task.
        atomic_write_json(self.ledger_file, {"version": 1, "active_task": {"task_id": "live"},
                                             "checkpoints": []})
        before = self.ledger_file.read_bytes()
        with mock.patch("scripts.disruption_recovery._read_ledger_file",
                        side_effect=PermissionError(13, "locked by another process")):
            with self.assertRaises(OSError):
                load_ledger(self.ledger_file)
        self.assertEqual(self.ledger_file.read_bytes(), before, "the file is left untouched")
        self.assertEqual(list(self.test_dir.glob("*.corrupt_*")), [], "nothing was quarantined")

    def test_corruption_is_still_quarantined_and_recovered(self):
        # The companion case: malformed content is corruption, so the .bak path still runs.
        # Written twice: the first write creates the file, the second rotates it into the .bak
        # that recovery reads (atomic_write_json only rotates a file that already exists).
        saved = {"version": 1, "active_task": {"task_id": "saved"}, "checkpoints": []}
        atomic_write_json(self.ledger_file, saved)
        atomic_write_json(self.ledger_file, saved)
        self.ledger_file.write_text("{ not json", encoding="utf-8")
        with contextlib.redirect_stderr(io.StringIO()):
            recovered = load_ledger(self.ledger_file)
        self.assertEqual(recovered["active_task"]["task_id"], "saved")
        self.assertEqual(len(list(self.test_dir.glob("*.corrupt_*"))), 1)

    def test_replace_retries_lock_contention_but_not_a_full_disk(self):
        # ADR-146: `except (PermissionError, OSError)` collapsed to OSError, so a full or
        # read-only disk was retried five times before the same failure surfaced.
        atomic_write_json(self.ledger_file, {"version": 1, "active_task": None, "checkpoints": []})
        for error, expected in ((PermissionError(13, "busy"), 3), (OSError(28, "No space left"), 1)):
            with self.subTest(error=type(error).__name__):
                attempts = []

                def fail(src, dst, error=error):
                    attempts.append(src)
                    raise error
                with mock.patch("scripts.disruption_recovery.os.replace", side_effect=fail):
                    with self.assertRaises(OSError):
                        atomic_write_json(self.ledger_file, {"version": 1, "active_task": None,
                                                             "checkpoints": []}, max_retries=3)
                self.assertEqual(len(attempts), expected)
                self.assertEqual(list(self.test_dir.glob("*.tmp_*")), [])

    def test_failed_replace_keeps_the_old_ledger_and_removes_temp(self):
        old = {"version": 1, "active_task": {"task_id": "old"}, "checkpoints": []}
        atomic_write_json(self.ledger_file, old)
        before = self.ledger_file.read_bytes()
        with mock.patch("scripts.disruption_recovery.os.replace",
                        side_effect=PermissionError(13, "busy")):
            with self.assertRaises(OSError):
                atomic_write_json(self.ledger_file,
                                  {"version": 1, "active_task": {"task_id": "new"},
                                   "checkpoints": []}, max_retries=1)
        self.assertEqual(self.ledger_file.read_bytes(), before)
        self.assertEqual(list(self.test_dir.glob("*.tmp_*")), [])

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
        # Enforces PRINCIPLE-006: safe automated purging of orphaned *.tmp_* and *.steal_* buffers
        tmp_file = self.test_dir / "model.py.tmp_8888_7777"
        tmp_file.write_text("corrupted buffer", encoding="utf-8")
        steal_file = self.test_dir / "data.json.steal_9999_1111"
        steal_file.write_text("abandoned steal buffer", encoding="utf-8")
        old = time.time() - 120
        os.utime(tmp_file, (old, old))
        os.utime(steal_file, (old, old))
        # Red-green pin (ADR-078): a buffer younger than 60 s may belong to a write in progress
        # (a parallel agent, a sync run); --clean used to delete it too.
        live = self.test_dir / "state.json.tmp_1_2"
        live.write_text("being written", encoding="utf-8")
        live_steal = self.test_dir / "state.json.steal_1_2"
        live_steal.write_text("active steal", encoding="utf-8")

        purged = clean_dangling_temp_files(workspace_dir=self.test_dir)
        self.assertEqual(sorted(Path(p).name for p in purged), ["data.json.steal_9999_1111", "model.py.tmp_8888_7777"])
        self.assertFalse(tmp_file.exists())
        self.assertFalse(steal_file.exists())
        self.assertTrue(live.exists())
        self.assertTrue(live_steal.exists())

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
            "feat(cli,rules): add multi-domain support",
            "fix(@aikit/core): resolve path resolution issue",
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

    def test_milestone_tags_are_well_formed_and_bounded(self):
        # Red-green pin (ADR-077): out-of-range or misplaced tags passed as description text.
        for msg in ("feat(x): [milestone 2/2] finish it", "fix(x): [milestone 6/6] last"):
            with self.subTest(msg=msg):
                self.assertTrue(validate_conventional_commit(msg)[0])
        for msg in ("feat(x): [milestone 3/2] overshoot", "feat(x): [milestone 1/1] single",
                    "feat(x): [milestone 1/7] too many", "feat(x): [milestone 0/3] zero",
                    "feat(x): do it [milestone 1/2]", "feat(x): [milestone 1/2]"):
            with self.subTest(msg=msg):
                self.assertFalse(validate_conventional_commit(msg)[0])

    def test_unwritable_ledger_reports_the_triad_not_a_traceback(self):
        # Red-green pin (ADR-098): a read-only ledger crashed --checkpoint with a raw traceback.
        with contextlib.redirect_stderr(io.StringIO()) as err:
            report_operational_error(PermissionError, PermissionError(13, "denied"), None)
        lines = err.getvalue().splitlines()
        self.assertTrue(lines[0].startswith("[LEDGER WRITE FAILED]"))
        self.assertTrue(lines[1].startswith("Why:") and lines[2].startswith("Fix:"))
        self.assertNotIn("Traceback", err.getvalue())

    def test_ledger_stores_repository_relative_paths(self):
        # Red-green pin (ADR-097): absolute paths were persisted as given, writing the user's home
        # directory into the tracked ledger (PRINCIPLE-012 R5).
        outside = Path(tempfile.gettempdir()) / "elsewhere.txt"
        cp = record_checkpoint("t", "implementation", "x", phase_num=3, ledger_file=self.ledger_file,
                               files_affected=[ROOT_DIR / "scripts" / "dogfood.py", "service.py", outside])
        self.assertEqual(cp["files_affected"][:2], ["scripts/dogfood.py", "service.py"])
        self.assertEqual(cp["files_affected"][2], str(outside))

    def test_lock_retries_through_windows_delete_pending_permission_error(self):
        # Red-green pin (ADR-077): EACCES while another process deletes the lock file is
        # contention, not a fault; it crashed a parallel checkpoint under suite load.
        real_open, calls = os.open, []

        def flaky_open(path, flags, *args):
            calls.append(path)
            if len(calls) == 1:
                raise PermissionError(13, "delete pending")
            return real_open(path, flags, *args)

        self.addCleanup(setattr, os, "open", real_open)
        os.open = flaky_open
        with file_lock(self.ledger_file, timeout_seconds=1.0, poll_interval=0.001) as acquired:
            self.assertTrue(acquired)
        self.assertEqual(len(calls), 2)

    def test_switching_from_an_in_progress_task_records_it_as_superseded(self):
        # Red-green pin (ADR-077): the interrupted task vanished from the ledger's active state
        # with no record that it was never completed or reset.
        ledger_file = self.ledger_file
        with contextlib.redirect_stderr(io.StringIO()) as err:
            record_checkpoint("first", "implementation", "half done", phase_num=3, ledger_file=ledger_file)
            record_checkpoint("second", "planning", "new", phase_num=2, ledger_file=ledger_file)
        superseded = [c for c in load_ledger(ledger_file)["checkpoints"] if c["status"] == "superseded"]
        self.assertEqual([(c["task_id"], c["phase_num"]) for c in superseded], [("first", 3)])
        self.assertIn("Task 'first' was still in progress", err.getvalue())
        with contextlib.redirect_stderr(io.StringIO()) as quiet:
            record_checkpoint("second", "implementation", "same task", phase_num=3, ledger_file=ledger_file)
        self.assertEqual(quiet.getvalue(), "")


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
                # Hermetic: the sandbox is the root, so no repository file is mapped.
                update_and_validate(knowledge_dir=temp_k_dir, root=temp_k_dir, strict=True)
            codebase_map = temp_k_dir / "codebase_map.md"
            self.assertTrue(codebase_map.exists())
            content = codebase_map.read_text(encoding="utf-8")
            self.assertIn("Codebase Metrics", content)
        finally:
            shutil.rmtree(temp_k_dir, ignore_errors=True)

    def test_codebase_map_freshness_stale_detection(self):
        # Negative path (PRINCIPLE-014): verify that stale codebase_map is detected and rejected
        temp_k_dir = Path(tempfile.mkdtemp(prefix="test_freshness_"))
        try:
            stale_map = temp_k_dir / "codebase_map.md"
            stale_map.write_text("# Stale Codebase Map\nNo metrics here.\n", encoding="utf-8")
            # The sandbox is the root, so the map compared against is a sandbox's, not all of AIKit's
            # (generating AIKit's twice made this the slowest unit test). Lenient mode returns False.
            self.assertFalse(check_codebase_map_freshness(knowledge_dir=temp_k_dir, root=temp_k_dir, strict=False))
            # In strict mode, raises ValueError
            with self.assertRaises(ValueError) as ctx:
                check_codebase_map_freshness(knowledge_dir=temp_k_dir, root=temp_k_dir, strict=True)
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

    def test_ast_distinguishes_properties_from_methods(self):
        temp_dir = Path(tempfile.mkdtemp(prefix="test_ast_kind_"))
        try:
            source = temp_dir / "box.py"
            source.write_text(
                "class Box:\n"
                "    @property\n"
                "    def size(self):\n"
                "        return 1\n"
                "    def open(self):\n"
                "        return True\n",
                encoding="utf-8",
            )
            symbols = extract_python_symbols(source)
            methods = {m["name"]: m["kind"] for m in symbols["classes"][0]["methods"]}
            self.assertEqual(methods, {"size": "property", "open": "method"})
            generated = generate_codebase_map(root=temp_dir)
            self.assertIn("Total Top-Level Functions", generated)
            self.assertIn("Total Class Methods", generated)
            self.assertIn("Property `.size`", generated)
            self.assertIn("Method `.open()", generated)
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

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
                with locked_ledger(self.ledger, timeout_seconds=0.01, poll_interval=0.002):
                    pass
        message = str(ctx.exception)
        self.assertIn("LOCK CONTENTION", message)
        self.assertIn("Fix:", message, "contention error lacks a remediation step")

    def test_resume_reports_the_phase_actually_recorded(self):
        # PRINCIPLE-002 R4 / PRINCIPLE-004 R2: readers looked for a 'last_phase_num' key that was
        # never written, so every resumption reported Phase 2 and could send agents backwards.
        # Only the recorded phase is under test, so fsync is a no-op here (RAII-restored); this
        # class's fsync_dir test keeps the real call.
        self.addCleanup(setattr, os, "fsync", os.fsync)
        os.fsync = lambda fd: None
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

    def test_nul_separated_status_parses_a_rename_whose_names_contain_an_arrow(self):
        # `git status --porcelain -z` quotes nothing and gives a rename as two fields, the new
        # path first. v1 output could not be split when a name held " -> " (POSIX allows it).
        nul = chr(0)
        porcelain = nul.join(["R  new -> name.txt", "old -> name.txt", "?? yeni çift.txt",
                              " M keep.txt", "UU both.txt", ""])
        out = classify_git_status(porcelain)
        self.assertEqual(out["modified"], ["old -> name.txt -> new -> name.txt", "keep.txt"])
        self.assertEqual(out["untracked"], ["yeni çift.txt"])
        self.assertEqual(out["conflicted"], ["UU both.txt"])

    def test_paths_git_quotes_are_reported_as_the_real_names(self):
        # Porcelain v1 quotes a path with a space or a non-ASCII letter, C-style, so the audit -
        # and `status --json` - named files that do not exist (ADR-189).
        q, bs = chr(34), chr(92)
        porcelain = "\n".join([
            f"?? {q}{bs}305{bs}237ifre_notlar{bs}304{bs}261.txt{q}",   # şifre_notları.txt
            f"?? {q}with space.txt{q}",
            f" M {q}say {bs}{q}hi{bs}{q}.txt{q}",                         # say "hi".txt
            f"R  {q}old name.txt{q} -> {q}new name.txt{q}",
            f"UU {q}both added.txt{q}",
            "?? plain.txt",
        ])
        out = classify_git_status(porcelain)
        self.assertEqual(out["untracked"], ["şifre_notları.txt", "with space.txt", "plain.txt"])
        self.assertEqual(out["modified"], ['say "hi".txt', "old name.txt -> new name.txt"])
        self.assertEqual(out["conflicted"], ["UU both added.txt"])

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


class TestProjectRegistry(unittest.TestCase):
    """Projects live outside AIKit's state and carry their own `.aikit/` memory (ADR-119)."""

    def setUp(self):
        self.kit = Path(tempfile.mkdtemp(prefix="test_projects_kit_"))
        self.addCleanup(shutil.rmtree, self.kit, ignore_errors=True)
        # Durability is PRINCIPLE-013's tests' subject; these test registry logic, so fsync is a
        # no-op here to keep the unit tier under 1s. RAII-restored (PRINCIPLE-014 R4).
        self.addCleanup(setattr, os, "fsync", os.fsync)
        os.fsync = lambda fd: None

    def make_folder(self, *files):
        folder = Path(tempfile.mkdtemp(prefix="test_projects_ext_"))
        self.addCleanup(shutil.rmtree, folder, ignore_errors=True)
        for name, text in files:
            (folder / name).write_text(text, encoding="utf-8")
        return folder

    def test_detects_every_stack_and_its_test_command(self):
        folder = self.make_folder(
            ("pyproject.toml", "[tool.pytest.ini_options]\n"),
            ("package.json", '{"scripts": {"test": "vitest run"}}'),
            ("yarn.lock", ""),
            ("go.mod", "module x\n"),
        )
        self.assertEqual(
            [(s.name, s.test_command) for s in detect_stacks(folder)],
            [("python", "python -m pytest"), ("node", "yarn test"), ("go", "go test ./...")])

    def test_npm_placeholder_is_not_a_test_command(self):
        folder = self.make_folder(
            ("package.json", '{"scripts": {"test": "echo \\"Error: no test specified\\" && exit 1"}}'))
        self.assertEqual(detect_stacks(folder), (Stack("node", None),))

    def test_name_must_be_one_portable_segment(self):
        for bad in ("", "My App", "../x", "a/b", "-x", "x" * 65):
            with self.assertRaises(ProjectError) as caught:
                validate_name(bad)
            self.assertEqual(caught.exception.exit_code, 2)
        validate_name("my-app_2")

    def test_name_is_not_a_windows_device(self):
        # ADR-196: `new nul` said the folder already exists and `new con` failed in `git init`;
        # elsewhere such a project is created and its repository cannot be cloned on Windows.
        for bad in ("con", "prn", "aux", "nul", "com0", "com1", "com9", "lpt0", "lpt1", "lpt9"):
            with self.subTest(name=bad), self.assertRaises(ProjectError) as caught:
                validate_name(bad)
            self.assertEqual(caught.exception.exit_code, 2)
            self.assertIn("Windows device", caught.exception.why)
        for good in ("conin", "console", "com10", "lpt10", "nul-app", "auxiliary"):
            with self.subTest(name=good):
                validate_name(good)

    def test_attach_writes_memory_once_and_lists_the_project(self):
        folder = self.make_folder(("Cargo.toml", "[package]\n"))
        name, path, created = attach_project(folder, "svc", workspace=self.kit)
        self.assertEqual((name, path, created), ("svc", folder.resolve(), True))
        config = load_config(folder)
        self.assertEqual((config["name"], config["test_command"]), ("svc", None))
        self.assertIn(".aikit/*.lock", (folder / ".gitignore").read_text(encoding="utf-8"))
        # Re-attaching keeps the existing memory and adds no duplicate ignore lines.
        self.assertFalse(attach_project(folder, "svc", workspace=self.kit)[2])
        self.assertEqual((folder / ".gitignore").read_text(encoding="utf-8").count(".aikit/*.lock"), 1)
        [project] = list_projects(self.kit)
        self.assertEqual((project.name, project.attached, project.test_command, project.present),
                         ("svc", True, "cargo test", True))

    def test_override_beats_detection_and_missing_folder_is_reported(self):
        folder = self.make_folder(("go.mod", "module x\n"))
        attach_project(folder, "svc", test_command="make test", workspace=self.kit)
        self.assertEqual(list_projects(self.kit)[0].test_command, "make test")
        shutil.rmtree(folder)
        self.assertFalse(list_projects(self.kit)[0].present)

    def test_attach_refuses_folders_overlapping_the_kit(self):
        nested = self.kit / "scripts"
        nested.mkdir()
        for folder in (self.kit, nested):
            with self.assertRaises(ProjectError) as caught:
                attach_project(folder, "x", workspace=self.kit)
            self.assertEqual(caught.exception.exit_code, 2)

    def test_projects_folder_is_discovered_without_the_attached_file(self):
        folder = self.kit / "projects" / "local-app"
        folder.mkdir(parents=True)
        attach_project(folder, workspace=self.kit)
        self.assertFalse((self.kit / "projects" / "attached.json").exists())
        self.assertEqual([(p.name, p.attached) for p in list_projects(self.kit)],
                         [("local-app", False)])

    def test_corrupt_attached_file_is_an_error_not_an_empty_list(self):
        (self.kit / "projects").mkdir()
        (self.kit / "projects" / "attached.json").write_text("{", encoding="utf-8")
        with self.assertRaises(ProjectError):
            list_projects(self.kit)

    def test_failed_git_init_leaves_no_half_made_project(self):
        def refuse(project_root):
            raise ProjectError("git missing", "why", "fix")
        with self.assertRaises(ProjectError):
            create_project("app", workspace=self.kit, git_start=refuse)
        self.assertFalse((self.kit / "projects" / "app").exists())

    def test_new_project_starts_licensed_described_tagged_and_linked_to_aikit(self):
        # ADR-199, ADR-214: a new project is free for personal use under AL-1.0, says what it
        # is, carries GitHub topics and its README links back to AIKit.
        description = "A command-line tool that keeps a reading list in sync across devices."
        folder = create_project("reader", workspace=self.kit, git_start=lambda project_root: None,
                                description=description, topics=["Python", "cli", "python"])
        self.assertEqual((folder / "LICENSE").read_text(encoding="utf-8"),
                         (ROOT_DIR / "LICENSE").read_text(encoding="utf-8"))
        self.assertTrue((folder / "LICENSE").read_text(encoding="utf-8").lstrip()
                        .startswith("# Aegean License 1.0 (AL-1.0)"))
        self.assertEqual(license_state(folder).tier, "personal")
        readme = (folder / "README.md").read_text(encoding="utf-8")
        self.assertIn(f"]({AIKIT_URL})", readme, "the badge links to AIKit")
        self.assertIn("Built with AIKit", readme)
        self.assertIn(f"\n{description}\n", readme)
        self.assertIn("├── LICENSE", readme)
        self.assertIn("├── COMMERCIAL.md", readme)
        self.assertIn("Aegean License 1.0 (AL-1.0)", readme)
        self.assertIn("Aegean Commercial License 1.0 (ACL-1.0)", readme)
        self.assertNotIn("Affero", readme)
        self.assertNotIn("Aegean-E", readme, "the licenses are named Aegean, not Aegean-E")
        self.assertIn("COMMERCIAL.md", readme)
        self.assertEqual((folder / "COMMERCIAL.md").read_text(encoding="utf-8"),
                         (ROOT_DIR / "COMMERCIAL.md").read_text(encoding="utf-8"))
        self.assertEqual(extract_readme_description(folder), description, "publish reads it back")
        config = json.loads((folder / ".aikit" / "project.json").read_text(encoding="utf-8"))
        self.assertNotIn("description", config, "the README is its one source (ADR-202)")
        self.assertEqual(config["topics"], ["aikit", "python", "cli"], "aikit first, deduplicated")

    def test_attach_adds_the_integrated_badge_under_the_title(self):
        # ADR-202: a project AIKit is integrated into says so and links to AIKit.
        folder = self.make_folder()
        (folder / "README.md").write_bytes(b"# Tool\r\n\r\nWhat it does.\r\n")
        code, out, err = self.run_cli("attach", str(folder), "--name", "tool")
        self.assertEqual(code, 0, err)
        self.assertEqual((folder / "README.md").read_bytes(),
                         f"# Tool\r\n\r\n{AIKIT_INTEGRATED_BADGE}\r\n\r\nWhat it does.\r\n".encode(),
                         "inserted under the title, the file's own line endings kept")
        self.assertIn("AIKit Integrated badge", out)
        self.assertIn("uncommitted", out)
        # ADR-207: an attached repository's own commands run as the user; nothing sandboxes them.
        self.assertIn("run this project's own commands under your account, unsandboxed", out)
        self.assertEqual(extract_readme_description(folder), "What it does.", "the badge is no description")

    def test_a_folder_is_attached_under_one_name_only(self):
        # ADR-202: a second name for an attached folder made two projects share one .aikit/ ledger.
        folder = self.make_folder()
        attach_project(folder, "first", workspace=self.kit)
        attach_project(folder, "first", workspace=self.kit)  # the same pair again is a no-op
        with self.assertRaises(ProjectError) as caught:
            attach_project(folder, "second", workspace=self.kit)
        self.assertEqual(caught.exception.exit_code, 2)
        self.assertIn("already attached as 'first'", str(caught.exception))
        self.assertEqual(set(load_attached(self.kit)), {"first"})

    def test_the_badge_is_added_once_and_only_to_a_readme(self):
        folder = self.make_folder(("README.md", "No title here.\n"))
        self.assertTrue(add_aikit_badge(folder))
        self.assertEqual((folder / "README.md").read_text(encoding="utf-8"),
                         f"{AIKIT_INTEGRATED_BADGE}\n\nNo title here.\n")
        self.assertFalse(add_aikit_badge(folder), "a README that links to AIKit is left alone")
        built = self.make_folder(("README.md", f"# x\n\n{AIKIT_BADGE}\n"))
        self.assertFalse(add_aikit_badge(built), "a Built with AIKit badge already links to AIKit")
        self.assertFalse(add_aikit_badge(self.make_folder()), "no README is created")

    def test_a_legacy_badge_link_is_rewritten_instead_of_duplicated(self):
        legacy = AIKIT_INTEGRATED_BADGE.replace(AIKIT_URL, LEGACY_AIKIT_URL)
        folder = self.make_folder(
            ("README.md", f"# x\n\n{legacy}\n\ntext that mentions {LEGACY_AIKIT_URL}.\n"))
        self.assertTrue(add_aikit_badge(folder), "a legacy link is migrated, not left alone")
        text = (folder / "README.md").read_text(encoding="utf-8")
        self.assertIn(AIKIT_INTEGRATED_BADGE, text)
        self.assertNotIn(LEGACY_AIKIT_URL, text, "no stale AIKit URL survives the migration")
        self.assertEqual(text.count("[![AIKit Integrated]"), 1,
                         "the migration must not append a second badge")
        self.assertFalse(add_aikit_badge(folder), "a migrated README is left alone afterwards")

    def test_a_readme_holding_both_urls_loses_the_legacy_one(self):
        # ADR-213: checking the current URL first left a mixed pair when both appeared, so the
        # stale link survived every refresh.
        folder = self.make_folder((
            "README.md",
            f"# x\n\n{AIKIT_INTEGRATED_BADGE}\n\nForked from {LEGACY_AIKIT_URL}.\n",
        ))
        self.assertTrue(add_aikit_badge(folder))
        text = (folder / "README.md").read_text(encoding="utf-8")
        self.assertNotIn(LEGACY_AIKIT_URL, text)
        self.assertEqual(text.count("[![AIKit Integrated]"), 1, "no second badge is appended")

    def test_migrate_aikit_links_keeps_line_endings_and_is_idempotent(self):
        folder = self.make_folder()
        (folder / "README.md").write_bytes(f"# x\r\n\r\nSee {LEGACY_AIKIT_URL}.\r\n".encode())
        self.assertTrue(migrate_aikit_links(folder))
        self.assertEqual((folder / "README.md").read_bytes(),
                         f"# x\r\n\r\nSee {AIKIT_URL}.\r\n".encode())
        self.assertFalse(migrate_aikit_links(folder), "a migrated README is left alone")
        self.assertFalse(migrate_aikit_links(self.make_folder()), "no README is created")

    def test_fix_migrates_a_pre_move_badge_link(self):
        folder = self.make_folder(
            ("README.md", f"# app\n\n{AIKIT_INTEGRATED_BADGE.replace(AIKIT_URL, LEGACY_AIKIT_URL)}\n"))
        attach_project(folder, "myapp", workspace=self.kit)
        with mock.patch("scripts.aikit_cli.cmd_check", return_value=0):
            code, out, _ = self.run_cli("fix", "myapp")
        self.assertEqual(code, 0)
        self.assertIn("updated the README's pre-move AIKit link", out)
        text = (folder / "README.md").read_text(encoding="utf-8")
        self.assertIn(AIKIT_INTEGRATED_BADGE, text)
        self.assertNotIn(LEGACY_AIKIT_URL, text)
        self.assertEqual(text.count("[![AIKit Integrated]"), 1, "fix never appends a second badge")

    def test_fix_seeds_an_attached_projects_readme_with_the_integrated_badge(self):
        self.assertIn(AIKIT_INTEGRATED_BADGE, render_project_readme("app", integrated=True))
        self.assertNotIn(AIKIT_BADGE, render_project_readme("app", integrated=True))
        self.assertIn(AIKIT_BADGE, render_project_readme("app"))
        template = (ROOT_DIR / ".agents" / "rules" / "readme_quickref.md.template").read_text(encoding="utf-8")
        self.assertTrue(template.startswith(AIKIT_INTEGRATED_BADGE), "the copy-in README starts with it")

    def test_new_project_without_description_keeps_a_fill_marker(self):
        folder = create_project("blank", workspace=self.kit, git_start=lambda project_root: None)
        readme = (folder / "README.md").read_text(encoding="utf-8")
        self.assertIn("<FILL: one sentence on what this project does", readme)
        self.assertEqual(extract_readme_description(folder), "", "the marker is never uploaded")
        config = json.loads((folder / ".aikit" / "project.json").read_text(encoding="utf-8"))
        self.assertNotIn("description", config)
        self.assertEqual(config["topics"], ["aikit"])

    def test_description_and_topics_are_checked_before_anything_is_created(self):
        for kwargs in ({"description": "too short"}, {"description": "x" * 351},
                       {"description": "first line\nsecond line long enough"},
                       {"topics": ["-lead"]}, {"topics": ["two words"]}, {"topics": ["x" * 51]},
                       {"topics": [f"t{n}" for n in range(20)]}):
            with self.subTest(kwargs=str(kwargs)[:40]), self.assertRaises(ProjectError) as caught:
                create_project("checked", workspace=self.kit, git_start=lambda project_root: None,
                               **kwargs)
            self.assertEqual(caught.exception.exit_code, 2)
            self.assertFalse((self.kit / "projects" / "checked").exists())

    def test_first_commit_holds_the_license(self):
        from scripts.project_registry import _git_start
        folder = self.make_folder(("LICENSE", "AEGEAN-E PERSONAL USE LICENSE\n"))
        ok = mock.Mock(returncode=0, stderr="")
        with mock.patch("scripts.project_registry._run_git", return_value=ok) as run:
            _git_start(folder)
        added = next(c.args for c in run.call_args_list if c.args[1] == "add")
        self.assertIn("LICENSE", added)
        with mock.patch("scripts.project_registry._run_git", return_value=ok) as run:
            _git_start(self.make_folder())
        added = next(c.args for c in run.call_args_list if c.args[1] == "add")
        self.assertNotIn("LICENSE", added, "a missing file would make `git add` fail")

    def test_first_commit_holds_commercial_md(self):
        from scripts.project_registry import _git_start
        folder = self.make_folder(("COMMERCIAL.md", "# Aegean Commercial License (ACL-1.0)\n"))
        ok = mock.Mock(returncode=0, stderr="")
        with mock.patch("scripts.project_registry._run_git", return_value=ok) as run:
            _git_start(folder)
        added = next(c.args for c in run.call_args_list if c.args[1] == "add")
        self.assertIn("COMMERCIAL.md", added)

    def test_pinned_license_texts_match_their_recorded_digests(self):
        # ADR-214: licenses/ copies aegean-licensing; a hand edit here breaks the pin.
        pin = json.loads((ROOT_DIR / "licenses" / "PIN.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(pin["sha256"]), ["ACL-1.0.md", "AL-1.0.md", "RESTRICTED-NOTICE.md"])
        for name, digest in pin["sha256"].items():
            text = (ROOT_DIR / "licenses" / name).read_text(encoding="utf-8").replace("\r\n", "\n")
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256(text.encode("utf-8")).hexdigest(), digest,
                                 "copy it from aegean-licensing and refresh licenses/PIN.json")
        self.assertEqual((ROOT_DIR / "LICENSE").read_text(encoding="utf-8"),
                         (ROOT_DIR / "licenses" / "AL-1.0.md").read_text(encoding="utf-8"),
                         "AIKit's LICENSE is the pinned AL-1.0 text verbatim")

    def make_licensed_project(self, name="vault"):
        # What `new` leaves that the license tier reads, without `new`'s cost (PRINCIPLE-014 R4).
        folder = self.kit / "projects" / name
        (folder / ".aikit").mkdir(parents=True)
        (folder / ".aikit" / "project.json").write_text(json.dumps({"schema": 1, "name": name}),
                                                        encoding="utf-8")
        for license_file in ("LICENSE", "COMMERCIAL.md"):
            shutil.copyfile(ROOT_DIR / license_file, folder / license_file)
        (folder / "README.md").write_text(render_project_readme(name, licensed=True), encoding="utf-8")
        return folder

    @staticmethod
    def git_head(commit="0123456789abcdef0123456789abcdef01234567", returncode=0):
        return mock.Mock(return_value=mock.Mock(returncode=returncode, stdout=commit + "\n",
                                                stderr="fatal: no commits"))

    def test_restrict_swaps_the_license_records_the_cutoff_and_drops_commercial_terms(self):
        # ADR-214: a restricted project is All Rights Reserved from a recorded cutoff commit on.
        folder = self.make_licensed_project()
        state = restrict_project(folder, "vault", today="2026-10-25", runner=self.git_head())
        self.assertEqual((state.tier, state.since, state.since_commit[:7]),
                         ("restricted", "2026-10-25", "0123456"))
        license_text = (folder / "LICENSE").read_text(encoding="utf-8")
        self.assertTrue(license_text.startswith("AEGEAN RESTRICTED SOFTWARE NOTICE"))
        self.assertIn("ALL RIGHTS RESERVED", license_text)
        self.assertIn("Project: vault.", license_text)
        self.assertIn("0123456789abcdef0123456789abcdef01234567", license_text,
                      "the notice names the last commit released under the earlier license")
        self.assertNotIn("{", license_text, "the canonical template is filled completely")
        self.assertFalse((folder / "COMMERCIAL.md").exists(), "no public commercial offer remains")
        readme = (folder / "README.md").read_text(encoding="utf-8")
        self.assertNotIn("COMMERCIAL.md", readme)
        self.assertNotIn("Aegean License 1.0", readme)
        self.assertIn("All Rights Reserved", readme)
        self.assertEqual(readme.count("## 📜 License"), 1)
        config = json.loads((folder / ".aikit" / "project.json").read_text(encoding="utf-8"))
        self.assertEqual(config["license"]["since_commit"], state.since_commit)
        self.assertEqual(license_state(folder), state, "the state reads back from disk")

    def test_restrict_twice_keeps_the_first_cutoff(self):
        folder = self.make_licensed_project()
        first = restrict_project(folder, "vault", today="2026-10-25", runner=self.git_head())
        again = restrict_project(folder, "vault", today="2027-01-01",
                                 runner=self.git_head("f" * 40))
        self.assertEqual(again, first)

    def test_restrict_without_a_commit_changes_nothing(self):
        folder = self.make_licensed_project()
        before = (folder / "LICENSE").read_text(encoding="utf-8")
        with self.assertRaises(ProjectError) as caught:
            restrict_project(folder, "vault", runner=self.git_head("", returncode=128))
        self.assertIn("commit", caught.exception.fix)
        self.assertEqual((folder / "LICENSE").read_text(encoding="utf-8"), before)
        self.assertTrue((folder / "COMMERCIAL.md").exists())

    def test_restrict_appends_a_license_section_to_a_readme_without_one(self):
        folder = self.make_folder(("README.md", "# Tool\n\nWhat it does.\n"))
        attach_project(folder, "tool", workspace=self.kit)
        self.assertEqual(license_state(folder).tier, "unrecorded", "its own license is not ours to read")
        restrict_project(folder, "tool", today="2026-10-25", runner=self.git_head())
        readme = (folder / "README.md").read_text(encoding="utf-8")
        self.assertTrue(readme.startswith("# Tool\n\nWhat it does.\n"))
        self.assertIn("## 📜 License", readme)

    def test_cli_license_reports_then_restricts_with_a_checklist(self):
        self.make_licensed_project()
        code, out, _ = self.run_cli("license", "vault")
        self.assertEqual(code, 0)
        self.assertIn("personal", out)
        with mock.patch("scripts.project_license._run_git", self.git_head()):
            code, out, _ = self.run_cli("license", "vault", "--restrict")
        self.assertEqual(code, 0)
        self.assertIn("restricted", out)
        self.assertIn("0123456789ab", out)
        self.assertIn("private", out, "the checklist names the steps AIKit cannot take")
        self.assertIn("stay under", out, "earlier releases keep their license")

    def test_a_restricted_project_pushes_only_to_a_private_remote(self):
        # ADR-214: `check --push` and `publish` to an existing origin must not hand a restricted
        # project to a public repository, and an unknown visibility counts as public.
        folder = self.make_licensed_project()
        self.assertIsNone(public_remote_refusal(folder, "vault", runner=lambda argv, cwd: (0, "PUBLIC")),
                          "a personal-tier project is not checked")
        restrict_project(folder, "vault", today="2026-10-25", runner=self.git_head())
        self.assertIsNone(public_remote_refusal(folder, "vault", runner=lambda argv, cwd: (0, "PRIVATE\n")))
        for answer in ((0, "PUBLIC"), (0, "INTERNAL"), (1, "gh: not logged in"), (-1, "")):
            with self.subTest(answer=answer):
                error = public_remote_refusal(folder, "vault", runner=lambda argv, cwd, a=answer: a)
                self.assertIsInstance(error, ProjectError)
                self.assertIn("private", error.fix)

    def test_check_push_refuses_a_restricted_project_with_a_public_origin(self):
        folder = self.make_licensed_project()
        restrict_project(folder, "vault", today="2026-10-25", runner=self.git_head())
        with mock.patch("scripts.project_license.run_command", return_value=(0, "PUBLIC")), \
             mock.patch("scripts.aikit_cli.run_gates") as gates, \
             mock.patch("scripts.aikit_cli.auto_push_project") as push:
            code, _, err = self.run_cli("check", "vault", "--push")
        self.assertEqual(code, 2)
        self.assertIn("restricted", err)
        gates.assert_not_called()
        push.assert_not_called()

    def test_publish_public_refuses_a_restricted_project(self):
        folder = self.make_licensed_project()
        restrict_project(folder, "vault", today="2026-10-25", runner=self.git_head())
        with mock.patch("scripts.aikit_cli.publish_project") as publish:
            code, _, err = self.run_cli("publish", "vault", "--public")
        self.assertEqual(code, 2)
        self.assertIn("restricted", err)
        self.assertIn("Why:", err)
        publish.assert_not_called()

    def test_cli_new_takes_a_description_and_topics(self):
        with mock.patch("scripts.project_registry._git_start"):
            code, out, err = self.run_cli("new", "tagged", "--description",
                                          "A small web app that tracks shared household chores.",
                                          "--topic", "web", "--topic", "flask")
        self.assertEqual(code, 0, err)
        config = json.loads((self.kit / "projects" / "tagged" / ".aikit" / "project.json")
                            .read_text(encoding="utf-8"))
        self.assertEqual(config["topics"], ["aikit", "web", "flask"])

    def test_new_project_ignores_bytecode_and_has_a_clean_adr_template(self):
        folder = create_project("pyapp", workspace=self.kit,
                                git_start=lambda project_root: None)
        ignored = (folder / ".gitignore").read_text(encoding="utf-8")
        for line in ("__pycache__/", "*.py[cod]", "node_modules/"):
            self.assertIn(line, ignored)
        decisions = (folder / ".aikit" / "decisions.md").read_text(encoding="utf-8")
        self.assertEqual(audit_adr_register(decisions), [])

    def test_git_identity_failure_is_an_error_not_a_warning(self):
        from scripts.project_registry import _git_start
        results = [mock.Mock(returncode=0, stderr=""),
                   mock.Mock(returncode=0, stderr=""),
                   mock.Mock(returncode=128, stderr="fatal: identity unknown")]
        with mock.patch("scripts.project_registry._run_git", side_effect=results):
            with self.assertRaises(ProjectError) as caught:
                _git_start(self.make_folder())
        self.assertIn("initial commit failed", str(caught.exception))

    def test_cli_reports_triad_and_exit_codes(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr), self.assertRaises(SystemExit) as caught:
            aikit_main(["frobnicate"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("Why:", stderr.getvalue())
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            self.assertEqual(aikit_main(["new", "Bad Name"]), 2)
        self.assertIn("Fix:", stderr.getvalue())

    def test_a_filesystem_error_is_reported_with_a_remedy(self):
        import scripts.aikit_cli as cli

        def fail(args):
            raise PermissionError("denied")

        with mock.patch.dict(cli.HANDLERS, {"list": fail}):
            code, _, err = self.run_cli("list")
        self.assertEqual(code, 1)
        self.assertIn("Why:", err)
        self.assertIn("Fix:", err)

    def test_project_memory_holds_ledger_and_decisions(self):
        folder = self.make_folder()
        attach_project(folder, "svc", workspace=self.kit)
        self.assertEqual(workspace_ledger_path(folder), folder / ".aikit" / "task_ledger.json")
        self.assertEqual(workspace_ledger_path(self.kit), self.kit / ".agents" / "task_ledger.json")
        # attach adds only .aikit/ and .gitignore lines; `fix` seeds a README when asked (ADR-128).
        self.assertFalse((folder / "README.md").exists())
        self.assertTrue((folder / ".aikit" / "task_ledger.json").is_file())
        self.assertTrue((folder / ".aikit" / "project.json").is_file())
        self.assertTrue((folder / ".aikit" / "decisions.md").is_file())
        self.assertFalse((folder / "AGENTS.md").exists())
        self.assertFalse((folder / "CLAUDE.md").exists())
        # The template's commented example is not a decision; real entries are, newest last.
        self.assertIsNone(latest_decision(folder))
        with open(folder / ".aikit" / "decisions.md", "a", encoding="utf-8") as handle:
            handle.write("\n### ADR-001: Use SQLite\n\n### ADR-002: Expose a REST API\n")
        self.assertEqual(latest_decision(folder), "ADR-002: Expose a REST API")

    def test_status_names_unknown_and_missing_projects(self):
        with self.assertRaises(ProjectError) as caught:
            find_project("nope", self.kit)
        self.assertEqual(caught.exception.exit_code, 2)
        folder = self.make_folder()
        attach_project(folder, "svc", workspace=self.kit)
        shutil.rmtree(folder)
        self.assertFalse(find_project("svc", self.kit).present)

    def test_fix_cli_reports_triad_on_unknown_project(self):
        stderr = io.StringIO()
        with contextlib.redirect_stderr(stderr):
            self.assertEqual(aikit_main(["fix", "nonexistent"]), 2)
        self.assertIn("Why:", stderr.getvalue())
        self.assertIn("Fix:", stderr.getvalue())

    def run_cli(self, *argv):
        """`aikit` in-process against this test's kit; returns (exit code, stdout, stderr)."""
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = aikit_main(["--workspace", str(self.kit), *argv])
        return code, out.getvalue(), err.getvalue()

    def stale(self, path):
        path.write_text("buffer", encoding="utf-8")
        old = time.time() - 3600
        os.utime(path, (old, old))
        return path

    def test_fix_restores_memory_and_readme_and_removes_only_stale_buffers(self):
        folder = self.make_folder()
        attach_project(folder, "myapp", workspace=self.kit)
        self.assertFalse((folder / "README.md").exists(), "attach leaves the folder's files alone")
        stale = self.stale(folder / "state.json.tmp_1_1")
        fresh = folder / "other.json.tmp_2_2"
        fresh.write_text("in-flight write", encoding="utf-8")
        (folder / ".aikit" / "decisions.md").unlink()
        (folder / "core.py").write_text("def work():\n    return 1\n", encoding="utf-8")
        with mock.patch("scripts.aikit_cli.cmd_check", return_value=0):
            code, out, _ = self.run_cli("fix", "myapp")
        self.assertEqual(code, 0)
        for fixed in ("restored .aikit/decisions.md", "seeded README.md", "removed stale buffer",
                      "regenerated .aikit/codebase_map.md"):
            self.assertIn(fixed, out)
        self.assertFalse(stale.exists())
        self.assertTrue(fresh.exists(), "a young buffer may be another agent's write in flight")
        # The seed fails PRINCIPLE-005's audit on its unfilled marker, and passes once the
        # prerequisite line states the project's facts (pure form: no git spawn here).
        readme = (folder / "README.md").read_text(encoding="utf-8")
        tracked = [".gitignore", "README.md", ".aikit/project.json", ".aikit/decisions.md"]

        def audit(text):
            return audit_readme(text, tracked, lambda rel: (folder / rel).exists(), lambda rel: None)

        self.assertIn("unfilled '<FILL:' placeholder", "".join(audit(readme)))
        self.assertEqual(audit(re.sub(r"<FILL:[^>]*>", "Python 3.10+ and git", readme)), [])

    def test_fix_reconciles_omitted_tracked_files_in_readme_tree(self):
        folder = self.make_folder(
            ("README.md",
             "# demo\n\n## ⚡ 30-Second Cold-Start Quick Reference\n"
             "- **Runtime Prerequisites**: Python 3.10+\n"
             "- **Canonical Regression Shield Gate**:\n  ```bash\n  python -m unittest discover\n  ```\n\n"
             "## 📦 What's Inside\n\n```text\ndemo/\n"
             "├── .gitignore\n"
             "├── README.md\n"
             "└── .aikit/\n```\n"),
            ("LICENSE", "AGPL-3.0 text\n"),
            (".gitignore", ".aikit/*.lock\n"),
        )
        (folder / ".git").mkdir()
        attach_project(folder, "demoapp", workspace=self.kit)
        with mock.patch("scripts.update_knowledge_base.subprocess.run") as mock_run, \
             mock.patch("scripts.aikit_cli.cmd_check", return_value=0):
            mock_run.return_value = subprocess.CompletedProcess(
                ["git", "ls-files", "-z"], 0,
                ".gitignore\0README.md\0LICENSE\0.aikit/project.json\0", ""
            )
            code, out, _ = self.run_cli("fix", "demoapp")
        self.assertEqual(code, 0)
        self.assertIn("added 'LICENSE' to README.md tree", out)
        readme = (folder / "README.md").read_text(encoding="utf-8")
        self.assertIn("LICENSE", readme)

    def test_fix_reconciles_a_name_that_is_a_substring_of_another_entry(self):
        folder = self.make_folder(
            ("README.md",
             "# demo\n\n## ⚡ 30-Second Cold-Start Quick Reference\n"
             "- **Runtime Prerequisites**: Python 3.10+\n"
             "- **Canonical Regression Shield Gate**:\n  ```bash\n  python -m unittest discover\n  ```\n\n"
             "## 📦 What's Inside\n\n```text\ndemo/\n"
             "├── .gitignore\n"
             "├── README.md\n"
             "├── LICENSE.md\n"
             "└── .aikit/\n```\n"),
            ("LICENSE", "AGPL-3.0 text\n"),
            ("LICENSE.md", "license notes\n"),
            (".gitignore", ".aikit/*.lock\n"),
        )
        (folder / ".git").mkdir()
        attach_project(folder, "substringapp", workspace=self.kit)
        with mock.patch("scripts.update_knowledge_base.subprocess.run") as mock_run, \
             mock.patch("scripts.aikit_cli.cmd_check", return_value=0):
            mock_run.return_value = subprocess.CompletedProcess(
                ["git", "ls-files", "-z"], 0,
                ".gitignore\0README.md\0LICENSE\0LICENSE.md\0.aikit/project.json\0", ""
            )
            code, out, _ = self.run_cli("fix", "substringapp")
        self.assertEqual(code, 0)
        self.assertIn("added 'LICENSE' to README.md tree", out)
        readme = (folder / "README.md").read_text(encoding="utf-8")
        self.assertIn("├── LICENSE\n", readme)
        self.assertIn("├── LICENSE.md\n", readme)

    def test_project_ledger_commands_keep_the_impact_gate(self):
        folder = self.make_folder()
        attach_project(folder, "demo", workspace=self.kit)
        plan = ["checkpoint", "demo", "--task", "task-alpha", "--phase-num", "2", "--desc", "[1/2] setup database"]
        code, _, err = self.run_cli(*plan)
        self.assertEqual(code, 2, "a first plan without an impact assessment is refused (PRINCIPLE-007 R6)")
        self.assertIn("[INCOMPLETE IMPACT]", err)
        code, out, _ = self.run_cli(*plan, "--why", "storage", "--benefits", "state", "--mitigation", "tests",
                                    "--risks", "contract: none; dependency: none; concurrency: none; state: new db")
        self.assertEqual(code, 0)
        self.assertIn("Checkpoint recorded: Task 'task-alpha'", out)
        ledger = load_ledger(folder / ".aikit" / "task_ledger.json")
        self.assertEqual((ledger["active_task"]["task_id"], ledger["active_task"]["active_phase"]),
                         ("task-alpha", 2))
        self.assertIn("setup database", self.run_cli("resume", "demo")[1])
        self.assertEqual(self.run_cli("complete", "demo", "--task", "other")[0], 1)
        self.assertEqual(self.run_cli("complete", "demo", "--task", "task-alpha")[0], 0)
        self.assertEqual(load_ledger(folder / ".aikit" / "task_ledger.json")["active_task"]["status"], "completed")
        stale = self.stale(folder / "temp.json.tmp_1_1")
        fresh = folder / "young.json.tmp_2_2"
        fresh.write_text("x", encoding="utf-8")
        self.assertEqual(self.run_cli("clean", "demo")[0], 0)
        self.assertEqual((stale.exists(), fresh.exists()), (False, True))

    def test_workspace_is_explicit_never_the_working_directory(self):
        # A `projects/` folder in the working directory used to become the registry (ADR-128).
        stray = self.make_folder()
        (stray / "projects" / "ghost" / ".aikit").mkdir(parents=True)
        (stray / "projects" / "ghost" / ".aikit" / "project.json").write_text(
            '{"schema": 1, "name": "ghost"}', encoding="utf-8")
        cwd = os.getcwd()
        os.chdir(stray)
        self.addCleanup(os.chdir, cwd)
        code, out, _ = self.run_cli("list")
        self.assertEqual(code, 0)
        self.assertNotIn("ghost", out)

    def test_new_with_publish_flag_calls_publish_project(self):
        with mock.patch("scripts.aikit_cli.create_project", return_value=self.kit / "projects" / "publishedapp"), \
             mock.patch("scripts.aikit_cli.publish_project", return_value=(0, "[OK] Published to GitHub")) as mock_pub:
            code, out, _ = self.run_cli("new", "publishedapp", "--publish", "--test", "python -m unittest",
                                        "--description", "A tool that publishes itself on creation.",
                                        "--topic", "Demo")
            self.assertEqual(code, 0)
            mock_pub.assert_called_once()
            # ADR-200: the new project's description and topics reach the repository it creates.
            self.assertNotIn("description", mock_pub.call_args.kwargs, "publish reads the README (ADR-202)")
            self.assertEqual(mock_pub.call_args.kwargs["topics"], ["aikit", "demo"])
            self.assertIn("Publishing 'publishedapp' to GitHub:", out)
            self.assertIn("[OK] Published to GitHub", out)


    def test_status_displays_repo_url(self):
        folder = self.make_folder()
        attach_project(folder, "repoapp", workspace=self.kit)
        with mock.patch("scripts.aikit_cli.get_project_repo_url", return_value="https://github.com/org/repoapp"):
            code, out, _ = self.run_cli("status", "repoapp")
            self.assertEqual(code, 0)
            self.assertIn("Repo:      https://github.com/org/repoapp", out)

    def test_status_exit_code_tracks_dirty_state_without_changing_plain_status(self):
        folder = self.make_folder()
        attach_project(folder, "codeapp", workspace=self.kit)
        clean = {"modified_files": [], "untracked_files": [], "conflicted_files": [],
                 "ledger_error": None, "git_missing": False}
        dirty = {"modified_files": ["core.py"], "untracked_files": ["test_features.py"],
                 "conflicted_files": [], "ledger_error": None, "git_missing": False}
        unauditable = {"modified_files": [], "untracked_files": [], "conflicted_files": [],
                       "ledger_error": None, "git_missing": True}
        with mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=clean):
            code, _, _ = self.run_cli("status", "codeapp")
            self.assertEqual(code, 0)
            code, _, _ = self.run_cli("status", "codeapp", "--exit-code")
            self.assertEqual(code, 0)
        ui_task = folder / ".aikit" / "ui_task.json"
        ui_task.write_text("{}", encoding="utf-8")
        with mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=clean):
            code, out, _ = self.run_cli("status", "codeapp")
            self.assertEqual(code, 0)
            self.assertIn("UI task:", out)
            code, _, _ = self.run_cli("status", "codeapp", "--exit-code")
            self.assertEqual(code, 1, "an open UI task blocks machine-readable delivery")
        ui_task.unlink()
        with mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=dirty):
            code, _, _ = self.run_cli("status", "codeapp")
            self.assertEqual(code, 0, "plain status keeps its advisory exit semantics")
            code, _, _ = self.run_cli("status", "codeapp", "--exit-code")
            self.assertEqual(code, 1)
        with mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=unauditable):
            code, _, _ = self.run_cli("status", "codeapp")
            self.assertEqual(code, 0, "plain status remains advisory without git")
            code, _, _ = self.run_cli("status", "codeapp", "--exit-code")
            self.assertEqual(code, 1, "a tree git cannot audit is not delivery-ready")

    def test_status_json_reports_the_same_readiness_as_the_exit_code(self):
        folder = self.make_folder()
        attach_project(folder, "jsonstatus", workspace=self.kit)
        clean = {"modified_files": [], "untracked_files": [], "conflicted_files": [],
                 "ledger_error": None, "git_missing": False}
        dirty = {"modified_files": ["core.py"], "untracked_files": [], "conflicted_files": [],
                 "ledger_error": None, "git_missing": False}
        for audit, expected_clean in ((clean, True), (dirty, False)):
            with mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=audit):
                code, out, err = self.run_cli("status", "jsonstatus", "--json")
                payload = json.loads(out)
                self.assertTrue(payload["ok"])
                self.assertEqual(payload["clean"], expected_clean)
                self.assertEqual(payload["project"]["name"], "jsonstatus")
                self.assertEqual(payload["disruption"]["modified_files"],
                                 audit["modified_files"])
                self.assertFalse(payload["ui_task_open"])
                self.assertIsInstance(payload["gates"], list)
                self.assertEqual(err, "")
                self.assertEqual(code, 0, "--json alone stays advisory like plain status")
                exit_code, _, _ = self.run_cli("status", "jsonstatus", "--exit-code")
                self.assertEqual(payload["clean"], exit_code == 0,
                                 "the payload and the exit code must not disagree")

    def test_status_json_honors_exit_code_when_both_flags_are_given(self):
        folder = self.make_folder()
        attach_project(folder, "bothflags", workspace=self.kit)
        dirty = {"modified_files": ["core.py"], "untracked_files": [], "conflicted_files": [],
                 "ledger_error": None, "git_missing": False}
        clean = {"modified_files": [], "untracked_files": [], "conflicted_files": [],
                 "ledger_error": None, "git_missing": False}
        with mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=dirty):
            code, out, err = self.run_cli("status", "bothflags", "--json", "--exit-code")
        self.assertEqual(code, 1, "--exit-code must not be ignored in JSON mode")
        self.assertFalse(json.loads(out)["clean"])
        self.assertEqual(err, "")
        with mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=clean):
            code, out, _ = self.run_cli("status", "bothflags", "--json", "--exit-code")
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(out)["clean"])

    def test_status_treats_a_corrupt_ledger_as_unclean_on_both_surfaces(self):
        folder = self.make_folder()
        attach_project(folder, "corruptledger", workspace=self.kit)
        audit = {"modified_files": [], "untracked_files": [], "conflicted_files": [],
                 "ledger_error": {"found": 2, "supported": 1, "why": "newer schema",
                                  "fix": "use a newer AIKit"},
                 "git_missing": False}
        with mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=audit):
            code, out, err = self.run_cli("status", "corruptledger", "--json")
            payload = json.loads(out)
            self.assertEqual(code, 1)
            self.assertFalse(payload["clean"], "a corrupt ledger is not delivery-ready")
            self.assertEqual(payload["disruption"]["ledger_error"]["found"], 2)
            self.assertEqual(err, "")
            code, _, _ = self.run_cli("status", "corruptledger", "--exit-code")
        self.assertEqual(code, 1, "the text verdict must match the payload")

    def test_status_json_returns_the_error_envelope_for_an_unknown_project(self):
        code, out, err = self.run_cli("status", "nosuchproject", "--json")
        self.assertEqual(code, 2, "an unknown project name is a usage error (PRINCIPLE-011 R5)")
        payload = json.loads(out)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "project.error")
        self.assertIn("nosuchproject", payload["error"]["message"])
        self.assertEqual(err, "")

    def test_resume_json_carries_the_audit_and_the_guidelines_count(self):
        folder = self.make_folder()
        attach_project(folder, "jsonresume", workspace=self.kit)
        audit = {"modified_files": [], "untracked_files": [], "conflicted_files": [],
                 "ledger_error": None, "git_missing": False,
                 "interrupted_task": {"task_id": "t1", "last_phase": "in_progress"}}
        with mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=audit):
            code, out, err = self.run_cli("resume", "jsonresume", "--json")
        self.assertEqual(code, 0)
        payload = json.loads(out)
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["project"]["name"], "jsonresume")
        self.assertEqual(payload["project"]["guidelines"], [])
        add_guideline(folder, "Dates are ISO-8601 strings.", "user")
        with mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=audit):
            _, out, _ = self.run_cli("resume", "jsonresume", "--json")
        rules = json.loads(out)["project"]["guidelines"]
        self.assertEqual(len(rules), 1, "the cold-start payload carries the rules themselves")
        self.assertIn("ISO-8601", rules[0])
        self.assertEqual(payload["disruption"]["interrupted_task"]["task_id"], "t1")
        self.assertEqual(err, "")

    def test_new_public_without_publish_is_a_usage_error(self):
        # ADR-192: `new <name> --public` alone created a local project and ignored the flag.
        code, _, err = self.run_cli("new", "loneflag", "--public")
        self.assertEqual(code, 2)
        self.assertIn("--public needs --publish", err)
        self.assertIn("Fix:", err)
        self.assertFalse((self.kit / "projects" / "loneflag").exists(), "nothing is created")

    def test_aikit_ledger_commands_name_the_agent_and_guard_its_task(self):
        # ADR-209: the project ledger has the same owner rule as AIKit's own.
        attach_project(self.make_folder(), "owned", workspace=self.kit)
        code, _, err = self.run_cli("checkpoint", "owned", "--task", "t", "--phase-num", "1",
                                    "--desc", "start", "--agent", "kilo:1")
        self.assertEqual(code, 0, err)
        code, _, err = self.run_cli("complete", "owned", "--task", "t", "--agent", "gemini:3")
        self.assertEqual(code, 1)
        self.assertIn("belongs to agent 'kilo:1'", err)
        code, _, err = self.run_cli("complete", "owned", "--task", "t", "--agent", "gemini:3", "--take-over")
        self.assertEqual(code, 0, err)
        code, _, err = self.run_cli("checkpoint", "owned", "--task", "u", "--phase-num", "1",
                                    "--desc", "x", "--agent", "bad name")
        self.assertEqual(code, 2)

    def test_new_publish_without_description_is_a_usage_error(self):
        # ADR-205: `new --publish` uploads AIKit's starter files without publish's gates, so it must
        # at least give the repository a description; without one nothing is created.
        with mock.patch("scripts.aikit_cli.publish_project") as publish:
            code, _, err = self.run_cli("new", "nodesc", "--publish")
        self.assertEqual(code, 2)
        self.assertIn("--publish needs --description", err)
        self.assertIn("Fix:", err)
        publish.assert_not_called()
        self.assertFalse((self.kit / "projects" / "nodesc").exists(), "nothing is created")

    def test_check_pushes_only_when_asked(self):
        folder = self.make_folder()
        attach_project(folder, "pushapp", test_command="python -c exit(0)", workspace=self.kit)
        gate_res = mock.MagicMock()
        gate_res.passed = True
        gate_res.gate.name = "test"
        gate_res.seconds = 0.1
        gate_res.gate.source = "detected"
        gate_res.gate.command = "dummy"
        with mock.patch("scripts.aikit_cli.run_gates", return_value=[gate_res]), \
             mock.patch("scripts.aikit_cli.resolve_gates", return_value=[Gate("test", "dummy", "detected")]), \
             mock.patch("scripts.aikit_cli.auto_push_project", return_value=(0, "[OK] Pushed 'pushapp' commits")) as mock_push:
            # 1. Plain check is a verification: it never publishes (ADR-185). It used to push,
            #    so an agent running the documented Phase 4 pushed without authorization.
            code, out, _ = self.run_cli("check", "pushapp")
            self.assertEqual(code, 0)
            mock_push.assert_not_called()

            # 2. --push asks for it, for an agent whose push delivery is authorized.
            code, out, _ = self.run_cli("check", "pushapp", "--push")
            self.assertEqual(code, 0)
            mock_push.assert_called_once()
            self.assertIn("[OK] Pushed 'pushapp' commits", out)

            # 3. --no-push is still accepted, so existing scripts keep running.
            mock_push.reset_mock()
            code, out, _ = self.run_cli("check", "pushapp", "--no-push")
            self.assertEqual(code, 0)
            mock_push.assert_not_called()

        # 5. A requested push the secret scan refuses is a failure, not a warning (ADR-187).
        with mock.patch("scripts.aikit_cli.run_gates", return_value=[gate_res]),              mock.patch("scripts.aikit_cli.resolve_gates", return_value=[Gate("test", "dummy", "detected")]),              mock.patch("scripts.aikit_cli.auto_push_project",
                        return_value=(1, "Error: refused\nWhy: a credential\nFix: rotate")) as refused:
            code, _, err = self.run_cli("check", "pushapp", "--push")
            self.assertEqual(code, 1)
            self.assertIn("Why: a credential", err)
            refused.assert_called_once()

            # 6. fix ends in a check, and before ADR-185 it pushed on every clean run with no way
            #    to opt out; a repair must never publish.
            refused.reset_mock()
            code, _, _ = self.run_cli("fix", "pushapp")
            refused.assert_not_called()

        # 4. Asking for both is a usage error, not a silent choice.
        err = io.StringIO()
        with contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as caught:
            aikit_main(["--workspace", str(self.kit), "check", "pushapp", "--push", "--no-push"])
        self.assertEqual(caught.exception.code, 2)
        self.assertIn("not allowed with", err.getvalue())

    def _gate_result(self):
        gate_res = mock.MagicMock()
        gate_res.passed = True
        gate_res.gate.name = "test"
        gate_res.seconds = 0.1
        gate_res.gate.source = "detected"
        gate_res.gate.command = "dummy"
        return gate_res

    def test_dirty_check_skips_auto_push_and_strict_fails(self):
        folder = self.make_folder(("core.py", "value = 1\n"))
        attach_project(folder, "dirtyapp", test_command="python -c exit(0)", workspace=self.kit)
        dirty_audit = {"modified_files": ["core.py"], "untracked_files": [], "ledger_error": None,
                       "git_missing": False}
        with mock.patch("scripts.aikit_cli.run_gates", return_value=[self._gate_result()]), \
             mock.patch("scripts.aikit_cli.resolve_gates", return_value=[Gate("test", "dummy", "detected")]), \
             mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=dirty_audit), \
             mock.patch("scripts.aikit_cli.auto_push_project", return_value=(0, "")) as push:
            code, out, err = self.run_cli("check", "dirtyapp", "--push")
            self.assertEqual(code, 1, "an explicit push that cannot happen is a failure")
            self.assertIn("[DELIVERY] NOT READY", out)
            self.assertIn("skipping the push", err)
            push.assert_not_called()

            code, out, err = self.run_cli("check", "dirtyapp", "--strict", "--no-push")
            self.assertEqual(code, 1)
            self.assertIn("uncommitted non-bookkeeping changes", out)
            self.assertIn("not delivery-ready", err)

    def test_conflicted_check_skips_auto_push_and_strict_fails(self):
        folder = self.make_folder(("README.md", "# app\n"))
        attach_project(folder, "conflictedapp", test_command="python -c exit(0)", workspace=self.kit)
        conflicted = {"modified_files": [], "untracked_files": [], "conflicted_files": ["UU README.md"],
                      "ledger_error": None, "git_missing": False}
        with mock.patch("scripts.aikit_cli.run_gates", return_value=[self._gate_result()]), \
             mock.patch("scripts.aikit_cli.resolve_gates", return_value=[Gate("test", "dummy", "detected")]), \
             mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=conflicted), \
             mock.patch("scripts.aikit_cli.auto_push_project", return_value=(0, "")) as push:
            code, out, err = self.run_cli("check", "conflictedapp", "--push")
            self.assertEqual(code, 1, "an explicit push that cannot happen is a failure")
            self.assertIn("[DELIVERY] NOT READY", out)
            self.assertIn("1 conflicted", out)
            self.assertIn("skipping the push", err)
            push.assert_not_called()

            code, out, err = self.run_cli("check", "conflictedapp", "--strict", "--no-push")
            self.assertEqual(code, 1)
            self.assertIn("unresolved merge conflicts", out)
            self.assertIn("not delivery-ready", err)

    def test_open_ui_task_check_skips_auto_push_and_strict_fails(self):
        folder = self.make_folder(("README.md", "# app\n"))
        attach_project(folder, "uiopenapp", test_command="python -c exit(0)", workspace=self.kit)
        (folder / ".aikit" / "ui_task.json").write_text("{}", encoding="utf-8")
        clean = {"modified_files": [], "untracked_files": [], "conflicted_files": [],
                 "ledger_error": None, "git_missing": False}
        with mock.patch("scripts.aikit_cli.run_gates", return_value=[self._gate_result()]), \
             mock.patch("scripts.aikit_cli.resolve_gates", return_value=[Gate("test", "dummy", "detected")]), \
             mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=clean), \
             mock.patch("scripts.aikit_cli.auto_push_project", return_value=(0, "")) as push:
            code, out, err = self.run_cli("check", "uiopenapp", "--push")
            self.assertEqual(code, 1, "an explicit push that cannot happen is a failure")
            self.assertIn("[DELIVERY] NOT READY", out)
            self.assertIn("1 open UI task", out)
            self.assertIn("skipping the push", err)
            push.assert_not_called()

            code, out, err = self.run_cli("check", "uiopenapp", "--strict", "--no-push")
            self.assertEqual(code, 1)
            self.assertIn("a UI task is open", out)
            self.assertIn("not delivery-ready", err)

    def test_strict_requires_a_codebase_map(self):
        folder = self.make_folder(("core.py", "value = 1\n"))
        attach_project(folder, "mapapp", test_command="python -c exit(0)", workspace=self.kit)
        clean_audit = {"modified_files": [], "untracked_files": [], "ledger_error": None,
                       "git_missing": False}
        with mock.patch("scripts.aikit_cli.run_gates", return_value=[self._gate_result()]), \
             mock.patch("scripts.aikit_cli.resolve_gates", return_value=[Gate("test", "dummy", "detected")]), \
             mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=clean_audit):
            code, out, _ = self.run_cli("check", "mapapp", "--strict", "--no-push")
            self.assertEqual(code, 1)
            self.assertIn("codebase_map.md is missing", out)

            (folder / ".aikit" / "codebase_map.md").write_text("# map\n", encoding="utf-8")
            code, _, _ = self.run_cli("check", "mapapp", "--strict", "--no-push")
            self.assertEqual(code, 0)

    def test_ui_required_blocks_strict_and_publish_without_a_contract(self):
        folder = self.make_folder()
        attach_project(folder, "uiapp", workspace=self.kit)
        config_path = folder / ".aikit" / "project.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["ui_required"] = True
        config_path.write_text(json.dumps(config), encoding="utf-8")
        clean = {"modified_files": [], "untracked_files": [], "ledger_error": None,
                 "git_missing": False, "conflicted_files": []}
        with mock.patch("scripts.aikit_cli.run_gates", return_value=[self._gate_result()]), \
             mock.patch("scripts.aikit_cli.resolve_gates",
                        return_value=[Gate("test", "dummy", "detected")]), \
             mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=clean), \
             mock.patch("scripts.ui_contract.surface_digest", return_value=""):
            code, out, _ = self.run_cli("check", "uiapp", "--strict", "--no-push")
            self.assertEqual(code, 1)
            self.assertIn("ui_required is true but the UI contract is unusable", out)
            self.assertIn("No UI contract", out)

            (folder / ".aikit" / "ui.json").write_text("{}", encoding="utf-8")
            code, out, _ = self.run_cli("check", "uiapp", "--strict", "--no-push")
            self.assertEqual(code, 1)
            self.assertIn("ui_required is true but the UI contract is unusable", out)
            self.assertIn("schema is not supported", out)

            contract = {"schema": 1, "surfaces": {"menu": {"paths": ["src/**"]}},
                        "commands": {"fast": "exit 0"}}
            (folder / ".aikit" / "ui.json").write_text(json.dumps(contract), encoding="utf-8")
            (folder / ".aikit" / "ui_history.json").write_text(json.dumps([
                {"surface": "menu", "surface_digest": ""},
            ]), encoding="utf-8")
            code, _, _ = self.run_cli("check", "uiapp", "--strict", "--no-push")
            self.assertEqual(code, 0)

        with mock.patch("scripts.aikit_cli.run_gates", return_value=[self._gate_result()]), \
             mock.patch("scripts.aikit_cli.resolve_gates",
                        return_value=[Gate("test", "dummy", "detected")]), \
             mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=clean), \
             mock.patch("scripts.ui_contract.surface_digest", return_value=""), \
             mock.patch("scripts.aikit_cli.publish_project",
                        return_value=(0, "[OK] Published")) as publish:
            code, _, _ = self.run_cli("publish", "uiapp")
        self.assertEqual(code, 0)
        publish.assert_called_once()
        # ADR-200: a project.json without topics, from before ADR-199, still gets `aikit`.
        self.assertEqual(publish.call_args.kwargs["topics"], ["aikit"])
        self.assertNotIn("description", publish.call_args.kwargs)

        failed = self._gate_result()
        failed.passed = False
        failed.output = "boom"
        with mock.patch("scripts.aikit_cli.run_gates", return_value=[failed]), \
             mock.patch("scripts.aikit_cli.resolve_gates",
                        return_value=[Gate("test", "dummy", "detected")]), \
             mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=clean), \
             mock.patch("scripts.ui_contract.surface_digest", return_value=""), \
             mock.patch("scripts.aikit_cli.publish_project",
                        return_value=(0, "[OK] Published")) as publish:
            code, _, err = self.run_cli("publish", "uiapp")
        self.assertEqual(code, 1)
        self.assertIn("gates failed", err)
        publish.assert_not_called()

        (folder / ".aikit" / "ui.json").unlink()
        with mock.patch("scripts.aikit_cli.run_gates", return_value=[self._gate_result()]), \
             mock.patch("scripts.aikit_cli.resolve_gates",
                        return_value=[Gate("test", "dummy", "detected")]), \
             mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=clean), \
             mock.patch("scripts.aikit_cli.auto_push_project", return_value=(0, "")) as push:
            code, out, _ = self.run_cli("check", "uiapp")
            self.assertEqual(code, 0)
            self.assertIn("UI contract not delivery-ready", out)
            push.assert_not_called()

        with mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=clean), \
             mock.patch("scripts.aikit_cli.publish_project",
                        return_value=(0, "[OK] Published")) as publish:
            code, _, err = self.run_cli("publish", "uiapp")
        self.assertEqual(code, 1)
        self.assertIn("ui_required is true but the UI contract is unusable", err)
        publish.assert_not_called()

    def test_ui_verify_json_emits_stable_codes(self):
        folder = self.make_folder()
        attach_project(folder, "jsonapp", workspace=self.kit)
        message = "style literal '#fff' outside theme paths: src/ui/menu.py:1"
        with mock.patch("scripts.aikit_cli.ui_contract.verify", return_value=[message]), \
             mock.patch("scripts.aikit_cli.ui_contract.read_task",
                        return_value={"surface": "menu"}), \
             mock.patch("scripts.aikit_cli.ui_contract.load_contract",
                        return_value=mock.Mock(theme_paths=())):
            code, out, err = self.run_cli("ui", "verify", "jsonapp", "--json")
        self.assertEqual(code, 1)
        payload = json.loads(out)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["surface"], "menu")
        self.assertEqual(payload["style_lint"], "off")
        self.assertEqual(payload["findings"],
                         [{"code": "ui.style-literal", "message": message}])
        self.assertEqual(err, "")

    def test_ui_init_writes_the_react_vite_pilot_contract(self):
        folder = self.make_folder(
            ("package.json", json.dumps({
                "dependencies": {"react": "^18", "vite": "^5"},
                "scripts": {"build": "vite build"},
            })),
        )
        (folder / "src").mkdir()
        (folder / "src" / "main.tsx").write_text("export {};\n", encoding="utf-8")
        attach_project(folder, "initapp", workspace=self.kit)
        code, out, _ = self.run_cli("ui", "init", "initapp", "--surface", "menu")
        self.assertEqual(code, 0)
        self.assertIn("Wrote .aikit/ui.json", out)
        contract = json.loads((folder / ".aikit" / "ui.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["surfaces"]["menu"]["paths"], ["src/**"])
        self.assertEqual(contract["commands"]["fast"], "npm run build")

    def test_ui_evidence_and_json_error_paths(self):
        folder = self.make_folder()
        attach_project(folder, "evidenceapp", workspace=self.kit)
        config_path = folder / ".aikit" / "project.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["ui_required"] = True
        config_path.write_text(json.dumps(config), encoding="utf-8")
        contract = {"schema": 1, "surfaces": {"menu": {"paths": ["src/**"]}},
                    "commands": {"fast": "exit 0"}}
        (folder / ".aikit" / "ui.json").write_text(json.dumps(contract), encoding="utf-8")
        clean = {"modified_files": [], "untracked_files": [], "ledger_error": None,
                 "git_missing": False, "conflicted_files": []}
        with mock.patch("scripts.aikit_cli.run_gates", return_value=[self._gate_result()]), \
             mock.patch("scripts.aikit_cli.resolve_gates",
                        return_value=[Gate("test", "dummy", "detected")]), \
             mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=clean), \
             mock.patch("scripts.ui_contract.surface_digest", return_value="digest"):
            code, out, _ = self.run_cli("check", "evidenceapp", "--strict", "--no-push")
            self.assertEqual(code, 1)
            self.assertIn("UI surface 'menu' has no finished UI task", out)
            (folder / ".aikit" / "ui_history.json").write_text(json.dumps([
                {"surface": "menu", "surface_digest": "digest"},
            ]), encoding="utf-8")
            code, _, _ = self.run_cli("check", "evidenceapp", "--strict", "--no-push")
            self.assertEqual(code, 0)

        config["ui_required"] = False
        config_path.write_text(json.dumps(config), encoding="utf-8")
        (folder / ".aikit" / "ui.json").write_text("{}", encoding="utf-8")
        with mock.patch("scripts.aikit_cli.run_gates", return_value=[self._gate_result()]), \
             mock.patch("scripts.aikit_cli.resolve_gates",
                        return_value=[Gate("test", "dummy", "detected")]), \
             mock.patch("scripts.aikit_cli.run_disruption_audit", return_value=clean):
            code, out, _ = self.run_cli("check", "evidenceapp", "--strict", "--no-push")
            self.assertEqual(code, 1)
            self.assertIn("the UI contract is unusable", out)

        (folder / ".aikit" / "ui.json").unlink()
        code, out, err = self.run_cli("ui", "verify", "evidenceapp", "--json")
        self.assertEqual(code, 2)
        payload = json.loads(out)
        self.assertFalse(payload["ok"])
        self.assertEqual(payload["error"]["code"], "ui.error")
        self.assertIn("No UI contract", payload["error"]["message"])
        self.assertEqual(err, "")

    def test_ui_finish_blocked_only_by_review_says_so_and_offers_no_revert(self):
        # finish() returns the review finding only when verify() found nothing, so "outside its
        # contract" was false in exactly this case, and its first remedy (abort) reverts the work.
        folder = self.make_folder()
        attach_project(folder, "reviewapp", workspace=self.kit)
        review = "human review not recorded: no one confirmed the running UI looks right."
        with mock.patch("scripts.aikit_cli.ui_contract.finish", return_value=[review]), \
             mock.patch("scripts.aikit_cli.ui_contract.read_task", return_value={}):
            code, out, err = self.run_cli("ui", "finish", "reviewapp")
        self.assertEqual(code, 1, "an unreviewed task still must not close")
        self.assertIn(f"[FAIL] {review}", out)
        self.assertIn("passed verification", err)
        self.assertIn("ui finish reviewapp --reviewed", err)
        for misleading in ("outside its contract", "abort", "revert", "ui allow"):
            self.assertNotIn(misleading, err, f"review-only failure still says '{misleading}'")

    def test_ui_finish_with_a_contract_finding_keeps_the_contract_advice(self):
        folder = self.make_folder()
        attach_project(folder, "contractapp", workspace=self.kit)
        violation = "out-of-surface edit: src/other.py"
        with mock.patch("scripts.aikit_cli.ui_contract.finish", return_value=[violation]), \
             mock.patch("scripts.aikit_cli.ui_contract.read_task", return_value={}):
            code, _, err = self.run_cli("ui", "finish", "contractapp", "--reviewed")
        self.assertEqual(code, 1)
        self.assertIn("outside its contract", err)
        self.assertIn("ui abort contractapp", err)

    def test_ui_finish_prints_every_allowed_removal_and_its_reason(self):
        folder = self.make_folder()
        attach_project(folder, "reasonapp", workspace=self.kit)
        task = {"surface": "menu",
                "allowed_removals": [{"pattern": "Button*", "reason": "replaced by the toolbar"}]}
        with mock.patch("scripts.aikit_cli.ui_contract.finish", return_value=[]), \
             mock.patch("scripts.aikit_cli.ui_contract.read_task", return_value=task):
            code, out, err = self.run_cli("ui", "finish", "reasonapp", "--reviewed")
        self.assertEqual(code, 0)
        self.assertIn("allowed removal 'Button*': replaced by the toolbar", out)
        self.assertEqual(err, "")

    def test_ui_init_generic_override_from_cli(self):
        folder = self.make_folder()
        attach_project(folder, "genericapp", workspace=self.kit)
        code, _, _ = self.run_cli("ui", "init", "genericapp", "--fast", "exit 0",
                                  "--paths", "app/**")
        self.assertEqual(code, 0)
        contract = json.loads((folder / ".aikit" / "ui.json").read_text(encoding="utf-8"))
        self.assertEqual(contract["surfaces"]["app"]["paths"], ["app/**"])
        self.assertEqual(contract["commands"]["fast"], "exit 0")

    def test_rendered_readme_uses_a_project_test_command(self):
        self.assertIn("<FILL: the command that runs the whole test suite",
                      render_project_readme("app"))
        self.assertIn("python -m unittest discover",
                      render_project_readme("app", "python -m unittest discover"))

    def test_run_git_uses_utf8_encoding_with_replacement(self):
        folder = self.make_folder()
        with mock.patch("subprocess.run") as mock_run:
            mock_run.return_value = subprocess.CompletedProcess(["git", "status"], 0, "clean", "")
            _run_git(folder, "status")
            mock_run.assert_called_once_with(
                ["git", "status"],
                cwd=folder,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=mock.ANY,
            )



class TestProjectGates(unittest.TestCase):
    """A project's Phase 4 is the gates its own config declares, plus the secret scan (ADR-122)."""

    def setUp(self):
        self.kit = Path(tempfile.mkdtemp(prefix="test_gates_kit_"))
        self.addCleanup(shutil.rmtree, self.kit, ignore_errors=True)
        self.created = []

    def project(self, files, gates=None):
        # A folder under projects/ with a project.json is a project (discovery, ADR-119); writing
        # the record directly keeps the registry's locked writes out of these gate tests.
        name = f"app{len(self.created)}"
        self.created.append(name)
        folder = self.kit / "projects" / name
        (folder / ".aikit").mkdir(parents=True)
        for file_name, text in files:
            (folder / file_name).write_text(text, encoding="utf-8")
        record = {"schema": 1, "name": name, "test_command": None, "gates": gates or {}}
        (folder / ".aikit" / "project.json").write_text(json.dumps(record), encoding="utf-8")
        return find_project(name, self.kit)

    def names(self, project):
        return [(gate.name, gate.command) for gate in resolve_gates(project) if gate.source != "built-in"]

    def test_gates_come_only_from_the_projects_own_config(self):
        bare = self.project([("requirements.txt", "")])
        self.assertEqual(self.names(bare), [("test", "python -m unittest discover")])
        configured = self.project([("pyproject.toml", "[tool.ruff]\n[tool.mypy]\n[tool.pytest.ini_options]\n")])
        self.assertEqual(self.names(configured), [("test", "python -m pytest"), ("lint", "python -m ruff check ."),
                                                  ("typecheck", "python -m mypy .")])
        node = self.project([("package.json", '{"scripts": {"test": "jest", "lint": "eslint .", "build": "tsc"}}'),
                             ("yarn.lock", "")])
        self.assertEqual(self.names(node), [("test", "yarn test"), ("lint", "yarn run lint"),
                                            ("build", "yarn run build")])

    def test_built_in_scans_are_always_present_and_last(self):
        gates = resolve_gates(self.project([("go.mod", "module x\n")]))
        self.assertEqual([gate.name for gate in gates],
                         ["test", "vet", "hygiene", "guidelines", "secrets"])
        self.assertIn("check_project_hygiene.py", gates[-3].command)
        self.assertIn("--workspace", gates[-3].command)
        self.assertIn("update_knowledge_base.py", gates[-2].command)
        self.assertIn("--workspace", gates[-2].command)
        self.assertIn("--check", gates[-2].command)
        self.assertIn("check_secrets.py", gates[-1].command)
        self.assertIn("--workspace", gates[-1].command)

    def test_project_json_adds_replaces_and_disables_gates(self):
        project = self.project([("go.mod", "module x\n")],
                               gates={"vet": None, "test": "make test", "e2e": "make e2e"})
        self.assertEqual(self.names(project), [("test", "make test"), ("e2e", "make e2e")])
        self.assertEqual(resolve_gates(project)[1].source, "project.json")

    def test_invalid_gate_config_is_refused(self):
        for gates in ({"secrets": None}, {"guidelines": None}, {"hygiene": None}, {"lint": 3},
                      {"lint": " "}, ["lint"]):
            with self.subTest(gates=gates), self.assertRaises(ProjectError):
                resolve_gates(self.project([("go.mod", "")], gates=gates))

    def test_every_gate_runs_after_a_failure(self):
        gates = [Gate("a", "fail", "t"), Gate("b", "pass", "t")]
        calls = []

        def runner(command, cwd, timeout):
            calls.append(command)
            return (1, "x\n\nerror: broken\n") if command == "fail" else (0, "")
        results = run_gates(Path("."), gates, runner=runner)
        self.assertEqual(calls, ["fail", "pass"])
        self.assertEqual([r.passed for r in results], [False, True])
        self.assertEqual(failure_tail(results[0].output), ["x", "error: broken"])

class TestProjectHygieneScan(unittest.TestCase):
    """The hygiene scan decides from the AST and from lines what the project gates could not (ADR-137)."""

    def rules(self, source):
        return {finding.rule for finding in check_python_source("app.py", source)}

    def test_allow_marker_is_read_on_the_line_above_the_finding(self):
        above = ("import os\n"
                 "# hygiene: allow the launcher documents its required variable\n"
                 "token = os.environ['TOKEN']\n")
        self.assertEqual(self.rules(above), set())
        stale = ("# hygiene: allow the launcher documents its required variable\n"
                 "import os\n"
                 "token = os.environ['TOKEN']\n")
        self.assertEqual(self.rules(stale), {"environ-index"})

    def test_subprocess_rules_are_decidable(self):
        self.assertEqual(self.rules("import subprocess\nsubprocess.run('x', shell=True, timeout=1)\n"),
                         {"shell-true", "subprocess-argv"})
        self.assertEqual(self.rules("import subprocess\nsubprocess.run(['python', 'x.py'], timeout=1)\n"),
                         {"sys-executable"})
        self.assertEqual(self.rules("import subprocess, sys\nsubprocess.run([sys.executable, 'x.py'])\n"),
                         {"subprocess-timeout"})
        # Popen has no timeout= parameter; it needs a bounded wait/communicate instead.
        popen = "subprocess." + "Popen"
        self.assertEqual(self.rules("import subprocess, sys\n" + popen + "([sys.executable, 'x.py'])\n"),
                         {"popen-wait-timeout"})
        self.assertEqual(self.rules("import subprocess\np = " + popen + "(['x'])\np.wait(timeout=5)\n"),
                         set())
        self.assertEqual(self.rules("import subprocess\np = " + popen + "(['x'])\np.wait()\n"),
                         {"popen-wait-timeout"})
        self.assertEqual(self.rules("import subprocess\nwith " + popen
                                    + "(['x']) as p:\n    p.communicate(timeout=5)\n"), set())
        self.assertEqual(self.rules("import subprocess\n" + popen
                                    + "(['x']).wait(timeout=5)\n"), set())
        self.assertEqual(self.rules(
            "import subprocess\n"
            "def spawn():\n"
            "    p = " + popen + "(['x'])\n"
            "    p.wait()\n"
            "def unrelated():\n"
            "    p.wait(timeout=1)\n"), {"popen-wait-timeout"})
        self.assertEqual(self.rules("from subprocess import Popen as P\np = P(['python', 'x.py'])\n"
                                    "p.wait(timeout=5)\n"), {"sys-executable"})
        self.assertEqual(self.rules("import os\nos.system('x')\n"), {"os-system"})
        self.assertEqual(self.rules("eval('1')\n"), {"eval-exec"})

    def test_only_imported_subprocess_names_count(self):
        self.assertEqual(self.rules("from subprocess import run\nrun('x', timeout=1)\n"),
                         {"subprocess-argv"})
        self.assertEqual(self.rules("def run(cmd):\n    return cmd\nrun('x')\n"), set())

    def test_startup_and_file_rules(self):
        self.assertEqual(self.rules("import os\nos.environ['HOME']\n"), {"environ-index"})
        self.assertEqual(self.rules("open('x')\n"), {"open-encoding", "open-context"})
        self.assertEqual(self.rules("import os\nos.open('x', os.O_RDONLY)\n"), set())
        self.assertEqual(self.rules("with open('x', 'rb') as handle:\n    handle.read()\n"), set())
        self.assertEqual(self.rules("try:\n    pass\nexcept Exception:\n    pass\n"),
                         {"silent-except"})

    def test_any_handler_that_only_discards_is_flagged(self):
        # ADR-147: the gate passed `except OSError: pass`, the commonest way a real failure is
        # thrown away; this assertion previously required it to pass (PRINCIPLE-014 R2).
        for body in ("pass", "return", "continue", "break"):
            loop = "for x in []:\n    try:\n        pass\n    except OSError:\n        %s\n" % body
            with self.subTest(typed=body):
                expected = {"silent-except"} if body == "pass" else set()
                self.assertEqual(self.rules(loop), expected)
            broad = loop.replace("except OSError", "except Exception")
            with self.subTest(broad=body):
                self.assertEqual(self.rules(broad), {"silent-except"})
        # A reason on the handler's own line is the documented exception; it needs real words.
        self.assertEqual(self.rules("try:\n    pass\nexcept OSError:  # hygiene: allow best effort\n    pass\n"),
                         set())
        self.assertEqual(self.rules("try:\n    pass\nexcept OSError:  # hygiene: allow no\n    pass\n"),
                         {"silent-except"})
        # A handler that acts is never silent, however broad it is.
        self.assertEqual(self.rules("try:\n    pass\nexcept Exception:\n    return report()\n"), set())

    def test_absolute_paths_only_when_they_reach_file_access(self):
        self.assertEqual(self.rules('with open("C:/Users/me/x.txt", encoding="utf-8") as f:\n    f.read()\n'),
                         {"absolute-path"})
        self.assertEqual(self.rules('VirtualFile(path="/etc/hosts", size_kb=1)\n'), set())
        self.assertEqual(self.rules('"""Docs may name C:/Users/me."""\n'), set())

    def test_inline_allow_marker_needs_a_reason(self):
        self.assertEqual(self.rules("import os\nos.system('x')  # hygiene: allow bootstrapper\n"), set())
        self.assertEqual(self.rules("import os\nos.system('x')  # hygiene: allow x\n"), {"os-system"})

    def test_asset_urls_skip_loopback_namespaces_and_marked_lines(self):
        local = '<script src="http://localhost:8000/app.js"></script>\n'
        namespace = '<svg xmlns="http://www.w3.org/2000/svg"></svg>\n'
        marked = '<link href="https://fonts.example/x.css"> <!-- hygiene: allow fonts until vendored -->\n'
        remote = '<link href="https://fonts.example/x.css">\n'
        self.assertEqual({f.rule for f in check_asset_source("ui/index.html", local)}, set())
        self.assertEqual({f.rule for f in check_asset_source("ui/index.html", namespace)}, set())
        self.assertEqual({f.rule for f in check_asset_source("ui/index.html", marked)}, set())
        self.assertEqual({f.rule for f in check_asset_source("ui/index.html", remote)}, {"external-url"})

    def test_scan_tree_skips_vendored_dirs_and_reports_unreadable_files(self):
        root = Path(tempfile.mkdtemp(prefix="test_hygiene_"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        (root / "app.py").write_text("import os\nos.system('x')\n", encoding="utf-8")
        (root / "bin.py").write_bytes(b"\xff\xfe\x00def x(): pass\n")
        (root / "broken.py").write_text("def broken(:\n", encoding="utf-8")
        (root / "node_modules").mkdir()
        (root / "node_modules" / "vendored.js").write_text(
            "fetch('https://cdn.example/x.js')\n", encoding="utf-8")
        self.assertEqual([(finding.path, finding.rule) for finding in scan_tree(root)],
                         [("app.py", "os-system"), ("bin.py", "unreadable"),
                          ("broken.py", "unparseable")])

    def test_artifact_classifier_flags_root_tests_outputs_and_source(self):
        findings = classify_artifacts(
            tracked=["app/core.py", "tests/test_core.py", "tests.py", "TestFoo.py"],
            untracked=["test_features.py", "testfoo.py", "review_rules.py", "test_output.txt",
                       "app.js", "site.css", "docs/notes.txt", "README.md"],
        )
        pairs = {(finding.path, finding.rule) for finding in findings}
        self.assertEqual(pairs, {
            ("tests.py", "root-test-module"),
            ("TestFoo.py", "root-test-module"),
            ("test_features.py", "root-test-module"),
            ("testfoo.py", "root-test-module"),
            ("review_rules.py", "untracked-root-source"),
            ("app.js", "untracked-root-source"),
            ("site.css", "untracked-root-source"),
            ("test_output.txt", "untracked-output"),
            ("README.md", "untracked-readme"),
        })

    def test_artifact_scan_reports_missing_git_without_a_traceback(self):
        root = Path(tempfile.mkdtemp(prefix="test_hygiene_no_git_"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        with mock.patch("scripts.check_project_hygiene.subprocess.run",
                        side_effect=OSError("git vanished")):
            findings = scan_artifacts(root)
        self.assertEqual([(finding.path, finding.rule) for finding in findings],
                         [(".", "git-unavailable")])

    def test_artifact_classifier_flags_tracked_caches_and_temporary_state(self):
        findings = classify_artifacts(
            tracked=["__pycache__/core.pyc", "build/app.zip", "pkg.egg-info/PKG-INFO",
                     ".coverage", ".aikit/state.json.tmp_1", ".aikit/task_ledger.json"],
            untracked=[],
        )
        pairs = {(finding.path, finding.rule) for finding in findings}
        self.assertEqual(pairs, {
            ("__pycache__/core.pyc", "tracked-artifact"),
            ("build/app.zip", "tracked-artifact"),
            ("pkg.egg-info/PKG-INFO", "tracked-artifact"),
            (".coverage", "tracked-artifact"),
            (".aikit/state.json.tmp_1", "tracked-artifact"),
        })

    def test_artifact_classifier_flags_an_untracked_project_readme(self):
        findings = classify_artifacts(
            tracked=[],
            untracked=["README.md", "README.txt", "docs/README.md", "NOTES.md"],
        )
        self.assertEqual([(finding.path, finding.rule) for finding in findings],
                         [("README.md", "untracked-readme"),
                          ("README.txt", "untracked-readme")])

    def test_artifact_classifier_keeps_bookkeeping_and_normal_source(self):
        findings = classify_artifacts(
            tracked=[".aikit/task_ledger.json", ".aikit/decisions.md", "app/core.py",
                     "tests/test_core.py", "docs/guide.txt"],
            untracked=["examples/demo.py", "tests/test_new.py"],
        )
        self.assertEqual(findings, [])

class TestGateCommandsHaveOneLine(unittest.TestCase):
    """
    Windows `cmd /c` runs only the first line of a command, so `exit 0\\nexit 7` reported success
    there while /bin/sh returned 7. A command with a line break inside is refused on every
    platform, before any process starts (ADR-183).
    """

    def test_a_nul_inside_a_command_is_refused_instead_of_crashing(self):
        # A JSON "\u0000" escape decodes to NUL, and Popen raised an uncaught ValueError on it,
        # so `aikit check` ended in a traceback (ADR-189).
        from scripts.project_gates import run_shell
        code, output = run_shell("pytest" + chr(0) + "x", ROOT_DIR, 5)
        self.assertEqual(code, -1)
        self.assertIn("NUL", output)

    def test_a_line_break_inside_a_command_is_refused_without_running_it(self):
        from scripts.project_gates import run_shell
        for command in ("exit 0\nexit 7", "pytest\r\nflake8", "echo a\recho b"):
            with self.subTest(command=command):
                code, output = run_shell(command, ROOT_DIR, 5)
                self.assertEqual(code, -1, "a refused command is a failed gate, never a pass")
                self.assertIn("line break", output)
                self.assertIn("&&", output, "the refusal says how to join the steps")


class TestAnnotationsResolveOnEverySupportedPython(unittest.TestCase):
    """
    Python 3.14 evaluates annotations only when they are read (PEP 649); Python 3.10 to 3.13,
    which README and CI support, evaluate them when `def` runs. An annotation naming something
    never imported therefore passes every test on 3.14 and makes the module unimportable on the
    rest. `aikit_cli` shipped exactly that (`Dict`, ADR-181), and CI could not catch it. Reading
    every `__annotations__` here forces the older, eager evaluation on any interpreter.
    """

    def test_every_annotation_in_scripts_names_something_defined(self):
        import importlib
        import inspect
        unresolved = []
        for path in sorted((ROOT_DIR / "scripts").glob("*.py")):
            if path.stem.startswith("_"):
                continue
            module = importlib.import_module(f"scripts.{path.stem}")
            # Module-level annotations (`TABLE: Dict[str, int] = {}`) are deferred on 3.14 too and
            # evaluated at import on 3.10-3.13; reading them here covers that case (ADR-188).
            try:
                module.__annotations__
            except NameError as error:
                unresolved.append(f"{module.__name__} (module level): {error}")
            for obj in list(vars(module).values()):
                if getattr(obj, "__module__", None) != module.__name__:
                    continue
                owners = [obj]
                if inspect.isclass(obj):
                    owners += [member for member in vars(obj).values() if inspect.isfunction(member)]
                for owner in owners:
                    if inspect.isfunction(owner) or inspect.isclass(owner):
                        try:
                            owner.__annotations__
                        except NameError as error:
                            unresolved.append(f"{module.__name__}.{owner.__qualname__}: {error}")
        self.assertEqual(unresolved, [], "these annotations break import on Python 3.10-3.13")


class TestFstringsParseOnPython310(unittest.TestCase):
    """
    Since 3.12 (PEP 701) an f-string may reuse its own quote, or hold a backslash or `#`, inside
    `{}`; each is a SyntaxError on 3.10 and 3.11. The AST gate parses with feature_version=(3, 10)
    but on a newer interpreter it accepts quote reuse, so this check reads the source (ADR-188).
    """

    @staticmethod
    def rejected_on_310(src):
        # Lines split once, sliced by the AST's UTF-8 byte offsets: ast.get_source_segment
        # re-splits the whole source on every call, which took ~2s over this repository's tests.
        lines = [line.encode("utf-8") for line in src.splitlines(keepends=True)]

        def segment(node):
            if node.lineno == node.end_lineno:
                return lines[node.lineno - 1][node.col_offset:node.end_col_offset].decode("utf-8")
            return (lines[node.lineno - 1][node.col_offset:]
                    + b"".join(lines[node.lineno:node.end_lineno - 1])
                    + lines[node.end_lineno - 1][:node.end_col_offset]).decode("utf-8")

        found = []
        for node in ast.walk(ast.parse(src)):
            if not isinstance(node, ast.JoinedStr):
                continue
            match = re.match(r"[rRbBuUfF]*('''|\"\"\"|'|\")", segment(node))
            if not match:
                continue
            quote = match.group(1)
            for value in node.values:
                if isinstance(value, ast.FormattedValue):
                    expr = segment(value.value)
                    if (len(quote) == 1 and quote in expr) or chr(92) in expr or "#" in expr:
                        found.append(f"{value.lineno}: {{{expr}}}")
        return found

    def test_the_check_flags_what_310_rejects_and_nothing_it_accepts(self):
        q, bs = chr(34), chr(92)
        bad = (f"a = f{q}{{x[{q}k{q}]}}{q}\n"                       # f"{x["k"]}"
               f"b = f{q}{{{q}{bs}n{q}.join(y)}}{q}\n")              # f"{"\n".join(y)}"
        good = f"c = f{q}{{x['k']}}{q}\n"                             # f"{x['k']}"
        self.assertEqual(len(self.rejected_on_310(bad)), 2)
        self.assertEqual(self.rejected_on_310(good), [])

    def test_no_fstring_in_aikit_needs_python_312(self):
        files = sorted((ROOT_DIR / "scripts").glob("*.py")) + sorted((ROOT_DIR / "tests").glob("*.py"))
        found = [f"{path.name}:{hit}" for path in files + [ROOT_DIR / "aikit.py"]
                 for hit in self.rejected_on_310(path.read_text(encoding="utf-8"))]
        self.assertEqual(found, [], "these f-strings are SyntaxErrors on Python 3.10 and 3.11")


class TestAikitHelpFastPath(unittest.TestCase):
    """
    `python aikit.py --help` parses with scripts/aikit_parser.py alone, so it must stay light
    and agree with the modules it mirrors instead of importing them (ADR-180).
    """

    def test_parser_constants_match_the_modules_they_mirror(self):
        import scripts.aikit_parser as grammar
        import scripts.disruption_recovery as ledger
        self.assertEqual(grammar.ROOT_DIR, ledger.ROOT_DIR)
        self.assertEqual(grammar.TEMP_STALE_SECONDS, ledger.TEMP_STALE_SECONDS)

    def test_parser_module_imports_only_the_standard_library_at_top_level(self):
        # One AIKit import here would make every `--help` load the whole graph again, silently.
        tree = ast.parse((ROOT_DIR / "scripts" / "aikit_parser.py").read_text(encoding="utf-8"))
        top = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
        names = [alias.name for node in top if isinstance(node, ast.Import) for alias in node.names]
        names += [node.module for node in top if isinstance(node, ast.ImportFrom)]
        self.assertTrue(names, "expected the parser module to import argparse at least")
        self.assertEqual([name for name in names if name.split(".")[0] == "scripts"], [])

    def test_cli_reexports_the_parser_so_existing_callers_keep_working(self):
        import scripts.aikit_cli as cli
        import scripts.aikit_parser as grammar
        self.assertIs(cli.build_parser, grammar.build_parser)
        self.assertIs(cli.report_error, grammar.report_error)
        self.assertIs(cli.TriadArgumentParser, grammar.TriadArgumentParser)


class FakeGit:
    """A tiny git_io stand-in for the UI guard's unit tests; no subprocess is spawned."""

    def __init__(self, status="", head="a" * 40, tracked=(), diff=""):
        self.status = status
        self.head = head
        self.tracked = tuple(tracked)
        self.diff = diff

    def __call__(self, root, args):
        command = args[0]
        if command == "status":
            return 0, self.status, ""
        if command == "rev-parse":
            return 0, self.head + "\n", ""
        if command == "ls-files":
            return 0, "".join(path + "\0" for path in self.tracked), ""
        if command == "diff":
            return 0, self.diff, ""
        return 0, "", ""


class TestUiContract(unittest.TestCase):
    """The UI guard's decidable parts: patterns, porcelain, contract loading and task records."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="test_ui_contract_"))
        self.addCleanup(shutil.rmtree, self.root, ignore_errors=True)
        (self.root / ".aikit").mkdir()

    def write_contract(self, **overrides):
        contract = {"schema": 1, "surfaces": {"menu": {"paths": ["src/ui/**"]}},
                    "protected": ["tests/**"], "commands": {"fast": "python -c pass"},
                    "limits": {"max_files": 2, "max_lines": 20}}
        contract.update(overrides)
        (self.root / ".aikit" / "ui.json").write_text(json.dumps(contract), encoding="utf-8")

    def test_patterns_scope_surfaces_and_protected_paths(self):
        self.assertTrue(ui_contract._matches("src/ui/Menu.ts", ("src/ui/**",)))
        self.assertFalse(ui_contract._matches("src/ui2/Menu.ts", ("src/ui/**",)))
        self.assertTrue(ui_contract._matches("tests/ui/menu.test.ts", ("tests/**",)))
        self.assertFalse(ui_contract._matches("src/App.ts", ("src/ui/**",)))

    def test_finding_codes_are_stable(self):
        message = "style literal '#fff' outside theme paths: src/ui/menu.py:1"
        self.assertEqual(ui_contract.finding_code(message), "ui.style-literal")
        self.assertEqual(ui_contract.finding_code("path outside surface 'menu': src/x"),
                         "ui.outside-surface")
        self.assertEqual(ui_contract.finding_code("unexpected prose"), "ui.other")
        self.assertEqual(ui_contract.findings_payload([message]),
                         [{"code": "ui.style-literal", "message": message}])

    def test_scaffold_generic_override_skips_stack_detection(self):
        contract = ui_contract.scaffold_contract(self.root, "app", fast="exit 0",
                                                 paths=["app/**"])
        self.assertEqual(contract["surfaces"]["app"], {"paths": ["app/**"]})
        self.assertEqual(contract["commands"]["fast"], "exit 0")
        self.assertEqual(ui_contract.load_contract(self.root).surfaces["app"], ("app/**",))

    def test_scaffold_writes_a_valid_react_vite_contract(self):
        (self.root / "src").mkdir()
        (self.root / "package.json").write_text(json.dumps({
            "peerDependencies": {"react": "^18", "vite": "^5", "vitest": "^1"},
            "scripts": {"test": "vitest", "build": "vite build"},
        }), encoding="utf-8")
        contract = ui_contract.scaffold_contract(self.root, "menu")
        self.assertEqual(contract["surfaces"]["menu"], {"paths": ["src/**"]})
        self.assertEqual(contract["commands"]["fast"], "npm run test -- --run")
        self.assertIn("src/**/__tests__/**", contract["protected"])
        self.assertEqual(ui_contract.load_contract(self.root).surfaces["menu"], ("src/**",))
        with self.assertRaises(ProjectError):
            ui_contract.scaffold_contract(self.root, "menu")

    def test_empty_surface_still_requires_evidence(self):
        self.write_contract()

        def fake_git(root, args):
            return 0, "", ""

        self.assertTrue(ui_contract.surface_evidence_errors(self.root, fake_git))
        (self.root / ".aikit" / "ui_history.json").write_text(json.dumps([
            {"surface": "menu", "surface_digest": ""},
        ]), encoding="utf-8")
        self.assertEqual(ui_contract.surface_evidence_errors(self.root, fake_git), [])

    def test_surface_evidence_requires_a_matching_finished_task(self):
        self.write_contract()
        (self.root / "src" / "ui").mkdir(parents=True)
        target = self.root / "src" / "ui" / "menu.py"
        target.write_text("value = 1\n", encoding="utf-8")

        def fake_git(root, args):
            if args[0] == "ls-files":
                return 0, "src/ui/menu.py\0", ""
            if args[0] == "status":
                return 0, "", ""
            return 0, "", ""

        digest = ui_contract.surface_digest(self.root, ("src/ui/**",), fake_git)
        self.assertTrue(digest)
        errors = ui_contract.surface_evidence_errors(self.root, fake_git)
        self.assertEqual(len(errors), 1)
        self.assertIn("no finished UI task", errors[0])
        (self.root / ".aikit" / "ui_history.json").write_text(json.dumps([
            {"surface": "menu", "surface_digest": digest},
        ]), encoding="utf-8")
        self.assertEqual(ui_contract.surface_evidence_errors(self.root, fake_git), [])
        target.write_text("value = 2\n", encoding="utf-8")
        self.assertTrue(ui_contract.surface_evidence_errors(self.root, fake_git))

    def test_scaffold_refuses_a_non_react_stack(self):
        (self.root / "src").mkdir()
        (self.root / "package.json").write_text(json.dumps({
            "dependencies": {"vue": "^3"}, "scripts": {"build": "vite build"},
        }), encoding="utf-8")
        with self.assertRaises(ProjectError):
            ui_contract.scaffold_contract(self.root)

    def test_porcelain_renames_expand_and_bookkeeping_is_ignored(self):
        changes = ui_contract.parse_status(
            "R  src/ui/new.ts\0src/ui/old.ts\0 M .aikit/ui_task.json\0?? notes.md\0")
        self.assertEqual(changes, [("R ", "src/ui/new.ts"), ("R ", "src/ui/old.ts"),
                                   (" M", ".aikit/ui_task.json"), ("??", "notes.md")])
        self.assertTrue(ui_contract._is_bookkeeping(".aikit/ui_task.json"))
        self.assertTrue(ui_contract._is_bookkeeping(".aikit/ui_history.json"))

    def test_contract_accepts_a_utf8_bom_from_windows_editors(self):
        contract = {"schema": 1, "surfaces": {"menu": {"paths": ["src/ui/**"]}},
                    "commands": {"fast": "exit 0"}}
        (self.root / ".aikit" / "ui.json").write_text(json.dumps(contract), encoding="utf-8-sig")
        loaded = ui_contract.load_contract(self.root)
        self.assertEqual(loaded.surfaces["menu"], ("src/ui/**",))

    def test_contract_rejects_escaping_paths_and_bad_schema(self):
        self.write_contract(protected=["../outside"])
        with self.assertRaises(ProjectError) as caught:
            ui_contract.load_contract(self.root)
        self.assertIn("relative path patterns", str(caught.exception))
        self.write_contract(schema=2)
        with self.assertRaises(ProjectError):
            ui_contract.load_contract(self.root)

    def test_contract_parses_snapshot_and_style_fields(self):
        self.write_contract(commands={"fast": "exit 0", "snapshot": "python inventory.py",
                                      "snapshot_timeout": 60},
                            style={"theme_paths": ["src/theme.py", "src/styles/**"]})
        loaded = ui_contract.load_contract(self.root)
        self.assertEqual(loaded.snapshot, "python inventory.py")
        self.assertEqual(loaded.snapshot_timeout, 60)
        self.assertEqual(loaded.theme_paths, ("src/theme.py", "src/styles/**"))
        self.write_contract()
        loaded = ui_contract.load_contract(self.root)
        self.assertEqual((loaded.snapshot, loaded.snapshot_timeout, loaded.theme_paths),
                         ("", ui_contract.FAST_TIMEOUT_SECONDS, ()))

    def test_contract_rejects_bad_snapshot_and_style_fields(self):
        self.write_contract(commands={"fast": "exit 0", "snapshot": 7})
        with self.assertRaises(ProjectError):
            ui_contract.load_contract(self.root)
        self.write_contract(commands={"fast": "exit 0", "snapshot_timeout": 0})
        with self.assertRaises(ProjectError):
            ui_contract.load_contract(self.root)
        self.write_contract(style={"theme_paths": ["../escape"]})
        with self.assertRaises(ProjectError):
            ui_contract.load_contract(self.root)
        self.write_contract(style={"theme_paths": "src/theme.py"})
        with self.assertRaises(ProjectError):
            ui_contract.load_contract(self.root)

    def test_begin_records_the_baseline_snapshot(self):
        self.write_contract(commands={"fast": "exit 0", "snapshot": "python inventory.py"})
        fake = FakeGit(tracked=(".aikit/ui.json", "src/ui/menu.py"))
        runner = lambda command, cwd, timeout: (0, "Menu(file)\nButton(save)\nButton(save)\n")
        task = ui_contract.begin(self.root, "menu", git_io=fake, shell_runner=runner)
        self.assertEqual(task["baseline_snapshot"], ["Button(save)", "Menu(file)"])
        self.assertEqual(task["allowed_removals"], [])

    def test_begin_refuses_a_failing_or_empty_snapshot(self):
        self.write_contract(commands={"fast": "python -c pass", "snapshot": "python inventory.py"})
        fake = FakeGit(tracked=(".aikit/ui.json", "src/ui/menu.py"))

        def red(command, cwd, timeout):
            return (0, "") if command == "python -c pass" else (1, "traceback")

        with self.assertRaises(ProjectError) as caught:
            ui_contract.begin(self.root, "menu", git_io=fake, shell_runner=red)
        self.assertIn("snapshot", str(caught.exception).lower())

        def empty(command, cwd, timeout):
            return (0, "") if command == "python -c pass" else (0, "  \n")

        with self.assertRaises(ProjectError):
            ui_contract.begin(self.root, "menu", git_io=fake, shell_runner=empty)

    def test_begin_refuses_an_unknown_surface_before_touching_git(self):
        self.write_contract()
        with self.assertRaises(ProjectError) as caught:
            ui_contract.begin(self.root, "missing")
        self.assertIn("Unknown UI surface", str(caught.exception))

    def test_corrupt_task_record_names_the_abort_remedy(self):
        (self.root / ".aikit" / "ui_task.json").write_text("{", encoding="utf-8")
        with self.assertRaises(ProjectError) as caught:
            ui_contract.read_task(self.root)
        self.assertIn("unreadable", str(caught.exception))
        self.assertIn("ui abort", caught.exception.fix)

    def test_cli_parses_every_ui_action(self):
        parser = build_parser()
        begin = parser.parse_args(["ui", "begin", "app", "--surface", "menu"])
        self.assertEqual((begin.ui_action, begin.name, begin.surface), ("begin", "app", "menu"))
        for action in ("verify", "finish", "abort", "status"):
            parsed = parser.parse_args(["ui", action, "app"])
            self.assertEqual(parsed.ui_action, action)
        allowed = parser.parse_args(["ui", "allow", "app", "Button*", "--reason", "replaced"])
        self.assertEqual((allowed.ui_action, allowed.name, allowed.pattern, allowed.reason),
                         ("allow", "app", "Button*", "replaced"))
        with self.assertRaises(SystemExit) as caught:
            parser.parse_args(["ui", "allow", "app", "Button*"])
        self.assertEqual(caught.exception.code, 2)
        finished = parser.parse_args(["ui", "finish", "app", "--reviewed"])
        self.assertTrue(finished.reviewed)
        attributed = parser.parse_args(["ui", "finish", "app", "--reviewed", "--reviewer", "yd"])
        self.assertEqual(attributed.reviewer, "yd")

    def test_verify_flags_protected_paths_and_a_moved_baseline(self):
        self.write_contract()
        fake = FakeGit(tracked=(".aikit/ui.json", "src/ui/menu.py"))
        runner = lambda command, cwd, timeout: (0, "")
        ui_contract.begin(self.root, "menu", git_io=fake, shell_runner=runner)

        fake.status = "?? tests/ui/test_menu.py\0"
        findings = ui_contract.verify(self.root, git_io=fake, shell_runner=runner)
        self.assertTrue(any("protected path changed" in finding for finding in findings), findings)

        fake.status = ""
        fake.head = "b" * 40
        findings = ui_contract.verify(self.root, git_io=fake, shell_runner=runner)
        self.assertTrue(any("baseline moved" in finding for finding in findings), findings)

    def test_finish_closes_only_a_green_task(self):
        self.write_contract()
        fake = FakeGit(tracked=(".aikit/ui.json", "src/ui/menu.py"))
        runner = lambda command, cwd, timeout: (0, "")
        ui_contract.begin(self.root, "menu", git_io=fake, shell_runner=runner)
        fake.status = " M src/ui/menu.py\0"
        self.assertEqual(ui_contract.finish(self.root, git_io=fake, shell_runner=runner,
                                            reviewed=True), [])
        self.assertFalse((self.root / ".aikit" / "ui_task.json").exists())

    def test_a_red_fast_command_increments_strikes_and_blocks_finish(self):
        self.write_contract()
        fake = FakeGit(tracked=(".aikit/ui.json", "src/ui/menu.py"))
        green = lambda command, cwd, timeout: (0, "")
        red = lambda command, cwd, timeout: (1, "menu test failed")
        ui_contract.begin(self.root, "menu", git_io=fake, shell_runner=green)
        fake.status = " M src/ui/menu.py\0"
        findings = ui_contract.finish(self.root, git_io=fake, shell_runner=red)
        self.assertTrue(any("fast UI proof failed" in finding for finding in findings), findings)
        self.assertEqual(ui_contract.read_task(self.root)["strikes"], 1)
        self.assertTrue((self.root / ".aikit" / "ui_task.json").is_file())

    def write_snapshot_contract(self):
        self.write_contract(commands={"fast": "python -c pass", "snapshot": "python inventory.py"},
                            style={"theme_paths": ["src/theme.py"]})

    def test_verify_flags_a_lost_control_in_the_snapshot_proof(self):
        self.write_snapshot_contract()
        fake = FakeGit(tracked=(".aikit/ui.json", "src/ui/menu.py"))

        def baseline(command, cwd, timeout):
            return (0, "") if command == "python -c pass" else (0, "Button(save)\nMenu(file)\n")

        ui_contract.begin(self.root, "menu", git_io=fake, shell_runner=baseline)
        fake.status = " M src/ui/menu.py\0"

        def lost(command, cwd, timeout):
            return (0, "") if command == "python -c pass" else (0, "Menu(file)\n")

        findings = ui_contract.verify(self.root, git_io=fake, shell_runner=lost)
        self.assertTrue(any("Button(save)" in finding and "snapshot" in finding
                            for finding in findings), findings)
        self.assertEqual(ui_contract.read_task(self.root)["strikes"], 1)

    def test_allow_records_intended_removals_and_verify_passes(self):
        self.write_snapshot_contract()
        fake = FakeGit(tracked=(".aikit/ui.json", "src/ui/menu.py"))

        def baseline(command, cwd, timeout):
            return (0, "") if command == "python -c pass" else (0, "Button(save)\nMenu(file)\n")

        ui_contract.begin(self.root, "menu", git_io=fake, shell_runner=baseline)
        ui_contract.allow(self.root, "Button*", "replaced by the toolbar")
        self.assertEqual(ui_contract.read_task(self.root)["allowed_removals"],
                         [{"pattern": "Button*", "reason": "replaced by the toolbar"}])
        with self.assertRaises(ProjectError) as caught:
            ui_contract.allow(self.root, "Menu*", "  ")
        self.assertEqual(caught.exception.exit_code, 2)

        def lost(command, cwd, timeout):
            return (0, "") if command == "python -c pass" else (0, "Menu(file)\n")

        fake.status = " M src/ui/menu.py\0"
        self.assertEqual(ui_contract.verify(self.root, git_io=fake, shell_runner=lost), [])

    def test_verify_flags_style_literals_outside_the_theme(self):
        self.write_snapshot_contract()
        fake = FakeGit(tracked=(".aikit/ui.json", "src/ui/menu.py"))

        def green(command, cwd, timeout):
            return (0, "") if command == "python -c pass" else (0, "Menu(file)\n")

        ui_contract.begin(self.root, "menu", git_io=fake, shell_runner=green)
        fake.status = " M src/ui/menu.py\0"
        fake.diff = ("diff --git a/src/ui/menu.py b/src/ui/menu.py\n"
                     "+++ b/src/ui/menu.py\n"
                     "@@ -1,2 +1,3 @@\n"
                     "+save = Button(fg=\"#ff0000\")\n"
                     "+value = width * 2\n")
        findings = ui_contract.verify(self.root, git_io=fake, shell_runner=green)
        self.assertTrue(any("style literal '#ff0000'" in finding for finding in findings),
                        findings)
        self.assertTrue(all("width * 2" not in finding for finding in findings), findings)

    def test_finish_requires_a_recorded_human_review(self):
        self.write_contract()
        fake = FakeGit(tracked=(".aikit/ui.json", "src/ui/menu.py"))
        green = lambda command, cwd, timeout: (0, "")
        ui_contract.begin(self.root, "menu", git_io=fake, shell_runner=green)
        fake.status = " M src/ui/menu.py\0"
        findings = ui_contract.finish(self.root, git_io=fake, shell_runner=green)
        self.assertTrue(any("review" in finding for finding in findings), findings)
        self.assertTrue((self.root / ".aikit" / "ui_task.json").is_file())
        self.assertEqual(ui_contract.finish(self.root, git_io=fake, shell_runner=green,
                                            reviewed=True), [])
        self.assertFalse((self.root / ".aikit" / "ui_task.json").exists())

    def test_finish_appends_each_completed_task_to_history(self):
        self.write_snapshot_contract()
        fake = FakeGit(tracked=(".aikit/ui.json", "src/ui/menu.py"))

        def snapshot(command, cwd, timeout):
            return (0, "") if command == "python -c pass" else (0, "Button(save)\nMenu(file)\n")

        ui_contract.begin(self.root, "menu", git_io=fake, shell_runner=snapshot)
        fake.status = " M src/ui/menu.py\0"
        self.assertEqual(ui_contract.finish(self.root, git_io=fake, shell_runner=snapshot,
                                            reviewed=True, reviewer="yd"), [])
        history_path = self.root / ".aikit" / "ui_history.json"
        self.assertTrue(history_path.is_file(), "a finished task leaves its evidence behind")
        history = json.loads(history_path.read_text(encoding="utf-8"))
        self.assertEqual(len(history), 1)
        record = history[0]
        self.assertEqual(record["surface"], "menu")
        self.assertEqual(record["reviewer"], "yd")
        self.assertEqual(record["final_snapshot_entries"], 2)
        self.assertTrue(record["final_snapshot_digest"])
        self.assertEqual(record["strikes"], 0)
        self.assertFalse((self.root / ".aikit" / "ui_task.json").exists())

        fake.status = ""
        ui_contract.begin(self.root, "menu", git_io=fake, shell_runner=snapshot)
        self.assertTrue((self.root / ".aikit" / "ui_task.json").is_file(),
                        "a finished task's history does not block the next begin")
        fake.status = " M src/ui/menu.py\0"
        self.assertEqual(ui_contract.finish(self.root, git_io=fake, shell_runner=snapshot,
                                            reviewed=True), [])
        history = json.loads(history_path.read_text(encoding="utf-8"))
        self.assertEqual(len(history), 2, "each finished task appends one record")
        self.assertEqual(history[1]["reviewer"], "", "an unattributed review is recorded as such")

    def test_finish_refuses_to_destroy_an_unreadable_history_file(self):
        self.write_contract()
        fake = FakeGit(tracked=(".aikit/ui.json", "src/ui/menu.py"))
        green = lambda command, cwd, timeout: (0, "")
        ui_contract.begin(self.root, "menu", git_io=fake, shell_runner=green)
        fake.status = " M src/ui/menu.py\0"
        (self.root / ".aikit" / "ui_history.json").write_text("{", encoding="utf-8")
        with self.assertRaises(ProjectError) as caught:
            ui_contract.finish(self.root, git_io=fake, shell_runner=green, reviewed=True)
        self.assertIn("history", str(caught.exception).lower())
        self.assertTrue((self.root / ".aikit" / "ui_task.json").is_file(),
                        "a failed finish leaves the open task untouched")
        self.assertEqual((self.root / ".aikit" / "ui_history.json").read_text(encoding="utf-8"),
                         "{", "the corrupt evidence file is not overwritten")


class TestUiProof(unittest.TestCase):
    """The UI guard's mechanical proofs: inventory diffs and style drift (ADR-160)."""

    def test_snapshot_lines_sort_strip_and_deduplicate(self):
        self.assertEqual(ui_proof.snapshot_lines("  Button(save)\nMenu(file)\nButton(save)\n\n"),
                         ["Button(save)", "Menu(file)"])

    def test_inventory_findings_flag_removed_entries_only(self):
        baseline = ["Button(save)", "Label(title)", "Menu(file)"]
        self.assertEqual(ui_proof.inventory_findings(baseline, baseline, []), [])
        self.assertEqual(ui_proof.inventory_findings(
            ["Menu(file)"], ["Menu(file)", "Button(new)"], []), [])
        findings = ui_proof.inventory_findings(baseline, ["Menu(file)"], [])
        self.assertEqual(len(findings), 1)
        self.assertIn("Button(save)", findings[0])
        self.assertIn("Label(title)", findings[0])

    def test_inventory_findings_honor_allowed_removal_patterns(self):
        self.assertEqual(ui_proof.inventory_findings(
            ["Button(save)", "Label(title)"], [], ["Button*", "Label(title)"]), [])
        findings = ui_proof.inventory_findings(["Button(save)", "Label(title)"], [], ["Label*"])
        self.assertEqual(len(findings), 1)
        self.assertIn("Button(save)", findings[0])
        self.assertNotIn("Label(title)", findings[0])

    def test_style_findings_flag_hardcoded_literals_outside_theme_paths(self):
        added = [("src/ui/menu.py", 12, 'save = Button(text="Save", fg="#ff0000")'),
                 ("src/ui/menu.py", 13, "title.font_size = 14"),
                 ("src/ui/menu.py", 14, "panel.configure(font=(\"Arial\", 10))"),
                 ("web/app.css", 3, "color: rgb(10, 20, 30)"),
                 ("web/app.css", 4, "font-family: Arial"),
                 ("web/app.css", 5, "color: #ffffffff"),
                 ("src/theme.py", 7, 'ERROR = "#ff0000"'),
                 ("src/ui/menu.py", 15, "value = width * 2")]
        findings = ui_proof.style_findings(added, ("src/theme.py",))
        self.assertEqual(findings, [
            "style literal '#ff0000' outside theme paths: src/ui/menu.py:12",
            "style literal 'font_size' outside theme paths: src/ui/menu.py:13",
            "style literal 'font' outside theme paths: src/ui/menu.py:14",
            "style literal 'rgb(' outside theme paths: web/app.css:3",
            "style literal 'font-family:' outside theme paths: web/app.css:4",
            "style literal '#ffffffff' outside theme paths: web/app.css:5",
        ])

    def test_style_findings_skip_font_properties_whose_value_is_a_token(self):
        added = [("web/app.css", 3, "font-family: var(--font-sans);"),
                 ("web/app.css", 4, "font-size: var(--text-lg);"),
                 ("src/ui/menu.py", 5, "title.font_size = var(SIZE)"),
                 ("web/app.css", 6, "font-family: var(--font-sans); color: #fff;"),
                 ("web/app.css", 7, "font-size: 14px; color: var(--fg);"),
                 ("src/ui/menu.py", 8, "title.font_size = 14; color = var(THEME)")]
        self.assertEqual(ui_proof.style_findings(added, ("src/theme.py",)),
                         ["style literal '#fff' outside theme paths: web/app.css:6",
                          "style literal 'font-size:' outside theme paths: web/app.css:7",
                          "style literal 'font_size' outside theme paths: src/ui/menu.py:8"])

    def test_style_findings_are_off_without_declared_theme_paths(self):
        added = [("src/ui/menu.py", 12, 'fg = "#ff0000"')]
        self.assertEqual(ui_proof.style_findings(added, []), [])


class TestProjectsStayOutOfKitState(unittest.TestCase):
    """AIKit's map, gates and sweeps never read a project's files (ADR-119)."""

    def test_codebase_scan_and_sweeps_prune_projects(self):
        kit = Path(tempfile.mkdtemp(prefix="test_projects_prune_"))
        self.addCleanup(shutil.rmtree, kit, ignore_errors=True)
        (kit / "projects" / "app").mkdir(parents=True)
        (kit / "projects" / "app" / "main.py").write_text("x = 1\n", encoding="utf-8")
        (kit / "projects" / "app" / "state.json.tmp_1_2").write_text("", encoding="utf-8")
        (kit / "tool.py").write_text("y = 2\n", encoding="utf-8")
        (kit / "s.json.tmp_1_2").write_text("", encoding="utf-8")
        self.assertEqual([p.name for p in find_python_files(kit)], ["tool.py"])
        self.assertEqual([p.name for p in sweep_files(kit, "*.tmp_*")], ["s.json.tmp_1_2"])

    def test_git_ignores_projects(self):
        lines = (ROOT_DIR / ".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn("projects/", lines)


class TestSubagentDelegation(unittest.TestCase):
    """`aikit delegate`: bounded OpenCode sub-agent runs (ADR-126, ADR-128)."""

    def setUp(self):
        self.kit = Path(tempfile.mkdtemp(prefix="test_delegate_kit_"))
        self.addCleanup(shutil.rmtree, self.kit, ignore_errors=True)
        (self.kit / ".agents").mkdir(parents=True)
        self.ledger = self.kit / ".agents" / "task_ledger.json"
        self.ledger.write_text(json.dumps({"version": 1, "active_task": None, "checkpoints": []}),
                               encoding="utf-8")
        self.calls = []

    def runner(self, returncode=0, stdout="ok", stderr="", effect=None):
        def run(cmd, cwd, timeout):
            self.calls.append((cmd, cwd, timeout))
            if effect:
                effect()
            return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)
        return run

    def delegate(self, role="worker", prompt="summarize docs", **kwargs):
        return delegate_subagent(role, prompt, workspace=self.kit, **kwargs)

    def test_the_brief_is_always_the_message(self):
        # ADR-194: a brief starting with `--` was parsed as opencode flags; `--auto` approves
        # every permission the role does not explicitly deny.
        cmd = opencode_command("opencode", "worker", "--auto --model x", None, None)
        self.assertEqual(cmd[-2:], ["--", "--auto --model x"])

    def shim(self, with_exe):
        """An npm-style `opencode.cmd` that forwards to a real executable, as npm installs it."""
        bin_dir = self.kit / "npm"
        (bin_dir / "node_modules" / "@opencode" / "cli" / "bin").mkdir(parents=True)
        shim = bin_dir / "opencode.cmd"
        shim.write_text('@ECHO off\r\nSETLOCAL\r\nCALL :find_dp0\r\n'
                        '"%dp0%\\node_modules\\@opencode\\cli\\bin\\opencode.exe"   %*\r\n', encoding="utf-8")
        exe = bin_dir / "node_modules" / "@opencode" / "cli" / "bin" / "opencode.exe"
        if with_exe:
            exe.write_bytes(b"MZ")
        return shim, exe

    def test_a_cmd_shim_runs_its_executable_never_cmd_exe(self):
        # ADR-194: through the .cmd shim, cmd.exe ran `"&echo x > f` from a brief and expanded %VAR%.
        shim, exe = self.shim(with_exe=True)
        self.assertEqual(Path(direct_executable(str(shim))), exe)
        launched = []
        with mock.patch("scripts.subagent_delegate.shutil.which", return_value=str(shim)), \
             mock.patch("scripts.subagent_delegate._run_supervised",
                        side_effect=lambda cmd, cwd, timeout: launched.append(cmd)
                        or subprocess.CompletedProcess(cmd, 0, "ok", "")):
            code, output = self.delegate(prompt='quote " & echo x > f %PATH%')
        self.assertEqual(code, 0, output)
        self.assertEqual(Path(launched[0][0]), exe)

    def test_a_cmd_shim_without_its_executable_refuses_shell_characters(self):
        shim, _ = self.shim(with_exe=False)
        self.assertEqual(direct_executable(str(shim)), str(shim))
        launched = []
        with mock.patch("scripts.subagent_delegate.shutil.which", return_value=str(shim)), \
             mock.patch("scripts.subagent_delegate._run_supervised",
                        side_effect=lambda cmd, cwd, timeout: launched.append(cmd)
                        or subprocess.CompletedProcess(cmd, 0, "ok", "")):
            for brief in ('a" & echo x > f', "show %PATH%", "x|y"):
                with self.subTest(brief=brief):
                    code, output = self.delegate(prompt=brief)
                    self.assertEqual(code, 1)
                    self.assertIn("cmd.exe", output)
                    self.assertIn("Fix:", output)
            self.assertEqual(launched, [], "nothing ran")
            self.assertEqual(self.delegate(prompt="summarize the docs")[0], 0)
        self.assertEqual(len(launched), 1)

    def test_roles_are_the_opencode_profiles(self):
        self.assertEqual(subagent_roles(), tuple(sorted(p.stem for p in (ROOT_DIR / ".opencode" / "agents").glob("*.md"))))
        code, output = self.delegate(role="hacker")
        self.assertEqual(code, 2)
        self.assertIn("unknown subagent role 'hacker'", output)
        self.assertIn("Fix:", output)

    def test_refuses_empty_brief_unknown_project_and_missing_file(self):
        for kwargs, expected in (({"prompt": "  "}, "empty prompt"),
                                 ({"project_name": "nope"}, "No project named 'nope'"),
                                 ({"file": "not_here.py"}, "'not_here.py' does not exist")):
            with self.subTest(kwargs=kwargs):
                code, output = self.delegate(runner=self.runner(), **kwargs)
                self.assertEqual(code, 2)
                self.assertIn(expected, output)
        self.assertEqual(self.calls, [], "nothing runs after a refused brief")

    def test_runs_opencode_headless_with_the_brief(self):
        (self.kit / "sample.py").write_text("print('hi')", encoding="utf-8")
        code, output = self.delegate(role="reviewer", prompt="check code", file="sample.py",
                                     model="opencode/glm-5.3-flash-free", runner=self.runner(stdout="inspected"))
        self.assertEqual(code, 0)
        self.assertIn("[SUBAGENT OK (reviewer", output)
        cmd, cwd, timeout = self.calls[0]
        self.assertEqual(cmd[1:7], ["run", "--standalone", "--format", "json", "--agent", "reviewer"])
        self.assertEqual(cmd[-1], "check code")
        self.assertIn("--file", cmd)
        self.assertEqual((cwd, timeout), (self.kit, 120))

    def test_json_report(self):
        code, output = self.delegate(role="explorer", output_format="json", runner=self.runner(stdout="found"))
        self.assertEqual(code, 0)
        data = json.loads(output)
        self.assertEqual((data["status"], data["agent"], data["output"]), ("success", "explorer", "found"))

    def test_json_and_failure_reports_scrub_credentials(self):
        # `answer_text` scrubbed only the success-text path; JSON and failure reports embedded
        # stdout/stderr raw, so a sub-agent could leak a credential into the caller's context
        # (PRINCIPLE-019 R4/R5, ADR-173, ADR-177).
        leak = "glpat\x2daB3dE5gH7jK9mN1pQ3rS"  # aikit:allow-secret
        cases = [
            ("json success", {"output_format": "json"}, 0, leak, ""),
            ("text failure", {}, 1, leak, ""),
            ("json failure", {"output_format": "json"}, 1, leak, ""),
            ("stderr failure", {}, 1, "", leak),
        ]
        for label, kwargs, returncode, stdout, stderr in cases:
            with self.subTest(case=label):
                code, output = self.delegate(
                    runner=self.runner(returncode=returncode, stdout=stdout, stderr=stderr),
                    **kwargs)
                self.assertEqual(code, returncode)
                self.assertNotIn(leak, output)
                self.assertIn("[REDACTED]", output)
        code, output = self.delegate(output_format="json", runner=self.runner(stdout=leak))
        self.assertEqual(json.loads(output)["output"], "[REDACTED]")

    def test_a_changed_ledger_is_reported_and_never_overwritten(self):
        # The ledger may hold a parallel session's checkpoint; restoring a snapshot erased it (ADR-128).
        def write():
            self.ledger.write_text('{"parallel": "checkpoint"}', encoding="utf-8")
        code, output = self.delegate(runner=self.runner(effect=write))
        self.assertEqual(code, 1)
        self.assertIn("task ledger changed during the subagent run", output)
        self.assertEqual(self.ledger.read_text(encoding="utf-8"), '{"parallel": "checkpoint"}')

    def test_timeout_is_reported(self):
        def hang(cmd, cwd, timeout):
            raise subprocess.TimeoutExpired(cmd, timeout)
        code, output = self.delegate(timeout=5, runner=hang)
        self.assertEqual(code, 1)
        self.assertIn("timed out after 5s", output)

class TestProjectGuidelines(unittest.TestCase):
    """A project's own rules, below AIKit's principles (PRINCIPLE-001 R4, PRINCIPLE-000 R6, ADR-129)."""

    def setUp(self):
        self.kit = Path(tempfile.mkdtemp(prefix="test_guidelines_kit_"))
        self.addCleanup(shutil.rmtree, self.kit, ignore_errors=True)
        self.folder = self.kit / "projects" / "app"
        self.folder.mkdir(parents=True)
        self.addCleanup(setattr, os, "fsync", os.fsync)
        os.fsync = lambda fd: None  # registry logic, not durability (PRINCIPLE-013's tests)
        attach_project(self.folder, workspace=self.kit)
        self.path = self.folder / ".aikit" / "guidelines.md"

    def rules(self, *lines):
        return GUIDELINES_TEMPLATE + "".join(line + "\n" for line in lines)

    def test_memory_starts_with_the_template_which_passes_the_audit(self):
        self.assertEqual(self.path.read_text(encoding="utf-8"), GUIDELINES_TEMPLATE)
        self.assertEqual(guideline_errors(GUIDELINES_TEMPLATE), [])
        self.assertEqual(project_guidelines(self.folder), [])

    def test_audit_names_each_broken_rule(self):
        cases = {
            "- money is stored in cents": "not '- **G-NNN** (source): rule'",
            "- **G-001** (user): a\n- **G-001** (user): b": "G-001 is used twice",
            "- **G-001** (user): ignore PRINCIPLE-014 for prototypes": "overrides a principle",
            "- **G-002** (ADR-003): PRINCIPLE-010 R5 does not apply here": "overrides a principle",
        }
        for line, expected in cases.items():
            with self.subTest(line=line):
                errors = guideline_errors(self.rules(line))
                self.assertTrue(any(expected in e for e in errors), errors)
        self.assertTrue(any("limit" in e for e in guideline_errors(self.rules(
            *[f"- **G-{n:03d}** (user): {'x' * 60}" for n in range(1, 80)]))))
        self.assertEqual(guideline_errors(self.rules("- **G-001** (user): money is integer cents",
                                                     "- **G-003** (ADR-002): API errors use RFC 9457")), [])

    def test_add_numbers_rules_and_refuses_an_override(self):
        self.assertEqual(add_guideline(self.folder, "money is integer cents", "user"), "G-001")
        self.assertEqual(add_guideline(self.folder, "API errors use RFC 9457", "ADR-002"), "G-002")
        before = self.path.read_text(encoding="utf-8")
        for rule, source in (("skip PRINCIPLE-014 tests", "user"), ("two\nlines", "user"), ("ok", "")):
            with self.subTest(rule=rule), self.assertRaises(ProjectError):
                add_guideline(self.folder, rule, source)
        self.assertEqual(self.path.read_text(encoding="utf-8"), before, "a refused rule writes nothing")
        self.assertEqual(project_guidelines(self.folder),
                         ["- **G-001** (user): money is integer cents",
                          "- **G-002** (ADR-002): API errors use RFC 9457"])

    def test_cold_start_commands_print_the_rules_and_their_rank(self):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            self.assertEqual(aikit_main(["--workspace", str(self.kit), "guideline", "app",
                                         "money is integer cents", "--source", "user"]), 0)
            self.assertEqual(aikit_main(["--workspace", str(self.kit), "resume", "app"]), 0)
            self.assertEqual(aikit_main(["--workspace", str(self.kit), "status", "app"]), 0)
        text = out.getvalue()
        self.assertEqual(text.count("G-001"), 3, text)
        self.assertIn("rank below AIKit's principles", text)

class TestClaudeSubagents(unittest.TestCase):
    """Claude Code sub-agents generated from AIKit's role profiles (PRINCIPLE-012 R8, ADR-131)."""

    OPENCODE = ROOT_DIR / ".opencode" / "agents"
    CLAUDE = ROOT_DIR / ".claude" / "agents"
    WRITE_TOOLS = {"Edit", "Write", "NotebookEdit", "Bash"}

    def tools(self, role):
        return {t.strip() for t in CLAUDE_AGENT_ROLES[role][0].split(",")}

    def test_every_role_exists_for_both_hosts(self):
        self.assertEqual(set(CLAUDE_AGENT_ROLES), {p.stem for p in self.OPENCODE.glob("*.md")})
        self.assertEqual({p.stem for p in self.CLAUDE.glob("*.md")}, set(CLAUDE_AGENT_ROLES))

    def test_profile_is_generated_from_the_one_role_text(self):
        source = "---\ndescription: Finds things\nmode: subagent\n---\n\nYou are AIKit's explorer.\n"
        rendered = render_claude_agent("explorer", source)
        self.assertTrue(rendered.startswith("---\nname: explorer\ndescription: Finds things\n"))
        self.assertIn(f"tools: {CLAUDE_AGENT_ROLES['explorer'][0]}\n", rendered)
        self.assertIn(f"model: {CLAUDE_AGENT_ROLES['explorer'][1]}\n", rendered)
        self.assertTrue(rendered.rstrip().endswith("You are AIKit's explorer."))
        with self.assertRaises(ValueError):  # ': ' in an unquoted YAML value stops the host loading it
            render_claude_agent("explorer", source.replace("Finds things", "Search: finds things"))
        for role in CLAUDE_AGENT_ROLES:
            with self.subTest(role=role):
                expected = render_claude_agent(role, (self.OPENCODE / f"{role}.md").read_text(encoding="utf-8"))
                self.assertEqual((self.CLAUDE / f"{role}.md").read_text(encoding="utf-8").replace("\r\n", "\n"),
                                 expected, "run `python scripts/sync_principles.py`")

    def test_read_only_roles_cannot_write(self):
        for role in ("explorer", "architect"):
            with self.subTest(role=role):
                self.assertFalse(self.tools(role) & self.WRITE_TOOLS)
        self.assertNotIn("Bash", self.tools("worker"), "the docs worker runs no commands")

    def test_role_text_is_host_neutral_and_names_both_ledgers(self):
        for path in self.OPENCODE.glob("*.md"):
            with self.subTest(role=path.stem):
                body = path.read_text(encoding="utf-8").split("---", 2)[2]
                self.assertNotIn("OpenCode", body)
                self.assertIn(".aikit/task_ledger.json", body)

    def test_no_agent_may_edit_a_task_ledger(self):
        settings = json.loads((ROOT_DIR / ".claude" / "settings.json").read_text(encoding="utf-8"))
        self.assertIn("Edit(**/task_ledger.json)", settings["permissions"]["deny"])

class TestFreeModelPolicy(unittest.TestCase):
    """Sub-agents run only on free models (PRINCIPLE-012 R8, ADR-132)."""

    CONFIG = json.loads((ROOT_DIR / "opencode.jsonc").read_text(encoding="utf-8"))

    def test_policy_names_free_and_paid_models(self):
        free = ["opencode/deepseek-v4.1-flash-free", "openrouter/qwen/qwen-2.5-coder-32b-instruct:free",
                "ollama/qwen2.5-coder:latest", "lmstudio/any-model", "gemini/gemini-3.8-flash",
                "gemini/gemini-3.5-flash-lite", "opencode/deepseek-v4.1-flash-free#high"]
        paid = ["gemini/gemini-3.1-pro-preview", "openrouter/google/gemini-2.5-pro", "opencode/claude-sonnet",
                "anthropic/claude-opus", "gemini/", "", "free",
                # ADR-194: the `#variant` is not part of the name; `-free` there named a paid model.
                "opencode/claude-sonnet#-free", "gemini/gemini-3.1-pro-preview#x"]
        for model in free:
            with self.subTest(model=model):
                self.assertTrue(is_free_model(model, self.CONFIG))
        for model in paid:
            with self.subTest(model=model):
                self.assertFalse(is_free_model(model, self.CONFIG))

    def test_benchmark_doc_names_each_roles_configured_model(self):
        # ADR-197: the doc's role column put coder/tester on a model no profile runs, and nothing
        # said the profiles decide; its `Configured today:` line now must match every profile.
        text = (ROOT_DIR / "knowledge" / "model_benchmarks.md").read_text(encoding="utf-8")
        line = re.search(r"^Configured today: (.+)$", text, re.M)
        self.assertIsNotNone(line, "model_benchmarks.md has no `Configured today:` line")
        documented = {}
        for roles, model in re.findall(r"((?:`\w+`(?:, | and )?)+) `([^`]+)`", line.group(1)):
            for role in re.findall(r"`(\w+)`", roles):
                documented[role] = model
        configured = {path.stem: re.search(r"^model:\s*(\S+)", path.read_text(encoding="utf-8"), re.M).group(1)
                      for path in (ROOT_DIR / ".opencode" / "agents").glob("*.md")}
        self.assertEqual(documented, configured)
        tree = text[text.index("Routing Decision Tree"):]
        self.assertNotRegex(tree, r"SWE-bench|\d+ t/s", "an unverified score is never a reason to choose")

    def test_every_role_and_the_default_run_on_a_free_model(self):
        models = {"default": self.CONFIG["model"]}
        for path in (ROOT_DIR / ".opencode" / "agents").glob("*.md"):
            models[path.stem] = re.search(r"^model:\s*(\S+)", path.read_text(encoding="utf-8"), re.M).group(1)
        for role, model in models.items():
            with self.subTest(role=role):
                self.assertTrue(is_free_model(model, self.CONFIG), model)

    def test_delegate_refuses_a_paid_model_before_running_anything(self):
        calls = []

        def runner(cmd, cwd, timeout):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, "ok", "")
        code, output = delegate_subagent("worker", "summarize", model="gemini/gemini-3.1-pro-preview", runner=runner)
        self.assertEqual(code, 2)
        self.assertIn("not a free model", output)
        self.assertEqual(calls, [])
        self.assertEqual(delegate_subagent("worker", "summarize", model="gemini/gemini-3.8-flash", runner=runner)[0], 0)

    def test_gemini_key_comes_only_from_the_environment(self):
        gemini = self.CONFIG["providers"]["gemini"]
        self.assertEqual(gemini["env"], ["GEMINI_API_KEY"])
        text = (ROOT_DIR / "opencode.jsonc").read_text(encoding="utf-8")
        self.assertNotRegex(text, r"AQ\.[0-9A-Za-z_-]{20}|AIza[0-9A-Za-z_-]{20}|apiKey")

    def test_text_report_keeps_only_the_answer(self):
        stream = "\n".join(json.dumps(e) for e in (
            {"type": "step_start", "part": {}},
            {"type": "tool_use", "part": {"tool": "glob", "state": {"output": "a\nb\n" * 50}}},
            {"type": "text", "part": {"text": "`scripts/project_registry.py` owns it."}},
        ))
        self.assertEqual(answer_text(stream), "`scripts/project_registry.py` owns it.")
        self.assertEqual(answer_text("plain output"), "plain output")

    def test_a_key_split_across_a_concatenation_is_still_caught(self):
        # ADR-133: `"AQ." + "<rest of a real key>"` passed every detector and was committed. The
        # sample is generated, so this file holds no key-shaped literal.
        import base64
        import hashlib
        fake = base64.urlsafe_b64encode(hashlib.sha256(b"aikit").digest()).decode().rstrip("=")
        findings = scan_text("t.py", f'key = "AQ." + "{fake}"')
        self.assertIn("high-entropy string literal", [f[2] for f in findings])
        self.assertNotIn(fake, findings[0][3], "the excerpt is redacted")
        for benign in (f'digest = "{hashlib.sha256(b"x").hexdigest()}"',
                       'name = "test_codebase_map_freshness_stale_detection_for_projects"'):
            with self.subTest(line=benign[:20]):
                self.assertEqual(scan_text("t.py", benign), [])

    def test_commit_diffs_are_scanned_line_by_line_with_their_file(self):
        import base64
        import hashlib
        fake = base64.urlsafe_b64encode(hashlib.sha256(b"history").digest()).decode().rstrip("=")
        diff = ("diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -1 +1 @@\n"
                f'-old = "{fake}"\n+x = 1\n'
                "diff --git a/cfg.py b/cfg.py\n--- /dev/null\n+++ b/cfg.py\n@@ -0,0 +1 @@\n"
                f'+token = "AQ." + "{fake}"\n')
        findings = scan_diff(diff)
        self.assertEqual([f[0] for f in findings], ["cfg.py"], "added lines only, labelled by file")

    def test_commit_scan_asks_for_merge_diffs(self):
        # ADR-163: `git log -p` omits a merge commit's resolution diff; -m shows each parent.
        from scripts.check_secrets import scan_commits
        with mock.patch("scripts.check_secrets.git_output", return_value="") as git:
            scan_commits("a..b")
        self.assertIn("-m", git.call_args.args[0], "a merge resolution must be scanned")

    def test_scan_commits_reads_a_merge_resolution_line(self):
        from scripts.check_secrets import scan_diff
        diff = ("diff --git a/merge.py b/merge.py\n--- a/merge.py\n+++ b/merge.py\n"
                "@@ -0,0 +1 @@\n+token = 'sk_live_" + "A" * 24 + "'\n")
        self.assertTrue(scan_diff(diff), "an added merge-resolution line is scanned")

    def test_merge_scan_deduplicates_the_same_hunk(self):
        from scripts.check_secrets import scan_commits
        block = ("diff --git a/merge.py b/merge.py\n--- a/merge.py\n+++ b/merge.py\n"
                 "@@ -0,0 +1 @@\n+token = 'sk_live_" + "A" * 24 + "'\n")
        with mock.patch("scripts.check_secrets.git_output", return_value=block + block):
            findings = scan_commits("a..b")
        self.assertEqual(len(findings), 1, "-m reports one hunk per parent")

    def test_scanner_catches_a_bare_gemini_key(self):
        # A fabricated value: a real key, even split in two, is a committed credential (ADR-133).
        key = "AQ." + "FakeKey0" * 6 + "xy"
        self.assertTrue(scan_text("notes.md", key))

class TestProjectPublish(unittest.TestCase):
    """`aikit publish`: a project in its own GitHub repository, private unless asked (ADR-134)."""

    def runner(self, **replies):
        """A scripted stand-in for git, gh and the secret scan; records every call."""
        self.calls = []
        defaults = {"rev-parse": (0, "abc123"), "status": (0, ""), "check_secrets.py": (0, "[OK]"),
                    "get-url": (1, ""), "auth": (0, "Logged in"), "create": (0, "https://github.com/me/app"),
                    "push": (0, "")}
        defaults.update(replies)

        # Most specific first: `gh auth status` must not match `status`, nor `--push` match `push`.
        order = ("auth", "create", "push", "get-url", "check_secrets.py", "rev-parse", "status")

        def run(argv, cwd):
            self.calls.append(argv)
            for key in order:
                if key in argv or any(key in str(a) for a in argv):
                    return defaults[key]
            return 0, ""
        return run

    def made(self, word):
        return [c for c in self.calls if word in c]

    def test_new_repository_is_private_scanned_first_and_pushed(self):
        code, report = publish_project(Path("/p/app"), "app", runner=self.runner())
        self.assertEqual(code, 0, report)
        create = self.made("create")[0]
        self.assertEqual(create[:3], ["gh", "repo", "create"])
        for flag in ("--private", "--push"):
            self.assertIn(flag, create)
        self.assertEqual(create[create.index("--remote") + 1], "origin")
        scan_at = next(i for i, c in enumerate(self.calls) if any("check_secrets.py" in str(a) for a in c))
        self.assertLess(scan_at, self.calls.index(create), "the scan runs before anything is uploaded")
        scan = self.calls[scan_at]
        self.assertEqual(scan[scan.index("--commits") + 1], "HEAD", "every commit about to be uploaded")
        self.assertNotIn("--all", scan, "the working tree is not what gets pushed (ADR-145)")

    def test_public_only_when_asked(self):
        publish_project(Path("/p/app"), "app", public=True, runner=self.runner())
        self.assertIn("--public", self.made("create")[0])
        self.assertNotIn("--private", self.made("create")[0])

    def test_existing_remote_is_pushed_never_recreated_or_forced(self):
        code, report = publish_project(Path("/p/app"), "app",
                                       runner=self.runner(**{"get-url": (0, "https://github.com/me/app.git")}))
        self.assertEqual(code, 0, report)
        self.assertEqual(self.made("create"), [])
        push = self.made("push")[0]
        self.assertEqual(push, ["git", "push", "-u", "origin", "HEAD"])

    def test_an_existing_upstream_scans_only_the_commits_it_pushes(self):
        code, report = publish_project(Path("/p/app"), "app", runner=self.runner(
            **{"get-url": (0, "https://github.com/me/app.git")}))
        self.assertEqual(code, 0, report)
        scan = next(c for c in self.calls if any("check_secrets.py" in str(a) for a in c))
        self.assertEqual(scan[scan.index("--commits") + 1], "@{u}..HEAD")

    def test_auto_push_scans_the_commits_it_pushes_and_refuses_a_finding(self):
        def runner(scan_code):
            def run(argv, cwd):
                self.calls.append(argv)
                if "get-url" in argv:
                    return 0, "https://github.com/me/app.git"
                if any("check_secrets.py" in str(a) for a in argv):
                    return scan_code, "[FAIL] 1 potential secret" if scan_code else "[OK]"
                if "@{u}" in argv:
                    return 0, "origin/main"
                if "@{u}..HEAD" in argv:
                    return 0, "abc1234 feat: x\n"
                return 0, ""
            return run
        self.calls = []
        code, report = auto_push_project(Path("/p/app"), "app", runner=runner(1))
        self.assertEqual(code, 1)
        self.assertIn("Fix:", report)
        self.assertEqual(self.made("push"), [], "nothing is pushed past a finding")
        self.calls = []
        self.assertEqual(auto_push_project(Path("/p/app"), "app", runner=runner(0))[0], 0)
        scan = next(c for c in self.calls if any("check_secrets.py" in str(a) for a in c))
        self.assertEqual(scan[scan.index("--commits") + 1], "@{u}..HEAD")
        self.assertLess(self.calls.index(scan), self.calls.index(self.made("push")[0]))

    def test_refusals_upload_nothing(self):
        cases = {"no commit": {"rev-parse": (128, "")},
                 "secret found": {"check_secrets.py": (1, "[FAIL] 1 potential secret")},
                 "gh not logged in": {"auth": (1, "not logged in")}}
        for case, replies in cases.items():
            with self.subTest(case=case):
                code, report = publish_project(Path("/p/app"), "app", runner=self.runner(**replies))
                self.assertEqual(code, 1, report)
                self.assertIn("Fix:", report)
                self.assertEqual(self.made("create") + self.made("push"), [])

    def test_uncommitted_work_is_named_in_the_report(self):
        code, report = publish_project(Path("/p/app"), "app", runner=self.runner(status=(0, " M app.py")))
        self.assertEqual(code, 0)
        self.assertIn("uncommitted", report)

    def test_extract_readme_description_finds_first_paragraph_and_truncates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            # Empty / missing
            self.assertEqual(extract_readme_description(root), "")
            # With description paragraph
            (root / "README.md").write_text("# my-app\n\n> **A lightweight CLI app.**\n\n## Quick Start\n", encoding="utf-8")
            self.assertEqual(extract_readme_description(root), "A lightweight CLI app.")
            # Cut at GitHub's 350-character limit; it was 200, which cut a description that
            # `new --description` accepts (ADR-202).
            (root / "README.md").write_text(f"# my-app\n\n{'x' * 300}\n", encoding="utf-8")
            self.assertEqual(extract_readme_description(root), "x" * 300)
            (root / "README.md").write_text(f"# my-app\n\n{'x' * 400}\n", encoding="utf-8")
            extracted = extract_readme_description(root)
            self.assertEqual(len(extracted), 350)
            self.assertTrue(extracted.endswith("..."))

            # Badges and images are stripped, finding the real description
            badge_md = (
                "# my-app\n\n"
                "[![CI Status](https://img.shields.io/ci)](https://example.com)\n"
                "![License](https://img.shields.io/license)\n\n"
                "A clean tool built with [Python](https://python.org).\n\n"
                "## Usage\n"
            )
            (root / "README.md").write_text(badge_md, encoding="utf-8")
            self.assertEqual(extract_readme_description(root), "A clean tool built with Python.")

            # HTML comments and tags are cleaned
            html_md = "# my-app\n\n<!-- intro --> <p>Fast and robust library.</p>\n"
            (root / "README.md").write_text(html_md, encoding="utf-8")
            self.assertEqual(extract_readme_description(root), "Fast and robust library.")

            # README without # header
            no_header_md = "A standalone tool with no top heading.\n\nMore details later.\n"
            (root / "README.md").write_text(no_header_md, encoding="utf-8")
            self.assertEqual(extract_readme_description(root), "A standalone tool with no top heading.")

    def test_get_project_repo_url(self):
        root = Path("/p/app")
        # No remote
        self.assertIsNone(get_project_repo_url(root, runner=self.runner(**{"get-url": (1, "")})))
        # Configured remote via runner
        url = get_project_repo_url(root, runner=self.runner(**{"get-url": (0, "https://github.com/me/app.git\n")}))
        self.assertEqual(url, "https://github.com/me/app.git")

        # Direct .git/config parsing (zero process spawns) with duplicate fetch entries and comments
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)
            git_dir = tmp_root / ".git"
            git_dir.mkdir()
            config = (
                "# Repository configuration\n"
                "[core]\n"
                "\trepositoryformatversion = 0\n"
                "[remote \"origin\"]\n"
                "\turl = https://github.com/team/core-app.git\n"
                "\tfetch = +refs/heads/*:refs/remotes/origin/*\n"
                "\tfetch = +refs/tags/*:refs/tags/*\n"
                "; trailing comment\n"
            )
            (git_dir / "config").write_text(config, encoding="utf-8")
            self.assertEqual(get_project_repo_url(tmp_root), "https://github.com/team/core-app.git")

    def test_repo_url_reads_the_config_as_git_does(self):
        # ADR-191: `URL = ...` hid a real remote from `status`, and an inline comment stayed in it.
        cases = (('[remote "origin"]\n\tURL = https://e.x/a.git\n', "https://e.x/a.git"),
                 ('[remote "origin"]\n\turl = https://e.x/b.git ; note\n', "https://e.x/b.git"),
                 ('[remote "origin"]\n\turl = "https://e.x/c d.git" # note\n', "https://e.x/c d.git"),
                 ('[Remote "origin"]\n\turl = https://e.x/d.git\n', "https://e.x/d.git"),
                 ('[remote "Origin"]\n\turl = https://e.x/e.git\n', None))
        for config, expected in cases:
            with self.subTest(config=config), tempfile.TemporaryDirectory() as tmp:
                (Path(tmp) / ".git").mkdir()
                (Path(tmp) / ".git" / "config").write_text(config, encoding="utf-8")
                self.assertEqual(get_project_repo_url(Path(tmp)), expected)

    def test_repo_url_never_shows_credentials(self):
        # ADR-191: a token in the remote URL was printed by `status`, `list` and the push report.
        hidden = "https://***@github.com/me/app.git"
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / ".git").mkdir()
            (Path(tmp) / ".git" / "config").write_text(
                '[remote "origin"]\n\turl = https://me:s3cret@github.com/me/app.git\n',  # aikit:allow-secret
                encoding="utf-8")
            self.assertEqual(get_project_repo_url(Path(tmp)), hidden)
        url = get_project_repo_url(Path("/p/app"), runner=self.runner(
            **{"get-url": (0, "https://s3cret@github.com/me/app.git\n")}))
        self.assertEqual(url, hidden)
        scp = get_project_repo_url(Path("/p/app"), runner=self.runner(
            **{"get-url": (0, "git@github.com:me/app.git\n")}))
        self.assertEqual(scp, "git@github.com:me/app.git", "an scp-style user is not a credential")

    def test_push_reports_never_show_credentials(self):
        token_url = "https://me:s3cret@github.com/me/app.git"  # aikit:allow-secret
        refused = self.runner(**{"get-url": (0, token_url), "push": (1, f"fatal: {token_url} refused")})

        def unpushed(argv, cwd):
            if "log" in argv:
                return 0, "abc123 work"
            return refused(argv, cwd)
        for code, report in (auto_push_project(Path("/p/app"), "app", runner=unpushed),
                             publish_project(Path("/p/app"), "app", runner=refused)):
            self.assertEqual(code, 1, report)
            self.assertNotIn("s3cret", report)
            self.assertIn("https://***@github.com/me/app.git", report)
        code, report = publish_project(Path("/p/app"), "app", runner=self.runner(**{"get-url": (0, token_url)}))
        self.assertEqual(code, 0, report)
        self.assertNotIn("s3cret", report)

    def test_publish_sets_the_readme_description_and_recorded_topics(self):
        # ADR-200, ADR-202: topics come from project.json, the description from the README alone,
        # so an edited README is what reaches GitHub.
        description = "A command-line tool that keeps a reading list in sync across devices."
        root = Path(tempfile.mkdtemp(prefix="test_publish_"))
        self.addCleanup(shutil.rmtree, root, ignore_errors=True)
        (root / "README.md").write_text(f"# app\n\n{AIKIT_BADGE}\n\n{description}\n\n## Quick\n",
                                        encoding="utf-8")
        code, report = publish_project(root, "app", runner=self.runner(), topics=["aikit", "python", "cli"])
        self.assertEqual(code, 0, report)
        create = self.made("create")[0]
        self.assertEqual(create[create.index("--description") + 1], description)
        self.assertIn(["gh", "repo", "edit", "--add-topic", "aikit,python,cli"], self.calls)
        self.assertIn("topics aikit, python, cli", report)

        code, report = publish_project(root, "app", runner=self.runner(
            **{"get-url": (0, "https://github.com/me/app.git")}), topics=["aikit"])
        self.assertEqual(code, 0, report)
        self.assertIn(["gh", "repo", "edit", "--description", description], self.calls)
        self.assertIn(["gh", "repo", "edit", "--add-topic", "aikit"], self.calls)

    def test_a_topic_failure_after_upload_is_a_note(self):
        base = self.runner()

        def run(argv, cwd):
            if "--add-topic" in argv:
                self.calls.append(argv)
                return 1, "HTTP 422: topic invalid"
            return base(argv, cwd)
        code, report = publish_project(Path("/p/app"), "app", runner=run, topics=["aikit", "web"])
        self.assertEqual(code, 0, "the repository exists and holds the commits")
        self.assertIn("Note: the topics were not set", report)
        self.assertIn("gh repo edit --add-topic aikit,web", report)

    def test_publish_passes_extracted_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# app\n\nA great tool.\n\n## Quick Ref\n", encoding="utf-8")
            publish_project(root, "app", runner=self.runner())
            create = self.made("create")[0]
            self.assertIn("--description", create)
            self.assertIn("A great tool.", create)

    def test_auto_push_project(self):
        root = Path("/p/app")
        # 1. Local only (no remote): the push was asked for and cannot happen, so it fails. It
        #    returned 0 while the push ran implicitly after every check (ADR-185, ADR-192).
        code, msg = auto_push_project(root, "app", runner=self.runner(**{"get-url": (1, "")}))
        self.assertEqual(code, 1)
        self.assertIn("no 'origin' remote", msg)
        self.assertIn("python aikit.py publish app", msg)
        self.assertEqual(self.made("push"), [])

        # 2. No commits on HEAD -> returncode 0, no push
        def no_commit_runner(argv, cwd):
            self.calls.append(argv)
            if "get-url" in argv:
                return 0, "https://github.com/me/app.git"
            if "rev-parse" in argv and "HEAD" in argv:
                return 128, "fatal: ambiguous argument 'HEAD'"
            return 0, ""
        self.calls = []
        code, msg = auto_push_project(root, "app", runner=no_commit_runner)
        self.assertEqual(code, 0)
        self.assertEqual(self.made("push"), [])

        # 3. Up to date with upstream -> returncode 0, no push
        def up_to_date_runner(argv, cwd):
            self.calls.append(argv)
            if "get-url" in argv:
                return 0, "https://github.com/me/app.git"
            if "@{u}" in argv:
                return 0, "origin/main"
            if "@{u}..HEAD" in argv:
                return 0, ""
            return 0, ""
        self.calls = []
        code, msg = auto_push_project(root, "app", runner=up_to_date_runner)
        self.assertEqual(code, 0)
        self.assertEqual(self.made("push"), [])

        # 4. Ahead of upstream -> runs git push origin HEAD
        def ahead_runner(argv, cwd):
            self.calls.append(argv)
            if "get-url" in argv:
                return 0, "https://github.com/me/app.git"
            if "@{u}" in argv:
                return 0, "origin/main"
            if "@{u}..HEAD" in argv:
                return 0, "abc1234 feat: new feature\n"
            if "push" in argv:
                return 0, "pushed successfully"
            return 0, ""
        self.calls = []
        code, msg = auto_push_project(root, "app", runner=ahead_runner)
        self.assertEqual(code, 0)
        push_call = self.made("push")[0]
        self.assertEqual(push_call, ["git", "push", "origin", "HEAD"])
        self.assertIn("Pushed 'app'", msg)

        # 5. Upstream not configured -> runs git push -u origin HEAD
        def no_upstream_runner(argv, cwd):
            self.calls.append(argv)
            if "get-url" in argv:
                return 0, "https://github.com/me/app.git"
            if "@{u}" in argv:
                return 128, "fatal: no upstream configured"
            if "push" in argv:
                return 0, "pushed successfully"
            return 0, ""
        self.calls = []
        code, msg = auto_push_project(root, "app", runner=no_upstream_runner)
        self.assertEqual(code, 0)
        push_call = self.made("push")[0]
        self.assertEqual(push_call, ["git", "push", "-u", "origin", "HEAD"])
        self.assertIn("Pushed 'app'", msg)

        # 6. Push fails -> returns 1 with triad
        def fail_runner(argv, cwd):
            self.calls.append(argv)
            if "get-url" in argv:
                return 0, "https://github.com/me/app.git"
            if "@{u}" in argv:
                return 0, "origin/main"
            if "@{u}..HEAD" in argv:
                return 0, "abc1234 feat: new feature\n"
            if "push" in argv:
                return 1, "remote rejected"
            return 0, ""
        self.calls = []
        code, msg = auto_push_project(root, "app", runner=fail_runner)
        self.assertEqual(code, 1)
        self.assertIn("Why:", msg)



class TestTestTierBudgetGate(unittest.TestCase):
    """PRINCIPLE-010 R6: both tier budgets are measured by a gate instead of assumed."""

    UNIT = "tests.test_kit"
    INTEG = "tests.test_integration"

    def fake_runner(self, table):
        # This tier may not start a process (PRINCIPLE-014 R3), so the tier runner is injected
        # exactly as auto_push_project's git runner is (PRINCIPLE-009 R4).
        def runner(module, timeout):
            return table[module]
        return runner

    def ok(self, tests, seconds):
        return 0, f"...\nRan {tests} tests in {seconds}s\n\nOK\n"

    def gate(self, table):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = run_budget_check(runner=self.fake_runner(table))
        return code, buf.getvalue()

    def test_parse_reads_the_count_and_duration_unittest_prints(self):
        self.assertEqual(parse_tier_output("...\nRan 317 tests in 1.139s\n\nOK\n"), (317, 1.139))
        self.assertIsNone(parse_tier_output("ImportError: cannot import name x"))

    def test_a_tier_over_its_per_test_average_fails_and_names_the_tier(self):
        # Red-green pin: the unit tier ran 1.21-1.45s against a <1s absolute budget for months
        # because no gate measured either tier.
        code, out = self.gate({self.UNIT: self.ok(100, 9.0), self.INTEG: self.ok(45, 1.0)})
        self.assertEqual(code, 1)
        self.assertIn(self.UNIT, out)
        self.assertIn("90.00ms", out)

    def test_both_tiers_inside_budget_pass_and_report_the_average(self):
        code, out = self.gate({self.UNIT: self.ok(317, 1.139), self.INTEG: self.ok(45, 7.631)})
        self.assertEqual(code, 0, out)
        self.assertIn("3.59ms", out)
        self.assertIn("169.58ms", out)

    def test_a_failing_tier_fails_the_gate_whatever_its_speed(self):
        red = (1, "Ran 10 tests in 0.010s\n\nFAILED (failures=1)\n")
        code, out = self.gate({self.UNIT: red, self.INTEG: self.ok(45, 1.0)})
        self.assertEqual(code, 1)
        self.assertIn("failed", out.lower())

    def test_unparseable_tier_output_fails_instead_of_reporting_zero(self):
        code, _ = self.gate({self.UNIT: (0, "collection exploded"), self.INTEG: self.ok(45, 1.0)})
        self.assertEqual(code, 1)

    def test_every_test_module_in_the_repository_has_a_budget(self):
        # A new tier must not escape the gate by simply existing.
        modules = {f"tests.{path.stem}" for path in (ROOT_DIR / "tests").glob("test_*.py")}
        self.assertEqual(set(TIER_BUDGETS_MS), modules)

    def test_budget_errors_is_silent_when_every_tier_fits(self):
        self.assertEqual(budget_errors([]), [])

class TestChecklistWording(unittest.TestCase):
    """
    PRINCIPLE-000 R7 bans hedge words in "every rule added or changed", but the slices the
    wording tests read stopped at the principle sections. The two checklists an agent actually
    runs sat outside them and carried "concise", "dense" and "relevant" (ADR-147).
    """

    HEDGES = TestPrinciple001Unambiguity.HEDGES

    @classmethod
    def setUpClass(cls):
        text = SSOT_MD.read_text(encoding="utf-8")
        cls.section = text[text.index("## 🛠️ AI Task Checklists"):]

    def test_checklists_contain_no_hedge_words(self):
        for hedge in self.HEDGES:
            with self.subTest(hedge=hedge):
                self.assertNotIn(hedge, self.section,
                                 f"a checklist item uses '{hedge}', which PRINCIPLE-000 R7 bans")

    def test_every_checklist_item_cites_a_principle(self):
        items = re.findall(r"^- \[ \] ([^\n]+)$", self.section, re.M)
        self.assertGreater(len(items), 10, "both checklists must be in the slice")
        for item in items:
            with self.subTest(item=item[:50]):
                self.assertRegex(item, r"PRINCIPLE-\d{3}",
                                 "a checklist item names the principle it checks, so its verdict is traceable")

class TestPostCommitVerification(unittest.TestCase):
    """PRINCIPLE-018 R7: the commit itself is verified, not the tree it was tested in (ADR-149)."""

    def runner(self, failing=(), worktree_fails=False, pushed=False, remote_contains=False):
        """A scripted git/gate stand-in; records every call so order and cwd can be asserted."""
        self.calls = []

        def run(argv, cwd):
            self.calls.append((argv, Path(cwd)))
            joined = " ".join(str(a) for a in argv)
            if "merge-base --is-ancestor" in joined:
                return (0, "") if pushed else (1, "")
            if "branch -r --contains" in joined:
                return 0, ("  origin/main" if remote_contains else "")
            if "rev-parse --short" in joined:
                return 0, "abc1234"
            if joined.endswith("rev-parse 1111old"):
                return 0, "1111old"
            if "rev-parse HEAD@{u}" in joined:
                return 0, "0000upstream"
            if "rev-parse" in joined:
                return 0, "9999head"
            if "worktree add" in joined:
                return (1, "fatal: invalid reference") if worktree_fails else (0, "")
            for name in failing:
                if name == "tiers" and "check_test_budgets" in joined:
                    return 1, "[FAIL] tests.test_kit: the tier failed"
                if name == "knowledge" and "update_knowledge_base" in joined:
                    return 1, "[FAIL] codebase_map.md is stale"
            return 0, "ok"
        return run

    def ran(self, fragment):
        return [(argv, cwd) for argv, cwd in self.calls if any(fragment in str(a) for a in argv)]

    def test_a_green_commit_passes_and_every_gate_runs_in_the_worktree(self):
        code, report = verify_commit(repo=Path("/repo"), runner=self.runner())
        self.assertEqual(code, 0, report)
        self.assertIn("[OK] Commit abc1234 passes every gate on its own.", report)
        added = self.ran("worktree")[0][0]
        self.assertIn("--detach", added)
        worktree = Path(added[added.index("--detach") + 1])
        for gate in ("check_test_budgets", "sync_principles", "update_knowledge_base",
                     "check_reachability", "check_secrets", "dogfood"):
            with self.subTest(gate=gate):
                calls = self.ran(gate)
                self.assertTrue(calls, f"{gate} never ran")
                self.assertEqual(calls[0][1], worktree, f"{gate} ran outside the worktree")

    def test_the_secret_scan_reads_the_unpushed_range_as_resolved_shas(self):
        verify_commit(repo=Path("/repo"), runner=self.runner())
        argv = self.ran("check_secrets")[0][0]
        self.assertIn("--commits", argv)
        self.assertEqual(argv[argv.index("--commits") + 1], "0000upstream..9999head",
                         "a detached worktree cannot resolve @{u} or HEAD itself")

    def test_the_scanned_range_is_what_this_verification_covers(self):
        # ADR-149: the first draft returned a bare SHA when no upstream resolved, and
        # `git log -p <sha>` means every commit reachable from it: the whole history, which is
        # red forever because of the key ADR-133 records. This repository hit it: `@{u}` resolves
        # as a name while `origin/main` has no local ref, so the bare-SHA branch was taken.
        cases = {
            "ahead of a resolvable upstream": ({"up": (0, "aaa"), "parent": (0, "ppp")}, "aaa..hhh"),
            "upstream equal to the commit": ({"up": (0, "hhh"), "parent": (0, "ppp")}, "ppp..hhh"),
            "upstream name without a local ref": ({"up": (128, "fatal"), "parent": (0, "ppp")}, "ppp..hhh"),
            "a root commit": ({"up": (128, "fatal"), "parent": (128, "fatal")}, "hhh"),
        }
        for label, (replies, expected) in cases.items():
            with self.subTest(case=label):
                def run(argv, cwd, replies=replies):
                    joined = " ".join(str(a) for a in argv)
                    if "@{u}" in joined:
                        return replies["up"]
                    if joined.endswith("^"):
                        return replies["parent"]
                    return 0, "hhh"
                self.assertEqual(scanned_range(Path("/repo"), "HEAD", run), expected)

    def test_a_failing_gate_is_named_with_the_undo_that_fits_an_unpushed_commit(self):
        code, report = verify_commit(repo=Path("/repo"), runner=self.runner(failing=("knowledge",)))
        self.assertEqual(code, 1)
        text = "\n".join(report)
        self.assertIn("[FAIL] knowledge", text)
        self.assertIn("codebase_map.md is stale", text, "the gate's own output is quoted")
        self.assertIn("does not pass on its own: knowledge", text)
        self.assertIn("git reset --soft HEAD^", text)
        for part in ("Why:", "Fix:"):
            self.assertIn(part, text)

    def test_a_pushed_commit_is_told_to_fix_forward_not_to_reset(self):
        # The old Fix always said `git reset --soft HEAD^`, which rewrites published history when
        # the failing commit is already on the remote.
        code, report = verify_commit(repo=Path("/repo"),
                                     runner=self.runner(failing=("knowledge",), pushed=True))
        text = "\n".join(report)
        self.assertEqual(code, 1)
        self.assertIn("already on the remote", text)
        self.assertIn("new commit", text)
        self.assertNotIn("git reset", text)

    def test_a_commit_pushed_without_an_upstream_is_not_told_to_reset(self):
        # `git push origin HEAD` without -u leaves no upstream, so HEAD@{u} cannot answer; the
        # commit is still on the remote and resetting it rewrites published history (ADR-188).
        code, report = verify_commit(repo=Path("/repo"),
                                     runner=self.runner(failing=("knowledge",), remote_contains=True))
        text = "\n".join(report)
        self.assertEqual(code, 1)
        self.assertIn("already on the remote", text)
        self.assertNotIn("git reset", text)

    def test_a_commit_that_is_not_head_is_not_told_to_reset_head(self):
        # Verifying an older commit with --ref: resetting HEAD would undo a different commit.
        code, report = verify_commit(ref="1111old", repo=Path("/repo"),
                                     runner=self.runner(failing=("knowledge",)))
        text = "\n".join(report)
        self.assertEqual(code, 1)
        self.assertIn("not HEAD", text)
        self.assertIn("new commit", text)
        self.assertNotIn("git reset", text)

    def test_the_worktree_is_removed_even_when_a_gate_fails(self):
        for failing in ((), ("tiers", "knowledge")):
            with self.subTest(failing=failing):
                verify_commit(repo=Path("/repo"), runner=self.runner(failing=failing))
                removed = self.ran("remove")
                self.assertTrue(removed, "the worktree was left behind")
                self.assertIn("--force", removed[0][0])

    def test_a_worktree_that_cannot_be_made_is_reported_not_passed(self):
        code, report = verify_commit(repo=Path("/repo"), runner=self.runner(worktree_fails=True))
        self.assertEqual(code, 1)
        self.assertIn("could not be checked out on its own", "\n".join(report))
        self.assertEqual(self.ran("dogfood"), [], "no gate runs when the checkout failed")

    def test_a_ref_that_is_no_commit_is_refused(self):
        code, report = verify_commit(repo=Path("/repo"), runner=lambda argv, cwd: (128, "fatal"))
        self.assertEqual(code, 1)
        self.assertIn("no commit to verify", report[0])


if __name__ == "__main__":
    unittest.main()
