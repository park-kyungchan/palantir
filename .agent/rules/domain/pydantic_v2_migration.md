---
description: Pydantic V2 migration requirements to avoid deprecation
---

# Pydantic V2 Migration

## Deprecated Pattern
```python
class Config:
    validate_assignment = True
```

## Required Pattern
```python
from pydantic import ConfigDict

model_config = ConfigDict(validate_assignment=True)
```

## Affected Files
- `scripts/ontology/ontology_types.py`
- `scripts/aip_logic/function.py`

## Reference
- [Pydantic V2 Migration Guide](https://errors.pydantic.dev/2.12/migration/)
