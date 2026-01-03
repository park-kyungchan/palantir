---
description: Field naming rules to avoid parent class shadowing
---

# Naming Conventions

## Rule
Child class fields MUST NOT shadow parent class attributes.

## Example Violation
```python
class Agent(OntologyObject):
    is_active: bool  # Shadows OntologyObject.is_active
```

## Fix
Use unique field names or override explicitly.

## Affected
- `task_actions.py:Agent.is_active`
