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

## 🛡️ Model Invariants
1. Models must be type-annotated and deterministic.
2. Configuration models must support sensible default values for zero-install immediate execution (**PRINCIPLE-008**).
