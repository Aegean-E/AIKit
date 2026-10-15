# GitHub Copilot Instructions

All GitHub Copilot interactions in this repository must align with the architectural rules in `AGENTS.md` and `GUIDELINES.md`.
Deterministic Grep Anchor: `Query='### PRINCIPLE-XXX:'` in `GUIDELINES.md`.

## Core Principles Summary (Tier 1 Invariants):
1. **PRINCIPLE-001: Progressive Rule Disclosure & Governance Frugality (Zero Instruction Bloat)**:
   - Two-tier progressive disclosure (<1,500 tokens Tier 1); self-sufficient invariant capsules with deterministic grep anchors (`### PRINCIPLE-XXX:`); slice-view Tier 2 on architectural boundary, regression, or ambiguity.
2. **PRINCIPLE-002: Lifecycle-Aligned Instruction Ordering & Attentional Priming (Cognitive Flow Invariant)**:
   - Monotonic 5-phase lifecycle execution gate (Phase 4 test pass required before Phase 5 delivery); adaptive task pathing (Query/Doc/Eng); immunity to late-stage user priming.
3. **PRINCIPLE-003: Empirical Grounding & Anti-Hallucination Invariant (Verify-Before-Execution)**:
   - Read-before-write slice freshness & call-site check; manifest dependency grounding; platform parity; dual-track ambiguity protocol; strict AST syntax gate.
4. **PRINCIPLE-004: Attentional Drift Prevention & Compaction Resilience (Context Anchor Protocol)**:
   - Disk-backed working memory (`.agents/task_ledger.json`); living plan SSOT; anti-repetition on compaction; AST-first slice retrieval; bounded rolling ledger.
5. **PRINCIPLE-005: AI Cold-Start Readiness & Living Documentation (README Sync)**:
   - Self-describing repo; 30s cold-start orientation (<20k chars); material surface README sync; executable command parity; whole-tree drift shield.
6. **PRINCIPLE-006: Incremental Progress Checkpointing & Disruption Recovery (Zero-Progress-Loss Workflow)**:
   - Incremental atomic micro-commits; pre-flight disruption audit; disruption recovery CLI & ledger (scripts/disruption_recovery.py); explicit micro-staging.
7. **PRINCIPLE-007: Pre-flight Impact & Quality Checklist (Cold-Start Gate)**:
   - Track C impact gate (evaluate why, benefits, 4 blast-radius dimensions, anti-satisficing, scope ceiling, clean reversibility) before non-trivial edits.
8. **PRINCIPLE-008: Hierarchical Problem & Task Decomposition**:
   - Hierarchical decomposition (Goal -> Domain -> Leaf Unit); top-down plan, bottom-up execution; bounded milestones ($2 \le M \le 6$); independent leaf verifiability ($N/M$).
9. **PRINCIPLE-009: Modularity & Pluggable Architecture**:
   - 4-layer architecture (Presentation -> Service -> Domain <- Adapter); role protocols & registry; zero-config constructor DI; immutable DTOs.
10. **PRINCIPLE-010: Performance & Resource Optimization (Speed & Lean Architecture)**:
   - Algorithmic stream efficiency ($O(1)$ memory); non-blocking event-loop hygiene; bounded subprocess timeouts; write-coalescing batch I/O; lazy imports (<100ms startup); sub-second test gate (<1s).
11. **PRINCIPLE-011: Zero-Friction Onboarding & Instant Usability (One-Click Start)**:
   - Pure-stdlib clone-and-run; self-bootstrapping workspace; mode transparency; non-interactive headless parity; deterministic exit codes; remediation triad.
12. **PRINCIPLE-012: Token Frugality & Lean Code Architecture (Context Budgeting)**:
   - Prompt cache prefix alignment (>=80% cache hits); bounded tool outputs & unified diffs; terse schema generation; token budget circuit breakers; lean syntactic density.
13. **PRINCIPLE-013: Crash Resilience, State Atomicity & Power-Loss Recovery (Fail-Safe Operations)**:
   - Resilient atomic writes (flush + os.fsync + retried os.replace + parent-dir fsync); advisory locking on read-modify-write; shadow backups (.bak); schema migration; signal-drain flush; read-only fallback.
14. **PRINCIPLE-014: Automated Test Verification & Continuous Test Coverage (Regression Shield)**:
   - 100% test pass gate (<1s unit tier, <5s integration tier); test sanctity invariant (anti-weakening); RAII fixture reversion (zero state leakage); anti-tautological observable contracts; hostile & negative path coverage.
15. **PRINCIPLE-015: Universal Operational Dogfooding & Chaos Verification (The AI Must Use What It Builds)**:
   - Domain-specific interactive dogfooding (GUI loop / CLI subshell / DOM mount / API probe); portable RAII process tree teardown; ephemeral safety jail (zero host mutation); non-interactive stdin parity; golden path + chaos perturbation; terse reporting (<15 lines).
16. **PRINCIPLE-016: AI Knowledge Base & Continuous Synchronization**:
   - Canonical `knowledge/` sync; atomic code-and-doc pairing (zero drift); monotonic append-only ADR register; strict AST syntax validation; link integrity shield; `scripts/update_knowledge_base.py`.
17. **PRINCIPLE-017: Living Principles System & Automated Synchronization (Auto-Sync Governance)**:
   - Automated cross-IDE rule sync (`scripts/sync_principles.py`); context budget check (<8,000 chars cap, >7,200 char warning); schema compliance; freshness test gate; Tier 1B domain rules injection.
18. **PRINCIPLE-018: Automatic Git Workflow (Commit & Push)**:
   - Automatic conventional commits (`feat`, `fix`, `refactor`, `docs`, `chore`, `test`) + adaptive push; explicit staging (zero `git add .`); pre-commit delivery triad; non-destructive recoil.
19. **PRINCIPLE-019: Secret & Sensitive Data Hygiene (Irreversible Disclosure Shield)**:
   - Zero credentials in tracked files, logs, or ledgers; secrets via env/secret-store only; ignore-list baseline (`.env`, keys, certs); pre-commit secret scan of staged diffs & ledger free-text; redacted diagnostics; rotate-not-revert on exposure.
