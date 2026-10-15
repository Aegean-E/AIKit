# Project Guidelines & Architecture Principles

This document defines the architectural guidelines and design principles for this project. All contributors, automated pipelines, and AI systems must adhere to these rules.

---

## 🧭 Principles Index

| ID | Title | Summary |
|---|---|---|
| **[PRINCIPLE-001](#principle-001-hierarchical-problem--task-decomposition)** | Hierarchical Problem Decomposition | Hierarchical decomposition of complex problems and datasets into bounded sub-tasks. |
| **[PRINCIPLE-002](#principle-002-automatic-git-workflow-commit--push)** | Automatic Git Workflow | Automated conventional commits and pushes upon task completion. |
| **[PRINCIPLE-003](#principle-003-modularity--pluggable-architecture)** | Modularity & Pluggable Architecture | Abstract provider/service interfaces and decoupled presentation/business logic. |
| **[PRINCIPLE-004](#principle-004-living-principles-system-extensible-governance--auto-sync)** | Living Principles & Auto-Sync | Extensible protocol; automatically synchronizes all AI guidelines across the repository. |
| **[PRINCIPLE-005](#principle-005-ai-cold-start-readiness--living-documentation-readme-sync)** | AI Cold-Start Readiness & README Sync | Self-describing repo for instant agent onboarding; README updated after every change. |
| **[PRINCIPLE-006](#principle-006-pre-flight-impact--quality-checklist-cold-start-gate)** | Impact & Quality Checklist | Pre-flight cold-start checklist evaluating why, benefits, risks, and quality preservation. |
| **[PRINCIPLE-007](#principle-007-performance--resource-optimization-speed--lean-architecture)** | Speed & Lean Optimization | Maximum execution speed, non-blocking async operations, and lean dependency footprint. |
| **[PRINCIPLE-008](#principle-008-zero-friction-onboarding--instant-usability-one-click-start)** | One-Click Zero-Install Usability | Zero mandatory external apps; one-click start with sensible defaults and graceful degradation. |
| **[PRINCIPLE-009](#principle-009-token-frugality--lean-code-architecture-context-budgeting)** | Token Frugality & Lean Code | Concise code, strict token budgets, compact payloads, and rate-limit safeguards. |
| **[PRINCIPLE-010](#principle-010-ai-knowledge-base--continuous-synchronization)** | AI Knowledge Base | Active codebase documentation in `knowledge/` auto-updated after every change. |
| **[PRINCIPLE-011](#principle-011-automated-test-verification--continuous-test-coverage-regression-shield)** | Regression Shield | 100% test pass gate and continuous test coverage before staging and committing. |
| **[PRINCIPLE-012](#principle-012-crash-resilience-state-atomicity--power-loss-recovery-fail-safe-operations)** | Crash Resilience & Atomicity | Fail-safe atomic writes (fsync + replace) and incremental WAL for sudden power cuts. |
| **[PRINCIPLE-013](#principle-013-incremental-progress-checkpointing--disruption-recovery-zero-progress-loss-workflow)** | Zero-Progress-Loss Workflow | Micro-milestone commits, pre-flight disruption audit, and task ledger recovery. |
| **[PRINCIPLE-014](#principle-014-empirical-grounding--anti-hallucination-invariant-verify-before-execution)** | Empirical Grounding | Read-before-write invariant, verifying disk symbols, and deterministic AST verification. |
| **[PRINCIPLE-015](#principle-015-attentional-drift-prevention--compaction-resilience-context-anchor-protocol)** | Compaction & Drift Resilience | Context anchor protocol, continuous checklist re-anchoring, and ledger self-orientation. |
| **[PRINCIPLE-016](#principle-016-universal-operational-dogfooding--chaos-verification-the-ai-must-use-what-it-builds)** | Operational Dogfooding & Chaos | Interactive UI/CLI/API dogfooding, zero-blast-radius sandboxing, and chaos resilience. |

---

## 📖 Principle Details

### PRINCIPLE-001: Hierarchical Problem & Task Decomposition
- **Problem**: Monolithic or flat batch processing fails when dealing with deep hierarchies, thousands of items, or complex taxonomies.
- **Guideline**:
  - Implement hierarchical decomposition: Root Domain $\rightarrow$ High-Level Category $\rightarrow$ Sub-Task $\rightarrow$ Atomic Unit.
  - Divide-and-conquer problem spaces recursively instead of feeding unbounded flat lists into single prompts.
  - Enable recursive validation and refinement loops for ambiguous edge cases.

### PRINCIPLE-002: Automatic Git Workflow (Commit & Push)
- **Problem**: Uncommitted work leads to lost progress, uncoordinated branches, and accidental regressions.
- **Guideline**:
  - The AI assistant automatically stages, commits, and pushes verified code changes upon task or milestone completion.
  - Always use [Conventional Commits](https://www.conventionalcommits.org/):
    - `feat(scope): ...`
    - `fix(scope): ...`
    - `refactor(scope): ...`
    - `docs(scope): ...`
    - `chore(scope): ...`

### PRINCIPLE-003: Modularity & Pluggable Architecture
- **Problem**: Monolithic architectures make it difficult to introduce new backends, providers, or algorithms without breaking existing code.
- **Guideline**:
  - **Provider/Service Abstraction**: Decouple external services and adapters behind abstract interfaces.
  - **Decoupled Architecture**: Keep UI and CLI wrappers purely focused on presentation and input handling, delegating all domain logic to dedicated service modules and data models.

### PRINCIPLE-004: Living Principles System (Extensible Governance & Auto-Sync)
- **Problem**: Projects evolve, and static rules or fragmented guideline files become outdated and desynchronized.
- **Guideline**:
  - When new architectural patterns or project requirements emerge, register a new principle following the `PRINCIPLE-XXX` template.
  - **Mandatory Auto-Sync**: Modifying or adding any principle must automatically update all AI guideline targets (`AGENTS.md`, `GUIDELINES.md`, `GEMINI.md`, `CLAUDE.md`, `.cursorrules`, `.agents/rules/principles.md`, `.github/copilot-instructions.md`, and `README.md`).
  - Use `scripts/sync_principles.py` to programmatically validate and synchronize all targets.

### PRINCIPLE-005: AI Cold-Start Readiness & Living Documentation (README Sync)
- **Problem**: New AI sessions and developers starting fresh ("cold start") lose context if documentation is stale, fragmented, or implicit.
- **Guideline**:
  - **Cold-Start Availability**: Keep the repository completely self-describing so any AI model can immediately understand architecture, run commands, principles, and configurations without external guesswork.
  - **Mandatory README Update**: Update `README.md` immediately following any functional change, feature addition, refactoring, or architectural modification.

### PRINCIPLE-006: Pre-flight Impact & Quality Checklist (Cold-Start Gate)
- **Problem**: Rushing into implementation without understanding context, risks, or rationale leads to broken contracts, regressions, or cheapened designs.
- **Guideline**:
  - Before writing code, execute a pre-flight assessment:
    - **Why required**: Understand root cause and motivation.
    - **Expected benefits**: Identify improvements to UX, reliability, or performance.
    - **Potential harm/risks**: Anticipate failure modes, high latency, context window exhaustion, or thread locks.
    - **Quality Non-Diminution**: Checklists must strictly elevate standards and prevent corners from being cut; they must never justify degraded quality.

### PRINCIPLE-007: Performance & Resource Optimization (Speed & Lean Architecture)
- **Problem**: Bloated dependencies, unoptimized loops, blocking operations, and inefficient prompting degrade user experience and inflate resource costs.
- **Guideline**:
  - **Speed & Latency**: Optimize algorithms for minimal runtime ($O(N)$ operations, generators, set lookups).
  - **Non-blocking Execution**: Execute disk operations and heavy API calls in background threads or async tasks to keep main event loops fluid.
  - **Lean Dependencies**: Maintain a minimal dependency footprint; favor standard library solutions and lazy imports.
  - **Prompt Frugality**: Design token-efficient prompt structures to accelerate inference and reduce API costs.

### PRINCIPLE-008: Zero-Friction Onboarding & Instant Usability (One-Click Start)
- **Problem**: Cumbersome installation steps, mandatory third-party software setups, and fragile configuration scripts alienate users and developers.
- **Guideline**:
  - **Zero Mandatory External Installations**: Enable users to run the core features immediately out of the box with sensible defaults.
  - **Graceful Degradation**: If an optional external service or runtime is unavailable or unconfigured, the application must guide the user with clear instructions rather than crashing or freezing.

### PRINCIPLE-009: Token Frugality & Lean Code Architecture (Context Budgeting)
- **Problem**: Careless token usage exhausts context windows, triggers rate-limit (TPM) failures, increases latency, and bloats costs. Overly verbose code impedes maintainability.
- **Guideline**:
  - **Lean, High-Leverage Code**: Keep code concise, elegant, and modular. Eliminate boilerplate and unnecessary verbosity.
  - **Strict Token Budgeting**: Never dump raw, unbounded data lists into a single prompt. Cap payload batches and enforce maximum thresholds.
  - **Dense Payload Serialization**: Transmit concise relative identifiers and compact schemas rather than repetitive verbose structures.
  - **Rate Limit Safeguards**: Implement rate-limit aware batch pacing and backoff strategies.

### PRINCIPLE-010: AI Knowledge Base & Continuous Synchronization
- **Problem**: When AI assistants or new contributors enter a codebase, they often lack contextual awareness of internal service contracts, data structures, threading guarantees, and design decisions. This results in slow cold-starts, inaccurate modifications, or knowledge drift.
- **Guideline**:
  - **Dedicated Knowledge Base**: Maintain an active, modular knowledge repository under `knowledge/` (`INDEX.md`, `architecture.md`, `services.md`, `data_models.md`, `state_and_ui.md`, `decisions.md`, and `codebase_map.md`).
  - **Continuous Updates**: Whenever architecture, services, providers, models, or UI flows change, the corresponding knowledge documents must be updated in the same commit.
  - **Automated AST Synchronization**: Use `python scripts/update_knowledge_base.py` to continuously parse the codebase AST, refresh `knowledge/codebase_map.md`, and validate knowledge base completeness.
  - **Cold-Start Acceleration**: Any AI assistant starting work on the repository must first consult `knowledge/INDEX.md` to establish deep contextual grounding without exhaustive searches.

### PRINCIPLE-011: Automated Test Verification & Continuous Test Coverage (Regression Shield)
- **Problem**: Code changes made without automated tests easily introduce subtle regressions, break edge-case contracts, or crash in production. Manual testing is slow, incomplete, and error-prone.
- **Guideline**:
  - **Mandatory Test-Backed Changes**: Every code modification, new feature, bug fix, or refactoring must be accompanied by automated unit or integration tests in `tests/`.
  - **Zero-Regression Gate**: The full test suite must be executed and confirmed 100% passing before any commit is finalized.
  - **Deterministic, Fast, and Isolated**: Tests must run quickly (<1 second total), avoid brittle external network calls (use mocks or local fixtures), and clean up all temporary filesystem artifacts.
  - **Comprehensive Coverage**: Incrementally expand test coverage for core paths, error handling, provider fallback, and sync scripts.

### PRINCIPLE-012: Crash Resilience, State Atomicity & Power-Loss Recovery (Fail-Safe Operations)
- **Problem**: Sudden power cuts, electrical outages, process crashes, or battery failures mid-operation can corrupt state files, sever logs, or leave batches in an unrecoverable, untracked state.
- **Guideline**:
  - **Atomic File Operations**: All critical JSON configurations and logs must use atomic temporary staging (`.tmp`) with buffer flushing (`flush` + `os.fsync`) followed by atomic filesystem replacement (`os.replace`). Direct in-place overwrites are prohibited.
  - **Write-Ahead Logging (WAL)**: Progress across batch operations must be journaled incrementally as each operation succeeds, guaranteeing that an unexpected power cut leaves a complete record up to the instant of failure.
  - **Startup Self-Healing**: On launch, corrupted or truncated state files caused by sudden crashes must be quarantined gracefully (`*.corrupt_*`), with the app restoring safe defaults or backups without crashing.
  - **Non-Destructive Operations**: Never overwrite colliding target files; guarantee data persistence until destination operations are verified on disk.

### PRINCIPLE-013: Incremental Progress Checkpointing & Disruption Recovery (Zero-Progress-Loss Workflow)
- **Problem**: When electricity cuts out or hardware crashes occur during a multi-file task or long coding session, all uncommitted in-memory work is wiped out, files may be left in half-edited states, and cold-starting AI agents cannot determine what was interrupted or where to resume.
- **Guideline**:
  - **Micro-Milestone Atomicity**: Break down complex implementations into small, verifiable sub-tasks and commit working state incrementally rather than accumulating large, vulnerable working-tree drifts.
  - **Pre-flight Disruption Audit**: Every cold-start session must begin by auditing `git status`, inspecting surviving uncommitted files, and checking for interrupted ledger records before modifying any code.
  - **Atomic File Modifications**: All source, test, script, and guideline modifications must be written atomically with buffer flushes and atomic replaces (`os.replace`) to eliminate 0-byte truncation risks during unexpected power-downs.
  - **Disruption Ledger**: Track in-flight multi-step refactors in `.agents/task_ledger.json` (managed via `scripts/disruption_recovery.py`) so any subsequent agent or developer can seamlessly inspect the checkpoint trail and resume.
  - **Non-Breaking Invariant**: Every intermediate checkpoint commit must maintain a clean build and 100% passing automated unit tests (`PRINCIPLE-011`).

### PRINCIPLE-014: Empirical Grounding & Anti-Hallucination Invariant (Verify-Before-Execution)
- **Problem**: AI coding models frequently hallucinate non-existent module imports, obsolete function signatures, phantom file paths, or arbitrary data schemas when guessing without empirical verification.
- **Guideline**:
  - **Read-Before-Write Invariant**: Never edit a file, call an internal function, or instantiate a class without first reading or grepping its definition and signature from the local codebase.
  - **Empirical Fact-Checking**: When referencing file paths, configuration keys, or third-party capabilities, verify their presence on disk or in the active runtime environment rather than presuming they exist.
  - **Zero Assumption on Ambiguity**: When data or intent is ambiguous, fall back to safe deterministic patterns (e.g., standard fallbacks, date-based groupings, explicit exceptions for unsupported features) rather than guessing arbitrary categories or hallucinating contents.
  - **Automated AST & Test Gating**: Rely on deterministic verification tools (`scripts/update_knowledge_base.py`, compiler/linter checks, and unit tests) to mechanically catch hallucinations before committing.

### PRINCIPLE-015: Attentional Drift Prevention & Compaction Resilience (Context Anchor Protocol)
- **Problem**: In long-running pair programming sessions, large contexts induce "attentional drift" (the AI forgetting rules, skipping checklists, or losing constraints) and conversation compaction discards transient conversational context, causing amnesia.
- **Guideline**:
  - **Externalized Working Memory**: Never store task status, multi-step plans, or architectural decisions solely in transient conversation turns. Persist them immediately to structured artifacts (`.agents/task_ledger.json`, `knowledge/decisions.md`, or working scratch files).
  - **Continuous Checklist Re-anchoring**: At the beginning of each turn and after any compaction event, the AI must actively re-anchor to the Pre-flight/Post-flight checklist and active principles rather than relying on stale conversational inertia.
  - **Context-Budgeted Information Retrieval**: When retrieving code or context, use targeted slice viewing (`StartLine`/`EndLine`, `grep_search`, AST outlines) rather than blindly dumping large files into context, preventing context bloating that accelerates compaction.
  - **Compaction Self-Orientation**: Upon detecting a compaction resume or cold restart, the AI must immediately inspect `git status`, the latest commit log (`git log -n 1`), and the task ledger (`.agents/task_ledger.json`) to establish 100% factual grounding before proposing or executing code.

### PRINCIPLE-016: Universal Operational Dogfooding & Chaos Verification (The AI Must Use What It Builds)
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
  - **Terse Context Reporting**: Dogfood runner outputs in terminal/chat must remain concise status dashboards (<15 lines). Verbose diagnostics and stack traces must be externalized to persistent disk logs (`.agents/dogfood_last_run.log`) to prevent conversational attentional drift and context compaction (**PRINCIPLE-009**, **PRINCIPLE-015**).
  - **Pre-Ship Dogfooding Gate**: The interactive dogfooding suite must be executed and confirmed passing with 100% success alongside standard unit tests before staging changes.

---

## 📝 How to Add New Principles

To add a new principle:
1. Assign the next sequential ID (`PRINCIPLE-017`, etc.).
2. Define the **Problem/Concept** and concrete **Rules/Guidelines**.
3. Update `GUIDELINES.md` and `AGENTS.md`.
4. Run `python scripts/sync_principles.py` to auto-propagate across all AI guidelines.

