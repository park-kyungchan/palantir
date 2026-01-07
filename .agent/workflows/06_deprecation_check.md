---
description: Check for deprecation warnings before commit
---

# Deprecation Check Workflow

## Steps

### 1. Run E2E Tests
// turbo
```bash
cd /home/palantir/park-kyungchan/palantir && source .venv/bin/activate && timeout 120 python -m pytest tests/e2e/ -v --tb=short 2>&1 | grep -i "warning\|deprecated" || true
```

### 2. Check Pydantic Config
```bash
grep -r "class Config:" scripts/ --include="*.py" || true
```

### 3. Check Datetime
```bash
grep -r "utcnow()" scripts/ --include="*.py" || true
```

## Pass Criteria
- Zero deprecation warnings
