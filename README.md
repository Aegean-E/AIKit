# 🤖 Universal AI Principles & Agent Operating System (Portable Kit)

> **Plug-and-Play AI Assistant Governance, Architecture Principles & Disruption Recovery for Any Software Project.**

This kit contains the complete, battle-tested AI governance system extracted from production development. It ensures that any AI coding assistant (Antigravity IDE, Cursor, Claude Code, GitHub Copilot, Gemini CLI, etc.) follows strict engineering principles, prevents progress loss from unexpected power cuts or crashes, maintains living documentation, and executes automated regression-shielded git workflows.

---

## ⚡ 30-Second Cold-Start Quick Reference

> **Orientation Contract for AI Agents & Developers**: Orient yourself in seconds with the verified commands and prerequisites below.

- **Runtime Prerequisites**: Python 3.10+ (Standard Library only — zero external pip dependencies) and `git`.
- **Canonical Regression Shield Gate**:
  ```bash
  python -m unittest discover tests
  ```
  *(100% test pass required before staging or committing changes).*

### 🛠️ Core Operational Command Matrix
| Operational Role | Canonical Command | Verification Gate |
|---|---|---|
| **Run Regression Suite** | `python -m unittest discover tests` | 100% tests pass (both tiers, ~5s) |
| **Run Unit Tier Only** | `python -m unittest tests.test_kit` | 100% pass, strict <1s gate |
| **Run Integration Tier Only** | `python -m unittest tests.test_integration` | 100% pass, <5s, bounded spawns |
| **Synchronize IDE Rules** | `python scripts/sync_principles.py` | <=1,600 est. tokens/target incl. a reserved 300-token Tier 1B |
| **Verify Rule Freshness** | `python scripts/sync_principles.py --check` | Read-only; exits 1 on rule drift, or when a principle changed since the last commit lacks an ADR naming its `--citing` set (PRINCIPLE-000 R3) |
| **Find Principles to Read** | `python scripts/sync_principles.py --involved <paths/commands/output>` | Same answer for every agent (PRINCIPLE-001 R3) |
| **Cross-Principle Check Set** | `python scripts/sync_principles.py --citing <PRINCIPLE-NNN>` | Principles a rule change must be checked against (PRINCIPLE-000 R3) |
| **Update AST & Knowledge** | `python scripts/update_knowledge_base.py` | Rewrites the codebase map; exits 1 on a syntax error (Python 3.10 grammar), README drift, an ADR ID out of order, or unfinished code (PRINCIPLE-007 R3) |
| **Verify AST Map Freshness** | `python scripts/update_knowledge_base.py --check` | Read-only; exits 1 on a stale codebase map, README drift (PRINCIPLE-005), an ADR ID out of order, or unfinished code (PRINCIPLE-007 R3) |
| **Classify Lifecycle Track** | `python scripts/disruption_recovery.py --track` | Prints Track A/B/C of current changes (PRINCIPLE-002 R3) |
| **Audit Disruption Recovery**| `python scripts/disruption_recovery.py --audit` | Clean status check; detects surviving uncommitted files |
| **Resume Interrupted Task** | `python scripts/disruption_recovery.py --resume` | Cold-start command: every `--audit` finding, then the interrupted task, its plan and resumption phase |
| **Record Task Checkpoint**   | `python scripts/disruption_recovery.py --checkpoint <task_id> --phase-num <1-5> --desc <text>` | Appends a checkpoint (PRINCIPLE-002 R4); exits 2 when a task's first plan lacks `--why --benefits --risks --mitigation` (PRINCIPLE-007 R6) |
| **Complete Task Ledger**     | `python scripts/disruption_recovery.py --complete <task_id>` | Marks the active task completed in `.agents/task_ledger.json`; exits 1, changing nothing, if `<task_id>` is not the active task |
| **Reset Active Task**        | `python scripts/disruption_recovery.py --reset [reason]` | Abandons/clears in-progress task in ledger |
| **Purge Temp Buffers**       | `python scripts/disruption_recovery.py --clean` | Deletes orphaned `*.tmp_*` buffers older than 60 s; younger ones may be a write in progress |
| **Secret Scan Gate** | `python scripts/check_secrets.py --staged` | Exits 1 on a credential pattern in the staged diff or agent memory, or when any surface could not be scanned (PRINCIPLE-019) |
| **Reachability Shield** | `python scripts/check_reachability.py` | No unwired capability or phantom state key (PRINCIPLE-014 R7) |
| **Operational Dogfood Gate** | `python scripts/dogfood.py` | 5/5 tracks pass; zero host mutation (PRINCIPLE-015) |
| **Discover Any CLI** | `python scripts/<script>.py --help` | Prints usage and exits `0` in <100ms, writing nothing |
| **Sandbox the Ledger CLI** | `python scripts/disruption_recovery.py --workspace <dir> --audit` | Operates on `<dir>/.agents/`, never the repo ledger |

**Universal CLI contract (PRINCIPLE-011, PRINCIPLE-015).** Every script in `scripts/` honours the same
contract: `--help` / `-h` prints a usage block to stdout and exits `0` without touching the filesystem;
an unrecognized flag is refused with the What → Why → Fix remediation triad on stderr and exit code `2`
(never the default action); `0` = success, `1` = operational failure, `2` = CLI misuse. Read-only
verification runs through `--check` on `sync_principles.py` and `update_knowledge_base.py`.

---

## 📦 What's Inside

```text
portable_agent_kit/
├── README.md                           <- This Integration & Setup Guide
├── .gitignore                          <- Credential & local-state baseline (PRINCIPLE-019 R3)
├── AGENTS.md                           <- Generated Tier 1 capsules (auto-loaded by AGENTS.md-convention agents)
├── GUIDELINES.md                       <- Single source of truth: every principle, rule & checklist (Tier 2)
├── GEMINI.md                           <- Google Gemini & Antigravity IDE rules
├── CLAUDE.md                           <- Anthropic Claude Code configuration
├── .cursorrules                        <- Cursor IDE instructions
├── .github/
│   ├── copilot-instructions.md         <- GitHub Copilot instructions
│   └── workflows/
│       └── ci.yml                      <- Continuous verification gate (both tiers + freshness)
├── .agents/
│   ├── rules/
│   │   ├── principles.md               <- Antigravity / Agent IDE workspace rules
│   │   ├── domain.md.template          <- Template for project domain rules (Tier 1B)
│   │   └── readme_quickref.md.template <- Adopter README Quick Reference & tree (PRINCIPLE-005 R6)
│   └── task_ledger.json                <- Disruption ledger for power-loss resilience (WAL)
├── scripts/
│   ├── sync_principles.py              <- Generates all 6 Tier 1 files from GUIDELINES.md, budget-gated
│   ├── disruption_recovery.py          <- Power-loss audit, atomic checkpointing & ledger CLI
│   ├── update_knowledge_base.py        <- Automatic codebase AST symbol extractor & validator
│   ├── dogfood.py                      <- Operational dogfood runner (sandbox jail + chaos tracks)
│   ├── check_reachability.py           <- Invariant reachability shield (anti-dead-capability)
│   └── check_secrets.py                <- Secret & sensitive data scanner (pre-commit gate)
├── tests/
│   ├── test_kit.py                     <- Unit tier: in-process regression shield (strict <1s gate)
│   └── test_integration.py             <- Integration tier: concurrency, CLI contracts & dogfooding
└── knowledge/
    ├── INDEX.md                        <- Knowledge base table of contents & architecture map
    ├── architecture.md                 <- High-level system architecture and component boundaries
    ├── services.md                     <- Core services, API contracts, and business logic
    ├── data_models.md                  <- Data structures, schemas, and persistence models
    ├── state_and_ui.md                 <- Presentation layer, UI state, and event loops
    ├── decisions.md                    <- Architectural Decision Records (ADRs)
    └── codebase_map.md                 <- Auto-generated AST catalog of classes and functions
```

---

## 🚀 How to Apply to Another Project (2-Minute Setup)

### Step 1: Copy Governance Assets

- **Option A (New Greenfield Project)**:
  Copy all files directly into the target project:
  ```bash
  cp -r portable_agent_kit/* /path/to/target/
  cp -r portable_agent_kit/.* /path/to/target/ 2>/dev/null || true
  ```

- **Option B (Existing Project / Non-Destructive Merge)**:
  Copy only the source of truth and tooling; the Tier 1 files are generated in Step 3, never copied:
  ```bash
  cd portable_agent_kit
  mkdir -p /path/to/target/.agents
  cp -r GUIDELINES.md scripts knowledge /path/to/target/
  cp -r .agents/rules /path/to/target/.agents/
  ```
  Do **not** copy `tests/`, `.github/` or `.agents/task_ledger.json`: they test, build and record *this* repository (verified: AIKit's suite fails 19 checks inside a fresh adopter repo). Your project keeps its own suite; AIKit's enforcement travels as the CLI gates, which all pass in an adopter repo: `sync_principles.py --check`, `update_knowledge_base.py --check`, `check_reachability.py`, `check_secrets.py --all` and `dogfood.py`. Replace the copied `knowledge/` documents with your own project's after Step 4.
  Then copy `.agents/rules/readme_quickref.md.template` into the top of your existing `README.md` and replace every placeholder that begins with `<FILL` with your project's values; it holds only what travels (the two labels, AIKit's gate commands and a tree skeleton), never AIKit's own test modules. `update_knowledge_base.py --check` fails while any such placeholder remains or the tree misses a tracked top-level entry (PRINCIPLE-005 R1, R5, R6).

### Step 2: Move Your Own Agent Instructions into Tier 1B
If the target already has its own `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursorrules` or `.github/copilot-instructions.md`, move their project-specific rules into `.agents/rules/domain.md` (start from `.agents/rules/domain.md.template`, at most 1,200 chars), then delete the originals. Sync injects that block into every generated file. It never overwrites a file it did not generate: it stops with `[PROTECTED]` and names the file, so nothing is lost.

### Step 3: Run Principle Synchronization
Generate every Tier 1 file from `GUIDELINES.md`:

```bash
python scripts/sync_principles.py
```
This writes `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursorrules`, `.agents/rules/principles.md` and `.github/copilot-instructions.md`, each within 1,600 est. tokens including your Tier 1B block.

### Step 4: Generate Your Knowledge Base
Run the knowledge base AST scanner to automatically index your project's classes and functions:

```bash
python scripts/update_knowledge_base.py
```
This generates `knowledge/codebase_map.md` with every exported class, method, argument, and docstring across your project!

---

## 🏛️ The 20 Core Principles (Lifecycle-Ordered)

The principles are strictly organized across **5 chronological execution phases**:

<!-- principles:begin (generated from GUIDELINES.md by scripts/sync_principles.py; do not edit) -->
### 🏛️ Phase 1: Meta-Governance & Attentional Grounding
| Principle | Title | Capsule |
|---|---|---|
| **PRINCIPLE-000** | Meta-Principle Integrity & Mutual Alignment | Every rule binds; conflicts follow R6 order; rule edits re-check every citing principle; gaming a gate is a violation; quality doubts go to the user. |
| **PRINCIPLE-001** | Progressive Rule Disclosure & Governance Frugality | Pre-Flight checklist before the first Track C edit; Post-Flight checklist before any Track B or C commit; report only failed items (R8). |
| **PRINCIPLE-002** | Lifecycle-Aligned Instruction Ordering & Attentional Priming | Track via `disruption_recovery.py --track` (A none, B docs/comments but not rule files, C rest); urgency alone never skips P018 gates (R5). |
| **PRINCIPLE-003** | Empirical Grounding & Anti-Hallucination Invariant | Read-before-write slice freshness; `git grep -w -e` call-site check; deps only if declared; platform parity; ask on intent ambiguity; strict AST syntax gate. |
| **PRINCIPLE-004** | Attentional Drift Prevention & Compaction Resilience | Plan = latest `[1/` Phase 2 `--desc` in `task_ledger.json`; cold start `--resume`; never re-ask recorded answers; ADR before commit; reads/output <=100 lines. |

### 🧭 Phase 2: Pre-Flight Orientation & Planning
| Principle | Title | Capsule |
|---|---|---|
| **PRINCIPLE-005** | AI Cold-Start Readiness & Living Documentation | README <=20k chars: prerequisites, test command, tree; user-visible changes update it same commit; `update_knowledge_base.py --check` gates it. |
| **PRINCIPLE-006** | Incremental Progress Checkpointing & Disruption Recovery | Commit each `[milestone N/M]` once Phase 4 passes; failing work stays uncommitted, described by `--checkpoint`; `--complete` or `--reset` before switching tasks; `--clean` stale `.tmp_*`. |
| **PRINCIPLE-007** | Pre-flight Impact & Quality Checklist | Track C first plan checkpoint carries --why --benefits --risks (contract, dependency, concurrency, state) --mitigation; no TODO or stub; no change outside the plan. |
| **PRINCIPLE-008** | Hierarchical Problem & Task Decomposition | Goal -> Domain -> Leaf decomposition; plan top-down, build bottom-up; 2<=M<=6 milestones as `[milestone N/M]` commits; each leaf independently verifiable. |

### 🏗️ Phase 3: Architecture & Lean Implementation
| Principle | Title | Capsule |
|---|---|---|
| **PRINCIPLE-009** | Modularity & Pluggable Architecture | 4 layers (Presentation -> Service -> Domain <- Adapter); role protocols & registry; zero-config constructor DI; immutable DTOs. |
| **PRINCIPLE-010** | Performance & Resource Optimization | O(1)-memory streaming; non-blocking event loops; subprocess timeouts; write-coalescing batch I/O; lazy imports (<100ms `--help`); <1s unit test tier. |
| **PRINCIPLE-011** | Zero-Friction Onboarding & Instant Usability | Pure-stdlib clone-and-run; self-bootstrapping workspace; mode transparency; non-interactive headless parity; deterministic exit codes (0/1/2); remediation triad. |
| **PRINCIPLE-012** | Token Frugality & Lean Code Architecture | Prompt cache prefix alignment (>=80% hits); bounded tool output & diffs; terse schema output; token circuit breakers; lean syntactic density. |

### 🛡️ Phase 4: Operational Verification & Resilience
| Principle | Title | Capsule |
|---|---|---|
| **PRINCIPLE-013** | Crash Resilience, State Atomicity & Power-Loss Recovery | Atomic writes: flush + os.fsync + retried os.replace + parent-dir fsync; advisory locking on read-modify-write; .bak shadow backups; schema migration; signal-drain flush; read-only fallback. |
| **PRINCIPLE-014** | Automated Test Verification & Continuous Test Coverage | 100% test pass gate (<1s unit tier, <5s integration tier); test sanctity invariant (never weaken); RAII fixture reversion; anti-tautological observable contracts; hostile & negative path coverage; reachability shield (`scripts/check_reachability.py`). |
| **PRINCIPLE-015** | Universal Operational Dogfooding & Chaos Verification | Domain-specific interactive dogfooding (GUI/CLI/web/API) via `scripts/dogfood.py`; portable RAII process tree teardown; ephemeral safety jail (zero host mutation); non-interactive stdin parity; golden path + chaos perturbation; terse reporting (<15 lines). |

### 🚀 Phase 5: Living Synchronization & Delivery
| Principle | Title | Capsule |
|---|---|---|
| **PRINCIPLE-016** | AI Knowledge Base & Continuous Synchronization | Canonical `knowledge/` sync; atomic code-and-doc pairing; monotonic append-only ADR register; strict AST syntax validation; link integrity shield; `scripts/update_knowledge_base.py`. |
| **PRINCIPLE-017** | Living Principles System & Automated Synchronization | Cross-IDE rule sync (`scripts/sync_principles.py`); context budget check (P001); schema compliance; freshness test gate; Tier 1B domain rules injection. |
| **PRINCIPLE-018** | Automatic Git Workflow | Automatic conventional commits (feat\|fix\|refactor\|docs\|chore\|test\|perf\|build\|ci) + adaptive push; explicit staging (zero `git add .`); pre-commit delivery triad (tests, read-only gates, staged diff); non-destructive recoil. |
| **PRINCIPLE-019** | Secret & Sensitive Data Hygiene | Zero credentials in tracked files, logs or ledgers; secrets via env/secret store; `.gitignore` credential baseline; `scripts/check_secrets.py` scans staged diffs + ledger; redacted diagnostics; rotate, never revert. |
<!-- principles:end -->
---

## ⚡ Disruption Recovery & Power-Loss Protection

If electricity cuts out, battery dies, or the computer crashes mid-task:
1. **Pre-flight Audit**: On a cold start, run this one command first (PRINCIPLE-004 R2):
   ```bash
   python scripts/disruption_recovery.py --resume
   ```
   It prints every `--audit` finding (conflicts, modified and untracked files, orphaned `.tmp_*` files, quarantined files; at most 20 entries per list), then the interrupted task, its plan and the phase to resume at. With no interrupted task it says "Ready" only when no uncommitted files exist.
2. **Findings Only**: `python scripts/disruption_recovery.py --audit` prints the same findings without resumption guidance.
3. **Recording In-Flight Checkpoints & Impact Rationale**: During multi-step implementations, record milestones cleanly (including optional pre-flight impact assessment):
   ```bash
   python scripts/disruption_recovery.py --checkpoint "task_name" --phase-num 2 --desc "description" --why "why" --benefits "benefits" --risks "risks" --mitigation "mitigation"
   ```
4. **Marking Completion**: When a task finishes successfully:
   ```bash
   python scripts/disruption_recovery.py --complete "task_name"
   ```
5. **Resetting In-Flight Tasks**: To abandon or reset a task without manually editing JSON:
   ```bash
   python scripts/disruption_recovery.py --reset "Superseded by new requirements"
   ```
6. **Purging Dangling Temp Files**: Safely remove orphaned `.tmp_*` files:
   ```bash
   python scripts/disruption_recovery.py --clean
   ```
7. **Atomic File Safety**: All writes use `os.fsync` and temporary staging, guaranteeing that sudden power-downs never leave 0-byte truncated source files. Corrupted JSON files from sudden shutdowns are automatically isolated to `*.corrupt_*` and self-healed.

---

## 🛠️ Adding New Principles to Your Project

1. Add `### PRINCIPLE-0XX: [Title]` (the next free ID) to `GUIDELINES.md` only, with `Problem`, `Concept`, `Invariant` and numbered `Rules`, under the right lifecycle heading.
2. Raise `MIN_PRINCIPLES` in `scripts/sync_principles.py` and `EXPECTED_PRINCIPLE_COUNT` in `tests/test_kit.py`; add the ID to this README and both checklists.
3. Run `python scripts/sync_principles.py`. On `[TOKEN EXCEEDED]` or `[TIER 1B HEADROOM]`, pay for the new capsule by condensing existing capsule narrative (PRINCIPLE-001 R9).
4. All six generated Tier 1 files then carry the new capsule.
