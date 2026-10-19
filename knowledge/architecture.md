# System Architecture & Component Boundaries

This document describes how AIKit is built. The rules it follows live only in `GUIDELINES.md`; this file names the principle a mechanism serves and never restates its rules (PRINCIPLE-001 R7). Numbers below cite the code constant that holds them, so the value has one home.

## 🏛️ Components & Data Flow
AIKit is seven standard-library CLIs in `scripts/` plus the files they read and write. No CLI imports another (PRINCIPLE-009 R5); `services.md` lists each one's responsibility and gate.

```text
GUIDELINES.md ──sync_principles.py──▶ AGENTS.md, CLAUDE.md, GEMINI.md, .cursorrules,
  (only hand-edited rules)              .github/copilot-instructions.md, .agents/rules/principles.md,
.agents/rules/domain.md (Tier 1B) ──▶   README.md principle table (between markers)

repository *.py ──update_knowledge_base.py──▶ knowledge/codebase_map.md
                  └─ audits: README, ADR register, unfinished code, code structure

agent ──disruption_recovery.py──▶ .agents/task_ledger.json (AIKit's only state file)

user ──aikit.py──▶ projects/<name>/ (own git repo) with .aikit/project.json; projects/attached.json

Phase 4 gates: both test tiers, sync_principles.py --check, update_knowledge_base.py --check,
               check_reachability.py, check_secrets.py, dogfood.py   (PRINCIPLE-018 R3)
```

## 🧭 Projects: AIKit as the Workspace
AIKit is the folder a person opens in an AI host; the software it builds lives in `projects/<name>/`, each its own git repository with its memory in `.aikit/`. See [ADR-119](decisions.md).

- **Isolation**: `projects/` is in `.gitignore`, in `IGNORE_DIRS` (codebase map, structure audits) and in `SWEEP_PRUNED_DIRS` (temp-file and quarantine sweeps), so no project file reaches AIKit's gates, map or ledger, and `--track` never sees one.
- **Discovery**: a folder under `projects/` is a project when it holds `.aikit/project.json`; only folders elsewhere are listed in `projects/attached.json`. `attach` refuses a folder that contains or sits inside AIKit outside `projects/`.
- **Project guidelines**: `.aikit/guidelines.md` holds the project's own rules (PRINCIPLE-001 R4 project tier). They cannot enter Tier 1, which every project shares, so `aikit status` and `aikit resume`, the project cold start, print them with their rank; `guideline_errors` keeps them well-formed and unable to override a principle (ADR-129).
- **Self-check**: the built-in `guidelines` gate runs `update_knowledge_base.py --workspace <project> --check`, whose `check_workspace` is the same code path as AIKit's own `--check`: map freshness (once `fix` wrote a map), the full PRINCIPLE-005 README audit, unfinished code, code structure and the ADR register (ADR-124, ADR-128).
- **Detection**: `DETECTORS` maps marker files to a stack and its test command; a new stack is one row.
- **Gates**: `project_gates.resolve_gates` orders a project's gates as test, extras from `EXTRA_GATES` (only what the project's own config declares: ruff/mypy tables, `lint`/`typecheck`/`build` package scripts, `go vet`), `project.json` `gates` overrides, then the built-in hygiene scan, the guidelines check and the secret scan (ADR-137). `run_shell` runs each through the platform shell under `supervised()` with stdin closed and `GATE_TIMEOUT_SECONDS`; every gate runs even after a failure (ADR-122).
- **Memory**: `.aikit/` holds `project.json`, `decisions.md` and `task_ledger.json`. Every ledger command takes `--workspace <project>`, so checkpoints, `--resume`, `--audit` and `--track` read the project's ledger and run `git status` in the project's repository; the project ledger is bookkeeping (`BOOKKEEPING_PATHS`), so a checkpoint never changes the project's track. Project work runs `python aikit.py check <name>` as its Phase 4 (ADR-123); AIKit's other gates cover AIKit only (PRINCIPLE-011 R8, ADR-121). `new` commits the memory as the first commit, and warns instead of inventing an author when git has no identity (ADR-120).
- **Delivery**: `check --strict` adds the commit-level baseline: a git repository, no uncommitted non-bookkeeping changes, and `.aikit/codebase_map.md` when Python sources exist. Ordinary `check` warns about those gaps and skips auto-push while the tree is dirty, so an older commit is never presented as the tested one (ADR-142).

## 🤝 Sub-Agent Roles Across Hosts
Each role (`architect`, `coder`, `explorer`, `reviewer`, `tester`, `worker`) has one text, `.opencode/agents/<role>.md`. OpenCode runs it directly (`aikit delegate`); `sync_principles.py` renders it into `.claude/agents/<role>.md` with the tools and model from `CLAUDE_AGENT_ROLES`, and `--check` reports a drifted copy. `render_claude_agent` refuses a description that would break YAML frontmatter. See [ADR-131](decisions.md).

## 🗂️ Single Source of Truth & Generated Tier 1 Files
The rules live in exactly one hand-edited file. See [ADR-048](decisions.md).

| File | Tier | Role |
|---|---|---|
| `GUIDELINES.md` | 2 | The only hand-edited copy: Problem, Concept, Invariant, Rules, checklists |
| `AGENTS.md` | 1 | **Generated** capsules; auto-loaded by AGENTS.md-convention agents |
| `CLAUDE.md`, `GEMINI.md`, `.cursorrules`, `.github/copilot-instructions.md`, `.agents/rules/principles.md` | 1 | Generated capsules for each IDE |

- **Why AGENTS.md cannot be the specification**: tools following the AGENTS.md convention load it automatically, so whatever it holds is Tier 1; as the master spec it put ~13 times the budget into always-on context.
- **Write safety**: `is_generated_target()` recognises current and legacy generated headers; anything else is refused with `[PROTECTED]` before any target is written, protecting an adopter's own `CLAUDE.md`.
- **Schema gate**: `parse_principles()` rejects a principle without Problem, Concept, Invariant or Rules, a rule without an audience tag, a duplicate ID or a phase inversion (PRINCIPLE-017 R1, R5).
- **Cross-principle gate**: `--check` compares `GUIDELINES.md` and `decisions.md` with `HEAD`; every principle whose section changed needs a new ADR naming its `--citing` set (PRINCIPLE-000 R3, ADR-073).

## 📏 Tier 1 Context Budget
Always-injected rules cost context on every turn, so the budget is a gate. See [ADR-046](decisions.md).

| Ceiling | Constant | Enforcement |
|---|---|---|
| Total per target, Tier 1B included | `TARGET_TOKEN_BUDGET` | `[TOKEN EXCEEDED]` blocks sync |
| Tier 1B reservation | `MAX_DOMAIN_CHARS` must still fit with no domain rules loaded | `[TIER 1B HEADROOM]` blocks sync |
| Early warning | 90% of budget | `[BUDGET WARN]`, advisory |

Budget is reclaimed by deleting duplication, never by compressing mechanisms out of a capsule (PRINCIPLE-001 R2); `TestTier1ContextBudget` pins the mechanism words capsules must keep.

## 🛡️ Invariant Reachability Shield
`scripts/check_reachability.py` serves PRINCIPLE-014 R7. See [ADR-044](decisions.md).

| Audit | Catches |
|---|---|
| Call-site reachability | a function defined and tested but called from no production path |
| Key round-trip integrity | a persisted key read by production code that no production code writes |

References are counted broadly (`ast.Name` loads, attributes, `ImportFrom`), because a function stored in a tuple or passed as a callback is reachable; `PUBLIC_API_ALLOWLIST` names deliberate public API, and a test asserts no entry outlives its symbol.

## 🎮 Operational Dogfood Runner
`scripts/dogfood.py` serves PRINCIPLE-015 for AIKit's own CLIs. See [ADR-043](decisions.md).

| Track | What it proves |
|---|---|
| golden lifecycle | checkpoint, resume and complete through the real ledger CLI, asserted on disk |
| chaos perturbation | malformed flag, missing value, corrupted and 0-byte ledgers handled without a traceback |
| read-only gates | the four read-only gates pass, run concurrently in a pool of at most `os.cpu_count()` |
| help + startup budget | every CLI answers `--help` within `budget_ms` as a fresh process |
| blast radius | `repo_fingerprint()` of tracked files is unchanged after the run |

- **Concurrency**: tracks not in `TIMED_TRACKS` run concurrently, each in its own sandbox folder with its own log; the startup-budget track runs alone afterwards so parallel load cannot inflate its timings (ADR-122).
- **Supervision**: `supervised()` kills the whole process tree (`taskkill /F /T` on Windows, `killpg(SIGKILL)` on POSIX).
- **Sandbox**: `--workspace <dir>` keeps every ledger write inside the run's temporary directory; the only write outside it is the git-ignored `.agents/dogfood_last_run.log`.
- **UTF-8 capture**: every spawn forces `encoding="utf-8"`; the locale codec silently dropped the CLIs' non-ASCII output.

## 🧪 Two-Tier Test Budget
Both tiers run under `python -m unittest discover tests`. See [ADR-040](decisions.md).

| Tier | Module | Budget | Contents |
|---|---|---|---|
| Unit | `tests/test_kit.py` | under 1s, no process, no sleep | parsing, classification, ledger atomicity, AST gates, rule wording |
| Integration | `tests/test_integration.py` | under 5s, timeout per spawn | multi-process races, real CLI contracts, real `git`, the dogfood run, the CLI matrix |

The unit tier is fast by construction: `TestTierBudgetDiscipline` fails on a spawn or sleep call in `test_kit.py`, and a module-level guard refuses any process the unit tier starts indirectly (ADR-049). `TestSuiteHygiene` checks every test asserts and no test module imports a network library (ADR-099).

## 💾 Ledger Concurrency & Durability
- **Locked read-modify-write**: `locked_ledger()` holds the advisory lock across load, change and save; `record_checkpoint`, `mark_task_completed` and `reset_active_task` all use it (PRINCIPLE-013 R3).
- **Lock behaviour**: acquisition times out with a `TimeoutError` carrying the triad; a lock older than 30s is broken by an atomic rename; Windows `PermissionError` during a concurrent delete is retried as contention (ADR-077).
- **Durability**: `atomic_write_json()` checks headroom, rotates `.bak`, writes a temp file, fsyncs, retries `os.replace` and fsyncs the directory (`fsync_dir`, a no-op on win32).
- **Recovery**: `load_ledger()` quarantines a corrupt file, falls back to `.bak` and migrates the schema, warning at each failed step; the CLI turns an `OSError` or `TimeoutError` into the triad and exit 1 (`report_operational_error`, ADR-098).
- **Version refusal**: `load_ledger()` validates before normalizing. A newer schema raises `UnsupportedLedgerVersion`; the file is left byte-identical, `--resume`/`--audit` report `BLOCKED` and exit 1, and a missing version is treated as legacy `1` in memory only. The adopter recipe is `.agents/rules/persistence.md.template`.
- **Resumption**: `resolve_active_phase()` reads the `active_phase` writers produce; `task_plan_checkpoint()` returns the latest `[1/` Phase 2 checkpoint (PRINCIPLE-004 R1).

## 🔀 Git Status Classification
`classify_git_status()` is pure, so every porcelain state is testable without git.

| Code | Bucket |
|---|---|
| `??` | untracked |
| `!!` | ignored (skipped) |
| `DD` `AU` `UD` `UA` `DU` `AA` `UU` | conflicted (git's closed unmerged set) |
| any other non-blank XY | modified |

`AA` and `DD` are conflicts without a `U`, so a `"U" in xy` test is insufficient; `modified` is the open default so no future code is dropped.

## 🖥️ Universal CLI Contract
Every entrypoint in `scripts/` implements one contract (PRINCIPLE-011 R5, R6), checked by `TestOperationalDogfooding` and the dogfood chaos track. See [ADR-039](decisions.md).

| Invocation | Required behaviour | Exit |
|---|---|---|
| `--help` / `-h` | usage on stdout, nothing on stderr, no writes, within the dogfood `budget_ms` | `0` |
| unknown flag or missing value | What, `Why:`, `Fix:` on stderr; the default action is never run | `2` |
| normal operation | action performed; a failure prints the triad, never a traceback | `0` / `1` |

Validators (`validate_argv`, `argv_value_errors`, `_validate_argv`) skip the value of value-taking flags, so free text such as `--desc "-n refactor"` is never read as an option, and a `--`-prefixed token is never consumed as a value.
