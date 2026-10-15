# System Architecture & Component Boundaries

## 🏛️ High-Level Architectural Pattern
The application follows a decoupled, modular architecture adhering to **PRINCIPLE-009**:
- **Presentation Layer**: Handles user interactions, command-line arguments, or graphical interface rendering. Never contains raw disk I/O, network calls, or business rules.
- **Service Layer**: Implements domain logic, algorithms, batching, and coordination. Communicates with presentation via callbacks or events.
- **Provider / Adapter Layer**: Decouples external services, APIs, databases, or AI models behind pluggable abstract interfaces.
- **Data Models**: Pure data schemas, configuration models, and immutable transfer objects.

---

## 🧭 5-Phase Execution Pipeline Architecture
The system enforces strict chronological ordering (**PRINCIPLE-002**) across all instructions, agent prompts, and task checkpoints:
1. **Phase 1: Meta-Governance & Attentional Grounding**: Progressive disclosure (<1,500 tokens), cognitive flow sequencing, read-before-write symbol verification, and externalized disk memory.
2. **Phase 2: Pre-Flight Orientation & Planning**: Cold-start documentation, power-loss disruption audit, impact/quality checklist, and hierarchical task decomposition.
3. **Phase 3: Architecture & Lean Implementation**: Pluggable provider modularity, non-blocking asynchronous speed, zero-friction out-of-the-box defaults, and compact token serialization.
4. **Phase 4: Operational Verification & Resilience**: Atomic JSON mutations (`fsync` + `replace`), 100% automated test pass gate, and interactive dogfooding inside ephemeral sandboxes.
5. **Phase 5: Living Synchronization & Delivery**: Active codebase AST synchronization in `knowledge/`, automated cross-IDE rule synchronization, and conventional commit/push workflow.

---

## 🧵 Threading & Concurrency Model
- **Non-blocking UI / Event Loop**: Heavy disk scanning, network requests, and computationally intensive tasks run in asynchronous tasks or background worker threads (**PRINCIPLE-010**).
- **Thread Safety**: State transitions and shared data structures are guarded against race conditions.

---

## 💾 Persistence & Atomicity (Fail-Safe Architecture)
- All persistent configuration and state mutations use atomic write patterns (`flush` + `os.fsync` + `os.replace`) to prevent zero-byte truncation during sudden power loss (**PRINCIPLE-013**, **PRINCIPLE-006**).

---

## 🔍 Epistemic Grounding & Anti-Hallucination Invariant
- **Read-Before-Write Protocol**: All code changes, internal references, and type signatures are verified against real disk files and AST symbols prior to execution (**PRINCIPLE-003**).
- **AST Gating**: Automated AST parsing via `scripts/update_knowledge_base.py` guarantees symbol parity and catches hallucinated imports or signatures.

---

## 🧠 Attentional Drift Prevention & State Externalization
- **Disk-Anchored Memory**: In-flight state, task checkpoints, and architectural rationale are externalized immediately to `.agents/task_ledger.json` and `knowledge/decisions.md`, eliminating dependence on volatile conversational context (**PRINCIPLE-004**).
- **Context-Budgeted Retrieval**: Code examination uses slice windows and targeted searches to preserve the LLM attention budget.

---

## 🎮 Operational Dogfooding & Ephemeral Chaos Sandboxing
- **Live System Verification**: Components are interactively exercised across their native runtime surfaces (UI loops, subshells, HTTP clients) prior to shipping (**PRINCIPLE-015**).
- **Zero-Blast-Radius Jail**: Dogfood execution occurs inside ephemeral, synthetic sandbox directories to guarantee safety against accidental user data modification.

---

## ⚡ Progressive Rule Disclosure & Governance Frugality
- **Two-Tier Architecture**: Injected IDE prompt instructions are capped (<1,500 tokens) with terse, self-sufficient invariant capsules (Tier 1), while exhaustive guides, edge-case rationale, and failure analysis live in disk-backed knowledge documents (Tier 2) (**PRINCIPLE-001**).
- **Self-Sufficient Invariant Capsules**: Every Tier 1 entry contains the exact technical mechanism (e.g., `flush` + `os.fsync` + `os.replace`, 100% test pass gate, read-before-write symbol check), ensuring routine code generation is 100% accurate with zero disk roundtrips.
- **Autonomous Retrieval Trigger Protocol**: Defines explicit operational triggers where an AI agent must slice-view Tier 2 knowledge:
  1. *Architectural Boundary Trigger*: Introducing new services, data schemas, or cross-module API contracts.
  2. *Failure & Regression Trigger*: Test failures, build breakages, or unhandled exceptions.
  3. *Ambiguity Trigger*: Underspecified domain requirements or missing schema models.
- **Universal vs Domain Rule Partitioning (Adopter Architecture)**:
  - *Tier 1A (Universal AI Governance)*: AIKit's immutable 18 engineering invariants (<1,000 tokens).
  - *Tier 1B (Project Domain Invariants)*: Project-specific ironclad conventions defined in `.agents/rules/domain.md` or dedicated prompt section (<300 tokens: framework version, linting, naming conventions).
  - *Tier 2 (Disk Knowledge & Schemas)*: Project architecture, database schemas, and API specs in `knowledge/`.
- **Deterministic Grep Anchor Contract**: All Tier 2 sections use unique regex-safe headers (`### PRINCIPLE-XXX:`). Pointers instruct agents to locate and slice-view the exact 30-line block via single-call grep (`Query="### PRINCIPLE-XXX:"`), eliminating line-number drift across edits.
- **Context Overhead Guardrails**: `scripts/sync_principles.py` automatically measures and mechanically enforces character/token budgets (<8,000 chars / ~1,500 tokens) across all generated AI rules, preventing instruction bloat.
