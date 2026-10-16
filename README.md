# 🤖 Universal AI Principles & Agent Operating System (Portable Kit)

> **Plug-and-Play AI Assistant Governance, Architecture Principles & Disruption Recovery for Any Software Project.**

This kit contains the complete, battle-tested AI governance system extracted from production development. It ensures that any AI coding assistant (Antigravity IDE, Cursor, Claude Code, GitHub Copilot, Gemini CLI, etc.) follows strict engineering principles, prevents progress loss from unexpected power cuts or crashes, maintains living documentation, and executes automated regression-shielded git workflows.

---

## ⚡ 30-Second Cold-Start Quick Reference

> **Orientation Contract for AI Agents & Developers**: Orient yourself in seconds with the verified commands and prerequisites below.

- **Runtime Prerequisites**: Python 3.10+ (Standard Library only — zero external pip dependencies).
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
| **Synchronize IDE Rules** | `python scripts/sync_principles.py` | <=1,500 est. tokens/target incl. a reserved 300-token Tier 1B |
| **Verify Rule Freshness** | `python scripts/sync_principles.py --check` | Read-only; exits 1 on rule drift |
| **Find Principles to Read** | `python scripts/sync_principles.py --involved <paths/commands/output>` | Same answer for every agent (PRINCIPLE-001 R3) |
| **Update AST & Knowledge** | `python scripts/update_knowledge_base.py` | AST parsed & validated without syntax errors |
| **Verify AST Map Freshness** | `python scripts/update_knowledge_base.py --check` | Read-only; exits 1 on stale codebase map |
| **Classify Lifecycle Track** | `python scripts/disruption_recovery.py --track` | Prints Track A/B/C of current changes (PRINCIPLE-002 R3) |
| **Audit Disruption Recovery**| `python scripts/disruption_recovery.py --audit` | Clean status check; detects surviving uncommitted files |
| **Resume Interrupted Task** | `python scripts/disruption_recovery.py --resume` | Disruption recovery guidance & surviving files |
| **Record Task Checkpoint**   | `python scripts/disruption_recovery.py --checkpoint <id> --phase <p>` | Appends atomic milestone to task ledger |
| **Complete Task Ledger**     | `python scripts/disruption_recovery.py --complete <task_id>` | Marks task completed in `.agents/task_ledger.json` |
| **Reset Active Task**        | `python scripts/disruption_recovery.py --reset [reason]` | Abandons/clears in-progress task in ledger |
| **Purge Temp Buffers**       | `python scripts/disruption_recovery.py --clean` | Safely unlinks orphaned `*.tmp_*` buffers |
| **Secret Scan Gate** | `python scripts/check_secrets.py --staged` | No credential patterns in staged diff or ledger (PRINCIPLE-019) |
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
│   │   └── domain.md.template          <- Template for project domain rules (Tier 1B)
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
  Then paste the **⚡ 30-Second Cold-Start Quick Reference** section into the top of your existing `README.md`.

### Step 2: Move Your Own Agent Instructions into Tier 1B
If the target already has its own `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `.cursorrules` or `.github/copilot-instructions.md`, move their project-specific rules into `.agents/rules/domain.md` (start from `.agents/rules/domain.md.template`, at most 1,200 chars), then delete the originals. Sync injects that block into every generated file. It never overwrites a file it did not generate: it stops with `[PROTECTED]` and names the file, so nothing is lost.

### Step 3: Run Principle Synchronization
Generate every Tier 1 file from `GUIDELINES.md`:

```bash
python scripts/sync_principles.py
```
This writes `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `.cursorrules`, `.agents/rules/principles.md` and `.github/copilot-instructions.md`, each within 1,500 est. tokens including your Tier 1B block.

### Step 4: Generate Your Knowledge Base
Run the knowledge base AST scanner to automatically index your project's classes and functions:

```bash
python scripts/update_knowledge_base.py
```
This generates `knowledge/codebase_map.md` with every exported class, method, argument, and docstring across your project!

---

## 🏛️ The 19 Core Principles (Lifecycle-Ordered)

The principles are strictly organized across **5 chronological execution phases**:

### 🏛️ Phase 1: Meta-Governance & Attentional Grounding
| Principle | Title | Core Concept |
|---|---|---|
| **PRINCIPLE-001** | Progressive Disclosure & Governance Frugality | Two-tier progressive disclosure (<1,500 tokens); self-sufficient invariant capsules; deterministic grep anchors; autonomous retrieval triggers. |
| **PRINCIPLE-002** | Lifecycle-Aligned Instruction Ordering | Monotonic 5-phase gate (Phase 4 passes before delivery); Track A/B/C computed by `--track`; urgency never skips gates. |
| **PRINCIPLE-003** | Empirical Grounding & Anti-Hallucination | Slice freshness & call-site check; manifest dependency grounding; platform parity; strict AST gate. |
| **PRINCIPLE-004** | Attentional Drift & Compaction Resilience | Bounded ledger (`task_ledger.json`); living plan SSOT; anti-repetition on compaction; AST-first retrieval. |

### 🧭 Phase 2: Pre-Flight Orientation & Planning
| Principle | Title | Core Concept |
|---|---|---|
| **PRINCIPLE-005** | AI Cold-Start Readiness & README Sync | Self-describing repo; 30s cold-start orientation (<20k chars); material surface sync; executable command parity; whole-tree drift shield. |
| **PRINCIPLE-006** | Incremental Checkpointing & Disruption Recovery | Zero progress loss from power outages; micro-milestone commits; disruption CLI (`scripts/disruption_recovery.py`); explicit micro-staging. |
| **PRINCIPLE-007** | Pre-Flight Impact & Quality Checklist | Track C gate: why, benefits, 4 blast-radius risks, scope ceiling, and anti-satisficing quality. |
| **PRINCIPLE-008** | Hierarchical Problem & Task Decomposition | Dual-pillar decomposition: top-down plan, bottom-up execution, bounded milestones ($2 \le M \le 6$), and leaf verifiability. |

### 🏗️ Phase 3: Architecture & Lean Implementation
| Principle | Title | Core Concept |
|---|---|---|
| **PRINCIPLE-009** | Modularity & Pluggable Architecture | 4-layer architecture (Presentation -> Service -> Domain <- Adapter); role protocols & registry; zero-config constructor DI; immutable DTOs. |
| **PRINCIPLE-010** | Performance & Resource Optimization | Algorithmic stream efficiency ($O(1)$ memory); non-blocking I/O; subprocess timeout gate; batch write coalescing; sub-second tests (<1s). |
| **PRINCIPLE-011** | Zero-Friction Onboarding & Instant Usability | Pure-stdlib clone-and-run; auto-init; mode transparency; cross-platform parity; deterministic exit codes. |
| **PRINCIPLE-012** | Token Frugality & Lean Code Architecture | Prompt cache alignment (>=80% hits); bounded diffs; terse schema generation; runaway circuit breakers; lean code. |

### 🛡️ Phase 4: Operational Verification & Resilience
| Principle | Title | Core Concept |
|---|---|---|
| **PRINCIPLE-013** | Crash Resilience & State Atomicity | Resilient atomic writes, shadow backups (.bak), schema migration, signal drain, and ENOSPC guards. |
| **PRINCIPLE-014** | Automated Test Verification (Regression Shield) | 100% test pass gate (<1s unit tier, <5s integration tier); test sanctity; RAII fixture reversion; anti-tautology; negative paths. |
| **PRINCIPLE-015** | Universal Operational Dogfooding & Chaos | Interactive UI/CLI/API dogfooding; portable process teardown; stdin parity; chaos perturbation. |

### 🚀 Phase 5: Living Synchronization & Delivery
| Principle | Title | Core Concept |
|---|---|---|
| **PRINCIPLE-016** | AI Knowledge Base & Continuous Sync | Modular `knowledge/` sync; atomic code-doc pairing; append-only ADRs; AST freshness gate; link shield. |
| **PRINCIPLE-017** | Living Principles System (Auto-Sync) | Multi-IDE rule sync; schema validation; freshness test gate; triad parity; Tier 1B domain rules. |
| **PRINCIPLE-018** | Automatic Git Workflow | Conventional Commits; explicit staging (zero blind add); pre-commit triad; adaptive push. |
| **PRINCIPLE-019** | Secret & Sensitive Data Hygiene | Zero credentials in tracked files, logs or ledgers; ignore-list baseline; pre-commit secret scan; rotate-not-revert. |

---

## ⚡ Disruption Recovery & Power-Loss Protection

If electricity cuts out, battery dies, or the computer crashes mid-task:
1. **Pre-flight Audit**: On cold start or when opening a terminal, run:
   ```bash
   python scripts/disruption_recovery.py --audit
   ```
   This automatically detects surviving uncommitted files, modified buffers, orphaned `.tmp_*` files, and interrupted tasks.
2. **Resumption Guidance**: To inspect surviving progress and receive structured recovery guidance:
   ```bash
   python scripts/disruption_recovery.py --resume
   ```
3. **Recording In-Flight Checkpoints & Impact Rationale**: During multi-step implementations, record milestones cleanly (including optional pre-flight impact assessment):
   ```bash
   python scripts/disruption_recovery.py --checkpoint "task_name" --phase "planning" --desc "description" --why "why" --benefits "benefits" --risks "risks" --mitigation "mitigation"
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
