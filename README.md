# 🤖 Universal AI Principles & Agent Operating System (Portable Kit)

> **Plug-and-Play AI Assistant Governance, Architecture Principles & Disruption Recovery for Any Software Project.**

This kit contains the complete, battle-tested AI governance system extracted from production development. It ensures that any AI coding assistant (Antigravity IDE, Cursor, Claude Code, GitHub Copilot, Gemini CLI, etc.) follows strict engineering principles, prevents progress loss from unexpected power cuts or crashes, maintains living documentation, and executes automated regression-shielded git workflows.

---

## 📦 What's Inside

```text
portable_agent_kit/
├── README.md                           <- This Integration & Setup Guide
├── AGENTS.md                           <- Master AI Specification & Checklists (All 17 Principles)
├── GUIDELINES.md                       <- Comprehensive Architectural Reference & Problem Index
├── GEMINI.md                           <- Google Gemini & Antigravity IDE rules
├── CLAUDE.md                           <- Anthropic Claude Code configuration
├── .cursorrules                        <- Cursor IDE instructions
├── .github/
│   └── copilot-instructions.md         <- GitHub Copilot instructions
├── .agents/
│   ├── rules/
│   │   └── principles.md               <- Antigravity / Agent IDE workspace rules
│   └── task_ledger.json                <- Disruption ledger for power-loss resilience (WAL)
├── scripts/
│   ├── sync_principles.py              <- Auto-sync engine (syncs all IDE files from AGENTS.md)
│   ├── disruption_recovery.py          <- Power-loss audit, atomic checkpointing & ledger CLI
│   └── update_knowledge_base.py        <- Automatic codebase AST symbol extractor & validator
└── knowledge/
    ├── INDEX.md                        <- Knowledge base table of contents & architecture map
    ├── architecture.md                 <- High-level system architecture and component boundaries
    ├── services.md                     <- Core services, API contracts, and business logic
    ├── data_models.md                  <- Data structures, schemas, and persistence models
    ├── state_and_ui.md                 <- Presentation layer, UI state, and event loops
    ├── decisions.md                    <- Architectural Decision Records (ADRs)
    └── codebase_map.md                 <- Auto-generated AST catalog of classes and functions
```

---

## 🚀 How to Apply to Another Project (2-Minute Setup)

### Step 1: Copy the Files
Copy the contents of `portable_agent_kit/` directly into the root directory of your target repository:

```bash
# Example (from terminal or file explorer):
cp -r portable_agent_kit/* /path/to/your-target-project/
cp -r portable_agent_kit/.* /path/to/your-target-project/ 2>/dev/null || true
```

Ensure the hidden folders (`.agents/`, `.github/`, `.cursorrules`) are copied as well.

### Step 2: Customize Project Name
In `AGENTS.md` and `GUIDELINES.md`, replace `<PROJECT_NAME>` with your project's name (e.g. `MyAwesomeApp`).

### Step 3: Run Principle Synchronization
Run the auto-sync script to programmatically regenerate and align all IDE target rules:

```bash
python scripts/sync_principles.py
```
This automatically updates `GEMINI.md`, `CLAUDE.md`, `.cursorrules`, `.agents/rules/principles.md`, and `.github/copilot-instructions.md`.

### Step 4: Generate Your Knowledge Base
Run the knowledge base AST scanner to automatically index your project's classes and functions:

```bash
python scripts/update_knowledge_base.py
```
This generates `knowledge/codebase_map.md` with every exported class, method, argument, and docstring across your project!

---

## 🏛️ The 17 Core Principles Overview

| Principle | Title | Core Concept |
|---|---|---|
| **PRINCIPLE-001** | Hierarchical Problem Decomposition | Decompose complex or large-scale tasks into bounded recursive sub-tasks; avoid monolithic unbounded context dumps. |
| **PRINCIPLE-002** | Automatic Git Workflow | AI automatically stages, commits ([Conventional Commits](https://www.conventionalcommits.org/)), and pushes verified code changes upon task completion. |
| **PRINCIPLE-003** | Modularity & Pluggable Architecture | Single Responsibility Principle; decoupled business logic; abstract provider interfaces. |
| **PRINCIPLE-004** | Living Principles System (Auto-Sync) | Principles evolve; `scripts/sync_principles.py` automatically synchronizes all AI rules across every IDE format. |
| **PRINCIPLE-005** | AI Cold-Start Readiness & README Sync | Self-describing repository; any cold-starting AI agent can immediately orient itself; mandatory `README.md` sync after every change. |
| **PRINCIPLE-006** | Pre-Flight Impact & Quality Checklist | Cold-start gate evaluating: Why required? Expected benefits? Potential harm/risks? Quality non-diminution guarantee. |
| **PRINCIPLE-007** | Performance & Resource Optimization | $O(N)$ efficiency, non-blocking asynchronous/threaded I/O, lean dependencies, token frugality. |
| **PRINCIPLE-008** | Zero-Friction Onboarding & Instant Usability | "One-click start" out of the box with zero mandatory external app installs; sensible defaults and graceful degradation. |
| **PRINCIPLE-009** | Token Frugality & Lean Code Architecture | Concise code; dense payload serialization (~70% token savings); batch size limits; rate-limit pacing. |
| **PRINCIPLE-010** | AI Knowledge Base & Continuous Sync | Dedicated modular repository in `knowledge/` auto-updated after changes; AST symbol mapping. |
| **PRINCIPLE-011** | Automated Test Verification (Regression Shield) | 100% test pass gate before committing; test-backed modifications; fast (<1s), isolated unit tests. |
| **PRINCIPLE-012** | Crash Resilience & State Atomicity | Fail-safe atomic writes (`flush` + `os.fsync` + `os.replace`); WAL journaling; startup self-healing of corrupted files. |
| **PRINCIPLE-013** | Incremental Checkpointing & Disruption Recovery | Zero progress loss from power outages; micro-milestone commits; task ledger recovery (`scripts/disruption_recovery.py`). |
| **PRINCIPLE-014** | Empirical Grounding & Anti-Hallucination | Read-before-write invariant; verify disk symbols, definitions, and schemas before coding. |
| **PRINCIPLE-015** | Attentional Drift & Compaction Resilience | Context anchor protocol; externalized working memory on disk; slice viewing to protect context window. |
| **PRINCIPLE-016** | Universal Operational Dogfooding & Chaos | Interactive UI/CLI/API dogfooding; zero-blast-radius synthetic sandboxing; offline chaos fuzzing. |
| **PRINCIPLE-017** | Progressive Disclosure & Governance Frugality | Two-tier rule disclosure; strict prompt context budget (<1,500 tokens); zero instruction bloat. |


---

## ⚡ Disruption Recovery & Power-Loss Protection

If electricity cuts out, battery dies, or the computer crashes mid-task:
1. **Pre-flight Audit**: On cold start or when opening a terminal, run:
   ```bash
   python scripts/disruption_recovery.py --audit
   ```
   This automatically detects surviving uncommitted files, modified buffers, and interrupted tasks recorded in `.agents/task_ledger.json`.
2. **Marking Completion**: When a task finishes successfully:
   ```bash
   python scripts/disruption_recovery.py --complete "task_name"
   ```
3. **Atomic File Safety**: All writes use `os.fsync` and temporary staging, guaranteeing that sudden power-downs never leave 0-byte truncated source files. Corrupted JSON files from sudden shutdowns are automatically isolated to `*.corrupt_*` and self-healed.

---

## 🛠️ Adding New Principles to Your Project

1. Add `### PRINCIPLE-018: [Title]` to `AGENTS.md` and `GUIDELINES.md` following the standard schema.
2. Run `python scripts/sync_principles.py`.
3. All target IDE files (`GEMINI.md`, `CLAUDE.md`, `.cursorrules`, `.agents/rules/principles.md`, `.github/copilot-instructions.md`) will instantly reflect the new principle!


