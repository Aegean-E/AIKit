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

