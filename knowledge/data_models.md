# Domain Data Models & Schemas

## 📦 Data Structures
The single home of every schema in this repository (**PRINCIPLE-016** R5).

### Task Ledger (`.agents/task_ledger.json`, and `<project>/.aikit/task_ledger.json` per project)
Written only by `scripts/disruption_recovery.py` (locked, atomic; PRINCIPLE-013). `workspace_ledger_path` picks the project's file when the workspace has an `.aikit/` folder (ADR-120); the schema is the same.

| Key | Type | Meaning |
|---|---|---|
| `version` | int | Schema version, `1`; `migrate_ledger_schema` fills missing keys. A newer version is refused in place; a missing version is treated as legacy `1` in memory only. |
| `active_task` | object or null | `task_id`, `last_phase` (label), `active_phase` (1-5), `status`, `updated_at` (epoch s), optional `impact_assessment` {`why`, `benefits`, `risks`, `mitigation`}. |
| `checkpoints` | list | At most 20 entries (the active task's plan checkpoint is always kept). Each: `task_id`, `phase`, `phase_num` (1-5), `description`, `files_affected`, `status`, `timestamp`, `timestamp_str`, optional `impact_assessment`. |

`status` values: `in_progress` (recorded by `--checkpoint`), `completed` (`--complete`), `abandoned` (`--reset`), `superseded` (written for the previous task when `--checkpoint` names a different task while it was still `in_progress`; ADR-077). The plan is the latest `phase_num` 2 checkpoint whose `description` starts with `[1/` (PRINCIPLE-004 R1).

### Project Record (`<project>/.aikit/project.json`)
Written once by `write_memory` in `scripts/project_registry.py` when a project is created or first attached; never overwritten afterwards, so a person may edit it. Committed in the project's own repository (ADR-119).

| Key | Type | Meaning |
|---|---|---|
| `schema` | int | `1`; any other value is refused by `load_config`. |
| `name` | string | The project name: 1-64 of `a-z 0-9 - _`, starting with a letter or digit. |
| `test_command` | string or null | Overrides the detected test command; null means detect from the project's files on every call. |
| `gates` | object | Gate name to shell command (adds or replaces a gate) or null (disables a detected one); `secrets` cannot be named. Absent in records written before ADR-122, read as empty. |
| `created` | string | Creation date, `YYYY-MM-DD`. |

The project's decision register is `<project>/.aikit/decisions.md`, created from `DECISIONS_TEMPLATE` with the same entry format as `knowledge/decisions.md`; `latest_decision` ignores the template's commented example.

Stacks and test commands are never stored: `detect_stacks` reads the marker files each time, so they cannot go stale.

### Project Guidelines (`<project>/.aikit/guidelines.md`)
The project tier of PRINCIPLE-001 R4: the project's own rules, written by people or agents, ranked below every principle (PRINCIPLE-000 R6). Created from `GUIDELINES_TEMPLATE`; everything after `## Rules` is one rule per line, `- **G-NNN** (source): rule`, where source is `user`, `ADR-NNN` or a person. IDs are never reused. `guideline_errors` (the guidelines gate) rejects a malformed line, a reused ID, a rule worded to override a principle, and a file over `PROJECT_GUIDELINES_MAX_CHARS`; `add_guideline` refuses the same before writing.

### Attached Projects (`projects/attached.json`)
Local to one AIKit checkout (git-ignored). Lists only folders outside `projects/`; folders inside it are found by their `.aikit/project.json`. Written under `file_lock`, atomically. Unreadable content is an error, never an empty list.

| Key | Type | Meaning |
|---|---|---|
| `schema` | int | `1`. |
| `projects` | object | Project name to absolute folder path. |

### Subagent Result Payload
Returned by `delegate_subagent` in `scripts/aikit_cli.py` (`python aikit.py delegate <role> "<task>" --format json`) when executing background tasks delegated to subagents (**PRINCIPLE-008 R1/R6**, **PRINCIPLE-012 R8**).

| Key | Type | Meaning |
|---|---|---|
| `status` | string | `"success"` if process returncode is 0, else `"error"`. |
| `agent` | string | Subagent role invoked (`worker`, `architect`, `coder`, `tester`, `reviewer`, `explorer`). |
| `exit_code` | int | Process exit code (`0` success, `1` operational failure, `2` usage error). |
| `duration_seconds` | float | Execution duration in seconds measured with monotonic clock. |
| `output` | string | Subagent execution findings, suggested diffs, or structured JSON. |
| `ledger_shield` | string | `"unmutated"` confirming task ledgers were shielded against unauthorized modification. |

## 🛡️ Model Invariants
1. Models are type-annotated; data passed between layers is a frozen dataclass or `NamedTuple` (**PRINCIPLE-009** R5).
2. Every setting has a documented default, so a clone runs with no configuration (**PRINCIPLE-011** R2).
3. A persisted model carries a version key (`version` in the ledger) and a migration function that fills missing keys (**PRINCIPLE-013** R4). A reader refuses an unsupported newer version without modifying or quarantining the file; a missing version is accepted only through a documented legacy migration.
