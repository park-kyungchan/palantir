# ODA Workspace Test Plan

> **Version:** 1.0 | **Status:** IN_PROGRESS | **Date:** 2026-01-18
> **Related:** oda_workspace_audit.md

---

## Test Strategy

### Test Levels

| Level | Purpose | Scope |
|-------|---------|-------|
| Unit | Individual component validation | Single hook/command |
| Integration | Component interaction | Hook chains |
| E2E | Full workflow | Complete command execution |

---

## Unit Tests

### UT-001: Hook Existence Verification

**Purpose:** Verify all hooks referenced in settings.json exist on disk

**Script:**
```bash
#!/bin/bash
# test_hook_existence.sh

SETTINGS="/home/palantir/.claude/settings.json"
PASS=0
FAIL=0

echo "=== UT-001: Hook Existence Test ==="

# Extract all hook commands from settings.json
hooks=$(jq -r '.. | .command? // empty' "$SETTINGS" 2>/dev/null | grep -v null | sort -u)

for hook in $hooks; do
  if [ -f "$hook" ]; then
    echo "[PASS] $hook exists"
    ((PASS++))
  else
    echo "[FAIL] $hook MISSING"
    ((FAIL++))
  fi
done

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
```

**Expected:** 0 FAIL (after fixes applied)

---

### UT-002: Hook Permission Check

**Purpose:** Verify all hooks have executable permissions

**Script:**
```bash
#!/bin/bash
# test_hook_permissions.sh

HOOKS_DIR="/home/palantir/.claude/hooks"
PASS=0
FAIL=0

echo "=== UT-002: Hook Permission Test ==="

for hook in "$HOOKS_DIR"/*.sh "$HOOKS_DIR"/*.py; do
  if [ -x "$hook" ]; then
    echo "[PASS] $hook is executable"
    ((PASS++))
  else
    echo "[FAIL] $hook NOT executable"
    ((FAIL++))
  fi
done

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
```

**Expected:** All hooks executable

---

### UT-003: Bash Syntax Validation

**Purpose:** Verify shell scripts have valid syntax

**Script:**
```bash
#!/bin/bash
# test_bash_syntax.sh

HOOKS_DIR="/home/palantir/.claude/hooks"
PASS=0
FAIL=0

echo "=== UT-003: Bash Syntax Test ==="

for script in "$HOOKS_DIR"/*.sh; do
  if bash -n "$script" 2>/dev/null; then
    echo "[PASS] $script syntax OK"
    ((PASS++))
  else
    echo "[FAIL] $script syntax ERROR"
    bash -n "$script" 2>&1
    ((FAIL++))
  fi
done

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
```

**Expected:** All shell scripts pass syntax check

---

### UT-004: Python Syntax Validation

**Purpose:** Verify Python hooks have valid syntax

**Script:**
```bash
#!/bin/bash
# test_python_syntax.sh

HOOKS_DIR="/home/palantir/.claude/hooks"
PASS=0
FAIL=0

echo "=== UT-004: Python Syntax Test ==="

for script in "$HOOKS_DIR"/*.py; do
  if python3 -m py_compile "$script" 2>/dev/null; then
    echo "[PASS] $script syntax OK"
    ((PASS++))
  else
    echo "[FAIL] $script syntax ERROR"
    python3 -m py_compile "$script" 2>&1
    ((FAIL++))
  fi
done

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
```

**Expected:** All Python scripts pass syntax check

---

### UT-005: Command Frontmatter Validation

**Purpose:** Verify command files have required YAML frontmatter

**Script:**
```bash
#!/bin/bash
# test_command_frontmatter.sh

CMDS_DIR="/home/palantir/.claude/commands"
PASS=0
FAIL=0
WARN=0

echo "=== UT-005: Command Frontmatter Test ==="

for cmd in "$CMDS_DIR"/*.md; do
  name=$(basename "$cmd")

  # Check for description
  if grep -q "^description:" "$cmd"; then
    echo "[PASS] $name has description"
    ((PASS++))
  else
    echo "[FAIL] $name missing description"
    ((FAIL++))
  fi

  # Check for allowed-tools (warning only)
  if grep -q "^allowed-tools:" "$cmd" || grep -q "^tools:" "$cmd"; then
    : # OK
  else
    echo "[WARN] $name missing allowed-tools"
    ((WARN++))
  fi
done

echo ""
echo "Results: $PASS passed, $FAIL failed, $WARN warnings"
[ $FAIL -eq 0 ] && exit 0 || exit 1
```

**Expected:** All commands have description field

---

### UT-006: Config YAML Validation

**Purpose:** Verify config files are valid YAML

**Script:**
```bash
#!/bin/bash
# test_config_yaml.sh

CONFIG_DIR="/home/palantir/.claude/hooks/config"
PASS=0
FAIL=0

echo "=== UT-006: Config YAML Test ==="

for config in "$CONFIG_DIR"/*.yaml; do
  if python3 -c "import yaml; yaml.safe_load(open('$config'))" 2>/dev/null; then
    echo "[PASS] $config is valid YAML"
    ((PASS++))
  else
    echo "[FAIL] $config invalid YAML"
    ((FAIL++))
  fi
done

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ $FAIL -eq 0 ] && exit 0 || exit 1
```

**Expected:** All configs are valid YAML

---

## Integration Tests

### INT-001: PreToolUse Hook Chain

**Purpose:** Verify PreToolUse hooks fire in correct order

**Scenario:**
1. Execute a Bash command
2. Verify hook chain: pre-tool-use-oda.sh → governance-check.sh → orchestrator_enforcement.py

**Test Steps:**
```bash
# Enable verbose hook logging
export CLAUDE_HOOK_DEBUG=1

# Trigger PreToolUse
ls -la

# Check audit log
tail -20 ~/.agent/logs/hook_audit.log | grep PreToolUse
```

**Pass Criteria:**
- All configured PreToolUse hooks execute
- Execution order matches settings.json sequence
- No hook errors in log

---

### INT-002: PostToolUse Hook Chain for Task

**Purpose:** Verify PostToolUse hooks fire after Task completion

**Scenario:**
1. Execute `/audit .` command
2. Verify hook chain: progressive_disclosure_hook.py → output_preservation_hook.py → validate_task_result.py

**Test Steps:**
```bash
# Run audit command
/audit .

# Check for L2 file creation
ls -la ~/.agent/outputs/explore/

# Check hook execution log
grep "PostToolUse:Task" ~/.agent/logs/hook_audit.log | tail -10
```

**Pass Criteria:**
- L2 structured report created
- L1 headline returned to main context
- All hooks complete without error

---

### INT-003: Orchestrator Enforcement

**Purpose:** Verify orchestrator blocks direct complex operations

**Scenario:**
1. Attempt complex Bash command (> 200 chars or > 3 pipes)
2. Verify enforcement hook triggers

**Test Steps:**
```bash
# Attempt complex command
find . -name "*.py" | xargs grep "import" | sort | uniq -c | sort -rn | head -20

# Check enforcement log
grep "orchestrator" ~/.agent/logs/orchestrator_violations.log | tail -5
```

**Pass Criteria:**
- Warning or block issued for complex command
- Suggestion to use Task() delegation provided
- Log entry created

---

### INT-004: Progressive Disclosure Output

**Purpose:** Verify verbose output is transformed to L1+L2 format

**Scenario:**
1. Execute `/deep-audit lib/oda/planning`
2. Verify output transformation

**Test Steps:**
```bash
# Run deep audit (produces verbose output)
/deep-audit lib/oda/planning

# Verify L1 headline in response (should be ~100 chars max)
# Verify L2 file created
ls -la ~/.agent/outputs/*/

# Check L2 content has full details
head -50 ~/.agent/outputs/explore/*_structured.md
```

**Pass Criteria:**
- Main context receives only L1 headline
- L2 file contains full structured report
- L3 raw output exists in /tmp/claude/

---

## E2E Tests

### E2E-001: Full /plan Workflow

**Purpose:** Test complete planning workflow

**Test Steps:**
1. Execute `/plan implement user authentication`
2. Verify dual-path analysis runs (ODA + Plan subagent)
3. Verify plan file created
4. Verify TodoWrite updated with 3+ items

**Pass Criteria:**
| Check | Expected |
|-------|----------|
| Plan file exists | `.agent/plans/*.md` |
| TodoWrite items | >= 3 |
| Dual-path L2 reports | 2 files in `.agent/outputs/` |
| User approval prompt | Presented |

---

### E2E-002: Full /execute Workflow

**Purpose:** Test plan execution with orchestrator enforcement

**Prerequisites:** E2E-001 completed with approved plan

**Test Steps:**
1. Execute `/execute .agent/plans/implement_user_authentication.md`
2. Verify ORCHESTRATOR MODE declaration in TodoWrite
3. Verify all work delegated to subagents
4. Verify result verification at each step

**Pass Criteria:**
| Check | Expected |
|-------|----------|
| Orchestrator mode active | First todo item |
| No direct Edit/Write | All via Task() |
| Result verification | No summary-only passes |
| Phase completion | All phases marked done |

---

### E2E-003: Session Lifecycle

**Purpose:** Test session start and end hooks

**Test Steps:**
```bash
# Start new Claude session
claude --new-session

# Verify session start hooks fired
grep "SessionStart" ~/.agent/logs/hook_audit.log | tail -5

# Perform some work
/audit .

# Exit session
exit

# Verify session end hooks fired
grep "SessionEnd" ~/.agent/logs/hook_audit.log | tail -5
```

**Pass Criteria:**
- session-start.sh executed
- welcome.sh executed (first time only)
- setup.sh executed (first time only)
- session-end.sh executed on exit

---

### E2E-004: Auto-Compact Recovery

**Purpose:** Test context recovery after Auto-Compact

**Test Steps:**
1. Start long-running `/plan` that triggers Auto-Compact
2. Verify plan file persists
3. Verify TodoWrite persists
4. Verify recovery possible via `/recover`

**Pass Criteria:**
| Check | Expected |
|-------|----------|
| Plan file intact | Contents unchanged |
| TodoWrite intact | All items present |
| /recover works | Context restored |
| Resume possible | Task(resume=id) works |

---

## Test Execution Order

| Order | Test | Dependencies |
|-------|------|--------------|
| 1 | UT-001 Hook Existence | None |
| 2 | UT-002 Hook Permissions | None |
| 3 | UT-003 Bash Syntax | UT-001 |
| 4 | UT-004 Python Syntax | UT-001 |
| 5 | UT-005 Command Frontmatter | None |
| 6 | UT-006 Config YAML | None |
| 7 | INT-001 PreToolUse Chain | UT-001, UT-002 |
| 8 | INT-002 PostToolUse Chain | UT-001, UT-002 |
| 9 | INT-003 Orchestrator | INT-001 |
| 10 | INT-004 Progressive Disclosure | INT-002 |
| 11 | E2E-001 /plan | INT-001 to INT-004 |
| 12 | E2E-002 /execute | E2E-001 |
| 13 | E2E-003 Session | INT-001 |
| 14 | E2E-004 Recovery | E2E-001 |

---

## Test Results Template

```markdown
## Test Run: YYYY-MM-DD HH:MM

### Unit Tests
| Test | Result | Notes |
|------|--------|-------|
| UT-001 | PASS/FAIL | |
| UT-002 | PASS/FAIL | |
| UT-003 | PASS/FAIL | |
| UT-004 | PASS/FAIL | |
| UT-005 | PASS/FAIL | |
| UT-006 | PASS/FAIL | |

### Integration Tests
| Test | Result | Notes |
|------|--------|-------|
| INT-001 | PASS/FAIL | |
| INT-002 | PASS/FAIL | |
| INT-003 | PASS/FAIL | |
| INT-004 | PASS/FAIL | |

### E2E Tests
| Test | Result | Notes |
|------|--------|-------|
| E2E-001 | PASS/FAIL | |
| E2E-002 | PASS/FAIL | |
| E2E-003 | PASS/FAIL | |
| E2E-004 | PASS/FAIL | |

### Summary
- Total: X tests
- Passed: X
- Failed: X
- Blocked: X
```

---

## Test Automation Script

```bash
#!/bin/bash
# run_oda_tests.sh
# Full ODA workspace test suite

set -e

SCRIPT_DIR="$(dirname "$0")"
RESULTS_FILE=".agent/logs/test_results_$(date +%Y%m%d_%H%M%S).log"

echo "ODA Workspace Test Suite" > "$RESULTS_FILE"
echo "========================" >> "$RESULTS_FILE"
echo "Started: $(date)" >> "$RESULTS_FILE"
echo "" >> "$RESULTS_FILE"

# Run unit tests
echo "Running Unit Tests..."
for test in test_hook_existence test_hook_permissions test_bash_syntax test_python_syntax test_command_frontmatter test_config_yaml; do
  if "$SCRIPT_DIR/$test.sh" >> "$RESULTS_FILE" 2>&1; then
    echo "[PASS] $test"
  else
    echo "[FAIL] $test"
  fi
done

# Run integration tests (manual verification needed)
echo ""
echo "Integration and E2E tests require manual execution."
echo "See: .agent/plans/oda_workspace_test_plan.md"

echo ""
echo "Results saved to: $RESULTS_FILE"
```

---

## Approval Checklist

- [ ] Unit test scripts reviewed
- [ ] Integration test scenarios approved
- [ ] E2E test coverage sufficient
- [ ] Test execution order confirmed
- [ ] Ready to execute tests
