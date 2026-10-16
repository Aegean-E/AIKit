# Codebase Map & Symbol Catalog 🗺️

> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**
> This document provides an automated, up-to-date registry of all modules, classes, and exported functions across this repository.

---

## 📊 Codebase Metrics
- **Total Python Modules**: `8`
- **Total Classes**: `34`
- **Total Functions / Methods**: `100`
- **Total Source Lines**: `6743`

---

## 📦 Modules & Exported Symbols

### [`scripts/check_reachability.py`](scripts/check_reachability.py)
> *Invariant Reachability Shield (PRINCIPLE-014 Rule 7)*

**Size**: `288` lines (`11276` bytes)

**Functions:**
- `def parse_module(path)` - *Parse a module once per content. Every analysis below walks the same files, and parsing each*
- `def production_modules()` - *Production source files whose reachability is audited (excludes this checker itself).*
- `def collect_definitions(files)` - *Map every top-level function name to the module that defines it.*
- `def collect_references(files)` - *Every name referenced in production code, however it is reached.*
- `def find_unreachable(files)` - *Functions defined in production code with no production reference and no allowlist entry.*
- `def collect_state_keys(files)` - *Literal string keys read via `.get("k")` or `["k"]`, and keys written as dict literals or*
- `def find_phantom_keys(files)` - *State keys read by production code that no production code ever writes.*
- `def run_check(verbose)` - *Audit reachability and key round-trips, reporting tersely (PRINCIPLE-012 Rule 4).*

---

### [`scripts/check_secrets.py`](scripts/check_secrets.py)
> *Secret & Sensitive Data Hygiene Scanner (PRINCIPLE-019)*

**Size**: `368` lines (`15619` bytes)

**Functions:**
- `def shannon_entropy(value)` - *Bits of entropy per character; random credentials score high, English prose low.*
- `def is_strongly_allowlisted(line)` - *An explicit pragma or an unambiguous placeholder suppresses every detector.*
- `def is_weakly_allowlisted(line)` - *A hint like "example" suppresses only the low-confidence entropy fallback.*
- `def scan_text(label, text)` - *Return (label, line_no, detector, excerpt) for every finding in a blob of text.*
- `def should_skip(path_str)`
- `def git_output(args)`
- `def scan_staged(gaps)` - *Scan staged content only - the surface about to become permanent history.*
- `def iter_tracked_files(gaps)`
- `def scan_all(gaps)`
- `def scan_agent_memory(gaps)` - *PRINCIPLE-019 Rule 3: agent working memory is tracked output. The ledger's free-text impact*
- `def run_scan(mode, target, verbose)` - *Scan the requested surface plus agent memory, reporting tersely (PRINCIPLE-012 R4).*

---

### [`scripts/disruption_recovery.py`](scripts/disruption_recovery.py)
> *Disruption Recovery & Task Progress Ledger (PRINCIPLE-006, PRINCIPLE-013)*

**Size**: `1193` lines (`51612` bytes)

**Functions:**
- `def get_ledger_path(custom_dir)` - *Return path to task ledger, creating parent directories if needed.*
- `def file_lock(lock_path, timeout_seconds, poll_interval)` - *Cross-platform cooperative advisory lock (PRINCIPLE-013).*
- `def locked_ledger(ledger_file, timeout_seconds, poll_interval)` - *Serialize a full read-modify-write cycle on the task ledger (PRINCIPLE-013 Rule 3).*
- `def fsync_dir(dir_path)` - *Flush a directory entry so a completed `os.replace` survives power loss (PRINCIPLE-013 R1).*
- `def check_disk_headroom(target_dir, min_mb)` - *Check whether sufficient disk headroom exists before writing (PRINCIPLE-013).*
- `def migrate_ledger_schema(data)` - *Ensure recovered or loaded ledger conforms to current schema specification (PRINCIPLE-013).*
- `def atomic_write_json(file_path, data, max_retries, min_headroom_mb)` - *Atomically write JSON data using fsync, shadow backup, and temporary replacement (PRINCIPLE-013).*
- `def load_ledger(ledger_file)` - *Safely load the task ledger with startup self-healing (PRINCIPLE-013).*
- `def prune_checkpoints(checkpoints, active_task_id, max_history)` - *Prune checkpoints to maintain a bounded rolling memory window (PRINCIPLE-004).*
- `def task_plan_checkpoint(task_checkpoints)` - *The task's plan (PRINCIPLE-004 R1): its latest Phase 2 checkpoint whose description starts*
- `def save_ledger(ledger, ledger_file, max_history, _locked)` - *Save the task ledger atomically to disk with bounded rolling history (PRINCIPLE-004).*
- `def resolve_phase_num(phase, explicit_num)` - *Resolve lifecycle phase number 1..5 for compaction orientation (PRINCIPLE-002).*
- `def classify_git_status(porcelain_output)` - *Classify `git status --porcelain` v1 output into disruption categories (PRINCIPLE-006 R2).*
- `def resolve_active_phase(active_task, default)` - *Read the recorded lifecycle phase of a task (PRINCIPLE-002 R4, PRINCIPLE-004 R2).*
- `def record_checkpoint(task_id, phase, description, files_affected, status, ledger_file, phase_num, why, benefits, risks, mitigation)` - *Record an atomic micro-checkpoint in the task ledger (PRINCIPLE-002, PRINCIPLE-006, PRINCIPLE-007).*
- `def mark_task_completed(task_id, ledger_file)` - *Mark the active task completed (locked, PRINCIPLE-013 R3). Returns False, changing nothing,*
- `def reset_active_task(reason, ledger_file)` - *Abandon or reset the active in-progress task in the ledger (locked, PRINCIPLE-006).*
- `def clean_dangling_temp_files(workspace_dir)` - *Scan and safely purge orphaned *.tmp_* files left by interrupted writes (PRINCIPLE-006, PRINCIPLE-013).*
- `def git_porcelain_status(workspace)` - *Default git adapter: run `git status --porcelain` in `workspace` (bounded, PRINCIPLE-010 R3).*
- `def run_disruption_audit(workspace_dir, git_status)` - *Execute a comprehensive pre-flight disruption audit (PRINCIPLE-006, PRINCIPLE-007).*
- `def append_file_list(lines, title, files, cap)` - *Append a titled file list of at most `cap` entries, so a huge tree stays bounded (PRINCIPLE-004 R5).*
- `def audit_body_lines(audit)` - *Findings shared by --audit and --resume, so neither report hides what the other shows.*
- `def format_audit_report(audit)` - *Generate human and AI-readable disruption recovery audit report.*
- `def format_resume_report(audit)` - *The one cold-start report (PRINCIPLE-004 R2): every --audit finding, then where to resume.*
- `def validate_conventional_commit(message)` - *Validate that a commit message conforms to Conventional Commits (PRINCIPLE-018).*
- `def _ast_without_docstrings(source)` - *AST dump with docstrings removed; comments and formatting never reach the AST.*
- `def classify_change(path, old, new)` - *Return (track, reason) for one changed file. Pure: no I/O.*
- `def classify_track(changes)` - *Classify a change set into Track A, B or C (PRINCIPLE-002 R3). Pure: no I/O.*
- `def collect_working_changes(workspace)` - *Read every changed, staged or untracked file versus HEAD (git adapter for --track).*
- `def validate_argv(argv)` - *Return unrecognized options, skipping values of known value-taking flags (PRINCIPLE-011).*
- `def argv_value_errors(argv)` - *Value flags given without a value, or with an invalid one (PRINCIPLE-003 R6). These used to*

---

### [`scripts/dogfood.py`](scripts/dogfood.py)
> *Operational Dogfooding Runner (PRINCIPLE-015)*

**Size**: `462` lines (`19997` bytes)

**Functions:**
- `def terminate_process_tree(proc)` - *Kill a process and all of its children (PRINCIPLE-015 Rule 2).*
- `def supervised(argv, cwd)` - *RAII supervisor: guarantees recursive teardown even if the body raises.*
- `def sandbox_jail()` - *Ephemeral workspace outside the repository and outside host user directories*
- `def run_cli(script, args, cwd)` - *Invoke a CLI as a real binary with stdin closed (PRINCIPLE-015 Rule 3 EOF safety).*
- `def repo_fingerprint()` - *Content fingerprint of the repository working tree, or None when git is unavailable.*
- `def track_golden_lifecycle(jail, log)` - *Track 1 (PRINCIPLE-015 Rule 5): a complete create -> modify -> retrieve lifecycle driven*
- `def track_chaos_perturbation(jail, log)` - *Track 2 (PRINCIPLE-015 Rule 5): hostile perturbations. Each must fail cleanly with no*
- `def track_readonly_gates(jail, log)` - *Track 3: the two freshness gates the delivery triad depends on must run read-only from an*
- `def track_help_startup_budget(jail, log)` - *Track 4: every entrypoint must answer --help safely and inside the PRINCIPLE-010 R5*
- `def run_dogfood(verbose, keep_sandbox)` - *Execute every dogfood track and emit a terse dashboard (PRINCIPLE-015 Rule 7).*

---

### [`scripts/sync_principles.py`](scripts/sync_principles.py)
> *Principles Auto-Sync Tool (PRINCIPLE-017)*

**Size**: `670` lines (`32197` bytes)

**Functions:**
- `def is_generated_target(text)` - *True when `text` carries this tool's generated-file header (current or legacy).*
- `def estimate_tokens(text)` - *Estimate tokens as chars // 4.*
- `def fsync_dir(dir_path)` - *Flush the directory entry so a completed os.replace survives power loss (PRINCIPLE-013 R1).*
- `def load_tier_1b_domain_rules(domain_path)` - *Load project-specific domain rules from .agents/rules/domain.md if present (PRINCIPLE-001, PRINCIPLE-017).*
- `def append_domain_rules(lines, domain_rules)` - *Helper to append Tier 1B domain rules to prompt targets.*
- `def parse_principles(agents_file, strict)` - *Parse the principle SSOT, enforce strict schema validation, reject duplicate IDs, and verify monotonic lifecycle progression.*
- `def _parse_principles_uncached(content, strict)` - *Parsing and validation proper; see parse_principles().*
- `def validate_triad_consistency(principles, readme_file)` - *Verify the documentation triad's public leg: README.md lists every principle (PRINCIPLE-017).*
- `def tier1_title(title)` - *Drop a trailing parenthetical subtitle in Tier 1; the full title stays in Tier 2.*
- `def render_tier1_target(heading, principles, domain_rules)` - *Render one always-injected Tier 1 target (PRINCIPLE-001 R1/R3, PRINCIPLE-017 R2).*
- `def audit_tier1_budget(principles, domain_rules)` - *Enforce the Tier 1 context budget on every target (PRINCIPLE-001 R4/R6/R9).*
- `def sync_all(check_only, exit_on_mismatch, domain_path, readme_file)` - *Generate every always-injected Tier 1 target from the principle SSOT.*
- `def involved_principles(principles, text)` - *Compute which principles a situation involves (PRINCIPLE-001 R3), identically for every agent.*
- `def principle_sections(ssot_text)` - *Each `### PRINCIPLE-NNN:` section's text, ending at the next heading of level 2 or 3.*
- `def citing_principles(ssot_text, pid)` - *The principles a change to `pid` must be checked against (PRINCIPLE-000 R3): those whose*
- `def _adr_blocks(decisions)` - *ADR ID -> its text, for every `### ADR-NNN:` heading.*
- `def changed_principles(old_text, new_text)` - *Principles whose `### PRINCIPLE-NNN:` section differs between two texts (PRINCIPLE-000 R3).*
- `def cross_check_errors(old_text, new_text, old_decisions, new_decisions)` - *PRINCIPLE-000 R3 made decidable: every principle whose section changed since the last commit*
- `def git_head_text(rel_path)` - *`rel_path` as committed at HEAD, or None when git, a commit or the file is missing.*
- `def print_help()` - *Print command line usage for sync_principles.py.*

---

### [`scripts/update_knowledge_base.py`](scripts/update_knowledge_base.py)
> *Codebase Knowledge Base Auto-Updater & Validator (PRINCIPLE-016)*

**Size**: `627` lines (`25609` bytes)

**Functions:**
- `def fsync_dir(dir_path)` - *Flush the directory entry so a completed os.replace survives power loss (PRINCIPLE-013 R1).*
- `def render_signature(node, drop_self)` - *Render a complete call signature from an AST function node (PRINCIPLE-003, PRINCIPLE-016).*
- `def extract_python_symbols(file_path, strict)` - *Parse a python file with AST and extract docstrings, classes, and functions (PRINCIPLE-003).*
- `def _extract_symbols_uncached(file_path, content, strict)` - *AST extraction proper; see extract_python_symbols().*
- `def find_python_files(root)` - *Dynamically discover all source python files across the repository.*
- `def generate_codebase_map(root, strict)` - *Generate the markdown content for knowledge/codebase_map.md with AST validation (PRINCIPLE-003).*
- `def validate_knowledge_links(knowledge_dir)` - *Verify that all relative file links in knowledge/INDEX.md physically exist on disk (PRINCIPLE-016).*
- `def audit_adr_register(decisions)` - *ADR IDs must be unique and consecutive (PRINCIPLE-016 R3, PRINCIPLE-000 R3). Two sessions that*
- `def check_codebase_map_freshness(knowledge_dir, strict)` - *Check if codebase_map.md accurately reflects current codebase AST (PRINCIPLE-016).*
- `def update_and_validate(knowledge_dir, strict)`
- `def quick_reference_errors(readme)` - *The structure PRINCIPLE-005 R1 states, not just its words: a heading, then inside its section*
- `def parse_readme_tree(readme)` - *Paths in the first ```text block after "What's Inside" (PRINCIPLE-005 R5), relative to the*
- `def audit_readme(readme, tracked, exists, script_source)` - *Every PRINCIPLE-005 rule a program can decide, as one error per violation. Pure: the caller*
- `def check_readme(root)` - *Run `audit_readme` on `root`, listing tracked files with git (bounded, PRINCIPLE-010 R3).*
- `def report_readme(errors)` - *Print README findings with the remediation triad (PRINCIPLE-011 R6); True when clean.*
- `def _validate_argv(argv, known, help_text)` - *Short-circuit on --help and reject unknown flags with exit 2 (PRINCIPLE-011, PRINCIPLE-015).*

---

### [`tests/test_integration.py`](tests/test_integration.py)
> *Integration & Operational Dogfooding Tier (PRINCIPLE-014, PRINCIPLE-015).*

**Size**: `558` lines (`26054` bytes)

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
- `class TestWorkspaceIsolation` - *`disruption_recovery.py` anchors its ledger to the repository, not the working directory, so*
  - Method `.setUp()`
  - Method `._ledger_cli(*args)`
  - Method `.test_workspace_flag_redirects_the_ledger()`
  - Method `.test_workspace_without_value_is_refused()`
  - Method `.test_audit_and_resume_honour_the_workspace()`
- `class TestDogfoodRunner` - *The operational dogfood runner is itself a shipped surface (PRINCIPLE-015), so it carries*
  - Method `.setUpClass()`
  - Method `.test_dogfood_run_passes_every_track()`
  - Method `.test_dogfood_reports_tersely()`
  - Method `.test_dogfood_covers_golden_and_chaos_tracks()`
  - Method `.test_dogfood_emits_no_unhandled_traceback()`
  - Method `.test_dogfood_writes_its_declared_log()`
  - Method `.test_dogfood_leaves_tracked_content_untouched()`
  - Method `.test_dogfood_cli_contract()`
- `class TestInvolvedCli` - *`sync_principles.py --involved` is the authoritative answer to PRINCIPLE-001 R3.*
  - Method `._run(*args)`
  - Method `.test_lists_involved_principles_one_per_line()`
  - Method `.test_text_after_involved_is_never_parsed_as_options()`
  - Method `.test_missing_text_is_misuse()`
  - Method `.test_citing_lists_the_cross_principle_set_and_rejects_unknown_ids()`
- `class TestTrackCli` - *`disruption_recovery.py --track` reads real git state (PRINCIPLE-002 R3).*
  - Method `.test_track_follows_the_actual_diff()`
- `class TestCallSiteCommand` - *PRINCIPLE-003 R2's exact command must work for every name kind it covers, flags included.*
  - Method `.test_command_finds_a_flag()`
- `class TestAstGateCli` - *PRINCIPLE-003 R7: the gate halts with file and line, never a raw traceback.*
  - Method `.test_syntax_error_halts_cleanly()`
- `class TestRepositorySecretHygiene` - *PRINCIPLE-019 live invariant. Integration tier: the scan shells out to `git ls-files`.*
  - Method `.test_this_repository_is_clean()`
- `class TestReadmeDriftShield` - *PRINCIPLE-005 live invariant. Integration tier: completeness shells out to `git ls-files`.*
  - Method `.test_this_readme_matches_the_tracked_tree()`
- `class TestTierBudgetDiscipline` - *Structural enforcement of the two-tier test budget (PRINCIPLE-010 R6, PRINCIPLE-014 R3).*
  - Method `.test_unit_tier_spawns_no_processes_and_never_sleeps()`
  - Method `.test_unit_tier_guards_itself_against_spawns()`
  - Method `.test_integration_tier_bounds_every_spawn()`

---

### [`tests/test_kit.py`](tests/test_kit.py)
> *Automated Test Suite for Portable Agent Kit (PRINCIPLE-011, PRINCIPLE-016)*

**Size**: `2577` lines (`141234` bytes)

**Classes:**
- `class TestPrincipleSync` - *Verifies that all 20 principles are maintained and synchronized (PRINCIPLE-001, PRINCIPLE-017).*
  - Method `.test_parse_all_principles()`
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
  - Method `.test_principle_000_meta_principle_capsule()`
  - Method `.test_guideline_targets_freshness_gate()`
  - Method `.test_triad_consistency_gate()`
  - Method `.test_checklists_cover_every_principle()`
  - Method `.test_no_stale_principle_counts_in_docs()`
  - Method `.test_principle_count_constants_agree()`
  - Method `.test_adopter_readme_without_principles_is_not_drift()`
  - Method `.test_aikit_readme_lists_every_principle_strictly()`
  - Method `.test_single_ssot_and_generated_agents_md()`
  - Method `.test_principle_schema_strictness()`
  - Method `.test_last_principle_block_stops_at_next_section()`
  - Method `.test_tier_1b_domain_rules_injection()`
  - Method `.test_domain_rules_template_validity()`
  - Method `.test_readme_cold_start_orientation_and_script_parity()`
- `class TestPrinciple005ReadmeGate` - *PRINCIPLE-005: every README rule a program can decide is decided by `audit_readme`.*
  - Method `.audit(readme, tracked, exists)`
  - Method `.test_a_correct_readme_passes()`
  - Method `.test_tree_paths_and_directories()`
  - Method `.test_a_dead_tree_path_fails()`
  - Method `.test_a_missing_top_level_entry_fails()`
  - Method `.test_an_expanded_directory_must_be_complete_and_a_collapsed_one_need_not()`
  - Method `.test_documented_commands_must_exist()`
  - Method `.test_size_labels_and_tree_are_required()`
  - Method `.test_a_prose_mention_is_not_the_tree_heading()`
  - Method `.test_quick_reference_is_checked_by_structure_not_words()`
  - Method `.test_the_adopter_template_fails_unfilled_and_passes_filled()`
- `class TestAdrRegister` - *PRINCIPLE-016 R3 / PRINCIPLE-000 R3: ADR IDs are unique and consecutive (ADR-069).*
  - Method `.register(*numbers)`
  - Method `.test_consecutive_ids_pass()`
  - Method `.test_a_duplicate_fails()`
  - Method `.test_a_gap_fails()`
  - Method `.test_this_register_is_clean()`
- `class TestPrinciple005Unambiguity` - *PRINCIPLE-005 must say the same thing to every model: exact labels, triggers and homes.*
  - Method `.setUpClass()`
  - Method `.test_rules_contain_no_hedge_words()`
  - Method `.test_every_rule_names_its_audience()`
  - Method `.test_rule_labels_are_the_ones_the_gate_checks()`
  - Method `.test_every_trigger_and_home_is_defined()`
  - Method `.test_checklists_match_the_rules()`
- `class TestPrinciple000Unambiguity` - *PRINCIPLE-000 must pass its own R7: every meta-rule is decidable, none licenses skipping.*
  - Method `.setUpClass()`
  - Method `.test_r7_word_list_is_the_hedge_list()`
  - Method `.test_principle_000_obeys_its_own_r7()`
  - Method `.test_every_rule_names_its_audience()`
  - Method `.test_every_meta_rule_is_decidable()`
  - Method `.test_second_pass_definitions()`
  - Method `.test_citing_set_is_computed_from_sections_only()`
  - Method `.test_r3_completeness_is_decided_by_the_gate()`
  - Method `.test_capsule_does_not_license_skipping_procedure()`
  - Method `.test_rule_changes_carry_a_cross_principle_check()`
- `class TestPrinciple001Unambiguity` - *PRINCIPLE-001 must say the same thing to every model. These tests make that mechanical:*
  - Method `.setUpClass()`
  - Method `.test_rules_contain_no_hedge_words()`
  - Method `.test_every_rule_names_its_audience()`
  - Method `.test_rules_use_normative_keywords()`
  - Method `.test_tier1_header_mirrors_r3_triggers_and_r1_precedence()`
  - Method `.test_every_agent_rule_reaches_tier1()`
  - Method `.test_precedence_never_contradicts_another_principle()`
  - Method `.test_open_terms_are_defined()`
  - Method `.test_involvement_is_deterministic()`
  - Method `.test_common_words_do_not_involve_principles()`
  - Method `.test_single_id_placeholder()`
  - Method `.test_tool_neutral_retrieval()`
- `class TestPrinciple002Unambiguity` - *PRINCIPLE-002 must give every model the same track, the same phase gates and the same*
  - Method `.setUpClass()`
  - Method `._rule(pid, number)`
  - Method `.test_rules_contain_no_hedge_words()`
  - Method `.test_every_rule_names_its_audience()`
  - Method `.test_open_decisions_are_defined()`
  - Method `.test_cross_references_resolve()`
  - Method `.test_p001_precedence_points_at_this_r5()`
  - Method `.test_checklists_are_in_principle_order()`
- `class TestPrinciple003Unambiguity` - *PRINCIPLE-003 must give every model the same grounding steps and the same answer to "is this*
  - Method `.setUpClass()`
  - Method `.test_rules_contain_no_hedge_words()`
  - Method `.test_every_rule_names_its_audience()`
  - Method `.test_ambiguity_split_is_decided_by_one_question()`
  - Method `.test_open_terms_are_defined()`
  - Method `.test_cross_references_resolve()`
  - Method `.test_every_external_program_the_scripts_run_is_declared()`
  - Method `.test_no_silent_broad_exception_handlers()`
  - Method `.test_user_facing_commands_use_python_not_py()`
  - Method `.test_unmeasurable_disk_space_is_announced()`
  - Method `.test_unreadable_backup_is_announced()`
  - Method `.test_failed_audit_scan_is_never_reported_clean()`
  - Method `.test_ast_gate_rejects_syntax_newer_than_the_minimum()`
  - Method `.test_no_standard_library_apis_newer_than_the_minimum()`
  - Method `.test_scripts_follow_platform_parity()`
- `class TestPrinciple004Unambiguity` - *PRINCIPLE-004 must name where each kind of state is written and how it is read back, so no*
  - Method `.setUpClass()`
  - Method `.test_rules_contain_no_hedge_words()`
  - Method `.test_every_rule_names_its_audience()`
  - Method `.test_every_kind_of_state_has_one_home()`
  - Method `.test_no_second_resumption_procedure()`
  - Method `.test_one_cold_start_command_everywhere()`
  - Method `.test_fifteen_line_limit_has_one_owner()`
  - Method `.test_no_unobservable_obligation()`
  - Method `.test_resume_never_says_ready_over_uncommitted_files()`
  - Method `.test_report_file_lists_are_bounded()`
  - Method `.test_schemas_are_not_sent_to_adrs()`
  - Method `.test_active_task_is_bounded_and_keeps_its_plan()`
  - Method `.test_resume_prints_the_plan()`
  - Method `.test_revised_plan_replaces_the_old_one_and_answers_do_not()`
  - Method `.test_cli_never_replaces_a_missing_value_with_a_default()`
  - Method `.test_completing_a_task_that_is_not_active_changes_nothing()`
- `class TestLifecycleToolSemantics` - *PRINCIPLE-002 delegates decisions to commands; each command must mean what the rule says.*
  - Method `.test_bare_digit_phase_is_that_phase()`
  - Method `.test_resume_stays_in_the_recorded_phase_on_a_clean_tree()`
  - Method `.test_audit_ignores_the_ledger()`
  - Method `.test_p002_names_one_resume_line_and_defines_cold_start()`
  - Method `.test_caches_never_leak_or_go_stale()`
  - Method `.test_every_command_in_the_rules_exists()`
- `class TestTrackClassification` - *PRINCIPLE-002 R3: the track is computed, so every model assigns the same one.*
  - Method `.test_no_changes_is_track_a()`
  - Method `.test_documentation_is_track_b()`
  - Method `.test_comment_and_docstring_edits_are_track_b()`
  - Method `.test_logic_change_is_track_c()`
  - Method `.test_rule_text_and_generated_files_are_track_c()`
  - Method `.test_config_tests_and_new_python_are_track_c()`
  - Method `.test_unplanned_files_criterion_is_gone()`
  - Method `.test_highest_track_wins()`
- `class TestSyncWriteSafety` - *ADR-048. Sync now writes AGENTS.md, which older layouts used as the hand-authored rule source,*
  - Method `.setUp()`
  - Method `._sync(check_only)`
  - Method `._written_targets()`
  - Method `.test_clean_sandbox_generates_every_target()`
  - Method `.test_hand_authored_file_is_never_overwritten()`
  - Method `.test_protection_is_all_or_nothing()`
  - Method `.test_legacy_generated_target_is_upgraded()`
  - Method `.test_unmigrated_layout_gets_migration_guidance_not_a_traceback()`
  - Method `.test_generated_marker_detection()`
- `class TestTier1ContextBudget` - *PRINCIPLE-001 R6/R9. Always-injected rules cost context on every turn in every IDE, so the*
  - Method `.test_every_target_is_within_the_token_target()`
  - Method `.test_token_overage_blocks_rather_than_warns()`
  - Method `.test_shipped_domain_template_syncs_within_budget()`
  - Method `.test_universal_rules_reserve_full_tier1b_headroom()`
  - Method `.test_headroom_breach_is_detected()`
  - Method `.test_advisory_warning_cannot_shadow_a_violation()`
  - Method `.test_token_estimate_is_conservative()`
  - Method `.test_grep_anchor_contract_survives_in_every_target()`
  - Method `.test_capsules_retain_their_mechanisms_after_condensation()`
- `class TestSecretHygieneScanner` - *PRINCIPLE-019. Secret leakage is the one defect class with no clean rollback, so the scanner*
  - Method `.test_a_scan_that_skipped_a_surface_never_reports_clean()`
  - Method `.test_detects_known_credential_shapes()`
  - Method `.test_does_not_flag_indirection_or_placeholders()`
  - Method `.test_weak_allowlist_cannot_veto_a_pattern_match()`
  - Method `.test_weak_allowlist_still_suppresses_entropy_fallback()`
  - Method `.test_explicit_pragma_suppresses_everything()`
  - Method `.test_entropy_separates_random_from_prose()`
  - Method `.test_agent_memory_free_text_is_scanned()`
  - Method `.test_gitignore_carries_the_credential_baseline()`
- `class TestInvariantReachabilityShield` - *PRINCIPLE-014 R7. A passing test proves a mechanism works, never that it is used. These*
  - Method `.setUp()`
  - Method `._write(name, source)`
  - Method `.test_detects_capability_with_zero_production_call_sites()`
  - Method `.test_detects_state_key_read_with_no_producer()`
  - Method `.test_key_with_a_producer_is_not_flagged()`
  - Method `.test_this_repository_passes_the_shield()`
  - Method `.test_allowlist_entries_still_exist()`
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

**Functions:**
- `def _refuse_spawn(popen_self, args, *unused_args, **unused_kwargs)`
- `def setUpModule()`
- `def tearDownModule()`
- `def not_a_git_repo(workspace)` - *In-process stand-in for `git status` in a non-repository: exactly what real git returns*

---
