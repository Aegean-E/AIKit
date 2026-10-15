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
  2. **Adaptive Lifecycle Pathing (Scale to Task Scale)**: To keep development zero-friction, task execution adapts across 3 explicit operational tracks:
     - *Track A (Query / Exploration)*: Questions, code explanations, or searches $\rightarrow$ Phase 1 (Grounding) $\rightarrow$ Direct Output (Phases 2–5 bypassed).
     - *Track B (Trivial / Documentation)*: Typo fixes, markdown tweaks, or comment updates $\rightarrow$ Phase 1 $\rightarrow$ Phase 3 (Edit) $\rightarrow$ Phase 5 (Sync & Commit), with Phase 4 scaled to syntax/budget check.
     - *Track C (Engineering / Feature / Refactor)*: Complete 5-phase sequence with mandatory impact gates, regression tests, and living sync.
  3. **Immunity to Late-Stage User Priming**: When users issue urgent late-stage commands (e.g. *"commit right now"*, *"push immediately"*, *"skip tests"*), the AI must remain anchored to the lifecycle gate. Terminal delivery actions cannot be executed until required verification gates pass.
  4. **Primacy-Weighted Anchoring**: Epistemic grounding, context budget limits, and safety invariants must occupy the top of prompts (primacy zone) where transformer attention is sharpest. Terminal delivery gates must reside strictly at the end.
  5. **Continuous Sequence Audit**: Auto-sync tooling and automated tests must mechanically verify that all 18 principles are partitioned across the 5 lifecycle phases in strictly monotonic sequence without phase inversions.

---

### PRINCIPLE-003: Empirical Grounding & Anti-Hallucination Invariant (Verify-Before-Execution)
- **Concept**: Never make architectural assumptions, guess function signatures, invent phantom dependencies, or extrapolate ambiguous data models without first reading and verifying factual source code, schemas, and runtime state on disk.
- **Invariant**: Read-before-write invariant (`view_file`/`grep_search` symbol check before write); zero assumption on ambiguity; deterministic AST test gating.
- **Rules**:
  1. **Read-Before-Write Invariant**: Never edit a file, call an internal function, or instantiate a class without first reading or grepping its definition and signature from the local codebase.
  2. **Empirical Fact-Checking**: When referencing file paths, configuration keys, or third-party capabilities, verify their presence on disk or in the active runtime environment rather than presuming they exist.
  3. **Zero Assumption on Ambiguity**: When data or intent is ambiguous, fall back to safe deterministic patterns (e.g. standard fallbacks, date-based groupings, explicit exceptions for unsupported features) rather than guessing arbitrary categories or hallucinating contents.
  4. **Automated AST & Test Gating**: Rely on deterministic verification tools (`scripts/update_knowledge_base.py`, compiler/linter checks, and unit tests) to mechanically catch hallucinations before committing.

---

### PRINCIPLE-004: Attentional Drift Prevention & Compaction Resilience (Context Anchor Protocol)
- **Concept**: Complex, long-running agent workflows must actively counteract attentional drift and context compaction through externalized working memory, disciplined context budgeting, and continuous self-orientation against persistent disk state.
- **Invariant**: Externalized working memory (`.agents/task_ledger.json`); continuous checklist re-anchoring; cold-start self-orientation via `git status` + `git log -n 1`.
- **Rules**:
  1. **Externalized Working Memory**: Never store task status, multi-step plans, or architectural decisions solely in transient conversation turns. Persist them immediately to structured artifacts (`.agents/task_ledger.json`, `knowledge/decisions.md`, or working scratch files).
  2. **Continuous Checklist Re-anchoring**: At the beginning of each turn and after any compaction event, the AI must actively re-anchor to the Pre-flight/Post-flight checklist and active principles rather than relying on stale conversational inertia.
  3. **Context-Budgeted Information Retrieval**: When retrieving code or context, use targeted slice viewing (`StartLine`/`EndLine`, `grep_search`, AST outlines) rather than blindly dumping large files into context, preventing context bloating that accelerates compaction.
  4. **Compaction Self-Orientation**: Upon detecting a compaction resume or cold restart, the AI must immediately inspect `git status`, the latest commit log (`git log -n 1`), and the task ledger (`.agents/task_ledger.json`) to establish 100% factual grounding before proposing or executing code.

---

## 🧭 Phase 2: Pre-Flight Orientation & Planning

### PRINCIPLE-005: AI Cold-Start Readiness & Living Documentation (README Sync)
- **Concept**: The repository must be permanently prepared for a "cold start" by any AI assistant or developer. Any new agent entering the project with zero prior conversational history must immediately understand the project state, run commands, architecture, and principles. To prevent knowledge drift, `README.md` must be systematically updated after every meaningful change.
- **Invariant**: Self-describing repository; zero-ambiguity quickstart; mandatory `README.md` update after every feature, UI, or architectural change.
- **Rules**:
  1. **Self-Describing Repository**: Every architectural decision, file structure, command, and configuration option must be documented explicitly in `README.md`, `GUIDELINES.md`, and code docstrings. No hidden or implicit assumptions are allowed.
  2. **Mandatory README Update After Every Change**: After completing any feature, UI update, configuration change, refactoring, or architectural modification, the AI must immediately update `README.md` to reflect the new state.
  3. **Zero-Ambiguity Quickstart**: The setup and run instructions in `README.md` must always remain functional and up to date for a cold-starting AI or user.

---

### PRINCIPLE-006: Incremental Progress Checkpointing & Disruption Recovery (Zero-Progress-Loss Workflow)
- **Concept**: Development workflows and AI execution sessions must be resilient against abrupt disruptions—such as sudden power outages, battery depletion, OS crashes, or process termination. Progress must never be treated as an all-or-nothing end-of-turn artifact; it must be recorded through incremental, atomic micro-checkpoints, persistent task ledgers, and immediate cold-start recovery protocols to guarantee zero work loss without compromising code quality.
- **Invariant**: Incremental atomic micro-commits; pre-flight disruption audit; disruption recovery ledger via `scripts/disruption_recovery.py`.
- **Rules**:
  1. **Micro-Milestone Atomicity & Verified Commits**: For multi-step tasks or non-trivial implementations, the AI must checkpoint and commit working state incrementally after each logical, verified sub-task (e.g. service logic $\rightarrow$ verified commit; UI component $\rightarrow$ verified commit; docs/tests $\rightarrow$ verified commit) rather than accumulating large, vulnerable working-tree states that risk total loss upon power cut.
  2. **Pre-flight Disruption Audit on Cold Start**: Upon every cold start or conversation resumption, before beginning any new coding task, the AI must immediately audit the working tree (`git status`, uncommitted changes, untracked files, temp artifacts) to detect, preserve, and recover any uncommitted progress interrupted by an unclean shutdown.
  3. **Atomic File Write Integrity**: All script, source, and guideline modifications must be written atomically to disk via temporary buffers and atomic replacements (`os.replace`), ensuring that an abrupt power cut during a write operation never leaves 0-byte or corrupted source files.
  4. **Non-Breaking Micro-Checkpoints**: Every incremental commit must leave the repository in a stable, syntactically valid state with passing unit tests (`PRINCIPLE-014`), never committing broken or half-implemented code to the active branch.
  5. **Disruption Ledger & Resumption Protocol**: Interrupted tasks, ongoing refactors, and multi-step plans must be persisted to a local disruption ledger (`.agents/task_ledger.json` managed via `scripts/disruption_recovery.py`) so any incoming AI assistant or developer can immediately determine the exact point of interruption, review surviving files, and resume execution with zero duplicate effort.

---

### PRINCIPLE-007: Pre-flight Impact & Quality Checklist (Cold-Start Gate)
- **Concept**: Before implementing code modifications, refactorings, or architecture changes—especially upon a cold start—the AI must evaluate a structured pre-flight impact checklist. This assessment ensures the AI clarifies the *why*, maximizes project *benefits*, preemptively identifies potential *harm/regressions*, and proactively guards quality.
- **Invariant**: Cold-start impact gate (evaluate why, benefits, risks/harm mitigation, quality non-diminution) before non-trivial edits.
- **Rules**:
  1. **Mandatory Cold-Start Assessment**:
     - **Why is this required?**: Articulate the exact user goal, pain point, or architectural gap being solved.
     - **How does it benefit the project?**: Identify concrete improvements to user experience, performance, modularity, or reliability.
     - **How could it harm the project?**: Preemptively analyze potential downsides (e.g. breaking changes, performance drops, API rate limit exposure, thread blocking, UI freezes, or complexity bloat).
     - **Mitigation Plan**: Implement defensive designs to neutralize identified risks before applying changes.
  2. **Quality Non-Diminution**:
     - Principles and checklists must **never** be used as an excuse to deliver substandard, crippled, or lazy implementations.
     - All code must maintain high visual polish, complete type safety, robust exception handling, and non-blocking asynchronous execution where applicable.
  3. **Continuous Enforcement**:
     - Run the pre-flight checklist mentally or in scratch plans at every cold start.
     - Complete all items in the task checklist before marking work finished.

---

### PRINCIPLE-008: Hierarchical Problem & Task Decomposition
- **Concept**: Complex systems, deep directory hierarchies, and large datasets must be partitioned hierarchically rather than processed via monolithic, flat-batch prompting or unbounded single-pass operations.
- **Invariant**: Hierarchical decomposition (Root -> Domain -> Sub-task -> Atomic); bounded context; recursive validation with base-case limits.
- **Rules**:
  1. **Hierarchical Partitioning**: Decompose large inputs or operations into structured levels (e.g. Root Domain $\rightarrow$ High-Level Category $\rightarrow$ Sub-Task $\rightarrow$ Atomic Unit).
  2. **Bounded Context**: Never feed unbounded flat data or file lists into a single prompt or operation. Decompose into recursive sub-tasks with well-defined base cases and max-depth limits.
  3. **Recursive Validation & Refinement**: Support recursive self-validation where an AI model checks and refines ambiguous categories, classifications, or edge cases.
  4. **State Propagation**: Child recursive steps must receive scoped context from parent decisions and return structured nodes back up the tree.

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
- [ ] **Pre-Flight Impact & Quality Gate**: Have I evaluated why this change is needed, projected benefits, analyzed potential harm/risks, and guarded quality (**PRINCIPLE-007**)?
- [ ] **Hierarchical Decomposition Plan**: Has the problem been partitioned hierarchically rather than dumped in flat batches (**PRINCIPLE-008**)?
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
- [ ] Have I adhered to **hierarchical decomposition** where applicable (**PRINCIPLE-008**)?
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
