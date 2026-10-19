# Core Services & API Abstractions

## 🛠️ Service Registry
AIKit's services are its seven gate CLIs in `scripts/` plus the project CLI `aikit.py`. The seven gate CLIs import nothing from each other; `aikit_cli.py` imports `project_registry.py`, which imports only `atomic_write_json` and `file_lock` from `disruption_recovery.py`, one direction with no cycle (PRINCIPLE-009 R5). The command table in `README.md` lists their flags and exit codes, and `codebase_map.md` lists their functions.

| Service | Responsibility | Gate it provides |
|---|---|---|
| `sync_principles.py` | Generates every Tier 1 file in `TIER1_TARGETS` and README's principle table from `GUIDELINES.md`; computes `--involved` and `--citing` | `--check`: freshness, token budget, cross-principle ADR check (PRINCIPLE-000 R3) |
| `update_knowledge_base.py` | Regenerates `codebase_map.md`; audits README (including every `python aikit.py <cmd>` against the CLI's declared subcommands), the ADR register, unfinished code and code structure (including assignment to another object's `_private` attribute) | `--check` (PRINCIPLE-005, -007, -009 to -011, -016) |
| `disruption_recovery.py` | Task ledger: checkpoints, resume, reset, track, commit-message validation; `--workspace <project>` uses that project's `.aikit/task_ledger.json` (ADR-120) | `--validate-commit`, `--track` (PRINCIPLE-002, -006) |
| `check_reachability.py` | Finds production functions with no production caller and keys read but never written | exit 1 on either (PRINCIPLE-014 R7) |
| `check_secrets.py` | Scans staged changes, tracked files and agent memory for credentials; `--workspace <dir>` scans that repository instead, e.g. a project (ADR-121) | exit 1 on a finding or an unscanned surface (PRINCIPLE-019) |
| `aikit.py` (`aikit_cli.py`) | `new`, `attach`, `list`, `status`, `resume`, `checkpoint`, `complete`, `clean`, `guideline`, `check`, `fix`, `publish`, `delegate`: the projects AIKit builds, each its own folder and git repository (ADR-119) | exit 2 on a bad name or path, 1 on a failed request, with Why/Fix |
| `project_registry.py` | Library behind `aikit.py`: finds projects, detects each one's stacks and test command (`DETECTORS`), writes `.aikit/project.json` and `.aikit/decisions.md` | none; reached through `aikit.py` |
| `project_gates.py` | A project's gates: test command, extras detected from its config (`EXTRA_GATES`), `project.json` `gates` overrides, built-in hygiene scan, guidelines check and secret scan; runs them in the project folder | `python aikit.py check <name>` exits 1 on any failed gate or no test gate (ADR-122) |
| `check_project_hygiene.py` | Scans a project's Python source and static assets: shell/system/exec, non-portable subprocess, unencoded `open()`, any `except` that only discards the error, absolute paths, third-party asset URLs | exit 1 on a finding; built into `aikit check` (ADR-137) |
| `project_publish.py` | Uploads a project's commits to its own GitHub repository (`gh repo create --private --source --remote origin --push`, or a push to an existing `origin`) and auto-pushes after a passing `aikit check`; both first scan exactly the commits they push (`check_secrets.py --commits`: the whole history for a new remote, `@{u}..HEAD` after) and refuse on a finding | `aikit publish` exits 1 on a refusal (ADR-134, ADR-145) |
| `subagent_delegate.py` | Runs one OpenCode sub-agent (roles = `.opencode/agents/*.md`) supervised, stdin closed, with a timeout; reports a ledger changed during the run | `aikit delegate` exits 1 on timeout or a changed ledger (ADR-128) |
| `verify_commit.py` | Checks a commit out into a throwaway worktree and runs the whole gate set there, so a commit that cannot stand alone is caught while it is still local | exit 1 on any failed gate, naming `git reset --soft HEAD^` (PRINCIPLE-018 R7, ADR-149) |
| `dogfood.py` | Runs AIKit's CLIs as real processes in a sandbox: golden path, chaos, gates, `--help` budget | exit 1 on any failed track (PRINCIPLE-015) |

## 📋 Design Rules
1. A service is one module; a role with two or more implementations is declared as a `typing.Protocol` of 1 to 5 methods (PRINCIPLE-009 R1, R2).
2. Each service runs alone with the standard library (PRINCIPLE-011 R1); a shared import goes one direction only (PRINCIPLE-009 R5).
3. A failing service exits 1 with the remediation triad and never prints a traceback (PRINCIPLE-011 R5, R6).
