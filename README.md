# 🤖 Universal AI Principles & Agent Operating System (Portable Kit)

> **AI governance, architecture principles & disruption recovery for any software project.**

The AI governance system extracted from production development: principles, power-cut recovery, documentation and regression-shielded workflows.

---

## ⚡ 30-Second Cold-Start Quick Reference

> **Orientation Contract**: verified commands and prerequisites below.

- **Runtime Prerequisites**: Python 3.10+ (Standard Library only — zero external pip dependencies) and `git`.
- **Canonical Regression Shield Gate**:
  ```bash
  python -m unittest discover tests
  ```
  *(100% test pass required before staging or committing).*

### 🛠️ Core Operational Command Matrix
| Operational Role| Canonical Command| Verification Gate|
|---|---|---|
| **Manage Projects**| `python aikit.py <cmd>`| `new`, `attach`, `list`, `status`, `check`, `fix` (ADR-119..124)|
| **Run Regression Suite**| `python scripts/check_test_budgets.py`| Both tiers pass; per-test average <=10ms unit, <=350ms integration|
| **Run One Tier**| `python -m unittest tests.test_kit` / `python -m unittest tests.test_integration`| Isolates a failing tier|
| **Synchronize IDE Rules**| `python scripts/sync_principles.py`| <=1,600 est. tokens/target incl. a reserved 300-token Tier 1B|
| **Verify Rule Freshness**| `python scripts/sync_principles.py --check`| Read-only; exits 1 on rule drift, or when a principle changed since the last commit lacks an ADR naming its `--citing` set (PRINCIPLE-000 R3)|
| **Find Principles to Read**| `python scripts/sync_principles.py --involved <paths/commands/output>`| Same answer for every agent (PRINCIPLE-001 R3)|
| **Cross-Principle Check Set**| `python scripts/sync_principles.py --citing <PRINCIPLE-NNN>`| Principles a rule change must be checked against (PRINCIPLE-000 R3)|
| **Update AST & Knowledge**| `python scripts/update_knowledge_base.py`| Rewrites the codebase map, then runs every audit of `--check` below; exits 1 on a syntax error (Python 3.10 grammar) or any audit failure|
| **Verify AST Map Freshness**| `python scripts/update_knowledge_base.py --check`| Read-only; exits 1 on a stale codebase map, README drift (PRINCIPLE-005), an ADR ID out of order, unfinished code (PRINCIPLE-007 R3) or a code-structure violation (PRINCIPLE-009 to PRINCIPLE-011)|
| **Classify Lifecycle Track**| `python scripts/disruption_recovery.py --track`| Prints Track A/B/C of current changes (PRINCIPLE-002 R3)|
| **Audit Disruption Recovery**| `python scripts/disruption_recovery.py --audit`| Clean status check; detects surviving uncommitted files|
| **Resume Interrupted Task**| `python scripts/disruption_recovery.py --resume`| Cold-start command: every `--audit` finding, then the interrupted task, its plan and resumption phase|
| **Record Task Checkpoint**| `python scripts/disruption_recovery.py --checkpoint <task_id> --phase-num <1-5> --desc <text>`| Appends a checkpoint (PRINCIPLE-002 R4); exits 2 when a task's first plan lacks `--why --benefits --risks --mitigation`, and warns when a task reaches Phase 3 with none (PRINCIPLE-007 R1, R6); exits 1 on credential-shaped text, or records `[REDACTED]` with `--redact` (PRINCIPLE-019 R3); `--handoff "next: ...; state: ...; failed: ...; open: ..."` records the packet `--resume` prints (PRINCIPLE-004 R2)|
| **Complete Task Ledger**| `python scripts/disruption_recovery.py --complete <task_id>`| Marks the active task completed in `.agents/task_ledger.json`; exits 1, changing nothing, if `<task_id>` is not the active task|
| **Reset Active Task**| `python scripts/disruption_recovery.py --reset [reason]`| Abandons/clears in-progress task in ledger|
| **Purge Temp Buffers**| `python scripts/disruption_recovery.py --clean`| Deletes orphaned `*.tmp_*` buffers older than 60 s; younger ones may be a write in progress|
| **Secret Scan Gate**| `python scripts/check_secrets.py --staged\|--commits <range> [--workspace <project>]`| Exits 1 on a credential pattern in the staged diff or agent memory, or when any surface could not be scanned (PRINCIPLE-019)|
| **Verify the Commit Itself**| `python scripts/verify_commit.py`| Runs every gate against the commit alone in a throwaway worktree; exits 1 when the commit holds less than the tree it was tested in (PRINCIPLE-018 R7)|
| **Reachability Shield**| `python scripts/check_reachability.py`| No unwired capability or phantom state key (PRINCIPLE-014 R7)|
| **Operational Dogfood Gate**| `python scripts/dogfood.py`| 5/5 tracks pass; zero host mutation (PRINCIPLE-015)|
| **Discover Any CLI**| `python scripts/<script>.py --help`| Prints usage and exits `0` in <200ms as a fresh process, writing nothing|
| **Sandbox the Ledger CLI**| `python scripts/disruption_recovery.py --workspace <dir> --audit`| Operates on `<dir>/.agents/`, never the repo ledger|

**Universal CLI contract (PRINCIPLE-011, PRINCIPLE-015).** Every CLI: `--help`/`-h` prints usage, writes nothing, exits `0`; exit `0` success, `1` operational failure, `2` misuse (an unknown flag is refused, never the default); failures print What → Why → Fix on stderr, never a traceback. `--check` is the read-only mode of `sync_principles.py` and `update_knowledge_base.py`.

---

## 📦 What's Inside

```text
portable_agent_kit/
├── README.md                       <- This Integration & Setup Guide
├── LICENSE                         <- GNU AGPL-3.0 License
├── aikit.py                        <- Project CLI
├── .gitignore                      <- Credential & local-state baseline (PRINCIPLE-019 R3)
├── AGENTS.md                       <- Generated Tier 1 capsules (auto-loaded by AGENTS.md-convention agents)
├── GUIDELINES.md                   <- Single source of truth: every principle, rule & checklist (Tier 2)
├── GEMINI.md                       <- Google Gemini & Antigravity IDE rules
├── CLAUDE.md                       <- Anthropic Claude Code configuration
├── .cursorrules                    <- Cursor IDE instructions
├── .windsurfrules                  <- Codeium Windsurf IDE instructions
├── .clinerules                     <- Cline / Roo Code IDE instructions
├── .github/
│   ├── copilot-instructions.md     <- GitHub Copilot instructions
│   └── workflows/
│       └── ci.yml                  <- Continuous verification gate (both tiers + freshness)
├── .claude/
│   ├── agents/                     <- Claude sub-agents (generated)
│   ├── settings.json               <- no agent may edit a task ledger
│   └── skills/
│       └── aikit/
│           └── SKILL.md            <- Claude Code operational runbook (native skill)
├── .agents/
│   ├── rules/
│   │   ├── principles.md           <- Antigravity / Agent IDE workspace rules
│   │   ├── domain.md.template      <- Template for project domain rules (Tier 1B)
│   │   ├── persistence.md.template <- Versioned state contract
│   │   └── readme_quickref.md.template <- Adopter README Quick Reference & tree (PRINCIPLE-005 R6)
│   ├── skills/
│   │   └── aikit/
│   │       └── SKILL.md            <- Antigravity operational runbook & command matrix
│   ├── agents/
│   │   └── opencode_worker.md      <- OpenCode subagent spec for free models
│   └── task_ledger.json            <- Disruption ledger for power-loss resilience (WAL)
├── .opencode/
│   └── agents/                     <- OpenCode subagent profiles (architect, coder, ...)
├── opencode.jsonc                  <- OpenCode provider, model & permission config
├── scripts/
│   ├── sync_principles.py          <- Generates 8 Tier 1 files from GUIDELINES.md
│   ├── disruption_recovery.py      <- Power-loss audit, atomic checkpointing & ledger CLI
│   ├── update_knowledge_base.py    <- Codebase AST symbol extractor & validator
│   ├── dogfood.py                  <- Operational dogfood runner (sandbox jail + chaos tracks)
│   ├── check_reachability.py       <- Invariant reachability shield (anti-dead-capability)
│   ├── check_test_budgets.py       <- Test tier budget gate (per-test ceilings)
│   ├── project_registry.py         <- Project discovery, stack detection, .aikit/ memory
│   ├── project_gates.py            <- A project's gates: detection, overrides, runs
│   ├── check_project_hygiene.py    <- Project source, asset & artifact hygiene scan
│   ├── ui_contract.py              <- Bounded UI-surface guard (opt-in .aikit/ui.json)
│   ├── ui_proof.py                 <- UI proofs: inventory diff + style drift lint (pure)
│   ├── aikit_cli.py                <- `aikit.py` commands and error triads
│   ├── subagent_delegate.py        <- `aikit delegate`: bounded OpenCode sub-agent runs
│   ├── project_publish.py          <- Uploads a project to its own GitHub repository
│   ├── check_secrets.py            <- Secret & sensitive data scanner (pre-commit gate)
│   └── verify_commit.py            <- Verifies a commit alone in a throwaway worktree
├── tests/
│   ├── test_kit.py                 <- Unit tier: in-process regression shield (<=10ms per test)
│   └── test_integration.py         <- Integration tier: concurrency, CLI contracts & dogfooding
└── knowledge/
    ├── INDEX.md                    <- Knowledge base table of contents & architecture map
    ├── architecture.md             <- High-level system architecture and component boundaries
    ├── services.md                 <- Core services, API contracts, and business logic
    ├── data_models.md              <- Data structures, schemas, and persistence models
    ├── state_and_ui.md             <- Presentation layer, UI state, and event loops
    ├── decisions.md                <- Architectural Decision Records (ADRs)
    ├── codebase_map.md             <- Auto-generated AST catalog of classes and functions
    ├── model_benchmarks.md         <- Subagent model benchmark database & selection tree
    ├── host_clients.md             <- Host client portability & cross-environment parity
    └── principles_audit_ledger.md  <- Snapshot audit at ADR-107 (not kept current)
```

---

## 🚀 Start a Project

Open this folder in any AI host and describe what to build. Each project gets its own folder under `projects/` (ignored by AIKit's git) and its own git repository; AIKit's gates, map and ledger never read it.

```bash
python aikit.py new my-app          # projects/my-app/: new git repo + .aikit/ memory
python aikit.py attach ../existing  # register a folder elsewhere; adds only .aikit/ and .gitignore lines
python aikit.py list                # every project, its stack and test command
python aikit.py status my-app       # its task, changes, decision; --exit-code fails when dirty or blocked, --json for CI
python aikit.py check my-app        # its tests, configured checks, hygiene, guidelines, secrets
python aikit.py check my-app --strict  # delivery gate: clean tree, map, no conflicts, no open UI task
python aikit.py ui init my-app        # React/Vite pilot: write a conservative .aikit/ui.json
python aikit.py ui init my-app --fast "npm run test" --paths "src/**"  # manual other-stack contract
python aikit.py ui begin my-app --surface menu  # bound edits to one declared UI surface
python aikit.py ui verify my-app       # scope, budget, fast + snapshot proofs, style drift
python aikit.py ui verify my-app --json  # stable finding codes for CI
python aikit.py ui allow my-app "Btn*" --reason "<why>"  # record intended inventory removals
python aikit.py ui finish my-app --reviewed  # close after review; evidence in .aikit/ui_history.json
python aikit.py ui abort my-app        # restore only the surface; keep unrelated work
python aikit.py fix my-app          # restore memory/README, refresh map, then check
python aikit.py guideline my-app "money is integer cents" --source user  # project rule
python aikit.py publish my-app      # own private GitHub repo, scanned first
```
A project's memory is its `.aikit/` folder (record, ledger, decisions, guidelines: its own rules, below the principles), committed in its repository; ledger commands take `--workspace projects/<name>`. Stack and test command are detected from its files (Python, Node, Rust, Go, Java, .NET); `--test "<cmd>"` overrides. Before a project commit, `check` asks you to record `checklists: passed` or the failed IDs in the task's latest checkpoint; a deliberate finding needs `hygiene: allow <reason>` on its line or the one directly above it. `check_project_hygiene.py --artifacts` adds test modules, untracked source/output, an untracked root README and tracked caches. The `ui` commands are opt-in: commit `.aikit/ui.json` with named surfaces, protected paths, a fast proof command, an optional `snapshot` inventory command and optional `style.theme_paths`, plus file/line limits; `verify` refuses out-of-surface edits, protected paths, budget overruns, a moved baseline, a red proof, lost inventory entries (unless `ui allow <pattern> --reason <why>` records them, and `finish` prints each one) and hardcoded color/font literals outside the theme, except a font value that is a `var()` theme token; `finish` needs `--reviewed` (optionally `--reviewer <name>`) and appends the task's evidence to `.aikit/ui_history.json`; an open UI task blocks `status --exit-code`, `check --strict` and auto-push (ADR-160, ADR-161, ADR-163). Set `ui_required: true` in `.aikit/project.json` to make `check --strict` and `publish` require `.aikit/ui.json`; a missing or invalid contract or open task blocks delivery. With `ui_required`, each declared surface must also match a finished task's recorded digest, and `ui verify --json` returns stable codes plus a `ui.error` envelope on operational errors. `status --json` and `resume --json` report the project, its guidelines, the disruption audit and `clean` (the same verdict `--exit-code` uses), with a `project.error` envelope on failure. `publish` also runs the project's gates and test gate before uploading.

## 📥 Alternative: Copy AIKit Into an Existing Project

The primary path is above: keep the project under `projects/`. To instead govern a repository in
place, copy the source of truth and tooling into it and generate the rest:

```bash
cd portable_agent_kit
mkdir -p /path/to/target/.agents
cp -r GUIDELINES.md scripts knowledge /path/to/target/
cp -r .agents/rules .agents/skills /path/to/target/.agents/
cd /path/to/target && python scripts/sync_principles.py && python scripts/update_knowledge_base.py
```

- **Do not copy** `tests/`, `.github/` or `.agents/task_ledger.json`: they are AIKit's own. The CLI
  gates in the matrix above carry the enforcement.
- Replace the copied `knowledge/` documents with your project's, and copy
  `.agents/rules/readme_quickref.md.template` into your `README.md`, filling every `<FILL` placeholder.
- If the target already has instruction files, move their project-specific rules into
  `.agents/rules/domain.md` (max 1,200 chars) and delete the originals. Sync injects that block into
  all 8 Tier 1 files and refuses to overwrite a hand-authored file (`[PROTECTED]`).
- The two commands above generate the 8 Tier 1 files (each <=1,600 tokens including Tier 1B) and
  `knowledge/codebase_map.md`, the AST catalogue of every class, method, argument and docstring.

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
| **PRINCIPLE-005** | AI Cold-Start Readiness & Living Documentation | README <=22.5k chars: prerequisites, test command, tree; user-visible changes update it same commit; `update_knowledge_base.py --check` gates it. |
| **PRINCIPLE-006** | Incremental Progress Checkpointing & Disruption Recovery | Commit `[milestone N/M]` once Phase 4 passes under PRINCIPLE-018 R1; failing work uncommitted via `--checkpoint`; `--complete`/`--reset` before switching tasks; `--clean` stale `.tmp_*`. |
| **PRINCIPLE-007** | Pre-flight Impact & Quality Checklist | Track C first plan checkpoint carries --why --benefits --risks (contract, dependency, concurrency, state) --mitigation; no TODO or stub; no change outside the plan. |
| **PRINCIPLE-008** | Hierarchical Problem & Task Decomposition | Plan of M<=6 milestones (more: split into tasks), built bottom-up, each passing Phase 4 alone; re-plan = new `[1/M']` checkpoint; sub-agents never write the ledger. |

### 🏗️ Phase 3: Architecture & Lean Implementation
| Principle | Title | Capsule |
|---|---|---|
| **PRINCIPLE-009** | Modularity & Pluggable Architecture | Every module: no junk-drawer name, roles of 1-5 methods, no import cycle (gated). At a pluggable boundary: 4 layers, registry lookup, constructor DI with default, frozen DTOs. |
| **PRINCIPLE-010** | Performance & Resource Optimization | Stream uncontrolled input; threads only for steps >=200ms; timeout= on subprocess, with on open(); one fsync per file; `--help` <200ms; unit <=10ms, integ <=350ms/test. |
| **PRINCIPLE-011** | Zero-Friction Onboarding & Instant Usability | Only declared deps; creates its dirs; prompts only with `--interactive`; no `os.environ[...]` reads; exit 0/1/2; errors give `Why:`/`Fix:`; demo <10s; other software: its `aikit.py` project is the workspace (R8). |
| **PRINCIPLE-012** | Token Frugality & Lean Code Architecture | LLM code: <=16k-char payloads, static prefix first, schema-checked replies, 429 backoff, step caps; agent: diff -U3, search <=50 hits, relative paths. |

### 🛡️ Phase 4: Operational Verification & Resilience
| Principle | Title | Capsule |
|---|---|---|
| **PRINCIPLE-013** | Crash Resilience, State Atomicity & Power-Loss Recovery | State files: >=10MB free, temp + fsync + os.replace (5 tries) + dir fsync, .bak, advisory locking 3s/30s stale, corrupt -> quarantine/.bak/migrate. Generated: temp + fsync + replace. |
| **PRINCIPLE-014** | Automated Test Verification & Continuous Test Coverage | 100% test pass gate; behaviour change = failing-first test; weakening a test needs user approval + ADR naming it; unit <=10ms/test, no spawns/sleeps; integ <=350ms/test; tempdir + addCleanup; `scripts/check_reachability.py`. |
| **PRINCIPLE-015** | Universal Operational Dogfooding & Chaos Verification | Domain-specific interactive dogfooding via `scripts/dogfood.py` as a commit gate; golden path + chaos perturbation; non-interactive stdin parity; portable RAII process tree teardown; ephemeral safety jail; terse reporting (<=15 lines). |

### 🚀 Phase 5: Living Synchronization & Delivery
| Principle | Title | Capsule |
|---|---|---|
| **PRINCIPLE-016** | AI Knowledge Base & Continuous Synchronization | Canonical `knowledge/` sync; atomic code-and-doc pairing; monotonic append-only ADR register; strict AST syntax validation; link integrity shield; `scripts/update_knowledge_base.py`. |
| **PRINCIPLE-017** | Living Principles System & Automated Synchronization | Rule sync (`scripts/sync_principles.py`); context budget check; schema compliance; freshness test gate; Tier 1B domain rules (<=1,200 chars). |
| **PRINCIPLE-018** | Automatic Git Workflow | Conventional commits (`--validate-commit`) + adaptive push, never forced, only if authorized (R1); explicit staging (no `git add .`); pre-commit triad (tests/gates/diff); commit verified alone pre-push (R7); non-destructive recoil. |
| **PRINCIPLE-019** | Secret & Sensitive Data Hygiene | Zero credentials in tracked files, logs or ledgers; secrets via env/secret store; `.gitignore` credential baseline; `scripts/check_secrets.py` scans staged diffs + ledger; redacted diagnostics; rotate, never revert. |
<!-- principles:end -->
---

## ⚡ Disruption Recovery & Power-Loss Protection

If electricity cuts out, battery dies, or the computer crashes mid-task:
1. **Pre-flight Audit**: On a cold start, run this one command first (PRINCIPLE-004 R2):
   ```bash
   python scripts/disruption_recovery.py --resume
   ```
   It prints every `--audit` finding, then the interrupted task, its plan and the phase to resume at. With no interrupted task it says "Ready" only when no uncommitted files exist.
2. **Everything else** (`--audit`, `--checkpoint`, `--complete`, `--reset`, `--clean`) is in the command matrix above; a task's first plan checkpoint must carry `--why --benefits --risks --mitigation`.
3. **Atomic File Safety**: state files are written to a temp file, fsynced and renamed (PRINCIPLE-013); a corrupt ledger is moved to `*.corrupt_*` and restored from its `.bak`.

---

## 🛠️ Adding New Principles to Your Project

1. Add `### PRINCIPLE-0XX: [Title]` (the next free ID) to `GUIDELINES.md` only, with `Problem`, `Concept`, `Invariant` and numbered `Rules`, under the right lifecycle heading.
2. Raise `MIN_PRINCIPLES` in `scripts/sync_principles.py` and `EXPECTED_PRINCIPLE_COUNT` in `tests/test_kit.py`; add the ID to this README and both checklists.
3. Run `python scripts/sync_principles.py`. On `[TOKEN EXCEEDED]` or `[TIER 1B HEADROOM]`, pay for the new capsule by condensing existing capsule narrative (PRINCIPLE-001 R9).
4. All 8 generated Tier 1 files then carry the new capsule.
