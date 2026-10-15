# GitHub Copilot Instructions

All GitHub Copilot interactions in this repository must align with the architectural rules in `AGENTS.md` and `GUIDELINES.md`.
Deterministic Grep Anchor: `Query='### PRINCIPLE-XXX:'` in `GUIDELINES.md`.

## Core Principles Summary (Tier 1 Invariants):
1. **PRINCIPLE-001: Progressive Rule Disclosure & Governance Frugality (Zero Instruction Bloat)**:
   - Two-tier progressive disclosure (<1,500 tokens Tier 1); self-sufficient invariant capsules with deterministic grep anchors (`### PRINCIPLE-XXX:`); slice-view Tier 2 on architectural boundary, regression, or ambiguity. [GUIDELINES.md#principle-001]
2. **PRINCIPLE-002: Lifecycle-Aligned Instruction Ordering & Attentional Priming (Cognitive Flow Invariant)**:
   - Monotonic 5-phase lifecycle execution gate (Phase 4 test pass required before Phase 5 delivery); adaptive task pathing (Query/Doc/Eng); immunity to late-stage user priming. [GUIDELINES.md#principle-002]
3. **PRINCIPLE-003: Empirical Grounding & Anti-Hallucination Invariant (Verify-Before-Execution)**:
   - Read-before-write slice freshness & call-site check; manifest dependency grounding; platform parity; dual-track ambiguity protocol; strict AST syntax gate. [GUIDELINES.md#principle-003]
4. **PRINCIPLE-004: Attentional Drift Prevention & Compaction Resilience (Context Anchor Protocol)**:
   - Disk-backed working memory (`.agents/task_ledger.json`); living plan SSOT; anti-repetition on compaction; AST-first slice retrieval; bounded rolling ledger. [GUIDELINES.md#principle-004]
5. **PRINCIPLE-005: AI Cold-Start Readiness & Living Documentation (README Sync)**:
   - Self-describing repo; 30s cold-start orientation; material surface README sync; executable command parity. [GUIDELINES.md#principle-005]
6. **PRINCIPLE-006: Incremental Progress Checkpointing & Disruption Recovery (Zero-Progress-Loss Workflow)**:
   - Incremental atomic micro-commits; pre-flight disruption audit; disruption recovery ledger via `scripts/disruption_recovery.py`. [GUIDELINES.md#principle-006]
7. **PRINCIPLE-007: Pre-flight Impact & Quality Checklist (Cold-Start Gate)**:
   - Cold-start impact gate (evaluate why, benefits, risks/harm mitigation, quality non-diminution) before non-trivial edits. [GUIDELINES.md#principle-007]
8. **PRINCIPLE-008: Hierarchical Problem & Task Decomposition**:
   - Hierarchical decomposition (Root -> Domain -> Sub-task -> Atomic); bounded context; recursive validation with base-case limits. [GUIDELINES.md#principle-008]
9. **PRINCIPLE-009: Modularity & Pluggable Architecture**:
   - Single responsibility; abstract provider/service interfaces; decoupled presentation and business logic. [GUIDELINES.md#principle-009]
10. **PRINCIPLE-010: Performance & Resource Optimization (Speed & Lean Architecture)**:
   - Algorithmic efficiency ($O(N)$ scanning, set lookups); non-blocking async execution; lean stdlib-first dependencies. [GUIDELINES.md#principle-010]
11. **PRINCIPLE-011: Zero-Friction Onboarding & Instant Usability (One-Click Start)**:
   - Zero mandatory external dependencies; out-of-the-box defaults; graceful degradation with actionable user guidance. [GUIDELINES.md#principle-011]
12. **PRINCIPLE-012: Token Frugality & Lean Code Architecture (Context Budgeting)**:
   - Concise code; strict token budgets; compact JSON schemas/relative paths; exponential backoff rate-limit guards. [GUIDELINES.md#principle-012]
13. **PRINCIPLE-013: Crash Resilience, State Atomicity & Power-Loss Recovery (Fail-Safe Operations)**:
   - Fail-safe atomic writes (temp buffer -> `flush()` -> `os.fsync()` -> `os.replace()`); WAL for batch ops; isolate `*.corrupt_*`. [GUIDELINES.md#principle-013]
14. **PRINCIPLE-014: Automated Test Verification & Continuous Test Coverage (Regression Shield)**:
   - 100% test pass gate (`python -m unittest discover tests`); fast deterministic isolated unit tests before staging/committing. [GUIDELINES.md#principle-014]
15. **PRINCIPLE-015: Universal Operational Dogfooding & Chaos Verification (The AI Must Use What It Builds)**:
   - Universal operational dogfooding (pump GUI event loop / test CLI / check DOM / API calls); zero-blast-radius test sandbox; terse reporting (<15 lines). [GUIDELINES.md#principle-015]
16. **PRINCIPLE-016: AI Knowledge Base & Continuous Synchronization**:
   - Canonical `knowledge/` sync; auto-update architecture/decisions/codebase map on change; `scripts/update_knowledge_base.py`. [GUIDELINES.md#principle-016]
17. **PRINCIPLE-017: Living Principles System & Automated Synchronization (Auto-Sync Governance)**:
   - Automated cross-IDE rule sync (`scripts/sync_principles.py`); context budget check (<8,000 chars cap); schema compliance. [GUIDELINES.md#principle-017]
18. **PRINCIPLE-018: Automatic Git Workflow (Commit & Push)**:
   - Automatic conventional commits (`feat`, `fix`, `refactor`, `docs`, `chore`, `test`) + git push upon verified task completion. [GUIDELINES.md#principle-018]
