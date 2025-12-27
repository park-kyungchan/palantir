# Implementation Plan: Palantir AIP/Foundry Compliance Audit

**Status**: 🔄 In Progress
**Started**: 2025-12-24
**Last Updated**: 2025-12-24
**Estimated Completion**: 2025-12-25

---

**CRITICAL INSTRUCTIONS**: After completing each phase:
1. Check off completed task checkboxes
2. Run all quality gate validation commands
3. Verify ALL quality gate items pass
4. Update "Last Updated" date above
5. Document learnings in Notes section
6. Only then proceed to next phase

**DO NOT skip quality gates or proceed with failing checks**

---

## Overview

### Audit Description
This audit validates the Orion Orchestrator V2 codebase against Palantir AIP/Foundry architectural standards, focusing on four critical compliance areas:

1. **Schema vs Backing Store Separation** (CRITICAL)
2. **Declarative Action Governance** (HIGH)
3. **Optimistic Locking Implementation** (HIGH)
4. **Async/Await Correctness** (MEDIUM)

### Success Criteria
- [ ] Ontology Object Integrity: OntologyObject decoupled from ProposalModel
- [ ] Action Governance: Declarative ActionType with SubmissionCriteria enforced
- [ ] Optimistic Locking: Version-based concurrency with conflict detection
- [ ] Async Correctness: No blocking calls in kernel event loop

### Business Impact
Ensures the Orion Orchestrator aligns with enterprise-grade Palantir architecture patterns, enabling:
- Scalable governance workflows
- Safe concurrent data access
- Auditable action execution

---

## Architecture Analysis Summary

| Component | File | Palantir Pattern | Current Status |
|-----------|------|------------------|----------------|
| Domain Schema | `ontology_types.py` | Object Type (Schema) | COMPLIANT |
| Persistence Model | `models.py` | Backing Dataset | COMPLIANT |
| Action System | `actions.py` | Foundry Actions | COMPLIANT |
| Optimistic Locking | `manager.py` | Version Control | PARTIAL |
| Optimistic Locking | `proposal_repository.py` | Version Control | COMPLIANT |
| Async Runtime | `kernel.py` | Non-blocking | MOSTLY COMPLIANT |

---

## Key Files Under Audit

```
/home/palantir/orion-orchestrator-v2/
scripts/
  ontology/
    ontology_types.py      # Domain Schema (OntologyObject)
    actions.py             # ActionType, SubmissionCriteria, Registry
    manager.py             # ObjectManager (Sync DAO)
    objects/
      proposal.py          # Proposal Domain Object
    storage/
      orm.py               # AsyncOntologyObject Base
      models.py            # ProposalModel, ProposalHistoryModel
      proposal_repository.py  # Async Repository with OCC
      database.py          # Database Connection Manager
  runtime/
    kernel.py              # Async Event Loop Runtime
```

---

## Implementation Phases

### Phase 1: Schema vs Backing Store Separation Audit
**Goal**: Verify OntologyObject (Domain) is decoupled from ProposalModel (Persistence)
**Priority**: CRITICAL
**Status**: Pending

#### Analysis Tasks

- [ ] **Task 1.1**: Audit `OntologyObject` base class
  - File: `scripts/ontology/ontology_types.py`
  - Verify: Pure Pydantic model with no SQLAlchemy dependencies
  - Check: No imports from `storage/` modules

- [ ] **Task 1.2**: Audit `Proposal` domain object
  - File: `scripts/ontology/objects/proposal.py`
  - Verify: Extends `OntologyObject`, contains business logic only
  - Check: State machine transitions, validation rules

- [ ] **Task 1.3**: Audit `ProposalModel` persistence model
  - File: `scripts/ontology/storage/models.py`
  - Verify: SQLAlchemy model separate from domain object
  - Check: Maps 1:1 with Proposal but doesn't inherit from it

- [ ] **Task 1.4**: Audit `_to_domain()` mapping function
  - File: `scripts/ontology/storage/proposal_repository.py:59-82`
  - Verify: Proper conversion between Model -> Domain Object
  - Check: No business logic leakage into repository

- [ ] **Task 1.5**: Identify dual persistence pattern
  - Files: `manager.py` vs `proposal_repository.py`
  - Issue: ObjectManager uses JSON storage, Repository uses ORM
  - Document: Inconsistency in persistence approach

#### Quality Gate

**Compliance Checklist**:
- [ ] OntologyObject has NO SQLAlchemy imports
- [ ] Proposal domain object contains ONLY business logic
- [ ] ProposalModel is a separate SQLAlchemy class
- [ ] Repository handles Model<->Domain conversion
- [ ] No circular dependencies between domain and storage

**Palantir Standard Reference**:
```
Object Type (Schema)     Backing Dataset (Storage)
        OntologyObject  <>  ProposalModel
             Proposal   <>  ProposalModel
                            |
                    ProposalRepository (Mapping)
```

**Findings to Document**:
- [ ] Schema independence verified
- [ ] Mapping layer exists and is correct
- [ ] Any violations identified

---

### Phase 2: Declarative Action Governance Audit
**Goal**: Verify ActionType follows Foundry Actions pattern with SubmissionCriteria
**Priority**: HIGH
**Status**: Pending

#### Analysis Tasks

- [ ] **Task 2.1**: Audit `ActionType` base class
  - File: `scripts/ontology/actions.py:405-565`
  - Verify: Abstract base with declarative class attributes
  - Check: `api_name`, `object_type`, `submission_criteria`, `side_effects`

- [ ] **Task 2.2**: Audit `SubmissionCriterion` protocol
  - File: `scripts/ontology/actions.py:102-130`
  - Verify: Protocol-based validation (not inheritance)
  - Check: `name` property, `validate()` method signature

- [ ] **Task 2.3**: Audit built-in criteria implementations
  - File: `scripts/ontology/actions.py:133-223`
  - Verify: RequiredField, AllowedValues, MaxLength, CustomValidator
  - Check: Proper ValidationError raising

- [ ] **Task 2.4**: Audit SideEffect protocol
  - File: `scripts/ontology/actions.py:229-264`
  - Verify: Async execution, fire-and-forget pattern
  - Check: Error isolation (no side effect breaks others)

- [ ] **Task 2.5**: Audit ActionRegistry
  - File: `scripts/ontology/actions.py:582-640`
  - Verify: Centralized registration with metadata
  - Check: `requires_proposal` flag for hazardous actions

- [ ] **Task 2.6**: Audit GovernanceEngine
  - File: `scripts/ontology/actions.py:667-691`
  - Verify: Policy enforcement (ALLOW_IMMEDIATE, REQUIRE_PROPOSAL, DENY)
  - Check: Integration with ActionRegistry metadata

#### Quality Gate

**Compliance Checklist**:
- [ ] ActionType is abstract with declarative attributes
- [ ] SubmissionCriteria are evaluated before execution
- [ ] SideEffects execute post-commit only
- [ ] ActionRegistry provides central governance
- [ ] GovernanceEngine enforces execution policy

**Palantir Standard Reference**:
```
Foundry Action Structure:
- Parameters: User input definitions
- Rules: Transformation logic
- Submission Criteria: Pre-execution validation
- Side Effects: Post-commit notifications/webhooks
```

**Findings to Document**:
- [ ] Declarative pattern compliance
- [ ] Validation flow correctness
- [ ] Side effect isolation

---

### Phase 3: Optimistic Locking Implementation Audit
**Goal**: Verify version-based concurrency control
**Priority**: HIGH
**Status**: Pending

#### Analysis Tasks

- [ ] **Task 3.1**: Audit `OntologyObject.version` field
  - File: `scripts/ontology/ontology_types.py:217-222`
  - Verify: Version field with default=1, ge=1
  - Check: `touch()` method increments version

- [ ] **Task 3.2**: Audit `AsyncOntologyObject.version` ORM column
  - File: `scripts/ontology/storage/orm.py:54-57`
  - Verify: Integer column, default=1, not nullable
  - Check: Commented out `version_id_col` mapper args

- [ ] **Task 3.3**: Audit `ObjectManager.save()` versioning
  - File: `scripts/ontology/manager.py:121-196`
  - ISSUE: Line 155 blindly increments without conflict check
  - Verify: `obj.version = (existing.version or 0) + 1`
  - Problem: No WHERE clause with version check!

- [ ] **Task 3.4**: Audit `ProposalRepository.save()` versioning
  - File: `scripts/ontology/storage/proposal_repository.py:84-183`
  - Verify: Lines 117-127 check version sequence
  - Check: `if proposal.version == db_version + 1`
  - Verify: ConcurrencyError raised on mismatch
  - Check: WHERE clause includes version: Line 145

- [ ] **Task 3.5**: Document versioning inconsistency
  - ObjectManager: NO conflict detection (unsafe)
  - ProposalRepository: Proper OCC implementation (safe)
  - Recommendation: Align ObjectManager to Repository pattern

#### Quality Gate

**Compliance Checklist**:
- [ ] Version field exists on all OntologyObjects
- [ ] ProposalRepository implements proper OCC
- [ ] ObjectManager versioning issues documented
- [ ] ConcurrencyError exception defined

**Palantir Standard Reference**:
```
Optimistic Locking Pattern:
1. READ: Load object + version
2. VALIDATE: Compare version on commit
3. WRITE: Update with WHERE version=expected
4. CONFLICT: Raise error if rowcount=0
```

**Critical Finding**:
```python
# ObjectManager (UNSAFE - Line 155):
obj.version = (existing.version or 0) + 1  # No conflict check!

# ProposalRepository (SAFE - Lines 117-127):
if proposal.version == db_version + 1:
    new_version = proposal.version
else:
    raise ConcurrencyError(...)  # Proper conflict detection

# Also Line 145:
.where(ProposalModel.version == expected_version)  # Atomic CAS
```

---

### Phase 4: Async/Await Correctness Audit
**Goal**: Ensure kernel event loop has no blocking calls
**Priority**: MEDIUM
**Status**: Pending

#### Analysis Tasks

- [ ] **Task 4.1**: Audit `OrionRuntime.start()` main loop
  - File: `scripts/runtime/kernel.py:44-61`
  - Verify: `asyncio.run()` for entry point
  - Check: `await asyncio.sleep(1)` for non-blocking wait

- [ ] **Task 4.2**: Audit `_process_task_cognitive()` LLM call
  - File: `scripts/runtime/kernel.py:94-151`
  - Verify: Line 110 uses `asyncio.to_thread()` for blocking call
  - Check: `plan = await asyncio.to_thread(self.llm.generate_plan, prompt)`

- [ ] **Task 4.3**: Audit `_process_approved_proposals()`
  - File: `scripts/runtime/kernel.py:63-88`
  - Verify: `await self.repo.find_by_status()` is async
  - Check: `await self.marshaler.execute_action()` is async
  - Check: `await self.repo.execute()` is async

- [ ] **Task 4.4**: Audit RelayQueue.dequeue()
  - File: `scripts/relay/queue.py` (needs review)
  - Verify: Is `self.relay.dequeue()` blocking or non-blocking?
  - Check: Line 53 calls without await

- [ ] **Task 4.5**: Audit Database.transaction() context manager
  - File: `scripts/ontology/storage/database.py:81-95`
  - Verify: `@asynccontextmanager` decorator
  - Check: `async with self.session_factory() as session`

#### Quality Gate

**Compliance Checklist**:
- [ ] Main event loop uses proper asyncio patterns
- [ ] Blocking LLM call wrapped in thread pool
- [ ] All database operations are async
- [ ] RelayQueue blocking status documented
- [ ] No sync calls in async context

**Palantir Standard Reference**:
```
AIP Async Pattern:
- Event loop drives all I/O
- LLM calls offloaded to thread pool
- Database uses async drivers (aiosqlite)
- Side effects are fire-and-forget async
```

**Key Verification Points**:
```python
# Good: Thread pool for blocking call (Line 110)
plan = await asyncio.to_thread(self.llm.generate_plan, prompt)

# Good: Async database operations
await self.repo.find_by_status(ProposalStatus.APPROVED)

# Needs Check: Is this blocking?
task_payload = self.relay.dequeue()  # Line 53 - no await!
```

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation Strategy |
|------|-------------|--------|---------------------|
| ObjectManager has no OCC | HIGH | HIGH | Document as critical finding, recommend refactor |
| RelayQueue may block | MEDIUM | MEDIUM | Audit RelayQueue implementation |
| Dual persistence patterns | MEDIUM | LOW | Document inconsistency, recommend unification |
| Test coverage unknown | HIGH | MEDIUM | Run pytest with coverage analysis |

---

## Rollback Strategy

### If Audit Reveals Critical Issues
- Document all findings in this plan
- Create separate remediation plan for each issue
- Prioritize by business impact

### If Tests Fail During Audit
- Capture test output in findings
- Classify as pre-existing or audit-related
- Document in blockers section

---

## Progress Tracking

### Completion Status
- **Phase 1 (Schema Separation)**: Pending
- **Phase 2 (Action Governance)**: Pending
- **Phase 3 (Optimistic Locking)**: Pending
- **Phase 4 (Async Correctness)**: Pending

**Overall Progress**: 0% complete

---

## Preliminary Findings (Pre-Audit)

### Positive Observations
1. `OntologyObject` (Pydantic) is cleanly separated from `ProposalModel` (SQLAlchemy)
2. `ActionType` follows declarative pattern with class attributes
3. `SubmissionCriterion` uses Protocol-based validation
4. `ProposalRepository` has proper Optimistic Locking
5. `kernel.py` uses `asyncio.to_thread()` for LLM calls

### Critical Issues Identified
1. **ObjectManager.save()** (Line 155): No conflict detection - blindly increments version
2. **Dual Persistence Patterns**: ObjectManager uses JSON, ProposalRepository uses ORM
3. **RelayQueue.dequeue()**: Called without await - potential blocking

### Recommendations
1. Refactor ObjectManager to use WHERE clause with version check
2. Unify persistence patterns (prefer ProposalRepository approach)
3. Audit RelayQueue for async compliance

---

## Validation Commands

```bash
# Run existing tests
cd /home/palantir/orion-orchestrator-v2
pytest tests/ -v

# Check test coverage
pytest tests/ --cov=scripts --cov-report=html

# Run type checking
mypy scripts/ --ignore-missing-imports

# Verify no circular imports
python -c "from scripts.ontology.ontology_types import OntologyObject; print('OK')"
python -c "from scripts.ontology.actions import ActionType; print('OK')"
python -c "from scripts.ontology.storage.proposal_repository import ProposalRepository; print('OK')"
```

---

## Notes & Learnings

### Implementation Notes
- (To be filled during audit)

### Blockers Encountered
- (To be filled during audit)

---

## References

### Palantir Documentation
- [Foundry Ontology Overview](https://palantir.com/docs/foundry/ontology/overview/)
- [Action Types](https://palantir.com/docs/foundry/action-types/overview/)
- [Submission Criteria](https://palantir.com/docs/foundry/action-types/submission-criteria/)

### Orion Codebase
- Root: `/home/palantir/orion-orchestrator-v2`
- CLAUDE.md: Project-level AI instructions

---

## Final Checklist

**Before marking audit as COMPLETE**:
- [ ] All 4 phases completed with quality gates passed
- [ ] All critical issues documented
- [ ] Recommendations prioritized
- [ ] Test coverage analyzed
- [ ] Remediation plan created for critical issues
- [ ] Stakeholders notified of findings

---

**Audit Status**: 🔄 In Progress
**Next Action**: Begin Phase 1 - Schema vs Backing Store Separation Audit
**Blocked By**: None
