# Core Services & API Abstractions

## 🛠️ Service Registry
AIKit's services are its six CLIs in `scripts/`. Each is one module with no import of another (PRINCIPLE-009 R5); the command table in `README.md` lists their flags and exit codes, and `codebase_map.md` lists their functions.

| Service | Responsibility | Gate it provides |
|---|---|---|
| `sync_principles.py` | Generates the six Tier 1 files and README's principle table from `GUIDELINES.md`; computes `--involved` and `--citing` | `--check`: freshness, token budget, cross-principle ADR check (PRINCIPLE-000 R3) |
| `update_knowledge_base.py` | Regenerates `codebase_map.md`; audits README, the ADR register, unfinished code and code structure | `--check` (PRINCIPLE-005, -007, -009 to -011, -016) |
| `disruption_recovery.py` | Task ledger: checkpoints, resume, reset, track, commit-message validation | `--validate-commit`, `--track` (PRINCIPLE-002, -006) |
| `check_reachability.py` | Finds production functions with no production caller and keys read but never written | exit 1 on either (PRINCIPLE-014 R7) |
| `check_secrets.py` | Scans staged changes, tracked files and agent memory for credentials | exit 1 on a finding or an unscanned surface (PRINCIPLE-019) |
| `dogfood.py` | Runs AIKit's CLIs as real processes in a sandbox: golden path, chaos, gates, `--help` budget | exit 1 on any failed track (PRINCIPLE-015) |

## 📋 Design Rules
1. A service is one module; a role with two or more implementations is declared as a `typing.Protocol` of 1 to 5 methods (PRINCIPLE-009 R1, R2).
2. Services share no code by import; each is runnable alone with the standard library (PRINCIPLE-011 R1).
3. A failing service exits 1 with the remediation triad and never prints a traceback (PRINCIPLE-011 R5, R6).
