# Domain Data Models & Schemas

## 📦 Data Structures
The single home of every schema in this repository (**PRINCIPLE-016** R5).

### Task Ledger (`.agents/task_ledger.json`)
Written only by `scripts/disruption_recovery.py` (locked, atomic; PRINCIPLE-013).

| Key | Type | Meaning |
|---|---|---|
| `version` | int | Schema version, `1`; `migrate_ledger_schema` fills missing keys. |
| `active_task` | object or null | `task_id`, `last_phase` (label), `active_phase` (1-5), `status`, `updated_at` (epoch s), optional `impact_assessment` {`why`, `benefits`, `risks`, `mitigation`}. |
| `checkpoints` | list | At most 20 entries (the active task's plan checkpoint is always kept). Each: `task_id`, `phase`, `phase_num` (1-5), `description`, `files_affected`, `status`, `timestamp`, `timestamp_str`, optional `impact_assessment`. |

`status` values: `in_progress` (recorded by `--checkpoint`), `completed` (`--complete`), `abandoned` (`--reset`), `superseded` (written for the previous task when `--checkpoint` names a different task while it was still `in_progress`; ADR-077). The plan is the latest `phase_num` 2 checkpoint whose `description` starts with `[1/` (PRINCIPLE-004 R1).

## 🛡️ Model Invariants
1. Models are type-annotated; data passed between layers is a frozen dataclass or `NamedTuple` (**PRINCIPLE-009** R5).
2. Every setting has a documented default, so a clone runs with no configuration (**PRINCIPLE-011** R2).
3. A persisted model carries a version key (`version` in the ledger) and a migration function that fills missing keys (**PRINCIPLE-013** R4).
