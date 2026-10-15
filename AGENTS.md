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
- **Concept**: Every major component must be modular, decoupled, and adhere to the Single Responsibility Principle.
- **Invariant**: Single responsibility; abstract provider/service interfaces; decoupled presentation and business logic.
- **Rules**:
  1. **Pluggable Provider/Service Interfaces**: Core services must use abstract provider or adapter interfaces. Never tightly couple business logic to specific external APIs, third-party libraries, or runtime backends.
  2. **Decoupled Presentation & Logic**: UI/CLI entrypoints must only handle presentation, input validation, and user interactions. Business logic must live strictly in decoupled service modules and data models.
  3. **Extensibility**: Adding a new provider, strategy, format, or algorithm must require minimal changes and zero breaking changes to existing modules.

---

### PRINCIPLE-010: Performance & Resource Optimization (Speed & Lean Architecture)
- **Concept**: Every code change, architectural modification, and dependency choice must be optimized for execution speed, low latency, optimal algorithmic complexity, and lean resource utilization (CPU, memory, disk I/O, and token budgets).
- **Invariant**: Algorithmic efficiency ($O(N)$ scanning, set lookups); non-blocking async execution; lean stdlib-first dependencies.
- **Rules**:
  1. **Algorithmic & I/O Efficiency**: All scanning, filtering, and data transformations must employ optimal algorithmic complexity ($O(N)$ scanning, set lookups, generator pipelines, buffered file operations).
  2. **Non-Blocking & Asynchronous Execution**: Heavy operations (file system walks, batch processing, network/API calls) must execute asynchronously or in worker threads, never blocking the UI or main event loop.
  3. **Lean Dependency Footprint**: Avoid introducing bloated, heavy third-party packages when standard library or lightweight modules suffice. Utilize lazy loading for heavy dependencies.
  4. **Token & Network Frugality**: Prompts, batch sizes, and data payloads must be budgeted to minimize latency, token consumption, and API costs while preserving reasoning accuracy.
  5. **No Brittle Premature Hacks**: Optimization must remain readable, maintainable, modular (**PRINCIPLE-009**), and strictly tested.

---

### PRINCIPLE-011: Zero-Friction Onboarding & Instant Usability (One-Click Start)
- **Concept**: The application must be instantly usable out of the box ("one-click and start") without forcing users to jump through cumbersome installation hurdles, manual environment configurations, or mandatory third-party software setups.
- **Invariant**: Zero mandatory external dependencies; out-of-the-box defaults; graceful degradation with actionable user guidance.
- **Rules**:
  1. **Zero Mandatory External Setup**: Never force users into external dependency setup to experience core application features. Provide immediate zero-install pathways and intelligent fallbacks.
  2. **Sensible Out-of-the-Box Defaults**: The application must run cleanly on first launch using default settings without requiring manual configuration files.
  3. **Graceful Degradation**: If an optional external service or runtime is unavailable or unconfigured, the application must guide the user with clear instructions rather than crashing, freezing, or error-looping.

---

### PRINCIPLE-012: Token Frugality & Lean Code Architecture (Context Budgeting)
- **Concept**: Code must be concise, expressive, and devoid of unnecessary bloat. All interactions with LLMs must be strictly budgeted for tokens—leveraging compact representations and hierarchical batching so requests never exhaust context windows, exceed rate limits (TPM), or waste user tokens.
- **Invariant**: Concise code; strict token budgets; compact JSON schemas/relative paths; exponential backoff rate-limit guards.
- **Rules**:
  1. **Concise, High-Leverage Code**: Avoid gratuitous verbosity, bloated helper chains, or repetitive boilerplate. Write clean, modular, and concise implementations.
  2. **Strict Token Budgeting**: Prompts must never blindly dump raw, unbounded file or data lists into a single context. Enforce strict batch size caps and character limits.
  3. **Compact Serialization**: Use dense, compact payload formats (e.g. relative paths, short keys, terse JSON schemas) to cut prompt token consumption by 50–70%.
  4. **Rate-Limit Guardrails**: Implement token-aware pacing and exponential backoff to operate seamlessly within free-tier API limits.

---

## 🛡️ Phase 4: Operational Verification & Resilience

### PRINCIPLE-013: Crash Resilience, State Atomicity & Power-Loss Recovery (Fail-Safe Operations)
- **Concept**: The application must remain fail-safe and self-healing against abrupt disruptions—such as sudden power outages, battery exhaustion, OS crashes, or external process termination. User data, application settings, and state transaction logs must never be left in a corrupted, half-written, or unrecoverable state due to unexpected power loss.
- **Invariant**: Fail-safe atomic writes (temp buffer -> `flush()` -> `os.fsync()` -> `os.replace()`); WAL for batch ops; isolate `*.corrupt_*`.
- **Rules**:
  1. **Atomic State & Configuration Persistence**: All persistent JSON state, configuration, and cache files must be written via atomic temporary files with buffer flushing (`flush` + `os.fsync`) followed by atomic replacement (`os.replace`). Direct in-place truncation writes that risk 0-byte files on power cut are strictly prohibited.
  2. **Incremental Transaction Journaling (WAL)**: Batch modifications must record operations incrementally into persistent storage as each operation safely completes, guaranteeing that an interrupted batch leaves an accurate, reversible trail up to the exact moment of failure.
  3. **Startup Self-Healing & Crash Tolerance**: On startup, if any persistent state file is detected to be damaged or malformed from an unclean shutdown, the application must automatically isolate the corrupted artifact (`*.corrupt_*`), recover from backup or safe defaults, and report the event cleanly rather than crashing.
  4. **Non-Destructive File Guarantees**: Move/delete operations must prioritize data retention over speed. Critical paths must verify target presence before source unlinking, and existing destination files must never be overwritten on collision.
  5. **Continuous Recovery Verification**: Automated tests must validate crash recovery behaviors, ensuring corrupted JSON, partial transactions, and unclean shutdowns are handled gracefully without application panic.

---

### PRINCIPLE-014: Automated Test Verification & Continuous Test Coverage (Regression Shield)
- **Concept**: Every code modification, new feature, bug fix, or refactoring must be accompanied by automated unit or integration tests wherever technically feasible. Before finalizing any task, the full automated test suite must be executed and confirmed passing to guarantee zero regressions.
- **Invariant**: 100% test pass gate (`python -m unittest discover tests`); fast deterministic isolated unit tests before staging/committing.
- **Rules**:
  1. **Test-Backed Changes**: Any new feature, service method, model, or bug fix must include dedicated unit tests in `tests/`.
  2. **Zero-Regression Gate**: The complete test suite (`python -m unittest discover tests` or project test command) must be executed and pass with 100% success before staging and committing.
  3. **Deterministic & Fast Tests**: Tests must be fully automated, fast (<1s), isolated, independent of external network APIs (using mocks/fakes where necessary), and clean up all temporary filesystem artifacts.
  4. **Continuous Test Expansion**: As the codebase evolves, edge cases, error conditions, and cross-platform path handling must be incrementally added to the test suite to fortify test coverage.
  5. **Pre-flight & Post-flight Integration**: The Pre-flight checklist must plan test coverage, and the Post-flight checklist must verify that all tests pass.

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
- [ ] **Modularity & Provider Plan**: Is the architecture decoupled with pluggable provider/service boundaries (**PRINCIPLE-009**)?
- [ ] **Performance & Resource Plan**: Is the solution designed for optimal speed, minimal latency, and lean dependencies (**PRINCIPLE-010**)?
- [ ] **Friction & Accessibility Check**: Does the solution maintain "one-click start" without forcing external app installs (**PRINCIPLE-011**)?
- [ ] **Code Conciseness & Token Budget Plan**: Is the code concise, and are prompts/payloads token-budgeted and compact (**PRINCIPLE-012**)?
- [ ] **Crash Resilience & Atomicity Plan**: Are file writes, settings, and transaction logs protected against power-loss corruption (**PRINCIPLE-013**)?
- [ ] **Test Coverage Plan**: Have I planned unit tests to validate this change and prevent regressions (**PRINCIPLE-014**)?
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
- [ ] Is the architecture **modular** and decoupled (**PRINCIPLE-009**)?
- [ ] Are code paths **optimized for speed, responsiveness, and lean resource consumption** (**PRINCIPLE-010**)?
- [ ] Does the app maintain **one-click zero-install accessibility** (**PRINCIPLE-011**)?
- [ ] Is the code **concise, lean, and token-frugal** without context waste (**PRINCIPLE-012**)?
- [ ] Are all state changes and logs **crash-resilient and written atomically** (**PRINCIPLE-013**)?
- [ ] Have all **automated unit tests passed with 100% success** (**PRINCIPLE-014**)?
- [ ] Has **domain-specific operational dogfooding & chaos verification** passed in a sandboxed jail (**PRINCIPLE-015**)?
- [ ] Has the **AI knowledge base in `knowledge/` been updated and verified** (**PRINCIPLE-016**)?
- [ ] Have all **AI guideline files been automatically synchronized** if principles changed (**PRINCIPLE-017**)?
- [ ] Has an **automatic commit** been created with a conventional commit message and pushed (**PRINCIPLE-018**)?
