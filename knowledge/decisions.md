# Architectural Decision Records (ADR) 🏛️

Record all significant architectural decisions, trade-offs, and rationale here.

---

## Decisions
 
### ADR-001: Expansion to 16 Core Universal AI Principles
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**: Autonomous AI coding assistants frequently suffer from three subtle failure modes: (1) hallucinating non-existent signatures and dependencies, (2) conversational attentional drift and compaction amnesia during long sessions, and (3) passing headless unit tests while failing on real user interaction loops.
- **Decision**: Formally add PRINCIPLE-014 (Empirical Grounding), PRINCIPLE-015 (Attentional Drift Prevention & Compaction Resilience), and PRINCIPLE-016 (Universal Operational Dogfooding & Chaos Verification) to the universal kit.
- **Consequences**:
  - *Positive*: Guarantees read-before-write discipline, disk-anchored memory against compaction, real interactive validation across GUI/CLI/Web/API surfaces, and zero blast-radius test containment.
  - *Trade-offs*: Requires agents to perform pre-flight symbol checks and maintain structured ledgers, slightly increasing discipline overhead for massive reliability gains.

### ADR-002: Progressive Governance Disclosure and Context Budgeting (PRINCIPLE-001)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**: As governance guidelines expand, monolithic rule files injected into every system prompt consume 15–30% of the active context window, causing prompt bloat, high latency, token burn, and instruction dilution ("lost in the middle").
- **Decision**: Introduce Progressive Disclosure (PRINCIPLE-001) enforcing a Two-Tier architecture: Tier 1 always-on IDE rules are capped (<1,500 tokens) using dense canonical summaries, while Tier 2 deep rationale lives on disk and is retrieved on demand.
- **Consequences**:
  - *Positive*: Guarantees bounded, lean system prompts; preserves context window for real code; reduces API token consumption and TTFT latency.
  - *Trade-offs*: Requires developers and agents to view full guideline documents on disk when deep rationale is needed rather than expecting full manuals in prompt memory.

### ADR-003: Lifecycle-Aligned Principle Reordering & Cognitive Flow Architecture (PRINCIPLE-002)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**: Principles originally evolved chronologically, leading to severe cognitive phase disorder: e.g. "Git Commit & Push" was #2 while "Read-Before-Write" was #14. This primed models toward premature delivery before grounding themselves in workspace facts, aggravating attention bias and phase errors.
- **Decision**: Re-order the entire governance framework into 5 chronological lifecycle execution phases (Meta-Governance & Grounding $\rightarrow$ Pre-Flight Orientation & Planning $\rightarrow$ Architecture & Implementation $\rightarrow$ Operational Verification & Resilience $\rightarrow$ Living Sync & Delivery), and codify this ordering requirement as PRINCIPLE-002.
- **Consequences**:
  - *Positive*: Eliminates phase inversion; maximizes transformer attention through primacy-weighted anchoring of safety/grounding invariants; provides a natural step-by-step cognitive path from cold start to terminal push.
  - *Trade-offs*: Requires renumbering historical principle IDs (001 to 018), which is mitigated by synchronizing all IDE target files atomically.

### ADR-004: Self-Sufficient Invariant Capsules, Autonomous Retrieval Triggers, and Universal vs Domain Partitioning (PRINCIPLE-001)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**: In Tier 1, abstract philosophical summaries caused AI models to "satisfice" (skip disk reads and invent brittle, non-atomic code because the exact technical formula was missing). Conversely, without explicit retrieval triggers, agents either never read Tier 2 or randomly read full files. Furthermore, developers adopting AIKit had no formal standard for segregating universal AI governance from app-specific domain rules.
- **Decision**:
  1. Upgrade Tier 1 summaries into Self-Sufficient Invariant Capsules containing exact technical mechanisms (e.g. `flush` + `os.fsync` + `os.replace`, 100% test pass gate, read-before-write symbol check) plus anchor pointers.
  2. Codify the Autonomous Retrieval Trigger Protocol: agents must slice-view Tier 2 on Architectural Boundaries, Failures/Regressions, or Ambiguity.
  3. Establish 3-tier partitioning for adopters: Tier 1A (Universal AIKit Invariants <1,000 tokens), Tier 1B (Project Domain Invariants <300 tokens), Tier 2 (Project Knowledge Base in `knowledge/`).
  4. Standardize Deterministic Grep Anchors (`Query="### PRINCIPLE-XXX:"` in `GUIDELINES.md`) for 1-call slice viewing without line drift.
- **Consequences**:
  - *Positive*: Routine tasks execute with 100% mechanical accuracy without burning tokens on disk reads; high-risk tasks reliably trigger targeted Tier 2 slice views; clear onboarding path for third-party project adopters.
  - *Trade-offs*: None; all targets remain strictly budgeted (<8,000 chars / ~1,250 tokens).

### ADR-005: Operational Execution Gating and Adaptive Lifecycle Pathing (PRINCIPLE-002)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**: Passive chronological ordering in prompt text was insufficient to prevent autonomous agents from skipping Phase 4 (verification & dogfooding) and jumping directly to Phase 5 delivery. Furthermore, treating every trivial question or documentation edit as a full 5-phase ceremony caused high latency, wasted tokens, and created developer friction. Finally, urgent conversational requests from users ("push now!") frequently triggered recency bias, causing agents to bypass tests.
- **Decision**:
  1. Transform Principle 2 into an active Operational Execution Gate: Phase 5 delivery actions are mechanically locked until Phase 4 verification gates yield a 100% pass.
  2. Implement Adaptive Lifecycle Pathing across 3 operational tracks: Track A (Query/Exploration: Phase 1 Grounding -> Direct output), Track B (Trivial/Doc: Phase 1 -> Phase 3 Edit -> Phase 5 Sync/Commit), and Track C (Engineering/Feature: Strict 1 -> 2 -> 3 -> 4 -> 5).
  3. Codify immunity to late-stage user priming (user urgency cannot override verification gates).
  4. Implement automated 5-phase boundary parsing and validation in `scripts/sync_principles.py` and `tests/test_kit.py`.
- **Consequences**:
  - *Positive*: Eliminates unverified commits; protects agents from conversational pressure; speeds up routine questions and doc edits; guarantees strict mechanical enforcement in test pipelines.
  - *Trade-offs*: None; preserves accuracy while significantly improving development ergonomics.

### ADR-006: Remediation Recoil, Automatic Track Escalation, and Compaction Phase Resumption (PRINCIPLE-002)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**: In real agentic workflows: (1) When Phase 4 verification breaks, agents without explicit guidance either attempt to mutate test assertions (test cheating) or rush ahead to commit broken states. (2) When tasks start as lightweight documentation tweaks (Track B), scope creep often causes agents to modify production code under relaxed rules without running tests. (3) Conversation compaction causes agents to lose their active phase, triggering repetitive planning or premature deliveries.
- **Decision**:
  1. Formalize the Remediation Recoil Protocol: Phase 4 verification failure triggers an immediate recoil to Phase 3 (code defects) or Phase 2 (design defects). Modifying tests to mask regressions is strictly forbidden (Test Sanctity Invariant).
  2. Implement Automatic Track Escalation: Modifying any executable code, schemas, or dependencies in Track A/B instantly escalates the workflow to Track C, enforcing the full Phase 4 regression shield.
  3. Persist `active_phase: 1..5` and `phase_num` in `.agents/task_ledger.json` via `scripts/disruption_recovery.py` to enable instant phase re-orientation after conversation compaction.
- **Consequences**:
  - *Positive*: Closes test-cheating vulnerabilities; eliminates scope creep loopholes; guarantees phase continuity across conversation compactions.
  - *Trade-offs*: None; keeps routine development agile while locking down correctness under failure or scope expansion.

### ADR-007: Target Slice Freshness, Manifest-Backed Dependencies, Contract Parity, and Dual-Track Ambiguity (PRINCIPLE-003)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**: In real-world AI software development: (1) Agents editing code across multi-turn sessions experience stale line-drift and character-offset drift, leading to failed edits or corrupted files. (2) AI models frequently hallucinate external third-party dependencies (`import requests`, `pydantic`, `lodash`) that are not present in project manifests or the environment, breaking lean and zero-dependency builds. (3) Full-stack systems suffer from contract drift when backend schemas or API routes are updated without verifying consumer types. (4) Silent fallbacks for architectural or business intent can result in unintended destructive changes or architectural deviation.
- **Decision**:
  1. Mandate Atomic Target Slice Freshness: Re-verify target slice lines/symbols immediately prior to mutation if intervening turns or edits occurred.
  2. Implement Manifest-Backed Dependency Grounding: Prohibit importing or invoking external third-party modules without first verifying their declaration in project manifests (`requirements.txt`, `package.json`, `Cargo.toml`, etc.) or the language standard library. In zero-dependency repos (like AIKit), third-party imports are strictly forbidden.
  3. Enforce Bi-Directional Contract Parity: Ground both producer and consumer interfaces across system boundaries before altering data models or API routes.
  4. Codify the Dual-Track Ambiguity Protocol: Allow safe deterministic fallbacks with logs for runtime data ambiguities; mandate halting and escalating to the user for architectural or intent ambiguity.
  5. Enforce deterministic AST and syntax validation prior to advancing to Phase 4 test execution.
- **Consequences**:
  - *Positive*: Eliminates the #1 source of AI code defects (phantom dependencies and stale-slice edits); protects data integrity by preventing unguided assumptions on user intent; enforces zero-dependency hygiene.
  - *Trade-offs*: None; preserves high velocity while guaranteeing epistemic precision.

### ADR-008: Strict AST Mechanical Gating, Platform Parity, and Call-Site Reference Completeness (PRINCIPLE-003)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**: In real agentic pair programming: (1) AST tools that silently swallow syntax errors give agents false confidence, delaying error detection until test execution. (2) AI models exhibit strong Unix training bias, hallucinating POSIX shell builtins, slash conventions, and package aliases when operating on Windows or cross-platform targets. (3) During refactoring or deletion, agents often update symbol definitions without inspecting call-sites, causing runtime regression cascades and orphan symbols.
- **Decision**:
  1. Fortify `scripts/update_knowledge_base.py` with strict AST validation (`strict=True` default), raising `ValueError` and failing with non-zero exit when any scanned source file contains syntax errors.
  2. Codify the Platform & Runtime Parity Invariant: agents must use standard-library cross-platform primitives (`pathlib.Path`, `sys.executable`) and ground against the active OS and shell environment.
  3. Codify the Call-Site Reference Completeness Invariant: require grepping for all references and callers prior to altering signatures, renaming, or deleting symbols.
  4. Codify the Epistemic Triad (Symbol Reality, Dependency Reality, Platform Reality) as a fast 3-point pre-implementation filter.
- **Consequences**:
  - *Positive*: Converts AST verification into an active mechanical gate; prevents cross-platform runtime failures; eliminates orphan symbols and duplicate ghost implementations during refactoring.
  - *Trade-offs*: None; zero external dependencies, fast execution.

### ADR-009: Living Plan SSOT, Compaction Resumption Sequence, and AST-First Retrieval (PRINCIPLE-004)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**: In extended agentic coding sessions: (1) Agents frequently reprint verbose 10-to-20-step plans in conversation turns, creating context bloat and causing attentional drift toward obsolete plan versions. (2) Conversation compaction truncates dialogue history, inducing "compaction amnesia" where agents re-ask resolved questions or re-execute completed steps. (3) Unbounded raw file viewing consumes tens of thousands of tokens, accelerating compaction. (4) Negative constraints (e.g. zero-dependency rules) decay over long sessions if not persisted as immutable architectural records.
- **Decision**:
  1. Mandate Living Plan SSOT: multi-step plans must live and update in-place in `.agents/task_ledger.json` or scratch files, while conversational responses remain terse (<15 lines).
  2. Implement the Deterministic Compaction Resumption Sequence: agents execute a 3-step orientation (Ledger audit for `active_phase` and completed checkpoints $\rightarrow$ Working tree audit for uncommitted changes $\rightarrow$ Monotonic phase resumption) without repeating questions.
  3. Enforce AST-First & Slice-Capped Retrieval: consult AST symbol maps (`knowledge/codebase_map.md`) or targeted greps before loading raw files; cap file slices to relevant functional blocks (<100 lines).
  4. Mandate immediate persistence of non-trivial architectural decisions and negative constraints to `knowledge/decisions.md` (ADR Register).
- **Consequences**:
  - *Positive*: Eliminates conversational plan bloat; preserves 70%+ of the active context window; makes compaction recovery seamless without repetitive user friction; protects negative constraints from memory decay.
  - *Trade-offs*: None; preserves high developer velocity with minimal token overhead.

### ADR-010: Bounded Rolling Ledger Window, Anti-Repetition Compaction Invariant, and Two-Tier Memory (PRINCIPLE-004)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**: In multi-week or high-turn projects: (1) `task_ledger.json` accumulates hundreds of historical checkpoints, eventually becoming a massive multi-thousand-token context burden when loaded. (2) Upon conversation compaction, models frequently fall into repetitive prompt loops, re-asking users to decide on previously settled architectural choices. (3) Trivial in-flight scratchpad notes often clutter permanent architectural registers. (4) Unbounded CLI tool outputs (huge git diffs, verbose test outputs) exhaust context budgets.
- **Decision**:
  1. Implement Bounded Rolling Ledger Window: `scripts/disruption_recovery.py` auto-prunes historical checkpoints to keep `task_ledger.json` lean (active task + recent history, default max 20), preserving active task progress while preventing memory bloat.
  2. Codify the Anti-Repetition Invariant: disk state (`task_ledger.json`, `knowledge/decisions.md`) is authoritative over summarized dialogue history; agents must never re-prompt users on recorded decisions.
  3. Formalize Two-Tier Memory Architecture: strictly partition mutable in-flight task scratchpads (`task_ledger.json`) from permanent immutable architectural records (`knowledge/decisions.md`).
  4. Mandate Terse Tool Invocation: require bounded, summary-oriented CLI flags (`git status --short`, `git log -n 1 --oneline`, `git diff --stat`, test runner `-q`).
- **Consequences**:
  - *Positive*: Keeps working memory footprint permanently small (<2 KB); eliminates repetitive user questioning after compaction; keeps decision records clean; prevents terminal output context blowouts.
  - *Trade-offs*: None; zero external dependencies, entirely deterministic.

### ADR-011: Material Surface Sync Contract, 30-Second Cold-Start Orientation, and Documentation SSOT Triad (PRINCIPLE-005)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**: In agentic repositories:
  1. Blanket rules like "update README.md after every change" trigger severe documentation churn—agents spend tokens modifying the root README for trivial internal refactors, test additions, or bug fixes that don't affect public interfaces.
  2. Cold-starting agents entering a repository with zero conversational context often spend several expensive discovery turns reading arbitrary files just to discover how to run the project or where core modules reside.
  3. Setup commands in READMEs frequently decay into non-working pseudo-code or broken aliases because they are treated as static markdown without executable parity verification.
  4. Architectural documentation, governance invariants, and onboarding orientation often become blurred across files with duplicate, conflicting information.
- **Decision**:
  1. Mandate the **30-Second Cold-Start Orientation** in `README.md`: require standard entry points, verified one-line run commands, runtime prerequisites, and a high-level file tree index so cold-starting agents or developers can orient within 30 seconds.
  2. Implement the **Material Surface Sync Contract**: restrict mandatory `README.md` updates strictly to changes in public surfaces (quickstart commands, CLI flags, public API contracts, new principles, repository directory structures). Internal refactoring, private helper changes, and test updates must sync to `knowledge/` (architecture or decisions) instead of churning `README.md`.
  3. Codify **Executable Command Parity**: all commands, test invocations, and script entrypoints documented in `README.md` must be literal, reproducible, shell-agnostic, and guaranteed to succeed without hidden flags or environment variables.
  4. Establish the **Documentation SSOT Triad**: partition documentation into (1) `README.md` (Orientation & Public Surface), (2) `AGENTS.md` / `GUIDELINES.md` (Governance & Invariants), and (3) `knowledge/` (Deep Architecture, AST Map & ADRs).
- **Consequences**:
  - *Positive*: Eliminates unnecessary `README.md` churn; accelerates cold-start agent comprehension from multiple turns to a single 30-second read; guarantees 100% executable setup commands; enforces crisp separation between public docs, governance rules, and deep architectural knowledge.
  - *Trade-offs*: Requires agents to distinguish between public surface changes and internal refactors during Phase 5 documentation sync.

### ADR-012: Automated Cold-Start Parity Gate, Directory Tree Drift Invariant, and Adopter Blueprint (PRINCIPLE-005)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. Even with high-level orientation guidelines, projects often fail to document canonical test commands and runtime prerequisites in `README.md` itself, leaving cold-starting agents to guess test commands or explore multiple files.
  2. As tools, helper scripts, and architecture docs are created, renamed, or refactored, the ASCII directory tree in `README.md` easily drifts, resulting in dead references or phantom script citations.
  3. Documentation parity cannot rely solely on manual vigilance; it requires automated mechanical test gates to prevent documentation rot across refactorings.
- **Decision**:
  1. Add an explicit **⚡ 30-Second Cold-Start Quick Reference** section directly under the title in `README.md`, containing runtime prerequisites, the canonical test command (`python -m unittest discover tests`), and an operational command matrix.
  2. Codify the **Directory Tree & Script Reference Invariant (Tree-Drift Shield)**: every core entrypoint script and top-level directory must be reflected in `README.md`, and all script paths cited in `README.md` must physically exist on disk.
  3. Implement **Automated Cold-Start Parity Testing** in `tests/test_kit.py`: mechanically verify that `README.md` contains runtime prerequisites, the canonical test command, and valid on-disk paths for all cited `scripts/*.py`.
- **Consequences**:
  - *Positive*: Guarantees that any cold-starting agent immediately receives the exact runtime requirements and test commands; mechanically eliminates phantom script references in documentation; shields the project against directory tree drift.
  - *Trade-offs*: None; test execution is purely deterministic and fast (<10ms).

### ADR-013: Whole-Tree Drift Shield, Cold-Start Token Ceiling, and Non-Destructive Adopter Setup (PRINCIPLE-005)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. Testing only `scripts/*.py` in `README.md` leaves the rest of the 19 files and directories in the ASCII tree vulnerable to drift when files in `knowledge/`, `.agents/`, or root are added or renamed.
  2. Unbounded growth of `README.md` leads to context exhaustion on cold start, where an agent consumes a large fraction of its prompt window on turn 1 reading documentation fluff.
  3. Adopting AIKit in existing projects by copying everything (`cp -r portable_agent_kit/*`) risks overwriting the adopter's existing product `README.md`.
- **Decision**:
  1. Implement **Whole-Tree Drift Shield Testing** in `tests/test_kit.py`: parse the entire ASCII tree in `README.md` and assert that 100% of the listed file and directory paths physically exist on disk.
  2. Enforce a **Cold-Start Token Ceiling**: mechanically test that `README.md` remains strictly under 20,000 characters (<5,000 tokens), delegating exhaustive technical details to `knowledge/`.
  3. Formalize **Non-Destructive Adopter Setup**: document Option A (Greenfield) vs. Option B (Existing Project Quick-Merge) in `README.md` and `GUIDELINES.md` so adopters safely adopt governance without destroying existing documentation.
- **Consequences**:
  - *Positive*: Completely eliminates ASCII tree drift; guarantees lean, fast cold starts without prompt bloat; protects adopter documentation during integration.
  - *Trade-offs*: None; automated test overhead is negligible (<15ms).

### ADR-014: Disruption Recovery CLI Ergonomics, Explicit Micro-Staging, and Transient Buffer Hygiene (PRINCIPLE-006)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. Developers and agents previously had to run verbose python one-liners (`python -c "from scripts.disruption_recovery import record_checkpoint; ..."`) to record task progress in `.agents/task_ledger.json`, creating developer friction.
  2. While `--audit` reported interrupted tasks, there was no standardized command to output human- and AI-readable structured guidance on how and where to resume.
  3. When saving progress during long workflows, indiscriminate staging (`git add .`) risks committing unvetted drafts or dangling temporary buffers into git history.
  4. Interrupted atomic writes can leave orphaned `.tmp_*` files that clutter the working tree unnoticed.
- **Decision**:
  1. Expand `scripts/disruption_recovery.py` with first-class CLI commands:
     - `--checkpoint <task_id> --phase <phase> [--phase-num <N>] [--desc <desc>]` to record milestones cleanly.
     - `--resume` to output structured cold-start resumption guidance (task ID, last phase, next phase, modified files, next steps).
  2. Codify the **Explicit Micro-Staging Invariant**: agents must explicitly stage only the files verified for that sub-task rather than using blind `git add .`.
  3. Implement **Transient Buffer Hygiene**: enhance `run_disruption_audit()` to scan for and report dangling `*.tmp_*` buffers.
  4. Enforce the **Non-Breaking Micro-Commit Rule**: commits are strictly gated by passing unit tests (100% pass gate); intermediate progress that does not yet pass tests must be persisted to the task ledger rather than committed to git.
- **Consequences**:
  - *Positive*: Eliminates CLI friction; turns cold-start disruption resumption into a single standardized command; prevents git repository pollution; ensures clean working trees.
  - *Trade-offs*: None; stdlib-only, zero dependencies.

### ADR-015: Disruption CLI Reset & Clean Commands, Git Detection, and Conventional Micro-Commits (PRINCIPLE-006)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. If an in-progress task was abandoned or superseded, developers and agents previously had to manually edit `.agents/task_ledger.json` to clear `active_task`.
  2. When orphaned `*.tmp_*` buffers were identified by audit, manual file deletion commands were required across platforms.
  3. When AIKit is adopted into a folder without git initialized (`git status` fails), `run_disruption_audit()` silently reported a clean state, hiding the missing git tracking.
  4. Micro-milestone commits risked inconsistency if free-form messages like `wip` were used.
- **Decision**:
  1. Add `reset_active_task()` and `--reset [reason]` to `scripts/disruption_recovery.py` to cleanly abandon/clear active tasks in the ledger.
  2. Add `clean_dangling_temp_files()` and `--clean` to `scripts/disruption_recovery.py` to automatically purge orphaned temporary buffers.
  3. Add non-git workspace detection in `run_disruption_audit()` to report `⚠️ Git Inactive: Not a git repository (run 'git init' to enable full tracking)`.
  4. Standardize the **Conventional Micro-Commit Format**: `type(task): [milestone N/M] description`.
- **Consequences**:
  - *Positive*: One-click task abort and buffer cleanup; proactive warning when git is missing; pristine git histories with structured conventional micro-commits.
  - *Trade-offs*: None; 100% standard library.

### ADR-016: Pre-Flight Track C Impact Gating, 4 Blast-Radius Dimensions, Anti-Satisficing Invariant, and Ledger Impact Persistence (PRINCIPLE-007)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. Principle 7 previously lacked a distinct trigger boundary, risking process overhead on read-only queries (Track A) or simple typo fixes (Track B) while being too loose on major engineering refactors (Track C).
  2. The risk assessment question ("How could it harm the project?") was abstract, often leading to generic LLM platitudes rather than concrete technical blast-radius checks.
  3. Quality non-diminution prohibited "substandard or lazy code" but did not mechanically enumerate the classic satisficing shortcuts LLMs take (stubs, `# TODO`, silent exception swallowing, weakened test assertions, UI demotion).
  4. Pre-flight assessments were executed purely "mentally" or in chat, causing rationale, risks, and mitigation designs to be lost upon conversation compaction or power disruption.
- **Decision**:
  1. Anchor the mandatory 4-quadrant impact assessment strictly to **Track C (Engineering/Feature/Refactor)** tasks; Track B scales to a micro-sanity check (zero syntax/link breakage); Track A bypasses the gate.
  2. Codify the **4 Blast-Radius Dimensions**: (1) Contracts & Signatures, (2) Dependency Infiltration, (3) Concurrency & Thread Safety, (4) State Mutation & Schema Drift.
  3. Codify the **Anti-Satisficing Invariant (Zero Lazy Code)** with explicit mechanical prohibitions against `# TODO` placeholders, silent exception swallowing (`except Exception: pass`), assertion tampering, and UI downgrades.
  4. Require clean baseline verification (`git status`) and explicit rollback/recoil preparedness before mutating code.
  5. Expand `scripts/disruption_recovery.py` with optional `--why`, `--risks`, and `--mitigation` flags in `record_checkpoint` and CLI to persist pre-flight impact metadata in `.agents/task_ledger.json` across compactions.
- **Consequences**:
  - *Positive*: Eliminates impulsive LLM coding; provides a concrete 4-point blast-radius checklist; permanently bans LLM shortcuts; preserves pre-flight architectural intent across compactions and disruptions.
  - *Trade-offs*: Adds optional arguments to checkpointing CLI; remains 100% standard library and backward-compatible.

### ADR-017: Scope Ceiling, Type Preservation, 4-Quadrant CLI Symmetry, and Principle 8 Bridge (PRINCIPLE-007 Pass 2)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. While anti-satisficing protects against under-engineering, LLMs frequently fail by over-engineering (speculative architectural rewrites, unsolicited scope creep, and gold-plating).
  2. Bypassing type safety by casting to `Any` or disabling type checkers via `# type: ignore` is a frequent subtle satisficing shortcut that damages type contracts.
  3. The CLI in `scripts/disruption_recovery.py` previously supported `--why`, `--risks`, and `--mitigation`, omitting `--benefits`, creating an asymmetry against the 4-quadrant model.
  4. Conversational output risked ballooning into multi-paragraph essays explaining impact assessments on every task.
  5. Mitigations identified in Principle 7 lacked an explicit bridge to the sub-tasks decomposed in Principle 8.
- **Decision**:
  1. Codify the **Scope Ceiling (Anti-Gold-Plating Invariant)** in Principle 7, restricting changes strictly to the evaluated user goal and direct blast-radius mitigations.
  2. Codify the **Type Preservation Invariant**, explicitly banning `Any` casts and `# type: ignore` suppressions used to bypass type checks.
  3. Complete full 4-quadrant symmetry in `scripts/disruption_recovery.py` by adding `benefits: Optional[str] = None` and `--benefits` / `--benefit` to `record_checkpoint()` and reporting.
  4. Formulate the **Conversational Conciseness Contract** (<6 lines total in chat) to preserve prompt focus and screen real estate while persisting full depth in the disk ledger.
  5. Formally bridge Principle 7 to Principle 8: defensive mitigations directly formulate the hierarchical micro-milestones decomposed in `PRINCIPLE-008`.
- **Consequences**:
  - *Positive*: Perfect balance between preventing laziness and preventing over-engineering; complete 4-quadrant metadata preservation; preserved type safety; ultra-concise chat interactions.
  - *Trade-offs*: None; stdlib-only.

### ADR-018: Dual-Pillar Framework, Top-Down Planning / Bottom-Up Execution, and Milestone Indexing (PRINCIPLE-008)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. Principle 8 previously mixed task planning and data processing into ambiguous terminology, leaving room for monolithic execution bias where agents attempt multi-layer features in a single turn.
  2. Top-down implementation by AI agents frequently produces ghost symbols, broken imports, and hallucinated types because consumer components are written before foundational models exist.
  3. Conventional micro-commits introduced in `PRINCIPLE-006` (`[milestone N/M]`) lacked a formal definition of where $N/M$ originates.
  4. Decomposed sub-tasks were not explicitly required to leave the codebase in an independently testable, non-breaking intermediate state.
- **Decision**:
  1. Codify the **Dual-Pillar Framework**: Pillar A governs agent engineering task workflows (Goal $\rightarrow$ Domains $\rightarrow$ Leaf Units), while Pillar B governs recursive data/file architecture with concrete limits ($D \le 3, K \le 50$).
  2. Codify the **Top-Down Planning, Bottom-Up Execution Invariant**: Plan top-down to map contracts; implement bottom-up (models/primitives first $\rightarrow$ domain services $\rightarrow$ consumers/presentation $\rightarrow$ tests) so symbols physically exist before use.
  3. Establish the **Milestone Indexing Contract**: Hierarchical decomposition directly defines the bounded micro-milestone sequence ($N=1..M$) logged in `.agents/task_ledger.json` and committed incrementally (`PRINCIPLE-006`).
  4. Enforce **Independent Leaf Verifiability**: Every leaf unit must compile and pass tests in isolation without breaking the working tree.
- **Consequences**:
  - *Positive*: Eliminates monolithic execution bias; guarantees clean runnable intermediate states; prevents ghost imports; harmonizes planning with conventional micro-commits.
  - *Trade-offs*: None; conceptual and behavioral alignment.

### ADR-019: Bounded Milestone Horizon, Dynamic Re-Decomposition, and Single-Domain Leaf Atomicity (PRINCIPLE-008 Pass 2)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. Guarding only against monolithic bias risks driving LLMs into the opposite trap: micro-task over-fragmentation ($M > 10$ with 1-line commits), generating massive token churn and commit noise.
  2. Unanticipated discoveries during mid-execution (upstream bugs, dependency limits, schema conflicts) frequently cause agents to either blindly push ahead with broken assumptions or wipe out the entire plan.
  3. Decomposed leaf milestones previously lacked a domain-scoping rule, risking diffuse edits across unrelated subsystems in a single commit.
  4. Recursive data traversal in Pillar B lacked a deterministic fallback when hitting the depth ceiling ($D_{\max}=3$).
- **Decision**:
  1. Codify the **Bounded Milestone Horizon**: Target $2 \le M \le 6$ cohesive milestones for standard Track C tasks. If $M > 6$, decompose into multiple distinct user features.
  2. Codify the **Dynamic Re-Decomposition Protocol**: When unanticipated blockers or gaps emerge, agents pause forward progression, refine sub-tasks in `.agents/task_ledger.json`, adjust $M'$, and resume monotonically without discarding completed progress.
  3. Enforce **Single-Domain Leaf Atomicity**: Each leaf unit must focus on a single architectural domain or interface boundary, enabling clean micro-staging.
  4. Specify **Base-Case Summary Aggregation**: When tree recursion hits $D_{\max}$ or batch caps, roll child items up into a structured summary node rather than failing or recursing unbounded.
- **Consequences**:
  - *Positive*: Protects against both monolithic bias and micro-task over-fragmentation; provides a clear, adaptive protocol for mid-task discoveries; ensures focused git commits.
  - *Trade-offs*: None; stdlib-only.

### ADR-020: Canonical 4-Layer Architecture, Dependency Injection, and Explicit Interface Contracts (PRINCIPLE-009)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. Principle 9 previously stated high-level modularity goals ("decoupled presentation and business logic", "abstract provider/service interfaces") without specifying concrete architectural layer boundaries or dependency direction.
  2. Without clear layer definitions, AI agents frequently mix CLI argument parsing, file I/O, business validation, and API calls within single files, leading to monolithic, untestable scripts.
  3. LLMs routinely construct generic `utils.py` or `helpers.js` "junk drawer" files that accumulate unrelated functions with loose cohesion and high coupling.
  4. Services often instantiate concrete infrastructure adapters directly inside domain logic, defeating test isolation and mockability.
  5. Circular dependencies and cross-module mutations of private `_attributes` degrade maintainability.
- **Decision**:
  1. Codify the **Canonical 4-Layer Architecture**: (1) Presentation (CLI/UI/API), (2) Service (orchestration & workflows), (3) Domain/Model (pure business entities & invariants), and (4) Infrastructure/Adapter (external I/O & tools).
  2. Enforce the **Anti-Junk-Drawer Invariant**: Generic `utils.py` files are strictly prohibited. Helpers must be co-located with their domain or grouped into focused, single-purpose utility modules (`date_utils.py`, `string_parsers.py`).
  3. Codify the **Explicit Interface Contracts Invariant**: All pluggable provider/adapter boundaries must declare explicit contracts using native typing constructs (`abc.ABC` or `typing.Protocol`).
  4. Enforce **Dependency Injection & Inversion (DIP)**: Domain services must receive adapters via constructor or factory injection, enabling deterministic in-memory mock testing (`PRINCIPLE-014`).
  5. Enforce **Unidirectional Dependency Flow**: Dependencies must flow strictly inward: Presentation $\rightarrow$ Service $\rightarrow$ Domain $\leftarrow$ Infrastructure. Circular imports are banned.
  6. Enforce **Encapsulation & Boundary Integrity**: Modules interact strictly through declared public contracts, forbidding external mutation of `_private` attributes.
- **Consequences**:
  - *Positive*: Crystal-clear structural organization; complete test isolation through constructor DI; clean domain separation; prevents spaghetti code and junk-drawer bloat.
  - *Trade-offs*: Requires explicit typing contracts and constructor wiring; well worth the testability and architectural cleanliness.

### ADR-021: Scalable Layering, Narrow Role Protocols, Pluggable Registries, and Zero-Config DI (PRINCIPLE-009 Pass 2)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. While ADR-020 established the canonical 4-layer architecture, agents frequently over-engineered small scripts (<300 lines) by generating 4 nested directories and 8+ files of folder bloat.
  2. Abstract interfaces created by LLMs tended to become "fat" monolithic classes (10+ methods), forcing test mocks to implement dozens of dummy stub methods and violating the Anti-Satisficing Invariant (`PRINCIPLE-007`).
  3. Pluggable adapters were often wired using fragile hardcoded `if/elif` branching in service logic, violating the Open-Closed Principle (OCP).
  4. Dependency injection frameworks add external dependency overhead, while requiring callers to manually wire adapters damages one-click usability (`PRINCIPLE-011`).
  5. Cross-layer data leakage occurred when mutable domain or database state was passed directly to presentation layers.
- **Decision**:
  1. Codify **Scalable Layering (Anti-Boilerplate Invariant)**: The 4 layers represent logical boundaries; for small utilities (<300 lines), keep layers logically separated within a single module rather than generating excessive folder bloat. Multi-directory trees are reserved for larger systems.
  2. Enforce **Interface Segregation & Narrow Role Protocols**: Pluggable interfaces must be fine-grained and role-oriented ($1 \le \text{methods} \le 5$). Never force test mocks to implement unused stub methods.
  3. Enforce **Pluggable Registry & Open-Closed Extensibility (OCP)**: Dynamically register backends and adapters via registries/factories (`@register_adapter` or lookup table) rather than hardcoded `if/elif` branching in domain services.
  4. Enforce **Pure-Stdlib Dependency Injection & Zero-Config Usability**: Use standard-library constructor injection with default factory fallbacks (`adapter: Protocol | None = None`), enabling instant one-click execution with 100% in-memory test mockability without third-party DI containers.
  5. Enforce **Boundary Immutability via Immutable DTOs**: Data crossing layer boundaries must use immutable DTOs (`dataclass(frozen=True)` or `NamedTuple`), preventing state leakage and side-effect mutations.
- **Consequences**:
  - *Positive*: Eliminates boilerplate bloat for small tools; eliminates dummy stub methods in unit tests; enables zero-modification provider pluggability; reconciles pure DI with zero-friction usability; protects domain state integrity.
  - *Trade-offs*: None; stdlib-only.

### ADR-022: Stream-First Processing, Non-Blocking Event-Loop Hygiene, RAII Cleanup, and Lazy Imports (PRINCIPLE-010)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. Principle 10 previously overlapped with Principle 12 by mixing token budgeting and prompt engineering into computational runtime optimization.
  2. AI agents frequently introduce $O(N^2)$ quadratic scanning bottlenecks and buffer entire multi-hundred megabyte files into memory with `.read()`.
  3. Blocking synchronous I/O executed on async event loops or GUI threads causes event-loop starvation and application freezing.
  4. Failure to use context managers (`with`) causes operating system file descriptor leaks on Windows/Linux, and unbounded caches leak memory in daemon processes.
  5. Top-level imports of optional third-party packages ruin cold startup latency and break zero-install usability (`PRINCIPLE-011`).
  6. Slow unit tests tempt developers and agents to bypass verification gates.
- **Decision**:
  1. Partition token economics strictly to `PRINCIPLE-012`, focusing `PRINCIPLE-010` purely on computational runtime, I/O, memory, and concurrency.
  2. Enforce **Algorithmic Stream Processing ($O(1)$ Auxiliary Memory)**: Use $O(1)$ set/dict lookups and generator pipelines (`yield`) to stream unbounded files and datasets without memory buffering.
  3. Enforce **Non-Blocking Concurrency & Thread Offloading**: Strictly ban blocking I/O on async event loops and GUI threads; offload to `asyncio.to_thread()` or worker pools with thread-safe locks (`threading.Lock`).
  4. Enforce **Deterministic Resource Reclamation (RAII)**: Require context managers (`with`) or explicit try/finally for all OS resources; enforce bounds on in-memory caches.
  5. Enforce **Zero-Weight Baseline & Lazy Imports**: Run core logic on stdlib primitives (<100ms startup); import optional external packages lazily inside adapter methods.
  6. Enforce **Sub-Second Test Performance Gate**: Keep the full unit test suite running under 1 second (<1s) by eliminating artificial delays (`time.sleep()`).
- **Consequences**:
  - *Positive*: Eliminates UI freezes, memory leaks, file descriptor leaks, quadratic slowdowns, and cold-start import lag; clarifies boundary between Principles 10 and 12; guarantees sub-second test feedback.
  - *Trade-offs*: None; pure standard library practices.

### ADR-023: Subprocess Timeout Gating, Measurement-Driven Concurrency, Batch I/O Coalescing, and Ring-Buffer State (PRINCIPLE-010 Pass 2)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. AI agents often invoke external tools and commands via `subprocess.run()` without explicit timeouts, risking permanent deadlocks if child processes hang.
  2. Spawning unbounded child processes causes process table (PID) exhaustion and OS-level thrashing.
  3. LLMs routinely apply speculative multithreading to sub-20ms micro-tasks, resulting in context-switch overhead that slows down execution while introducing race conditions.
  4. Performing atomic writes (`flush` + `os.fsync` + `os.replace`) in tight loops causes severe disk I/O thrashing.
  5. Background daemons, watchers, and monitors frequently accumulate unbounded event logs and diffs, leading to process memory creep.
  6. Heavy imports in CLI entrypoints inflate cold startup times beyond acceptable responsiveness thresholds.
- **Decision**:
  1. Enforce **Subprocess Timeout Gating & Bounded Concurrency**: Require explicit timeouts (`timeout=30`) on all subprocess calls and bound parallel process execution ($K \le \text{os.cpu\_count()}$).
  2. Codify the **Measurement-Driven Concurrency (Profile-Before-Optimizing Invariant)**: Never introduce multithreading or multiprocessing for tasks whose single-threaded baseline completes in under 20ms.
  3. Enforce **Batch I/O Coalescing (Write-Coalescing Invariant)**: Coalesce high-frequency mutations in memory before committing atomic transactions, eliminating tight-loop `fsync` bottlenecks.
  4. Enforce **Bounded Daemon Working State (Ring Buffer Hygiene)**: Require long-running daemons and monitors to use bounded ring buffers (`collections.deque(maxlen=N)`) or bounded caches (`maxsize=N`) for constant $O(1)$ memory consumption.
  5. Enforce **Cold Startup Latency Budget (<100ms)**: Keep CLI entrypoint startup under 100ms by restricting top-level imports to lightweight stdlib modules and loading domain modules lazily.
- **Consequences**:
  - *Positive*: Eliminates process deadlocks and zombie storms; prevents premature multithreading overhead; eliminates disk thrashing from unbatched atomic writes; guarantees leak-free daemon operation and sub-100ms CLI startup.
  - *Trade-offs*: None; pure standard library practices.

### ADR-024: Pure-Stdlib Core, Self-Bootstrapping Workspace, Zero-Crash Config, and Headless Parity (PRINCIPLE-011)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. AI-generated code frequently crashes on initial launch due to unhandled `KeyError` exceptions when expected environment variables are missing.
  2. Missing directories (e.g. `.agents/`, `logs/`, `data/`) cause `FileNotFoundError` crashes instead of self-initializing default scaffolds.
  3. Excessive external package requirements in `requirements.txt` cause onboarding friction and build failures on clean machines or Windows environments.
  4. Interactive terminal prompts (`input()`) cause permanent deadlocks when scripts run in headless AI subagents, IDE extensions, or CI/CD pipelines.
  5. Cryptic bare exception tracebacks leave users and AI agents confused about how to resolve runtime failures.
- **Decision**:
  1. Enforce **Pure-Stdlib Clone-and-Run Baseline**: Core entrypoints and unit test suites must run immediately after `git clone` using standard library primitives alone. Third-party dependencies are strictly optional plugins.
  2. Enforce **Self-Bootstrapping Workspace**: Applications must auto-create missing directories and default configuration states on launch.
  3. Enforce **Zero-Crash Missing Config Protocol**: Access environment variables safely via `os.getenv()` with mock/dry-run fallbacks; exit cleanly with actionable advice if credentials are mandatory.
  4. Enforce **Non-Interactive & Headless Parity**: Default to non-interactive mode when `not sys.stdin.isatty()`; provide `--yes` / `--batch` flags and never hang on stdin.
  5. Enforce **Actionable Remediation Triad**: User-facing errors must present (1) What happened, (2) Why it happened, and (3) How to fix it with an exact command.
  6. Enforce **Idempotent Health Diagnostics (`doctor` pattern)**: Provide an explicit check command (`--audit` / `--doctor`) to verify environment and ledger health.
- **Consequences**:
  - *Positive*: True one-click usability; zero cold-start crashes; safe headless execution for AI agents; crystal-clear actionable error messages.
  - *Trade-offs*: None; pure standard library practices.

### ADR-025: Explicit Mode Transparency, Zero-Prompt Auto-Init, Polyglot Shell Parity, and Deterministic Exit Codes (PRINCIPLE-011 Pass 2)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. While ADR-024 established graceful fallbacks, silent mock execution created a "phantom success" anti-pattern where users or calling agents assumed real mutations occurred when in fact simulated operations ran.
  2. First-run interactive configuration wizards asking multiple terminal questions caused automated AI subagent runs to deadlock.
  3. Commands and documentation frequently broke across platforms due to POSIX-specific shell syntax (`export`, `./run.sh`) or hardcoded path separators.
  4. Non-standard or ambiguous exit codes prevented parent processes and subagents from reliably determining execution outcomes.
  5. The absence of built-in sample fixtures created an external data dependency barrier that delayed first-run verification.
- **Decision**:
  1. Enforce **Explicit Mode Transparency (Anti-Phantom-Success Invariant)**: Prominently signpost all mock, dry-run, or fallback modes (`[INFO] OFFLINE MOCK MODE`). Mutating operations requiring real credentials must fail-fast with clean diagnostic exits.
  2. Enforce **Zero-Prompt Autonomous Initialization**: First-run routines select sensible, secure defaults automatically without prompting console questions; interactive wizards must be strictly opt-in (`--interactive` or `-i`).
  3. Enforce **Cross-Platform Polyglot Command & Path Parity**: Use portable standard-library invocations (`python -m <module>` or `sys.executable`) and `pathlib.Path` across Windows, macOS, and Linux without shell-specific assumptions.
  4. Enforce **Deterministic Exit Code Contract**: Strictly adhere to standard POSIX-compliant exit semantics (`0` clean success, `1` operational failure, `2` CLI argument misuse or invalid syntax).
  5. Enforce **Built-in Self-Demonstrating Fixtures**: Systems must embed minimal self-demonstrating fixtures or demo commands (`--demo`) enabling verified execution in under 10 seconds without external data dependencies.
- **Consequences**:
  - *Positive*: Eliminates deceptive silent mock successes; prevents interactive console deadlocks; ensures identical cross-platform behavior; standardizes exit codes for robust machine orchestration; achieves 10-second verification.
  - *Trade-offs*: None; pure standard library practices.

### ADR-026: Bounded Prompt Ceilings, Schema-First Contracts, Relative-Path Serialization, and TPM Rate Pacing (PRINCIPLE-012 Pass 1)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. Unbounded file ingestion and mega-diff dumps exhaust AI context windows, degrading model reasoning, causing "lost-in-the-middle" amnesia, and triggering expensive token burn.
  2. Multi-turn system prompts and few-shot examples often suffer from conversational fluff and narrative filler, which dilutes instruction following compared to compact schema contracts.
  3. Absolute paths repeated across prompt injections and ledger states waste up to 70% of serialization overhead across deeply nested repository structures.
  4. Rapid successive model or tool API invocations without rate pacing trigger HTTP 429 (Too Many Requests) exceptions and cascade into workflow halts.
  5. Over-engineering with heavy enterprise boilerplate, ceremonial class hierarchies, and unvetted micro-dependencies inflates repository size and maintenance burden.
- **Decision**:
  1. Enforce **Bounded Prompt Payload Ceilings & AST Slicing**: Dynamic context payloads injected into prompts must target <4,000 tokens (<16,000 characters). Full-file dumps are replaced by AST symbol digests (`knowledge/codebase_map.md`) and targeted line slices (<100 lines).
  2. Enforce **Information-Dense Prompt Architecture (Anti-Fluff Invariant)**: High information-to-token ratio; eliminate conversational pleasantries; prioritize terse schema contracts and structured constraints over multi-page narrative instructions or few-shot examples.
  3. Enforce **Compact Schema & Relative-Path Serialization**: Tool outputs, prompt schemas, and ledger records must use compact JSON/YAML and repository-relative paths (`./src/main.py`), trimming up to 70% of path token bloat.
  4. Enforce **Adaptive Token-Aware Rate Pacing & Jittered Exponential Backoff**: Track client-side tokens-per-minute (TPM) consumption; proactively pace rapid bursts; implement jittered exponential backoff on HTTP 429 errors.
  5. Enforce **High-Leverage Standard Library Architecture (Anti-Code-Bloat Invariant)**: Leverage Python/Node standard library tools (`dataclasses`, `pathlib`, `typing`, `http.client`) over heavy external dependencies; keep implementations concise and maintainable.
- **Consequences**:
  - *Positive*: Maximizes model attention by eliminating context dilution; reduces token expenditure by ~70% on paths and payloads; prevents HTTP 429 rate-limit deadlocks; keeps codebases lean and maintainable.
  - *Trade-offs*: None; pure discipline in token budgeting and lean stdlib design.

### ADR-027: Prompt Cache Prefix Alignment, Bounded Tool Outputs, Circuit Breakers, and Syntactic Density (PRINCIPLE-012 Pass 2)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. Frontier LLM inference models (Claude, Gemini, OpenAI) support prompt caching (prefix caching) that cuts input token costs by 80–90% and reduces latency by 5–10x. However, injecting volatile timestamps, random session IDs, or shifting ledger states into prompt headers constantly thrashes the cache.
  2. Multi-turn agent executions frequently append raw tool outputs (massive git diffs, verbose build outputs, un-sifted grep searches), dumping thousands of irrelevant tokens directly into the context window and precipitating attention degradation ("lost-in-the-middle").
  3. Output tokens cost 3–5x more than input tokens; free-form conversational echoing and verbose thought preambles slow execution and inflate billing.
  4. Autonomous subagent execution loops without strict spend ceilings risk entering runaway retry death spirals, exhausting context and consuming excessive API quotas.
  5. Generating overly ceremonial boilerplate code (e.g., enterprise abstract factories, superfluous wrappers) creates a permanent token penalty on all future AI agents reading the codebase.
- **Decision**:
  1. Enforce **Prompt Cache Prefix Alignment (Cache-Friendly Invariant)**: Structurally partition prompt payloads into a deterministic frozen prefix (system instructions, rules, schemas $\ge 1,024$ tokens) and a volatile dynamic tail. Guarantee $\ge 80\%$ prompt cache hit rates across multi-turn sessions.
  2. Enforce **Tool Output Frugality & Bounded Diff Slicing (Anti-Mega-Log Invariant)**: Scope unified diffs strictly to changed hunks with $\le 3$ lines of surrounding context; default test and build runners to quiet/summary modes; cap search/grep results to $\le 50$ matches.
  3. Enforce **Output Token Frugality & Terse Schema Generation**: Require models to produce compact typed data schemas (JSON Schema / dataclasses) in automated orchestration; cap conversational status reports to $\le 15$ lines without polite echoing.
  4. Enforce **Token Budget Ceilings & Runaway Circuit Breakers (Anti-Death-Spiral Invariant)**: Autonomous agent loops and background tasks must define hard token and step ceilings ($K$ turns); budget breaches trip a circuit breaker, checkpoint state to `.agents/task_ledger.json`, and pause cleanly for human input.
  5. Enforce **Lean Syntactic Density & Anti-Premature-Abstraction**: Code produced by AI assistants must prioritize high syntactic density and standard-library leverage (`dataclasses`, `pathlib`, `itertools`), avoiding ceremonial enterprise bloat to keep the codebase token footprint permanently lean for downstream AI reasoning.
- **Consequences**:
  - *Positive*: Maximizes provider prompt cache hit rates ($\ge 80\%$), drastically reducing API costs and latency; shields conversational context from tool output pollution; provides financial guardrails against runaway agent loops; keeps codebase token footprints minimal.
  - *Trade-offs*: None; pure discipline in prompt structuring, tool output filtering, and idiomatic coding.

### ADR-028: Cross-Platform Atomic Replace Retries, Advisory Locking, Dual-Slot Shadow Backups, and Multi-File Staging (PRINCIPLE-013 Pass 1)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. On Windows systems and virtualized filesystems, `os.replace` frequently encounters transient lock contention (`PermissionError: [WinError 32]`) when background file watchers, virus scanners, or IDE indexers momentarily access the target file.
  2. Parallel autonomous subagents or concurrent CLI invocations mutating persistent state (such as `task_ledger.json`) risk last-write-wins collisions and silent progress clobbering without concurrency controls.
  3. While quarantining corrupted JSON files prevented runtime crashes, falling back immediately to an empty dictionary discarded task history and completed checkpoint memory.
  4. Interrupted atomic writes abandoned orphaned temporary files (`*.tmp_*`) across the repository, littering git status and cluttering workspace hygiene.
  5. Multi-file synchronization operations (e.g., updating multiple IDE rule targets) could be severed midway, resulting in partial split-brain discrepancies.
- **Decision**:
  1. Enforce **Lock-Contention Retry Loops on Atomic Replace**: Wrap `os.replace` in a bounded retry loop ($3 \le \text{retries} \le 5$ with exponential backoff) to withstand transient Windows/AV lock contention without failing.
  2. Enforce **Inter-Process Advisory Locking (Anti-Race Invariant)**: Require cooperative advisory file locks (`path.with_suffix('.lock')`) with bounded timeouts ($2\text{s}$–$5\text{s}$) and automatic stale-lock expiration (>30s) around read-modify-write state lifecycles.
  3. Enforce **Dual-Slot Shadow Snapshots & Resilient Rollback (`.bak` Fallback)**: Rotate the verified existing file into a shadow backup (`.bak`) before replacement; on launch, corrupted artifacts (`*.corrupt_*`) are quarantined and state is recovered from `.bak` before defaulting to empty state.
  4. Enforce **Multi-File Staging & Transactional Coherence**: Complex multi-file synchronizations must stage all target buffers completely in temporary files and validate syntax prior to executing rapid sequential atomic replacements.
  5. Enforce **Orphaned Buffer Sanitation**: Startup routines and disruption audits sweep and purge abandoned temporary files (`*.tmp_*`) left by interrupted dead processes.
- **Consequences**:
  - *Positive*: Eliminates Windows atomic replace crashes; prevents multi-agent write clobbering; preserves task memory through shadow backup recovery; keeps the repository free of temporary file garbage; guarantees all-or-nothing consistency across multi-file syncs.
  - *Trade-offs*: None; pure standard library implementation (`shutil`, `contextlib`, `os`).

### ADR-029: Storage Headroom Guards (ENOSPC), Forward Schema Migrations, Signal Drains, and Chaos Verification (PRINCIPLE-013 Pass 2)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. Low disk space or high-volume write bursts can cause writes to fail mid-stream with `OSError: [Errno 28] No space left on device` (`ENOSPC`), potentially leaving files truncated or corrupted.
  2. Over time, schemas evolve; restoring an older `.bak` shadow snapshot from prior versions could crash modern deserializers if required fields or structures differ.
  3. Abrupt process aborts via `Ctrl+C` (`SIGINT`) or IDE termination (`SIGTERM`) risk dropping in-flight working memory that was not yet flushed to the persistent ledger.
  4. Running on read-only container volumes or permissions-restricted directories could crash tools on startup rather than gracefully operating in degraded ephemeral memory mode.
  5. Crash resilience mechanisms require continuous automated verification under hostile fault conditions (0-byte truncation, severed streams) to prevent silent regressions.
- **Decision**:
  1. Enforce **Storage Headroom Pre-Check (ENOSPC Resilience)**: Inspect storage via `shutil.disk_usage` ($\ge 10\text{MB}$) before initiating atomic writes; halt cleanly with actionable diagnostic if space is exhausted.
  2. Enforce **Forward-Compatible Schema Migration**: State loaders must apply idempotent schema migration transforms (`migrate_ledger_schema`) to legacy or restored snapshots to ensure all required fields exist.
  3. Enforce **Signal-Aware Memory Drain & Read-Only Fallback**: Intercept termination signals (`SIGINT`/`SIGTERM`) to flush memory state and release lockfiles before exiting; degrade gracefully to ephemeral in-memory state on read-only filesystems.
  4. Enforce **Continuous Power-Loss Fault-Injection Verification**: Automated tests must inject 0-byte truncations, corrupted JSON streams, and concurrent lock contention to verify 100% deterministic self-healing.
- **Consequences**:
  - *Positive*: Protects systems against storage exhaustion panics; ensures recovered snapshots never crash modern code; guarantees clean in-flight memory persistence during user aborts; proves crash resilience through continuous automated fault injection.
  - *Trade-offs*: None; pure standard library practices.

### ADR-030: Test Sanctity Invariant, Hermetic Sub-Second Isolation, and Self-Explaining Diagnostics (PRINCIPLE-014 Pass 1)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. In automated AI pair programming and autonomous subagent loops, a common failure pattern is "test satisficing" (test mutilation): modifying, weakening, skipping, or deleting failing assertions simply to produce a clean exit code `0` rather than repairing the underlying defect.
  2. Slow, sleep-dependent unit tests (`time.sleep`) create non-deterministic test failures across varied execution environments and destroy rapid feedback loops.
  3. Tests writing to relative working paths leak temporary files into the repository, polluting `git status` and causing false disruption alerts.
  4. Bare assertions (e.g. `assertTrue(val)`) lack contextual failure messages, forcing calling agents to waste multiple turns guessing why a test failed.
  5. Focusing solely on happy-path line coverage leaves boundary and hostile inputs (empty strings, `None`, 0-byte files, malformed types) untested.
- **Decision**:
  1. Enforce **Test Sanctity Invariant (Anti-Regression Masking)**: Test assertions represent immutable contractual truth; repairing regressions by weakening, skipping (`@unittest.skip`), or deleting assertions is strictly prohibited.
  2. Enforce **Hermetic Isolation & Zero Flakiness (<1s Gate)**: All unit tests must execute in under 1 second total ($T_{\text{suite}} < 1\text{s}$), run deterministically, avoid external network calls, and prohibit wall-clock sleeps in favor of mock clocks and deterministic ticks.
  3. Enforce **Pristine Working Tree Invariant (Zero Leaked Artifacts)**: File I/O tests must execute strictly within ephemeral temporary sandboxes (`tempfile.TemporaryDirectory()`); test execution must leave `git status --porcelain` 100% clean.
  4. Enforce **Self-Explaining Assertions & Diagnostics**: Assertions must provide explicit descriptive failure messages with expected vs. actual context, allowing agents to diagnose failures in a single turn.
  5. Enforce **Hostile Boundary & Edge-Case Hardening**: Mandate test coverage for boundary inputs (empty collections, `None` arguments, 0-byte files, schema variations, and malformed types).
- **Consequences**:
  - *Positive*: Guarantees that AI agents fix real defects rather than weakening tests; provides sub-second deterministic feedback; keeps the working tree pristine; enables 1-turn defect localization.
  - *Trade-offs*: None; pure testing discipline.

### ADR-031: RAII Fixture Reversion, Anti-Tautological Observable Contracts, and Red-Green Defect Pinning (PRINCIPLE-014 Pass 2)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. Tests that modify global interpreter state (`os.environ`, `sys.argv`, logger levels, or singleton registries) without atomic cleanup cause order-dependent test failures (leaky fixtures), wasting agent turns on non-existent bugs.
  2. Over-mocking internal helper methods creates tautological "mock echo" tests that achieve high line coverage while testing zero real domain logic, failing when internal implementations are refactored.
  3. When resolving reported defects, agents often apply speculative fixes without first establishing a reproducible failing test, risking recurrent regressions.
  4. Testing often ignores negative error-handling branches (`except` blocks, custom error types, exit codes, and diagnostic messages), causing production code to crash on malformed inputs.
  5. Non-deterministic tests with unseeded pseudorandom data intermittently fail, eroding AI agent autonomy and prompting unnecessary code changes.
- **Decision**:
  1. Enforce **RAII Fixture Reversion (Anti-Pollution Invariant)**: Tests modifying global state (`os.environ`, `sys.argv`, singletons) must guarantee bit-for-bit restoration via `self.addCleanup()` or context managers, ensuring tests pass in any execution order.
  2. Enforce **Observable Contracts Over Mock Echoes (Anti-Tautological Invariant)**: Assert outward observable behavior, return values, state transitions, and exception boundaries rather than internal mock call counts (`assert_called_once`); prefer lightweight in-memory instances over excessive mocking.
  3. Enforce **Red-Green Defect Pinning**: Before resolving a reported bug or defect, write a reproducing unit test that fails on the defect (Red), then verify that the fix makes it pass (Green).
  4. Enforce **Hostile & Negative Path Parity**: Mandate coverage for negative and error paths (expected exception classes, exit codes, and user-facing diagnostic messages).
  5. Enforce **Zero Flakiness Tolerance & Seed Pinning**: Tests using pseudorandom generation must pin their seeds (`random.seed(42)`). Flaky tests are treated as Sev-1 blocking defects.
- **Consequences**:
  - *Positive*: Eliminates order-dependent test flakiness; prevents tautological tests; guarantees that bug fixes are verified and permanently shielded against regressions; ensures error handling is thoroughly validated.
  - *Trade-offs*: Requires disciplined test fixture teardown and explicit negative path test design.

### ADR-032: Supervised Process Lifecycles, Headless Display Parity, and Dual-Track Chaos Dogfooding (PRINCIPLE-015 Pass 1)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. Headless unit tests in isolated vacuums fail to detect real-world execution bugs (event loop freezing, unhandled callback exceptions, routing failures, or exit code mismatches).
  2. Spawning background dev servers or subshells during dogfooding without supervised process trees frequently leaks zombie processes and locks network ports (`EADDRINUSE`).
  3. Running desktop GUI applications in headless environments (CI runners, containers, remote subshells) without display fallback crashes the verification harness.
  4. Cheating operational verification by executing `--help` alone conceals critical runtime failures across data lifecycles.
  5. Uncontrolled operational testing poses a risk of mutating host user directories or polluting the workspace repository.
- **Decision**:
  1. Enforce **Headless Parity & Virtualized Display Loops**: Desktop GUI dogfooding must support virtualized displays (`xvfb`/offscreen) and bounded timeouts ($T \le 10\text{s}$) with automated window destruction.
  2. Enforce **Supervised Process Tree Lifecycles (RAII Process Cleanup)**: All server processes and child daemons must execute within managed supervisors or RAII context managers that guarantee recursive child process termination (`SIGTERM` followed by `SIGKILL`) on exit or assertion failure.
  3. Enforce **Dual-Track Dogfooding (Golden Path + Hostile Chaos Injection)**: Testing `--help` alone is forbidden; every dogfood run must execute a complete golden workflow (create, modify, retrieve) and at least one hostile perturbation (simulated SIGINT interrupt, invalid payload, malformed data stream).
  4. Enforce **Strict Ephemeral Safety Jail (`SANDBOX_ROOT`)**: File modifications must execute strictly within an isolated ephemeral directory (`SANDBOX_ROOT`), asserting zero host file mutations and bit-for-bit clean `git status`.
  5. Enforce **Deterministic Domain Exit Contracts**: Verify concrete domain success criteria: zero unhandled tracebacks in stderr, zero browser console errors, valid API schemas, and clean exit codes.
- **Consequences**:
  - *Positive*: Guarantees that built applications function end-to-end in real environments; eliminates background zombie processes and port collisions; protects user files with strict sandboxing; prevents superficial verification cheating.
  - *Trade-offs*: None; pure operational engineering discipline.

### ADR-033: Platform-Portable Process Teardown, Stdin Parity, and Web Hydration Assertions (PRINCIPLE-015 Pass 2)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. Interactive CLI prompts block indefinitely in subshells waiting for human keystrokes, deadlocking autonomous agents.
  2. Background process trees on Windows spawned via shell commands survive parent process termination, leaving zombie node/python processes holding network ports and locks.
  3. Web applications can return HTTP 200 on the initial HTML shell while client-side React/Vue rendering crashes with a white screen due to unhandled bundling or runtime exceptions.
  4. Dogfooding database operations directly against workspace storage pollutes the repository and creates collision errors in subsequent runs.
- **Decision**:
  1. Enforce **Non-Interactive Stdin Parity & EOF Safety**: Interactive CLI commands must support non-interactive bypass flags (`--yes`/`--headless`) and gracefully handle closed `stdin` streams (`< /dev/null`) without deadlocks or unhandled exceptions.
  2. Enforce **Platform-Portable Process Tree Teardown**: Dogfood supervisors must recursively terminate child processes across Windows (`taskkill /F /T /PID`) and POSIX (`os.killpg(pid, signal.SIGKILL)`), guaranteeing zero leaked background daemons.
  3. Enforce **Web DOM Mount & Client-Side Hydration Assertions**: Web app dogfooding must assert rendered children in the root container (`#root`/`#app`) and zero browser console errors (`console.error`), beyond bare HTTP 200 status codes.
  4. Enforce **Hermetic Ephemeral State & Storage Sandboxing**: Operational tests must use in-memory databases (`sqlite:///:memory:`) or ephemeral databases in `SANDBOX_ROOT`, wiped upon teardown with bit-for-bit clean `git status`.
- **Consequences**:
  - *Positive*: Eliminates interactive prompt deadlocks; prevents orphaned background workers across all operating systems; catches client-side white screens; protects workspace databases from state pollution.
  - *Trade-offs*: None; robust cross-platform execution.

### ADR-034: Atomic Code-Doc Pairing, Monotonic ADR Hygiene, and Automated Link Integrity Shield (PRINCIPLE-016 Pass 1)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. Modifying code, service interfaces, or schemas without synchronously updating `knowledge/` causes silent knowledge drift, leading incoming agents to hallucinate stale APIs.
  2. Overwriting or deleting past ADRs destroys historical architectural rationale, causing agents to re-introduce previously rejected antipatterns.
  3. Broken relative Markdown links in documentation disrupt cold-start navigation and cause agent tool call failures.
  4. Large unstructured documentation files burn prompt context tokens when agents only require specific section slices.
- **Decision**:
  1. Enforce **Atomic Code-and-Doc Pairing (Anti-Drift Invariant)**: Service signatures, schemas, and architectural conventions must update synchronously with `knowledge/` documents in the same commit.
  2. Enforce **Monotonic Append-Only ADR Register**: Decisions in `knowledge/decisions.md` are strictly immutable; design pivots append new sequential ADRs marking predecessors as superseded.
  3. Enforce **Strict AST Syntax Gating**: `scripts/update_knowledge_base.py` parses the codebase AST, validates zero syntax errors, and updates `codebase_map.md`.
  4. Enforce **Automated Link Integrity Shield**: `scripts/update_knowledge_base.py` programmatically verifies that all relative file links in `knowledge/INDEX.md` physically resolve on disk.
  5. Enforce **Slice-View Heading Hygiene**: Markdown documents must use structured section headings (`##`, `###`) to enable targeted single-call grep line slices (<100 lines).
- **Consequences**:
  - *Positive*: Eliminates knowledge drift; preserves complete architectural history; guarantees 100% working document links; keeps agent context usage lean and slice-targeted.
  - *Trade-offs*: None; pure documentation and governance hygiene.

### ADR-035: Codebase Map Freshness Gate, SSOT Schema Partitioning, and Polyglot Architecture (PRINCIPLE-016 Pass 2)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. Agents frequently edit code and pass unit tests but forget to execute `scripts/update_knowledge_base.py`, leaving `knowledge/codebase_map.md` stale and desynchronized.
  2. Copy-pasting schema definitions into multiple documentation files (`architecture.md`, `services.md`, `data_models.md`) causes cross-document synchronization drift when schemas change.
  3. Schemas in `data_models.md` that lack explicit version numbers or migration transformer references risk breaking legacy user state upon deserialization.
  4. Adopter repositories in non-Python languages need clear structural guidance on implementing knowledge bases.
- **Decision**:
  1. Enforce **Deterministic Codebase Map Freshness Gate**: Unit tests in `tests/test_kit.py` must assert that the on-disk `knowledge/codebase_map.md` bit-for-bit matches `generate_codebase_map()`, mechanically preventing un-synchronized symbol maps from being committed.
  2. Enforce **Modular SSOT Schema Partitioning**: Prohibit duplicating schemas across files; `data_models.md` is the sole Single Source of Truth for schemas and DTOs, cross-referenced via hyperlinks.
  3. Enforce **Versioned Schema Specifications & Migration Rules**: All persistent schemas in `data_models.md` must declare `schema_version`, nullability defaults, and backward-compatible migration transformers.
  4. Enforce **Universal Polyglot Knowledge Architecture**: The 7-document layout is standard across all software ecosystems (TypeScript, Go, Rust, Python).
- **Consequences**:
  - *Positive*: Mechanically prevents stale codebase maps via automated tests; eliminates contradictory documentation through SSOT partitioning; guarantees backward-compatible schema evolutions.
  - *Trade-offs*: Requires running `scripts/update_knowledge_base.py` whenever source code changes to satisfy test assertions.

### ADR-036: Deterministic Sync Freshness Gate, Strict Principle Schema, and Tier 1B Domain Rules Injection (PRINCIPLE-017)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. Unit tests verified file existence and token budgets, but did not assert that target IDE prompt files (`GEMINI.md`, `CLAUDE.md`, `.cursorrules`, etc.) were bit-for-bit fresh against `AGENTS.md`, allowing stale prompt files to be committed.
  2. `parse_principles()` permitted missing `Concept`, `Invariant`, or `Rules` sections, risking incomplete prompt injections.
  3. Desynchronization between `AGENTS.md`, `GUIDELINES.md`, and `README.md` was undetected by automated tooling.
  4. External projects adopting AIKit had no automated mechanism to inject custom project domain rules (Tier 1B) into generated IDE rule files without manually editing multiple generated files.
- **Decision**:
  1. Enforce **Deterministic Auto-Sync Freshness Gate**: Unit tests must assert that `sync_all(check_only=True)` returns 0 mismatches against on-disk files.
  2. Enforce **Strict Principle Schema Validation**: `parse_principles()` must validate non-empty Title, Concept, Invariant, and numbered Rules, halting on any omission.
  3. Enforce **Triad Documentation Consistency Shield**: Programmatically verify that all principles in `AGENTS.md` are present in `GUIDELINES.md` and `README.md`.
  4. Enforce **Dynamic Lifecycle Phase Tracking**: Replace hardcoded ranges with dynamic header-driven phase mapping, enforcing monotonic execution ($Phase_i \ge Phase_{i-1}$).
  5. Enforce **Tier 1B Domain Rules Extension Slot**: If `.agents/rules/domain.md` exists and satisfies budget constraints (<1,200 chars / ~300 tokens), `sync_principles.py` automatically injects it under `## Project Domain Invariants (Tier 1B)` in all generated targets.
- **Consequences**:
  - *Positive*: Mechanically shields all IDE environments from rule drift; guarantees principle schema completeness; enables zero-friction domain customization for adopter repositories.
  - *Trade-offs*: Modifications to `AGENTS.md` require running `scripts/sync_principles.py` before test assertions pass.

### ADR-037: Exact Heading Title Parity, Duplicate Principle ID Shield, and Domain Blueprint (PRINCIPLE-017 Pass 2)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. Triad consistency verified principle ID presence, but did not enforce exact heading title parity (`### {p['id']}: {p['title']}`) between `AGENTS.md` and `GUIDELINES.md`, permitting subtle title drift.
  2. `parse_principles()` lacked duplicate ID detection, meaning duplicate principle blocks would pollute generated prompt files.
  3. `scripts/sync_principles.py` lacked CLI argument handling, executing file modifications even when called with `--help` or `-h`.
  4. Adopters had no template or schema blueprint for `.agents/rules/domain.md`, causing ambiguity during onboarding.
  5. Context budget checks lacked early warning thresholds before hitting the hard 8,000-character ceiling.
- **Decision**:
  1. Enforce **Exact Heading Title Parity**: `validate_triad_consistency()` verifies that `### {p['id']}: {p['title']}` in `AGENTS.md` matches `GUIDELINES.md` exactly.
  2. Enforce **Duplicate Principle ID Shield**: `parse_principles()` tracks seen IDs and immediately rejects duplicates.
  3. Enforce **Safe CLI Help & Options Handling**: `scripts/sync_principles.py` cleanly handles `--help` / `-h` (exiting 0 without writing files) and supports `--domain <path>`.
  4. Provide **Canonical Domain Rules Template**: Distribute `.agents/rules/domain.md.template` with structured stack, architectural, and linter guidance bounded to 1,200 chars.
  5. Enforce **Proactive 90% Budget Warning**: Emit `[BUDGET WARN]` when any target exceeds 7,200 chars (>90% of budget).
- **Consequences**:
  - *Positive*: Guarantees exact title consistency across human and agent documentation; protects against accidental duplicate rules; provides zero-friction onboarding template for adopter projects.
  - *Trade-offs*: Title edits in `AGENTS.md` require updating `GUIDELINES.md` simultaneously.

### ADR-038: Explicit Staging Invariant, Adaptive Remote Push, and Conventional Commit Tooling (PRINCIPLE-018)
- **Date**: 2026-10-15
- **Status**: Accepted
- **Context**:
  1. Agents frequently execute blind staging (`git add .`), accidentally committing unwanted scratch buffers, OS artifacts, test sandboxes, or unrelated human workspace edits.
  2. Pushing blindly to `origin main` causes agent crashes in greenfield local-only repositories (where no remote exists yet) or triggers dangerous force-pushes upon upstream divergence.
  3. Agents attempting error recovery sometimes execute destructive commands (`git reset --hard`, `git clean -fdx`) that discard uncommitted progress.
  4. There was no automated validator for Conventional Commit formats and milestone indices.
- **Decision**:
  1. Enforce **Explicit Staging Invariant**: Blind staging commands (`git add .`, `git add -A`) are strictly prohibited; target paths must be explicitly listed in git add commands.
  2. Enforce **Pre-Commit Delivery Triad**: Terminal commits are locked until (1) 100% tests pass, (2) principle rules and codebase map pass freshness checks (`--check`), and (3) clean working tree is confirmed.
  3. Enforce **Adaptive Push & Zero Force Push**: Automatically inspect active branches and remotes; fall back cleanly to local-only commits if unconfigured; rebase on divergence; strictly prohibit `--force`.
  4. Enforce **Non-Destructive Recoil Invariant**: Error recoveries must use soft rollbacks (`git reset --soft HEAD~1`), preserving working tree changes.
  5. Provide **Pure-Stdlib Conventional Commit Validator**: Implement `validate_conventional_commit()` in `scripts/disruption_recovery.py` with `--validate-commit` CLI support.
- **Consequences**:
  - *Positive*: Guarantees clean, noise-free git history; protects against data loss during failure recovery; provides automated validation for Conventional Commits and micro-milestone indexing.
  - *Trade-offs*: Requires explicit staging commands instead of one-line blanket additions.





### ADR-039: Universal CLI Contract Parity, Safe Help Short-Circuit, and Real Dual-Track Dogfooding (PRINCIPLE-010, PRINCIPLE-011, PRINCIPLE-015)
- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**:
  1. Only `scripts/sync_principles.py` handled `--help`. `scripts/update_knowledge_base.py --help` fell through to its default action and **silently rewrote `knowledge/codebase_map.md`** — a help request mutated the repository. `scripts/disruption_recovery.py --help` ran a full git-backed disruption audit.
  2. All three entrypoints silently swallowed unrecognized flags: `--bogus-flag` performed the default action and exited `0`, violating the PRINCIPLE-011 R5 exit-code contract (`2` = CLI misuse). For an agent that mistypes a flag, this produced a *silent wrong action reported as success* — including an unintended repository write.
  3. Because help did not short-circuit before AST walks and subprocess calls, the PRINCIPLE-010 R5 startup budget (<100ms to `--help`) was breached on 2 of 3 entrypoints (107ms and 130ms).
  4. PRINCIPLE-015 carried the heaviest operational mandates in the system yet had no mechanical enforcement. Its sole dogfood test created a temporary directory and then asserted that the directory existed and carried the prefix it had just supplied — a tautology, in breach of the PRINCIPLE-014 R5 anti-tautological invariant.
  5. The PRINCIPLE-001 invariant reads "<1,500 tokens / <8,000 chars", but only characters were gated. At ~4 chars/token the 8,000-char cap admits ~2,000 tokens, so `.agents/rules/principles.md` sat at ~1,556 est. tokens — past the stated target — and the gate reported `[BUDGET PASS]`.
  6. The verification gate sprayed ~37 lines of sync chatter into agent context on every run, against PRINCIPLE-012 R3 (runners default to quiet).
- **Decision**:
  1. Establish a **Universal CLI Contract** across all `scripts/`: `--help`/`-h` short-circuits before any import-heavy work or I/O, prints usage to stdout, and exits `0`; unknown flags are refused with the What → Why → Fix remediation triad on stderr and exit `2`; `0`/`1`/`2` exit semantics are uniform.
  2. Implement **value-aware flag validation**: validators skip the value token of known value-taking flags (`--desc`, `--why`, `--validate-commit`, …), so free-text values are never misread as unknown options.
  3. Enforce **`--check` purity**: `sync_all` no longer calls `mkdir(parents=True)` on target parents in check-only mode, so the read-only gate cannot create directories.
  4. Add **token-target observability**: `TARGET_TOKEN_BUDGET = 1500` emits `[TOKEN WARN]` when a target passes the stated Tier 1 token target while remaining under the hard character cap, making the previously silent breach visible without churning the 5 generated targets.
  5. Replace the tautological dogfood test with a **real dual-track CLI dogfood matrix**: every entrypoint is executed as a subshell binary from an ephemeral `dogfood_jail_*` sandbox cwd with stdin closed (EOF safety), across a golden path (`--help`) and a hostile perturbation (malformed flag), asserting exit codes, the remediation triad, zero tracebacks, and a bit-for-bit unchanged `git status --porcelain` before and after the matrix.
  6. Hold the sub-second gate by running the subshell matrix **once** in `setUpClass` through a bounded `ThreadPoolExecutor` ($K \le$ `os.cpu_count()`) per PRINCIPLE-010 R3, and by retiring the older single-script help test that the 3-script contract strictly subsumes.
  7. Buffer sync/validation diagnostics in the test gate via `contextlib.redirect_stdout`, replaying them in the assertion message only on failure.
  8. Add **PRINCIPLE-017 and PRINCIPLE-018 pre-flight checklist entries**, which previously appeared only in the post-flight list, so rule-freshness and rollback baselines are established at cold start rather than discovered at delivery.
- **Consequences**:
  - *Positive*: Eliminates the silent-wrong-action failure class on every CLI surface; a help request can no longer mutate the repository; brings all 3 entrypoints inside the <100ms startup budget (107/130ms → 52/67ms); converts PRINCIPLE-015 from unenforced prose into a mechanical gate; cuts verification-gate output from 37 lines to 0.
  - *Trade-offs*: Strict flag rejection means any future flag must be registered in its script's `KNOWN_FLAGS` set or it will be refused with exit `2` — deliberate, since silent acceptance was the defect. The dogfood matrix adds ~45ms of real subshell execution to the suite (0.694s → 0.739s), retained because headless in-process tests cannot observe exit codes or stderr contracts.
  - *Deferred*: A standalone `scripts/dogfood.py` runner with process-tree teardown and `.agents/dogfood_last_run.log` remains unbuilt; the CLI matrix covers the single-process CLI domain, but the GUI/web/API domains in PRINCIPLE-015 R1 stay uninstantiated until AIKit governs a project that has those surfaces. The ledger key `version` also still differs from the `schema_version` name mandated by PRINCIPLE-016 R5; left unchanged to avoid a breaking schema rename for a naming nit.

### ADR-040: Advisory Lock Wiring, Exhaustive Porcelain Classification, Phase-Accurate Resumption, Full AST Signatures, and the Two-Tier Test Budget
- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**: A line-by-line audit of all 18 principles found four invariants that reported **green in tests while broken in production**. Each was reproduced before being fixed (PRINCIPLE-014 R6 red-green pinning):
  1. **PRINCIPLE-013 R3 (unused advisory lock)**: `file_lock()` was defined, exported and unit-tested, but had **zero production call sites**. Every ledger mutation (`record_checkpoint`, `mark_task_completed`, `reset_active_task`) performed an unprotected load-modify-save cycle. Six concurrent `record_checkpoint` processes persisted **2 of 7 checkpoints — 5 silently lost**, which is precisely the "silent progress erasure" the rule names.
  2. **PRINCIPLE-006 R2 (porcelain blindness)**: `run_disruption_audit` classified `git status --porcelain` against a closed whitelist `("M","A","D","R","MM","AM")`, silently dropping **10 of 16 real states** — including *every* unmerged/conflict state. A real repository with `UU f.txt` was reported as `🟢 Clean state. No interrupted tasks or uncommitted drift detected.` by the audit that PRINCIPLE-006 R2 makes the mandatory first action of every cold start.
  3. **PRINCIPLE-002 R4 / PRINCIPLE-004 R2 (broken resumption)**: `format_resume_report` and `reset_active_task` read `last_phase_num`, a key **no writer ever produced**. `record_checkpoint` persists `active_phase`. Every resumption therefore defaulted to a fixed phase: a task interrupted in Phase 4 reported `Last Active Phase: Phase 2 (verification)` — self-contradictory in its own output — and recommended resuming at Phase 3, sending the agent *backwards* against PRINCIPLE-002 R1 monotonicity.
  4. **PRINCIPLE-016 R4 / PRINCIPLE-003 R1 (lossy symbol catalog)**: `extract_python_symbols` matched only `ast.FunctionDef`, so **every `async def` function and method was absent** from `codebase_map.md`, and read only `args.args`, so `f(a, *args, kwonly, **kwargs)` was catalogued as `f(a)`. The document agents are instructed to consult before verifying call-sites (PRINCIPLE-004 R3) was both incomplete and actively misleading.
  Secondary findings: no parent-directory `fsync` after `os.replace` anywhere (PRINCIPLE-013 R1 claims power-loss durability, but on POSIX journalling filesystems the rename can be lost even after the file is synced); a racy stale-lock break where two processes could both claim the same expired lock; and `str` paths raising a raw `AttributeError` from deep inside `load_ledger` against PRINCIPLE-011 R6.
- **Decision**:
  1. Introduce `locked_ledger()`, a context manager that holds the advisory lock across the **entire** read-modify-write cycle, and route all three mutators through it. Contention raises an actionable `TimeoutError` with the What/Why/Fix triad rather than writing unprotected. `save_ledger` grows a `_locked` flag because the lock is not reentrant, and `file_lock` now creates its own parent directory so a first-run adopter can lock before `.agents/` exists.
  2. Extract porcelain parsing into a **pure** `classify_git_status()` function, free of subprocess I/O so every state is deterministically testable. Classification is exhaustive by construction: `??` untracked, `!!` skipped, one of git's **closed 7-code unmerged set** conflicted, and *any other non-blank code* modified — so no future git code can ever vanish again. `AA` and `DD` are conflicts despite containing no `U`, which a `"U" in xy` substring test missed; this was caught by the new test table, not by inspection.
  3. Surface conflicts as a dominant `🔴 UNRESOLVED MERGE CONFLICTS` status in both the audit and resume reports, with explicit `git merge --abort` / `git rebase --abort` remediation.
  4. Add `resolve_active_phase()`, reading `active_phase` first, honouring the legacy `last_phase_num` for ledgers written before this fix, and falling back to the textual phase label. Resumption is clamped to never recommend an earlier phase than the one reached.
  5. Add `render_signature()` covering positional-only (`/`), positional, `*args`, the bare `*` keyword-only marker, keyword-only names and `**kwargs`, and catalogue `ast.AsyncFunctionDef` alongside `ast.FunctionDef`, rendering `async def` in the map so awaitability is visible.
  6. Add `fsync_dir()` as a durability barrier after every `os.replace` across all three scripts (no-op on win32, which exposes no directory handle and whose `os.replace` is already metadata-atomic). Break stale locks by **atomic rename** so exactly one racer can win. Coerce `str` paths to `Path` at the ledger boundary.
  7. **Two-tier test budget.** The new concurrency and CLI-contract tests pushed the suite from 0.74s to ~1.13s, breaching the stated <1s gate. Rather than delete the tests that proved the defects or leave a headline invariant knowingly unmet, partition into a unit tier (`tests/test_kit.py`, strict <1s) and an integration tier (`tests/test_integration.py`, <5s, explicit timeout per spawn). Both run under the unchanged canonical command; nothing is hidden or opt-in. The unit gate is enforced **structurally** — the unit module may not reference `subprocess`, `Popen`, `os.system` or `time.sleep` — because a wall-clock assertion on a 1s budget would itself be flaky, and PRINCIPLE-014 R3 treats flaky tests as blocking defects.
- **Consequences**:
  - *Positive*: Concurrent checkpoints now lose **0 of 7** (was 5 of 7). A conflicted tree can no longer report clean. Resumption reports the phase actually recorded, for every phase 1–5. `async def` symbols and complete signatures appear in the catalog. Atomic writes gain a real POSIX durability barrier. Measured: unit tier 61 tests / 0.62s, integration tier 12 tests / 0.57s, canonical run 73 tests / ~1.18s.
  - *Trade-offs*: `fsync_dir` is duplicated as a small local shim in all three scripts rather than shared, deliberately: these are standalone zero-dependency entrypoints with no cross-imports, and a shared module would require a fragile dual-mode `import` dance that risks PRINCIPLE-011 clone-and-run. The `<1s` figure in PRINCIPLE-010 R6 and PRINCIPLE-014 R3 now scopes to the unit tier, which is a deliberate amendment of a headline number, recorded here so the change is auditable rather than silent.
  - *Deferred*: The real end-to-end merge-conflict fixture (11 git subprocesses, 367ms) was replaced by the exhaustive pure-function table plus a cheap grounding test that classifies the live repository's own real `git status --porcelain` output. The full conflict path was verified manually during this session; conflict codes come from a documented closed set, so the table is the stronger long-term guard. `scripts/dogfood.py` with process-tree teardown and `.agents/dogfood_last_run.log` (ADR-039) remains unbuilt, as do PRINCIPLE-015's GUI/web/API domains. The ledger key `version` still differs from PRINCIPLE-016 R5's `schema_version`.

### ADR-041: Continuous Verification Gate (CI) with Cross-Platform Matrix and Command-Parity Shield
- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**:
  1. `.github/` contained only `copilot-instructions.md`. There was **no CI workflow of any kind**, so every gate the principles declare — the 100% test pass gate (`PRINCIPLE-014`), rule sync freshness (`PRINCIPLE-017` R3), AST map freshness (`PRINCIPLE-016` R4), and the `PRINCIPLE-018` R3 delivery triad — existed purely as agent discipline. Any contributor, or any future agent that skipped the ritual, could push drift with nothing to stop it.
  2. AIKit is developed on Windows. The `fsync_dir()` POSIX durability branch added in ADR-040 had therefore **never executed**, and the cross-platform path/shell parity asserted by `PRINCIPLE-003` R4 and `PRINCIPLE-011` R4 was an untested claim.
  3. A workflow that drifts from the documented commands is worse than none, because it manufactures false confidence.
- **Decision**:
  1. Add `.github/workflows/ci.yml` running on push to `main`, on pull requests, and on manual dispatch, with `permissions: contents: read`, a 10-minute job timeout (`PRINCIPLE-010` R3 bounded execution) and in-progress cancellation.
  2. Run a **3 OS x 2 Python matrix** (`ubuntu-latest`, `windows-latest`, `macos-latest` x `3.10`, `3.13`) with `fail-fast: false`, so the POSIX legs exercise the directory-fsync barrier and path parity that the Windows development environment cannot.
  3. Gate on every declared invariant: unit tier, integration tier, the canonical discover command, both `--check` freshness gates, the universal CLI contract (`--help` exits 0, misuse exits 2 on all three entrypoints), and a final `git status --porcelain` assertion that verification left the tree pristine (`PRINCIPLE-014` R4).
  4. Include **no install step**, as a standing executable proof of the `PRINCIPLE-011` R1 pure-stdlib clone-and-run baseline.
  5. Add `TestContinuousVerificationGate` as a drift shield: it asserts the workflow exists, runs each declared gate by its exact command string, covers both POSIX and Windows runners, declares a timeout and least-privilege permissions, and checks the pristine-tree assertion. A companion assertion enforces **executable command parity** in both directions — anything CI runs must also appear in `README.md`.
- **Consequences**:
  - *Positive*: Gates are now enforced off the agent's machine for every contributor. The parity shield immediately earned its place: it failed on first run because `README.md` documented `sync_principles.py` and `update_knowledge_base.py` but never their `--check` forms, which are exactly the commands the `PRINCIPLE-018` R3 triad depends on; both are now documented.
  - *Trade-offs*: Workflow validity cannot be fully verified locally (no PyYAML in a stdlib-only environment); validation was limited to a structural tab/indent check plus a local rehearsal of the embedded bash contract block. The first push is therefore the real test of the workflow itself. Six matrix legs cost CI minutes, justified by platform-parity claims that were previously unverified.
  - *Deferred*: No release/publish automation, and no branch protection requiring the workflow — enabling that is a repository setting, not a file.

### ADR-042: CI Is Correct but Blocked at the Account Level (Private-Repo Actions Unavailable)
- **Date**: 2026-10-16
- **Status**: Accepted (blocked on an external account setting)
- **Context**:
  1. The workflow added in ADR-041 failed on first push. The first failure was a genuine defect: an unquoted YAML plain scalar containing `": "` rejected the file outright (now pinned by a regression test).
  2. After that fix the YAML parses cleanly under PyYAML (10 steps, 1 job), yet runs still ended in `startup_failure` at 0s with `total_count: 0` jobs and no check-runs or annotations.
  3. A binary experiment settled it: a deliberately minimal workflow (`smoke.yml`, one `ubuntu-latest` job running a single `echo`) **also** ended in `startup_failure`. The cause is therefore not the workflow schema.
  4. Repository state: `private: true`, owner type `User`, `actions.permissions.enabled: true`, workflow registered and `state: active`. Billing could not be inspected - the REST billing endpoint requires the `user` OAuth scope, and widening the CLI's auth scopes is an account-level change that is not AIKit's to make unilaterally.
- **Decision**:
  1. Keep `.github/workflows/ci.yml`. It is validated as far as it can be locally (PyYAML parse, structural checks, and a local rehearsal of its embedded bash contract block) and will execute unchanged as soon as Actions can start on this repository.
  2. Delete the diagnostic `smoke.yml`; it served its single purpose.
  3. Trim the matrix from 6 legs to 4 (`ubuntu-latest`, `windows-latest` x `3.10`, `3.13`). `macos-latest` bills at a 10x minute multiplier and adds little over ubuntu for POSIX parity, which is an unjustifiable standing cost on a private repository.
  4. Record the blocker here rather than silently leaving a red badge: the most likely cause is GitHub Actions minutes or a spending limit for **private**-repository usage on this account. Resolution lives in account settings (Billing -> Plans and usage -> Actions spending limit), or by making the repository public, which removes minute billing entirely.
- **Consequences**:
  - *Positive*: The gate exists, is drift-shielded by `TestContinuousVerificationGate`, and is one account setting away from enforcing every invariant off the agent's machine. The YAML defect it surfaced is permanently pinned.
  - *Trade-offs*: Until Actions can start, the gates remain agent-discipline only - exactly the weakness ADR-041 set out to remove. The repository therefore still depends on the agent running the delivery triad by hand.
  - *Deferred*: Branch protection requiring the CI check is a repository setting, not a file, and cannot be added from the working tree.

### ADR-043: Operational Dogfood Runner, Ledger Workspace Redirection, and Content-Hashed Blast Radius (PRINCIPLE-015)
- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**:
  1. `PRINCIPLE-015` carried the heaviest operational mandates in the system - `SANDBOX_ROOT` jailing, platform-portable process-tree teardown, `.agents/dogfood_last_run.log`, golden path plus hostile chaos, a terse <15-line dashboard, and a pre-ship gate - with **zero tooling**. ADR-039 and ADR-040 both recorded it as deferred. It was the only principle whose rules could not be executed.
  2. Writing the runner immediately exposed three real defects, which is the point of dogfooding:
     - `disruption_recovery.py` anchors its ledger to `ROOT_DIR` derived from `__file__`, not to the working directory, and offered **no CLI flag to target another workspace**. The first dogfood run therefore wrote straight into the live repository ledger, replacing the active task with the chaos track's `victim` entry. `PRINCIPLE-015` Rule 4 ("never touch host directories") was literally unsatisfiable for the ledger CLI as built.
     - The runner's own blast-radius check compared `git status --porcelain` text before and after. That is blind to content changes in files that were **already dirty**: porcelain prints the identical `" M .agents/task_ledger.json"` line regardless of what changed inside. The run passed its own safety check while clobbering the ledger.
     - `subprocess.Popen(text=True)` decodes child output with the **locale** codec. AIKit's CLIs reconfigure stdout to UTF-8 on Windows and emit non-ASCII status glyphs, so on this Turkish Windows install (`cp1254`) the reader threads died with `UnicodeDecodeError` and `communicate()` returned empty output - which then surfaced misleadingly as "resume report lost the recorded phase".
- **Decision**:
  1. Add `scripts/dogfood.py` with five tracks: a full create -> modify -> retrieve -> complete ledger lifecycle asserted against on-disk state; hostile chaos (malformed flag, missing flag value, corrupted ledger, 0-byte truncation); both read-only freshness gates; `--help` safety with a measured startup budget; and a blast-radius check. Process supervision uses an RAII `supervised()` context manager with `taskkill /F /T` on Windows and `killpg(SIGKILL)` on POSIX (via `start_new_session`), so no spawn can be orphaned.
  2. Add `--workspace <dir>` to `disruption_recovery.py`, threaded through every action (`--checkpoint`, `--complete`, `--reset`, `--clean`, `--audit`, `--resume`). The default stays repository-anchored so an agent in a subdirectory still finds the real ledger; a missing value exits 2 with the remediation triad rather than silently falling back to the real ledger.
  3. Replace the porcelain-text blast-radius check with `repo_fingerprint()`, a SHA-256 over `git status --porcelain` plus the content of every `git ls-files` entry. Status text alone is not evidence of non-mutation.
  4. Force `encoding="utf-8", errors="replace"` on every spawn in the runner.
  5. Promote dogfooding to a real gate: it runs in CI, and `tests/test_integration.py` carries seven regression tests over the runner (exit code, terseness, track coverage, traceback freedom, log emission, non-mutation, CLI contract) plus three over `--workspace` isolation that assert the repository ledger is byte-identical afterwards.
  6. Gitignore `.agents/dogfood_last_run.log`. `PRINCIPLE-015` Rule 7 mandates that path while Rule 4 forbids writes outside `SANDBOX_ROOT`; the log is the single declared exception, and gitignoring it guarantees a run artifact can never enter history.
- **Consequences**:
  - *Positive*: `PRINCIPLE-015` is executable for the first time - `python scripts/dogfood.py` reports 5/5 in ~1.1s and exits 0/1. The runner earned its place before it was even committed by finding three defects, one of which was a silent-data-loss bug in the kit's own ledger CLI. Measured: unit 69 tests/0.61s, integration 22/2.18s, canonical 91/2.75s.
  - *Trade-offs*: The integration tier grew from 0.6s to ~2.2s because it now runs the full dogfood gate nested inside itself; still well inside the <5s budget, and the alternative is shipping an unverified runner. The dogfood "read-only gates" track fails whenever the codebase map is stale, which is correct but means the map must be regenerated before the gate passes.
  - *Deferred*: `PRINCIPLE-015` Rule 1's GUI, web-app and backend-API domains remain prose; AIKit has no such surfaces, so instantiating them would be speculation. The runner is the CLI domain only.

### ADR-044: Invariant Reachability Shield as PRINCIPLE-014 Rule 7 Rather Than a New Principle
- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**:
  1. Across two deep audits, the single highest-frequency defect class was **"green test, broken production"** - a capability that exists, is exported, is unit-tested, and is wired into nothing. Five occurrences: the unused `file_lock()` (5 of 7 concurrent checkpoints silently lost), the phantom `last_phase_num` key (every resumption reported a default phase), the porcelain whitelist gap, the omitted `async def` symbols, and the tautological dogfood test.
  2. No principle covered it. `PRINCIPLE-014` R5 forbids tautological *assertions*; `PRINCIPLE-003` governs reading before writing. Neither asks whether a declared mechanism is actually *reached*.
  3. A nineteenth principle was the obvious shape, but the Tier 1 injected budget is already breached: `.agents/rules/principles.md` sits at ~1,559 est. tokens against a stated 1,500-token target, and `PRINCIPLE-001` R9 requires that adding a principle be paid for by condensing others.
- **Decision**:
  1. Add the invariant as **`PRINCIPLE-014` Rule 7** rather than `PRINCIPLE-019`. Only invariant *capsules* are injected into Tier 1 targets, so adding a rule to an existing principle costs **zero** injected budget - measured and confirmed: `principles.md` remained at 6,238 chars / ~1,559 tokens before and after. A new principle would have added ~340 chars to each of 5 targets while the budget is already over.
  2. The rule states three sub-invariants: call-site reachability ("covered by a unit test" is not reachability), key round-trip integrity (every persisted key read must have a producer), and a declared-capability audit (when a principle names a mechanism, verify it is wired into the path it protects before marking work done).
  3. Implement `scripts/check_reachability.py`: an AST auditor over `scripts/*.py` reporting functions with no production reference and state keys read with no producer. References are collected deliberately broadly (`ast.Name` loads, attributes, `ImportFrom`) because a function used as a value - stored in a dispatch tuple, passed as a callback - is genuinely reachable; under-counting would produce false alarms that erode trust in the gate.
  4. Carry an explicit `PUBLIC_API_ALLOWLIST` for symbols that are deliberately public (driven by tests, adopters or other tooling rather than called internally), plus a test asserting no allowlist entry names a symbol that no longer exists - an allowlist outliving its symbols silently stops shielding anything.
  5. Wire it into every gate: CI step, the dogfood runner's read-only gates track, and the universal CLI contract loop.
- **Consequences**:
  - *Positive*: The highest-frequency defect class now has a mechanical shield at zero prompt cost. The shield is proven, not assumed: unit tests reconstruct both historical defects as synthetic fixtures and assert they are caught, so the checker cannot rot into one that only ever reports OK - the precise failure mode it exists to prevent.
  - *Trade-offs*: The allowlist is long (~40 entries) because AIKit's scripts are both entrypoints and a library the test suite drives directly. Each entry is a decision rather than a silenced warning, but the list must be curated or it will hollow the gate out over time. The key-round-trip heuristic is conservative - it flags only keys appearing exactly once in the entire corpus - so it catches phantom readers without flagging legitimate legacy-key fallbacks.
  - *Note*: Writing the shield's own tests surfaced an unrealistic fixture (a helper with no caller either), which the shield correctly flagged. The fixture was corrected to include an entrypoint dispatch; the implementation was not weakened.

### ADR-045: PRINCIPLE-019 Secret & Sensitive Data Hygiene with a Risk-Tiered Pre-Commit Scanner
- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**:
  1. Across all 18 principles, secrets appeared in exactly **three incidental mentions**, all tangential (`PRINCIPLE-011` R3 on safe env lookups, `PRINCIPLE-014` R4 on `os.environ` restoration, `PRINCIPLE-018` R2 citing secrets as a reason to avoid blind staging). No principle owned the subject.
  2. Two concrete exposures existed in AIKit itself:
     - `.gitignore` excluded bytecode, quarantine artifacts and virtualenvs, but **no credential surface at all** - no `.env`, `*.pem`, `*.key`, `id_rsa*`, `credentials*` or `secrets*`.
     - `.agents/task_ledger.json` is **git-tracked** and persists four agent-authored free-text fields (`--why`, `--benefits`, `--risks`, `--mitigation`). The `PRINCIPLE-007` pre-flight workflow therefore *is* a leak path: an agent that quotes a credential while explaining its reasoning commits it to history permanently.
  3. Secret leakage is the only defect class with no clean rollback. `git reset` is not remediation; the value must be assumed captured the moment it is pushed.
- **Decision**:
  1. Add `PRINCIPLE-019: Secret & Sensitive Data Hygiene (Irreversible Disclosure Shield)` under Phase 5, where its mechanical gate lives, with seven rules: zero credentials in tracked files; an ignore-list baseline established *before* exposure; agent working memory treated as tracked output; redacted diagnostics and prompt payloads; a mechanical pre-commit scan; rotate-never-revert; and least-privilege defaults with zero secret fabrication.
  2. Extend `.gitignore` with the credential baseline (`.env` and variants with an `.env.example` negation, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.jks`, `*.keystore`, `id_rsa*`, `id_ed25519*`, `credentials*`, `secrets.*`, `*.tfvars`, and the AWS/GCloud/Azure CLI config directories).
  3. Implement `scripts/check_secrets.py` scanning staged content (default), all tracked text, or a single file - **plus agent working memory in every mode**, since that is the leak path unique to this kit.
  4. Make detection **pattern-first** across 13 known credential shapes, with a high-entropy fallback applied only to assignment-shaped lines, so prose and committed hashes do not trip the gate.
  5. Make allowlisting **risk-tiered**, which a red-check forced. The first implementation suppressed any line containing a weak hint, and consequently **missed `AKIAIOSFODNN7EXAMPLE` entirely** because the line contained the word "example" - the same logic would have hidden a live key on an `# example usage` line. Strong markers (the explicit `# aikit:allow-secret` pragma, unambiguous placeholders) now suppress every detector; weak hints ("example", "sample", "dummy") suppress only the low-confidence entropy fallback and can never veto a pattern match.
  6. Honour **indirection** in the pattern path, not just the entropy path: a value that is wholly `${VAR}`, `$VAR`, `{{ var }}`, `%(var)s` or `<placeholder>` is not a literal credential. `password = "${DB_PASS}"` is correct code, and a scanner that blocks correct code gets bypassed, which protects nothing. A partial interpolation (`"abc${X}tail"`) is still flagged, so this is not a bypass.
  7. Declare the test suite's own credential-shaped fixtures with inline `# aikit:allow-secret` pragmas rather than skipping `tests/` wholesale. Skipping the directory would blind the scanner to real secrets in test files, which is a common leak location; declaring each fixture also dogfoods the pragma end-to-end.
  8. Wire the scan into CI, the dogfood runner's read-only gates track, and the universal CLI contract loop, as the fourth leg of the `PRINCIPLE-018` R3 delivery triad.
- **Consequences**:
  - *Positive*: The highest-damage AI-agent failure mode now has an owner and a mechanical gate; the kit's own ledger leak path is scanned on every run. Nine unit tests pin the scanner against real credential shapes, the weak-allowlist veto regression, pragma suppression, interpolation safety, entropy separation, ledger free-text scanning, and the `.gitignore` baseline. Measured: unit 83 tests/0.87s, integration 22/2.55s, canonical 105/3.36s, dogfood 5/5.
  - *Trade-offs*: This is the 19th principle and it **pushed four of five Tier 1 targets past the 1,500-token target** (`principles.md` 1,559 -> 1,656). `PRINCIPLE-001` R9 requires that expansion be paid for by condensing existing capsules; that paydown is the next milestone and is not optional. Documentation files are excluded from scanning (`SKIP_PATH_PARTS`) because they discuss credential patterns rather than carry them, which is a real blind spot accepted deliberately: a secret pasted into `README.md` would not be caught.
  - *Note*: Three of this scanner's own tests failed on first run - a malformed 36-character Google key fixture, the interpolation false positive, and the scanner catching its own test fixtures. All three were genuine findings; two were implementation defects and one was a fixture error. None was resolved by weakening an assertion.

### ADR-046: Tier 1 Budget Paydown via Redundant-Anchor Removal, and Promotion of the Token Target to an Enforced Gate
- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**:
  1. `PRINCIPLE-001` R6 states a Tier 1 budget of "<1,500 tokens / <8,000 chars". Only the character cap was ever enforced, and at ~4 chars per token an 8,000-char cap admits ~2,000 tokens - so the token figure was unenforceable by construction.
  2. The target was therefore **already breached before this session** (`principles.md` ~1,559 est. tokens) while the audit printed `BUDGET PASS`. ADR-039 made the overage visible as `[TOKEN WARN]`, but a warning changes nothing.
  3. Adding `PRINCIPLE-019` (ADR-045) pushed **four of five** targets past the target (`principles.md` 1,656). `PRINCIPLE-001` R9 requires that expansion be paid for by condensing existing summaries, so paydown was obligatory, not optional.
  4. The obvious lever - compressing invariant capsules - is directly constrained by `PRINCIPLE-001` R2, which forbids compressing away hard mechanical constraints. Capsules are where routine-task accuracy comes from, so squeezing them is the *worst* available lever.
- **Decision**:
  1. Pay the budget down **structurally rather than semantically**: remove the per-principle markdown anchor that every generated line carried (`[GUIDELINES.md#principle-0XX]`, and `[GUIDELINES.md](../../GUIDELINES.md#principle-0XX)` at 51 chars per line in `.agents/rules/principles.md`). Each target already states the deterministic grep contract (`Query='### PRINCIPLE-XXX:'`) once in its header, so the per-line anchors were pure duplication - and *less* reliable, since heading-slug links rot silently when a title changes, which is the exact drift class `PRINCIPLE-017` R4 had to add title-parity validation for. Zero information lost; 19 lines x 29-51 chars reclaimed per target.
  2. Promote the token check from `[TOKEN WARN]` to `[TOKEN EXCEEDED]`, incrementing `budget_violations` so an overage **blocks** `sync_principles.py` and its `--check` gate, with a What/Why/Fix remediation message naming the condensation rule and both ceilings.
  3. Sharpen the `PRINCIPLE-013` capsule from "flush + fsync + retry replace" to "flush + os.fsync + retried os.replace + parent-dir fsync", matching `PRINCIPLE-001` R2's own exemplar of a self-sufficient capsule and encoding the durability barrier added in ADR-040. Spending reclaimed budget on mechanical precision is the intended direction.
  4. Pin all of it: four tests assert every target is within the token target, that an overage returns non-zero with a remediation line, that the grep-anchor contract survives in each target (it is what replaces the removed anchors), and that condensation did not strip named mechanisms (`os.replace`, `fsync`, `100% test pass gate`, `<1s`, `task_ledger.json`, `advisory locking`).
- **Consequences**:
  - *Positive*: All five targets are under the stated target for the first time - and with **19** principles rather than 18. `principles.md` went 1,656 -> 1,426 est. tokens, a better figure than the 1,559 that preceded this session's expansion. The invariant is now enforced, so it cannot drift back silently.
  - *Trade-offs*: Headroom is genuine but finite. A simulated 20th principle of average capsule size lands at ~1,480 tokens, roughly 20 tokens under the gate, so **the next principle added will require a further paydown** - which is precisely the flat-overhead behaviour `PRINCIPLE-001` R9 intends. Navigation now depends on the grep contract rather than clickable anchors, which is a small loss for humans reading the generated files in an editor and a gain in drift resistance.
  - *Note*: The mechanism test failed on first run because it asserted `os.replace` while the capsule said "retry replace". The capsule was sharpened to match `PRINCIPLE-001` R2's exemplar rather than the assertion relaxed.

### ADR-047: Coherent Tier 1 Budget Model with Tier 1B Reservation, Unified Renderer, and Capsule Fidelity
- **Date**: 2026-10-16
- **Status**: Accepted (supersedes the budget mechanics of ADR-046; its anchor removal stands)
- **Context**: A line-by-line pass over `PRINCIPLE-001`, measuring each rule rather than reading it, found two regressions introduced by ADR-046 and four pre-existing defects.
  1. **Tier 1B was unusable (regression).** ADR-046 made the 1,500-token target blocking but reserved no room for the ~300-token Tier 1B allowance that `PRINCIPLE-001` R4 and `PRINCIPLE-017` R6 promise adopters. Copying the shipped `domain.md.template` - exactly as R6 instructs - put all five targets at ~1,690-1,730 est. tokens and blocked sync.
  2. **A warning shadowed the gate (regression).** The audit was an `if/elif` chain with the advisory 7,200-char `WARN` branch *ahead of* the token check, so a target at ~1,860 tokens printed `[BUDGET WARN]` and passed. In write mode it would have been written and subsequently passed `--check`.
  3. **R4 and R6 were never mutually satisfiable.** R4 declared Tier 1A "<1,000 tokens"; Tier 1A was ~1,400-1,550 at every point in history. R6 paired "<1,500 tokens" with "<8,000 chars", which at any realistic ratio are different budgets; the char threshold was dominated by the token one once enforced.
  4. **The header contradicted R1 and R3.** Every target opened with "Strictly follow all principles and guidelines defined in AGENTS.md and GUIDELINES.md", which invites loading ~27k real tokens of Tier 2 up front - the exact bloat the principle forbids.
  5. **Capsules had drifted from their own rules (R2).** `PRINCIPLE-018` listed 6 of the 9 commit types its validator accepts (omitting `perf`, `build`, `ci`, the last of which was used on this repository), and named a "delivery triad" whose gate (2) covered none of the reachability, secret or dogfood gates added since. `PRINCIPLE-014` omitted its R7 reachability shield; `PRINCIPLE-015`/`-019` omitted the tools that enforce them; `PRINCIPLE-010` still said "sub-second test gate" after the tier split. `PRINCIPLE-001`'s own capsule restated the header line directly above it in every target.
  6. **Stale counts.** Seven hardcoded references to 18 principles (including `PRINCIPLE-001`'s own "immutable 18"); `PRINCIPLE-019` was absent from both checklists.
  The token estimator itself was suspected and **cleared**: against OpenAI's `cl100k_base` and `o200k_base`, the Tier 1 targets measure ~4.2 chars/token, so `chars // 4` over-counts by ~6% and errs conservative.
- **Decision**:
  1. One unit, two blocking checks, then advice. `audit_tier1_budget()` blocks when a target (including any Tier 1B block) exceeds 1,500 est. tokens, **and** - when no domain rules are loaded - when the universal rules would not leave room for a full `MAX_DOMAIN_CHARS` Tier 1B block. The 90% warning is evaluated only after both, so it cannot shadow a violation. The dominated `MAX_TARGET_CHARS`/`WARN_TARGET_CHARS` thresholds are removed.
  2. R4 drops its never-true "<1,000 tokens" figure in favour of the constraint that actually binds: Tier 1A is bounded by what it must leave free. This removes a redundant number rather than raising one.
  3. Pay for the reservation **structurally first**: a single `render_tier1_target()` replaces five near-identical generators; trailing title parentheticals (~380 chars) stay in Tier 2; list scaffolding and decorative bold labels are dropped; the header is rewritten to say *when* to read Tier 2 ("on a boundary, failure or ambiguity ... never load it whole") and to mark each file as generated so hand edits are not silently overwritten.
  4. Then cut capsule **narrative only**, while adding the mechanisms capsules were missing (commit types, triad members, reachability shield, dogfood/secret tools, concrete exit codes 0/1/2). `PRINCIPLE-018` R3 gate (2) now covers every read-only verification gate.
  5. Replace hardcoded principle counts with count-free phrasing and a single `MIN_PRINCIPLES` constant; add `PRINCIPLE-019` to both checklists.
- **Consequences**:
  - *Positive*: Every target is ~1,177 est. tokens (from ~1,426) with ~311 tokens of Tier 1B room against the 300 promised, so the shipped template syncs. Capsules carry more mechanism than before at fewer tokens. Five red-green pins cover the template regression, the reservation check, the shadowing hole, the estimator ratio, and the header's retrieval-trigger contract; `test_targets_in_sync_and_budgeted` now asserts all 19 IDs rather than 8, and the real token budget rather than the dominated 8,000-char cap.
  - *Trade-offs*: Margin is thin by design (~11 tokens): the next principle, or any capsule addition beyond a few words, will require a paydown, which is `PRINCIPLE-001` R9 working as intended. Dropping bold labels makes generated files plainer for humans reading them rendered. Two test assertions were rewritten because they pinned *labels* ("Deterministic Grep Anchor", the old remediation wording) rather than contracts; each replacement asserts the underlying contract and is strictly stronger.

### ADR-048: Single Tier 2 Source of Truth in GUIDELINES.md; AGENTS.md Becomes a Generated Tier 1 Target
- **Date**: 2026-10-16
- **Status**: Accepted (supersedes the AGENTS.md-as-master layout assumed by ADR-001 through ADR-047)
- **Context**:
  1. **The largest always-on file was the one file the budget never gated.** AGENTS.md held the full specification - ~15.9k real tokens (`o200k_base`). Tools that follow the AGENTS.md convention (OpenAI Codex and GitHub Copilot's coding agent among them) load AGENTS.md automatically, so for those agents AIKit injected ~13x the 1,500-token Tier 1 budget that `PRINCIPLE-001` exists to enforce. AIKit's README told adopters to copy that file to their project root.
  2. **Tier 2 existed twice.** AGENTS.md (Concept/Invariant/Rules) and GUIDELINES.md (Problem/Guideline) were two hand-maintained copies of the same rules, ~27.4k real tokens combined. Only *titles* were parity-checked, so bodies drifted freely: a measured audit found about six rules present in one copy but not the other (`PRINCIPLE-005` polyglot blueprint and `PRINCIPLE-015` live budgeting only in GUIDELINES.md; `PRINCIPLE-008` state propagation, `PRINCIPLE-010` anti-cleverness and `PRINCIPLE-017` phase alignment only in AGENTS.md), plus pervasive label drift.
  3. Dogfooding the documented adoption flow in a sandbox found three further defects: Option B's "Non-Destructive Quick-Merge" overwrote the target's own `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` and `.cursorrules`; the README triad check failed every adopter's first sync with 19 "PRINCIPLE-0XX missing from README.md" errors by forcing their *product* README to list AIKit's principle IDs; and copying AIKit's `tests/` produced 17 failures and 2 errors in a fresh adopter repository, because those tests assert AIKit's own repository. README Step 2 also instructed replacing a `<PROJECT_NAME>` placeholder that existed nowhere.
- **Decision**:
  1. **One copy.** A verified one-shot migration folded both files into GUIDELINES.md: every Concept, Invariant and Rules body carried byte-for-byte; every Problem statement carried as an optional `- **Problem**:` field; both GUIDELINES-only rules appended as numbered rules (`PRINCIPLE-005` R6, `PRINCIPLE-015` R8); checklists carried verbatim. The migration asserted all of this before writing. The hand-maintained index table was dropped: it was a third set of summaries linked by heading slugs that rot when titles change.
  2. **AGENTS.md is generated.** It joins `TIER1_TARGETS` and is rendered by the same `render_tier1_target()` as the other five, inside the same enforced budget.
  3. **Sync never overwrites what it did not generate.** `is_generated_target()` recognises the current header and the legacy `(Tier 1 Invariants)` header so older AIKit output stays upgradable; any other existing file is refused with `[PROTECTED]` and a What/Why/Fix message. Every target is classified **before** any is written, so a protected file cannot leave a half-synced tree (`PRINCIPLE-013` R6). An unmigrated layout gets `[MIGRATION REQUIRED]` guidance instead of a raw `ValueError` traceback.
  4. **README parity is "all or none".** A README that documents some principles must document all of them; an adopter's README that documents none is reported as `[INFO]` adopter mode, not drift. AIKit's own README is held to the full listing by a separate strict test, so this leniency cannot let AIKit drop its table.
  5. **Adoption flow made true.** Option B now copies only `GUIDELINES.md`, `scripts`, `knowledge` and `.agents/rules`; Step 2 moves an adopter's own agent instructions into `.agents/rules/domain.md` (Tier 1B). The README states why `tests/`, `.github/` and the task ledger are not copied, and that the CLI gates - all five verified passing inside an adopter sandbox - carry AIKit's enforcement.
  6. Supporting fixes found on the way: `parse_principles` now bounds each principle at the next `##` heading (the last principle used to swallow the trailing checklists); `sync_all` returns the number of problems in both modes (write mode used to return the number of files *updated*, so success looked like failure to programmatic callers); triad bullets are ASCII (`•` printed as garbage on cp1254); and the whole-repository secret scan moved to the integration tier because it spawns `git`, which had pushed the unit tier to ~1.0s.
- **Consequences**:
  - *Positive*: AGENTS.md went from 15,895 to 1,076 real tokens, 14.8x less always-on context for every AGENTS.md-convention agent. Tier 2 is one file (27,431 -> 17,693 real tokens) that cannot drift from itself. The documented adoption flow was executed end to end in a sandbox: an adopter's own `CLAUDE.md` was protected with zero files written, then after Step 2 their rules reached the Tier 1B section of all six generated files within budget.
  - *Trade-offs*: Agents that load both AGENTS.md and their own file (for example Copilot's coding agent with `.github/copilot-instructions.md`) now see the same ~1.1k-token capsules twice. That cost is bounded and small next to the ~15.9k it replaces. Any adopter on the old layout must migrate once; sync detects this and explains how. Option B adopters no longer receive AIKit's regression suite.
  - *Known limits*: The unit tier's structural no-spawn gate inspects test source text, so tests that reach `git` *indirectly* through `run_disruption_audit` are not caught by it; the tier holds at ~0.89-0.93s with roughly 70ms of margin. Copied `knowledge/` documents still describe AIKit and must be replaced by the adopter after Step 4.

### ADR-049: Injectable Git Adapter and a Runtime No-Spawn Gate for the Unit Tier
- **Date**: 2026-10-16
- **Status**: Accepted (closes the known limit recorded in ADR-048)
- **Context**: ADR-040's unit-tier gate scanned test *source* for `subprocess`/`Popen`/`os.system`/`time.sleep`. A runtime spawn detector showed four unit tests still launched `git` indirectly, through `run_disruption_audit`, while the text check passed.
- **Decision**:
  1. `run_disruption_audit(workspace_dir, git_status=None)` takes an injectable git adapter returning `(returncode, stdout, stderr)`, defaulting to `git_porcelain_status()` (`PRINCIPLE-009` R4 zero-config DI; production behaviour unchanged).
  2. The four unit tests pass `not_a_git_repo`, which returns exactly what real git returns in a non-repository (exit 128) without spawning.
  3. `test_unit_tier_spawns_nothing_at_runtime` (integration tier) runs the entire unit tier under a `Popen` detector and requires zero launches. It was red-checked by reverting one fake: it failed and named the spawn.
- **Consequences**: The no-spawn invariant is now enforced at runtime, not just by text. The integration tier rises to ~3.9s (budget 5s) because it executes the unit tier once more; the unit tier stays ~0.91s.

### ADR-050: PRINCIPLE-001 Rewritten for a Single Interpretation
- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**: Audited for one property - could two models read PRINCIPLE-001 and act differently? Yes, in six ways: (1) no audience - agent-time rules (R3, R8) were mixed with maintainer rules with nothing saying which bound whom; (2) no precedence between a capsule and GUIDELINES.md, or for an explicit user request to read the full file; (3) undefined triggers ("relevant sub-tasks", "underspecified requirements", and "boundary" in the header vs "Architectural Boundary" in R3); (4) IDE-specific verbs (`view_file`, `grep_search`, `Query=`); (5) unverifiable rules ("100% accuracy", "maximize the ratio", "verified mentally", "bounded and flat"); (6) conflicting definitions (Tier 2 defined twice, "~300 tokens" vs "1,200 chars", three names for the capsule). P001 carried 8 hedge words, the most of any principle.
- **Decision**:
  1. Keep R1-R9 in their numbered slots (every number is cited elsewhere) and rewrite each as an RFC 2119 obligation (MUST / MUST NOT / MAY, declared once in the GUIDELINES.md header) tagged *[Agent]* or *[Maintainer]*.
  2. R1 adds precedence: capsules bind; GUIDELINES.md wins on conflict and the mismatch is reported; an explicit user instruction overrides both. R3 defines three triggers by observable events (contract change, failure, ambiguity) and states how to pick the section to read. R5 is tool-neutral. R2 gets a deletion test; R6 states the exact formula and thresholds; R7 defines what "decoration" and "copying" mean; R8 defines the reporting format; R9 forbids raising budget constants without user approval and an ADR.
  3. The generated Tier 1 header uses R1's and R3's exact words ("wins on conflict", "contract change, failure or ambiguity", "never the whole file").
  4. Five tests pin it: no hedge words in P001's rules, every rule tagged, RFC 2119 keywords declared and used, header trigger names derived from R3, no tool-specific terms. Red-checked: the previous text fails all of them.
  5. A stale full copy of old P001 in knowledge/architecture.md was replaced by a citation (R7).
- **Consequences**: P001 now reads as one instruction set for any model. Tier 1 grew by about 4 tokens (Tier 1B room 306, still above 300). Hedge words remain in other principles (`e.g.` in 9 of them, `concise` in 6, `relevant` in 2, `should` in 1); they are candidates for the same treatment in later passes.

### ADR-051: PRINCIPLE-001 Second Unambiguity Pass - Precedence Scope, Defined Terms, Agent Rules in Tier 1
- **Date**: 2026-10-16
- **Status**: Accepted (refines ADR-050)
- **Context**: Re-reading ADR-050's rewrite adversarially found eight places where two models could still act differently, two of them introduced by ADR-050 itself:
  1. R1 said "an explicit user instruction overrides both", contradicting PRINCIPLE-002 R5 ("skip tests" must not bypass the verification gate). Told "skip the tests and commit", models would split on which rule to obey.
  2. R3's "each principle whose capsule governs the action" left "governs" undefined: one model reads all 19 sections, another reads none.
  3. The ambiguity trigger fired on every request, because any two implementations differ observably somehow, and said nothing about what to do if reading did not resolve it.
  4. "Before acting", "public function" and "load in full" were undefined; reading all sections one by one evaded the full-load ban.
  5. R8 was an *[Agent]* rule that never reached Tier 1, so agents reading only their Tier 1 file never learned it; it also ignored Tracks, demanding a checklist on Track A edits.
  6. Two placeholders for one thing: `PRINCIPLE-NNN` (R5) and `PRINCIPLE-XXX` (Tier 1 header, tooling).
  7. The Concept claimed every rule says "how compliance is checked"; R3 and R8 had no check.
  8. R2's "routine task" was undefined.
- **Decision**: R1's user override is scoped to P001's own reading limits and defers cross-principle conflicts to the other principle, naming PRINCIPLE-002 R5. R3 defines *involved* by string match against the files, commands and failing output (falling back to PRINCIPLE-003), defines the timing, public functions, the ambiguity surfaces, and requires escalation to the user if reading does not settle the choice. R8 is scoped by Track and now reaches Tier 1 through P001's capsule, which was rewritten under R2's deletion test: its "change rules only in GUIDELINES.md, run sync" clause duplicated the header and was removed, which also paid for the additions. `NNN` is the only placeholder. Five new tests pin these; the previous text fails four of them.
- **Consequences**: Tier 1B room rose from 306 to 311 tokens despite the added precision. The checklist-coverage test had to be anchored to the checklist headings because rule text now mentions the checklists by name.

### ADR-052: Computable Involvement for PRINCIPLE-001 R3 (`sync_principles.py --involved`)
- **Date**: 2026-10-16
- **Status**: Accepted (refines ADR-051)
- **Context**: A third pass ran concrete scenarios through PRINCIPLE-001 instead of re-reading it, and found five places where the text still allowed two readings: (1) *involved* matched any capsule "term" appearing in the failing output, but common words such as "test" and "gate" occur in most capsules, so each model built a different reading list; (2) R3 required reading "before the next command", yet locating and reading a section is itself a command, a loop a strict model cannot satisfy; (3) the user override covered undefined "reading limits", leaving open whether a user could waive the obligation to read; (4) R8 never said how to report a checklist item that does not apply; (5) the Tier 1 header said "never the whole file" without R1's user exception, so Tier-1-only agents saw an absolute ban.
- **Decision**: Make involvement computable rather than better worded. `involved_principles()` matches only backtick-quoted names in capsules (files, paths, scripts, commands) plus principle IDs in the text, with PRINCIPLE-003 as the fallback, and `python scripts/sync_principles.py --involved <text>` prints the list and is authoritative. `--involved` must be the first argument, and everything after it is text, because failing output often contains flags. R3 exempts the commands needed to compute and read the sections; R1 names the two overridable items; R8 counts non-applicable items as passed; the header points to `--involved` and says "unless asked". Tests pin the scenarios, determinism, and that prose words never involve a principle; integration tests pin the CLI contract.
- **Consequences**: Two models given the same paths, commands and output now read the same sections. Tier 1B room is exactly at the 300-token floor on one target, so any further capsule growth will be blocked until other capsules shrink (R9). Unit tier ~0.91s, integration ~3.9s.

### ADR-053: PRINCIPLE-002 Rewritten for a Single Interpretation; Track Computed by `--track`
- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**: Running scenarios through PRINCIPLE-002 found it left the consequential decisions to judgement: (1) R5 said the agent must "remain anchored" under "commit now, skip tests" without saying what to do, or what happens if an informed user insists, while PRINCIPLE-001 R1 defers exactly this question to R5; (2) R3 put "comment updates" in Track B but escalated any change to "executable code" to Track C, so a comment edit in a `.py` file was B or C depending on the model, and it never placed `GUIDELINES.md` edits or CI configuration; (3) Track B's Phase 4 was "scaled to syntax/budget check" with no commands; (4) R2 left the Phase 2 vs Phase 3 recoil choice and "re-run Phase 4" (all gates or the failed one) undefined; (5) R1 and R5 said "gates (tests, dogfooding)" while the real list lives in PRINCIPLE-018 R3; (6) R4 did not say when or how to record the phase; (7) R2 restated test sanctity without PRINCIPLE-014 R2's exception, a drifting copy; (8) LaTeX arrows and "e.g." throughout.
- **Decision**: Make the track computable: `classify_track()` (pure) and `disruption_recovery.py --track` (reads git versus `HEAD`) classify every changed file as B (documentation other than rule text and generated files, or Python whose syntax tree is unchanged apart from docstrings) or C (everything else); no changes is A. R1 enumerates the five phases with their exact commands and requires Phase 4 to pass on the exact tree committed. R2 defines the recoil target by the PRINCIPLE-001 R3 contract-change trigger and requires re-running every Phase 4 command; test changes defer to PRINCIPLE-014 R2. R3 predicts the track before the first edit and re-checks it with `--track` before committing. Phase 4 is the full gate set for both B and C. R4 names the checkpoint command. R5: urgency alone never bypasses gates; an informed, explicit user instruction to commit anyway is allowed and the commit message must end with `Unverified: <gates>`; force-push stays with PRINCIPLE-018 R4. RFC 2119 keywords and audience tags throughout. P002's capsule dropped a clause duplicating PRINCIPLE-018's capsule, which paid for the change and restored margin.
- **Consequences**: Track, phases, recoil and the late-stage answer are now the same for every model. Tests pin the wording, the definitions, cross-references to PRINCIPLE-001/014/018 (so a contradiction like ADR-051's cannot recur silently), checklist ordering, the classifier on 7 cases, and the CLI on a real repository. Tier 1B room 306 tokens. Unit tier ~0.91s, integration ~4.3s.

### ADR-054: PRINCIPLE-002 Second Pass - Bookkeeping Is Track-Neutral, Checkable Recoil, Proportionate Checkpoints
- **Date**: 2026-10-16
- **Status**: Accepted (refines ADR-053)
- **Context**: P002 delegates its most consequential decision to `--track`, so this pass tested the tool on edge cases and followed the rules literally on a real task. Defects found: (1) the ledger write that R4 *requires* turned every task, even Track A, into Track C; (2) R1's "any edit after Phase 4 requires Phase 4 again" fired on the mandatory `--complete` ledger write, an infinite loop for a literal agent - the previous commit followed exactly that sequence; (3) git octal-quotes non-ASCII paths, so a comment-only edit to such a `.py` file was read as a deletion (Track C); (4) R2's "a file outside the Phase 2 plan" was uncheckable and meaningless on Track B; (5) R4 demanded four checkpoints for a typo fix and never closed the task with `--complete`; (6) R5's informed override allowed "commit" but left push open; (7) R5 did not say what happens when a gate fails under user pressure. A pure `.py` rename classifying as Track C was checked and kept: renaming a source file is a contract change under PRINCIPLE-001 R3.
- **Decision**: `.agents/task_ledger.json` written by `disruption_recovery.py` is bookkeeping: ignored by `--track` (`TRACK_NEUTRAL_PATHS`) and never re-triggers Phase 4. `--track` reads `git status --porcelain -z`. R2 recoils to Phase 2 on a contract change or a rising `--track` result. R4: Track C checkpoints every phase, Track B once on entering Phase 3, both `--complete` after Phase 5, one kebab-case task ID. R5: the informed override covers commit and push; a gate failure under pressure goes to R2 and is reported first.
- **Consequences**: Following P002 literally now terminates and keeps documentation tasks on Track B. Tests pin each fix; the integration test exercises the ledger and a non-ASCII path on a real repository. The integration tier is ~4.5s of its 5s budget, so the next integration test needs either a faster fixture or a budget decision.

### ADR-055: PRINCIPLE-002 Third Pass - Commands Must Mean What the Rules Say
- **Date**: 2026-10-16
- **Status**: Accepted (refines ADR-054)
- **Context**: Earlier passes checked P002's wording and the `--track` tool. This pass ran every command P002 names exactly as written and compared the behaviour with the rule. Findings: (1) R4 records a phase on *entering* it, but `--resume` assumed a recorded phase was *finished* and recommended `phase + 1` whenever the tree was clean - after a PRINCIPLE-006 milestone commit during Phase 3 it said "Phase 4", skipping the remaining milestones; (2) R4 said "continue at the phase that report names" while the report names two phases (Last Active, Recommended); (3) PRINCIPLE-007 R6 documents `--phase 2`, which `resolve_phase_num` recorded as Phase 1 because a bare digit matched no phase word, so the Phase 2 checkpoint P002 R1 requires was mis-recorded; (4) the disruption audit counted the ledger as uncommitted work, unlike `--track`; (5) "cold start" in R1 was undefined; (6) the capsule's "B docs/comments" implied rule-file edits are Track B. All existing tests passed throughout - none pinned resume behaviour.
- **Decision**: Resume recommends the recorded phase; R4 names the `Recommended Resumption Phase` line and states that a recorded phase was entered, not finished. `resolve_phase_num` accepts bare digits 1-5. The audit ignores `BOOKKEEPING_PATHS` (renamed from `TRACK_NEUTRAL_PATHS`, now shared with `--track`). R1 defines a cold start; the capsule says "not rule files". A repository-wide parity test checks that every `scripts/*.py` command quoted in the rules exists with the flags given (all currently do). Red-green pins for the three tool defects fail against the pre-fix script.
- **Budget fixes on the way**: the new tests pushed the unit tier to 1.09s and the integration tier to 5.15s. `parse_principles` (40 parses of the same file per run) and `extract_python_symbols` gained content-keyed caches that hand out copies, pinned by a no-leak/no-stale test; a lock test stopped sleeping a full 50ms poll; and the integration test that re-ran the entire unit tier (~1s) was replaced by a module-level guard in `test_kit.py` that fails any unit test the moment it starts a process - stronger, and free. The text gate now forbids spawn *calls* rather than the word `subprocess`.
- **Consequences**: Resumption, phase recording and the audit agree with P002. Unit tier ~0.83s, integration ~3.6s, both well inside budget again.

### ADR-056: PRINCIPLE-003 Rewritten for a Single Interpretation; Its Claims About the Repository Made True
- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**: Wording audit, scenarios and executable-parity checks on PRINCIPLE-003 found: (1) R6 split ambiguity into "data/runtime" (apply a fallback) and "architectural/intent" (stop and ask) with no deciding criterion, so a missing config value made one model guess and another ask; (2) R1's "read its definition" was undefined for files, "re-verify immediately prior" had no trigger, and the codebase map's status as a source was unstated; (3) R2's "grep for all call-sites across the codebase" did not say which files or what to do with hits; (4) "destructive actions" and "structured, concise options" were undefined; no audience tags or RFC 2119 keywords. Executable parity found that AIKit broke its own rules: (5) R3 requires declared dependencies, yet the scripts run `git` in five places while `README.md` declared "Standard Library only"; (6) R7 says the AST gate halts, and it did exit 1, but with a raw traceback, which PRINCIPLE-011 R6 forbids. R4 held: no `shell=True`, `os.system` or hardcoded interpreter in the scripts.
- **Decision**: R6's split is decided by one question - who faces the ambiguity: the running program (documented default with a warning, or a remediation-triad failure) or the agent (ask once, numbered options with their observable difference, no destructive action meanwhile, with "destructive" enumerated). R1: re-read when the file was written since the last read; the codebase map counts only when `update_knowledge_base.py --check` passes; flags come from `--help`. R2: `git grep -n -w <name>` over every tracked file, every hit updated or justified in the commit message, `check_reachability.py` after deletions. R3 defines a dependency, accepts the README `Runtime Prerequisites` line as the manifest for manifest-less repositories, and treats OS-bundled programs such as `taskkill` as platform (R4). `README.md` now declares `git`. R4 lists the concrete code requirements. R7 names the command and its exit behaviour; the CLI now prints the file and line with the triad instead of a traceback, and its bullet is ASCII (cp1254 printed garbage).
- **Shields**: tests pin the wording, the deciding question, defined terms and cross-references; one test derives every program the scripts actually execute and requires it to be declared or OS-bundled; one forbids `shell=True`, `os.system` and hardcoded interpreters in the scripts; an integration test pins the traceback-free AST gate. The previous text and README fail all of them.
- **Budget**: new tests pushed the unit tier to ~1.07s. The reachability checker now parses each file once instead of 3-4 times (content-keyed, read-only trees), and the write-safety tests no-op `fsync` RAII-style since they verify which files are written, not durability. Unit tier ~0.79s, integration ~3.7s.

### ADR-057: PRINCIPLE-003 Second Pass - Working Search Command, ADR Exception, and No Silent Guesses in AIKit's Own Code
- **Date**: 2026-10-16
- **Status**: Accepted (refines ADR-056)
- **Context**: Running the rewritten P003 literally and checking it against the corpus and the code it governs found: (1) R2's prescribed `git grep -n -w <name>` fails for any name starting with `-` - git parses a flag such as `--track` as its own option ("unknown option") - although R2 explicitly covers flags; (2) R2's "update every hit" contradicted PRINCIPLE-016 R3: renaming `record_checkpoint` hits `knowledge/decisions.md` five times, and past ADRs must never be rewritten; (3) R3 let an agent "declare" a new dependency by editing the manifest or README line itself; (4) R6 required a warning "whenever the code uses a default", which read literally covers every omitted optional argument; (5) R6 "ask once" and "stop" left open whether independent work may continue; (6) R4 says documentation uses `python`, yet nine user-facing help and "Fix:" lines said `py scripts/...`, a Windows-only launcher, so P011 R6's copy-paste remediation failed on Linux and macOS; (7) R6 forbids continuing on an undocumented guess, yet `disruption_recovery.py` had six `except Exception: pass/return` blocks (also banned by PRINCIPLE-007 R3). Two were dangerous: an unmeasurable disk silently passed the ENOSPC guard, and an unreadable shadow backup silently became an empty ledger; a failed audit scan reported "clean".
- **Decision**: R2 uses `git grep -n -w -e <name>` (with the reason for `-e`) and exempts `knowledge/decisions.md`. R3 requires the user's explicit approval to declare a new dependency. R6 limits the warning to needed input that is absent, unreadable or malformed, says an omitted optional argument is not missing input, bans `except Exception: pass`, asks in one message and allows independent work to continue. All six handlers now catch specific exceptions; every fallback prints a warning, and the audit records `scan_errors` and reports "Audit incomplete" instead of "Clean state". All `py scripts/` references became `python scripts/`.
- **Shields**: an AST scan rejects any broad, silent exception handler in `scripts/`; a scan rejects `py scripts/` in scripts, `GUIDELINES.md` and `README.md`; behaviour pins for the disk warning, the unreadable backup and the incomplete audit; an integration test runs R2's exact command on a flag. All fail against the pre-fix scripts.
- **Consequences**: P003's commands run as written, it no longer contradicts PRINCIPLE-016, and AIKit's own code follows R6. Unit tier ~0.8s, integration ~3.9s.

### ADR-058: PRINCIPLE-003 Third Pass - Decision-Table Gaps and the Minimum-Runtime Gate
- **Date**: 2026-10-16
- **Status**: Accepted (refines ADR-057)
- **Context**: A decision table of concrete agent situations traced through P003 found situations where no rule fired or two principles disagreed: (1) R1 covered "replacing text" but not overwriting a whole file; (2) no rule covered using syntax or standard-library APIs newer than the declared minimum - the development interpreter is 3.14 while AIKit declares 3.10, so such code would pass every local check and fail for users, and the CI 3.10 leg that would catch it cannot run (ADR-042); (3) R2 and R5 covered parameters and signatures but not a change to what a function returns or raises, the exact class of the `sync_all` return-value change earlier in this session; (4) PRINCIPLE-004 R3 says to consult `codebase_map.md` first, with no freshness condition, while P003 R1 accepts the map only when `--check` passes. AIKit's code currently parses under 3.10 and uses none of the common post-3.10 APIs, so the gap was latent, not yet a defect.
- **Decision**: R1 includes whole-file overwrites and states that map navigation under PRINCIPLE-004 R3 does not satisfy R1 unless the check passes. R4 binds code to the oldest declared runtime. R5 includes return values and raised exceptions. The AST gate (`update_knowledge_base.py`, R7) now parses with `feature_version=MIN_PYTHON` (3, 10), which rejects `except*`, PEP 695 type parameters and `type` statements while accepting 3.10 syntax such as `match`; a test pins that `MIN_PYTHON` matches the README prerequisite. A shield rejects ten common post-3.10 standard-library APIs in scripts and tests; their names are assembled from fragments so the test cannot match its own source.
- **Consequences**: A newer local interpreter can no longer hide syntax that the minimum version rejects; API age remains covered only for the listed names, since the parser cannot see it. YAML and JSON configuration files are still outside R7's gate; the CI workflow has its own structural tests (ADR-041/042), but a general config-validation rule is left for a later pass. Unit tier ~0.85s, integration ~3.8s.

### ADR-059: PRINCIPLE-004 Rewritten for a Single Interpretation; Its Ledger Claims Made True
- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**: Wording audit, executable parity, a decision table and cross-principle checks on P004 found: (1) R1 required persisting multi-step plans "in-place on disk" but no command or ledger field held a plan, so each model would invent its own place or keep it in chat; (2) R1 called the ledger a "bounded rolling window", but pruning exempted the active task - one task kept 60 checkpoints against a cap of 20; (3) R2 prescribed hand-inspecting `active_phase` in the JSON while PRINCIPLE-002 R4 prescribes `--resume` - two procedures for one event - and "never re-prompted" ignored a user who changes a decision and never said where a user's answer is recorded; (4) R4 sent data schemas to `decisions.md`, contradicting PRINCIPLE-016 R5 (`data_models.md` is their single source), and left "architectural choice" and "immediately" undefined; (5) R5 told the agent to re-anchor to the checklists every turn, conflicting with PRINCIPLE-001 R8's checklist timing, and duplicated PRINCIPLE-012 R3's output limits as a "prefer"; (6) R1's "<15 lines" read literally would cap deliverables the user asked for; (7) R3 used one IDE's parameter names (`StartLine`/`EndLine`); no audience tags or RFC 2119 keywords.
- **Decision**: The plan is the `--desc` of the task's Phase 2 checkpoint, revised by recording a new checkpoint; pruning now bounds the active task too and always keeps its plan, and `--resume` prints the plan. R2 defers to PRINCIPLE-002 R4, forbids re-asking anything recorded, follows a user who changes a decision and records the change (new checkpoint or superseding ADR). R3 is tool-neutral with a 100-line cap per read. R4 defines an architectural decision, the ADR deadline (before the next commit, or before the turn ends), and sends schemas to `data_models.md`. R5 bounds tool output by reference to PRINCIPLE-012 R3, requires knowing the current phase each turn, and leaves checklist timing to PRINCIPLE-001 R8. The <15-line cap applies to progress messages, not requested deliverables. The P004 capsule names the mechanisms; "bounded rolling ledger" was removed under PRINCIPLE-001 R2's deletion test (the tool bounds the ledger; no agent action follows), and its capsule test now pins the mechanisms instead.
- **Test budget**: the new pins pushed the unit tier to ~1.35s and, after trimming, it still flapped around 1.0s. Profiling showed 13 file opens costing ~45ms in one test (~3.4ms each on this Windows machine). Pruning is now tested as a pure function, `locked_ledger` gained a `poll_interval` passthrough so the contention test no longer sleeps 50ms, and the write-safety tests read the real `GUIDELINES.md`/`README.md` instead of copying them per test (sync never writes its sources; every write still lands in the sandbox). Unit tier ~0.70s, integration ~4.0s.

### ADR-060: PRINCIPLE-004 Second Pass - The Revised Plan Reaches `--resume`, and the Ledger CLI Stops Guessing
- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**: Running P004's workflow literally (plan, revise plan, record a user answer, resume) found three defects. (1) `task_plan_checkpoint` returned the earliest Phase 2 checkpoint, so a revised plan never reached `--resume`, while R1 said "the latest such checkpoint is the plan"; and since any Phase 2 checkpoint counted, a user's answer recorded in Phase 2 could become "the plan". (2) `--checkpoint --task-id x` recorded task `'task'`: `validate_argv` consumed `--task-id` as the value of `--checkpoint`, and the handler replaced the `--`-prefixed value with a silent default; `--phase-num six` was dropped the same way. (3) `--complete <id>` with an id that is not the active task (or with no id, defaulting to `'active'`) printed `[OK] ... marked as completed`, left the task in progress and appended a false completion checkpoint, so the next `--resume` reopened finished work.
- **Decision**: The plan is the latest Phase 2 checkpoint whose `--desc` starts with `[1/` (`PLAN_MARKER`); R1 says so and forbids that prefix on any other Phase 2 checkpoint. `validate_argv` never consumes a `--` token as a value; the new `argv_value_errors` exits 2 with the remediation triad when a value flag (except the optional `--reset` reason) lacks a value or `--phase-num` is not 1-5. `mark_task_completed` returns whether it completed the active task and changes nothing otherwise; the CLI then exits 1 with `[NOT COMPLETED]`.
- **Consequences**: R1, `--resume` and pruning agree on one plan. Every ledger CLI call that would have been recorded under a guessed value now fails loudly (PRINCIPLE-003 R6). Pinned by three unit tests; the old script fails them.

### ADR-061: PRINCIPLE-004 Third Pass - One Cold-Start Command, One Owner per Limit, No Unobservable Duties
- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**: Reading each P004 sentence as two different models would found places where both could comply and still act differently. (1) Cold start had three answers: P002 R1 said `--audit`, P006 R2 `--audit` or `--resume`, P004 R2 `--resume`. Worse, `--resume` with no interrupted task printed only "Ready for a new task" and hid the modified, untracked and quarantined files that `--audit` showed, so an agent obeying P004 alone could start over someone's uncommitted work. (2) P004 allowed progress messages "within 15 lines" while P012 R4 demanded "<15 lines". (3) "Progress message" versus "deliverable" was left to judgement; "a single read" did not say whether `cat`/`sed -n` or non-code files count; "the agent MUST know its current phase" could not be observed; "refers to it instead" named no form; command output was "bounded" with no number; "public contract" and "beyond the current task" were undefined; a schema change was both an ADR and "not an ADR"; the rule against keeping answers only in chat had no scope and no moment. (4) Report file lists were unbounded.
- **Decision**: `--resume` is the single cold-start command everywhere (P002 R1, P006 R2, P004 R2, README); it now prints every `--audit` finding through the shared `audit_body_lines`, and says "Ready" only with no uncommitted files, otherwise tells the agent not to overwrite them. Every report file list is capped at 20 entries (`append_file_list`). P004 owns the 15-line message limit and P012 R4 points to it; the limit applies to every message before the turn's final message, code blocks included. R1 is scoped to Track C, records a user's answer before the next file edit and forbids reprinting the plan unless asked. R2 adds what to do on `BLOCKED` and on uncommitted files, and requires checking `--resume` and `decisions.md` before asking, newest record winning. R3 defines a read by the commands that print file contents. R4 enumerates public contracts and when a user instruction is architectural; schema fields go to `data_models.md` and the ADR names it. R5 caps one command's output at 100 lines and drops the unobservable "know its phase" (R2 already covers resumption). The capsule states mechanisms (`[1/` plan, `--resume`, no re-asking, 100-line cap) instead of labels; "AST-first" left it for the budget, as R3 still requires search before reading.
- **Consequences**: Tier 1B room is exactly ~300 tokens on the tightest target: the next capsule growth needs a deletion elsewhere. Pinned by six new unit tests that fail on the previous rules and code.

### ADR-062: PRINCIPLE-005 README Drift Shield Becomes a Gate, Not a Fixed List
- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**: P005's "whole-tree drift shield" was one unit test holding a fixed list of 25 AIKit paths. It checked only that those paths existed and that their basenames appeared somewhere in README.md, so it could not see a tracked file missing from the tree (`.gitignore` was), a dead path in the tree unless it was on the list, or a documented flag no script declares. Adopters, who do not copy `tests/`, got none of it. The README also had a table row detached by a blank line and documented `--checkpoint <id> --phase <p>` while PRINCIPLE-002 R4 prescribes `--phase-num`.
- **Decision**: `update_knowledge_base.py` (both modes, and `--check`) runs `audit_readme`: README.md at most 20,000 chars; the labels `Cold-Start Quick Reference`, `**Runtime Prerequisites**:`, `**Canonical Regression Shield Gate**:` and a `What's Inside` heading present; the first ```` ```text ```` block after that heading is the tree, every path in it exists, every top-level tracked entry is in it, and every directory shown with children lists all its tracked children (a directory shown without children is collapsed and exempt); every `python scripts/<x>.py` command names an existing script and only flags it declares, and every `python -m unittest tests.<m>` names an existing module. The audit is pure; only `check_readme` calls `git ls-files`, and without git it warns and skips completeness. README gained `.gitignore`, the reattached row and the P002 R4 checkpoint form; the adopter step now says to add the two labels and a tree.
- **Consequences**: Any adopter whose README lacks the labels or tree fails `update_knowledge_base.py --check` until it adds them, with one line per violation. The fixed list test now calls the same audit; an integration test runs the git-backed check on AIKit.

### ADR-063: PRINCIPLE-005 Rewritten for a Single Interpretation
- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**: Read as two models would, P005 let each decide differently: R1 asked for a "high-visibility orientation block" and orientation "without speculative file browsing", which no one can check, and gave the size twice (20,000 chars and 5,000 tokens); R2's triggers ("public API/UI surfaces", "architectural boundaries") were undefined and its alternative ("update `knowledge/` rather than adding churn") was optional; R3 demanded every README command be "verified to run" with no method; R5's scope was "core entrypoint scripts (e.g. ...)"; R6 was examples only; no rule named its audience. The Post-Flight checklist required README to reflect "all changes", contradicting R2, and the Pre-Flight checklist required reviewing "every active principle", contradicting PRINCIPLE-001 R3.
- **Decision**: R1 names the exact labels and the 20,000-character limit that `audit_readme` (ADR-062) checks. R2 lists its triggers and forbids README edits for any other change. R3 splits commands into those the gate verifies (`python scripts/...`, `python -m unittest tests....`) and all others, which the agent runs before documenting, in a temporary directory when they copy, move or delete. R4 assigns each fact one home by who uses it. R5 defines the tree block, both directions of parity and collapsed directories. R6 maps a non-Python stack onto the same labels. Every rule carries its audience tag. Both checklists now restate their rule exactly. The capsule states mechanisms (size, items, trigger, gate) instead of labels.
- **Consequences**: Tier 1B room stays at ~300 tokens on the tightest targets ("<=20k" replaced "<=20,000" to fit). Pinned by `TestPrinciple005Unambiguity`; every pin fails on the previous text.

### ADR-064: PRINCIPLE-020 Meta-Principle Integrity and Context Budget Adjustment
- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**: The governance system lacked an overarching meta-principle enforcing universal adherence, mutual alignment, cross-principle impact checking on rule changes, and code quality primacy. Individual principles could theoretically be viewed in isolation or interpreted dogmatically to the detriment of coding excellence. Introducing PRINCIPLE-020 required expanding Tier 1 target space while preserving the full 300-token (~1,200 chars) Tier 1B domain reservation. With explicit user instruction and approval pursuant to PRINCIPLE-001 R9, the Tier 1 context budget (`TARGET_TOKEN_BUDGET`) was eligible for a slight increase.
- **Decision**: Added `PRINCIPLE-020: Meta-Principle Integrity & Mutual Alignment (Code Quality Primacy)` to Phase 5 in `GUIDELINES.md` with four core rules: (1) universal mandatory adherence across all tasks, (2) mutual alignment and zero contradiction among principles, (3) mandatory cross-principle impact verification when rules change, and (4) absolute primacy of code quality and craftsmanship over bureaucratic formalism. Increased `TARGET_TOKEN_BUDGET` from 1,500 to 1,600 estimated tokens (with advisory warning at 1,440) in `scripts/sync_principles.py`, `GUIDELINES.md`, and `README.md`. Raised `MIN_PRINCIPLES` and `EXPECTED_PRINCIPLE_COUNT` to 20, synchronized all 6 Tier 1 targets, and added checklist coverage.
- **Consequences**: All 20 principles are active, synchronized across IDE targets, and mutually verified. Tier 1 targets remain budgeted (~1,243 tokens) leaving ~345 tokens (>300 token promise) for Tier 1B domain rules. Pinned by `test_principle_020_meta_principle_capsule` and unit/integration test suites.

### ADR-065: Relocate Meta-Principle to PRINCIPLE-000 under Phase 1 (Zeroth Law Invariant)
- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**: PRINCIPLE-020 was initially appended to Phase 5 (Living Synchronization & Delivery). However, a meta-principle that enforces universal adherence, mutual alignment, rule change cross-checking, and code quality primacy is fundamentally a meta-governance and grounding invariant. Pursuant to PRINCIPLE-002 R6 (Primacy-Weighted Anchoring), grounding rules must precede operational rules in attention order so that agents encounter core behavioral invariants before any procedural rule.
- **Decision**: Relocated the meta-principle to `### PRINCIPLE-000: Meta-Principle Integrity & Mutual Alignment (Code Quality Primacy)` directly under `## 🏛️ Phase 1: Meta-Governance & Attentional Grounding` in `GUIDELINES.md`, superseding its temporary assignment as PRINCIPLE-020. Placed its verification items as the first entry in both the Pre-Flight and Post-Flight Checklists. Updated `tests/test_kit.py` to index principles over `range(0, EXPECTED_PRINCIPLE_COUNT)` and renamed capsule tests to `test_principle_000_meta_principle_capsule`. Updated `README.md` to place PRINCIPLE-000 at the head of the Phase 1 table. Regenerated all 6 Tier 1 targets with `sync_principles.py` so PRINCIPLE-000 renders at the top of `## Core Principles`.
- **Consequences**: Every agent loading any Tier 1 target is primed by the meta-principle first. All 20 principles (`PRINCIPLE-000` through `PRINCIPLE-019`) remain strictly monotonic across phases ($Phase_i \ge Phase_{i-1}$) and ascending by ID within each phase. Verified by 100% test suite pass (209 tests) and all read-only gates.

### ADR-066: Enrich PRINCIPLE-000 with Intent Fidelity, Conflict Resolution, and Falsifiability
- **Date**: 2026-10-16
- **Status**: Accepted
- **Context**: While PRINCIPLE-000 established universal adherence, alignment, cross-checking, and code quality primacy, real-world agent failure modes revealed three remaining risks: (1) malicious compliance where agents exploit syntactic loopholes to satisfy checks while violating engineering intent, (2) ambiguity when principles conflict or pull in competing directions, and (3) rule bloat where untestable wisdom or aspirational platitudes degrade governance clarity.
- **Decision**: Expanded PRINCIPLE-000 in `GUIDELINES.md` with three additional testable rules:
  - Rule 5: Anti-Malicious Compliance & Intent Fidelity (prohibiting superficial shortcuts, dummy tests, and metric gaming).
  - Rule 6: Deterministic Resolution Hierarchy (establishing strict precedence: Secret & State Safety > Empirical Correctness & Verification > Code Quality & Craftsmanship > Token & Resource Frugality).
  - Rule 7: Mechanical Falsifiability & Anti-Vagueness (requiring all added rules to define observable, falsifiable conditions or automated verification tools).
- **Consequences**: Strengthens meta-governance against loophole exploitation and agent degradation. Preserves the Tier 1 invariant capsule and context budget without target bloat. Verified through full unit and integration test suites.

### ADR-067: PRINCIPLE-005 Second Pass - Adopter Template and a Structural Quick Reference Check
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Following README's Option B literally in a scratch adopter repository showed: (1) "paste the Quick Reference section" has two readings; pasting all of it imports AIKit-only lines (`tests.test_kit`, `tests.test_integration`, "both tiers, ~5s", "Standard Library only"), of which the gate caught only the two test modules. (2) The gate checked R1's labels as substrings, so a README that only mentioned them in prose passed, though R1 requires a heading, a prerequisites line naming versions and a fenced test command. (3) A template placeholder left unfilled would have satisfied every label check, the loophole PRINCIPLE-000 R5 forbids.
- **Decision**: AIKit ships `.agents/rules/readme_quickref.md.template` (copied by Option B with `.agents/rules`): the Quick Reference heading, the two labels with `<FILL:` placeholders, AIKit's gate commands and a tree skeleton listing the generated files; nothing AIKit-specific. The adoption step names it instead of "paste the section". `quick_reference_errors` checks R1 structurally inside the Quick Reference section: a heading, a `- **Runtime Prerequisites**:` line containing a version number, and a fenced command directly after `**Canonical Regression Shield Gate**:`. Any `<FILL:` left in README.md fails the gate.
- **Consequences**: The adopter simulation now fails with five exact lines while placeholders remain and passes once they are filled. A unit test audits the shipped template both ways, so the template cannot drift from the gate.

### ADR-068: PRINCIPLE-005 R1 and R6 Name the Section and the Template
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: After ADR-067, R1 still said the labels sit "under" the Quick Reference heading (anywhere after it, or only inside its section?) and that the gate checks "the size, the labels and the tree" while it now checks structure and placeholders too. R6 told non-Python projects what to fill but no adopter where to start, and "lists its build and run commands" had no answer for a project without a build step.
- **Decision**: R1 defines the section as running to the next heading of the same or a higher level (what `quick_reference_errors` uses), forbids a remaining `<FILL:` placeholder and says the gate checks every requirement of the rule. R6 requires every adopter to start from `.agents/rules/readme_quickref.md.template`, forbids copying AIKit's own Quick Reference, and asks for the build and run commands the project has.
- **Consequences**: Rule, template and gate now describe the same README. Pinned in `TestPrinciple005Unambiguity`; the five new pins fail on the previous text.

### ADR-069: ADR IDs Gated as Unique and Consecutive; Two Colliding IDs Renumbered
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: While the PRINCIPLE-000 work wrote ADR-064 to ADR-066, a parallel PRINCIPLE-005 pass appended two more ADRs numbered ADR-064 and ADR-065 from its own memory of the register instead of reading it. The register then held two duplicate IDs out of order, against PRINCIPLE-016 R3's monotonic register, and every gate passed. The defect is the one PRINCIPLE-000 R3 exists to prevent: a change made without checking what other work had already changed.
- **Decision**: `audit_adr_register` requires every `### ADR-NNN:` ID to be exactly one more than the previous one; `update_knowledge_base.py` runs it in both modes and in `--check`. The two later headings were renumbered ADR-067 (PRINCIPLE-005 adopter template) and ADR-068 (PRINCIPLE-005 R1/R6 wording), with the one internal reference and one test comment updated. The renumbering corrects an identifier, not a decision's content; commits fea5691 and bc05769 still cite the old numbers in their messages, where ADR-064 and ADR-065 mean ADR-067 and ADR-068.
- **Consequences**: A duplicate or skipped ADR ID now fails Phase 4 with the ID it expected. Cross-principle check: PRINCIPLE-016 (owns the register; no conflict, the gate enforces its R3), PRINCIPLE-004 R4 (ADR before commit; no conflict), PRINCIPLE-018 R3 (the gate runs inside its existing `--check` command; no new command).

### ADR-070: PRINCIPLE-000 Rewritten to Pass Its Own Falsifiability Rule
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Read against its own R7, PRINCIPLE-000 failed it. R2 resolved "perceived friction" "toward systemic harmony" and R4 forbade interpretations that "degrade code quality", neither naming a decidable condition. R4 and the capsule ("code quality primacy over procedural formalism") let a model that judged a rule unhelpful skip it, while another obeyed it, contradicting R1 and PRINCIPLE-002 R5. R1's exceptions had to be "defined within that principle", but PRINCIPLE-002 R5 overrides PRINCIPLE-018 from outside it. R3 required an evaluation with no observable output, and two sessions' ADRs collided anyway (ADR-069). R5's prohibitions were labels ("metric gaming"). R6 ranked four tiers mixing principles with qualities ("operational convenience"), left fifteen principles unranked and did not separate itself from PRINCIPLE-001 R1's precedence. R7 covered only added rules and no word list. Both checklist items restated the principle instead of a check.
- **Decision**: R1 counts an exception only where a rule's text names it; an agent's judgment never is one. R2 defines a conflict and requires following R6 and reporting it. R3 requires `git grep -n -w -e PRINCIPLE-NNN` over each changed principle and a `Cross-principle check:` line ending the ADR, numbered from the register. R4 turns quality doubts into one question to the user and never a deviation. R5 lists the violating acts. R6 keeps the four tiers, adds a tie rule (the rule that cites the other wins, otherwise ask) and leaves capsule and user conflicts to PRINCIPLE-001 R1. R7 covers added and changed rules, requires an audience tag and lists the banned words, pinned equal to the tests' `HEDGES`. The capsule states the five meta-rules; the README row and both checklist items match.
- **Consequences**: P000 is now pinned by `TestPrinciple000Unambiguity`, whose tests fail on the previous text; ADRs from ADR-070 on whose title names a principle must carry the cross-principle line.
- Cross-principle check: PRINCIPLE-001 (R1 precedence named as the boundary of R6; no conflict), PRINCIPLE-002 (R5 named as an exception; no conflict), PRINCIPLE-003 (R2 search and R6 ask reused; no conflict), PRINCIPLE-004 (R4 ADR timing reused; no conflict), PRINCIPLE-009, PRINCIPLE-012, PRINCIPLE-013, PRINCIPLE-019 (tier membership unchanged; no conflict), PRINCIPLE-014 (R5 loosening needs an ADR, consistent with its test sanctity rule; no conflict), PRINCIPLE-016 (register gate of ADR-069; no conflict).

### ADR-071: PRINCIPLE-000 R5 Applied to AIKit - The Secret Gate Fails Closed
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Auditing AIKit's own code against the acts PRINCIPLE-000 R5 lists found its plainest violation in the secret scanner: when `git` failed, `--staged` warned and `--all` said nothing, then both printed `[OK]` and exited 0 having scanned nothing; an unreadable tracked file or agent-memory file was skipped silently. The pre-commit gate of PRINCIPLE-018 R3 could pass blind. Two ledger paths also hid failures: a `.bak` shadow copy (PRINCIPLE-013) that could not be written, and a corrupted ledger that could not be quarantined and would be read again. The other `except OSError: pass` blocks only clean up after an error already raised or reported.
- **Decision**: Every scan function records each surface it could not scan; `run_scan` then prints `[FAIL] Scan incomplete` with the triad and exits 1, whatever it found elsewhere. The two ledger paths write a `[WARN]` naming the file and the cause; the write or load itself proceeds as before.
- **Consequences**: A secret scan reports clean only after scanning every surface it names. Pinned by a unit test that stubs `git_output` to fail; it fails on the previous scanner.
- Cross-principle check: PRINCIPLE-019 (its gate now fails closed; no conflict), PRINCIPLE-018 (R3 gate exits 1 instead of 0 without git; git is a declared dependency per PRINCIPLE-003 R3; no conflict), PRINCIPLE-013 (backup loss now reported; no conflict), PRINCIPLE-011 (remediation triad on the new failure; no conflict).

### ADR-072: PRINCIPLE-000 Second Pass - A Computed Cross-Principle Set and Decidable R5/R6
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Applying P000 to the repository rather than reading it showed three readings left open. R3 asked the ADR to name "each principle the search found", but `git grep` returns files and lines; which principles a hit in a test, the ledger or a generated file stands for was each model's guess, and hits in `decisions.md` cannot be updated (PRINCIPLE-016 R3). R5's "catching an exception to hide a failure" could not tell the cleanup blocks in `disruption_recovery.py` from the hiding ones ADR-071 fixed. R6 gave no winner when two rules cite each other, and did not define "cites".
- **Decision**: `python scripts/sync_principles.py --citing PRINCIPLE-NNN` prints the principles whose section cites NNN and those NNN's section cites, sections ending at the next heading so the checklists do not count; R3's ADR line names exactly that output, and `decisions.md` and ledger hits are exempt from updating. R5 defines a hiding `except` block: no re-raise, error return, exit or warning, unless it only cleans up after an error already raised or reported. R6 sends mutual citation to the user and defines citing as containing `PRINCIPLE-NNN RN` or `PRINCIPLE-NNN`. README lists `--citing`; the Pre-Flight item names it.
- **Consequences**: Two models changing the same principle now check the same principles. Pinned by unit tests (fixture and the real P000 set) and an integration test of the CLI; the definition pins fail on the previous text.
- Cross-principle check: PRINCIPLE-001 (R1 boundary unchanged; no conflict), PRINCIPLE-002 (R5 exception unchanged; no conflict), PRINCIPLE-003 (R2 search kept, R6 ask reused for mutual citation; no conflict), PRINCIPLE-004 (R4 ADR timing; no conflict), PRINCIPLE-009 (tier unchanged; no conflict), PRINCIPLE-012 (tier unchanged; no conflict), PRINCIPLE-013 (tier unchanged; ADR-071 made its backup loss visible; no conflict), PRINCIPLE-014 (R5 loosening rule unchanged; no conflict), PRINCIPLE-016 (R3 never-edit is why `decisions.md` hits are exempt; no conflict), PRINCIPLE-019 (tier unchanged; no conflict).

### ADR-073: Cross-Principle Check Completeness Gated in `sync_principles.py --check`
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: ADR-072 made the set of principles a rule change must be checked against computable (`--citing`), but whether an ADR actually named that set still rested on the agent: no test can tell from an ADR's text which principles its change touched.
- **Decision**: `sync_principles.py --check` compares `GUIDELINES.md` and `knowledge/decisions.md` at HEAD with the working tree. A principle is changed when its `### PRINCIPLE-NNN:` section differs, ignoring trailing whitespace. Every changed principle needs an ADR added since HEAD with a `Cross-principle check:` line naming every principle `--citing` prints for it; otherwise the check exits 1 naming the missing principles. With no committed `GUIDELINES.md` (git missing, no commit, or the commit that first adds the file) it prints a warning and skips, the documented default of PRINCIPLE-003 R6. `subprocess` is imported only on this path, so `--help` stays fast.
- **Consequences**: Phase 4 now fails a rule change whose ADR lists an incomplete set. Pure functions `changed_principles` and `cross_check_errors` are unit-tested with fixtures; a one-word edit to PRINCIPLE-000 without an ADR was verified to fail the CLI.

### ADR-074: PRINCIPLE-000 Third Pass - R3 Defines a Changed Principle and Names Its Gate
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: R3 required checking "a change to a principle" and ending "the change's ADR" with a cross-principle line, but defined neither: whether a typo fix or a capsule-only edit counted, and which ADR was meant, were each model's call. ADR-073 added the gate that answers both from git.
- **Decision**: R3 now defines a changed principle as one whose `### PRINCIPLE-NNN:` section differs from the last commit, ignoring trailing whitespace; requires an added ADR containing the `Cross-principle check:` line; and names `python scripts/sync_principles.py --check` as the gate that fails until such an ADR names every principle `--citing` prints. The gate's remediation line now says "containing", as R3 does.
- **Consequences**: This change to PRINCIPLE-000 was itself checked by the gate before commit: a first draft of this ADR naming only two principles failed it, listing the eight it omitted.
- Cross-principle check: PRINCIPLE-001 (R1 precedence untouched; no conflict), PRINCIPLE-002 (R5 exception untouched; no conflict), PRINCIPLE-003 (R2 search kept; no conflict), PRINCIPLE-004 (R4 ADR timing: the ADR must now exist before `--check` passes, which Phase 4 already orders; no conflict), PRINCIPLE-009 (tier unchanged; no conflict), PRINCIPLE-012 (tier unchanged; no conflict), PRINCIPLE-013 (tier unchanged; no conflict), PRINCIPLE-014 (no conflict), PRINCIPLE-016 (ADRs added, never edited after commit; no conflict), PRINCIPLE-019 (tier unchanged; no conflict).

### ADR-075: README Rows and `--help` Brought Up to the Gates' Real Behaviour
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: An audit of recent history against PRINCIPLE-005 R2 found four commits that changed when a documented command exits 1 without changing its README row or `--help`: d67b640 and 0999588 made `update_knowledge_base.py --check` also fail on README drift and ADR order (row: "exits 1 on stale codebase map"); 279cac2 made `check_secrets.py` fail when a surface goes unscanned (help: "1 potential secret found"); 7256be3 made `sync_principles.py --check` fail on an incomplete cross-principle ADR (row and help: "exits 1 on rule drift"). The default `update_knowledge_base.py` run also reported every knowledge-base error as `[AST GATE FAILED]` with a syntax-error remediation, though an ADR-ID or link error has nothing to do with syntax.
- **Decision**: The four README rows and both help texts now state every condition that exits 1. Non-syntax failures print `[KNOWLEDGE GATE FAILED]` with their own Why/Fix.
- **Consequences**: The stale rows came from a gap in R2's trigger list, which ADR-076 closes.

### ADR-076: PRINCIPLE-005 Third Pass - Changed Behaviour Triggers README, and the Principle Table Is Generated
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Auditing history against R2 found four commits (ADR-075) that changed when a documented command exits 1 without touching README: R2's triggers named adding, removing or renaming a flag or exit code, and a new reason for an existing exit code matched none of them, so the duty was read as not applying. README's principle table was a hand-written second summary; its rows differed from the capsules for 19 of 20 principles and its titles for 17, some describing mechanisms long replaced, and nothing checked it.
- **Decision**: R2 adds the trigger "changes what a documented command checks, writes or prints, or a condition under which it exits non-zero", pairing the README row with the script's `--help` in the same commit. The principle table is generated by `sync_principles.py` from each principle's phase, title (without its parenthetical subtitle, for README's size budget) and capsule, between `<!-- principles:begin ... -->` and `<!-- principles:end -->`; `--check` fails while it is stale. Only a README inside the synced repository is written, so a test sandbox reading the real README never changes it. A README without markers keeps the old all-or-none ID check. P005 R4 and P017 R4 state this and cite each other.
- **Consequences**: README is 18,934 chars after generation (limit 20,000). The table can no longer drift from the capsules; the four stale rows of ADR-075 are the class R2 now names.
- Cross-principle check: PRINCIPLE-016 (R2 still sends code-level documentation to `knowledge/`; no conflict), PRINCIPLE-017 (R4 now generates the table it used to only check; no conflict), PRINCIPLE-005 (R4 and P017 R4 describe the same mechanism and cite each other; no conflict).

### ADR-077: Ledger and Commit Tooling Enforce What PRINCIPLE-006 Assumes
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Checking P006 against its tooling found three gaps. (1) `validate_conventional_commit` accepted any `[milestone N/M]` text, including `[milestone 3/2]` or `[milestone 1/9]`, though P006 R1 and PRINCIPLE-008 bound it. (2) A `--checkpoint` for a new task while another was still `in_progress` silently replaced the active task: the interrupted work disappeared from `--resume` with no record that it was never completed or reset. Refusing the switch is not an option, because parallel subagents legitimately record different task IDs in one ledger. (3) Under full-suite load a parallel checkpoint crashed with `PermissionError`: on Windows, creating a lock file that another process is deleting raises EACCES, which `file_lock` did not treat as contention. The ledger schema itself was documented nowhere, though PRINCIPLE-004 R4 assigns schemas to `knowledge/data_models.md`.
- **Decision**: A milestone tag must open the description as `[milestone N/M] <text>` with 2 <= M <= 6 and 1 <= N <= M; a one-milestone plan commits untagged. Switching away from an `in_progress` task appends a `superseded` checkpoint for it (its last phase kept) and warns on stderr. `file_lock` retries on `PermissionError`; a real permission fault still ends as `locked_ledger`'s `TimeoutError`. `data_models.md` documents the ledger schema and its four status values.
- **Consequences**: Pinned by unit tests (tags, superseded record, lock retry with a stubbed `os.open`); each fails on the previous code. The parallel-agent integration test passed 3 of 3 full-suite runs after the fix.
- Cross-principle check: PRINCIPLE-006 (tooling now enforces its milestone tag and task switch; no conflict), PRINCIPLE-008 (tag bounds equal its 2 <= M <= 6 horizon; no conflict), PRINCIPLE-013 (lock retry keeps its R3 locking and bounded timeout; no conflict), PRINCIPLE-004 (schema documented where its R4 assigns it; no conflict).

### ADR-078: PRINCIPLE-006 Rewritten for a Single Interpretation; `--clean` Spares Live Buffers
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: P006 left its central duty to judgement ("multi-step tasks or non-trivial implementations", "each logical, verified sub-task") and used words PRINCIPLE-000 R7 bans (`e.g.`, `$\rightarrow$`). Three rules were second, weaker homes for rules owned elsewhere: R2 restated PRINCIPLE-004 R2 with a different trigger, R3 restated PRINCIPLE-013 R1 without fsync and could not apply to edits made with an agent's tools, R6 restated PRINCIPLE-018 R2. R4 conflicted with PRINCIPLE-002 twice: it gated commits on unit tests only, where P002 R1 requires every Phase 4 command, and it forbade the commit P002 R5's informed override allows; it also told the agent to "buffer" failing code in the ledger, which holds descriptions, not code. R5 documented `--phase` where PRINCIPLE-002 R4 prescribes `--phase-num`, and never said when a task counts as abandoned. `--clean` deleted every `*.tmp_*` file, including one a parallel agent or a sync run was writing at that moment.
- **Decision**: R1 commits once per milestone of a plan with 2 to 6 milestones as soon as its Phase 4 passes, and untagged for a one-milestone plan (the validator of ADR-077 enforces the tag). R2, R3 and R6 point to PRINCIPLE-004 R2, PRINCIPLE-013 R1 and PRINCIPLE-018 R2. R4 defers to PRINCIPLE-002 R1/R5 and keeps failing work uncommitted, described by a checkpoint. R5 uses `--phase-num`, defines abandonment and requires `--reset` before the next task's first checkpoint. R6 runs `--clean` when `--resume` lists dangling buffers; `--clean` now deletes only buffers older than 60 seconds (README row and `--help` updated, PRINCIPLE-005 R2). Every rule carries its audience tag; the capsule states mechanisms. The sync summary line names the README table when it is part of the run.
- **Consequences**: Pinned by `TestPrinciple006Unambiguity` and the reworked `--clean` test; every new pin fails on the previous text or code.
- Cross-principle check: PRINCIPLE-002 (R1 gates and R5 override now govern P006 commits; resolves the R4 conflict), PRINCIPLE-004 (R2 is the cold-start audit and R1 the plan; no conflict), PRINCIPLE-008 (milestone horizon 2..6 shared; no conflict), PRINCIPLE-013 (R1 owns atomic writes; no conflict), PRINCIPLE-018 (R2 owns staging; no conflict), PRINCIPLE-014 (no longer cited: P002 R1's Phase 4 includes its test gate; no conflict).

### ADR-079: PRINCIPLE-007's Assessment and Lazy-Code Bans Become Checks
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: P007 R6 required the full impact assessment in the ledger, but the plan checkpoints of the PRINCIPLE-005 and PRINCIPLE-006 passes carried `--why` alone and nothing noticed. P007 R3 listed lazy-code acts (TODO markers, stubs, `NotImplementedError`, silenced type errors) with no check at all.
- **Decision**: `--checkpoint` exits 2 with the remediation triad when a task's first plan checkpoint (Phase 2, `--desc` starting `[1/`, no earlier impact for the task) lacks `--why`, `--benefits`, `--risks` or `--mitigation`, or when `--risks` lacks a verdict for `contract:`, `dependency:`, `concurrency:` or `state:` (R2's dimensions). Plan revisions and Phase 2 notes are not checked. The rule lives in the CLI, not in `record_checkpoint`, so library callers and tests are unaffected. `update_knowledge_base.py` (both modes) fails on a `TODO`/`FIXME`/`XXX`/`HACK` comment marker, a `# type: ignore` or `# noqa` naming no error code, and a function whose body is only `pass`, `...` or `raise NotImplementedError` unless it is abstract, an overload, or declared in a Protocol or ABC. Cleanup `except ...: pass` blocks are not functions and stay allowed (PRINCIPLE-000 R5). README rows and `--help` list the new exit conditions (PRINCIPLE-005 R2).
- **Consequences**: AIKit passes both checks unchanged. Pinned by unit tests for both functions, including the exemptions. The new tests took the unit tier to 0.95s of its 1s limit; stubbing `fsync` in `TestDisruptionRecovery` (its tests check ledger content, never power-loss durability) and shortening one deliberate lock timeout from 50ms to 10ms brought it to 0.71s with every assertion unchanged.
- Cross-principle check: PRINCIPLE-007 (R3 and R6 now checked; no conflict), PRINCIPLE-000 (R5's cleanup exception preserved; no conflict), PRINCIPLE-004 (the plan checkpoint of R1 is the one that carries the assessment; no conflict), PRINCIPLE-005 (R2 README and help updated; no conflict).

### ADR-080: PRINCIPLE-007 Rewritten for a Single Interpretation
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: P007 asked for a "full 4-quadrant impact assessment" without naming the quadrants, next to "4 blast-radius dimensions" with no required output, so the two "4"s were each model's reading. Track B got an undefined "micro-sanity check"; R5 applied to "non-trivial mutations"; R4's scope ceiling ("strictly bounded to the evaluated user goal") had no test; R6 used `--phase 2` where PRINCIPLE-002 R4 prescribes `--phase-num`. R3 banned every `pass`, contradicting the cleanup blocks PRINCIPLE-000 R5 allows, banned casting to `Any` though `Dict[str, Any]` is AIKit's JSON type, banned "demoting polished UI" with no test, and restated rules owned by PRINCIPLE-000, PRINCIPLE-003 and PRINCIPLE-014. No rule named its audience, and both checklist items restated the principle.
- **Decision**: R1 defines the assessment as four fields recorded before a Track C task's first edit; Track A and B have none. R2 makes the risks field four labelled verdicts (`contract:`, `dependency:`, `concurrency:`, `state:`), each concrete risk requiring a mitigation. R3 lists exactly what the ADR-079 gate rejects and points to the owners of the other shortcuts. R4 defines in scope as needed by a plan milestone, fixing a Phase 4 failure met during the task, or asked by the user; anything else is a suggestion in the final message. R5 reports pre-existing changes and never stages them, names the commit before the task as the rollback point (PRINCIPLE-018 R5) and puts every code mitigation in a plan milestone. R6 gives the exact command the CLI enforces and a 4-line chat limit. Every rule has its audience; the capsule and both checklist items state checks.
- **Consequences**: Pinned by `TestPrinciple007Unambiguity`; 30 of its sub-assertions fail on the previous text. PRINCIPLE-000's `--citing` set gains PRINCIPLE-007, which now cites it; the pin of that set was updated accordingly. Test budget: with the ADR-079 gates the integration tier measured 4.6 to 5.4 s against its 5 s budget. The lazy-code scan now shares one parse per file with the codebase map and tokenizes only files containing a marker word (151 ms to 55 ms); dogfood runs its four independent read-only gates concurrently; the `--track` CLI test proves its three git-only behaviours in three spawns instead of five, the B/C distinctions it repeated being pinned in-process by `TestTrackClassification`. The tier now measures 3.9 to 4.1 s.
- Cross-principle check: PRINCIPLE-000 (R4/R5 own quality trade-offs and gaming; R3 no longer bans their allowed cleanup blocks; resolves that conflict), PRINCIPLE-002 (R3 track and R1 Phase 4 reused; no conflict), PRINCIPLE-003 (R3 dependencies and R6 exceptions owned there; no conflict), PRINCIPLE-004 (R4's public-contract list reused for `contract:`; R1 plan carries the assessment; no conflict), PRINCIPLE-008 (mitigations become milestones; no conflict), PRINCIPLE-010 (`concurrency:` dimension; no conflict), PRINCIPLE-013 (`state:` dimension; no conflict), PRINCIPLE-014 (owns weakened-test ban; no conflict), PRINCIPLE-018 (R2 staging and R5 recoil; no conflict).

### ADR-081: PRINCIPLE-008 Rewritten for a Single Interpretation
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: P008 used words PRINCIPLE-000 R7 bans (`non-trivial`, `e.g.`, `$\rightarrow$`) and "target" for its milestone bound. Pillar B's limits (depth 3, fan-out 50) could govern either the code the agent writes or the work it delegates. Bottom-up execution had no test, M > 6 had no consequence, "single architectural domain" no definition, and R3 wrote `type(task)` where PRINCIPLE-006 and PRINCIPLE-018 use `type(scope)`. R5 updated "the active task ledger with refined sub-tasks", contradicting PRINCIPLE-004 R1's rule that a revised plan is a new checkpoint. R6 sent sub-agent results "back to the parent task ledger"; since ADR-077, a sub-agent checkpoint under its own task ID marks the parent task superseded.
- **Decision**: Pillar B bounds delegation (nesting <= 3, <= 50 files or records per brief). R2's test: no milestone uses a symbol a later milestone creates. R3: 1 to 6 milestones; more means separate tasks, each with its own plan, in an order told to the user. R4: a milestone changes one PRINCIPLE-009 layer plus tests and docs unless its plan entry says why two, and passes Phase 4 alone. R5: a revised plan is a new `[1/M']` checkpoint before the next edit. R6: sub-agents never write the ledger; the parent is its only writer. All rules carry audience tags. A shared, data-driven test (`TestRewrittenPrincipleWording`) now pins every principle rewritten from here on.
- **Consequences**: 19 sub-assertions of the new test fail on the previous text.
- Cross-principle check: PRINCIPLE-003 (R1 symbol reality backs the build order; no conflict), PRINCIPLE-004 (R1 owns plan revisions; resolves the R5 conflict), PRINCIPLE-006 (R1 commit format and R4 per-commit gates; no conflict), PRINCIPLE-007 (mitigations become milestones; no conflict), PRINCIPLE-009 (its layers define a milestone's unit; no conflict).

### ADR-082: PRINCIPLE-009 Scoped to Pluggable Boundaries; Its Checkable Parts Gated
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: P009 never said which code its rules cover. Read literally, four layers, constructor injection and immutable DTOs applied to every module, condemning AIKit's own single-module CLIs; read loosely, they applied nowhere. "Presentation" or "data crossing layer boundaries" has no marker in code. Its rules used `e.g.` and `$\rightarrow$`, named no audience, and its decidable parts (junk-drawer names, 1 to 5 methods per role, no circular imports) had no check.
- **Decision**: A *pluggable boundary* is a role with two or more implementations in the repository or the recorded plan; layering (R1), registry selection (R3), constructor injection with a `None` default (R4) and frozen DTOs (R5) apply there, layers sharing one module up to 300 lines. Every module is held to the checkable rules: no `utils`/`util`/`helpers`/`helper`/`common`/`misc` module, roles of 1 to 5 methods, no import cycle, no assignment to another object's `_private` attribute. `update_knowledge_base.py` (both modes) checks the first three over every Python file it maps, reusing the parsed trees (ADR-080); README and `--help` list the new exit condition (PRINCIPLE-005 R2).
- **Consequences**: AIKit passes unchanged (no cycles, no roles, no junk drawers). Pinned by `TestArchitectureGate` and the P009 entry of `TestRewrittenPrincipleWording`; 18 of its sub-assertions fail on the previous text.
- Cross-principle check: PRINCIPLE-000 (no conflict), PRINCIPLE-003 (R3 dependencies: a DI container is one; no conflict), PRINCIPLE-007 (R3 rejects stub implementations of a role; no conflict), PRINCIPLE-008 (milestones are cut by these layers; no conflict), PRINCIPLE-010 (no conflict), PRINCIPLE-011 (zero-config default; no conflict), PRINCIPLE-014 (test doubles via injection; no conflict).

### ADR-083: PRINCIPLE-010 Gets One Number per Limit; Timeouts and `with` Are Gated
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: P010 stated three limits twice with different numbers: concurrency was banned under 20ms and reserved for steps over 200ms (20 to 200ms undefined); the `--help` budget was "<100ms" in the rule but 400ms in dogfood; parallel processes were capped at `os.cpu_count()` while dogfood's new gate pool used one worker per gate. "Unbounded", "high-frequency" and "tight loops" were undefined; R1's ban on whole-payload reads condemned AIKit reading its own small files, and R5's fsync wording clashed with PRINCIPLE-013 R1's fsync per atomic write. R3's timeouts and R4's `with` blocks were decidable but unchecked. No rule named its audience.
- **Decision**: One number each: threads only for steps measured at 200ms or more; `--help` under 200ms as a fresh process (measured medians 47 to 71ms, interpreter start 24ms), enforced by dogfood at the same 200ms; pools of at most `os.cpu_count()` workers (dogfood fixed). Streaming applies to input the program does not control. One fsync per file is PRINCIPLE-013 R1; R5 bans per-record fsyncs into one file. `update_knowledge_base.py` now also fails on a blocking `subprocess` call without `timeout=` and on `open()` outside a `with` (README and `--help` updated). Optimizations that cost readability state a before/after measurement. The shared wording test now matches banned words as whole words ("mentally" had matched "incrementally").
- **Consequences**: AIKit passes unchanged. The capsule was shortened to fit the Tier 1B reservation. 23 sub-assertions fail on the previous text.
- Cross-principle check: PRINCIPLE-007 (`concurrency:` risk dimension; no conflict), PRINCIPLE-011 (fast `--help` and headless use; no conflict), PRINCIPLE-013 (R1's fsync per file is no longer contradicted; resolves that conflict), PRINCIPLE-014 (tier budgets restated identically; no conflict).

### ADR-084: PRINCIPLE-011 Rewritten; Its Dependency Rule Aligned With PRINCIPLE-003
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: P011 R1 required every third-party package to be an optional, gracefully degrading adapter, while PRINCIPLE-003 R3 lets a project declare required dependencies in its manifest: an adopter with a declared required package obeyed one and broke the other. R3 restated PRINCIPLE-003 R6's documented-default rule and R4 restated PRINCIPLE-003 R4's path and command rules, each in different words. R2 relied on "sensible, secure defaults"; R7 only recommended ("should") a `--demo` AIKit does not have. No rule named its audience; `e.g.` and `should` appeared.
- **Decision**: R1: the test command and every CLI run with only the dependencies declared under PRINCIPLE-003 R3, and a dependency of one adapter is imported inside it. R2: create each directory written to; no keyboard read without `--interactive`/`-i`. R3: `os.getenv` with a default, never an `os.environ[...]` read (now failed by `update_knowledge_base.py`; README and `--help` updated), one line naming any fallback mode, no simulated success. R4 points to PRINCIPLE-003 R4 and bans platform-only shell builtins in documented commands. R5: closed stdin never waits; exit codes 0/1/2 defined. R6: the triad's three parts as checkable lines (`Why:`, `Fix:`), no traceback. R7: one read-only state command and one end-to-end demo under 10s, which in AIKit are `--audit` and `dogfood.py`.
- **Consequences**: AIKit passes unchanged. The capsule was shortened to keep the Tier 1B reservation.
- Cross-principle check: PRINCIPLE-003 (R3 owns dependencies, R4 platform rules, R6 documented defaults; resolves the R1 conflict and two duplications), PRINCIPLE-009 (adapter-local imports; no conflict), PRINCIPLE-019 (credentials stay in the environment, read with `os.getenv`; no conflict).

### ADR-085: PRINCIPLE-012 Split by Audience, One Number per Limit
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: P012 mixed two audiences without saying so: rules for code that calls an LLM API (payloads, cache prefixes, schemas, rate limits) and rules for the agent's own output and code. R1 gave a "target" in two units (4,000 tokens / 16,000 chars); R2 promised ">= 80%" cache hits, an outcome the agent cannot check; R3 capped searches by "top-k relevant"; R6 required "step ceilings (K turns)" without requiring K to exist; R7's "maximize syntactic density" and "excessive class hierarchies" had no test. `~`, `concise`, `relevant` and `excessive` are banned by PRINCIPLE-000 R7; no rule named its audience.
- **Decision**: The concept states which rules bind LLM-calling code (R1, R2, R4, R6) and which bind the agent (R3, R5, R7). R1: 16,000 characters per dynamic part. R2: static prefix first and byte-identical. R3: diffs at most 3 context lines, searches at most 50 matches, test summaries; everything else PRINCIPLE-004 R5. R4: schema-declared requests validated before use; chat stays with PRINCIPLE-004 R5. R5: repository-relative paths in prompts, tool inputs and persisted files. R6: backoff with full jitter on 429/529, named step and token caps that checkpoint and stop. R7: three named anti-patterns (pass-through wrappers, one-method classes, single-implementation ABCs without a planned second).
- **Consequences**: Capsule shortened for the Tier 1B reservation.
- Cross-principle check: PRINCIPLE-000 (R7 banned words removed; no conflict), PRINCIPLE-004 (R3 slices, R5 owns message and output limits; no conflict), PRINCIPLE-006 (R5 checkpoint on a tripped cap; no conflict), PRINCIPLE-009 (R1 pluggable boundary decides when an ABC is warranted; no conflict), PRINCIPLE-011 (R6 failure message on schema mismatch; no conflict).

### ADR-086: PRINCIPLE-013 Defines State and Generated Files and Matches AIKit's Code
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: P013 applied to "persistent state" without defining it: AIKit's ledger writer has headroom checks, `.bak` rotation and a retried `os.replace`, while the writers of the Tier 1 files and the codebase map have none of the three, and the rule could be read either way. It gave ranges where the code uses one value (3 to 5 retries, a 2s to 5s lock timeout), "non-trivial atomic writes", "long-running agents" undefined, an R6 startup sweep of `*.tmp_*` that AIKit does not have and that PRINCIPLE-006 R6 replaced with `--clean`, and an R7 outcome ("guaranteeing 100% self-healing") instead of a test list. No rule named its audience.
- **Decision**: A state file is written and read back and cannot be rebuilt from tracked sources; a generated file can. State files get headroom (10MB), temp + fsync + `os.replace` retried up to 5 times + directory fsync, `.bak` rotation, a 3s advisory lock broken after 30s, and the quarantine / `.bak` / migrate load path; generated files get temp + fsync + replace and are repaired by rerunning their generator. Long-running means runs until stopped. Orphan buffers are removed only by `--clean` (PRINCIPLE-006 R6). R7 lists five faults; `TestChaosCoverage` checks each has a test.
- **Consequences**: The rule now describes AIKit's code exactly; no code change was needed. The capsule keeps "os.replace", "fsync" and "advisory locking", which `TestTier1ContextBudget` requires.
- Cross-principle check: PRINCIPLE-000 (no conflict), PRINCIPLE-006 (R6 owns orphan cleanup; resolves the R6 contradiction), PRINCIPLE-007 (`state:` risk dimension; no conflict), PRINCIPLE-010 (R5's one fsync per file is R1 here; no conflict), PRINCIPLE-011 (R6 failure messages; no conflict).

### ADR-087: PRINCIPLE-014 Defines Weakening and One Exception, Shared With PRINCIPLE-000
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Two principles named different exceptions for changing a failing test: PRINCIPLE-014 R2 allowed it only on the user's explicit request, PRINCIPLE-000 R5 counted loosening a test as a violation only "without an ADR", implying an ADR alone sufficed. "Weakening" was undefined, so rewording a pin to new rule text could be read either way. R1 required a test for "every code modification", including behaviour-preserving refactors; R5 ("avoid over-mocking") and R6 ("prioritize hostile paths") had no decidable test; `e.g.` appeared and no rule named its audience.
- **Decision**: R1: a behaviour change adds or changes a test that fails before it and passes after; refactors keep every test unchanged. R2 defines weakening (the test accepts a behaviour it rejected) and its one exception: the user approved the contract change and the ADR names the test and the approval; rewording that rejects the same or more is not weakening. PRINCIPLE-000 R5 now points to R2 for tests and keeps its ADR clause for thresholds, allowlists and budgets. R3 defines flaky (fails on rerun of unchanged code; blocks commits). R5: every test asserts an observable result. R6: red-green for bugs, one invalid-input test per new public function or flag.
- **Consequences**: Applying R2 to this change: `test_principle_014_regression_shield_capsule` had pinned four capsule labels ("test sanctity invariant", "raii fixture reversion", "anti-tautological observable contracts", "hostile & negative path coverage"); it now pins the mechanisms that replaced them. That accepts a capsule without those labels, so it is weakening by R2's definition; the approval is the user's request to rewrite the principles ("Fix whatever you deem necessary"), and this ADR names the test.
- Cross-principle check: PRINCIPLE-000 (R5 now defers to R2 for tests; resolves the conflict), PRINCIPLE-001 (no conflict), PRINCIPLE-002 (Phase 4 runs both tiers; no conflict), PRINCIPLE-003 (no conflict), PRINCIPLE-004 (no conflict), PRINCIPLE-007 (R3 shortcuts; no conflict), PRINCIPLE-009 (test doubles via injection; no conflict), PRINCIPLE-010 (R6 tier budgets identical; no conflict), PRINCIPLE-012 (no conflict), PRINCIPLE-013 (R7 fault tests; no conflict), PRINCIPLE-014 (R2 owns test weakening for both principles; no conflict), PRINCIPLE-016 (no conflict), PRINCIPLE-019 (no conflict).

### ADR-088: PRINCIPLE-015 Says Whose Runner, When It Runs, and Links Its Duplicates
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: `--citing PRINCIPLE-015` printed nothing: P015 cited no principle and none cited it, so the cross-principle check never connected it. Meanwhile R3 restated PRINCIPLE-011's non-interactive rules, R7 set "<15 lines" against PRINCIPLE-004 R5's "at most 15", and R8 restated PRINCIPLE-012 R6's caps. It never said that `scripts/dogfood.py` exercises AIKit's own tools while an adopting project needs its own runner, nor when a run is required. R6 repeated R1. "Concise" is banned by PRINCIPLE-000 R7; no rule named its audience.
- **Decision**: The concept separates AIKit's runner from a project's own. R1 states each product type's pass criterion as a number or observable (10s GUI teardown, rendered root and no `console.error`, real-process CLI with closed stdin, 500ms API answers). R2 names AIKit's supervisor. R3 and R8 point to PRINCIPLE-011 and PRINCIPLE-012 R6. R4 requires a before/after repository fingerprint and forbids writing to home folders. R5 defines the golden path and the hostile input. R7: at most 15 lines on the console, the runner is a PRINCIPLE-018 R3 commit gate run in Phase 4. The capsule keeps `scripts/dogfood.py`, which `sync_principles.py --involved` uses to route a failing dogfood run to P015; a first draft that dropped it was caught by two tests.
- **Consequences**: P015 is now connected to PRINCIPLE-002, -011, -012 and -018 for future cross-principle checks.
- Cross-principle check: PRINCIPLE-002 (R1 Phase 4 runs the runner; no conflict), PRINCIPLE-011 (owns non-interactive duties; resolves the duplication), PRINCIPLE-012 (R6 owns the caps; resolves the duplication), PRINCIPLE-018 (R3 lists the runner as a gate; no conflict), PRINCIPLE-004 (R5's 15-line limit now matched exactly; resolves the off-by-one).

### ADR-089: PRINCIPLE-016 Rewritten; AIKit's Knowledge Base Describes AIKit
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: P016 R2 required "the corresponding `knowledge/` documents" to change with the code without saying which document records which change, or whether a function edit needs a hand-written update when `codebase_map.md` is generated. R3 called ADRs immutable without saying from when, leaving open both editing an ADR before its commit and the ADR-069 renumbering. R5 demanded a `schema_version` field the ledger does not have (it uses `version`). R6 named an IDE tool (`view_file`). No rule named its audience. Meanwhile three of AIKit's own knowledge documents were generic templates: `services.md` showed a non-abstract `raise NotImplementedError` contract that PRINCIPLE-007 R3's gate now rejects; `state_and_ui.md` and `data_models.md` cited the wrong principles (P012 for atomic readers, P007 for non-blocking I/O, P008 for zero-install defaults); `data_models.md` showed a mutable `AppConfig` AIKit does not have; `INDEX.md` called reading it a "mandatory first step" under PRINCIPLE-010 and asked for "relevant" documents.
- **Decision**: R1: documents describe this repository; inapplicable sections say so. R2 maps each kind of change to one document; the map is never hand-edited. R3: an ADR is editable until its commit, then fixed; superseding is a new ADR; the only exception is a register-gate ID correction recorded in a new ADR. R5: a version key and a migration function, `version` in the ledger; the sole-source sentence for schemas is kept. R6 points to PRINCIPLE-004 R3. `services.md` now lists AIKit's six services and their gates, `state_and_ui.md` says AIKit has no UI and describes the ledger lifecycle, `data_models.md` drops the fictitious schema and cites the right principles, and `INDEX.md` routes by search (PRINCIPLE-004 R3).
- **Consequences**: The capsule keeps its pinned mechanism names; the README template rows are unaffected.
- Cross-principle check: PRINCIPLE-000 (R3 register IDs; no conflict), PRINCIPLE-003 (R7 AST gate at the minimum version; no conflict), PRINCIPLE-004 (R3 slices, R4 ADR timing; no conflict), PRINCIPLE-005 (README is not a `knowledge/` document; no conflict), PRINCIPLE-013 (R4 migration; no conflict), PRINCIPLE-018 (R3 runs the gate; no conflict).

### ADR-090: PRINCIPLE-017's Schema Rule Equals What the Generator Validates
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: P017 R1 described a 4-section schema with an optional `Problem`, though every principle has one and PRINCIPLE-000 R7 also requires audience tags; the generator checked neither. R5 enforced phase order "without rigid hardcoded range limits", which no reader can decide. R6 used "~300 tokens", banned by PRINCIPLE-000 R7; R3's "strictly prohibited" named no gate; no rule named its audience.
- **Decision**: `parse_principles` now rejects a principle without `- **Problem**:`; the schema-strictness fixtures gained a `Problem` line each so every case still isolates the section it targets, and a fifth case pins the new check. R1 lists the five sections in order plus audience tags per PRINCIPLE-000 R7 (the tag check joins the generator once PRINCIPLE-018 and -019 carry tags). R2 includes README's table among the generated files; R3 ties the freshness check to PRINCIPLE-018 R3; R5 states the validated rule (nearest Phase heading, non-decreasing, ending in Phase 5); R6 states 1,200 characters. The capsule keeps "context budget check" and "schema compliance", which a test pins.
- **Consequences**: PRINCIPLE-000's `--citing` set gains PRINCIPLE-017 (R1 cites R7); its pin was updated to the computed set.
- Cross-principle check: PRINCIPLE-000 (R7 rule standard referenced; no conflict), PRINCIPLE-005 (README table generation; no conflict), PRINCIPLE-013 (generated files written atomically; no conflict), PRINCIPLE-018 (R3 freshness gate; no conflict).

### ADR-091: PRINCIPLE-018 Rewritten: Honest Gate, User Opt-Out, Full Lists
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: P018 R3 said commits are "mechanically locked" until the gates pass; no hook exists, the agent enforces them. R1 and R4 committed and pushed automatically with no rule for a user who says not to. R2 banned two blind-staging forms and missed `--all`, `-u` and `commit -a`. R4 had no step for a rebase conflict. R5 offered one rollback (`reset --soft HEAD~1`) for both unpushed and pushed commits. R6 asked for a "concise" summary under 10 lines, undefined against a final message that also carries a requested analysis. No rule named its audience.
- **Decision**: R1 commits when Phase 4 passes unless the user said not to, and requires `--validate-commit` before every commit. R2 lists five blind forms. R3 says no hook enforces the triad and lists the exact gate commands. R4 pushes unless told not to, aborts a conflicting rebase and asks. R5 separates unpushed (`reset --soft HEAD^`, written without `~`, which PRINCIPLE-000 R7 bans) from pushed (`revert`) and lists the destructive commands banned on others' changes. R6 lists the facts of each commit the final message gives. The capsule keeps its pinned mechanism names and drops the type list, which `--validate-commit` enforces.
- **Consequences**: None for code; the rule now describes what AIKit's tooling and the agent actually do.
- Cross-principle check: PRINCIPLE-001 (no conflict), PRINCIPLE-002 (R1 Phase 4 = triad items 1 and 2; no conflict), PRINCIPLE-003 (R6 ask on a conflicting rebase; no conflict), PRINCIPLE-006 (R1 milestone commits; no conflict), PRINCIPLE-007 (no conflict), PRINCIPLE-015 (dogfood listed as a gate; no conflict), PRINCIPLE-016 (no conflict), PRINCIPLE-017 (freshness check listed; no conflict), PRINCIPLE-019 (secret scan listed; no conflict).

### ADR-092: PRINCIPLE-019 Matches Its Baseline File; Every Rule Now Names Its Audience
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: P019 R2 listed `credentials*` and `secrets*` (which would also ignore `secrets_scanner.py`) and "cloud CLI config directories", while `.gitignore` ships `credentials`, `credentials.*`, `secrets.*`, `*.jks`, `id_ed25519*` and named cloud directories; nothing compared the two. The Concept repeated the Problem nearly word for word. R5 mentioned an "inline pragma" without naming it; R7 relied on "narrowest scope that works" and "prefer". No rule named its audience. With P019 the last principle without audience tags, PRINCIPLE-000 R7's tag requirement could not yet be enforced by the generator.
- **Decision**: R2 lists exactly the shipped baseline, and a unit test checks `.gitignore` holds every listed pattern. The Concept states the mechanism instead of restating the Problem. R4 sets a redaction format (first 4 characters then `***`); R5 names `# aikit:allow-secret` and the two allowlist sets and requires a commit message saying why; R6 makes the agent tell the user to rotate first; R7 is decidable. `parse_principles` now rejects any numbered rule without an audience tag (PRINCIPLE-017 R1, PRINCIPLE-000 R7), so every principle added from here on carries one.
- **Consequences**: All 20 principles have been rewritten once; the second pass follows.
- Cross-principle check: PRINCIPLE-000 (R7 audience tags now enforced; no conflict), PRINCIPLE-011 (R3 `os.getenv`, R6 failure message; no conflict), PRINCIPLE-018 (R3 lists the scan as a gate; no conflict).

### ADR-093: PRINCIPLE-008 Second Pass - Scenario Gaps Closed
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Running three scenarios through the ADR-081 text gave two answers each: whether "nested more than 3 levels deep" counts the user-facing agent as level 0 or 1; whether a milestone may change three layers when "its plan entry states why it must change two"; and what R5's re-plan does when the revised plan needs more than R3's six milestones.
- **Decision**: The user-facing agent is level 0 and no sub-agent runs deeper than level 3. A milestone may change more than one layer when its plan entry says why. A revision that would exceed six milestones moves the milestones after the current one into a separate task with its own plan.
- **Consequences**: Pinned in `TestRewrittenPrincipleWording`; the new pins fail on the previous text.
- Cross-principle check: PRINCIPLE-003 (no conflict), PRINCIPLE-004 (R1 plan revisions; no conflict), PRINCIPLE-006 (R1 tags stay within 2..6; no conflict), PRINCIPLE-007 (no conflict), PRINCIPLE-009 (layers; no conflict).

### ADR-094: PRINCIPLE-009 Second Pass - A Test Double Is Not a Boundary
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Applied to AIKit's own code, the ADR-082 text read two ways. `run_disruption_audit` takes an injected `git_status` function so tests can pass a double; counting "an adapter and its test double" as a pluggable boundary made R1 demand four separated layers in a 1,200-line CLI module and R2 a Protocol for a single function, while a reader who ignored the double reached the opposite answer.
- **Decision**: A pluggable boundary needs two or more production implementations (in the repository or the plan); a test double alone does not make one, though it is still injected through R4's constructor or parameter default. A role with exactly one operation MAY be declared as a `Callable` type instead of a Protocol.
- **Consequences**: AIKit's injected `git_status` follows R2 and R4 as written; no layering refactor is required. Pinned in `TestRewrittenPrincipleWording`.
- Cross-principle check: PRINCIPLE-000 (no conflict), PRINCIPLE-003 (no conflict), PRINCIPLE-007 (no conflict), PRINCIPLE-008 (no conflict), PRINCIPLE-010 (no conflict), PRINCIPLE-011 (no conflict), PRINCIPLE-012 (R7's single-implementation ABC rule cites R1's boundary, which now excludes test doubles; no conflict), PRINCIPLE-014 (test doubles injected per R4; no conflict).

### ADR-095: PRINCIPLE-010 Second Pass - Where Limits Are Measured; Method-Style `open()`
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Two scenarios still had two answers after ADR-083. The time limits (unit tier 1s, integration 5s, `--help` 200ms) named no machine, so a slow CI runner and a fast laptop could each claim compliance or breach. R4 limited `open()` to `with` statements, but `Path('x').open('w')` outside a `with` was neither clearly covered nor caught by the gate, which matched only the builtin.
- **Decision**: Every time limit is measured on the machine that runs Phase 4, and a breach there is fixed before the commit. R4 covers `open()` and `Path.open()`; a raw descriptor from `os.open` is closed in `try`/`finally`. The gate now also rejects method-style `.open(` outside a `with`, except `os.open`.
- **Consequences**: AIKit passes unchanged. README's code-structure row and `--help` already describe the check. Pinned by a gate fixture and the P010 table entry.
- Cross-principle check: PRINCIPLE-007 (`concurrency:` dimension; no conflict), PRINCIPLE-013 (state writes use temp files in `with`; no conflict), PRINCIPLE-014 (tier limits measured where Phase 4 runs; no conflict).

### ADR-096: PRINCIPLE-011 Second Pass - The Triad as AIKit Prints It
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Checked against real output, R6's "a line starting `Why:`" failed AIKit's own gates literally: every gate prints an indented `   Why:` line on stdout, while usage errors print unindented lines on stderr. The rule named no stream, so one reader could fail every gate's message and another accept any text containing "Why".
- **Decision**: The triad lines are identified by their first non-blank text, `Why:` and `Fix:`, on stdout or stderr; a usage error (exit 2) prints on stderr. All six CLIs were checked with an unknown flag: each exits 2 with one `Why:` and one `Fix:` line on stderr.
- **Consequences**: No code change. Pinned in the P011 table entry.
- Cross-principle check: PRINCIPLE-003 (no conflict), PRINCIPLE-009 (no conflict), PRINCIPLE-012 (R4 schema mismatch uses this message; no conflict), PRINCIPLE-013 (R2/R7 failure messages; no conflict), PRINCIPLE-015 (R6 no traceback; no conflict), PRINCIPLE-019 (R7 missing credential message; no conflict).

### ADR-097: PRINCIPLE-012 Second Pass - Combined Output Limits; the Ledger Stores Relative Paths
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Three scenarios still had two answers after ADR-085. R1 capped "each dynamic part" of a request without defining a part. R3's 50-match search limit and PRINCIPLE-004 R5's 100-line cap overlapped without saying how: 50 matches with three context lines is 200 lines. R5 required repository-relative paths in persisted files, yet `record_checkpoint` stored `files_affected` exactly as given; an absolute path wrote the user's home directory into the tracked ledger.
- **Decision**: R1 applies 16,000 characters to the whole variable tail of one request. R3's limits apply together with PRINCIPLE-004 R5, and the first limit reached stops the output. `repo_relative` converts absolute paths inside the repository to `/`-separated relative paths before the ledger stores them; paths outside the repository stay as given, the exception R5 allows.
- **Consequences**: The committed ledger held no absolute path. Pinned by a unit test of the conversion and the P012 table entry; both fail on the previous text and code.
- Cross-principle check: PRINCIPLE-000 (no conflict), PRINCIPLE-004 (R5's 100-line cap applies together with R3; resolves the overlap), PRINCIPLE-006 (ledger checkpoints; no conflict), PRINCIPLE-009 (no conflict), PRINCIPLE-011 (no conflict), PRINCIPLE-015 (no conflict).

### ADR-098: PRINCIPLE-013 Second Pass - An Unwritable Ledger Explains Itself
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: Running `--checkpoint` against a read-only ledger crashed with a raw `PermissionError` traceback; a lock timeout would have done the same with its own `TimeoutError`. That broke PRINCIPLE-011 R6 (no traceback), R2 of this principle (exit 1 with the triad) and R5, whose "continue with in-memory state" has no meaning for a command that ends after one action.
- **Decision**: The ledger CLI installs `report_operational_error` as `sys.excepthook`: `OSError` and `TimeoutError` print `[LEDGER WRITE FAILED]` with `Why:` and `Fix:` and the process exits 1; any other exception keeps Python's traceback, because it is a bug. R5 now separates a long-running process (continues in memory with one warning) from a command that ends after one action (exits 1 with the triad). `--help` and README's CLI contract say so (PRINCIPLE-005 R2).
- **Consequences**: Verified with a read-only ledger: exit 1, three lines, no traceback. Pinned by a unit test of the hook and the P013 table entry.
- Cross-principle check: PRINCIPLE-000 (R5: no hidden failure; no conflict), PRINCIPLE-006 (ledger writes; no conflict), PRINCIPLE-007 (no conflict), PRINCIPLE-010 (no conflict), PRINCIPLE-011 (R6 triad, R5 exit 1; resolves the traceback), PRINCIPLE-016 (no conflict), PRINCIPLE-017 (no conflict).

### ADR-099: PRINCIPLE-014 Second Pass - Two Duties Become Meta-Tests
- **Date**: 2026-10-17
- **Status**: Accepted
- **Context**: After ADR-087, two P014 duties were still checked only by whoever read the suite: R5's "every test asserts at least one observable result" and R3's "no test makes a network call". An audit found the suite compliant, but nothing would notice the first violation.
- **Decision**: `TestSuiteHygiene` parses both test modules: every `test_` method must call an `assert*` method, `fail`, or contain an `assert` statement, and no test module may import `socket`, `http`, `urllib`, `requests`, `httpx` or `aiohttp`. R3 and R5 name these checks. A temporary test without an assertion was added to confirm the meta-test fails on it, then removed.
- **Consequences**: Assertions on mock calls alone still pass the meta-test; R5's rule that such tests do not count toward R1 stays a review duty.
- Cross-principle check: PRINCIPLE-000 (R5 assertion that cannot fail; no conflict), PRINCIPLE-002 (no conflict), PRINCIPLE-003 (no conflict), PRINCIPLE-007 (no conflict), PRINCIPLE-009 (no conflict), PRINCIPLE-010 (tier budgets; the meta-test is pure AST; no conflict).
