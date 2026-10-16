# Domain Data Models & Schemas

## 📦 Data Structures
Document core domain models, configuration schemas, and data transfer objects here.

### Example Schema Pattern
```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class AppConfig:
    """Application configuration schema."""
    version: str = "1.0.0"
    debug_mode: bool = False
    options: List[str] = field(default_factory=list)
```

### Task Ledger (`.agents/task_ledger.json`)
Written only by `scripts/disruption_recovery.py` (locked, atomic; PRINCIPLE-013).

| Key | Type | Meaning |
|---|---|---|
| `version` | int | Schema version, `1`; `migrate_ledger_schema` fills missing keys. |
| `active_task` | object or null | `task_id`, `last_phase` (label), `active_phase` (1-5), `status`, `updated_at` (epoch s), optional `impact_assessment` {`why`, `benefits`, `risks`, `mitigation`}. |
| `checkpoints` | list | At most 20 entries (the active task's plan checkpoint is always kept). Each: `task_id`, `phase`, `phase_num` (1-5), `description`, `files_affected`, `status`, `timestamp`, `timestamp_str`, optional `impact_assessment`. |

`status` values: `in_progress` (recorded by `--checkpoint`), `completed` (`--complete`), `abandoned` (`--reset`), `superseded` (written for the previous task when `--checkpoint` names a different task while it was still `in_progress`; ADR-077). The plan is the latest `phase_num` 2 checkpoint whose `description` starts with `[1/` (PRINCIPLE-004 R1).

## 🛡️ Model Invariants
1. Models must be type-annotated and deterministic.
2. Configuration models must support sensible default values for zero-install immediate execution (**PRINCIPLE-008**).
