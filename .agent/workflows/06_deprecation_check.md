---
description: Check for deprecation warnings before commit
---

# Deprecation Check Workflow

## Steps

### 1. Run E2E Tests
// turbo
```bash
cd /home/palantir/orion-orchestrator-v2 && source .venv/bin/activate && python -m pytest tests/e2e/ -v --tb=short 2>&1 | grep -i "warning\|deprecated"
```

### 2. Check Pydantic Config
```bash
grep -r "class Config:" scripts/ --include="*.py"
```

### 3. Check Datetime
```bash
grep -r "utcnow()" scripts/ --include="*.py"
```

## Pass Criteria
- Zero deprecation warnings
