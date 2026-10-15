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
