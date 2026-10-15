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

## 💾 Persistence & Atomicity (Fail-Safe Architecture)
- All persistent configuration and state mutations use atomic write patterns (`flush` + `os.fsync` + `os.replace`) to prevent zero-byte truncation during sudden power loss (**PRINCIPLE-013**, **PRINCIPLE-006**).

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

## 🎮 Operational Dogfooding & Ephemeral Chaos Sandboxing
- **Live System Verification**: Components are interactively exercised across their native runtime surfaces (UI loops, subshells, HTTP clients) prior to shipping (**PRINCIPLE-015**).
- **Zero-Blast-Radius Jail**: Dogfood execution occurs inside ephemeral, synthetic sandbox directories to guarantee safety against accidental user data modification.

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

