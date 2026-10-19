# Codebase Map & Symbol Catalog 🗺️

> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**
> This document provides an automated, up-to-date registry of all modules, classes, and exported functions across this repository.

---

## 📊 Codebase Metrics
- **Total Python Modules**: `16`
- **Total Classes**: `76`
- **Total Top-Level Functions**: `237`
- **Total Class Methods**: `442`
- **Total Source Lines**: `12519`

---

## 📦 Modules & Exported Symbols

### [`aikit.py`](aikit.py)
> *AIKit entry point: `python aikit.py --help`. The commands live in scripts/aikit_cli.py.*

**Size**: `9` lines (`214` bytes)

---

### [`scripts/aikit_cli.py`](scripts/aikit_cli.py)
> *`aikit` command line: create, attach, list, report on, check, fix and delegate for the projects*

**Size**: `409` lines (`19434` bytes)

**Classes:**
- `class TriadArgumentParser` - *argparse whose usage errors carry Why/Fix like every other AIKit error.*
  - Method `.error(message)`

**Functions:**
- `def report_error(error)` - *Print the error triad to stderr and return its exit code.*
- `def build_parser()`
- `def present_project(name, workspace)` - *The registered project `name`, refusing one whose folder or record is gone.*
- `def print_guidelines(project)` - *The project's own rules, with their rank, in every cold-start report (PRINCIPLE-004 R2).*
- `def cmd_new(args)`
- `def cmd_attach(args)`
- `def cmd_list(args)`
- `def cmd_status(args)`
- `def cmd_resume(args)`
- `def cmd_guideline(args)`
- `def cmd_checkpoint(args)`
- `def cmd_complete(args)`
- `def cmd_clean(args)`
- `def project_baseline_errors(project, audit)` - *The delivery baseline `--strict` requires; ordinary check reports these as warnings.*
- `def cmd_check(args)`
- `def cmd_fix(args)` - *Repair what AIKit can repair mechanically, then run the gates: everything left is the*
- `def cmd_publish(args)`
- `def cmd_delegate(args)`
- `def main(argv)`

---

### [`scripts/check_project_hygiene.py`](scripts/check_project_hygiene.py)
> *Project hygiene scan (PRINCIPLE-003 R4, PRINCIPLE-010, PRINCIPLE-011 R3, PRINCIPLE-000 R5).*

**Size**: `438` lines (`20028` bytes)

**Classes:**
- `class Finding` - *One violation, addressed to the line a developer must change.*
  - Method `.render()` - *The one-line report form: `path:line [rule] message`.*

**Functions:**
- `def _keyword(call, name)` - *The value of `call`'s keyword `name`, or None when the call omits it.*
- `def _true_literal(node)` - *Whether the expression is the literal `True` (a name called `True` cannot exist).*
- `def _subprocess_aliases(tree)` - *Names `subprocess` members were imported under, so `from subprocess import run` is seen.*
- `def _subprocess_call(node, aliases)` - *The node as a `subprocess` call (module-qualified or imported by name), else None.*
- `def check_banned_calls(rel, tree)` - *PRINCIPLE-003 R4 and PRINCIPLE-010: calls that lose quoting or execute data as code.*
- `def check_subprocess_calls(rel, tree)` - *PRINCIPLE-003 R4 and PRINCIPLE-010: portable, bounded, list-passed subprocess calls.*
- `def check_environ_index(rel, tree)` - *PRINCIPLE-011 R3: a hard-indexed environment variable crashes where it is unset.*
- `def _open_mode(call)` - *The literal mode of an open() call, or None when binary-ness is not decidable.*
- `def _is_open_call(node)` - *Whether the node is a builtin `open(...)` or an object's `.open(...)` method call.*
- `def check_open_calls(rel, tree)` - *PRINCIPLE-003 R4 and PRINCIPLE-010: text mode needs an explicit encoding and a with block.*
- `def check_silent_except(rel, tree)` - *PRINCIPLE-000 R5: a handler that discards the error and does nothing hides the failure.*
- `def _docstring_ids(tree)` - *Ids of docstring constants: prose may name any path without baking it into behaviour.*
- `def _call_head(node)` - *The called function's final name: `Path` for Path(...), `join` for os.path.join(...).*
- `def _direct_arguments(call)` - *Positional and keyword argument expressions of a call.*
- `def check_absolute_paths(rel, tree)` - *PRINCIPLE-003 R4: a machine-specific path reaching file access breaks every other machine.*
- `def check_asset_source(rel, source)` - *PRINCIPLE-003 R3: a static asset that loads from a third party is a hidden dependency.*
- `def _marked(lines, line)` - *Whether the finding's own line carries a deliberated `hygiene: allow <reason>` marker.*
- `def check_python_source(rel, source)` - *Every Python finding in one source text; findings on `hygiene: allow` lines are dropped.*
- `def _read_source(rel, path)` - *The file's UTF-8 text, or the finding that replaces it (PRINCIPLE-000 R5: no silent skip).*
- `def scan_tree(root)` - *Every hygiene finding under `root` in stable order. Generated and vendored directories are*
- `def run_scan(root)` - *Scan `root` and print the report; the process exit code (PRINCIPLE-012 R4: terse).*
- `def main(argv)` - *Parse `--workspace` and run; argument misuse returns 2 with the Why/Fix triad.*

---

### [`scripts/check_reachability.py`](scripts/check_reachability.py)
> *Invariant Reachability Shield (PRINCIPLE-014 Rule 7)*

**Size**: `310` lines (`12450` bytes)

**Functions:**
- `def parse_module(path)` - *Parse a module once per content. Every analysis below walks the same files, and parsing each*
- `def module_nodes(path)` - *Every node of the module, walked once per parsed tree: references, state keys and literals*
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

**Size**: `463` lines (`20969` bytes)

**Functions:**
- `def shannon_entropy(value)` - *Bits of entropy per character; random credentials score high, English prose low.*
- `def is_strongly_allowlisted(line)` - *An explicit pragma or an unambiguous placeholder suppresses every detector.*
- `def is_weakly_allowlisted(line)` - *A hint like "example" suppresses only the low-confidence entropy fallback.*
- `def scan_text(label, text)` - *Return (label, line_no, detector, excerpt) for every finding in a blob of text.*
- `def looks_random(value)` - *A token shaped like a generated key: mixed case and digits, and high entropy. Hex digests*
- `def redact(line, start, end)` - *The line with the secret span cut to its first 4 characters plus `***` (PRINCIPLE-019 R4).*
- `def should_skip(path_str)`
- `def git_output(args, repo)`
- `def scan_staged(gaps, repo)` - *Scan staged content only - the surface about to become permanent history.*
- `def scan_diff(diff, default_label)` - *Every added line of a unified diff, labelled by its file. Pure: removed lines are history*
- `def scan_commits(rev_range, gaps, repo)` - *Every line the commits in `rev_range` add: what a push uploads. The working tree is not, so a*
- `def iter_tracked_files(gaps, repo)`
- `def scan_all(gaps, repo)`
- `def scan_agent_memory(gaps, repo)` - *PRINCIPLE-019 Rule 3: agent working memory is tracked output. The ledger's free-text impact*
- `def run_scan(mode, target, verbose, repo, commits)` - *Scan the requested surface plus agent memory, reporting tersely (PRINCIPLE-012 R4).*

---

### [`scripts/check_test_budgets.py`](scripts/check_test_budgets.py)
> *Test Tier Budget Gate (PRINCIPLE-010 Rule 6, PRINCIPLE-014 Rule 3)*

**Size**: `185` lines (`7102` bytes)

**Classes:**
- `class TierResult` - *One tier's measured outcome; frozen so a report cannot edit what was measured.*
  - Property `.per_test_ms`
  - Property `.budget_ms`
  - Property `.inside_budget`

**Functions:**
- `def parse_tier_output(output)` - *The count and duration unittest prints, or None when it never got that far.*
- `def default_runner(module, timeout)` - *Run one tier the way the runbook documents it, so the gate measures the real command.*
- `def run_tier(module, runner)` - *Measure one tier, or None when its output carried no summary to measure.*
- `def budget_errors(results)` - *One line per tier that is over its ceiling; empty when every tier fits.*
- `def run_check(runner, verbose)`

---

### [`scripts/disruption_recovery.py`](scripts/disruption_recovery.py)
> *Disruption Recovery & Task Progress Ledger (PRINCIPLE-006, PRINCIPLE-013)*

**Size**: `1502` lines (`67652` bytes)

**Classes:**
- `class UnsupportedLedgerVersion` - *A ledger declares a schema this build cannot read (PRINCIPLE-013 R4, PRINCIPLE-016 R5).*
  - Method `.__init__(path, found, supported)`

**Functions:**
- `def empty_ledger()` - *A fresh in-memory ledger; load_ledger() never creates the file for this.*
- `def workspace_ledger_path(workspace)` - *The ledger of `workspace`: `<workspace>/.aikit/task_ledger.json` for a project AIKit builds,*
- `def get_ledger_path(custom_dir)` - *Return path to task ledger, creating parent directories if needed.*
- `def file_lock(lock_path, timeout_seconds, poll_interval)` - *Cross-platform cooperative advisory lock (PRINCIPLE-013).*
- `def locked_ledger(ledger_file, timeout_seconds, poll_interval)` - *Serialize a full read-modify-write cycle on the task ledger (PRINCIPLE-013 Rule 3).*
- `def fsync_dir(dir_path)` - *Flush a directory entry so a completed `os.replace` survives power loss (PRINCIPLE-013 R1).*
- `def check_disk_headroom(target_dir, min_mb)` - *Check whether sufficient disk headroom exists before writing (PRINCIPLE-013).*
- `def validate_ledger_version(data, path)` - *Refuse a ledger whose declared schema this build does not read (PRINCIPLE-013 R4).*
- `def _read_ledger_file(path)` - *Parse one ledger file, validate its version, then normalize it in memory.*
- `def _quarantine_ledger(path)` - *Move a corrupt ledger aside without overwriting an earlier quarantine in the same second.*
- `def migrate_ledger_schema(data)` - *Ensure recovered or loaded ledger conforms to current schema specification (PRINCIPLE-013).*
- `def atomic_write_json(file_path, data, max_retries, min_headroom_mb)` - *Atomically write JSON data using fsync, shadow backup, and temporary replacement (PRINCIPLE-013).*
- `def load_ledger(ledger_file)` - *Safely load the task ledger with startup self-healing (PRINCIPLE-013).*
- `def prune_checkpoints(checkpoints, active_task_id, max_history)` - *Prune checkpoints to maintain a bounded rolling memory window (PRINCIPLE-004).*
- `def task_plan_checkpoint(task_checkpoints)` - *The task's plan (PRINCIPLE-004 R1): its latest Phase 2 checkpoint whose description starts*
- `def _refuse_newer_ledger_on_disk(path)` - *Re-check both slots under the lock before replacing either (PRINCIPLE-013 R3).*
- `def save_ledger(ledger, ledger_file, max_history, _locked)` - *Save the task ledger atomically to disk with bounded rolling history (PRINCIPLE-004).*
- `def resolve_phase_num(phase, explicit_num)` - *Resolve lifecycle phase number 1..5 for compaction orientation (PRINCIPLE-002).*
- `def classify_git_status(porcelain_output)` - *Classify `git status --porcelain` v1 output into disruption categories (PRINCIPLE-006 R2).*
- `def resolve_active_phase(active_task, default)` - *Read the recorded lifecycle phase of a task (PRINCIPLE-002 R4, PRINCIPLE-004 R2).*
- `def repo_relative(path)` - *A path as the ledger stores it (PRINCIPLE-012 R5): repository-relative with `/` separators*
- `def record_checkpoint(task_id, phase, description, files_affected, status, ledger_file, phase_num, why, benefits, risks, mitigation)` - *Record an atomic micro-checkpoint in the task ledger (PRINCIPLE-002, PRINCIPLE-006, PRINCIPLE-007).*
- `def mark_task_completed(task_id, ledger_file)` - *Mark the active task completed (locked, PRINCIPLE-013 R3). Returns False, changing nothing,*
- `def reset_active_task(reason, ledger_file)` - *Abandon or reset the active in-progress task in the ledger (locked, PRINCIPLE-006).*
- `def _reraise(error)`
- `def sweep_files(workspace_dir, pattern)` - *Files under `workspace_dir` matching `pattern`, pruning `SWEEP_PRUNED_DIRS` while walking, so a*
- `def clean_dangling_temp_files(workspace_dir, min_age_seconds)` - *Purge orphaned *.tmp_* files left by interrupted writes (PRINCIPLE-006 R6, PRINCIPLE-013).*
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
- `def report_operational_error(exc_type, exc, tb)` - *`sys.excepthook` for the CLI (PRINCIPLE-011 R6, PRINCIPLE-013 R2/R5): an operational failure*
- `def validate_argv(argv)` - *Return unrecognized options, skipping values of known value-taking flags (PRINCIPLE-011).*
- `def impact_errors(description, phase_num, fields, has_prior_impact)` - *PRINCIPLE-007 R6: a task's first plan checkpoint (Phase 2, `--desc` starting `[1/`) carries the*
- `def missing_impact_warning(task_id, phase_num, has_prior_impact, has_impact_now)` - *PRINCIPLE-007 R1: a Track C task records its impact assessment before its first edit. A task*
- `def checkpoint_command(task_id, phase, phase_num, desc, impact, ledger_file)` - *Record a checkpoint behind the PRINCIPLE-007 R1/R6 impact gate; returns the exit code. The one*
- `def argv_value_errors(argv)` - *Value flags given without a value, or with an invalid one (PRINCIPLE-003 R6). These used to*

---

### [`scripts/dogfood.py`](scripts/dogfood.py)
> *Operational Dogfooding Runner (PRINCIPLE-015)*

**Size**: `487` lines (`21922` bytes)

**Functions:**
- `def terminate_process_tree(proc)` - *Kill a process and all of its children (PRINCIPLE-015 Rule 2).*
- `def supervised(argv, cwd)` - *RAII supervisor: guarantees recursive teardown even if the body raises. `argv` is a list, or*
- `def sandbox_jail()` - *Ephemeral workspace outside the repository and outside host user directories*
- `def run_cli(script, args, cwd)` - *Invoke a CLI as a real binary with stdin closed (PRINCIPLE-015 Rule 3 EOF safety).*
- `def repo_fingerprint()` - *Content fingerprint of the repository working tree, or None when git is unavailable.*
- `def track_golden_lifecycle(jail, log)` - *Track 1 (PRINCIPLE-015 Rule 5): a complete create -> modify -> retrieve lifecycle driven*
- `def track_chaos_perturbation(jail, log)` - *Track 2 (PRINCIPLE-015 Rule 5): hostile perturbations. Each must fail cleanly with no*
- `def track_readonly_gates(jail, log)` - *Track 3: the two freshness gates the delivery triad depends on must run read-only from an*
- `def track_help_startup_budget(jail, log)` - *Track 4: every entrypoint must answer --help safely and inside the PRINCIPLE-010 R5*
- `def _run_track(name, fn, jail)` - *Run one track with its own log; a crashing track is a failing track, never a crashing run.*
- `def run_dogfood(verbose, keep_sandbox)` - *Execute every dogfood track and emit a terse dashboard (PRINCIPLE-015 Rule 7).*

---

### [`scripts/project_gates.py`](scripts/project_gates.py)
> *Project gates: the checks a project's own configuration declares, run as its Phase 4 (ADR-122).*

**Size**: `192` lines (`8038` bytes)

**Classes:**
- `class Gate` - *A named check and the shell command that runs it; `source` says where it came from.*
- `class GateResult` - *One gate's outcome; `returncode` is -1 when the gate could not start or timed out.*
  - Property `.passed`

**Functions:**
- `def _python_gates(root)`
- `def _node_gates(root)`
- `def _go_gates(root)`
- `def guidelines_gate(project_root)` - *The built-in guidelines and quality scan of the project's repository.*
- `def hygiene_gate(project_root)` - *The built-in hygiene scan of the project's source and static assets (ADR-137).*
- `def secrets_gate(project_root)` - *The built-in secret scan of the project's repository.*
- `def resolve_gates(project)` - *The project's gates in run order: test, detected extras, `gates` overrides, hygiene,*
- `def run_shell(command, cwd, timeout)` - *Run `command` through the platform shell with stdin closed; on timeout the whole process*
- `def run_gates(project_root, gates, runner, timeout)` - *Run every gate, even after a failure, so one report lists all of them.*
- `def failure_tail(output, lines)` - *The last `lines` non-empty lines of a gate's output, where its error normally is.*

---

### [`scripts/project_publish.py`](scripts/project_publish.py)
> *Publish a project to its own GitHub repository (ADR-134).*

**Size**: `245` lines (`11371` bytes)

**Functions:**
- `def run_command(argv, cwd)` - *Default runner: the command's exit code and combined output; -1 when it cannot start.*
- `def _triad(what, why, fix)`
- `def _clean_markdown_line(raw)` - *Strip markdown formatting, badges, and html tags from a single line.*
- `def extract_readme_description(project_root)` - *Extract a single-line summary from the project's README.md for the GitHub description.*
- `def get_project_repo_url(project_root, runner)` - *Return the URL of the project's 'origin' remote, or None if not configured.*
- `def push_range(project_root, run)` - *The commits a push uploads: those past the upstream, or the whole history without one.*
- `def scan_refusal(project_root, rev_range, run)` - *Scan every line the commits in `rev_range` add, the exact content a push uploads; returns the*
- `def auto_push_project(project_root, name, runner)` - *Push unpushed commits of a published project to its remote origin (PRINCIPLE-018: adaptive push).*
- `def publish_project(project_root, name, public, runner)` - *Upload the project's commits to its own GitHub repository; returns (exit code, report).*

---

### [`scripts/project_registry.py`](scripts/project_registry.py)
> *Project registry: the projects AIKit builds (cockpit model, ADR-119).*

**Size**: `537` lines (`23529` bytes)

**Classes:**
- `class ProjectError` - *A request AIKit cannot carry out, with its reason and remedy (PRINCIPLE-011 R6).*
  - Method `.__init__(message, why, fix, exit_code)`
- `class Stack` - *A toolchain detected in a project folder and the command that runs its tests.*
- `class Project` - *A registered project as `aikit list` reports it.*

**Functions:**
- `def render_project_readme(name, test_command)` - *A README whose structure passes PRINCIPLE-005's audit, with a `<FILL:` prerequisite marker: the*
- `def seed_readme(project_root, name, test_command)` - *Write the template README when the project has none; returns whether it did. `new` and `fix`*
- `def _python_test(root)`
- `def node_scripts(root)` - *The `scripts` map of the project's `package.json`; empty when absent or unreadable.*
- `def node_runner(root)` - *The package manager the project's lockfile names: pnpm, yarn, or npm by default.*
- `def _node_test(root)`
- `def _gradle_test(root)`
- `def _fixed(command)`
- `def detect_stacks(root)` - *Every stack whose marker file sits in the project's top folder (polyglot repos list several).*
- `def validate_name(name)` - *Reject names that are not one portable folder name.*
- `def projects_dir(workspace)`
- `def config_path(project_root)`
- `def load_config(project_root)` - *A project's `.aikit/project.json`; a missing, unreadable or newer file is an error.*
- `def _ensure_gitignore(project_root)` - *Append the transient-state patterns the project's `.gitignore` does not yet list.*
- `def write_memory(project_root, name, test_command)` - *Create the project's `.aikit/project.json`, `.aikit/decisions.md` and `.aikit/task_ledger.json`*
- `def _attached_path(workspace)`
- `def load_attached(workspace)` - *Attached project folders by name; an unreadable file is an error, not an empty list.*
- `def _registered_names(workspace, attached)` - *Name to folder for every project; `attached` spares a second read of `attached.json`.*
- `def _run_git(project_root, *args)`
- `def _git_start(project_root)` - *`git init`, then commit the project's memory and instructions so a new project starts clean. Returns*
- `def create_project(name, test_command, workspace, git_start)` - *Create `projects/<name>/` as a new git repository whose first commit holds the project's*
- `def attach_project(folder, name, test_command, workspace)` - *Register an existing folder as a project; returns (name, folder, memory_created). The folder's*
- `def _build_project(name, path, attached)`
- `def list_projects(workspace)` - *Every registered project, sorted by name; a vanished attached folder is reported, not dropped.*
- `def find_project(name, workspace)` - *The registered project called `name`; only that project's folder is inspected.*
- `def project_guidelines(project_root)` - *The project's rule lines (`- **G-NNN** (source): rule`), oldest first; [] when it has none.*
- `def add_guideline(project_root, rule, source)` - *Append one rule to the project's guidelines and return its new ID. Whatever the guidelines*
- `def latest_decision(project_root)` - *The last `### ADR-NNN: ...` heading in the project's decision register, if any.*

---

### [`scripts/subagent_delegate.py`](scripts/subagent_delegate.py)
> *Sub-agent delegation: run one OpenCode sub-agent on a bounded brief (ADR-126, ADR-128).*

**Size**: `181` lines (`8800` bytes)

**Functions:**
- `def load_opencode_config(path)` - *The OpenCode configuration; its `providers` declare which Gemini models are free-tier.*
- `def is_free_model(model, config)` - *Whether `model` (`provider/name`) costs nothing to call: an OpenCode `-free` or OpenRouter*
- `def subagent_roles(agents_dir)` - *The roles OpenCode can run: one per profile in `.opencode/agents/` (the single source).*
- `def _triad(what, why, fix)`
- `def opencode_command(runner_bin, role, prompt, file, model)` - *The `opencode run` argv for one headless sub-agent call.*
- `def _run_supervised(cmd, cwd, timeout)`
- `def delegate_subagent(role, prompt, file, project_name, model, timeout, output_format, runner, workspace)` - *Run `role` on `prompt` in AIKit or in project `project_name`; returns (exit code, report).*
- `def answer_text(stdout)` - *The sub-agent's own words from OpenCode's `--format json` event stream: the `text` parts in*

---

### [`scripts/sync_principles.py`](scripts/sync_principles.py)
> *Principles Auto-Sync Tool (PRINCIPLE-017)*

**Size**: `799` lines (`39805` bytes)

**Functions:**
- `def is_generated_target(text)` - *True when `text` carries this tool's generated-file header (current or legacy).*
- `def estimate_tokens(text)` - *Estimate tokens as chars // 4.*
- `def fsync_dir(dir_path)` - *Flush the directory entry so a completed os.replace survives power loss (PRINCIPLE-013 R1).*
- `def load_tier_1b_domain_rules(domain_path)` - *Load project-specific domain rules from .agents/rules/domain.md if present (PRINCIPLE-001, PRINCIPLE-017).*
- `def append_domain_rules(lines, domain_rules)` - *Helper to append Tier 1B domain rules to prompt targets.*
- `def parse_principles(agents_file, strict)` - *Parse the principle SSOT, enforce strict schema validation, reject duplicate IDs, and verify monotonic lifecycle progression.*
- `def _parse_principles_uncached(content, strict)` - *Parsing and validation proper; see parse_principles().*
- `def render_readme_table(principles)` - *One table per lifecycle phase: ID, title and capsule, exactly as `GUIDELINES.md` states them.*
- `def sync_readme_table(readme_text, principles)` - *`readme_text` with its generated table refreshed, or None when it has no markers.*
- `def validate_triad_consistency(principles, readme_file)` - *Verify the documentation triad's public leg: README.md lists every principle (PRINCIPLE-017).*
- `def render_claude_agent(role, profile)` - *The Claude Code profile for `role`: the role's own description and instructions, unchanged,*
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

**Size**: `1004` lines (`46667` bytes)

**Functions:**
- `def fsync_dir(dir_path)` - *Flush the directory entry so a completed os.replace survives power loss (PRINCIPLE-013 R1).*
- `def write_generated_file(file_path, content)` - *Atomically persist generated text file (flush + fsync + os.replace + fsync_dir) (PRINCIPLE-013 R1).*
- `def render_signature(node, drop_self)` - *Render a complete call signature from an AST function node (PRINCIPLE-003, PRINCIPLE-016).*
- `def parse_source(content, filename)` - *`ast.parse` at the minimum supported grammar (PRINCIPLE-003 R7), cached by content.*
- `def extract_python_symbols(file_path, strict)` - *Parse a python file with AST and extract docstrings, classes, and functions (PRINCIPLE-003).*
- `def _extract_symbols_uncached(file_path, content, strict)` - *AST extraction proper; see extract_python_symbols().*
- `def find_python_files(root)` - *Every Python file under `root`, skipping `IGNORE_DIRS`. Ignored directories are pruned while*
- `def generate_codebase_map(root, strict)` - *Generate the markdown content for knowledge/codebase_map.md with AST validation (PRINCIPLE-003).*
- `def validate_knowledge_links(knowledge_dir)` - *Verify that all relative file links in knowledge/INDEX.md physically exist on disk (PRINCIPLE-016).*
- `def audit_adr_register(decisions)` - *ADR IDs must be unique and consecutive (PRINCIPLE-016 R3, PRINCIPLE-000 R3). Two sessions that*
- `def check_codebase_map_freshness(knowledge_dir, root, strict)` - *Check if codebase_map.md accurately reflects current codebase AST (PRINCIPLE-016).*
- `def update_and_validate(knowledge_dir, root, strict)`
- `def _names(nodes)` - *Bare names of decorators or base classes (`abc.abstractmethod` -> `abstractmethod`).*
- `def audit_lazy_code(source, rel)` - *PRINCIPLE-007 R3 as a gate: a `TODO`/`FIXME`/`XXX`/`HACK` comment marker, a `# type: ignore`*
- `def _is_stub(fn)` - *A body (after any docstring) that is only `pass`, `...` or `raise NotImplementedError`.*
- `def audit_architecture(modules)` - *The parts of PRINCIPLE-009 and PRINCIPLE-010 every module can be checked against: no*
- `def check_architecture(root)` - *`audit_architecture` over every Python file the codebase map covers.*
- `def report_architecture(errors)` - *Print architecture findings with the remediation triad (PRINCIPLE-011 R6); True when clean.*
- `def check_lazy_code(root)` - *`audit_lazy_code` over every Python file the codebase map covers.*
- `def report_lazy_code(errors)` - *Print lazy-code findings with the remediation triad (PRINCIPLE-011 R6); True when clean.*
- `def quick_reference_errors(readme)` - *The structure PRINCIPLE-005 R1 states, not just its words: a heading, then inside its section*
- `def parse_readme_tree(readme)` - *Paths in the first ```text block after "What's Inside" (PRINCIPLE-005 R5), relative to the*
- `def audit_readme(readme, tracked, exists, script_source)` - *Every PRINCIPLE-005 rule a program can decide, as one error per violation. Pure: the caller*
- `def check_readme(root)` - *Run `audit_readme` on `root`, listing tracked files with git (bounded, PRINCIPLE-010 R3).*
- `def report_readme(errors)` - *Print README findings with the remediation triad (PRINCIPLE-011 R6); True when clean.*
- `def guideline_errors(text)` - *Problems in a project's `.aikit/guidelines.md`: over the size limit, a line under `## Rules`*
- `def memory_dir(root)` - *Where `root` keeps its map and decisions: a project's `.aikit/`, else `knowledge/`.*
- `def check_workspace(root)` - *Every read-only audit of `--check`, for AIKit or for a project it builds: the codebase map*
- `def _validate_argv(argv, known, help_text)` - *Short-circuit on --help and reject unknown flags with exit 2 (PRINCIPLE-011, PRINCIPLE-015).*

---

### [`tests/test_integration.py`](tests/test_integration.py)
> *Integration & Operational Dogfooding Tier (PRINCIPLE-014, PRINCIPLE-015).*

**Size**: `914` lines (`45950` bytes)

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
  - Method `.test_resume_and_checkpoint_refuse_a_newer_ledger()`
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
  - Method `.test_workspace_cli_check_detects_violations_and_passes_when_clean()`
- `class TestRepositoryCodebaseMap` - *PRINCIPLE-016 live invariant. Integration tier with the other whole-repository scans: mapping*
  - Method `.test_codebase_map_freshness_gate()`
- `class TestSuiteHygiene` - *PRINCIPLE-014 R3 and R5 made mechanical (ADR-099). Integration tier: it parses the*
  - Method `.setUpClass()`
  - Method `.test_every_test_method_asserts()`
  - Method `.test_no_test_module_imports_a_network_library()`
- `class TestRepositoryReachability` - *PRINCIPLE-014 R7 live invariant over the whole repository. Integration tier with the other*
  - Method `.test_this_repository_passes_the_shield()`
  - Method `.test_allowlist_entries_still_exist()`
- `class TestRepositorySecretHygiene` - *PRINCIPLE-019 live invariant. Integration tier: the scan shells out to `git ls-files`.*
  - Method `.test_this_repository_is_clean()`
- `class TestReadmeDriftShield` - *PRINCIPLE-005 live invariant. Integration tier: completeness shells out to `git ls-files`.*
  - Method `.test_this_readme_matches_the_tracked_tree()`
- `class TestTierBudgetDiscipline` - *Structural enforcement of the two-tier test budget (PRINCIPLE-010 R6, PRINCIPLE-014 R3).*
  - Method `.test_unit_tier_spawns_no_processes_and_never_sleeps()`
  - Method `.test_unit_tier_guards_itself_against_spawns()`
  - Method `.test_integration_tier_bounds_every_spawn()`
- `class TestProjectCreation` - *`aikit new` makes a separate git repository with its memory (ADR-119).*
  - Method `.test_new_project_is_its_own_clean_repository_with_its_own_ledger()`
- `class TestProjectSelfCheck` - *`aikit fix` repairs what it can, `aikit check` applies AIKit's guidelines (ADR-124, ADR-128).*
  - Method `.test_fix_then_check_and_the_guidelines_gate_reads_the_readme()`
- `class TestProjectHygieneGate` - *The hygiene gate runs inside `aikit check` and fails the project on real findings (ADR-137).*
  - Method `.test_check_passes_clean_and_fails_on_a_third_party_asset()`
- `class TestProjectSecretScan` - *`check_secrets.py --workspace` scans a project's repository, not AIKit's (ADR-121).*
  - Method `.test_scan_reads_the_projects_staged_changes_and_ledger()`
- `class TestProjectGateShell` - *Gates run through the platform shell in the project folder (ADR-122).*
  - Method `.test_shell_keeps_quotes_and_reports_exit_codes()`
- `class TestProjectPublishLifecycle` - *Publishing visibility and check --no-push with real processes and git checkouts (ADR-134, ADR-135).*
  - Method `.test_project_status_list_repo_and_check_no_push()`

**Functions:**
- `def complete_readme(project_root)` - *Fill a seed README's `<FILL:` marker the way a project's first commit must (ADR-138).*

---

### [`tests/test_kit.py`](tests/test_kit.py)
> *Automated Test Suite for Portable Agent Kit (PRINCIPLE-011, PRINCIPLE-016)*

**Size**: `4844` lines (`269486` bytes)

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
  - Method `.test_only_level_two_headings_set_the_phase()`
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
- `class TestGeneratedReadmeTable` - *PRINCIPLE-005 R4 / PRINCIPLE-017 R4: README's principle table is generated (ADR-076).*
  - Method `.test_table_groups_by_phase_and_escapes_cells()`
  - Method `.test_only_the_block_between_markers_is_rewritten()`
  - Method `.test_this_readme_table_is_generated_and_fresh()`
- `class TestPrinciple007Tooling` - *PRINCIPLE-007 R3 and R6 as checks every model meets the same way (ADR-079).*
  - Method `.test_first_plan_needs_the_whole_assessment()`
  - Method `.test_reaching_phase_3_without_an_assessment_warns()`
  - Method `.test_only_the_first_plan_checkpoint_is_checked()`
  - Method `.test_lazy_code_markers_stubs_and_unnamed_suppressions_fail()`
  - Method `.test_protocols_abstract_methods_and_named_suppressions_pass()`
- `class TestArchitectureGate` - *PRINCIPLE-009's checkable parts (ADR-082).*
  - Method `.test_junk_drawers_fat_roles_and_cycles_fail()`
  - Method `.test_untimed_subprocess_and_unmanaged_open_fail()`
  - Method `.test_method_style_open_outside_with_fails_and_os_open_passes()`
  - Method `.test_raw_environ_reads_fail_and_writes_and_getenv_pass()`
  - Method `.test_focused_names_narrow_roles_and_one_way_imports_pass()`
- `class TestKnowledgeBaseWorkspaceAudits` - *PRINCIPLE-016 and PRINCIPLE-011 R8: update_knowledge_base audits external project workspaces.*
  - Method `.setUp()`
  - Method `.test_workspace_audits_lazy_code_architecture_and_adr_register()`
  - Method `.test_clean_workspace_passes_lazy_and_architecture()`
  - Method `.test_aikit_dir_is_ignored_by_python_file_discovery()`
  - Method `.test_write_generated_file_persists_atomically()`
  - Method `.test_workspace_codebase_map_freshness()`
- `class TestSecretBaselineAndRuleSchema` - *PRINCIPLE-019 R2 and PRINCIPLE-017 R1 (ADR-092).*
  - Method `.test_gitignore_holds_every_baseline_pattern_the_rule_lists()`
  - Method `.test_a_rule_without_audience_is_rejected()`
- `class TestRuleNumberParity` - *Every number a rule states equals the constant the code enforces (ADR-113). The budget moved*
  - Method `.test_rule_numbers_match_code_constants()`
- `class TestPythonFileDiscovery` - *`find_python_files` prunes ignored directories relative to the root (ADR-115).*
  - Method `.test_a_repository_under_an_ignored_name_is_still_scanned()`
- `class TestOpenCodePermissionBoundaries` - *PRINCIPLE-008 R6 / PRINCIPLE-009 R6 (ADR-116): replay OpenCode v2's documented evaluation*
  - Method `.decide(rules, action, resource)`
  - Method `.setUpClass()`
  - Method `.test_protected_files_and_destructive_commands_are_denied_to_every_subagent()`
  - Method `.test_each_subagent_edits_only_its_own_area()`
- `class TestKnowledgeCitations` - *PRINCIPLE-016 R2 drift made mechanical (ADR-101): citations in living documents resolve.*
  - Method `.test_every_rule_citation_names_an_existing_rule()`
  - Method `.test_required_documents_equal_the_ones_principle_016_names()`
  - Method `.test_audit_ledger_labels_predictions_as_predictions()`
  - Method `.test_every_benchmark_row_names_its_source_or_says_unverified()`
  - Method `.test_every_code_name_a_knowledge_document_cites_exists()`
- `class TestChaosCoverage` - *PRINCIPLE-013 R7 (ADR-086): each named fault has at least one test in the suite.*
  - Method `.test_every_named_fault_has_a_test()`
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
- `class TestPrinciple006Unambiguity` - *PRINCIPLE-006 must say the same thing to every model: when to commit, what to do with failing work.*
  - Method `.setUpClass()`
  - Method `.test_rules_contain_no_hedge_words()`
  - Method `.test_every_rule_names_its_audience()`
  - Method `.test_every_duty_is_defined()`
  - Method `.test_no_second_home_for_rules_owned_elsewhere()`
- `class TestPrinciple007Unambiguity` - *PRINCIPLE-007 must say the same thing to every model: fixed fields, fixed labels, a scope test.*
  - Method `.setUpClass()`
  - Method `.test_rules_contain_no_hedge_words()`
  - Method `.test_every_rule_names_its_audience()`
  - Method `.test_rules_match_the_checks()`
  - Method `.test_no_ban_contradicts_principle_000_r5()`
  - Method `.test_capsule_states_the_mechanisms()`
- `class TestRewrittenPrincipleWording` - *One data-driven check for every principle rewritten to a single reading (PRINCIPLE-000 R7):*
  - Method `.setUpClass()`
  - Method `.test_rewritten_principles_have_one_reading()`
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
  - Method `.test_oversized_domain_rules_report_the_triad()`
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
  - Method `.test_findings_never_echo_the_secret()`
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
  - Method `.test_newer_ledger_is_refused_without_mutation()`
  - Method `.test_newer_backup_is_not_used_when_primary_is_missing()`
  - Method `.test_legacy_ledger_is_migrated_in_memory_only()`
  - Method `.test_invalid_ledger_versions_are_refused()`
  - Method `.test_resume_report_blocks_a_newer_ledger()`
  - Method `.test_save_refuses_a_newer_ledger_on_disk()`
  - Method `.test_save_refuses_a_newer_backup()`
  - Method `.test_save_does_not_write_after_lock_timeout()`
  - Method `.test_noop_completion_does_not_rewrite_the_ledger()`
  - Method `.test_an_io_error_is_reported_not_quarantined()`
  - Method `.test_corruption_is_still_quarantined_and_recovered()`
  - Method `.test_replace_retries_lock_contention_but_not_a_full_disk()`
  - Method `.test_failed_replace_keeps_the_old_ledger_and_removes_temp()`
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
  - Method `.test_milestone_tags_are_well_formed_and_bounded()`
  - Method `.test_unwritable_ledger_reports_the_triad_not_a_traceback()`
  - Method `.test_ledger_stores_repository_relative_paths()`
  - Method `.test_lock_retries_through_windows_delete_pending_permission_error()`
  - Method `.test_switching_from_an_in_progress_task_records_it_as_superseded()`
- `class TestKnowledgeBase` - *Verifies AST parsing and documentation completeness (PRINCIPLE-003, PRINCIPLE-016).*
  - Method `.test_core_docs_exist()`
  - Method `.test_update_and_validate_runs()`
  - Method `.test_codebase_map_freshness_stale_detection()`
  - Method `.test_ast_symbol_extraction()`
  - Method `.test_ast_distinguishes_properties_from_methods()`
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
- `class TestProjectRegistry` - *Projects live outside AIKit's state and carry their own `.aikit/` memory (ADR-119).*
  - Method `.setUp()`
  - Method `.make_folder(*files)`
  - Method `.test_detects_every_stack_and_its_test_command()`
  - Method `.test_npm_placeholder_is_not_a_test_command()`
  - Method `.test_name_must_be_one_portable_segment()`
  - Method `.test_attach_writes_memory_once_and_lists_the_project()`
  - Method `.test_override_beats_detection_and_missing_folder_is_reported()`
  - Method `.test_attach_refuses_folders_overlapping_the_kit()`
  - Method `.test_projects_folder_is_discovered_without_the_attached_file()`
  - Method `.test_corrupt_attached_file_is_an_error_not_an_empty_list()`
  - Method `.test_failed_git_init_leaves_no_half_made_project()`
  - Method `.test_cli_reports_triad_and_exit_codes()`
  - Method `.test_project_memory_holds_ledger_and_decisions()`
  - Method `.test_status_names_unknown_and_missing_projects()`
  - Method `.test_fix_cli_reports_triad_on_unknown_project()`
  - Method `.run_cli(*argv)` - *`aikit` in-process against this test's kit; returns (exit code, stdout, stderr).*
  - Method `.stale(path)`
  - Method `.test_fix_restores_memory_and_readme_and_removes_only_stale_buffers()`
  - Method `.test_project_ledger_commands_keep_the_impact_gate()`
  - Method `.test_workspace_is_explicit_never_the_working_directory()`
  - Method `.test_new_with_publish_flag_calls_publish_project()`
  - Method `.test_status_displays_repo_url()`
  - Method `.test_check_triggers_auto_push_unless_opted_out()`
  - Method `._gate_result()`
  - Method `.test_dirty_check_skips_auto_push_and_strict_fails()`
  - Method `.test_strict_requires_a_codebase_map()`
  - Method `.test_rendered_readme_uses_a_project_test_command()`
- `class TestProjectGates` - *A project's Phase 4 is the gates its own config declares, plus the secret scan (ADR-122).*
  - Method `.setUp()`
  - Method `.project(files, gates)`
  - Method `.names(project)`
  - Method `.test_gates_come_only_from_the_projects_own_config()`
  - Method `.test_built_in_scans_are_always_present_and_last()`
  - Method `.test_project_json_adds_replaces_and_disables_gates()`
  - Method `.test_invalid_gate_config_is_refused()`
  - Method `.test_every_gate_runs_after_a_failure()`
- `class TestProjectHygieneScan` - *The hygiene scan decides from the AST and from lines what the project gates could not (ADR-137).*
  - Method `.rules(source)`
  - Method `.test_subprocess_rules_are_decidable()`
  - Method `.test_only_imported_subprocess_names_count()`
  - Method `.test_startup_and_file_rules()`
  - Method `.test_any_handler_that_only_discards_is_flagged()`
  - Method `.test_absolute_paths_only_when_they_reach_file_access()`
  - Method `.test_inline_allow_marker_needs_a_reason()`
  - Method `.test_asset_urls_skip_loopback_namespaces_and_marked_lines()`
  - Method `.test_scan_tree_skips_vendored_dirs_and_reports_unreadable_files()`
- `class TestProjectsStayOutOfKitState` - *AIKit's map, gates and sweeps never read a project's files (ADR-119).*
  - Method `.test_codebase_scan_and_sweeps_prune_projects()`
  - Method `.test_git_ignores_projects()`
- `class TestSubagentDelegation` - *`aikit delegate`: bounded OpenCode sub-agent runs (ADR-126, ADR-128).*
  - Method `.setUp()`
  - Method `.runner(returncode, stdout, effect)`
  - Method `.delegate(role, prompt, **kwargs)`
  - Method `.test_roles_are_the_opencode_profiles()`
  - Method `.test_refuses_empty_brief_unknown_project_and_missing_file()`
  - Method `.test_runs_opencode_headless_with_the_brief()`
  - Method `.test_json_report()`
  - Method `.test_a_changed_ledger_is_reported_and_never_overwritten()`
  - Method `.test_timeout_is_reported()`
- `class TestProjectGuidelines` - *A project's own rules, below AIKit's principles (PRINCIPLE-001 R4, PRINCIPLE-000 R6, ADR-129).*
  - Method `.setUp()`
  - Method `.rules(*lines)`
  - Method `.test_memory_starts_with_the_template_which_passes_the_audit()`
  - Method `.test_audit_names_each_broken_rule()`
  - Method `.test_add_numbers_rules_and_refuses_an_override()`
  - Method `.test_cold_start_commands_print_the_rules_and_their_rank()`
- `class TestClaudeSubagents` - *Claude Code sub-agents generated from AIKit's role profiles (PRINCIPLE-012 R8, ADR-131).*
  - Method `.tools(role)`
  - Method `.test_every_role_exists_for_both_hosts()`
  - Method `.test_profile_is_generated_from_the_one_role_text()`
  - Method `.test_read_only_roles_cannot_write()`
  - Method `.test_role_text_is_host_neutral_and_names_both_ledgers()`
  - Method `.test_no_agent_may_edit_a_task_ledger()`
- `class TestFreeModelPolicy` - *Sub-agents run only on free models (PRINCIPLE-012 R8, ADR-132).*
  - Method `.test_policy_names_free_and_paid_models()`
  - Method `.test_every_role_and_the_default_run_on_a_free_model()`
  - Method `.test_delegate_refuses_a_paid_model_before_running_anything()`
  - Method `.test_gemini_key_comes_only_from_the_environment()`
  - Method `.test_text_report_keeps_only_the_answer()`
  - Method `.test_a_key_split_across_a_concatenation_is_still_caught()`
  - Method `.test_commit_diffs_are_scanned_line_by_line_with_their_file()`
  - Method `.test_scanner_catches_a_bare_gemini_key()`
- `class TestProjectPublish` - *`aikit publish`: a project in its own GitHub repository, private unless asked (ADR-134).*
  - Method `.runner(**replies)` - *A scripted stand-in for git, gh and the secret scan; records every call.*
  - Method `.made(word)`
  - Method `.test_new_repository_is_private_scanned_first_and_pushed()`
  - Method `.test_public_only_when_asked()`
  - Method `.test_existing_remote_is_pushed_never_recreated_or_forced()`
  - Method `.test_an_existing_upstream_scans_only_the_commits_it_pushes()`
  - Method `.test_auto_push_scans_the_commits_it_pushes_and_refuses_a_finding()`
  - Method `.test_refusals_upload_nothing()`
  - Method `.test_uncommitted_work_is_named_in_the_report()`
  - Method `.test_extract_readme_description_finds_first_paragraph_and_truncates()`
  - Method `.test_get_project_repo_url()`
  - Method `.test_publish_passes_extracted_description()`
  - Method `.test_auto_push_project()`
- `class TestTestTierBudgetGate` - *PRINCIPLE-010 R6: both tier budgets are measured by a gate instead of assumed.*
  - Method `.fake_runner(table)`
  - Method `.ok(tests, seconds)`
  - Method `.gate(table)`
  - Method `.test_parse_reads_the_count_and_duration_unittest_prints()`
  - Method `.test_a_tier_over_its_per_test_average_fails_and_names_the_tier()`
  - Method `.test_both_tiers_inside_budget_pass_and_report_the_average()`
  - Method `.test_a_failing_tier_fails_the_gate_whatever_its_speed()`
  - Method `.test_unparseable_tier_output_fails_instead_of_reporting_zero()`
  - Method `.test_every_test_module_in_the_repository_has_a_budget()`
  - Method `.test_budget_errors_is_silent_when_every_tier_fits()`
- `class TestChecklistWording` - *PRINCIPLE-000 R7 bans hedge words in "every rule added or changed", but the slices the*
  - Method `.setUpClass()`
  - Method `.test_checklists_contain_no_hedge_words()`
  - Method `.test_every_checklist_item_cites_a_principle()`

**Functions:**
- `def _refuse_spawn(popen_self, args, *unused_args, **unused_kwargs)`
- `def setUpModule()`
- `def tearDownModule()`
- `def not_a_git_repo(workspace)` - *In-process stand-in for `git status` in a non-repository: exactly what real git returns*

---
