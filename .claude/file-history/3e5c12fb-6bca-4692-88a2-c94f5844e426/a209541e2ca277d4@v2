# Ontology-Definition Follow-up Optimization Plan

> **Version:** 1.1 | **Status:** IN_PROGRESS | **Date:** 2026-01-17
> **Auto-Compact Safe:** This file persists across context compaction
> **Scope:** Coverage 85% + Lint Fix + Dead Code Removal + Optimization
> **Analysis Agents:** a4881b6 (Explore), a42aef5 (Plan)

## Executive Summary

| Item | Before | Target |
|------|--------|--------|
| Test Coverage | 63% | 85% |
| Lint Issues | 530 | 0 |
| Test Count | 311 (2 failing) | ~400 (all passing) |
| __pycache__ dirs | 10 | 0 (gitignored) |

## Critical Finding (P0)

**2 Failing Tests Detected:**
1. `TestSchemaValidator::test_validate_dict_with_string_schema_type`
2. `TestSchemaValidator::test_validate_dict_schema_not_found`

**File:** `tests/test_validation.py`
**Root Cause:** `validate_dict` method returns `ValidationResult` with `schema_type=str(schema_type)` when schema type is invalid

## Analysis Findings (from Explore Agent a4881b6 + Plan Agent a42aef5)

### Project Statistics
- **Python modules:** 36 files
- **Test files:** 7 modules
- **Test functions:** 311 test cases
- **Generated artifacts:** 10 __pycache__ directories

### Identified Issues

#### 1. Low Coverage Modules (Priority: HIGH)

**Detailed Coverage by Module:**

| Module | Coverage | Missing Lines | Priority |
|--------|----------|---------------|----------|
| `schemas/__init__.py` | **0%** | 13-21 | P1-CRITICAL |
| `export/json_schema_exporter.py` | **15%** | 87-314 | P1-CRITICAL |
| `registry/interface_registry.py` | **18%** | 52-352 | P1-HIGH |
| `import_/migration.py` | **25%** | 79-419 | P2-MEDIUM |
| `registry/decorators.py` | **34%** | 107-383 | P2-MEDIUM |
| `core/identifiers.py` | **42%** | 68-297 | P3-LOW |
| `export/foundry_exporter.py` | **45%** | 134-423 | P2-MEDIUM |
| `types/value_type.py` | **51%** | 172-526 | P3-LOW |

**Factory Classes (0 test coverage):**

| Module | Issue | Tests |
|--------|-------|-------|
| `CommonValueTypes` (value_type.py:440+) | Factory class untested | 0 |
| `CommonStructTypes` (struct_type.py:380+) | Factory class untested | 0 |
| `CommonSharedProperties` (shared_property.py:352+) | Factory class untested | 0 |
| `LLMSchemaExporter` module functions | `to_compact_yaml()`, `to_markdown()`, `to_typescript()` untested | 0 |

#### 2. Potential Dead Code

| File | Lines | Description |
|------|-------|-------------|
| `core/identifiers.py` | 181-246 | Case conversion utilities - verify usage |
| `export/llm_schema_exporter.py` | 419-429 | Module-level convenience functions |

#### 3. Structure Optimization

| Module | Files | Lines | Opportunity |
|--------|-------|-------|-------------|
| registry/ | 4 | 1,282 | Consolidate decorators.py into ontology_registry.py |
| export/ | 3 | 1,281 | Test or remove module-level functions |

---

## Implementation Phases

### Phase 0: Fix Failing Tests (P0-CRITICAL)

**Must complete before any other work.**

```bash
# Files to investigate:
# - tests/test_validation.py
# - ontology_definition/validation/schema_validator.py

# Failing tests:
# 1. test_validate_dict_with_string_schema_type
# 2. test_validate_dict_schema_not_found
```

**Action:** Review test expectations vs. `validate_dict()` method implementation.

---

### Phase 1: Lint Auto-Fix (530 issues → 0)

```bash
cd Ontology-Definition
.venv/bin/ruff check --fix ontology_definition/ tests/

# Breakdown:
# - UP045: Optional[X] -> X | None (234 issues)
# - UP037: Remove quoted annotations (169 issues)
# - UP007: Union[X, Y] -> X | Y (50 issues)
# - F401: Unused imports (35 issues)
# - I001: Import sorting (34 issues)
# - Others (8 issues)
```

---

### Phase 2: Test Coverage Improvement (Target: 63% → 85%)

**Estimated new tests:** ~90 test functions

#### 1.1 CommonValueTypes Tests (Priority: P1)
```python
# tests/test_value_types.py - ADD
def test_email_address_value_type(): ...
def test_positive_integer_value_type(): ...
def test_priority_value_type(): ...
def test_url_value_type(): ...
def test_uuid_value_type(): ...
def test_percentage_value_type(): ...
```

#### 1.2 CommonStructTypes Tests (Priority: P1)
```python
# tests/test_struct_types.py - ADD
def test_address_struct_type(): ...
def test_monetary_amount_struct_type(): ...
def test_geo_coordinate_struct_type(): ...
def test_contact_info_struct_type(): ...
```

#### 1.3 CommonSharedProperties Tests (Priority: P1)
```python
# tests/test_shared_properties.py - ADD
def test_created_at_shared_property(): ...
def test_modified_at_shared_property(): ...
def test_created_by_shared_property(): ...
def test_modified_by_shared_property(): ...
def test_security_markings_shared_property(): ...
```

#### 1.4 LLMSchemaExporter Module Function Tests (Priority: P2)
```python
# tests/test_export.py - EXTEND
def test_to_compact_yaml_function(): ...
def test_to_markdown_function(): ...
def test_to_typescript_function(): ...
```

#### 1.5 MigrationManager Tests (Priority: P2)
```python
# tests/test_migration.py - ADD
def test_migration_manager_version_detection(): ...
def test_compatibility_layer_deprecated_fields(): ...
```

### Phase 2: Lint Auto-Fix

```bash
# Execute lint fix
cd Ontology-Definition
ruff check --fix ontology_definition/ tests/

# Expected results:
# - 500 auto-fixable issues resolved
# - ~1 issue may need manual fix
```

### Phase 3: Dead Code Analysis & Removal

#### 3.1 Verify Usage of Identifiers Utilities
```bash
# Search for actual usage
grep -r "is_pascal_case\|to_camel_case\|to_snake_case" ontology_definition/ --include="*.py"
```

**Decision:** Keep if used, document if internal-only, remove if dead.

#### 3.2 Module-Level Function Decision
- If tests added and passing → Keep
- If tests fail or no usage → Remove

### Phase 4: Cleanup & Optimization

#### 4.1 Remove __pycache__ directories
```bash
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
```

#### 4.2 Update .gitignore
```
# Add to .gitignore if not present
__pycache__/
*.pyc
*.pyo
```

#### 4.3 Optional: Registry Consolidation
- Merge `decorators.py` patterns into `ontology_registry.py`
- Estimated savings: ~50 LOC
- Risk: Medium (many files import from registry)

---

## Quality Gates

| Gate | Condition | Status |
|------|-----------|--------|
| All tests pass | `pytest` returns 0 | Pending |
| Coverage >= 85% | `pytest --cov` shows ≥85% | Pending |
| Lint clean | `ruff check` returns 0 | Pending |
| No deprecated imports | `grep "from lib.oda"` = 0 | ✅ Verified |

---

## Execution Order

| Step | Action | Command/Tool | Risk |
|------|--------|--------------|------|
| 1 | Add jsonschema optional dependency | Edit pyproject.toml | Low |
| 2 | Run lint auto-fix | `ruff check --fix` | Low |
| 3 | Add CommonValueTypes tests | Write tests | Low |
| 4 | Add CommonStructTypes tests | Write tests | Low |
| 5 | Add CommonSharedProperties tests | Write tests | Low |
| 6 | Add LLMSchemaExporter tests | Write tests | Low |
| 7 | Run coverage check | `pytest --cov` | N/A |
| 8 | Verify usage of identifiers utilities | Grep search | N/A |
| 9 | Remove/keep dead code based on analysis | Edit/Delete | Medium |
| 10 | Cleanup __pycache__ | Bash rm | Low |
| 11 | Final verification | Full test suite | N/A |

---

## Risk Register

| Risk | Severity | Mitigation |
|------|----------|------------|
| Test failures after lint fix | LOW | Lint fix is style-only |
| Dead code removal breaks imports | MEDIUM | Grep verify before removal |
| Coverage target not met | LOW | Add more edge case tests |

---

## Quick Resume After Auto-Compact

1. Read this file: `.agent/plans/ontology_optimization_followup.md`
2. Check TodoWrite for current task status
3. Resume from first PENDING phase
4. Use Explore agent for deep analysis if needed

## Agent Registry

| Task | Agent ID | Status |
|------|----------|--------|
| Directory Analysis (Explore) | a4881b6 | completed |
| Optimization Strategy (Plan) | a42aef5 | completed |
| Plan Synthesis | - | this file |

## Synthesized Recommendations

**From Both Agents:**

| Priority | Category | Action | Agent Source |
|----------|----------|--------|--------------|
| **P0** | Test Fixes | Fix 2 failing tests in test_validation.py | a42aef5 |
| **P1** | Lint | Run `ruff --fix` (526 auto-fixable) | a42aef5 |
| **P1** | Coverage | Add `test_schemas.py` (0% → 100%) | a42aef5 |
| **P1** | Coverage | Test CommonValueTypes/StructTypes/SharedProperties | a4881b6 |
| **P2** | Coverage | Test json_schema_exporter (15% → 70%) | a42aef5 |
| **P2** | Coverage | Test interface_registry (18% → 70%) | a42aef5 |
| **P2** | Coverage | Test migration.py (25% → 70%) | a42aef5 |
| **P3** | Cleanup | Remove __pycache__ directories | a4881b6 |
| **P3** | Analysis | Audit identifiers.py utilities | a4881b6 |
| **P4** | Refactor | Consider registry consolidation | a4881b6 |

---

*Generated by ODA /plan command v2.0*
*Scope: Coverage + Lint + Cleanup*
*V2.1.10 Progressive-Disclosure Native*
