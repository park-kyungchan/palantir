# ODA Observability & Error Handling Patterns

## 1. The Anti-Pattern: Exception Swallowing
During the January 2026 audit, a medium-severity finding was identified in `scripts/mcp_manager.py`:
```python
try:
    config = _read_json(path)
except Exception:
    # No config: ignore
    pass
```
This pattern, while enabling graceful degradation, completely hides diagnostic information when configuration loading fails due to malformed JSON or permissions issues.

## 2. The ODA-Standard Pattern (Graceful Observability)
The remediated code uses specific exception capture and non-intrusive logging:

```python
import logging
logger = logging.getLogger(__name__)

try:
    config = _read_json(path)
except Exception as e:
    # Log the failure for debugging while maintaining fallback logic
    logger.debug("Failed to load Antigravity config from %s: %s", path, e)
```

### 2.1 Key Principles
1. **Never use bare `except:`**: Always capture the error object (`as e`).
2. **Use `logger.debug` for fallbacks**: If an operation is optional and failure is "expected" in some environments, use `debug` level to avoid cluttering production logs while still allowing developers to investigate issues.
3. **Module-level Loggers**: Always instantiate a module-level logger (`logger = logging.getLogger(__name__)`) to allow granular control over log levels per component.

## 3. Implementation in OOW (Orion Ontology Workflow)
All ODA components (Action Runners, Registries, Ingestors) must follow this pattern to ensure that "Self-Healing" logic doesn't become "Silent Failure" logic.

### 3.1 Verification Checklist
- [ ] No `except: pass` or `except Exception: pass` blocks.
- [ ] Exceptions captured and logged with context (file path, action name).
- [ ] Proper use of log levels (`error` for critical failures, `warning` for unexpected but survivable issues, `debug` for optional component failures).
