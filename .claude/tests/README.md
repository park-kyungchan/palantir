# Shift-Left Validation Tests

> E2E Integration Tests for Shift-Left Philosophy validation gates

## Overview

The Shift-Left Philosophy ensures early error detection across the E2E pipeline.
These tests validate all 5 gates function correctly.

## Gates Tested

| Gate | Phase | Function | Purpose |
|------|-------|----------|---------|
| 1 | /clarify | `validate_requirement_feasibility()` | Check requirement completeness |
| 2 | /research | `validate_scope_access()` | Verify scope path accessibility |
| 3 | /planning | `pre_flight_checks()` | Validate target files and dependencies |
| 4 | /orchestrate | `validate_phase_dependencies()` | Detect circular/undefined dependencies |
| 5 | /worker | `pre_execution_gate()` | Pre-execution validation |

## Running Tests

```bash
# Run all tests
bash .claude/tests/shift-left-e2e-test.sh

# Check syntax only
bash -n .claude/tests/shift-left-e2e-test.sh
```

## Test Scenarios

### Gate 1: Clarify
- Very brief requirement → Warning
- Normal requirement → Pass
- Non-existent file reference → Warning

### Gate 2: Research
- Non-existent scope path → Fail
- Existing scope path → Pass
- Very broad scope (`.`) → Warning

### Gate 3: Planning
- Non-existent planning document → Fail
- Valid planning document → Pass
- Invalid target paths → Warning

### Gate 4: Orchestrate
- Duplicate phase IDs → Fail
- Undefined dependency → Fail
- Valid dependencies → Pass
- Large number of phases (>10) → Warning

### Gate 5: Worker
- Non-existent task file → Fail
- Valid task with writable targets → Pass
- Task without file specified → Pass

## Expected Output

```
==============================================
GATE 1: Clarify - Requirement Feasibility
==============================================
[TEST 1] Very brief requirement should produce warning
  ✓ PASSED - Expected 'passed_with_warnings', got 'passed_with_warnings'
...

==============================================
TEST SUMMARY
==============================================
Total Tests: 14
Passed: 14
Failed: 0

✓ All tests passed!
```

## Integration with Pipeline

The validation gates are integrated into skills via hooks:

```
/clarify  → Stop hook  → clarify-validate.sh  → Gate 1
/research → Setup hook → research-validate.sh → Gate 2
/planning → Setup hook → planning-preflight.sh → Gate 3
/orchestrate → Setup hook → orchestrate-validate.sh → Gate 4
/worker   → Setup hook → worker-preflight.sh → Gate 5
```

## Files

| File | Purpose |
|------|---------|
| `shift-left-e2e-test.sh` | Main test script |
| `README.md` | This documentation |

## Version History

| Version | Date | Change |
|---------|------|--------|
| 1.0.0 | 2026-01-25 | Initial E2E test suite |
