# Codebase Map & Symbol Catalog 🗺️

> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**
> This document provides an automated, up-to-date registry of all modules, classes, and exported functions across this repository.

---

## 📊 Codebase Metrics
- **Total Python Modules**: `5`
- **Total Classes**: `12`
- **Total Functions / Methods**: `43`
- **Total Source Lines**: `3194`

---

## 📦 Modules & Exported Symbols

### [`scripts/disruption_recovery.py`](scripts/disruption_recovery.py)
> *Disruption Recovery & Task Progress Ledger (PRINCIPLE-006, PRINCIPLE-013)*

**Size**: `971` lines (`39281` bytes)

**Functions:**
- `def get_ledger_path(custom_dir)` - *Return path to task ledger, creating parent directories if needed.*
- `def file_lock(lock_path, timeout_seconds, poll_interval)` - *Cross-platform cooperative advisory lock (PRINCIPLE-013).*
- `def locked_ledger(ledger_file, timeout_seconds)` - *Serialize a full read-modify-write cycle on the task ledger (PRINCIPLE-013 Rule 3).*
- `def fsync_dir(dir_path)` - *Flush a directory entry so a completed `os.replace` survives power loss (PRINCIPLE-013 R1).*
- `def check_disk_headroom(target_dir, min_mb)` - *Check whether sufficient disk headroom exists before writing (PRINCIPLE-013).*
- `def migrate_ledger_schema(data)` - *Ensure recovered or loaded ledger conforms to current schema specification (PRINCIPLE-013).*
- `def atomic_write_json(file_path, data, max_retries, min_headroom_mb)` - *Atomically write JSON data using fsync, shadow backup, and temporary replacement (PRINCIPLE-013).*
- `def load_ledger(ledger_file)` - *Safely load the task ledger with startup self-healing (PRINCIPLE-013).*
- `def prune_checkpoints(checkpoints, active_task_id, max_history)` - *Prune checkpoints to maintain a bounded rolling memory window (PRINCIPLE-004).*
- `def save_ledger(ledger, ledger_file, max_history, _locked)` - *Save the task ledger atomically to disk with bounded rolling history (PRINCIPLE-004).*
- `def resolve_phase_num(phase, explicit_num)` - *Resolve lifecycle phase number 1..5 for compaction orientation (PRINCIPLE-002).*
- `def classify_git_status(porcelain_output)` - *Classify `git status --porcelain` v1 output into disruption categories (PRINCIPLE-006 R2).*
- `def resolve_active_phase(active_task, default)` - *Read the recorded lifecycle phase of a task (PRINCIPLE-002 R4, PRINCIPLE-004 R2).*
- `def record_checkpoint(task_id, phase, description, files_affected, status, ledger_file, phase_num, why, benefits, risks, mitigation)` - *Record an atomic micro-checkpoint in the task ledger (PRINCIPLE-002, PRINCIPLE-006, PRINCIPLE-007).*
- `def mark_task_completed(task_id, ledger_file)` - *Mark the active task as successfully completed in the ledger (locked, PRINCIPLE-013 R3).*
- `def reset_active_task(reason, ledger_file)` - *Abandon or reset the active in-progress task in the ledger (locked, PRINCIPLE-006).*
- `def clean_dangling_temp_files(workspace_dir)` - *Scan and safely purge orphaned *.tmp_* files left by interrupted writes (PRINCIPLE-006, PRINCIPLE-013).*
- `def run_disruption_audit(workspace_dir)` - *Execute a comprehensive pre-flight disruption audit (PRINCIPLE-006, PRINCIPLE-007).*
- `def format_audit_report(audit)` - *Generate human and AI-readable disruption recovery audit report.*
- `def format_resume_report(audit)` - *Generate structured guidance for cold-starting AI agents to resume an interrupted task.*
- `def validate_conventional_commit(message)` - *Validate that a commit message conforms to Conventional Commits (PRINCIPLE-018).*
- `def validate_argv(argv)` - *Return unrecognized options, skipping values of known value-taking flags (PRINCIPLE-011).*

---

### [`scripts/sync_principles.py`](scripts/sync_principles.py)
> *Principles Auto-Sync Tool (PRINCIPLE-017)*

**Size**: `430` lines (`17752` bytes)

**Functions:**
- `def fsync_dir(dir_path)` - *Flush the directory entry so a completed os.replace survives power loss (PRINCIPLE-013 R1).*
- `def load_tier_1b_domain_rules(domain_path)` - *Load project-specific domain rules from .agents/rules/domain.md if present (PRINCIPLE-001, PRINCIPLE-017).*
- `def append_domain_rules(lines, domain_rules)` - *Helper to append Tier 1B domain rules to prompt targets.*
- `def parse_principles(agents_file, strict)` - *Parse AGENTS.md, enforce strict schema validation, reject duplicate IDs, and verify monotonic lifecycle progression.*
- `def validate_triad_consistency(principles, guidelines_file, readme_file)` - *Verify that all principles in AGENTS.md also exist in GUIDELINES.md and README.md with matching titles (PRINCIPLE-017).*
- `def generate_gemini_content(principles, domain_rules)`
- `def generate_agents_rule_content(principles, domain_rules)`
- `def generate_claude_content(principles, domain_rules)`
- `def generate_cursorrules_content(principles, domain_rules)`
- `def generate_copilot_content(principles, domain_rules)`
- `def sync_all(check_only, exit_on_mismatch, domain_path, guidelines_file, readme_file)` - *Synchronize master specification from AGENTS.md across all IDE prompt targets.*
- `def print_help()` - *Print command line usage for sync_principles.py.*

---

### [`scripts/update_knowledge_base.py`](scripts/update_knowledge_base.py)
> *Codebase Knowledge Base Auto-Updater & Validator (PRINCIPLE-016)*

**Size**: `402` lines (`14566` bytes)

**Functions:**
- `def fsync_dir(dir_path)` - *Flush the directory entry so a completed os.replace survives power loss (PRINCIPLE-013 R1).*
- `def render_signature(node, drop_self)` - *Render a complete call signature from an AST function node (PRINCIPLE-003, PRINCIPLE-016).*
- `def extract_python_symbols(file_path, strict)` - *Parse a python file with AST and extract docstrings, classes, and functions (PRINCIPLE-003).*
- `def find_python_files(root)` - *Dynamically discover all source python files across the repository.*
- `def generate_codebase_map(root, strict)` - *Generate the markdown content for knowledge/codebase_map.md with AST validation (PRINCIPLE-003).*
- `def validate_knowledge_links(knowledge_dir)` - *Verify that all relative file links in knowledge/INDEX.md physically exist on disk (PRINCIPLE-016).*
- `def check_codebase_map_freshness(knowledge_dir, strict)` - *Check if codebase_map.md accurately reflects current codebase AST (PRINCIPLE-016).*
- `def update_and_validate(knowledge_dir, strict)`
- `def _validate_argv(argv, known, help_text)` - *Short-circuit on --help and reject unknown flags with exit 2 (PRINCIPLE-011, PRINCIPLE-015).*

---

### [`tests/test_integration.py`](tests/test_integration.py)
> *Integration & Operational Dogfooding Tier (PRINCIPLE-014, PRINCIPLE-015).*

**Size**: `294` lines (`13080` bytes)

**Classes:**
- `class TestParallelAgentSafety` - *Multi-process reproduction of the lost-update race (PRINCIPLE-013 R3).*
  - Method `.setUp()`
  - Method `.test_parallel_checkpoints_do_not_lose_updates()`
  - Method `.test_no_lock_artifacts_survive_concurrent_writes()`
- `class TestGitStatusGrounding` - *Empirical grounding of the porcelain parser against real `git` output (PRINCIPLE-003 R1).*
  - Method `.test_parser_offsets_match_real_git_output()`
  - Method `.test_conflict_audit_reports_block_rather_than_clean()`
- `class TestCommitValidatorCli` - *Conventional Commit validator exercised as a real binary (PRINCIPLE-018 R1).*
  - Method `._run(message)`
  - Method `.test_valid_message_exits_zero()`
  - Method `.test_invalid_message_exits_one_with_reason()`
- `class TestOperationalDogfooding` - *Dual-Track CLI Dogfooding & Zero-Blast-Radius Chaos Test (PRINCIPLE-015).*
  - Method `._porcelain()` - *Return the working-tree state, or None when git is unavailable.*
  - Method `.setUpClass()`
  - Method `.test_ephemeral_sandbox_isolation()`
  - Method `.test_golden_path_help_contract()`
  - Method `.test_chaos_unknown_flag_rejected_with_remediation_triad()`
  - Method `.test_dogfood_matrix_leaves_zero_blast_radius()`
- `class TestTierBudgetDiscipline` - *Structural enforcement of the two-tier test budget (PRINCIPLE-010 R6, PRINCIPLE-014 R3).*
  - Method `.test_unit_tier_spawns_no_processes_and_never_sleeps()`
  - Method `.test_integration_tier_bounds_every_spawn()`

---

### [`tests/test_kit.py`](tests/test_kit.py)
> *Automated Test Suite for Portable Agent Kit (PRINCIPLE-011, PRINCIPLE-016)*

**Size**: `1097` lines (`55779` bytes)

**Classes:**
- `class TestPrincipleSync` - *Verifies that all 18 principles are maintained and synchronized (PRINCIPLE-001, PRINCIPLE-017).*
  - Method `.test_parse_18_principles()`
  - Method `.test_monotonic_lifecycle_phase_alignment()`
  - Method `.test_targets_in_sync_and_budgeted()`
  - Method `.test_principle_003_anti_hallucination_capsule()`
  - Method `.test_principle_004_compaction_resilience_capsule()`
  - Method `.test_principle_005_cold_start_capsule()`
  - Method `.test_principle_006_disruption_capsule()`
  - Method `.test_principle_014_regression_shield_capsule()`
  - Method `.test_principle_015_operational_dogfooding_capsule()`
  - Method `.test_principle_016_knowledge_base_capsule()`
  - Method `.test_principle_017_auto_sync_capsule()`
  - Method `.test_principle_018_git_workflow_capsule()`
  - Method `.test_guideline_targets_freshness_gate()`
  - Method `.test_triad_consistency_gate()`
  - Method `.test_principle_schema_strictness()`
  - Method `.test_tier_1b_domain_rules_injection()`
  - Method `.test_domain_rules_template_validity()`
  - Method `.test_readme_cold_start_orientation_and_script_parity()`
- `class TestContinuousVerificationGate` - *The CI workflow must enforce the same gates the principles declare, using the same*
  - Method `.setUpClass()`
  - Method `.test_workflow_exists()`
  - Method `.test_workflow_runs_every_declared_gate()`
  - Method `.test_workflow_commands_match_documented_commands()`
  - Method `.test_workflow_covers_posix_and_windows()`
  - Method `.test_workflow_is_bounded_and_least_privileged()`
  - Method `.test_workflow_asserts_pristine_tree()`
  - Method `.test_workflow_yaml_has_no_unquoted_colon_scalars()`
  - Method `.test_workflow_uses_no_tabs()`
- `class TestDisruptionRecovery` - *Verifies atomic write, disruption ledger, and crash recovery (PRINCIPLE-006, PRINCIPLE-013).*
  - Method `.setUp()`
  - Method `.tearDown()`
  - Method `.test_atomic_write_and_load()`
  - Method `.test_bounded_rolling_ledger_pruning()`
  - Method `.test_self_healing_quarantine_corrupted_json()`
  - Method `.test_self_healing_recovery_from_shadow_backup()`
  - Method `.test_advisory_file_lock()`
  - Method `.test_disk_headroom_check()`
  - Method `.test_schema_migration_backward_compatibility()`
  - Method `.test_zero_byte_power_loss_truncation_quarantine()`
  - Method `.test_record_checkpoint_and_complete()`
  - Method `.test_dangling_temp_file_detection()`
  - Method `.test_format_resume_report()`
  - Method `.test_reset_active_task()`
  - Method `.test_clean_dangling_temp_files()`
  - Method `.test_non_git_workspace_detection()`
  - Method `.test_checkpoint_with_impact_assessment()`
  - Method `.test_audit_and_resume_reports_with_impact_assessment()`
  - Method `.test_hierarchical_milestone_indexing()`
  - Method `.test_dynamic_re_decomposition_on_discovery()`
  - Method `.test_conventional_commit_validation()`
- `class TestKnowledgeBase` - *Verifies AST parsing and documentation completeness (PRINCIPLE-003, PRINCIPLE-016).*
  - Method `.test_core_docs_exist()`
  - Method `.test_update_and_validate_runs()`
  - Method `.test_codebase_map_freshness_gate()`
  - Method `.test_codebase_map_freshness_stale_detection()`
  - Method `.test_ast_symbol_extraction()`
  - Method `.test_ast_strict_mode_fails_on_syntax_error()`
  - Method `.test_link_integrity_shield()`
- `class TestConcurrencyAndResumptionCorrectness` - *Red-green defect pins for four invariants that reported green while broken in production*
  - Method `.setUp()`
  - Method `.test_locked_ledger_serializes_read_modify_write()`
  - Method `.test_locked_ledger_surfaces_contention_instead_of_writing_unprotected()`
  - Method `.test_resume_reports_the_phase_actually_recorded()`
  - Method `.test_resume_never_recommends_an_earlier_phase()`
  - Method `.test_resolve_active_phase_honours_legacy_and_label_fallbacks()`
  - Method `.test_fsync_dir_is_safe_and_platform_portable()`
  - Method `.test_ledger_paths_accept_strings_without_raw_tracebacks()`
- `class TestPorcelainClassification` - *Exhaustive table-driven coverage of `git status --porcelain` v1 classification*
  - Method `.test_every_porcelain_state_is_classified()`
  - Method `.test_no_real_state_is_silently_dropped()`
  - Method `.test_conflict_states_carry_their_code_for_diagnostics()`
  - Method `.test_ignored_and_blank_lines_are_skipped()`
  - Method `.test_empty_output_is_clean()`
  - Method `.test_paths_with_spaces_survive_classification()`
- `class TestAstSignatureFidelity` - *The symbol catalog is what agents consult before verifying call-sites (PRINCIPLE-004 R3), so*
  - Method `.setUp()`
  - Method `._probe(source)`
  - Method `.test_async_functions_and_methods_are_catalogued()`
  - Method `.test_full_signature_includes_varargs_kwonly_and_posonly()`
  - Method `.test_self_and_cls_are_dropped_from_method_signatures_only()`
  - Method `.test_generated_map_renders_async_keyword()`

---
