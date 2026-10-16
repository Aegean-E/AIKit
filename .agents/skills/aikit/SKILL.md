---
name: aikit
description: >-
  Operational runbook and command matrix for AIKit (Universal AI Principles & Disruption Recovery).
  Use this skill whenever running test suites, verifying rule freshness, synchronizing principles,
  updating the AST codebase map and knowledge base, classifying change tracks, auditing or resuming disruption recovery,
  checkpointing tasks, scanning for secrets, verifying reachability, or executing dogfooding and pre-commit gates.
---

# AIKit Operational Runbook (Antigravity Integration)

This skill integrates AIKit's command matrix with Antigravity agent workflows across the 5 lifecycle phases.

---

## 🧭 Phase 1: Orientation & Cold-Start Recovery

### 1. Resume Interrupted Tasks
Run on session startup, cold starts, or after a context compaction:
```bash
python scripts/disruption_recovery.py --resume
```
- If an interrupted task is found, resume from its recommended phase.
- If uncommitted files or orphaned buffers exist, inspect them before proceeding.

### 2. Disruption Recovery Audit
Check ledger state without altering it:
```bash
python scripts/disruption_recovery.py --audit
```

---

## 📋 Phase 2: Classification, Planning & Checkpointing

### 1. Classify Lifecycle Track
Determine required gates before editing:
```bash
python scripts/disruption_recovery.py --track
```
- **Track A** (none): No gates required.
- **Track B** (docs/comments): Post-flight checklist and secret scan.
- **Track C** (code/tests/contracts): Full pre-flight impact checklist, test gates, and pre-commit delivery triad.

### 2. Record Task Plan & Milestone Checkpoints
Record atomic milestones in `.agents/task_ledger.json`:
```bash
python scripts/disruption_recovery.py --checkpoint <task_id> --phase-num 2 --desc "[1/M] <plan_desc>" --why "<rationale>" --benefits "<benefits>" --risks "contract: none dependency: none concurrency: none state: none" --mitigation "none"
```
*(Subagents MUST NOT write to the ledger; only the root orchestrator records checkpoints).*

---

## 🤖 Token-Frugal Subagent Offloading (OpenCode Integration)

To prevent context exhaustion and preserve primary model quota (**PRINCIPLE-012**), delegate token-heavy exploratory and repetitive tasks to worker subagents running free or local models:

### 1. Headless CLI Delegation (PRINCIPLE-011 R2/R5)
Always invoke OpenCode in non-interactive headless mode (`opencode run`):
```bash
# Analyze target file(s) and return structured JSON:
opencode run --format json --file <path> "<prompt>"

# Scan codebase with auto-approved permissions:
opencode run --format json --auto "<prompt>"

# Target a free or local model:
opencode run --model <provider/model> --format json "<prompt>"
```

### 2. Free Model Configuration Options
- **Local (Ollama)**: `ollama/qwen2.5-coder:7b`, `ollama/deepseek-coder-v2` (100% free, offline, zero token usage).
- **Free Cloud Tiers**: Google AI Studio (`gemini-2.0-flash`), OpenRouter (`:free` endpoints), or Groq.

### 3. Subagent Boundaries & Safety
- **Ledger Protection (PRINCIPLE-008 R6)**: Subagents MUST NOT write to `.agents/task_ledger.json`.
- **Regression Shield Gate (PRINCIPLE-014)**: All code proposed by subagents must pass unit tests and read-only gates before staging.

---

## 🛡️ Phase 4: Operational Verification & Regression Shields

Execute these verification gates before staging or committing any Track C changes:

### 1. Unit & Integration Test Suites
```bash
# Fast unit tier (<1s gate):
python -m unittest tests.test_kit

# Full regression shield (100% pass required):
python -m unittest discover tests
```

### 2. Living Rules & Knowledge Freshness Gates
```bash
# Check rule parity and context budget (<1,600 tokens):
python scripts/sync_principles.py --check

# Check AST codebase map, README parity, and architecture gates:
python scripts/update_knowledge_base.py --check
```

### 3. Safety, Reachability & Chaos Gates
```bash
# Scan staged changes and agent memory for credentials:
python scripts/check_secrets.py --staged

# Verify no orphaned capability or phantom state keys:
python scripts/check_reachability.py

# Universal operational dogfood gate (golden path + chaos perturbation):
python scripts/dogfood.py
```

---

## 🚀 Phase 5: Living Synchronization & Delivery

### 1. Synchronize Generated Targets
When `GUIDELINES.md` or `.agents/rules/domain.md` is updated:
```bash
python scripts/sync_principles.py
```

When code structure, exported functions, or classes change:
```bash
python scripts/update_knowledge_base.py
```

### 2. Mark Task Completed
```bash
python scripts/disruption_recovery.py --complete <task_id>
```

### 3. Commit with Conventional Format
Validate message syntax prior to committing:
```bash
python scripts/disruption_recovery.py --validate-commit "feat(scope): [milestone N/M] description"
```
Stage files explicitly by name (`git add <file>`), never blind (`git add .`).

### 4. Cleanup Stale Buffers
Purge temporary write buffers older than 60s:
```bash
python scripts/disruption_recovery.py --clean
```
