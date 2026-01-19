# Enhancement Summary

## Tier 1 (Core Foundation)

### E2E Tests Added
- `tests/oda/e2e/test_types_e2e.py`
- `tests/oda/e2e/test_schemas_e2e.py`
- `tests/oda/e2e/test_decorators_e2e.py`

### Fixes / Improvements
- Link constraints: add `custom_validator` to `LinkTypeConstraints` and propagate to `to_link_constraint()`
- Shared properties: use Pydantic `create_model(__base__=...)` to inject shared properties as real model fields
- Computed properties: set `ignored_types=(ComputedPropertyDescriptor,)` in `ComputedPropertyMixin` to avoid Pydantic field errors
- Storage: add minimal async SQLAlchemy database wrapper (`Database`, `DatabaseManager`) used by tests

## Latest Verification
- Tier 1 suite: `19 passed` via `.venv/bin/python -m pytest tests/oda/e2e -v`

## Tier 2 (Data Layer) - Storage Baseline
- Added SQLAlchemy models and `ProposalRepository` to satisfy `tests/e2e/test_proposal_repository.py`
- Database: WAL mode, schema bootstrap, `health_check()`
- Proposal persistence: CRUD, optimistic locking, pagination, history, governance helpers
- Verification: `32 passed` via `.venv/bin/python -m pytest tests/e2e/test_proposal_repository.py -v --asyncio-mode=auto`

## Tier 2 (Data Layer) - E2E Tests
### E2E Tests Added
- `tests/oda/e2e/test_objects_e2e.py`
- `tests/oda/e2e/test_storage_e2e.py`
- `tests/oda/e2e/test_validators_e2e.py`

### Fixes / Improvements
- Workspace: enable slug auto-generation when not provided by setting `validate_default=True` on `Workspace.slug`

### Latest Verification
- Tier 2 suite: `30 passed` via `.venv/bin/python -m pytest tests/oda/e2e -v`

## Tier 3 Prep (Actions) - Import/Registry Unblock
- Exported storage repositories from `lib.oda.ontology.storage` for action modules (`InsightRepository`, `PatternRepository`, `ActionLogRepository`, `JobResultRepository`, `LearnerRepository`)
- Verification: `40 passed` via `.venv/bin/python -m pytest tests/ontology/test_action_types.py -v`
- Sanity: `256 passed` via `.venv/bin/python -m pytest tests/ontology -v`

## Tier 3 (Operations) - E2E Tests + Missing Modules
### E2E Tests Added
- `tests/oda/e2e/test_actions_e2e.py`
- `tests/oda/e2e/test_hooks_e2e.py`
- `tests/oda/e2e/test_evidence_e2e.py`
- `tests/oda/e2e/test_governance_e2e.py`

### Fixes / Improvements
- Evidence: implemented `lib/oda/ontology/evidence` (Stage C structured evidence: `StageCEvidence`, `QualityCheck`, `Finding`)
- Hooks: fixed priority override bug where `LifecycleHookPriority.CRITICAL == 0` was treated as falsy
- Storage: added `TaskRepository` and expanded `TaskModel` to unblock `lib.oda.claude.todo_sync` and orchestration flow tests

### Latest Verification
- Tier 3 suite: `39 passed` via `.venv/bin/python -m pytest tests/oda/e2e -v`
- Orchestration flow: `32 passed` via `.venv/bin/python -m pytest tests/oda/test_orchestration_flow.py -v`

## Transaction Support (Checkpoint System)
- Added `lib/oda/ontology/storage/orm.py` with `AsyncOntologyObject` + shared `Base` for transaction ORM models
- Added missing ORM tables (`TaskModel`, `AgentModel`) required by checkpoint snapshot/restore logic
- Ensured `CheckpointModel` is registered before DB schema creation and flushed insight writes for in-transaction reads
- Verification: `27 passed` via `.venv/bin/python -m pytest tests/transaction/test_branching.py -v`
