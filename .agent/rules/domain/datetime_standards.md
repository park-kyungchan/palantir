---
description: Datetime handling standards for timezone-aware operations
---

# Datetime Standards

## Deprecated
```python
datetime.datetime.utcnow()
```

## Required
```python
from datetime import datetime, UTC
datetime.now(UTC)
```

## Affected
- HybridRouter routing decisions
- Timestamp generation

## Reference
- Python 3.12 deprecation notice
