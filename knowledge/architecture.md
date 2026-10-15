# System Architecture & Component Boundaries

## 🏛️ High-Level Architectural Pattern
The application follows a decoupled, modular architecture adhering to **PRINCIPLE-003**:
- **Presentation Layer**: Handles user interactions, command-line arguments, or graphical interface rendering. Never contains raw disk I/O, network calls, or business rules.
- **Service Layer**: Implements domain logic, algorithms, batching, and coordination. Communicates with presentation via callbacks or events.
- **Provider / Adapter Layer**: Decouples external services, APIs, databases, or AI models behind pluggable abstract interfaces.
- **Data Models**: Pure data schemas, configuration models, and immutable transfer objects.

---

## 🧵 Threading & Concurrency Model
- **Non-blocking UI / Event Loop**: Heavy disk scanning, network requests, and computationally intensive tasks run in asynchronous tasks or background worker threads (**PRINCIPLE-007**).
- **Thread Safety**: State transitions and shared data structures are guarded against race conditions.

---

## 💾 Persistence & Atomicity (Fail-Safe Architecture)
- All persistent configuration and state mutations use atomic write patterns (`flush` + `os.fsync` + `os.replace`) to prevent zero-byte truncation during sudden power loss (**PRINCIPLE-012**, **PRINCIPLE-013**).

---

## 🔍 Epistemic Grounding & Anti-Hallucination Invariant
- **Read-Before-Write Protocol**: All code changes, internal references, and type signatures are verified against real disk files and AST symbols prior to execution (**PRINCIPLE-014**).
- **AST Gating**: Automated AST parsing via `scripts/update_knowledge_base.py` guarantees symbol parity and catches hallucinated imports or signatures.

---

## 🧠 Attentional Drift Prevention & State Externalization
- **Disk-Anchored Memory**: In-flight state, task checkpoints, and architectural rationale are externalized immediately to `.agents/task_ledger.json` and `knowledge/decisions.md`, eliminating dependence on volatile conversational context (**PRINCIPLE-015**).
- **Context-Budgeted Retrieval**: Code examination uses slice windows and targeted searches to preserve the LLM attention budget.

---

## 🎮 Operational Dogfooding & Ephemeral Chaos Sandboxing
- **Live System Verification**: Components are interactively exercised across their native runtime surfaces (UI loops, subshells, HTTP clients) prior to shipping (**PRINCIPLE-016**).
- **Zero-Blast-Radius Jail**: Dogfood execution occurs inside ephemeral, synthetic sandbox directories to guarantee safety against accidental user data modification.

---

## ⚡ Progressive Rule Disclosure & Governance Frugality
- **Two-Tier Architecture**: Injected IDE prompt instructions are capped (<1,500 tokens) with terse canonical summaries (Tier 1), while exhaustive guides, edge-case rationale, and failure analysis live in disk-backed knowledge documents (Tier 2) (**PRINCIPLE-017**).
- **Context Overhead Guardrails**: `scripts/sync_principles.py` automatically measures and validates character/token budgets across all generated AI rules, preventing instruction bloat.


