# System Architecture & Component Boundaries

## 🏛️ High-Level Architectural Pattern
The application follows a decoupled, modular architecture adhering to **PRINCIPLE-009**:
- **Presentation Layer**: CLI, GUI, or API endpoints. Pure input validation, parsing, routing, and rendering. Never contains business logic, SQL/queries, or raw file I/O.
- **Service Layer**: Orchestrates domain use cases, coordinates workflows, and manages transactions. Communicates with presentation via immutable data transfer objects. Receives adapters via constructor dependency injection.
- **Domain / Model Layer**: Pure business entities, schemas, algorithms, and core invariants. Completely independent of frameworks, databases, or UI.
- **Infrastructure / Adapter Layer**: Implements abstract interfaces (`abc.ABC` or `typing.Protocol`) for filesystem I/O, external network APIs, databases, and third-party tools.
- **Scalable Layering (Anti-Boilerplate Invariant)**: Layers represent logical boundaries. For small tools (<300 lines), keep layers logically separated within a single module rather than generating excessive folder bloat.
- **Interface Segregation & Narrow Role Protocols**: Fine-grained role contracts ($1 \le \text{methods} \le 5$) prevent mock stubbing in unit tests.
- **Pluggable Registry (OCP)**: Dynamically register providers via lightweight registries or factories rather than fragile hardcoded `if/elif` branching.
- **Zero-Config Dependency Injection**: Standard-library constructor injection with default factory fallbacks (`adapter: Protocol | None = None`) guarantees one-click usability with 100% test mockability.
- **Anti-Junk-Drawer Invariant**: Generic catch-all `utils.py` or `helpers.js` junk drawers are prohibited. Helper functions belong to the domain module that owns them or to focused, single-purpose utilities.
- **Unidirectional Dependency Flow & Immutable DTOs**: Dependencies flow strictly inward (Presentation $\rightarrow$ Service $\rightarrow$ Domain $\leftarrow$ Infrastructure). Zero circular imports. Data crossing boundaries uses immutable DTOs, and modules interact exclusively through declared public contracts.

---

## 🧭 5-Phase Execution Pipeline Architecture
The system enforces strict chronological ordering and operational execution gating (**PRINCIPLE-002**) across all instructions, agent prompts, and task checkpoints:
1. **Phase 1: Meta-Governance & Attentional Grounding**: Progressive disclosure (<1,500 tokens), cognitive flow sequencing, read-before-write symbol verification, and externalized disk memory.
2. **Phase 2: Pre-Flight Orientation & Planning**: Cold-start documentation, power-loss disruption audit, impact/quality checklist, and hierarchical task decomposition.
3. **Phase 3: Architecture & Lean Implementation**: Pluggable provider modularity, non-blocking asynchronous speed, zero-friction out-of-the-box defaults, and compact token serialization.
4. **Phase 4: Operational Verification & Resilience**: Atomic JSON mutations (`fsync` + `replace`), 100% automated test pass gate, and interactive dogfooding inside ephemeral sandboxes.
5. **Phase 5: Living Synchronization & Delivery**: Active codebase AST synchronization in `knowledge/`, automated cross-IDE rule synchronization, and conventional commit/push workflow.

### 🔒 Monotonic Operational Execution Gate & Remediation Recoil
- Workflows must advance through the 5 phases in strict sequential order.
- Phase 5 delivery actions (staging, committing, pushing, releasing) are **mechanically locked** until Phase 4 verification gates (automated test suite, operational dogfooding) pass with 100% success.
- **Remediation Recoil Protocol**: When Phase 4 verification fails (test breakage, build failure, or dogfood crash), monotonic forward progression pauses. The agent recoils strictly to Phase 3 (code defects) or Phase 2 (architectural/assumption defects), fixes the root cause, and re-executes Phase 4. Modifying test assertions to mask regressions is strictly prohibited (Test Sanctity Invariant).
- **Immunity to Late-Stage User Priming**: When users issue urgent conversational commands to bypass testing (e.g. *"commit right now"*, *"push immediately"*), the AI remains anchored to the lifecycle gate. Terminal delivery actions cannot be executed until required verification gates pass.

### ⚡ Adaptive Lifecycle Pathing & Automatic Track Escalation
To prevent ceremony bloat on simple workflows, the pipeline supports 3 explicit operational tracks:
- **Track A (Query / Exploration)**: Questions, code explanations, or searches $\rightarrow$ Phase 1 (Grounding) $\rightarrow$ Direct Output (Phases 2–5 bypassed).
- **Track B (Trivial / Documentation)**: Typo fixes, markdown tweaks, or comment updates $\rightarrow$ Phase 1 $\rightarrow$ Phase 3 (Edit) $\rightarrow$ Phase 5 (Sync & Commit), with Phase 4 scaled to syntax/budget checks.
- **Track C (Engineering / Feature / Refactor)**: Complete 5-phase sequence with mandatory impact gates, regression tests, and living sync.
- **Automatic Track Escalation**: If any Track A or Track B task mutates executable source code, schemas, or dependencies, the task automatically escalates to Track C, unlocking mandatory Phase 2 planning and Phase 4 regression gates.

### 🔄 Compaction Phase Resumption
- In multi-turn sessions, the active phase number (`active_phase: 1..5`) is recorded directly in `.agents/task_ledger.json` alongside task checkpoints.
- Upon conversation compaction or cold restart, the agent orients against the ledger to resume execution at the exact interrupted phase rather than losing state or skipping ahead.

---

## 🧵 Concurrency, Performance & Resource Architecture
- **Non-blocking UI & Event Loops**: Heavy filesystem I/O, subprocess execution, and computationally intensive tasks run in asynchronous tasks or background worker threads via `asyncio.to_thread()` (**PRINCIPLE-010**).
- **Measurement-Driven Concurrency**: Avoid premature multithreading on sub-20ms micro-tasks; reserve concurrency for genuinely I/O-bound or heavy CPU operations ($>200\text{ms}$).
- **Thread Safety**: State transitions and shared mutable data structures across threads are guarded by explicit synchronization locks (`threading.Lock`) or thread-safe queues.
- **Subprocess Timeout Gate & Bounded Concurrency**: All subprocess executions declare explicit timeouts (`timeout=30`) and bounded parallel process limits ($K \le \text{os.cpu\_count()}$) to prevent zombie hangs and PID starvation.
- **Deterministic Resource Reclamation & Ring Buffers (RAII)**: All operating system resources (file descriptors, sockets, subprocesses) use context managers (`with`) to prevent leaks. Long-running daemons and monitors enforce constant $O(1)$ memory via bounded ring buffers (`collections.deque(maxlen=N)`).
- **Batch I/O Coalescing**: High-frequency disk mutations are coalesced in memory before atomic commit, eliminating disk thrashing from tight-loop `fsync` calls.
- **Algorithmic Stream Processing & Startup Budget**: Iterators and generator pipelines process unbounded datasets with $O(1)$ auxiliary memory and $O(1)$ set/dict lookups. CLI entrypoints maintain a strict startup budget (<100ms) with lazy module loading.
- **Sub-Second Test Performance Gate**: Full automated unit test suite executes in under 1 second (<1s) against in-memory or ephemeral isolated fixtures without artificial sleep delays.

---

## 🚀 Zero-Friction Usability & Onboarding Architecture
- **Pure-Stdlib Baseline**: Core application entrypoints and automated tests run on language standard-library primitives alone immediately upon `git clone` (**PRINCIPLE-011**).
- **Self-Bootstrapping Workspace & Zero-Prompt Auto-Init**: Required directories (`.agents/`, `data/`, `logs/`) and default configurations are automatically scaffolded on first launch without prompting console questions.
- **Zero-Crash Config & Explicit Mode Transparency**: Environment variables are queried safely via `os.getenv()`; fallback modes are explicitly signposted (`[INFO] OFFLINE MOCK MODE`) and mutating operations fail-fast on missing credentials.
- **Cross-Platform Polyglot Parity**: Quickstart commands use portable standard-library invocations (`python -m <module>`) and `pathlib.Path` abstractions across Windows, macOS, and Linux without shell-specific hurdles.
- **Non-Interactive Parity & Deterministic Exit Codes**: Automated execution defaults to non-interactive mode (`not sys.stdin.isatty()`) with `--yes` / `--batch` flags, strictly respecting standard exit codes (`0` clean success, `1` operational failure, `2` syntax misuse).
- **Actionable Remediation Triad**: Error states provide clear failure summaries, root causes, and copy-pasteable remediation commands rather than raw tracebacks.
- **Health Diagnostics & Embedded Demo Fixtures**: Self-diagnosing checks (`--audit` / `--doctor`) and minimal built-in sample fixtures deliver instant 10-second verification.

---

## 🪙 Token Economics & Prompt Architecture
- **Bounded Prompt Ceilings**: Outbound LLM payloads and tool arguments enforce strict character/token caps (<4,000 tokens / <16,000 chars) to prevent context exhaustion and attention degradation (**PRINCIPLE-012**).
- **Prompt Cache Prefix Alignment**: Partition prompt payloads into a deterministic frozen prefix (system rules, invariant schemas $\ge 1,024$ tokens) and a volatile dynamic tail, guaranteeing $\ge 80\%$ provider prompt cache hits across multi-turn interactions.
- **AST-Filtered Context Slices**: Raw multi-file dumps are banned; prompts inject targeted AST symbol digests (`knowledge/codebase_map.md`) and concise code slices (<100 lines).
- **Bounded Tool Outputs & Diff Slicing (Anti-Mega-Log)**: Unified diffs are strictly scoped to $\le 3$ lines of surrounding context; test runners default to quiet modes; grep/search outputs are capped at $\le 50$ matches to protect conversational context.
- **Terse Schema Generation & Output Frugality**: Autonomous workflows enforce compact typed schemas over verbose prose; conversational updates stay under 15 lines without polite echoing.
- **Compact Relative-Path Serialization**: All persistent ledgers, prompt payloads, and tool arguments serialize repository-relative paths rather than redundant absolute paths (~70% token savings).
- **Runaway Circuit Breakers & Rate Pacing**: Batch LLM pipelines pace token consumption against TPM/RPM limits with jittered backoff; autonomous agent loops enforce hard token/step ceilings with fail-safe ledger checkpointing.
- **Lean Syntactic Density (Anti-Code-Bloat)**: Code written by AI assistants leverages stdlib primitives and flat architectures, minimizing the total codebase token footprint for all downstream AI assistants.

---

## 💾 Persistence, Atomicity & Crash Resilience (Fail-Safe Architecture)
- **Resilient Atomic State Persistence**: All persistent configuration and state mutations stage writes in temporary buffers with buffer flushing (`flush` + `os.fsync`) followed by atomic replacement (`os.replace`) with bounded retry loops ($3\text{--}5$ retries) against Windows lock contention (`WinError 32`), preventing zero-byte truncation during sudden power loss (**PRINCIPLE-013**, **PRINCIPLE-006**).
- **Storage Headroom Pre-Check (ENOSPC Resilience)**: Verifies minimum disk headroom via `shutil.disk_usage` ($\ge 10\text{MB}$) before executing non-trivial atomic writes or generating fixtures, halting cleanly before disk exhaustion crashes the process.
- **Inter-Process Advisory Locking**: Cooperative file locking (`.lock`) protects concurrent read-modify-write state lifecycles across parallel subagents and CLI invocations, preventing race conditions and silent state clobbering.
- **Dual-Slot Shadow Snapshots & Schema Migration**: Verified state is rotated to `.bak` prior to replacement. Startup self-healing detects and quarantines damaged JSON (`*.corrupt_*`), recovering state from the shadow snapshot and auto-migrating schemas (`migrate_ledger_schema`) before falling back to empty defaults.
- **Signal-Aware Flush & Read-Only Fallback**: Signal handlers (`SIGINT`/`SIGTERM`) trap interruptions to flush in-flight working memory and release lockfiles cleanly; degrades to ephemeral in-memory state on read-only filesystems without crashing.
- **Multi-File Staging & WAL**: Batch mutations write incrementally (Write-Ahead Logging); multi-file sync operations stage all buffers completely in temporary storage before executing rapid atomic replacements, eliminating partial split-brain states.
- **Orphan Buffer Sanitation**: Startup routines sweep and purge abandoned temporary files (`*.tmp_*`) left by interrupted dead processes, ensuring clean workspace hygiene.
- **Continuous Fault-Injection Verification**: Automated test suites inject 0-byte truncations, corrupted JSON streams, and lock collisions to guarantee 100% self-healing without application panic.

---

## 🔍 Epistemic Grounding & Anti-Hallucination Invariant
- **Atomic Pre-Mutation Slice Freshness**: All code changes, internal references, and type signatures are verified against real disk files and AST symbols immediately prior to write operations, preventing line-drift and stale-offset edit failures (**PRINCIPLE-003**).
- **Call-Site & Reference Completeness**: Before altering signatures or deleting symbols, all call-sites across the codebase are identified to prevent orphan references and ghost duplicates.
- **Manifest-Backed Dependency Grounding**: Introducing external packages, imports, or CLI tools requires prior verification against project dependency manifests (`pyproject.toml`, `requirements.txt`, `package.json`, etc.) or the language standard library. Zero-dependency environments prohibit third-party imports.
- **Platform & Runtime Parity**: Code and execution scripts adhere strictly to the active operating system and shell environment (`sys.platform`), utilizing cross-platform stdlib abstractions (`pathlib.Path`, `sys.executable`) without assuming Unix-only shell builtins.
- **Bi-Directional Contract Parity**: Cross-layer changes (e.g. backend models vs frontend consumers, database schemas vs repository types) require verifying both sides against the canonical contract before edits.
- **Epistemic Triad & Dual-Track Ambiguity**: Agents pass the 3-point check (Symbol, Dependency, Platform) before Phase 3 coding. Safe, deterministic fallbacks apply to data ambiguity; mandatory stop-and-escalate applies to architectural/intent ambiguity.
- **Strict AST Mechanical Gating**: `scripts/update_knowledge_base.py` strictly parses all Python sources with `ast.parse` and fails immediately with non-zero exit on any syntax error, preventing syntactically invalid code from advancing to Phase 4.

---

## 🧠 Attentional Drift Prevention & State Externalization
- **Disk-Anchored Memory & Living Plan SSOT**: In-flight state, task checkpoints, and architectural rationale are externalized immediately to `.agents/task_ledger.json` and `knowledge/decisions.md`, eliminating dependence on volatile conversational context. Multi-step plans are updated in-place on disk rather than reprinting bloat into conversation history (**PRINCIPLE-004**).
- **Bounded Rolling Ledger Window**: `scripts/disruption_recovery.py` auto-prunes historical checkpoints to maintain a bounded rolling memory window (active task + recent history), preventing the ledger itself from becoming a context bloat trap.
- **Compaction Resumption & Anti-Repetition Invariant**: Upon compaction or cold restart, agents execute a 3-step audit (Ledger `active_phase` check $\rightarrow$ Working tree check $\rightarrow$ Monotonic resumption). Disk state is authoritative over truncated dialogue history; once a choice is recorded, the agent never re-prompts the user to re-decide.
- **AST-First & Slice-Capped Retrieval**: Code examination prioritizes AST symbol maps (`knowledge/codebase_map.md`) and slice views (<100 lines) to preserve token budgets and prevent premature context compaction.
- **Two-Tier Memory Partitioning & Immediate ADR Register**: Strict separation between mutable in-flight scratchpads (`task_ledger.json`) and permanent immutable architectural records (`knowledge/decisions.md`). Negative constraints and architectural invariants are committed immediately to prevent constraint decay across long sessions.
- **Terse Tool Invocation**: Commands use bounded, summary-oriented flags (`git status -s`, `--oneline`, `--stat`, test runner `-q`) to prevent terminal logs from flooding the LLM context.

---

## 🛡️ Automated Regression Shield & Hermetic Testing
- **100% Test Pass Gate & Sub-Second Execution**: All modifications must pass the automated test suite with 100% success in under 1 second total ($T_{\text{suite}} < 1\text{s}$) prior to staging or committing (**PRINCIPLE-014**).
- **Test Sanctity Invariant**: Test assertions represent immutable contractual truth. Regressions must be solved by repairing production logic; modifying assertions, skipping (`@unittest.skip`), or deleting tests to bypass gates is strictly prohibited.
- **Pristine Working Tree & RAII Fixture Reversion**: All filesystem tests run inside isolated temporary sandboxes (`tempfile.TemporaryDirectory()`). Tests modifying global state (`os.environ`, `sys.argv`, singletons) guarantee complete teardown via `addCleanup()`, leaving `git status` bit-for-bit clean with zero leaked artifacts or polluted process state.
- **Observable Contracts Over Mock Echoes (Anti-Tautological Invariant)**: Assert outward observable behavior, return values, state transitions, and exception boundaries rather than internal mock call counts (`assert_called_once`), avoiding meaningless tautological tests.
- **Red-Green Defect Pinning & Negative Path Coverage**: Reproduce bugs with failing tests first (Red) before fixing (Green). Prioritize hostile boundary and negative path coverage (empty inputs, `None`, 0-byte files, extreme numbers, expected exceptions, and formatted diagnostic messages).

---

## 🎮 Operational Dogfooding & Ephemeral Chaos Sandboxing
- **Live System Verification & Headless Parity**: Components are interactively exercised across their native runtime surfaces (UI loops, subshells, HTTP clients) prior to shipping (**PRINCIPLE-015**). Desktop GUIs leverage virtual display buffers (`xvfb`/offscreen) with bounded timeouts ($T \le 10\text{s}$). Web apps assert client-side root container DOM hydration (rendered child elements in `#root`/`#app`) and zero `console.error` logs.
- **Platform-Portable Process Tree Teardown (RAII Cleanup)**: All server processes and child daemons run within managed supervisors or RAII context managers that guarantee recursive child process termination across Windows (`taskkill /F /T /PID`) and POSIX (`os.killpg(pid, signal.SIGKILL)`) on exit or assertion failure, preventing port collisions (`EADDRINUSE`) and zombie background processes.
- **Non-Interactive Stdin Parity & EOF Safety**: Interactive CLI prompts must never hang in subshells; commands must support non-interactive bypass flags (`--yes`/`--headless`) and gracefully handle closed `stdin` streams (`< /dev/null`).
- **Hermetic Ephemeral State & Storage Sandboxing**: All operational state modifications, runtime databases (`sqlite:///:memory:` or ephemeral file DB), and temporary caches execute strictly within an isolated ephemeral directory (`SANDBOX_ROOT`), asserting zero host mutations and bit-for-bit clean `git status --porcelain`.
- **Dual-Track Dogfooding (Golden Path + Hostile Chaos)**: Every dogfood run verifies a complete end-to-end data lifecycle (create, modify, retrieve) paired with intentional fault injection (SIGINT interrupt, invalid payloads, malformed data streams) to verify clean error recovery.
- **Deterministic Domain Exit Contracts**: Verify concrete domain success criteria: zero unhandled tracebacks in stderr, zero browser console errors, valid API schemas, and clean shutdown exit codes.

### Tier 1 Context Budget (Enforced Surface)
Always-injected IDE rules cost context on every turn, so the budget is a gate, not advice.
See [ADR-046](decisions.md).

| Ceiling | Value | Enforcement |
|---|---|---|
| Hard character cap | 8,000 chars | `[BUDGET EXCEEDED]` blocks sync |
| 90% early warning | 7,200 chars | `[BUDGET WARN]` advisory |
| Tier 1 token target | 1,500 est. tokens | `[TOKEN EXCEEDED]` blocks sync |

- **Structural paydown, not semantic**: budget is reclaimed by deleting duplication, never by
  compressing mechanisms. **PRINCIPLE-001** R2 forbids compressing hard constraints, so capsules
  are the worst lever. Removing the per-line `[GUIDELINES.md#principle-0XX]` anchors - redundant
  against the grep contract stated once per header, and prone to silent slug rot - reclaimed
  29-51 chars x 19 lines per target at zero information loss.
- **Flat overhead on expansion**: a simulated 20th principle lands ~20 tokens under the gate, so
  the next addition requires another paydown. That is **PRINCIPLE-001** R9 working as intended.
- **Navigation contract**: with per-line anchors gone, Tier 2 retrieval relies on the
  deterministic grep anchor `### PRINCIPLE-XXX:`; a test asserts it survives in all five targets.

### Invariant Reachability Shield (Implemented Surface)
`scripts/check_reachability.py` enforces **PRINCIPLE-014** Rule 7. See [ADR-044](decisions.md).

| Audit | Catches |
|---|---|
| Call-site reachability | a capability defined, exported and unit-tested but wired into nothing |
| Key round-trip integrity | a reader keyed to a persisted field that no writer produces |

- **Why it exists**: "green test, broken production" was the highest-frequency defect class found
  in this repository - the unused `file_lock()` lost 5 of 7 concurrent checkpoints, and the
  phantom `last_phase_num` key made every resumption report a default phase. Both passed CI.
- **Broad reference collection**: `ast.Name` loads, attributes and `ImportFrom` all count as
  references, because a function stored in a dispatch tuple or passed as a callback is genuinely
  reachable. Under-counting would produce false alarms and erode trust in the gate.
- **Curated allowlist**: `PUBLIC_API_ALLOWLIST` names symbols that are deliberately public API
  rather than internally called; a test asserts no entry outlives its symbol.
- **Zero Tier 1 cost**: implemented as a *rule* under an existing principle, not as
  PRINCIPLE-019, because only invariant capsules are injected into IDE targets. Measured:
  `principles.md` unchanged at ~1,559 tokens.

### Operational Dogfood Runner (Implemented Surface)
`scripts/dogfood.py` makes **PRINCIPLE-015** executable. See [ADR-043](decisions.md).

| Track | What it proves |
|---|---|
| golden lifecycle | create -> modify -> retrieve -> complete through the real ledger CLI, asserted on disk |
| chaos perturbation | malformed flag, missing flag value, corrupted ledger, 0-byte truncation all handled cleanly |
| read-only gates | both `--check` freshness gates run read-only and report truthfully from an unrelated cwd |
| help + startup budget | every entrypoint answers `--help` safely, measured as a real process |
| blast radius | tracked repository content is byte-identical after the run |

- **RAII Process Supervision**: `supervised()` guarantees recursive teardown via `taskkill /F /T`
  on Windows and `killpg(SIGKILL)` on POSIX (`start_new_session=True`), so no spawn is orphaned.
- **Sandbox Jail + Workspace Redirection**: the ledger CLI anchors to the repository, not the cwd,
  so `--workspace <dir>` is what actually keeps writes inside the jail. Without it the first
  dogfood run overwrote the live ledger.
- **Content-Hashed Blast Radius**: `repo_fingerprint()` hashes `git status --porcelain` plus every
  `git ls-files` entry's bytes. Comparing porcelain *text* is blind to content changes in files
  that were already dirty, and that hole let the first run pass while clobbering the ledger.
- **UTF-8 Capture**: every spawn forces `encoding="utf-8"`; the locale codec (cp1254 here) kills
  reader threads on the CLIs' non-ASCII status glyphs and silently returns empty output.

### Two-Tier Test Budget (Implemented Surface)
Tests are partitioned by whether they must spawn a process, with both tiers running under the one
canonical command (`python -m unittest discover tests`). See [ADR-040](decisions.md).

| Tier | Module | Budget | Contents |
|---|---|---|---|
| Unit | `tests/test_kit.py` | **<1s** (strict) | Pure in-process logic: parsing, classification, ledger atomicity, AST fidelity |
| Integration | `tests/test_integration.py` | <5s, timeout per spawn | Multi-process concurrency races, real-binary CLI contracts, real `git` grounding, dogfood matrix |

The unit gate is enforced **structurally**, not by a timing assertion: `TestTierBudgetDiscipline`
fails if `test_kit.py` references `subprocess`, `Popen`, `os.system` or `time.sleep`, which is what
keeps it sub-second by construction. A wall-clock assertion on a 1s budget would be flaky on a
loaded machine, and **PRINCIPLE-014** R3 classifies flaky tests as blocking defects. The companion
check asserts every spawn in the integration tier declares an explicit timeout (**PRINCIPLE-010** R3).

### Ledger Concurrency & Durability (Implemented Surface)
- **Locked Read-Modify-Write**: `locked_ledger()` holds the advisory lock across the whole
  load → mutate → save cycle. All three mutators (`record_checkpoint`, `mark_task_completed`,
  `reset_active_task`) route through it. Previously the lock had zero call sites and parallel
  subagents silently erased each other's checkpoints (**PRINCIPLE-013** R3).
- **Fail-Loud Contention**: lock acquisition failure raises `TimeoutError` carrying the
  What → Why → Fix triad rather than degrading to an unprotected write.
- **Atomic Stale-Lock Steal**: an expired (>30s) lock is broken by `os.replace` rename, so exactly
  one racer can win; a plain `unlink` let two processes both declare themselves the holder.
- **Directory Durability Barrier**: `fsync_dir()` follows every `os.replace`. Fsyncing the file
  alone leaves the *rename* in an unflushed directory entry on POSIX journalling filesystems, so a
  power cut could revert a file that was reported as durably written. No-op on win32.
- **Phase-Accurate Resumption**: `resolve_active_phase()` reads the `active_phase` key that writers
  actually produce, with legacy-key and textual-label fallbacks, and resumption never recommends an
  earlier phase than the one reached (**PRINCIPLE-002** R1).

### Git Status Classification (Implemented Surface)
`classify_git_status()` is pure domain logic, separated from the audit's subprocess I/O so every
porcelain state is deterministically testable. Classification is exhaustive by construction:

| Code | Bucket |
|---|---|
| `??` | untracked |
| `!!` | ignored (skipped) |
| `DD` `AU` `UD` `UA` `DU` `AA` `UU` | **conflicted** (git's closed unmerged set) |
| any other non-blank XY | modified |

The `modified` bucket is the open-ended default precisely so no future git code can be dropped. Note
that `AA` and `DD` are conflicts despite containing no `U`, so a `"U" in xy` test is insufficient.

### Universal CLI Contract (Implemented Surface)
Every entrypoint in `scripts/` implements one uniform contract, enforced mechanically by the
`TestOperationalDogfooding` matrix (see [ADR-039](decisions.md)):

| Invocation | Required behaviour | Exit |
|---|---|---|
| `--help` / `-h` | Usage block to stdout, clean stderr, zero filesystem writes, short-circuits before AST/git work (<100ms) | `0` |
| Unrecognized flag | What → Why → Fix remediation triad to stderr; default action is **never** performed | `2` |
| Normal operation | Action performed; operational failure reported | `0` / `1` |

- **Value-Aware Flag Validation**: Validators (`validate_argv` in `disruption_recovery.py`, `_validate_argv` in
  `update_knowledge_base.py`, inline in `sync_principles.py`) skip the value token of known value-taking flags,
  so free-text values such as `--desc "-n refactor"` are never misread as unknown options.
- **Bounded-Parallel Dogfood Matrix**: The subshell matrix (3 scripts × {golden `--help`, chaos malformed flag})
  executes once in `setUpClass` through a `ThreadPoolExecutor` bounded by `os.cpu_count()` (**PRINCIPLE-010** R3),
  from an ephemeral `dogfood_jail_*` cwd with `stdin=DEVNULL`, asserting a bit-for-bit unchanged
  `git status --porcelain` across the whole matrix. This keeps genuine subshell dogfooding inside the <1s gate.

---

## ⚡ Progressive Rule Disclosure & Governance Frugality
- **Two-Tier Architecture**: Injected IDE prompt instructions are capped (<1,500 tokens) with terse, self-sufficient invariant capsules (Tier 1), while exhaustive guides, edge-case rationale, and failure analysis live in disk-backed knowledge documents (Tier 2) (**PRINCIPLE-001**).
- **Self-Sufficient Invariant Capsules**: Every Tier 1 entry contains the exact technical mechanism (e.g., `flush` + `os.fsync` + `os.replace`, 100% test pass gate, read-before-write symbol check), ensuring routine code generation is 100% accurate with zero disk roundtrips.
- **Autonomous Retrieval Trigger Protocol**: Defines explicit operational triggers where an AI agent must slice-view Tier 2 knowledge:
  1. *Architectural Boundary Trigger*: Introducing new services, data schemas, or cross-module API contracts.
  2. *Failure & Regression Trigger*: Test failures, build breakages, or unhandled exceptions.
  3. *Ambiguity Trigger*: Underspecified domain requirements or missing schema models.
- **Universal vs Domain Rule Partitioning (Adopter Architecture)**:
  - *Tier 1A (Universal AI Governance)*: AIKit's immutable 18 engineering invariants (<1,000 tokens).
  - *Tier 1B (Project Domain Invariants)*: Project-specific ironclad conventions defined in `.agents/rules/domain.md` or dedicated prompt section (<300 tokens: framework version, linting, naming conventions).
  - *Tier 2 (Disk Knowledge & Schemas)*: Project architecture, database schemas, and API specs in `knowledge/`.
- **Deterministic Grep Anchor Contract**: All Tier 2 sections use unique regex-safe headers (`### PRINCIPLE-XXX:`). Pointers instruct agents to locate and slice-view the exact 30-line block via single-call grep (`Query="### PRINCIPLE-XXX:"`), eliminating line-number drift across edits.
- **Context Overhead Guardrails**: `scripts/sync_principles.py` automatically measures and mechanically enforces character/token budgets (<8,000 chars / ~1,500 tokens) across all generated AI rules, preventing instruction bloat.

---

## 📚 Living Documentation & Cold-Start Orientation (The SSOT Triad)
- **30-Second Cold-Start Orientation**: `README.md` serves as the authoritative entrypoint for cold-starting agents, providing unambiguous prerequisites, setup/run commands, test commands, and directory layouts (**PRINCIPLE-005**).
- **Material Surface Sync Contract**: Synchronous updates to `README.md` are gated strictly by modifications to public surface areas (quickstart, CLI flags, public APIs, governance principles). Internal refactors sync to `knowledge/` to prevent documentation churn.
- **Documentation Partitioning (The SSOT Triad)**:
  - `README.md`: Public surface, quickstart, entry points, and high-level architecture.
  - `AGENTS.md` / `GUIDELINES.md`: Behavioral rules, lifecycle invariants, and engineering principles.
  - `knowledge/`: Deep technical domain knowledge, AST codebase maps, schemas, and immutable ADR decision records.
- **Executable Command Parity**: All documented quickstart and run commands must be factual, literal, and verified to run in the active runtime.
- **Directory Tree & Whole-Tree Drift Shield**: Any addition, deletion, or renaming of core scripts or root files requires an atomic update to the `README.md` directory tree, ensuring zero phantom scripts or dead references across the project.
- **Cold-Start Token Ceiling**: `README.md` is strictly bounded (<20,000 characters / ~5,000 tokens) to guarantee that incoming agents orient without blowing out prompt budgets on turn 1.

---

## ⚡ Disruption Recovery & Progress Checkpointing Architecture (PRINCIPLE-006)
- **Zero-Progress-Loss Workflow**: Complex tasks are decomposed into discrete, verified micro-milestones. If electricity or session processes abruptly terminate, progress is preserved up to the last atomic checkpoint.
- **Persistent Task Ledger (WAL)**: `.agents/task_ledger.json` records in-flight tasks, current lifecycle phases (1..5), and completed checkpoints. Bounded rolling pruning (max 20) ensures the ledger remains a lightweight context anchor (<2 KB).
- **First-Class Disruption CLI**: `scripts/disruption_recovery.py` exposes `--audit` (workspace scan), `--resume` (resumption guidance), `--checkpoint` (atomic step recording), `--complete` (task finalization), `--reset` (abandoning in-flight tasks), and `--clean` (purging orphaned `.tmp_*` buffers).
- **Conventional Micro-Commit Standardization**: Micro-milestones committed to git follow standard semantic versioning and Conventional Commits (`type(task): [milestone N/M] description`) with passing test gates.
- **Explicit Micro-Staging Invariant**: Micro-milestone commits stage strictly the files modified for that sub-task (never blind `git add .`), preventing unvetted draft artifacts from contaminating git history.
- **Transient Buffer Hygiene**: Startup audits detect and flag orphaned temporary buffers (`*.tmp_*`) from interrupted writes, maintaining deterministic repository health.

---

## 🎯 Pre-Flight Impact & Quality Gate Architecture (PRINCIPLE-007)
- **Track C Impact Assessment Gate**: Before mutating executable code, schemas, or dependencies on Track C tasks, the AI must evaluate the 4 impact quadrants (Why, Expected Benefits, Blast-Radius Risks, and Mitigation). Track B scales down to a micro-sanity check; Track A is read-only.
- **4 Blast-Radius Dimensions**:
  1. *Contracts & Signatures*: Zero orphaned call-sites, broken CLI flags, or mismatched serialization schemas.
  2. *Dependency Infiltration*: Zero undeclared external packages or non-standard tools.
  3. *Concurrency & Thread Safety*: Non-blocking asynchronous execution without event-loop starvation or thread deadlocks.
  4. *State Mutation & Schema Drift*: Backward-compatible storage schemas and fail-safe atomic mutations.
- **Anti-Satisficing & Type Preservation**: Mechanically prohibits classic LLM shortcuts: no `# TODO` stubs, no silent exception swallowing (`except Exception: pass`), no weakened or deleted test assertions, no demoted UI designs, and no evading type safety via `Any` casting or `# type: ignore` suppressions.
- **Scope Ceiling (Anti-Gold-Plating)**: Modifications must remain strictly bounded to the evaluated user goal and direct mitigations; never introduce speculative unrequested frameworks or unsolicited refactoring.
- **Clean Baseline, Reversibility & Principle 8 Bridge**: Workflows start from a clean baseline (`git status`) with defined atomic rollback paths. Defensive mitigations directly formulate the hierarchical sub-tasks decomposed in `PRINCIPLE-008`.
- **Persistent Ledger Memory & Conversational Conciseness**: Checkpoint flags (`--why`, `--benefits`, `--risks`, `--mitigation`) embed the complete 4-quadrant assessment directly into `.agents/task_ledger.json`, preserving intent and rationale across compactions while keeping conversational chat ultra-terse (<6 lines).

---

## 🌳 Hierarchical Task & Problem Decomposition Architecture (PRINCIPLE-008)
- **Dual-Pillar Framework**:
  - *Pillar A (Engineering Task Workflow)*: Eliminates monolithic execution bias by breaking user goals down into functional domains (Model $\rightarrow$ Service $\rightarrow$ Presentation $\rightarrow$ Test) and atomic leaf units within a bounded milestone horizon ($2 \le M \le 6$).
  - *Pillar B (Data & System Architecture)*: Divides deep file hierarchies, AST structures, or datasets into bounded recursive chunks with strict termination bounds ($D \le 3$, fan-out $K \le 50$) and deterministic base-case summary aggregation.
- **Top-Down Planning, Bottom-Up Execution**:
  - *Top-Down Planning*: Discovers contracts, API boundaries, and dependencies from the user goal downward.
  - *Bottom-Up Execution*: Implements code upward starting from foundational primitives and models, moving to domain services, and finally to presentation/CLI and integration tests. Guarantees every referenced class and import physically exists prior to consumer invocation (`PRINCIPLE-003`).
- **Bounded Milestone Horizon & Indexing Contract ($N/M$)**: Decomposed plans must avoid both monolithic mega-diffs and micro-task proliferation ($2 \le M \le 6$). Leaf units directly define the milestone count ($M$) and index ($N$) logged in `.agents/task_ledger.json` and committed via Conventional Commits: `type(task): [milestone N/M] description` (`PRINCIPLE-006`).
- **Single-Domain Leaf Atomicity & Verifiability**: Each leaf unit targets a single architectural layer, compiles cleanly, and passes isolated tests without breaking repository stability.
- **Dynamic Re-Decomposition Protocol**: When unanticipated blockers or gaps emerge during execution, agents pause forward progression, update the active plan on disk (`task_ledger.json`), adjust $M'$, and resume monotonically without discarding completed progress.

---

## 🧠 AI Knowledge Base & Living External Memory (PRINCIPLE-016)
- **Canonical Modular Structure & Router Sitemap (`INDEX.md`)**: The knowledge base is partitioned into 7 focused documents (`INDEX.md`, `architecture.md`, `services.md`, `data_models.md`, `state_and_ui.md`, `decisions.md`, and `codebase_map.md`). `INDEX.md` serves as the authoritative router sitemap, providing high-density summaries for instant cold-start navigation without blind exploration.
- **Atomic Code-and-Doc Pairing (Anti-Drift Invariant)**: Whenever public service signatures, schemas, or architectural conventions are modified, the matching `knowledge/` documents must be updated in the exact same commit, eliminating silent documentation rot.
- **Monotonic Append-Only ADR Register**: Architectural decisions in `knowledge/decisions.md` are immutable historical records. Past decisions are never deleted or rewritten; design pivots append new sequential ADRs that mark predecessors as superseded.
- **Strict AST Syntax Validation & Freshness Gate**: `scripts/update_knowledge_base.py` parses the codebase AST, generates the symbol catalog `knowledge/codebase_map.md`, and halts on any syntax errors. Automated unit tests enforce that `codebase_map.md` bit-for-bit matches physical code AST prior to delivery.
- **Modular SSOT Partitioning & Versioned Models**: Schemas and DTOs are documented exclusively in `data_models.md` with explicit `schema_version`, nullability defaults, and migration paths; other documents link to `data_models.md` rather than duplicating definitions.
- **Automated Link Integrity Shield**: Mechanically validates that all relative file links cited across `knowledge/INDEX.md` physically exist on disk, preventing broken documentation references.
- **Language-Agnostic Knowledge Layout**: The 7-document architecture represents a universal engineering standard extensible to any polyglot repository (TypeScript, Go, Rust, Python).

---

## 🔄 Living Principles & Cross-IDE Governance Architecture (PRINCIPLE-017)
- **Multi-IDE Target Synchronization**: Principles defined in `AGENTS.md` are automatically compiled and synchronized to all active AI assistant environments (`GEMINI.md`, `.agents/rules/principles.md`, `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`) using atomic buffer replacements (`fsync` + `os.replace`).
- **Canonical Schema & Unique ID Enforcement**: Every principle must strictly declare Title, Concept, Invariant capsule, and numbered Rules; `scripts/sync_principles.py` validates schema completeness and halts on missing sections or duplicate principle IDs.
- **Deterministic Auto-Sync Freshness Gate**: Automated unit tests assert `sync_all(check_only=True) == 0`, preventing any pull request or commit from shipping with stale or desynchronized IDE rule files.
- **Triad Documentation Consistency & Exact Title Parity**: Programmatically verifies that all principle IDs and exact heading titles in `AGENTS.md` match across `GUIDELINES.md` and `README.md`.
- **Dynamic Monotonic Phase Progression**: Tracks lifecycle phases (Phases 1 through 5) dynamically without rigid range bounds, ensuring non-decreasing execution order ($Phase_i \ge Phase_{i-1}$).
- **Tier 1B Domain Rules Blueprint & Proactive Budget Warnings**: Adopter repositories define project-specific conventions in `.agents/rules/domain.md` based on `.agents/rules/domain.md.template` (<1,200 chars / ~300 tokens). `scripts/sync_principles.py` automatically injects this block into all targets and emits proactive warnings if prompt files exceed 90% capacity (>7,200 chars).

---

## 🚀 Automatic Git Workflow & Delivery Architecture (PRINCIPLE-018)
- **Terminal Lifecycle Execution**: Phase 5 git commit and push actions are mechanically locked until Phase 4 verification gates (tests, dogfooding, and freshness checks) pass with 100% success.
- **Explicit Staging Invariant**: Blind staging commands (`git add .`, `git add -A`) are strictly prohibited; target paths must be explicitly enumerated (`git add <file1> <file2>`) to prevent secret exposure or sweeping unrelated OS/test scratch files into git history.
- **Pre-Commit Delivery Triad**: Enforces a 3-point check before terminal commits: (1) 100% unit tests pass, (2) rule targets and codebase map pass freshness checks (`--check`), and (3) clean working tree with zero orphaned temporary buffers.
- **Adaptive Remote Protocol & Zero Force Push**: Automatically inspects active branches and upstream remotes. Commits are pushed adaptively; unconfigured remotes fall back safely to local commits with clear reporting. Rebase pulls (`git pull --rebase`) resolve remote divergence; force pushes (`--force`, `--force-with-lease`) are strictly forbidden.
- **Non-Destructive Recoil**: Automated error recovery must utilize soft rollbacks (`git reset --soft HEAD~1`), preserving working tree changes and strictly banning destructive resets (`git reset --hard`, `git clean -fdx`).
- **Standardized Conventional Commits**: Commit messages follow the Conventional Commits specification (`feat`, `fix`, `refactor`, `docs`, `chore`, `test`, `perf`, `build`, `ci`) with optional milestone indexing (`[milestone N/M]`), validated via pure-stdlib tooling.




