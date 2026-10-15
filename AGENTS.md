# AI Assistant Guidelines & Project Principles

> **MANDATORY INSTRUCTION FOR ALL AI AGENTS & CODING ASSISTANTS:**
> You must strictly read, respect, and enforce all principles in this document when planning, implementing, reviewing, or refactoring code in this repository.
> The principles are strictly ordered across 5 chronological execution phases: **Meta-Governance & Grounding** $\rightarrow$ **Pre-Flight Orientation & Planning** $\rightarrow$ **Architecture & Lean Implementation** $\rightarrow$ **Operational Verification & Resilience** $\rightarrow$ **Living Sync & Delivery**.

---

## 🏛️ Phase 1: Meta-Governance & Attentional Grounding

### PRINCIPLE-001: Progressive Rule Disclosure & Governance Frugality (Zero Instruction Bloat)
- **Concept**: AI governance systems must never consume excessive context windows or degrade model reasoning through instruction bloat. System-level rule injections must remain ultra-dense and compact (Tier 1), while deep architectural rationale, historical logs, and exhaustive edge cases are offloaded to disk-backed knowledge documents (Tier 2) to be retrieved progressively on demand.
- **Invariant**: Two-tier progressive disclosure (<1,500 tokens Tier 1); self-sufficient invariant capsules with deterministic grep anchors (`### PRINCIPLE-XXX:`); slice-view Tier 2 on architectural boundary, regression, or ambiguity.
- **Rules**:
  1. **Two-Tier Progressive Disclosure**:
     - *Tier 1 (Always-Injected System Instructions)*: IDE rule files (`.cursorrules`, `GEMINI.md`, `CLAUDE.md`, `.github/copilot-instructions.md`) must only contain dense, self-sufficient invariant capsules and essential pointers. Never inject multi-page essays, full code blocks, or raw historical logs into always-on prompt contexts.
     - *Tier 2 (Disk-Backed On-Demand Knowledge)*: Full explanations, deep problem analysis, and implementation guides live on disk (`GUIDELINES.md`, `knowledge/`) and are read selectively via targeted slice tooling (`view_file`, `grep_search`) only when relevant sub-tasks require them.
  2. **Self-Sufficient Invariant Capsules (Anti-Satisficing Invariant)**: Compression must target narrative filler, rationale, and examples—never hard mechanical constraints. Every Tier 1 summary must encode the exact technical mechanism (e.g. `flush` + `os.fsync` + `os.replace`, 100% test pass gate, read-before-write symbol check) so routine tasks succeed with 100% accuracy without requiring disk reads.
  3. **Autonomous Tier 2 Retrieval Trigger Protocol**: The AI agent must proactively slice-view Tier 2 documentation (`GUIDELINES.md` / `knowledge/`) upon encountering any of the following 3 operational triggers:
     - *Architectural Boundary Trigger*: Introducing new services, data schemas, or modifying cross-module API contracts.
     - *Failure & Regression Trigger*: Encountering any test failure, build breakage, or runtime exception.
     - *Ambiguity Trigger*: Addressing underspecified domain requirements or missing schema models.
  4. **Universal vs. Domain Rule Partitioning (Adopter Ready)**: When deploying AIKit to govern external projects, maintain a strict 3-tier boundary:
     - *Tier 1A (Universal AI Governance)*: AIKit's immutable 18 engineering invariants (<1,000 tokens).
     - *Tier 1B (Project Domain Invariants)*: Project-specific ironclad conventions defined in `.agents/rules/domain.md` or dedicated prompt section (<300 tokens: framework version, linting, naming conventions).
     - *Tier 2 (Disk Knowledge & Schemas)*: Project architecture, database schemas, and API specs in `knowledge/`.
  5. **Deterministic Grep Anchor Contract**: All Tier 2 guideline sections must use unique regex-safe headers (`### PRINCIPLE-XXX:`). Pointers must instruct agents to locate and slice-view the exact 30-line block via single-call grep (`Query="### PRINCIPLE-XXX:"`), eliminating line-number drift across edits.
  6. **Strict Injected Context Budget & Automated Gate**: Enforce a strict token budget for always-injected IDE rule files (target <1,500 tokens / <8,000 chars total overhead). `scripts/sync_principles.py` must track, report, and mechanically guard against rule footprint creep.
  7. **High Information Density (Anti-Fluff Invariant)**: Eliminate filler words, decorative prose, and duplicate instructions. Maximize the information-to-token ratio across all guidelines.
  8. **Terse Checklist Execution**: Checklists must be concise and actionable, designed to be verified mentally or in compact ledgers without spamming conversational history with verbose multi-paragraph checklists.
  9. **Zero Context Bloat on Expansion**: When adding new principles or guidelines, existing summaries must be condensed or modularized so total system prompt overhead remains bounded and flat over time.

---

### PRINCIPLE-002: Lifecycle-Aligned Instruction Ordering & Attentional Priming (Cognitive Flow Invariant)
- **Concept**: Prompts, rules, checklists, and documentation must be arranged strictly along the chronological execution lifecycle of an agent's task (Grounding $\rightarrow$ Orientation $\rightarrow$ Architecture $\rightarrow$ Verification $\rightarrow$ Delivery). Instructions must never present late-stage actions (e.g. committing, pushing) before early-stage prerequisites (e.g. symbol verification, pre-flight analysis), eliminating instruction order bias and cognitive phase confusion.
- **Invariant**: Monotonic 5-phase lifecycle execution gate (Phase 4 test pass required before Phase 5 delivery); adaptive task pathing (Query/Doc/Eng); immunity to late-stage user priming.
- **Rules**:
  1. **Monotonic Execution Gating (Lock-Step Integrity)**: All engineering workflows must advance through the 5 lifecycle phases sequentially: Phase 1 (Meta-Governance & Grounding) $\rightarrow$ Phase 2 (Pre-Flight Orientation & Planning) $\rightarrow$ Phase 3 (Architecture & Lean Implementation) $\rightarrow$ Phase 4 (Operational Verification & Resilience) $\rightarrow$ Phase 5 (Living Documentation & Delivery). Phase 5 actions (commit, push, release) are mechanically illegal and locked until Phase 4 verification gates (tests, dogfooding) pass with 100% success.
  2. **Remediation Recoil Protocol (Phase 4 Failure)**: When Phase 4 verification fails (test breakage, build failure, or dogfood crash), monotonic forward progression pauses. The agent must recoil strictly to Phase 3 (for code defects) or Phase 2 (for architectural/assumption defects), fix the root cause, and re-run Phase 4. Modifying test assertions to mask regressions is strictly prohibited (Test Sanctity Invariant).
  3. **Adaptive Lifecycle Pathing & Automatic Escalation**: To keep development zero-friction, task execution adapts across 3 explicit operational tracks:
     - *Track A (Query / Exploration)*: Questions, code explanations, or searches $\rightarrow$ Phase 1 (Grounding) $\rightarrow$ Direct Output (Phases 2–5 bypassed).
     - *Track B (Trivial / Documentation)*: Typo fixes, markdown tweaks, or comment updates $\rightarrow$ Phase 1 $\rightarrow$ Phase 3 (Edit) $\rightarrow$ Phase 5 (Sync & Commit), with Phase 4 scaled to syntax/budget check.
     - *Track C (Engineering / Feature / Refactor)*: Complete 5-phase sequence with mandatory impact gates, regression tests, and living sync.
     - *Automatic Track Escalation*: If any Track A or Track B task mutates executable code, data schemas, or dependency configs, it must instantly escalate to Track C, unlocking mandatory Phase 2 impact planning and Phase 4 regression gates.
  4. **Compaction Phase Resumption**: In multi-turn sessions, the active phase number (1 through 5) must be recorded in working memory (`.agents/task_ledger.json`). Upon conversation compaction or cold restart, the agent must orient against the ledger to resume execution at the exact interrupted phase rather than losing state.
  5. **Immunity to Late-Stage User Priming**: When users issue urgent late-stage commands (e.g. *"commit right now"*, *"push immediately"*, *"skip tests"*), the AI must remain anchored to the lifecycle gate. Terminal delivery actions cannot be executed until required verification gates pass.
  6. **Primacy-Weighted Anchoring**: Epistemic grounding, context budget limits, and safety invariants must occupy the top of prompts (primacy zone) where transformer attention is sharpest. Terminal delivery gates must reside strictly at the end.
  7. **Continuous Sequence Audit**: Auto-sync tooling and automated tests must mechanically verify that all 18 principles are partitioned across the 5 lifecycle phases in strictly monotonic sequence without phase inversions.

---

### PRINCIPLE-003: Empirical Grounding & Anti-Hallucination Invariant (Verify-Before-Execution)
- **Concept**: Never make architectural assumptions, guess function signatures, invent phantom dependencies, or extrapolate ambiguous data models without first reading and verifying factual source code, schemas, and runtime state on disk.
- **Invariant**: Read-before-write slice freshness & call-site check; manifest dependency grounding; platform parity; dual-track ambiguity protocol; strict AST syntax gate.
- **Rules**:
  1. **Read-Before-Write & Target Slice Freshness**: Never edit a file, call an internal function, or instantiate a class without first reading or grepping its definition and signature from the local codebase. When performing multi-turn or multi-file edits, re-verify the target slice immediately prior to mutation to eliminate line-drift and stale-offset failures.
  2. **Call-Site & Reference Completeness**: Before modifying signatures, renaming, or deleting any function, class, or configuration key, grep for all call-sites and references across the codebase to ensure complete refactoring with zero orphaned symbols or duplicate ghost implementations.
  3. **Manifest-Backed Dependency Grounding**: Never introduce a third-party package, module import, or external CLI tool without first verifying that it is declared in the project's dependency manifest (`pyproject.toml`, `requirements.txt`, `package.json`, `Cargo.toml`) or is part of the language standard library. In zero-dependency repositories, external imports are strictly prohibited.
  4. **Platform & Runtime Parity**: Never assume OS-specific shell builtins, path separators, or binary aliases (`python3` vs `py`, `bash` vs `powershell`) without checking the active runtime (`sys.platform`). Use portable standard-library APIs (`pathlib.Path`, `subprocess.run([sys.executable, ...])`) and shell-agnostic commands.
  5. **Bi-Directional Contract Parity**: When modifying data schemas, API contracts, or serialization models, the AI must verify both producer and consumer interfaces across system boundaries before proposing code changes.
  6. **Dual-Track Ambiguity Protocol & Epistemic Triad**:
     - *Epistemic Triad Gate*: Before starting Phase 3 implementation, pass the 3-point check: (1) Symbol Reality (verified exact definition & call-sites), (2) Dependency Reality (declared in manifest or stdlib), and (3) Platform Reality (valid for active OS/shell).
     - *Data/Runtime Ambiguity*: Apply safe, deterministic, non-destructive fallbacks with explicit warning logs.
     - *Architectural/Intent Ambiguity*: Never guess business logic or execute destructive actions under ambiguity. Halt forward progression and escalate to the user with structured, concise options.
  7. **Strict AST & Syntax Gating**: Rely on deterministic verification tools (`scripts/update_knowledge_base.py`, AST parsers, compiler dry-runs, and unit tests) to mechanically validate syntax and symbol integrity. `scripts/update_knowledge_base.py` enforces strict AST validation and halts on any syntax error before advancing to Phase 4.



---

### PRINCIPLE-004: Attentional Drift Prevention & Compaction Resilience (Context Anchor Protocol)
- **Concept**: Complex, long-running agent workflows must actively counteract attentional drift, context exhaustion, and compaction amnesia through externalized working memory, living plan SSOT hygiene, disciplined AST-first retrieval, and persistent disk-anchored state.
- **Invariant**: Disk-backed working memory (`.agents/task_ledger.json`); living plan SSOT; anti-repetition on compaction; AST-first slice retrieval; bounded rolling ledger.
- **Rules**:
  1. **Externalized Working Memory & Living Plan SSOT**: Never store task status, multi-step plans, or architectural decisions solely in transient conversational turns. Persist them immediately to structured artifacts (`.agents/task_ledger.json`, `knowledge/decisions.md`). Never reprint verbose multi-step plans across conversational turns; update the plan in-place on disk and keep chat updates terse (<15 lines). Maintain a bounded rolling ledger window via `scripts/disruption_recovery.py` to prevent working memory bloat.
  2. **Compaction Resumption & Anti-Repetition Invariant**: Upon cold restart or conversation compaction, execute a 3-step self-orientation before taking action:
     - *Step 1 (Ledger Audit)*: Inspect `.agents/task_ledger.json` for `active_task`, `active_phase` (1..5), and completed checkpoints.
     - *Step 2 (Working Tree Audit)*: Inspect `git status` and `git log -n 1` to establish factual physical ground truth.
     - *Step 3 (Monotonic Resumption & Anti-Repetition)*: Resume execution directly at the interrupted phase without re-asking resolved user questions or re-executing verified steps. Disk state is authoritative over truncated dialogue history; once a choice is recorded in an ADR or ledger, it is finalized and must never be re-prompted.
  3. **AST-First & Slice-Capped Retrieval**: When exploring code, consult AST symbol catalogs (`knowledge/codebase_map.md`) or targeted symbol greps before opening raw files. When reading source code, use targeted line slices (`StartLine`/`EndLine` <100 lines) focused on the relevant symbol, preventing context window exhaustion.
  4. **Two-Tier Memory Partitioning & Immediate ADR Persistence**: Maintain strict separation between (1) mutable in-flight execution scratchpads (`.agents/task_ledger.json`) and (2) permanent immutable architectural records (`knowledge/decisions.md`). Persist all architectural choices, user constraints (e.g. zero-dependency rules, library bans), and data schemas immediately to `knowledge/decisions.md` as structured ADRs. Treat the decision register as immutable disk ground truth across long sessions.
  5. **Terse Tool Invocation & Attentional Re-Anchoring**: When executing CLI commands, prefer bounded, summary-oriented flags (`git status --short`, `git log -n 1 --oneline`, `git diff --stat`, test runner `-q`). Never dump unbounded mega-logs or full file diffs into conversational turns. At the beginning of each turn, re-anchor to the Pre-flight/Post-flight checklist and active phase invariants.



---

## 🧭 Phase 2: Pre-Flight Orientation & Planning

### PRINCIPLE-005: AI Cold-Start Readiness & Living Documentation (README Sync)
- **Concept**: The repository must be permanently prepared for a "cold start" by any AI assistant or developer. Any new agent entering the project with zero prior conversational history must immediately understand the project state, run commands, architecture, and principles within a single turn. To prevent knowledge drift, public surface documentation must be systematically synchronized.
- **Invariant**: Self-describing repo; 30s cold-start orientation (<20k chars); material surface README sync; executable command parity; whole-tree drift shield.
- **Rules**:
  1. **Self-Describing Repository, 30-Second Orientation & Token Ceiling**: The project must maintain an explicit, high-visibility orientation block in `README.md` documenting: (1) runtime prerequisites, (2) zero-ambiguity setup/run commands, (3) the canonical test command, and (4) the directory tree and primary entry points. A cold-starting agent must achieve complete operational orientation in its first turn without speculative file browsing. To prevent first-turn context exhaustion, `README.md` must stay strictly under 20,000 characters (<5,000 tokens), delegating deep architectural details to `knowledge/`.
  2. **Material Surface Sync Contract**: A synchronous update to `README.md` is mandatory whenever a change alters:
     - Setup, build, or run instructions,
     - CLI flags, environment variables, or public API/UI surfaces,
     - Architectural boundaries, core directory layouts, or governance principles.
     Internal non-breaking refactors that preserve public surfaces update `knowledge/` rather than adding churn to `README.md`.
  3. **Executable Command Parity**: Every command, script invocation, or code snippet documented in `README.md` must be factual, literal, and verified to run successfully in the active runtime environment. Zero phantom commands or broken quickstarts.
  4. **Documentation Partitioning (The SSOT Triad)**:
     - `README.md`: Public surface, quickstart, entry points, and high-level architecture.
     - `AGENTS.md` / `GUIDELINES.md`: Behavioral rules, lifecycle invariants, and engineering principles.
     - `knowledge/`: Deep technical domain knowledge, AST codebase maps, schemas, and immutable ADR decision records.
  5. **Whole-Tree Drift Shield & Script Parity**: Whenever top-level files or core entrypoint scripts (e.g. in `scripts/`, `knowledge/`, or repository root) are added, removed, or renamed, the directory tree in `README.md` must be synchronously updated. Every relative path and script cited in the `README.md` directory tree must physically exist on disk (zero phantom scripts or dead file citations).


---

### PRINCIPLE-006: Incremental Progress Checkpointing & Disruption Recovery (Zero-Progress-Loss Workflow)
- **Concept**: Development workflows and AI execution sessions must be resilient against abrupt disruptions—such as sudden power outages, battery depletion, OS crashes, or process termination. Progress must never be treated as an all-or-nothing end-of-turn artifact; it must be recorded through incremental, atomic micro-checkpoints, persistent task ledgers, and immediate cold-start recovery protocols to guarantee zero work loss without compromising code quality.
- **Invariant**: Incremental atomic micro-commits; pre-flight disruption audit; disruption recovery CLI & ledger (scripts/disruption_recovery.py); explicit micro-staging.
- **Rules**:
  1. **Micro-Milestone Atomicity & Conventional Micro-Commits**: For multi-step tasks or non-trivial implementations, the AI must checkpoint and commit working state incrementally after each logical, verified sub-task (e.g. service logic $\rightarrow$ verified commit; UI component $\rightarrow$ verified commit; docs/tests $\rightarrow$ verified commit) rather than accumulating large, vulnerable working-tree states that risk total loss upon power cut. Micro-commits must follow Conventional Commits with milestone indices: `type(task): [milestone N/M] description`.
  2. **Pre-flight Disruption Audit on Cold Start**: Upon every cold start or conversation resumption, before beginning any new coding task, the AI must immediately audit the working tree (`git status`, uncommitted changes, untracked files, temp artifacts) via `scripts/disruption_recovery.py --audit` or `--resume` to detect, preserve, and recover any uncommitted progress interrupted by an unclean shutdown.
  3. **Atomic File Write Integrity**: All script, source, and guideline modifications must be written atomically to disk via temporary buffers and atomic replacements (`os.replace`), ensuring that an abrupt power cut during a write operation never leaves 0-byte or corrupted source files.
  4. **Non-Breaking Micro-Checkpoints (Test Sanctity Gate)**: Every incremental commit must leave the repository in a stable, syntactically valid state with passing unit tests (`PRINCIPLE-014`). Never commit broken, non-compiling, or failing code to git; if intermediate progress is non-passing, buffer it in `.agents/task_ledger.json` rather than committing broken states.
  5. **Disruption Ledger, Resumption & Reset Protocol**: Interrupted tasks, ongoing refactors, and multi-step plans must be persisted to `.agents/task_ledger.json` via `scripts/disruption_recovery.py --checkpoint <task_id> --phase <phase> --desc <desc>`. Incoming agents execute `scripts/disruption_recovery.py --resume` to inspect surviving files and cleanly resume at the interrupted phase with zero duplicate effort. Abandoned or superseded tasks must be cleanly cleared via `scripts/disruption_recovery.py --reset [reason]`.
  6. **Explicit Staging & Transient Buffer Hygiene**: When committing micro-milestones, explicitly stage only the files modified for that specific sub-task (never execute blind `git add .`). Orphaned temporary buffers (`*.tmp_*`) left behind by interrupted writes must be purged via `scripts/disruption_recovery.py --clean` to maintain clean workspace hygiene.

---

### PRINCIPLE-007: Pre-flight Impact & Quality Checklist (Cold-Start Gate)
- **Concept**: Before implementing code modifications, refactorings, or architecture changes—especially upon a cold start—the AI must evaluate a structured pre-flight impact checklist. This assessment ensures the AI clarifies the *why*, maximizes project *benefits*, preemptively neutralizes concrete *blast-radius risks*, bounds execution within an anti-gold-plating *scope ceiling*, strictly enforces *quality non-diminution*, and preserves assessment memory across interruptions.
- **Invariant**: Track C impact gate (evaluate why, benefits, 4 blast-radius dimensions, anti-satisficing, scope ceiling, clean reversibility) before non-trivial edits.
- **Rules**:
  1. **Adaptive Lifecycle Trigger (Track C Gate)**: The full 4-quadrant impact assessment is mandatory for **Track C (Engineering/Feature/Refactor)** tasks before mutating code or schemas. For Track B (Trivial/Doc), scale to a micro-sanity check (zero syntax/link breakage). Track A (Query/Exploration) bypasses this gate.
  2. **The 4 Blast-Radius Dimensions**: When evaluating *"How could this harm the project?"*, the AI must explicitly assess:
     - *Contract & Signature Breakage*: Call-site ripple effects on public APIs, CLI flags, method signatures, or data serialization schemas.
     - *Dependency Infiltration*: Accidental introduction of undeclared third-party packages, external runtime binaries, or version mismatches (`PRINCIPLE-003`).
     - *Concurrency & Thread Safety*: Synchronous blocking I/O, event-loop starvation, thread deadlocks, or UI freezing (`PRINCIPLE-010`).
     - *State Mutation & Schema Drift*: Modifying file formats or storage schemas without backward compatibility, migrations, or atomicity (`PRINCIPLE-013`).
  3. **Anti-Satisficing, Type Preservation & Zero Lazy Code**:
     - Principles, token frugality, or checklists must **never** be used as an excuse to deliver substandard, stubbed, or crippled implementations.
     - *Forbidden Shortcuts*: Never leave `# TODO`, `// implement later`, `pass`, or mock placeholders in production code paths. Never silently swallow exceptions (`except Exception: pass`). Never weaken, skip, or delete unit test assertions to force tests to pass (`PRINCIPLE-014`). Never demote polished UI to bare wireframes. Never evade type safety by casting variables to `Any` or disabling linters with `# type: ignore` to bypass compiler errors.
  4. **Scope Ceiling (Anti-Gold-Plating Invariant)**: Modifications must remain strictly bounded to the evaluated user goal and its direct blast-radius mitigations. Never introduce speculative abstractions, unrequested architectural overhauls, or unsolicited feature expansions beyond the evaluated scope.
  5. **Reversibility, Recoil Preparedness & Principle 8 Bridge**: Before starting non-trivial mutations, verify a clean working baseline (`git status`) with an atomic rollback path if verification gates fail. The defensive mitigations identified in this gate directly define the hierarchical micro-milestones decomposed in `PRINCIPLE-008`.
  6. **Persistent Assessment Memory & Conversational Conciseness**: Keep chat articulation ultra-terse (<6 lines: 1 compact bullet per quadrant). Record the full pre-flight impact assessment in the task ledger via `scripts/disruption_recovery.py --checkpoint <task_id> --phase 2 --desc <desc> --why <why> --benefits <benefits> --risks <risks> --mitigation <mitigation>` so intent and rationale survive conversation compaction and disruption recovery.

---

### PRINCIPLE-008: Hierarchical Problem & Task Decomposition
- **Concept**: Complex systems, deep directory hierarchies, and non-trivial engineering tasks must be partitioned hierarchically rather than processed via monolithic single-pass operations or micro-task over-fragmentation. Planning proceeds top-down from root goals to atomic leaf units within a bounded milestone horizon, while execution proceeds bottom-up from foundations to consumers, with each leaf milestone independently verified.
- **Invariant**: Hierarchical decomposition (Goal -> Domain -> Leaf Unit); top-down plan, bottom-up execution; bounded milestones ($2 \le M \le 6$); independent leaf verifiability ($N/M$).
- **Rules**:
  1. **Dual-Pillar Framework**:
     - *Pillar A (Engineering Task Workflow)*: Decompose non-trivial features into structured tiers: Root Goal $\rightarrow$ Functional Domains (Model / Service / Presentation / Test) $\rightarrow$ Atomic Leaf Units.
     - *Pillar B (Data & System Architecture)*: Divide-and-conquer deep trees, AST structures, or large datasets into bounded sub-graphs with strict recursion limits (max depth $D \le 3$, max fan-out batch $K \le 50$) and deterministic base-case summary aggregation.
  2. **Top-Down Decomposition, Bottom-Up Execution**:
     - *Planning (Top-Down)*: Deconstruct high-level user requirements downward into contracts, dependencies, and interfaces.
     - *Implementation (Bottom-Up)*: Implement upward from foundational primitives and data models first, domain service logic second, presentation/CLI interfaces third, and end-to-end integration tests last. This guarantees every referenced class, method, and import physically exists prior to consumer invocation (`PRINCIPLE-003`).
  3. **Bounded Milestone Horizon & Indexing Contract**:
     - Decomposed plans must avoid both monolithic mega-diffs and micro-task proliferation. Target a bounded milestone horizon ($2 \le M \le 6$ cohesive milestones). If $M > 6$, decompose into multiple distinct user features.
     - The leaf sequence directly defines the milestone indices ($N=1..M$) recorded in `.agents/task_ledger.json` and committed via Conventional Commits: `type(task): [milestone N/M] description` (`PRINCIPLE-006`).
  4. **Single-Domain Leaf Atomicity & Independent Verifiability**: Every leaf unit must focus on a single architectural domain (e.g. model + unit test), be independently testable, and compile cleanly without leaving the repository in a broken intermediate state.
  5. **Dynamic Re-Decomposition on Discovery**: When in-flight execution uncovers an unanticipated blocker, dependency gap, or schema conflict, pause forward progression, update the active task ledger (`.agents/task_ledger.json`) with refined sub-tasks, adjust $M'$, and resume monotonically without discarding completed milestones.
  6. **State & Context Propagation**: Child sub-agent or recursive tasks must receive scoped context from parent contracts and return structured, verified artifacts back to the parent task ledger.

---

## 🏗️ Phase 3: Architecture & Lean Implementation

### PRINCIPLE-009: Modularity & Pluggable Architecture
- **Concept**: Systems must follow a decoupled, 4-layer architecture adhering to the Single Responsibility Principle, narrow role protocols, open-closed provider registries, zero-config dependency injection, and unidirectional data flow. Presentation, domain logic, and infrastructure adapters must never bleed across layer boundaries.
- **Invariant**: 4-layer architecture (Presentation -> Service -> Domain <- Adapter); role protocols & registry; zero-config constructor DI; immutable DTOs.
- **Rules**:
  1. **Canonical 4-Layer Architecture & Scalable Layering**:
     - *Presentation Layer*: CLI, GUI, or API endpoints. Pure input validation, parsing, routing, and rendering. Never contains business logic, SQL/queries, or raw file I/O.
     - *Service Layer*: Orchestrates domain use cases, coordinates workflows, and manages transactions. Communicates with presentation via immutable data transfer objects.
     - *Domain / Model Layer*: Pure business entities, schemas, algorithms, and core invariants. Completely independent of frameworks, databases, or UI.
     - *Infrastructure / Adapter Layer*: Implements abstract interfaces for filesystem I/O, external network APIs, databases, and third-party tools.
     - *Scalable Layering (Anti-Boilerplate Invariant)*: The 4 layers represent logical boundaries. For small utilities or micro-modules (<300 lines), layers may be co-located as distinct classes/functions within a single module (e.g. `CliParser`, `WorkflowService`, `DataSchema`, `DiskAdapter`) without generating multi-directory folder bloat. Multi-directory packages are reserved for larger systems ($>300$ lines or multiple backends).
     - *Anti-Junk-Drawer Invariant*: Generic catch-all `utils.py` or `helpers.js` junk drawers are prohibited. Helper functions belong to the domain module that owns them or to focused, single-purpose utilities (`date_utils.py`, `string_parsers.py`).
  2. **Interface Segregation & Narrow Role Protocols (Anti-Fat-Interface)**: Pluggable provider/adapter boundaries must declare fine-grained, role-oriented contracts using language-native typing constructs (`abc.ABC` or `typing.Protocol`). Interfaces must never force an adapter or test mock to implement unused methods ($1 \le \text{methods} \le 5$). Concrete adapters must fulfill 100% of the declared contract without stubbing dummy methods.
  3. **Pluggable Registry & Open-Closed Extensibility (OCP)**: Pluggable backends, AI providers, and storage engines must register dynamically via lightweight registries or factories (`@register_adapter("name")` or dictionary lookups) rather than fragile hardcoded `if/elif` branching in service logic. New adapters are plugged in with zero modifications to existing domain orchestration.
  4. **Pure-Stdlib Dependency Injection & Zero-Config Usability**: Domain services must receive infrastructure adapters via constructor (`__init__`) or factory injection. To maintain one-click zero-install usability (`PRINCIPLE-011`) with zero third-party DI containers, provide default-argument factory fallbacks (`def __init__(self, adapter: StorageAdapter | None = None): self._adapter = adapter or DefaultStorageAdapter()`). This guarantees instant zero-config usability out of the box while enabling 100% in-memory mock injection for isolated unit testing (`PRINCIPLE-014`).
  5. **Unidirectional Flow & Immutable Data Transfer Objects (DTOs)**: Dependencies must flow strictly inward: Presentation $\rightarrow$ Service $\rightarrow$ Domain $\leftarrow$ Infrastructure. Circular imports are banned. Data crossing layer boundaries must use immutable DTOs (`dataclass(frozen=True)` or `NamedTuple`), preventing state leakage and side-effect mutations across system boundaries. Modules interact exclusively through declared public contracts with zero external mutation of `_private` attributes.

---

### PRINCIPLE-010: Performance & Resource Optimization (Speed & Lean Architecture)
- **Concept**: Systems must be architected for computational efficiency, sub-second latency, deterministic resource reclamation, non-blocking I/O, and lean dependency footprints. Code must maximize runtime performance while maintaining clean modularity and zero memory leaks.
- **Invariant**: Algorithmic stream efficiency ($O(1)$ memory); non-blocking event-loop hygiene; bounded subprocess timeouts; write-coalescing batch I/O; lazy imports (<100ms startup); sub-second test gate (<1s).
- **Rules**:
  1. **Algorithmic Stream Processing ($O(1)$ Auxiliary Memory)**: Scanning, filtering, and data transformations must use $O(1)$ set/dict lookups rather than $O(N)$ linear scans. Unbounded files, directories, and data streams must be processed via iterator pipelines and generators (`yield`) rather than buffering entire payloads into memory with `.read()`.
  2. **Non-Blocking Event Loops & Measurement-Driven Concurrency**: Heavy synchronous operations (filesystem I/O, subprocess execution, database queries, network calls) must never execute directly on asynchronous event loops or GUI main threads; offload to `asyncio.to_thread()` or background worker thread pools with explicit synchronization locks (`threading.Lock`). Never introduce multithreading or multiprocessing for tasks whose single-threaded baseline completes in under 20ms; reserve concurrency for genuinely I/O-bound or heavy CPU operations ($>200\text{ms}$).
  3. **Subprocess Timeout Gate & Bounded Concurrency**: All external process invocations (`subprocess.run`) must specify explicit timeouts (`timeout=30`), preventing hung child processes from freezing the application. Parallel subprocess execution must be bounded by a worker pool or semaphore ($K \le \text{os.cpu\_count()}$), preventing process table (PID) exhaustion and OS thrashing.
  4. **Deterministic Resource Reclamation & Daemon Ring Buffers (RAII)**: All operating system resources (file descriptors, sockets, database handles, subprocesses) must be deterministically managed using context managers (`with` statements) or explicit `try...finally` teardown. Long-running daemons, file watchers, and session monitors must use bounded ring buffers (`collections.deque(maxlen=N)`) or bounded caches (`maxsize=N`) to maintain constant $O(1)$ memory consumption indefinitely.
  5. **Batch I/O Coalescing & Cold Startup Budget (<100ms)**: High-frequency disk mutations must be coalesced in memory and committed in a single atomic transaction/batch rather than invoking costly disk syncs (`os.fsync`) in tight loops. CLI entrypoints must maintain a strict startup budget (<100ms to `--help`), keeping top-level imports restricted to lightweight standard libraries (`sys`, `os`, `argparse`, `pathlib`) and deferring heavy module loading until after argument dispatch.
  6. **Sub-Second Test Performance Gate (<1s)**: Automated unit tests must be architected for extreme execution speed, executing in memory or against ephemeral isolated fixtures without artificial sleep delays (`time.sleep()`), ensuring the full test suite runs in under 1 second (`PRINCIPLE-014`).
  7. **Clean Optimization (Anti-Cleverness Invariant)**: Performance optimizations must never compromise code clarity, type safety, modularity (`PRINCIPLE-009`), or correctness. Micro-optimizations that degrade readability without measurable profiling justification are strictly prohibited.

---

### PRINCIPLE-011: Zero-Friction Onboarding & Instant Usability (One-Click Start)
- **Concept**: The repository and applications must be instantly runnable and testable out of the box ("one-click and start") immediately upon clone, with zero mandatory package installations, zero config boilerplate, auto-bootstrapping workspaces, and resilient fallbacks.
- **Invariant**: Pure-stdlib clone-and-run; self-bootstrapping workspace; mode transparency; non-interactive headless parity; deterministic exit codes; remediation triad.
- **Rules**:
  1. **Pure-Stdlib Clone-and-Run Baseline**: The core application, CLI entrypoints, and regression test suites must execute cleanly immediately after `git clone` using language standard-library primitives alone. Third-party packages must be strictly optional adapters or plugins (`PRINCIPLE-009`, `PRINCIPLE-010`) that degrade gracefully when uninstalled.
  2. **Self-Bootstrapping Workspace & Zero-Prompt Auto-Init**: Applications must automatically bootstrap required runtime directories (`.agents/`, `data/`, `logs/`) and initialize default configuration states on first launch if absent. First-run routines select sensible, secure defaults automatically without prompting console questions; interactive configuration wizards must be strictly opt-in (`--interactive` or `-i`).
  3. **Zero-Crash Config Protocol & Explicit Mode Transparency**: Never access environment variables or configuration dicts via raw indexing (`os.environ['KEY']`). Always use safe lookups (`os.getenv('KEY')`) with sensible defaults, offline dry-run modes, or mock provider fallbacks. Operating under a fallback must be explicitly signposted (`[INFO] Running in OFFLINE MOCK MODE. Output is simulated.`). Mutating operations requiring external credentials must fail-fast with diagnostic guidance rather than silently simulating fake success or dumping unhandled `KeyError` tracebacks.
  4. **Cross-Platform Polyglot Command & Path Parity**: Quickstart commands, scripts, and documentation must execute identically across Windows, macOS, and Linux. Prefer portable standard-library invocations (`python -m <module>` or `sys.executable`) over platform-specific shell builtins (`export`, `./run.sh`). All file path logic must strictly use `pathlib.Path` or `os.path` abstractions, banning hardcoded `/` or `\\` path separators.
  5. **Non-Interactive Headless Parity & Deterministic Exit Codes**: Commands must default to non-interactive execution when running in automated AI subagent contexts, IDE extensions, or CI/CD pipelines (`not sys.stdin.isatty()`). Provide explicit non-interactive flags (`--yes`, `--batch`) and never hang indefinitely waiting on terminal stdin. Applications must strictly adhere to standard exit code semantics: `0` (clean success), `1` (operational failure), and `2` (CLI argument misuse or invalid syntax).
  6. **Actionable Remediation Triad (Anti-Cryptic Error Invariant)**: User-facing error messages must adhere to the 3-part Remediation Triad: (1) **What happened** (concise failure summary), (2) **Why it happened** (underlying root cause), and (3) **How to fix it** (exact, copy-pasteable command or remediation step). Never dump raw, unhandled exception stack traces to end users.
  7. **Idempotent Health Diagnostics & Self-Demonstrating Fixtures**: Applications must provide an idempotent pre-flight health diagnostic command (e.g. `--audit` or `--doctor`) to verify runtime version parity, platform permissions, tool paths, and ledger state. Systems should embed minimal self-demonstrating fixtures or demo commands (`--demo`) enabling incoming users or agents to experience verified functionality in under 10 seconds without external data dependencies.

---

### PRINCIPLE-012: Token Frugality & Lean Code Architecture (Context Budgeting)
- **Concept**: Systems, prompt pipelines, and autonomous agent loops must be architected for extreme token efficiency, prompt cache optimization, bounded context payloads, rate-limit resilience, and lean, expressive code. Every token ingested by or generated from an LLM must deliver maximum informational leverage.
- **Invariant**: Prompt cache prefix alignment (>=80% cache hits); bounded tool outputs & unified diffs; terse schema generation; token budget circuit breakers; lean syntactic density.
- **Rules**:
  1. **Bounded Prompt Payload Ceilings & AST Slicing**: Dynamic context payloads injected into prompts must enforce explicit ceilings (target <4,000 tokens / <16,000 characters per outbound payload). Utilize AST codebase symbol catalogs (`knowledge/codebase_map.md`), summary digests, and targeted line slices (`PRINCIPLE-004`) rather than raw, unbounded multi-file source dumps.
  2. **Prompt Cache Alignment & Deterministic Prefix Partitioning (Cache-Friendly Invariant)**: Structurally partition prompt payloads into a **Deterministic Frozen Prefix** (static system instructions, invariant rules, tool definitions, output schemas $\ge 1,024$ tokens) and a **Volatile Dynamic Tail** (timestamps, task ledger states, user prompts). Never inject fluctuating timestamps, session GUIDs, or volatile state into prompt headers, guaranteeing $\ge 80\%$ prompt cache hit rates across multi-turn sessions.
  3. **Tool Output Frugality & Bounded Diff Slicing (Anti-Mega-Log Invariant)**: Tool responses appended to conversational context must be bounded and sifted. Unified diffs must be scoped strictly to changed hunks with $\le 3$ lines of surrounding context; test runners and linters must default to summary/quiet modes; search/grep outputs must be capped ($\le 50$ matches or top-k relevant symbols). Never spew hundreds of lines of unchanged source code or raw stack traces into context.
  4. **Output Token Frugality & Schema-Constrained Generation**: Minimize high-cost generation tokens through strict schema-constrained outputs. In automated machine orchestration, models must return compact, typed data contracts (JSON Schema / dataclasses) rather than conversational prose. Conversational progress updates must remain terse (<15 lines), avoiding polite echoing or redundant restatements of code.
  5. **Compact Schema & Relative-Path Serialization (~70% Token Savings)**: All prompt payloads, tool inputs/outputs, and persistent ledgers must serialize repository-relative paths (`scripts/disruption_recovery.py`) rather than absolute filesystem paths. Employ concise, non-redundant key names and compact serialization structures (tabular markdown, JSON Lines, or key-value pairs).
  6. **Token-Aware Rate Pacing & Runaway Circuit Breakers (Anti-Death-Spiral Invariant)**: Batch LLM requests must track token consumption against TPM/RPM limits, implementing full-jitter exponential backoff on HTTP 429 throttling. Autonomous loops and background subagents must enforce explicit token and step ceilings ($K$ turns); if the budget is breached, execution must trip a circuit breaker, checkpoint state to `.agents/task_ledger.json`, and pause cleanly for user confirmation.
  7. **Lean Syntactic Density & Anti-Premature-Abstraction (Codebase Token Hygiene)**: Code written by AI assistants must maximize syntactic density and readability using standard-library primitives (`dataclasses`, `pathlib`, `itertools`, `collections`). Prohibit ceremonial enterprise boilerplate, excessive class hierarchies, and redundant wrapper layers that permanently inflate codebase token overhead for downstream AI agents.

---

## 🛡️ Phase 4: Operational Verification & Resilience

### PRINCIPLE-013: Crash Resilience, State Atomicity & Power-Loss Recovery (Fail-Safe Operations)
- **Concept**: The application, agent frameworks, and persistent data layers must remain fail-safe and self-healing against abrupt disruptions—such as sudden power outages, battery exhaustion, OS crashes, storage exhaustion (`ENOSPC`), process termination, or concurrent process contention. User data, application settings, and state transaction logs must never be left corrupted, half-written, or in split-brain states.
- **Invariant**: Resilient atomic writes (flush + fsync + retry replace); advisory locking; shadow backups (.bak); schema migration; signal-drain flush; read-only fallback.
- **Rules**:
  1. **Atomic Persistence & Lock-Contention Retry Loop**: All persistent JSON state, configuration, and cache files must be written via atomic temporary buffers with explicit flushing (`flush` + `os.fsync`) followed by atomic replacement (`os.replace`). On Windows and virtualized filesystems where concurrent readers (antivirus, indexers, watchers) hold shared locks, `os.replace` must execute a bounded retry loop ($3 \le \text{retries} \le 5$ with exponential backoff) rather than failing abruptly with `WinError 32 / PermissionError`. Direct in-place truncation writes that risk 0-byte corruption are strictly prohibited.
  2. **Storage Headroom Pre-Flight Check (ENOSPC Resilience)**: Before executing non-trivial atomic writes or generating synthetic fixtures, the persistence layer must verify minimum storage headroom via `shutil.disk_usage` ($\ge 10\text{MB}$). If available storage is exhausted, halt gracefully with an actionable warning rather than initiating failing disk writes that crash the process.
  3. **Inter-Process Advisory Locking (Anti-Race Invariant)**: In environments with concurrent subagents, CLI processes, or background threads, persistent read-modify-write state operations must acquire an advisory file lock (`path.with_suffix('.lock')`) with bounded timeout ($2\text{s}$–$5\text{s}$) and automatic stale-lock expiration (>30s), preventing interleaved writes and silent progress erasure.
  4. **Dual-Slot Shadow Snapshots & Schema Migration (`.bak` Fallback)**: Before replacing existing persistent state, rotate the verified file to a shadow backup (`file.json.bak`). On launch, if the primary file is detected to be corrupted or 0-byte truncated from an unclean shutdown, the self-healing routine must quarantine the corrupted artifact (`*.corrupt_*`), restore state from the shadow backup (`.bak`), and apply forward-compatible schema migration (`migrate_ledger_schema`) before falling back to empty defaults.
  5. **Signal-Aware Memory Drain & Read-Only Fallback**: Long-running agents and background tasks must register signal handlers (`SIGINT`/`SIGTERM`) to flush in-flight working memory to disk and release advisory locks before exiting. In read-only container environments or sandboxes where disk writes are restricted, the system must degrade gracefully to ephemeral in-memory state with a diagnostic warning rather than crashing.
  6. **Multi-File Staging, WAL & Orphan Sanitation**: Multi-file refactors or syncs must stage all target buffers completely in temporary storage and validate syntax before sequential atomic replacements, preventing split-brain states. Startup self-healing must actively sweep and purge abandoned temporary buffers (`*.tmp_*`) left by interrupted dead processes.
  7. **Continuous Chaos & Fault-Injection Verification**: Automated test suites must systematically validate resilience against hostile power cuts—including 0-byte truncated files, malformed JSON streams, disk space limits, shadow recovery, and lock concurrency—guaranteeing 100% self-healing without application panic.

---

### PRINCIPLE-014: Automated Test Verification & Continuous Test Coverage (Regression Shield)
- **Concept**: Automated tests form the immutable contract shield of the repository. Every code modification, new feature, bug fix, or refactoring must be accompanied by automated unit or integration tests. Under no circumstance may tests be weakened or deleted to force verification gates to pass.
- **Invariant**: 100% test pass gate (<1s sub-second execution); test sanctity invariant (anti-weakening); hermetic isolation (zero leaked files); self-explaining diagnostics.
- **Rules**:
  1. **Test-Backed Changes & Regression Shield**: Every code modification, service layer, data schema, or bug fix must include dedicated unit tests in `tests/`. Adding untested production logic or leaving coverage gaps across critical paths is strictly prohibited.
  2. **Test Sanctity Invariant (Anti-Regression Masking)**: Existing test assertions represent immutable contractual truth. When a test fails after code changes, the AI must fix the production implementation to satisfy the contract. Weakening assertions (e.g. changing strict checks to `assertTrue(True)`), commenting out tests, deleting test methods, or applying `@unittest.skip` to force passes is strictly prohibited unless the user explicitly requested a breaking contract overhaul.
  3. **Hermetic Isolation & Zero Flakiness (<1s Gate)**: Unit tests must execute in under 1 second total ($T_{\text{suite}} < 1\text{s}$), run completely deterministically, and avoid external network calls (use mocks/fakes). Prohibit arbitrary wall-clock sleeps (`time.sleep()`); use mock time, deterministic clocks, or seeded pseudorandom generators.
  4. **Pristine Working Tree Invariant (Zero Leaked Artifacts)**: File I/O tests must execute strictly within ephemeral temporary sandboxes (`tempfile.TemporaryDirectory()` or RAII context managers). Running the test suite must leave `git status --porcelain` completely clean with zero dangling test files, logs, or state artifacts left on disk.
  5. **Self-Explaining Assertions & Diagnostic Precision**: Test assertions must provide explicit, descriptive failure messages containing actual vs. expected values, evaluated paths, and failure context. Precise diagnostics allow calling agents to pinpoint root causes in a single turn without exploratory guesswork.
  6. **Hostile Boundary & Edge-Case Hardening**: Tests must prioritize boundary and hostile input verification (empty collections, `None` arguments, 0-byte files, schema variations, extreme numbers, malformed types) rather than superficial happy-path line coverage.

---

### PRINCIPLE-015: Universal Operational Dogfooding & Chaos Verification (The AI Must Use What It Builds)
- **Concept**: Synthetic headless unit tests in idealized vacuums fail to detect real-world interaction bugs. The AI assistant must interactively execute and operate what it builds across domain surfaces (UI event loops, CLI subshells, web dev servers, or backend APIs) coupled with chaos fuzzing and zero-blast-radius sandboxing.
- **Invariant**: Universal operational dogfooding (pump GUI event loop / test CLI / check DOM / API calls); zero-blast-radius test sandbox; terse reporting (<15 lines).
- **Rules**:
  1. **Domain-Specific Interactive Dogfooding**:
     - *Desktop GUI*: Spawns the live window in-process, pumps the event loop, invokes buttons, traverses tabs, stress-tests mid-operation window destruction, and mechanically traps unhandled callback exceptions.
     - *Web Apps*: Launches the local dev server, uses browser/headless tools to interact with DOM elements, verifies forms and routing, and asserts zero console errors (`console.error`).
     - *CLI Applications*: Executes the binary in subshells with arguments, pipes stdin/stdout, tests interrupt signals (SIGINT), and verifies exit codes and error formatting.
     - *Backend APIs*: Boots the service, executes real HTTP requests with test clients, and asserts status codes and response contracts.
  2. **Exhaustive Corner Verification & End-to-End Execution**: Every critical path, modal, dialog, toggle, setting, and error handler must be explicitly driven and tested under realistic conditions. Never assume untested UI corners or backend branches will function.
  3. **Realistic Live Budgeting & Sanity Guardrails**: When testing against live external providers or models, exercise real-world workflows rather than artificial micro-stubs. Ensure sanity guardrails prevent ridiculous waste: strictly forbid dumping unbounded raw data into prompts or spawning uncontrolled retry loops.
  4. **Offline Chaos Fuzzing & Malformed Output Resilience**: Complement live tests with offline deterministic chaos fuzzing to verify graceful recovery from malformed JSON, integer types, markdown codeblocks, rate limits, and network dropouts at zero token cost.
  5. **Zero-Blast-Radius & Ephemeral Sandboxing (Safety Jail)**: Dogfooding must NEVER touch real user directories (Desktop, Documents, personal folders, or system files). All operational tests must execute inside isolated, ephemeral test sandboxes populated strictly with synthetic test files, enforced by active blast-radius containment assertions, and cleaned up completely upon completion.
  6. **Terse Context Reporting**: Dogfood runner outputs in terminal/chat must remain concise status dashboards (<15 lines). Verbose diagnostics and stack traces must be externalized to persistent disk logs (`.agents/dogfood_last_run.log`) to prevent conversational attentional drift and context compaction (**PRINCIPLE-001**, **PRINCIPLE-004**, **PRINCIPLE-012**).
  7. **Pre-Ship Dogfooding Gate**: The interactive dogfooding suite must be executed and confirmed passing with 100% success alongside standard unit tests before staging changes.

---

## 🚀 Phase 5: Living Synchronization & Delivery

### PRINCIPLE-016: AI Knowledge Base & Continuous Synchronization
- **Concept**: The repository must maintain an active, structured, and modular codebase knowledge base in `knowledge/`. Every AI assistant interacting with this codebase must consult the knowledge base for deep architectural context and systematically update it after any architectural, service, model, or UI change to eliminate knowledge drift.
- **Invariant**: Canonical `knowledge/` sync; auto-update architecture/decisions/codebase map on change; `scripts/update_knowledge_base.py`.
- **Rules**:
  1. **Canonical Structure**: The knowledge base must reside in `knowledge/` with modular documentation (`INDEX.md`, `architecture.md`, `services.md`, `data_models.md`, `state_and_ui.md`, `decisions.md`, and `codebase_map.md`).
  2. **Mandatory Sync After Every Change**: Whenever classes, functions, architectural boundaries, or data models are added, modified, or refactored, the relevant knowledge base files must be updated immediately in the same task.
  3. **Automated Verification**: Run `python scripts/update_knowledge_base.py` to inspect the codebase AST, regenerate `knowledge/codebase_map.md`, and verify documentation completeness.
  4. **Cold-Start Acceleration**: A cold-starting AI assistant can read `knowledge/INDEX.md` to achieve comprehensive structural understanding without blind codebase searches.

---

### PRINCIPLE-017: Living Principles System & Automated Synchronization (Auto-Sync Governance)
- **Concept**: Principles can and will be added as the project evolves. Whenever any principle is added, updated, or revised, all AI guideline documents across the repository must be automatically synchronized to maintain absolute consistency.
- **Invariant**: Automated cross-IDE rule sync (`scripts/sync_principles.py`); context budget check (<8,000 chars cap); schema compliance.
- **Rules**:
  1. **Canonical Schema**: Any new principle must follow the standard schema:
     - `PRINCIPLE-XXX: [Title]`
     - **Concept**: High-level explanation.
     - **Invariant**: Dense mechanical formula and anchor pointer.
     - **Rules**: Concrete, testable requirements.
  2. **Automated Cross-AI Synchronization**: Whenever principles change, the AI MUST immediately update all guideline targets across the repository:
     - `AGENTS.md` (Master AI specification)
     - `GUIDELINES.md` (Human and architectural reference)
     - `GEMINI.md` (Gemini & Antigravity IDE)
     - `.agents/rules/principles.md` (Antigravity workspace rules)
     - `CLAUDE.md` (Anthropic Claude Code)
     - `.cursorrules` (Cursor IDE)
     - `.github/copilot-instructions.md` (GitHub Copilot)
     - `README.md` (Public documentation)
  3. **Automated Sync Tooling**: Maintain a synchronization script (`scripts/sync_principles.py`) to programmatically validate and propagate principle updates across all targets.
  4. **Forward Compatibility**: When new principles are introduced, existing code should be audited and adapted incrementally to maintain compliance.

---

### PRINCIPLE-018: Automatic Git Workflow (Commit & Push)
- **Concept**: AI must maintain an active, clean, and reliable Git trail without requiring manual commit reminders from the user.
- **Invariant**: Automatic conventional commits (`feat`, `fix`, `refactor`, `docs`, `chore`, `test`) + git push upon verified task completion.
- **Rules**:
  1. **Automatic Commits**: After completing any meaningful task, feature implementation, refactoring, or documentation update, the AI must automatically stage and commit the changes.
  2. **Conventional Commits**: Commit messages must follow the Conventional Commits format (`feat(...)`, `fix(...)`, `refactor(...)`, `docs(...)`, `chore(...)`) with clear, descriptive explanations.
  3. **Automatic Push**: After committing, the AI must automatically push the commit to the active remote branch (`origin/main` or current working branch) and confirm the commit hash to the user.
  4. **Integrity Check**: Before committing, ensure the code builds/runs, all unit tests pass (100%), and no temporary or unwanted files are staged.

---

## 🛠️ AI Task Checklists

### 🛫 Pre-Flight Checklist (Run at Cold Start / Before Coding)
- [ ] **Instruction & Context Budget Check**: Are prompt rules, summaries, and outputs compact to prevent context bloat and preserve LLM focus (**PRINCIPLE-001**)?
- [ ] **Lifecycle Alignment**: Am I following the 5 execution phases in chronological order (**PRINCIPLE-002**)?
- [ ] **Empirical Grounding (Read-Before-Write)**: Have I verified code definitions, imports, paths, and signatures on disk before writing or modifying code (**PRINCIPLE-003**)?
- [ ] **Attentional Anchor & Budget**: Is my working memory externalized to disk, and am I using targeted slices to preserve context budget (**PRINCIPLE-004**)?
- [ ] **Context Verification**: Have I reviewed active principles (`PRINCIPLE-001` through `PRINCIPLE-018`) and repo state (**PRINCIPLE-005**)?
- [ ] **Disruption & Progress Audit**: Have I checked for uncommitted changes, untracked files, or interrupted tasks from prior disruptions (**PRINCIPLE-006**)?
- [ ] **Pre-Flight Impact & Quality Gate**: Have I evaluated why this change is needed, projected benefits, 4 blast-radius risks, and anti-satisficing quality (**PRINCIPLE-007**)?
- [ ] **Hierarchical Decomposition Plan**: Has the task been planned top-down, indexed into micro-milestones ($N/M$), and scheduled for bottom-up implementation (**PRINCIPLE-008**)?
- [ ] **Modularity & Layering Plan**: Is the architecture 4-layer decoupled with role protocols, zero-config DI, and zero circular imports (**PRINCIPLE-009**)?
- [ ] **Performance & Resource Plan**: Is the solution designed for stream efficiency, non-blocking I/O, RAII cleanup, and lean dependencies (**PRINCIPLE-010**)?
- [ ] **Friction & Accessibility Check**: Is it pure-stdlib clone-and-run, self-bootstrapping, zero-crash, and headless-ready (**PRINCIPLE-011**)?
- [ ] **Code Conciseness & Token Budget Plan**: Are prompt prefixes cache-aligned, tool outputs bounded, and code syntactically dense (**PRINCIPLE-012**)?
- [ ] **Crash Resilience & Atomicity Plan**: Are state writes atomic, lock-retried, shadow-backed, schema-migrated, and ENOSPC-guarded (**PRINCIPLE-013**)?
- [ ] **Test Coverage Plan**: Have I planned hermetic, sub-second unit tests with boundary cases and self-explaining assertions (**PRINCIPLE-014**)?
- [ ] **Operational Dogfooding & Safety Plan**: Is there an interactive dogfooding plan with zero-blast-radius ephemeral sandboxing for real execution (**PRINCIPLE-015**)?
- [ ] **Knowledge Base Context**: Have I checked relevant guides in `knowledge/` to understand existing patterns (**PRINCIPLE-016**)?

### 🛬 Post-Flight Checklist (Run Before Completion)
- [ ] Is governance overhead **lean and progressively disclosed** without prompt bloat (**PRINCIPLE-001**)?
- [ ] Was the task executed according to the **temporal lifecycle flow** (**PRINCIPLE-002**)?
- [ ] Is all code **empirically grounded** with verified symbols, zero hallucinations, and AST validation (**PRINCIPLE-003**)?
- [ ] Was **working memory externalized** to disk/ledger, avoiding attentional drift (**PRINCIPLE-004**)?
- [ ] Has **README.md been updated** to reflect all changes (**PRINCIPLE-005**)?
- [ ] Have intermediate milestones been **safely checkpointed and disruption-protected** (**PRINCIPLE-006**)?
- [ ] Was the **pre-flight impact assessment respected** without diminishing quality (**PRINCIPLE-007**)?
- [ ] Have I adhered to **hierarchical decomposition and bottom-up execution** (**PRINCIPLE-008**)?
- [ ] Is the architecture **4-layer decoupled with role protocols, zero-config DI, and immutable DTOs** (**PRINCIPLE-009**)?
- [ ] Are code paths **stream-efficient, non-blocking, leak-free (RAII), and fast (<1s tests)** (**PRINCIPLE-010**)?
- [ ] Does the app maintain **clone-and-run accessibility, self-bootstrapping, and actionable errors** (**PRINCIPLE-011**)?
- [ ] Is the code **token-frugal, prompt-cache aligned, tool-bounded, and syntactically dense** (**PRINCIPLE-012**)?
- [ ] Are all state changes **crash-resilient, atomically written, shadow-backed, and schema-migrated** (**PRINCIPLE-013**)?
- [ ] Have all **tests passed with 100% success under the Test Sanctity Invariant with zero working-tree pollution** (**PRINCIPLE-014**)?
- [ ] Has **domain-specific operational dogfooding & chaos verification** passed in a sandboxed jail (**PRINCIPLE-015**)?
- [ ] Has the **AI knowledge base in `knowledge/` been updated and verified** (**PRINCIPLE-016**)?
- [ ] Have all **AI guideline files been automatically synchronized** if principles changed (**PRINCIPLE-017**)?
- [ ] Has an **automatic commit** been created with a conventional commit message and pushed (**PRINCIPLE-018**)?
