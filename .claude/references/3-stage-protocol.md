---
description: 3-Stage Protocol execution guide for ODA
version: "3.0"
enforcement: ANTIGRAVITY_ARCHITECT_V5.0
---

# 3-Stage Protocol Execution Guide

> **Framework:** Ontology-Driven Architecture (ODA)
> **Purpose:** Systematic verification to prevent hallucination and ensure quality
> **Principle:** Evidence-based execution with mandatory file verification

---

## 1. Stage Definitions

| Stage | Goal | Actions | Output |
|-------|------|---------|--------|
| **A: SCAN** | Establish reality | File analysis, requirements gathering, complexity assessment | `StageResult` with evidence |
| **B: TRACE** | Prevent failures | Import verification, signature matching, TDD strategy | `StageResult` with verified imports |
| **C: VERIFY** | Quality gate | Build, tests, lint, type checking | `StageResult` with quality metrics |

---

## 2. Stage A: SCAN

### Purpose
Establish ground truth by reading actual files before any planning or implementation.

### Required Actions
1. **File Discovery** - Identify all relevant files using `Glob` and `Grep`
2. **Content Analysis** - Read files using `Read` tool
3. **Requirements Extraction** - Document functional requirements (FRx)
4. **Complexity Assessment** - Classify task scope

### Evidence Schema

```yaml
stage_a_evidence:
  files_viewed:
    - "path/to/file.py"
    - "path/to/another.py"
  lines_referenced:
    - "file.py:42-58"
    - "another.py:10-25"
  requirements:
    - "FR1: Feature description"
    - "FR2: Another requirement"
  complexity: "small|medium|large"
  code_snippets:
    - snippet: "def existing_function():"
      file: "path/to/file.py"
      line: 42
```

### Complexity Classification

| Level | Criteria | Typical Scope |
|-------|----------|---------------|
| `small` | Single file, < 50 lines changed | Bug fix, minor feature |
| `medium` | 2-5 files, 50-200 lines | New feature, refactoring |
| `large` | 5+ files, 200+ lines | Major feature, architecture change |

### Pass Criteria
- [ ] At least one file read with `Read` tool
- [ ] `files_viewed` list populated (non-empty)
- [ ] Complexity level assigned
- [ ] Requirements documented (if applicable)

### Failure Conditions
- No files read before proceeding
- Empty `files_viewed` evidence
- Assumptions made without file verification

---

## 3. Stage B: TRACE

### Purpose
Verify all dependencies and plan implementation to prevent runtime failures.

### Required Actions
1. **Import Verification** - Confirm all imports exist and are valid
2. **Signature Matching** - Verify function/class signatures match usage
3. **Dependency Graph** - Map relationships between components
4. **Test Strategy** - Define TDD approach

### Evidence Schema

```yaml
stage_b_evidence:
  imports_verified:
    - "from module import Class"
    - "from package.submodule import function"
  signatures_matched:
    - signature: "def method(arg: Type) -> Return"
      file: "path/to/file.py"
      line: 42
  dependencies:
    - source: "module_a.py"
      target: "module_b.py"
      type: "import"
  test_strategy: "Unit tests for core logic, integration tests for API"
  tdd_plan:
    - "test_feature_happy_path"
    - "test_feature_edge_case"
    - "test_feature_error_handling"
```

### Verification Checklist

| Check | Method | Evidence |
|-------|--------|----------|
| Import exists | `Grep` for definition | `imports_verified` |
| Signature matches | `Read` target file | `signatures_matched` |
| Types compatible | Compare type hints | `type_analysis` |
| Dependencies available | Check imports | `dependencies` |

### Pass Criteria
- [ ] All imports verified (definitions found)
- [ ] Function/class signatures matched
- [ ] Test strategy defined
- [ ] No circular dependencies detected

### Failure Conditions
- Importing non-existent module
- Signature mismatch (wrong arguments/return type)
- Missing test strategy for non-trivial changes

---

## 4. Stage C: VERIFY

### Purpose
Quality gate ensuring all changes meet standards before completion.

### Required Actions
1. **Build Check** - Ensure code compiles/parses without errors
2. **Test Execution** - Run relevant test suites
3. **Lint Check** - Verify code style compliance
4. **Type Check** - Run static type analysis (if applicable)

### V2.1.x Enhanced Evidence Schema

**Module:** `lib/oda/ontology/evidence/quality_checks.py`

Stage C now uses structured Pydantic models for evidence:

```python
from lib.oda.ontology.evidence import (
    StageCEvidence,
    QualityCheck,
    Finding,
    CheckStatus,
    FindingSeverity,
)

# Create Stage C evidence
evidence = StageCEvidence()

# Add quality checks
evidence.add_quality_check(QualityCheck(
    name="tests",
    status=CheckStatus.PASSED,
    command="pytest tests/ -v",
    coverage="85%",
    duration_ms=12500,
))

# Add findings
evidence.add_finding(Finding(
    severity=FindingSeverity.WARNING,
    category="lint",
    message="Unused import",
    file="path/to/file.py",
    line=5,
    auto_fixable=True,
))

# Validate
if evidence.can_pass_stage():
    print("Stage C: PASSED")
```

### Evidence Schema (YAML Representation)

```yaml
stage_c_evidence:
  quality_checks:
    - name: "build"
      status: "passed"
      command: "python -m py_compile file.py"
      duration_ms: 500
      exit_code: 0
    - name: "tests"
      status: "passed"
      command: "pytest tests/ -v"
      coverage: "85%"
      duration_ms: 12500
    - name: "lint"
      status: "passed"
      command: "ruff check ."
      duration_ms: 2000
    - name: "typecheck"
      status: "passed"
      command: "mypy ."
      duration_ms: 8000
  findings:
    - severity: "WARNING"
      category: "lint"
      message: "Unused import"
      file: "path/to/file.py"
      line: 5
      column: 1
      code: "F401"
      auto_fixable: true
  findings_summary:
    CRITICAL: 0
    ERROR: 0
    WARNING: 1
    INFO: 0
  critical_count: 0
  error_count: 0
  verification_commands:
    - "pytest tests/ -v"
    - "ruff check ."
  execution_context:
    python_version: "3.12"
    working_directory: "/home/palantir/project"
  stage_started_at: "2026-01-11T19:00:00Z"
  stage_completed_at: "2026-01-11T19:00:23Z"
```

### Pydantic Schema Reference

| Model | Fields | Purpose |
|-------|--------|---------|
| `StageCEvidence` | quality_checks, findings, findings_summary, critical_count | Complete Stage C evidence |
| `QualityCheck` | name, status, command, output, coverage, duration_ms | Single check result |
| `Finding` | severity, category, message, file, line, auto_fixable | Single finding |
| `CheckStatus` | PASSED, FAILED, SKIPPED, RUNNING, TIMEOUT | Check status enum |
| `FindingSeverity` | CRITICAL, ERROR, WARNING, INFO | Finding severity enum |

### Quality Gates

| Gate | Command | Pass Condition |
|------|---------|----------------|
| Build | `python -m py_compile` | Exit code 0 |
| Tests | `pytest -v` | All tests pass |
| Lint | `ruff check .` | No errors (warnings OK) |
| Type | `mypy .` | No errors |

### Severity Levels

| Level | Action | Example |
|-------|--------|---------|
| `CRITICAL` | **Block** - Must fix | Syntax error, test failure |
| `ERROR` | **Block** - Must fix | Type error, lint error |
| `WARNING` | **Allow** - Should fix | Unused import, complexity |
| `INFO` | **Allow** - Optional | Style suggestion |

### Pass Criteria
- [ ] Build succeeds (exit code 0)
- [ ] All tests pass
- [ ] Zero CRITICAL findings
- [ ] Zero ERROR findings (or documented exceptions)

### Failure Conditions
- Build fails
- Tests fail
- CRITICAL or ERROR findings present
- Quality check not executed

---

## 5. Anti-Hallucination Rules

### Core Principle

> **Stages without `files_viewed` evidence are INVALID**

The protocol enforces evidence-based execution. Any stage that passes without demonstrating actual file reads is rejected.

### Enforcement Code

```python
class AntiHallucinationError(Exception):
    """Raised when a stage passes without evidence."""

    def __init__(self, stage: str, message: str):
        self.stage = stage
        self.message = message
        super().__init__(f"Stage {stage}: {message}")


class StageResult:
    def validate_evidence(self, strict: bool = True) -> bool:
        """Validate that evidence exists for passed stages."""
        if self.passed and not self.has_evidence:
            if strict:
                raise AntiHallucinationError(
                    stage=self.stage.value,
                    message="Stage passed without files_viewed evidence"
                )
            return False
        return True

    @property
    def has_evidence(self) -> bool:
        """Check if stage has valid evidence."""
        return bool(self.files_viewed) and len(self.files_viewed) > 0
```

### Validation Modes

| Mode | Behavior | Use Case |
|------|----------|----------|
| `strict=True` | Raise `AntiHallucinationError` | Production, critical operations |
| `strict=False` | Return `False` (warning) | Development, debugging |

### Evidence Requirements by Stage

| Stage | Minimum Evidence |
|-------|------------------|
| A: SCAN | `files_viewed` non-empty |
| B: TRACE | `imports_verified` or `signatures_matched` non-empty |
| C: VERIFY | `quality_checks` with at least one check executed |

### Anti-Hallucination Checklist

- [ ] Did you use `Read` tool to view files?
- [ ] Is `files_viewed` populated in evidence?
- [ ] Are code snippets from actual file content?
- [ ] Did you verify imports exist before referencing?
- [ ] Did you run actual commands for Stage C?

---

## 6. Protocol Execution Flow

```
[START]
    |
    v
+-------------------+
| Stage A: SCAN     |
| - Read files      |
| - Gather evidence |
+-------------------+
    |
    | files_viewed?
    |
    +--NO--> [AntiHallucinationError]
    |
    YES
    |
    v
+-------------------+
| Stage B: TRACE    |
| - Verify imports  |
| - Match signatures|
+-------------------+
    |
    | imports_verified?
    |
    +--NO--> [Back to Stage A]
    |
    YES
    |
    v
+-------------------+
| Stage C: VERIFY   |
| - Run tests       |
| - Check quality   |
+-------------------+
    |
    | zero CRITICAL?
    |
    +--NO--> [Fix and retry Stage C]
    |
    YES
    |
    v
[COMPLETE]
```

---

## 7. Quick Reference

### Mandatory Evidence Fields

```yaml
# Stage A (minimum)
files_viewed: [...]    # REQUIRED
complexity: "..."      # REQUIRED

# Stage B (minimum)
imports_verified: [...] # REQUIRED
test_strategy: "..."    # REQUIRED

# Stage C (minimum)
quality_checks: [...]   # REQUIRED
findings: [...]         # REQUIRED (can be empty)
```

### Common Commands

```bash
# Stage A - Discovery
rg "pattern" --type py
fd "*.py" src/

# Stage B - Verification
python -c "from module import Class"
grep -n "def function_name" file.py

# Stage C - Quality
pytest tests/ -v
ruff check .
mypy .
python -m py_compile file.py
```

### Protocol Invocation

```python
# Full protocol with RSIL (Recursive Search with Iterative Learning)
result = ThreeStageProtocol.execute_with_rsil(
    task=task,
    strict_evidence=True
)

# Individual stage execution
stage_a_result = execute_scan(files=["path/to/file.py"])
stage_b_result = execute_trace(imports=["module.Class"])
stage_c_result = execute_verify(commands=["pytest", "ruff"])
```

---

## 8. Related Resources

| Resource | Path | Purpose |
|----------|------|---------|
| Governance Rules | `.agent/rules/governance/` | Protocol definitions |
| Anti-Hallucination | `.agent/rules/governance/anti_hallucination.md` | Evidence requirements |
| Protocol Scripts | `scripts/ontology/protocols/` | Implementation |
| StageResult Schema | `lib/oda/ontology/objects/task_types.py` | Type definitions |

---

## 9. Available Protocols

| Protocol | Workflow | Purpose |
|----------|----------|---------|
| AuditProtocol | `/deep-audit` | Comprehensive codebase analysis |
| PlanningProtocol | `/plan` | Implementation planning |
| ExecutionProtocol | `/consolidate` | Memory consolidation |

---

> **Remember:** Evidence is not optional. Every stage must demonstrate actual file reads and verifications. When in doubt, read more files.
