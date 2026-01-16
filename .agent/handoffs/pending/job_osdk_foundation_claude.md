# HANDOFF: job-osdk-001-claude

## METADATA
- **From**: Orchestrator
- **To**: Architecture Agent (Logic Core)
- **Created**: 2025-12-27T11:06:00+09:00
- **Priority**: CRITICAL
- **Phase**: EXECUTION
- **Reference**: `/home/palantir/GAP_ANALYSIS_PALANTIR_AIP.md` (Section 4)

## OBJECTIVE
Implement the **OSDK (Ontology SDK) Core Layer** to address the "Critical Gap" identified in the recent Gap Analysis. This involves creating the type-safe mechanisms for querying objects and executing actions, replacing or extending current stubs.

## CONTEXT
The current codebase lacks a proper Client SDK.
- `scripts/osdk/` does not exist.
- Current `client.py` is a mock.
- We need a structure that allows `ObjectQuery.where(...).execute()` and `ActionClient.apply(...)`.

## TASKS

### Task 1: Scaffold Directory
- **Action**: CREATE directory `scripts/osdk/`
- **File**: `scripts/osdk/__init__.py` (Empty)

### Task 2: Implement ObjectQuery Builder
- **File**: `scripts/osdk/query.py`
- **Reference**: Gap Analysis Section 4.3
- **Requirements**:
  - Generic class `ObjectQuery[T]`
  - Methods: `where`, `select`, `order_by`, `limit`, `execute` (async stub)
  - Must type-hint correctly with `OntologyObject`

### Task 3: Implement ActionClient
- **File**: `scripts/osdk/actions.py`
- **Reference**: Gap Analysis Section 4.3
- **Requirements**:
  - Class `ActionClient`
  - Method: `apply(action, params)` -> Returns `ActionResult`
  - Method: `validate(action, params)` -> Returns `ValidationResult`

### Task 4: Implement OSDK Generator Stub
- **File**: `scripts/osdk/generator.py`
- **Reference**: Gap Analysis Section 4.3
- **Requirements**:
  - Class `OSDKGenerator`
  - Method: `generate_from_ontology(ontology_def) -> GeneratedSDK`
  - Just the skeleton for now.

## CONSTRAINTS
- Use **Standard Output Protocol** (No markdown nesting errors).
- Ensure strict type hinting (Pydantic/Typing).
- Do NOT delete existing `scripts/client.py` yet (unless it conflicts, but better to create new `osdk` namespace first).

## EXPECTED OUTPUT
- `scripts/osdk/` directory with 4 files.
- `ObjectQuery` class that looks like a Palantir OSDK query builder.

## ON COMPLETION
1. Create result file: `.agent/handoffs/completed/job_osdk_foundation_result.md`
