---
name: aikit
description: >-
  Operational runbook and command matrix for AIKit (Universal AI Principles & Disruption Recovery).
  Use this skill whenever running test suites, verifying rule freshness, synchronizing principles,
  updating the AST codebase map and knowledge base, classifying change tracks, auditing or resuming disruption recovery,
  checkpointing tasks, scanning for secrets, verifying reachability, or executing dogfooding and pre-commit gates.
---

# AIKit Operational Runbook (Universal Host Integration)

This operational runbook provides the unified command matrix for driving AIKit across all supported agent host clients (Antigravity, Claude, OpenCode, Cursor, Copilot) under **PRINCIPLE-009 R7** (Pluggable Host Architecture) and **PRINCIPLE-017 R2** (Cross-IDE Synchronization).

---

## 🌐 Host Client Operation Matrix

- **Antigravity**: Native chat harness. Discovers this skill via `.agents/skills/aikit/SKILL.md` and rule files in `.agents/rules/`.
- **Claude (Code CLI / Desktop)**: Reads `CLAUDE.md` automatically on startup. Executes kit commands directly via terminal tool calls.
- **OpenCode**: Runs headless subagent profiles (`architect`, `coder`, `tester`, etc.) via `opencode run --standalone`.
- **State SSOT**: All clients interact with workspace state strictly through `python scripts/disruption_recovery.py` and `.agents/task_ledger.json` (a project's: `.aikit/task_ledger.json`).

---

## 🧱 Projects: Building Software Other Than AIKit (PRINCIPLE-011 R8)
The user's software lives in its own project, never in AIKit's tree:
```bash
python aikit.py list                 # which projects exist
python aikit.py new <name>           # projects/<name>/, its own git repository
python aikit.py attach <path>        # an existing folder
python aikit.py status <name>        # its task, changes, latest decision and its gates
python aikit.py check <name>         # its Phase 4: every gate, secret scan last; exit 0 to commit
```
- Request names no single project: ask which one, or the name of a new one, before writing code.
- In the steps below, project work replaces the repository with the project: add `--workspace <project path>` to every `disruption_recovery.py` command, write ADRs in `<project>/.aikit/decisions.md`, stage and commit inside the project, and run `python aikit.py check <name>` as Phase 4. AIKit's other gates are for changes to AIKit only.

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
- **Track B** (docs/comments): Phases 1, 3, 4 and 5; Phase 4 is the same full gate set as Track C (PRINCIPLE-002 R3).
- **Track C** (code/tests/contracts): Full pre-flight impact checklist, test gates, and pre-commit delivery triad.

### 2. Record Task Plan & Milestone Checkpoints
Record atomic milestones in `.agents/task_ledger.json`:
```bash
python scripts/disruption_recovery.py --checkpoint <task_id> --phase-num 2 --desc "[1/M] <plan_desc>" --why "<rationale>" --benefits "<benefits>" --risks "contract: none dependency: none concurrency: none state: none" --mitigation "none"
```
*(Subagents MUST NOT write to the ledger; only the root orchestrator records checkpoints).*

---

## 🤖 Token-Frugal Subagent Offloading (OpenCode v2 Integration)

To prevent context exhaustion and preserve primary model quota (**PRINCIPLE-012 R8**), delegate token-heavy exploratory and repetitive tasks to worker subagents running free or local models:

### 1. Headless Multi-Subagent Invocations (OpenCode v2)
Invoke specialized subagents in non-interactive headless mode with `--standalone` (PRINCIPLE-011 R5, PRINCIPLE-015):
```bash
# Deep reasoning on system design & ADRs (architect):
opencode run --standalone --format json --agent architect "<prompt>"

# High-fidelity code generation & refactoring (coder):
opencode run --standalone --format json --agent coder --file <path> "<prompt>"

# Test engineering & regression suite generation (tester):
opencode run --standalone --format json --agent tester --file <test_file> "<prompt>"

# Documentation, link integrity & secret review (reviewer):
opencode run --standalone --format json --agent reviewer "<prompt>"

# High-speed symbol lookup & file tree mapping (explorer):
opencode run --standalone --format json --agent explorer "<search_query>"

# General background worker (worker):
opencode run --standalone --format json --agent worker --file <path> "<prompt>"
```

### 2. Model & Provider Options (opencode.jsonc)
- **OpenCode Free Tier**: `opencode/deepseek-v4.1-flash-free` (default), `opencode/glm-5.3-flash-free`, `opencode/mimo-v2.6-flash-free`, `opencode/beam-free` (built-in zero-cost coding models).
- **OpenRouter Free Tier**: `openrouter/qwen/qwen-2.5-coder-32b-instruct:free`, `openrouter/meta-llama/llama-3.3-70b-instruct:free`, etc. (requires free `OPENROUTER_API_KEY`).
- **Local Offline (Zero Network)**:
  - **Ollama**: `ollama/qwen2.5-coder:latest`, `ollama/deepseek-r1:latest`.
  - **LM Studio**: `lmstudio/<model_name>` at `http://127.0.0.1:1234/v1`.


### 3. Subagent Boundaries & Safety
- **Ledger Invariant (PRINCIPLE-008 R6)**: Subagents MUST NOT write to `.agents/task_ledger.json`. Denied to every OpenCode sub-agent by `.opencode/agents/*.md`, together with `GUIDELINES.md`, the generated Tier 1 files and destructive git commands; `TestOpenCodePermissionBoundaries` replays OpenCode's last-match evaluation over them (ADR-116).
- **Regression Shield Gate (PRINCIPLE-014)**: All code proposed by subagents must pass unit tests and read-only gates before staging.


---

## 🛡️ Phase 4: Operational Verification & Regression Shields

Execute every gate below before every commit, Track B or Track C (PRINCIPLE-018 R3):

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
