# Project Guidelines & Architecture Principles

This document defines the architectural guidelines and design principles for this project. All contributors, automated pipelines, and AI systems must adhere to these rules.
The principles are strictly ordered according to the **5 Chronological Execution Phases**: **Meta-Governance & Grounding** $\rightarrow$ **Pre-Flight Orientation & Planning** $\rightarrow$ **Architecture & Lean Implementation** $\rightarrow$ **Operational Verification & Resilience** $\rightarrow$ **Living Sync & Delivery**.

---

## 🧭 Principles Index (Lifecycle-Ordered)

### 🏛️ Phase 1: Meta-Governance & Attentional Grounding
| ID | Title | Summary |
|---|---|---|
| **[PRINCIPLE-001](#principle-001-progressive-rule-disclosure--governance-frugality-zero-instruction-bloat)** | Progressive Disclosure & Lean Rules | Two-tier rule disclosure, strict prompt token budget (<1,500 tokens), and zero instruction bloat. |
| **[PRINCIPLE-002](#principle-002-lifecycle-aligned-instruction-ordering--attentional-priming-cognitive-flow-invariant)** | Lifecycle-Aligned Instruction Ordering | Monotonic 5-phase execution gate, remediation recoil, adaptive pathing, and late-stage priming immunity. |
| **[PRINCIPLE-003](#principle-003-empirical-grounding--anti-hallucination-invariant-verify-before-execution)** | Empirical Grounding | Slice freshness & call-site check, manifest dependencies, platform parity, and strict AST gate. |
| **[PRINCIPLE-004](#principle-004-attentional-drift-prevention--compaction-resilience-context-anchor-protocol)** | Compaction & Drift Resilience | Bounded ledger, living plan SSOT, anti-repetition on compaction, and AST-first slice retrieval. |

### 🧭 Phase 2: Pre-Flight Orientation & Planning
| ID | Title | Summary |
|---|---|---|
| **[PRINCIPLE-005](#principle-005-ai-cold-start-readiness--living-documentation-readme-sync)** | AI Cold-Start Readiness & README Sync | Self-describing repo, 30s cold-start orientation (<20k chars), material surface sync, executable command parity, and whole-tree drift shield. |
| **[PRINCIPLE-006](#principle-006-incremental-progress-checkpointing--disruption-recovery-zero-progress-loss-workflow)** | Zero-Progress-Loss Workflow | Micro-milestone commits, pre-flight disruption audit, and CLI ledger recovery. |
| **[PRINCIPLE-007](#principle-007-pre-flight-impact--quality-checklist-cold-start-gate)** | Impact & Quality Checklist | Pre-flight Track C checklist evaluating why, benefits, 4 blast-radius risks, scope ceiling, and anti-satisficing. |
| **[PRINCIPLE-008](#principle-008-hierarchical-problem--task-decomposition)** | Hierarchical Problem Decomposition | Hierarchical decomposition of complex problems and datasets into bounded sub-tasks. |

### 🏗️ Phase 3: Architecture & Lean Implementation
| ID | Title | Summary |
|---|---|---|
| **[PRINCIPLE-009](#principle-009-modularity--pluggable-architecture)** | Modularity & Pluggable Architecture | Abstract provider/service interfaces and decoupled presentation/business logic. |
| **[PRINCIPLE-010](#principle-010-performance--resource-optimization-speed--lean-architecture)** | Speed & Lean Optimization | Maximum execution speed, non-blocking async operations, and lean dependency footprint. |
| **[PRINCIPLE-011](#principle-011-zero-friction-onboarding--instant-usability-one-click-start)** | One-Click Zero-Install Usability | Zero mandatory external apps; one-click start with sensible defaults and graceful degradation. |
| **[PRINCIPLE-012](#principle-012-token-frugality--lean-code-architecture-context-budgeting)** | Token Frugality & Lean Code | Concise code, strict token budgets, compact payloads, and rate-limit safeguards. |

### 🛡️ Phase 4: Operational Verification & Resilience
| ID | Title | Summary |
|---|---|---|
| **[PRINCIPLE-013](#principle-013-crash-resilience-state-atomicity--power-loss-recovery-fail-safe-operations)** | Crash Resilience & Atomicity | Fail-safe atomic writes (fsync + replace) and incremental WAL for sudden power cuts. |
| **[PRINCIPLE-014](#principle-014-automated-test-verification--continuous-test-coverage-regression-shield)** | Regression Shield | 100% test pass gate and continuous test coverage before staging and committing. |
| **[PRINCIPLE-015](#principle-015-universal-operational-dogfooding--chaos-verification-the-ai-must-use-what-it-builds)** | Operational Dogfooding & Chaos | Interactive UI/CLI/API dogfooding, zero-blast-radius sandboxing, and chaos resilience. |

### 🚀 Phase 5: Living Synchronization & Delivery
| ID | Title | Summary |
|---|---|---|
| **[PRINCIPLE-016](#principle-016-ai-knowledge-base--continuous-synchronization)** | AI Knowledge Base | Active codebase documentation in `knowledge/` auto-updated after every change. |
| **[PRINCIPLE-017](#principle-017-living-principles-system--automated-synchronization-auto-sync-governance)** | Living Principles & Auto-Sync | Extensible protocol; automatically synchronizes all AI guidelines across the repository. |
| **[PRINCIPLE-018](#principle-018-automatic-git-workflow-commit--push)** | Automatic Git Workflow | Automated conventional commits and pushes upon task completion. |

---

## 📖 Principle Details

### PRINCIPLE-001: Progressive Rule Disclosure & Governance Frugality (Zero Instruction Bloat)
- **Problem**: Monolithic rule injections burn 15–30% of active context windows, dilute reasoning, inflate latency, and trigger "satisficing" bugs where models guess implementation details instead of following rigorous invariants.
- **Guideline**:
  - **Two-Tier Progressive Disclosure**:
    - *Tier 1 (Always-Injected System Instructions)*: Target IDE rules (`.cursorrules`, `GEMINI.md`, `CLAUDE.md`, `.github/copilot-instructions.md`) must only contain dense, self-sufficient invariant capsules and essential pointers. Never inject multi-page essays, full code blocks, or raw historical logs into always-on prompt contexts.
    - *Tier 2 (Disk-Backed On-Demand Knowledge)*: Full explanations, deep problem analysis, and implementation guides live on disk (`GUIDELINES.md`, `knowledge/`) and are read selectively via targeted slice tooling (`view_file`, `grep_search`) only when relevant sub-tasks require them.
  - **Self-Sufficient Invariant Capsules (Anti-Satisficing Invariant)**: Compression must target narrative filler, rationale, and examples—never hard mechanical constraints. Every Tier 1 summary must encode the exact technical mechanism (e.g., `flush` + `os.fsync` + `os.replace`, 100% test pass gate, read-before-write symbol check) so routine tasks succeed with 100% accuracy without requiring disk roundtrips.
  - **Autonomous Tier 2 Retrieval Trigger Protocol**: The AI agent must proactively slice-view Tier 2 documentation (`GUIDELINES.md` / `knowledge/`) upon encountering any of the following 3 operational triggers:
    1. *Architectural Boundary Trigger*: Introducing new services, data schemas, or modifying cross-module API contracts.
    2. *Failure & Regression Trigger*: Encountering any test failure, build breakage, or runtime exception.
    3. *Ambiguity Trigger*: Addressing underspecified domain requirements or missing schema models.
  - **Universal vs. Domain Rule Partitioning (Adopter Ready)**: When deploying AIKit to govern external projects, maintain a strict 3-tier boundary:
    - *Tier 1A (Universal AI Governance)*: AIKit's immutable 18 engineering invariants (<1,000 tokens).
    - *Tier 1B (Project Domain Invariants)*: Project-specific ironclad conventions defined in `.agents/rules/domain.md` or dedicated prompt section (<300 tokens: framework version, linting, naming conventions).
    - *Tier 2 (Disk Knowledge & Schemas)*: Project architecture, database schemas, and API specs in `knowledge/`.
  - **Deterministic Grep Anchor Contract**: All Tier 2 guideline sections must use unique regex-safe headers (`### PRINCIPLE-XXX:`). Pointers must instruct agents to locate and slice-view the exact 30-line block via single-call grep (`Query="### PRINCIPLE-XXX:"`), eliminating line-number drift across edits.
  - **Strict Injected Context Budget & Automated Gate**: Enforce a strict token budget for always-injected IDE rule files (target <1,500 tokens / <8,000 chars total overhead). `scripts/sync_principles.py` must track, report, and mechanically guard against rule footprint creep.
  - **High Information Density (Anti-Fluff Invariant)**: Eliminate filler words, decorative prose, and duplicate instructions. Maximize the information-to-token ratio across all guidelines.
  - **Terse Checklist Execution**: Checklists must be concise and actionable, designed to be verified mentally or in compact ledgers without spamming conversational history with verbose multi-paragraph checklists.
  - **Zero Context Bloat on Expansion**: When adding new principles or guidelines, existing summaries must be condensed or modularized so total system prompt overhead remains bounded and flat over time.

### PRINCIPLE-002: Lifecycle-Aligned Instruction Ordering & Attentional Priming (Cognitive Flow Invariant)
- **Problem**: Arbitrary principle ordering causes cognitive phase confusion, while passive chronological text fails to prevent agents from skipping verification, cheating tests on failure, or yielding to late-stage user pressure ("push right now!"). Furthermore, forcing heavy multi-phase ceremonies on trivial queries destroys usability.
- **Guideline**:
  - **Monotonic Execution Gating (Lock-Step Integrity)**: Workflows must advance strictly along the 5 lifecycle phases: Meta-Governance $\rightarrow$ Pre-Flight Orientation $\rightarrow$ Architecture & Implementation $\rightarrow$ Verification & Resilience $\rightarrow$ Living Sync & Delivery. Phase 5 delivery actions (git commit, push, PR) are mechanically locked until Phase 4 verification gates (automated unit tests, operational dogfooding) pass with 100% success.
  - **Remediation Recoil Protocol (Phase 4 Failure)**: When Phase 4 verification breaks, forward progression pauses immediately. The agent recoils strictly to Phase 3 (for code defects) or Phase 2 (for architectural/assumption defects), fixes the root cause, and re-executes Phase 4. Modifying test assertions to mask regressions is strictly prohibited (Test Sanctity Invariant).
  - **Adaptive Lifecycle Pathing & Automatic Escalation**: To keep development fast and frictionless, execution adapts across 3 explicit operational tracks:
    - *Track A (Query / Exploration)*: Information retrieval and code explanation $\rightarrow$ Phase 1 Grounding $\rightarrow$ direct answer (Phases 2–5 bypassed).
    - *Track B (Trivial / Documentation)*: Typo fixes, doc edits, or comment updates $\rightarrow$ Phase 1 $\rightarrow$ Phase 3 (Edit) $\rightarrow$ Phase 5 (Sync & Commit), with Phase 4 scaled to syntax/budget check.
    - *Track C (Engineering / Feature / Refactor)*: Complete 5-phase sequence with mandatory impact gates, regression tests, and living sync.
    - *Automatic Track Escalation*: If any Track A or Track B task mutates executable source code, schemas, or dependencies, the task automatically escalates to Track C, unlocking mandatory Phase 2 planning and Phase 4 regression gates.
  - **Compaction Phase Resumption**: In multi-turn sessions, the active phase number (1 through 5) must be recorded in working memory (`.agents/task_ledger.json`). Upon conversation compaction or cold restart, the agent must orient against the ledger to resume execution at the exact interrupted phase rather than losing state.
  - **Immunity to Late-Stage User Priming**: When users issue urgent conversational commands to bypass testing (e.g., *"commit right now"*, *"push immediately"*), the AI must remain anchored to the lifecycle gate: delivery actions are strictly blocked until verification succeeds.
  - **Primacy-Weighted Anchoring**: Epistemic grounding, context budget limits, and safety invariants must occupy the primacy zone (top of context) where transformer attention is sharpest. Terminal delivery actions must reside strictly at the end.
  - **Continuous Sequence Audit**: Auto-sync tooling and automated test suites mechanically parse Phase headers and guarantee that principles maintain strictly monotonic lifecycle phase progression.

### PRINCIPLE-003: Empirical Grounding & Anti-Hallucination Invariant (Verify-Before-Execution)
- **Problem**: AI coding models frequently hallucinate non-existent module imports, obsolete function signatures, phantom file paths, or arbitrary data schemas when guessing without empirical verification. Furthermore, multi-turn editing suffers from stale line-drift failures, orphaned call-sites during refactoring, cross-platform OS incompatibilities, and cross-layer contract mismatches.
- **Guideline**:
  - **Read-Before-Write & Target Slice Freshness**: Never edit a file, call an internal function, or instantiate a class without first reading or grepping its definition and signature from the local codebase. When performing multi-turn or multi-file edits, re-verify the target slice immediately prior to mutation to eliminate line-drift and stale-offset edit failures.
  - **Call-Site & Reference Completeness**: Before modifying signatures, renaming, or deleting any function, class, or configuration key, grep for all call-sites and references across the codebase to ensure complete refactoring with zero orphaned symbols or duplicate ghost implementations.
  - **Manifest-Backed Dependency Grounding**: Never introduce a third-party package, module import, or external CLI tool without first verifying that it is declared in the project's dependency manifest (`pyproject.toml`, `requirements.txt`, `package.json`, `Cargo.toml`) or is part of the language standard library. In zero-dependency repositories (such as AIKit), external imports are strictly prohibited.
  - **Platform & Runtime Parity**: Never assume OS-specific shell builtins, path separators, or binary aliases (`python3` vs `py`, `bash` vs `powershell`) without checking the active runtime (`sys.platform`). Use portable standard-library APIs (`pathlib.Path`, `subprocess.run([sys.executable, ...])`) and shell-agnostic commands.
  - **Bi-Directional Contract Parity**: When modifying data schemas, API contracts, or serialization models, the AI must verify both producer and consumer interfaces across system boundaries before proposing code changes.
  - **Dual-Track Ambiguity Protocol & Epistemic Triad**:
    - *Epistemic Triad Gate*: Before starting Phase 3 implementation, pass the 3-point check: (1) Symbol Reality (verified exact definition & call-sites), (2) Dependency Reality (declared in manifest or stdlib), and (3) Platform Reality (valid for active OS/shell).
    - *Data/Runtime Ambiguity*: Apply safe, deterministic, non-destructive fallbacks with explicit warning logs.
    - *Architectural/Intent Ambiguity*: Never guess business logic or execute destructive actions under ambiguity. Halt forward progression and escalate to the user with structured, concise options.
  - **Strict AST & Syntax Gating**: Rely on deterministic verification tools (`scripts/update_knowledge_base.py`, AST parsers, compiler dry-runs, and unit tests) to mechanically validate syntax and symbol integrity. `scripts/update_knowledge_base.py` enforces strict AST validation and halts on any syntax error before advancing to Phase 4.

### PRINCIPLE-004: Attentional Drift Prevention & Compaction Resilience (Context Anchor Protocol)
- **Problem**: In long-running pair programming sessions, large contexts induce "attentional drift" (the AI forgetting rules, skipping checklists, or losing constraints), repetitive plan printing pollutes conversational history, unbounded file dumps exhaust tokens, and conversation compaction discards transient context, inducing amnesia. Furthermore, unbounded ledger files grow into context traps, and compacted agents frequently re-prompt users on already-resolved decisions.
- **Guideline**:
  - **Externalized Working Memory & Living Plan SSOT**: Never store task status, multi-step plans, or architectural decisions solely in transient conversational turns. Persist them immediately to structured artifacts (`.agents/task_ledger.json`, `knowledge/decisions.md`). Never reprint verbose multi-step plans across conversational turns; update the plan in-place on disk and keep chat updates terse (<15 lines). Maintain a bounded rolling ledger window via `scripts/disruption_recovery.py` to prevent working memory bloat.
  - **Compaction Resumption & Anti-Repetition Invariant**: Upon cold restart or conversation compaction, execute a 3-step self-orientation before taking action:
    1. *Ledger Audit*: Inspect `.agents/task_ledger.json` for `active_task`, `active_phase` (1..5), and completed checkpoints.
    2. *Working Tree Audit*: Inspect `git status` and `git log -n 1` to establish factual physical ground truth.
    3. *Monotonic Resumption & Anti-Repetition*: Resume execution directly at the interrupted phase without re-asking resolved user questions or re-executing verified steps. Disk state is authoritative over truncated dialogue history; once a choice is recorded in an ADR or ledger, it is finalized and must never be re-prompted.
  - **AST-First & Slice-Capped Retrieval**: When exploring code, consult AST symbol catalogs (`knowledge/codebase_map.md`) or targeted symbol greps before opening raw files. When reading source code, use targeted line slices (`StartLine`/`EndLine` <100 lines) focused on the relevant symbol, preventing context window exhaustion.
  - **Two-Tier Memory Partitioning & Immediate ADR Persistence**: Maintain strict separation between (1) mutable in-flight execution scratchpads (`.agents/task_ledger.json`) and (2) permanent immutable architectural records (`knowledge/decisions.md`). Persist all architectural choices, user constraints (e.g. zero-dependency rules, library bans), and data schemas immediately to `knowledge/decisions.md` as structured ADRs. Treat the decision register as immutable disk ground truth across long sessions.
  - **Terse Tool Invocation & Attentional Re-Anchoring**: When executing CLI commands, prefer bounded, summary-oriented flags (`git status --short`, `git log -n 1 --oneline`, `git diff --stat`, test runner `-q`). Never dump unbounded mega-logs or full file diffs into conversational turns. At the beginning of each turn, re-anchor to the Pre-flight/Post-flight checklist and active phase invariants.

### PRINCIPLE-005: AI Cold-Start Readiness & Living Documentation (README Sync)
- **Problem**: New AI sessions and developers starting fresh ("cold start") lose context if documentation is stale, fragmented, or implicit. Furthermore, rotting quickstart commands waste developer and agent turns, unmonitored directory trees drift out of date as files are added or renamed, unbounded README files exhaust the active context window on turn 1, and indiscriminate sync rules cause documentation churn on internal refactors.
- **Guideline**:
  - **Self-Describing Repository, 30-Second Orientation & Token Ceiling**: The project must maintain an explicit, high-visibility orientation block in `README.md` documenting: (1) runtime prerequisites, (2) zero-ambiguity setup/run commands, (3) canonical test commands, and (4) directory tree and primary entry points. A cold-starting agent must achieve complete operational orientation in its first turn without speculative file browsing. To prevent first-turn context exhaustion, `README.md` must stay strictly under 20,000 characters (<5,000 tokens), delegating deep architectural specifications to `knowledge/`.
  - **Material Surface Sync Contract**: A synchronous update to `README.md` is mandatory whenever a change alters setup/run instructions, CLI flags, environment variables, public API/UI contracts, or governance principles. Internal non-breaking refactors update `knowledge/` rather than adding churn to `README.md`.
  - **Executable Command Parity**: Every command, script invocation, or code snippet documented in `README.md` must be factual, literal, and verified to run successfully in the active runtime environment. Zero phantom commands or broken quickstarts.
  - **Documentation Partitioning (The SSOT Triad)**:
    - `README.md`: Public surface, quickstart, entry points, and high-level architecture.
    - `AGENTS.md` / `GUIDELINES.md`: Behavioral rules, lifecycle invariants, and engineering principles.
    - `knowledge/`: Deep technical domain knowledge, AST codebase maps, schemas, and immutable ADR decision records.
  - **Whole-Tree Drift Shield & Script Parity**: Whenever top-level files or core entrypoint scripts (e.g. in `scripts/`, `knowledge/`, or repository root) are added, removed, or renamed, the directory tree in `README.md` must be synchronously updated. Every relative path and script cited in the `README.md` directory tree must physically exist on disk (zero phantom scripts or dead file citations).
  - **Universal Polyglot Adopter Blueprint**: When adopting AIKit into non-Python stacks (Node/TS, Rust, Go, Java), the project's `README.md` must adapt the 30-second orientation matrix to declare the canonical stack equivalents (e.g. `npm test` / `cargo test` / `go test`, Node/Rust/Go toolchain versions, dev server commands) ensuring instant cold-start readiness regardless of programming language.

### PRINCIPLE-006: Incremental Progress Checkpointing & Disruption Recovery (Zero-Progress-Loss Workflow)
- **Problem**: When electricity cuts out or hardware crashes occur during a multi-file task or long coding session, all uncommitted in-memory work is wiped out, files may be left in half-edited states, orphaned temporary buffers clutter the tree, and cold-starting AI agents cannot determine what was interrupted or where to resume.
- **Guideline**:
  - **Micro-Milestone Atomicity & Conventional Micro-Commits**: Break down complex implementations into small, verifiable sub-tasks and commit working state incrementally rather than accumulating large, vulnerable working-tree drifts that risk total loss upon power cut. Micro-commits must follow Conventional Commits with milestone indices: `type(task): [milestone N/M] description`.
  - **Pre-flight Disruption Audit on Cold Start**: Every cold-start session must begin by auditing the working tree via `scripts/disruption_recovery.py --audit` or `--resume`, inspecting surviving uncommitted files, and checking for interrupted ledger records before modifying any code.
  - **Atomic File Modifications**: All source, test, script, and guideline modifications must be written atomically with buffer flushes and atomic replaces (`os.replace`) to eliminate 0-byte truncation risks during unexpected power-downs.
  - **Disruption Ledger, Resumption & Reset Protocol**: Track in-flight multi-step refactors in `.agents/task_ledger.json` via `scripts/disruption_recovery.py --checkpoint <task_id> --phase <phase> --desc <desc>`. Incoming agents execute `scripts/disruption_recovery.py --resume` to inspect surviving files and cleanly resume at the interrupted phase with zero duplicate effort. Abandoned tasks are cleanly cleared via `scripts/disruption_recovery.py --reset [reason]`.
  - **Non-Breaking Micro-Checkpoints (Test Sanctity Gate)**: Every intermediate checkpoint commit must maintain a clean build and 100% passing automated unit tests (`PRINCIPLE-014`). If intermediate code does not pass tests, progress must be recorded in `.agents/task_ledger.json` rather than committing broken states to git.
  - **Explicit Staging & Transient Buffer Hygiene**: When committing micro-milestones, explicitly stage only the files modified for that specific sub-task (never execute blind `git add .`). Orphaned temporary buffers (`*.tmp_*`) left behind by interrupted writes must be purged via `scripts/disruption_recovery.py --clean` to maintain clean workspace hygiene.

### PRINCIPLE-007: Pre-flight Impact & Quality Checklist (Cold-Start Gate)
- **Problem**: Rushing into implementation without understanding context, risks, or rationale leads to broken contracts, regressions, or cheapened designs. Conversely, uncontrolled scope creep results in speculative over-engineering.
- **Guideline**:
  - Before mutating code or schemas on Track C tasks, execute a structured pre-flight impact assessment:
    - **Why required**: Understand root cause, user goal, or architectural gap.
    - **Expected benefits**: Concrete UX, modularity, performance, or reliability gains.
    - **4 Blast-Radius Dimensions**:
      - *Contracts*: Public API, CLI flag, signature, and schema parity.
      - *Dependencies*: Zero undeclared external packages or non-standard tools.
      - *Concurrency*: Non-blocking async execution, no event-loop starvation or thread deadlocks.
      - *State*: Backward-compatible storage schemas and atomic mutations.
    - **Anti-Satisficing & Type Preservation**: Strictly forbids `# TODO` stubs, silent exception swallowing (`except Exception: pass`), weakened test assertions, aesthetic degradation, or casting to `Any` / `# type: ignore` to bypass type safety.
    - **Scope Ceiling (Anti-Gold-Plating)**: Keep modifications strictly bounded to the evaluated user goal and direct mitigations; never add speculative unrequested frameworks or features.
    - **Reversibility & Principle 8 Bridge**: Verify clean working baseline before starting with an atomic rollback path. Mitigations directly define the hierarchical micro-milestones decomposed in Principle 8.
    - **Ledger Persistence & Conversational Conciseness**: Keep chat output <6 lines. Persist full rationale via `scripts/disruption_recovery.py --checkpoint <task_id> --phase 2 --desc "..." --why "..." --benefits "..." --risks "..." --mitigation "..."` to preserve pre-flight context across compactions.

### PRINCIPLE-008: Hierarchical Problem & Task Decomposition
- **Problem**: Monolithic or flat batch processing fails when dealing with deep hierarchies, thousands of items, or complex taxonomies.
- **Guideline**:
  - Implement hierarchical decomposition: Root Domain $\rightarrow$ High-Level Category $\rightarrow$ Sub-Task $\rightarrow$ Atomic Unit.
  - Divide-and-conquer problem spaces recursively instead of feeding unbounded flat lists into single prompts.
  - Enable recursive validation and refinement loops for ambiguous edge cases.

### PRINCIPLE-009: Modularity & Pluggable Architecture
- **Problem**: Monolithic architectures make it difficult to introduce new backends, providers, or algorithms without breaking existing code.
- **Guideline**:
  - **Provider/Service Abstraction**: Decouple external services and adapters behind abstract interfaces.
  - **Decoupled Architecture**: Keep UI and CLI wrappers purely focused on presentation and input handling, delegating all domain logic to dedicated service modules and data models.

### PRINCIPLE-010: Performance & Resource Optimization (Speed & Lean Architecture)
- **Problem**: Bloated dependencies, unoptimized loops, blocking operations, and inefficient prompting degrade user experience and inflate resource costs.
- **Guideline**:
  - **Speed & Latency**: Optimize algorithms for minimal runtime ($O(N)$ scanning, generators, set lookups).
  - **Non-blocking Execution**: Execute disk operations and heavy tasks in background threads or async tasks to keep event loops silky smooth.
  - **Lean Dependencies**: Maintain a minimal dependency footprint; favor standard library solutions and lazy imports.
  - **Prompt Frugality**: Design token-efficient prompt structures to accelerate inference and reduce API costs.

### PRINCIPLE-011: Zero-Friction Onboarding & Instant Usability (One-Click Start)
- **Problem**: Requiring external desktop software or complicated setup adds huge friction and drives away potential users.
- **Guideline**:
  - **Zero Mandatory External Setup**: Enable users to run and test out-of-the-box with one click using zero-install defaults and intelligent fallbacks.
  - **Sensible Defaults**: The application must run cleanly on first launch using default settings without requiring manual configuration files.
  - **Graceful Degradation**: If an optional runtime or service is unconfigured, guide the user cleanly with helpful messages rather than crashing.

### PRINCIPLE-012: Token Frugality & Lean Code Architecture (Context Budgeting)
- **Problem**: Careless token usage exhausts context windows, triggers rate-limit (TPM) failures, increases latency, and bloats costs. Overly verbose code impedes maintainability.
- **Guideline**:
  - **Lean, High-Leverage Code**: Keep code concise, elegant, and modular. Eliminate boilerplate and unnecessary verbosity.
  - **Strict Token Budgeting**: Never dump raw, unbounded file lists into a single prompt. Cap payload batches and enforce maximum character/token thresholds.
  - **Dense Payload Serialization**: Transmit concise relative paths and compact schema fields rather than repetitive full-path strings.
  - **Rate Limit Safeguards**: Implement rate-limit aware batch pacing and backoff strategies.

### PRINCIPLE-013: Crash Resilience, State Atomicity & Power-Loss Recovery (Fail-Safe Operations)
- **Problem**: Sudden power cuts, electrical outages, process crashes, or battery failures mid-operation can corrupt state files, sever logs, or leave batches in an unrecoverable, untracked state.
- **Guideline**:
  - **Atomic File Operations**: All critical JSON configurations and logs must use atomic temporary staging (`.tmp`) with buffer flushing (`flush` + `os.fsync`) followed by atomic filesystem replacement (`os.replace`). Direct in-place overwrites are prohibited.
  - **Write-Ahead Logging (WAL)**: Progress across batch operations must be journaled incrementally as each operation succeeds, guaranteeing that an unexpected power cut leaves a complete record up to the instant of failure.
  - **Startup Self-Healing**: On launch, corrupted or truncated state files caused by sudden crashes must be quarantined gracefully (`*.corrupt_*`), with the app restoring safe defaults or backups without crashing.
  - **Non-Destructive Operations**: Never overwrite colliding target files; guarantee data persistence until destination operations are verified on disk.

### PRINCIPLE-014: Automated Test Verification & Continuous Test Coverage (Regression Shield)
- **Problem**: Code changes made without automated tests easily introduce subtle regressions, break edge-case contracts, or crash in production. Manual testing is slow, incomplete, and error-prone.
- **Guideline**:
  - **Mandatory Test-Backed Changes**: Every code modification, new feature, bug fix, or refactoring must be accompanied by automated unit or integration tests in `tests/`.
  - **Zero-Regression Gate**: The full test suite (`python -m unittest discover tests`) must be executed and confirmed 100% passing before any commit is finalized.
  - **Deterministic, Fast, and Isolated**: Tests must run quickly (<1 second total), avoid brittle external network calls (use mocks or local fixtures), and clean up all temporary filesystem artifacts.
  - **Comprehensive Coverage**: Incrementally expand test coverage for core paths, error handling, provider fallback, and sync scripts.

### PRINCIPLE-015: Universal Operational Dogfooding & Chaos Verification (The AI Must Use What It Builds)
- **Problem**: Headless unit tests test components in an idealized vacuum with synthetic data, leaving real-world interaction bugs undetected (e.g. unhandled UI event loop callback errors, broken CLI signal handlers, routing failures, or malformed API responses).
- **Guideline**:
  - **Domain-Specific Interactive Dogfooding**:
    - *Desktop GUI*: Spawns the live window in-process, pumps the event loop, invokes buttons, traverses tabs, stress-tests mid-operation window destruction, and mechanically traps unhandled callback exceptions.
    - *Web Apps*: Launches the local dev server, uses browser/headless tools to interact with DOM elements, verifies forms and routing, and asserts zero console errors (`console.error`).
    - *CLI Applications*: Executes the binary in subshells with arguments, pipes stdin/stdout, tests interrupt signals (SIGINT), and verifies exit codes and error formatting.
    - *Backend APIs*: Boots the service, executes real HTTP requests with test clients, and asserts status codes and response contracts.
  - **Exhaustive Corner Verification & End-to-End Execution**: Every critical path, modal, dialog, toggle, setting, and error handler must be explicitly driven and tested under realistic conditions. Never assume untested UI corners or backend branches will function.
  - **Realistic Live Budgeting & Sanity Guardrails**: When testing against live external providers or models, exercise real-world workflows rather than artificial micro-stubs. Ensure sanity guardrails prevent ridiculous waste: strictly forbid dumping unbounded raw data into prompts or spawning uncontrolled retry loops.
  - **Offline Chaos Fuzzing & Malformed Output Resilience**: Complement live tests with offline deterministic chaos fuzzing to verify graceful recovery from malformed JSON, integer types, markdown codeblocks, rate limits, and network dropouts at zero token cost.
  - **Zero-Blast-Radius & Ephemeral Sandboxing (Safety Jail)**: Dogfooding must NEVER touch real user directories (Desktop, Documents, personal folders, or system files). All operational tests must execute inside isolated, ephemeral test sandboxes populated strictly with synthetic test files, enforced by active blast-radius containment assertions, and cleaned up completely upon completion.
  - **Terse Context Reporting**: Dogfood runner outputs in terminal/chat must remain concise status dashboards (<15 lines). Verbose diagnostics and stack traces must be externalized to persistent disk logs (`.agents/dogfood_last_run.log`) to prevent conversational attentional drift and context compaction (**PRINCIPLE-001**, **PRINCIPLE-004**, **PRINCIPLE-012**).
  - **Pre-Ship Dogfooding Gate**: The interactive dogfooding suite must be executed and confirmed passing with 100% success alongside standard unit tests before staging changes.

### PRINCIPLE-016: AI Knowledge Base & Continuous Synchronization
- **Problem**: When AI assistants or new contributors enter a codebase, they often lack contextual awareness of internal service contracts, data structures, threading guarantees, and design decisions. This results in slow cold-starts, inaccurate modifications, or knowledge drift.
- **Guideline**:
  - **Dedicated Knowledge Base**: Maintain an active, modular knowledge repository under `knowledge/` (`INDEX.md`, `architecture.md`, `services.md`, `data_models.md`, `state_and_ui.md`, `decisions.md`, and `codebase_map.md`).
  - **Continuous Updates**: Whenever architecture, services, providers, models, or UI flows change, the corresponding knowledge documents must be updated in the same commit.
  - **Automated AST Synchronization**: Use `python scripts/update_knowledge_base.py` to continuously parse the codebase AST, refresh `knowledge/codebase_map.md`, and validate knowledge base completeness.
  - **Cold-Start Acceleration**: Any AI assistant starting work on the repository must first consult `knowledge/INDEX.md` to establish deep contextual grounding without exhaustive searches.

### PRINCIPLE-017: Living Principles System & Automated Synchronization (Auto-Sync Governance)
- **Problem**: Projects evolve, and static rules or fragmented guideline files become outdated and desynchronized across different AI tools and IDE formats.
- **Guideline**:
  - When new architectural patterns or project requirements emerge, register a new principle following the `PRINCIPLE-XXX` template.
  - **Mandatory Auto-Sync**: Modifying or adding any principle must automatically update all AI guideline targets (`AGENTS.md`, `GUIDELINES.md`, `GEMINI.md`, `CLAUDE.md`, `.cursorrules`, `.agents/rules/principles.md`, `.github/copilot-instructions.md`, and `README.md`).
  - Use `scripts/sync_principles.py` to programmatically validate and synchronize all targets.

### PRINCIPLE-018: Automatic Git Workflow (Commit & Push)
- **Problem**: Uncommitted work leads to lost progress, uncoordinated branches, and accidental regressions.
- **Guideline**:
  - The AI assistant automatically stages, commits, and pushes verified code changes upon task or milestone completion.
  - Always use [Conventional Commits](https://www.conventionalcommits.org/):
    - `feat(scope): ...`
    - `fix(scope): ...`
    - `refactor(scope): ...`
    - `docs(scope): ...`
    - `chore(scope): ...`

---

## 📝 How to Add New Principles

To add a new principle:
1. Assign the next sequential ID (`PRINCIPLE-019`, etc.).
2. Define the **Problem/Concept** and concrete **Rules/Guidelines**.
3. Place it within the appropriate execution phase.
4. Update `GUIDELINES.md` and `AGENTS.md`.
5. Run `python scripts/sync_principles.py` to auto-propagate across all AI guidelines.
