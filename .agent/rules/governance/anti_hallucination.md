---
description: Anti-Hallucination enforcement for all protocol stages
---

# Anti-Hallucination Rule

> **V6.0 Enhancement**
> **Enforcement:** All protocol stages must provide evidence of actual file reads

---

## Rule Definition

Stages that pass without `files_viewed` evidence are considered invalid.

## Enforcement Code

```python
# In StageResult
if stage.passed and not stage.has_evidence:
    raise AntiHallucinationError(
        stage=stage.stage.value,
        message="Stage passed without files_viewed evidence"
    )
```

## Validation Mode

| Mode | Behavior |
|------|----------|
| `strict=True` | Raise AntiHallucinationError |
| `strict=False` | Return False (warning) |

## Related

- `StageResult.validate_evidence()`
- `ThreeStageProtocol.execute_with_rsil(strict_evidence=True)`

