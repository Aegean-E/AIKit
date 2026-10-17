# Codebase Knowledge Base 🧠

> **For AI assistants (PRINCIPLE-016):** find code through `codebase_map.md` or a whole-word search (PRINCIPLE-004 R3); open the document below whose purpose matches the change you are making.

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
| **[`model_benchmarks.md`](model_benchmarks.md)** | Subagent model benchmark database, online empirical metrics, and selection tree. |
| **[`host_clients.md`](host_clients.md)** | Agent host clients, multi-environment portability architecture, and Claude parity. |
| **[`principles_audit_ledger.md`](principles_audit_ledger.md)** | Snapshot audit of the 20 principles at ADR-107, not kept current; its cross-model lines are predictions, not measurements (ADR-117). |

---

## ⚡ Maintenance Protocol

1. Whenever any service, architecture, or data model is added or modified, update the matching document in the same commit.
2. Run `python scripts/update_knowledge_base.py` to regenerate `codebase_map.md` and verify document completeness.
