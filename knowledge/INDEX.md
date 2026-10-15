# Codebase Knowledge Base 🧠

> **MANDATORY FIRST STEP FOR AI ASSISTANTS (PRINCIPLE-010):**
> Before designing, refactoring, or editing code, read this index and relevant documents below to achieve full architectural grounding.

---

## 🗺️ Knowledge Base Documents

| Document | Purpose |
|---|---|
| **[`architecture.md`](architecture.md)** | High-level system architecture, boundaries, threading model, and component layout. |
| **[`services.md`](services.md)** | Core business services, API adapters, and pluggable provider abstractions. |
| **[`data_models.md`](data_models.md)** | Domain data classes, configuration schemas, and persistence models. |
| **[`state_and_ui.md`](state_and_ui.md)** | State lifecycle, presentation layer, user feedback, and event flows. |
| **[`decisions.md`](decisions.md)** | Architectural Decision Records (ADR log of trade-offs and rationale). |
| **[`codebase_map.md`](codebase_map.md)** | Auto-generated AST symbol map of all modules, classes, and exported functions. |

---

## ⚡ Maintenance Protocol

1. Whenever any service, architecture, or data model is added or modified, update the matching document in the same commit.
2. Run `python scripts/update_knowledge_base.py` to regenerate `codebase_map.md` and verify document completeness.
