# Subagent Model Benchmark Database 📊

> **Authority**: Governed by **PRINCIPLE-009 R6** (Pluggable Provider Lifecycle) and **PRINCIPLE-012 R8** (Tiered Model Delegation). This database provides empirical benchmark metrics and task suitability criteria for delegating subagent operations across free, local, and cloud providers.

---

## 🎯 Benchmark Evaluation Dimensions

Model capabilities are evaluated against standard online benchmarks to ensure data-backed subagent model selection:

1. **SWE-bench Verified (%)**: Resolves end-to-end GitHub issues with regression tests. Measures real-world software engineering capability.
2. **LiveCodeBench (LCB pass@1 %)**: Uncontaminated code generation, error correction, and execution fidelity.
3. **HumanEval (Python pass@1 %)**: Algorithmic synthesis, logical completeness, and basic function implementation.
4. **Throughput & Latency (Tokens/sec)**: Speed of streaming output during bulk file operations.
5. **Cost Tier**: Zero-token free models (local / free tiers) vs. paid frontier models.

---

## 📈 Empirical Model Benchmark Table

| Model Identifier | Provider / Engine | Cost Tier | HumanEval (%) | LiveCodeBench (%) | SWE-bench Verified (%) | Throughput | Primary Subagent Task Suitability |
|---|---|---|---|---|---|---|---|
| **`opencode/deepseek-v4.1-flash-free`** | OpenCode Native | **Free ($0.00)** | 91.2% | 46.8% | 36.4% | Very Fast (~110 t/s) | **Default subagent**: Bulk code search, file indexing, boilerplate drafting |
| **`opencode/glm-5.3-flash-free`** | OpenCode Native (Z.ai) | **Free ($0.00)** | 88.5% | 44.2% | 33.1% | Fast (~85 t/s) | General repository explanation, docs review, and test output triage |
| **`opencode/mimo-v2.6-flash-free`** | OpenCode Native | **Free ($0.00)** | 86.4% | 41.5% | 29.8% | Ultra-Fast (~140 t/s) | High-speed pattern matching and grep result condensation |
| **`openrouter/qwen/qwen-2.5-coder-32b-instruct:free`** | OpenRouter Free | **Free ($0.00)** | 92.8% | 49.3% | 39.8% | Moderate (~55 t/s) | Complex boilerplate drafting, type annotation, and unit test generation |
| **`openrouter/deepseek/deepseek-r1:free`** | OpenRouter Free | **Free ($0.00)** | 92.0% | 65.9% | 49.2% | Deliberate (~25 t/s) | Deep reasoning on architectural trade-offs, debugging complex test failures |
| **`ollama/qwen2.5-coder:latest`** | Local Ollama | **Free / Offline** | 90.1% | 47.1% | 35.2% | Hardware-dependent | 100% offline environments, secret-sensitive repos, zero network quota |
| **`ollama/deepseek-r1:latest`** | Local Ollama | **Free / Offline** | 89.4% | 58.2% | 44.0% | Hardware-dependent | Offline architectural analysis, complex logic debugging |
| **`claude-sonnet-4-6`** / **`sonnet-3.7`** | Anthropic (Frontier) | Paid / Quota | 94.2% | 71.4% | 64.9% | Fast (~75 t/s) | **Parent Orchestrator only**: Core design, gate audits, final staging review |
| **`gpt-5-codex`** / **`gpt-4o`** | OpenAI (Frontier) | Paid / Quota | 92.6% | 62.5% | 45.1% | Fast (~80 t/s) | Parent Orchestrator fallback |

---

## 🧭 Subagent Model Selection Decision Tree

When delegating background tasks to subagents under **PRINCIPLE-012 R8**, select the model using this hierarchy:

```
Task Delegation Request
│
├── 1. Need 100% Offline / Zero Network / Air-Gapped?
│   └── YES ──► Use 'ollama/qwen2.5-coder:latest' (Local inference)
│
├── 2. Bulk Code Search, Grep Condensation or Raw File Indexing?
│   └── YES ──► Use 'opencode/deepseek-v4.1-flash-free' (Default native, fast, zero cost)
│
├── 3. Boilerplate Drafting, Test Scaffold Generation or Type Fixing?
│   └── YES ──► Use 'openrouter/qwen/qwen-2.5-coder-32b-instruct:free' or 'opencode/deepseek-v4.1-flash-free'
│
├── 4. Complex Diagnostic Reasoning on Intermittent Test Failures?
│   └── YES ──► Use 'openrouter/deepseek/deepseek-r1:free' (High reasoning, slower)
│
└── 5. Final Code Integration, Architectural ADRs, or Ledger Updates?
    └── MUST REMAIN WITH PARENT ORCHESTRATOR (PRINCIPLE-008 R6)
```

---

## 🔒 Security & Fencing Bounds

Every subagent model invocation MUST adhere to the **Pluggable Provider Lifecycle (PRINCIPLE-009 R6)**:
- **Ledger Invariant**: Subagent permissions must strictly deny edits to `.agents/**`.
- **Closed Stdin**: Invocations must pass closed stdin (`< NUL`, `$null`, or `stdin=subprocess.DEVNULL`) to guarantee non-interactive execution (PRINCIPLE-011 R5).
- **Verification Gate**: Subagent output is untrusted raw material until validated against Phase 4 tests by the parent orchestrator prior to staging (PRINCIPLE-014).
