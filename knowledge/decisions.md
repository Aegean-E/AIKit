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




