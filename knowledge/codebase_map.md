# Codebase Map & Symbol Catalog 🗺️

> **AUTO-GENERATED & VERIFIED BY `scripts/update_knowledge_base.py`**
> This document provides an automated, up-to-date registry of all modules, classes, and exported functions across this repository.

---

## 📊 Codebase Metrics
- **Total Python Modules**: `4`
- **Total Classes**: `4`
- **Total Functions / Methods**: `20`
- **Total Source Lines**: `1000`

---

## 📦 Modules & Exported Symbols

### [`scripts/disruption_recovery.py`](scripts/disruption_recovery.py)
> *Disruption Recovery & Task Progress Ledger (PRINCIPLE-006, PRINCIPLE-013)*

**Size**: `292` lines (`10409` bytes)

**Functions:**
- `def get_ledger_path(custom_dir)` - *Return path to task ledger, creating parent directories if needed.*
- `def atomic_write_json(file_path, data)` - *Atomically write JSON data using fsync and temporary replacement (PRINCIPLE-013).*
- `def load_ledger(ledger_file)` - *Safely load the task ledger with startup self-healing (PRINCIPLE-013).*
- `def save_ledger(ledger, ledger_file)` - *Save the task ledger atomically to disk.*
- `def resolve_phase_num(phase, explicit_num)` - *Resolve lifecycle phase number 1..5 for compaction orientation (PRINCIPLE-002).*
- `def record_checkpoint(task_id, phase, description, files_affected, status, ledger_file, phase_num)` - *Record an atomic micro-checkpoint in the task ledger (PRINCIPLE-002, PRINCIPLE-006).*
- `def mark_task_completed(task_id, ledger_file)` - *Mark the active task as successfully completed in the ledger.*
- `def run_disruption_audit(workspace_dir)` - *Execute a comprehensive pre-flight disruption audit (PRINCIPLE-006, PRINCIPLE-007).*
- `def format_audit_report(audit)` - *Generate human and AI-readable disruption recovery audit report.*

---

### [`scripts/sync_principles.py`](scripts/sync_principles.py)
> *Principles Auto-Sync Tool (PRINCIPLE-017)*

**Size**: `243` lines (`9714` bytes)

**Functions:**
- `def parse_principles(agents_file)`
- `def generate_gemini_content(principles)`
- `def generate_agents_rule_content(principles)`
- `def generate_claude_content(principles)`
- `def generate_cursorrules_content(principles)`
- `def generate_copilot_content(principles)`
- `def sync_all(check_only)`

---

### [`scripts/update_knowledge_base.py`](scripts/update_knowledge_base.py)
> *Codebase Knowledge Base Auto-Updater & Validator (PRINCIPLE-016)*

**Size**: `229` lines (`7784` bytes)

**Functions:**
- `def extract_python_symbols(file_path, strict)` - *Parse a python file with AST and extract docstrings, classes, and functions (PRINCIPLE-003).*
- `def find_python_files(root)` - *Dynamically discover all source python files across the repository.*
- `def generate_codebase_map(root, strict)` - *Generate the markdown content for knowledge/codebase_map.md with AST validation (PRINCIPLE-003).*
- `def update_and_validate(strict)`

---

### [`tests/test_kit.py`](tests/test_kit.py)
> *Automated Test Suite for Portable Agent Kit (PRINCIPLE-011, PRINCIPLE-016)*

**Size**: `236` lines (`10493` bytes)

**Classes:**
- `class TestPrincipleSync` - *Verifies that all 18 principles are maintained and synchronized (PRINCIPLE-001, PRINCIPLE-017).*
  - Method `.test_parse_18_principles()`
  - Method `.test_monotonic_lifecycle_phase_alignment()`
  - Method `.test_targets_in_sync_and_budgeted()`
  - Method `.test_principle_003_anti_hallucination_capsule()`
  - Method `.test_principle_004_compaction_resilience_capsule()`
- `class TestDisruptionRecovery` - *Verifies atomic write, disruption ledger, and crash recovery (PRINCIPLE-006, PRINCIPLE-013).*
  - Method `.setUp()`
  - Method `.tearDown()`
  - Method `.test_atomic_write_and_load()`
  - Method `.test_self_healing_quarantine_corrupted_json()`
  - Method `.test_record_checkpoint_and_complete()`
- `class TestKnowledgeBase` - *Verifies AST parsing and documentation completeness (PRINCIPLE-003, PRINCIPLE-016).*
  - Method `.test_core_docs_exist()`
  - Method `.test_update_and_validate_runs()`
  - Method `.test_ast_symbol_extraction()`
  - Method `.test_ast_strict_mode_fails_on_syntax_error()`
- `class TestOperationalDogfooding` - *Dogfooding & Zero-Blast-Radius Chaos Test (PRINCIPLE-015).*
  - Method `.setUp()`
  - Method `.tearDown()`
  - Method `.test_ephemeral_sandbox_isolation()`

---
