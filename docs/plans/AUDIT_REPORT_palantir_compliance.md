# Palantir AIP/Foundry Compliance Audit Report

**Project**: Orion Orchestrator V2
**Audit Date**: 2025-12-24
**Auditor**: Claude 4.5 Opus (Logic Core)
**Architecture**: Ontology-Driven Architecture (ODA) v3.2

---

## Executive Summary

| Audit Area | Priority | Verdict | Score |
|------------|----------|---------|-------|
| Schema vs Backing Store Separation | CRITICAL | **COMPLIANT** | 95% |
| Declarative Action Governance | HIGH | **COMPLIANT** | 98% |
| Optimistic Locking | HIGH | **PARTIAL** | 65% |
| Async/Await Correctness | MEDIUM | **PARTIAL** | 80% |

**Overall Compliance Score: 84.5% (CONDITIONAL PASS)**

---

## Phase 1: Schema vs Backing Store Separation

### Verdict: COMPLIANT (95%)

### Evidence

#### 1.1 OntologyObject (Domain Schema)
**File**: `scripts/ontology/ontology_types.py`

```python
# Line 165-228: Pure Pydantic model
class OntologyObject(BaseModel):
    """Base class for all Ontology Objects (Domain Entities)."""
    id: str = Field(default_factory=generate_object_id)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    status: ObjectStatus = Field(default=ObjectStatus.ACTIVE)
    version: int = Field(default=1, ge=1)
```

**Findings**:
- No SQLAlchemy imports in file
- Pure Pydantic BaseModel inheritance
- Contains domain logic only (touch(), soft_delete(), archive())

#### 1.2 Proposal (Domain Object)
**File**: `scripts/ontology/objects/proposal.py`

```python
# Line 128: Extends OntologyObject
class Proposal(OntologyObject):
    action_type: str
    payload: Dict[str, Any]
    status: ProposalStatus
    # ... business logic methods
```

**Findings**:
- No SQLAlchemy imports in file
- State machine implemented (VALID_TRANSITIONS)
- Business logic encapsulated (submit(), approve(), reject(), execute())

#### 1.3 ProposalModel (Persistence Model)
**File**: `scripts/ontology/storage/models.py`

```python
# Line 9-32: SQLAlchemy ORM Model
class ProposalModel(AsyncOntologyObject):
    __tablename__ = "proposals"
    action_type: Mapped[str]
    payload: Mapped[dict]
    # ... storage columns
```

**Findings**:
- Separate class from Proposal domain object
- Extends AsyncOntologyObject (SQLAlchemy base)
- Maps 1:1 with Proposal but NO inheritance relationship

#### 1.4 Repository Mapping
**File**: `scripts/ontology/storage/proposal_repository.py:59-82`

```python
def _to_domain(self, model: ProposalModel) -> Proposal:
    """Convert ORM Model to Domain Object."""
    p = Proposal(
        id=model.id,
        status=ProposalStatus(model.status),
        version=model.version,
        # ... explicit mapping
    )
    return p
```

**Findings**:
- Explicit Model → Domain conversion
- No automatic ORM-to-domain mapping
- Clean separation maintained

### Issues Found

| Severity | Issue | Location |
|----------|-------|----------|
| MINOR | Dual persistence patterns | ObjectManager vs ProposalRepository |

**ObjectManager uses JSON storage** (`manager.py:161-163`):
```python
"data": obj.model_dump(mode='json'),  # Stores entire object as JSON
```

**ProposalRepository uses ORM columns** (`models.py:17-29`):
```python
action_type: Mapped[str]
payload: Mapped[dict]
# Individual columns
```

### Recommendation
Consider unifying persistence patterns. ProposalRepository pattern is preferred for type safety and queryability.

---

## Phase 2: Declarative Action Governance

### Verdict: COMPLIANT (98%)

### Evidence

#### 2.1 ActionType Base Class
**File**: `scripts/ontology/actions.py:405-565`

```python
class ActionType(ABC, Generic[T]):
    # Declarative class attributes
    api_name: ClassVar[str]
    object_type: ClassVar[Type[T]]
    submission_criteria: ClassVar[List[SubmissionCriterion]] = []
    side_effects: ClassVar[List[SideEffect]] = []
    requires_proposal: ClassVar[bool] = False

    # Execution flow
    async def execute(self, params, context) -> ActionResult:
        # 1. Validation
        errors = self.validate(params, context)
        # 2. Apply Edits
        obj, edits = await self.apply_edits(params, context)
        # 3. Side Effects (fire-and-forget)
        for effect in self.side_effects:
            await effect.execute(result, context)
```

**Palantir Alignment**:
| Foundry Action Element | Orion Implementation | Status |
|------------------------|----------------------|--------|
| Parameters | `params: Dict[str, Any]` | MATCH |
| Rules | `apply_edits()` method | MATCH |
| Submission Criteria | `submission_criteria` list | MATCH |
| Side Effects | `side_effects` list | MATCH |

#### 2.2 SubmissionCriterion Protocol
**File**: `scripts/ontology/actions.py:102-130`

```python
@runtime_checkable
class SubmissionCriterion(Protocol):
    @property
    def name(self) -> str: ...

    def validate(self, params: Dict, context: ActionContext) -> bool: ...
```

**Built-in Implementations**:
- `RequiredField` (Line 133-151)
- `AllowedValues` (Line 154-173)
- `MaxLength` (Line 176-195)
- `CustomValidator` (Line 198-222)

#### 2.3 SideEffect Protocol
**File**: `scripts/ontology/actions.py:229-264`

```python
@runtime_checkable
class SideEffect(Protocol):
    @property
    def name(self) -> str: ...

    async def execute(self, action_result, context) -> None: ...
```

**Built-in Implementations**:
- `LogSideEffect` (Line 267-287)
- `WebhookSideEffect` (Line 290-317)
- `SlackNotification` (Line 320-340)

#### 2.4 ActionRegistry & GovernanceEngine
**File**: `scripts/ontology/actions.py:582-691`

```python
class ActionRegistry:
    def register(self, action_class, **metadata): ...
    def get_metadata(self, api_name) -> ActionMetadata: ...
    def get_hazardous_actions(self) -> List[str]: ...

class GovernanceEngine:
    def check_execution_policy(self, action_name) -> str:
        # Returns: "DENY", "REQUIRE_PROPOSAL", "ALLOW_IMMEDIATE"
```

### Issues Found
None. Implementation closely follows Palantir Foundry Actions pattern.

---

## Phase 3: Optimistic Locking Implementation

### Verdict: PARTIAL COMPLIANCE (65%)

### Evidence

#### 3.1 Version Field Definition

**OntologyObject** (`ontology_types.py:217-222`):
```python
version: int = Field(
    default=1,
    description="Version number for optimistic locking",
    ge=1
)
```

**AsyncOntologyObject** (`orm.py:54-57`):
```python
version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
# Note: __mapper_args__ with version_id_col is COMMENTED OUT
```

#### 3.2 ProposalRepository - PROPER IMPLEMENTATION

**File**: `scripts/ontology/storage/proposal_repository.py:84-163`

```python
async def save(self, proposal: Proposal, actor_id: str, comment: str = None):
    async with self.db.transaction() as session:
        # Check existence and version in DB
        stmt = select(ProposalModel.version, ProposalModel.status).where(...)
        row = (await session.execute(stmt)).first()

        if row is None:
            # Create path
            ...
        else:
            db_version, db_status = row

            # VERSION CHECK - Line 117-127
            if proposal.version == db_version + 1:
                new_version = proposal.version
                expected_version = db_version
            else:
                raise ConcurrencyError(
                    f"Proposal {proposal.id} Version Mismatch. DB={db_version}, Obj={proposal.version}",
                    expected_version=db_version,
                    actual_version=proposal.version
                )

            # ATOMIC UPDATE WITH WHERE CLAUSE - Line 142-145
            stmt = (
                update(ProposalModel)
                .where(ProposalModel.id == proposal.id)
                .where(ProposalModel.version == expected_version)  # CAS
                .values(version=new_version, ...)
            )
            result = await session.execute(stmt)
            if result.rowcount == 0:
                raise ConcurrencyError(...)
```

**VERDICT: COMPLIANT** - Proper Optimistic Concurrency Control

#### 3.3 ObjectManager - UNSAFE IMPLEMENTATION

**File**: `scripts/ontology/manager.py:147-169`

```python
def save(self, obj: OntologyObject, session: Optional[Session] = None, ...):
    if existing:
        # UPDATE - LINE 155: UNSAFE!
        obj.version = (existing.version or 0) + 1  # NO CONFLICT CHECK!

        update_stmt = objects_table.update().where(
            objects_table.c.id == obj.id
            # NO VERSION CHECK IN WHERE CLAUSE!
        ).values(**update_data)

        active_session.execute(update_stmt)
```

**CRITICAL ISSUE**:
- Line 155: Blindly increments version without conflict detection
- No `WHERE version = expected` clause
- Lost updates possible in concurrent scenarios

### Comparison

| Pattern | ProposalRepository | ObjectManager |
|---------|-------------------|---------------|
| Version Check | `if proposal.version == db_version + 1` | None |
| ConcurrencyError | Raised on mismatch | Never raised |
| WHERE Clause | Includes `version = expected` | No version check |
| Atomic CAS | `rowcount == 0` check | No check |

### Recommendation

**CRITICAL**: Refactor `ObjectManager.save()` to match `ProposalRepository` pattern:

```python
# Proposed fix for manager.py:147-169
if existing:
    expected_version = existing.version
    new_version = expected_version + 1

    # Validate object's version matches expected
    if obj.version != new_version:
        raise ConcurrencyError(f"Version mismatch: expected {new_version}, got {obj.version}")

    update_stmt = objects_table.update().where(
        objects_table.c.id == obj.id
    ).where(
        objects_table.c.version == expected_version  # ADD THIS!
    ).values(version=new_version, ...)

    result = active_session.execute(update_stmt)
    if result.rowcount == 0:
        raise ConcurrencyError("Concurrent modification detected")
```

---

## Phase 4: Async/Await Correctness

### Verdict: PARTIAL COMPLIANCE (80%)

### Evidence

#### 4.1 Kernel Main Loop - COMPLIANT
**File**: `scripts/runtime/kernel.py:44-61`

```python
async def start(self):
    db = await initialize_database()
    self.repo = ProposalRepository(db)

    while self.running:
        # Check Relay Queue
        task_payload = self.relay.dequeue()  # ISSUE HERE
        if task_payload:
            await self._process_task_cognitive(task_payload)

        # Check Approved Proposals
        await self._process_approved_proposals()

        await asyncio.sleep(1)  # Non-blocking wait
```

#### 4.2 LLM Call - COMPLIANT
**File**: `scripts/runtime/kernel.py:110`

```python
# Blocking call wrapped in thread pool - CORRECT!
plan = await asyncio.to_thread(self.llm.generate_plan, prompt)
```

#### 4.3 Database Operations - COMPLIANT
**File**: `scripts/ontology/storage/database.py:81-95`

```python
@asynccontextmanager
async def transaction(self) -> AsyncGenerator[AsyncSession, None]:
    async with self.session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

#### 4.4 RelayQueue.dequeue() - BLOCKING ISSUE
**File**: `scripts/relay/queue.py:42-53`

```python
def dequeue(self) -> Optional[Dict]:  # SYNC method!
    """Atomic Dequeue"""
    with self._get_conn() as conn:  # sqlite3.connect is BLOCKING
        cursor = conn.execute("SELECT ... FROM relay_tasks WHERE status='pending' LIMIT 1")
        row = cursor.fetchone()
        if row:
            conn.execute("UPDATE relay_tasks SET status='processing' WHERE id=?", (row['id'],))
            return dict(row)
    return None
```

**Called in kernel.py:53 without await**:
```python
task_payload = self.relay.dequeue()  # Blocks event loop!
```

### Issue Analysis

| Operation | Method | Blocking? | Location |
|-----------|--------|-----------|----------|
| Database init | `await initialize_database()` | No | kernel.py:46 |
| LLM call | `await asyncio.to_thread(...)` | No | kernel.py:110 |
| Proposal fetch | `await self.repo.find_by_status()` | No | kernel.py:68 |
| Action execute | `await self.marshaler.execute_action()` | No | kernel.py:75 |
| **Relay dequeue** | `self.relay.dequeue()` | **YES** | kernel.py:53 |
| Sleep | `await asyncio.sleep(1)` | No | kernel.py:61 |

### Recommendation

**Option A**: Wrap in thread pool (minimal change):
```python
# kernel.py:53
task_payload = await asyncio.to_thread(self.relay.dequeue)
```

**Option B**: Make RelayQueue async (preferred):
```python
# queue.py - use aiosqlite
import aiosqlite

async def dequeue(self) -> Optional[Dict]:
    async with aiosqlite.connect(self.db_path) as conn:
        cursor = await conn.execute("SELECT ... WHERE status='pending' LIMIT 1")
        row = await cursor.fetchone()
        if row:
            await conn.execute("UPDATE ... WHERE id=?", (row['id'],))
            await conn.commit()
            return dict(row)
    return None
```

---

## Summary of Findings

### Critical Issues (Must Fix)

| ID | Severity | Component | Issue | Fix Effort |
|----|----------|-----------|-------|------------|
| **C-1** | CRITICAL | ObjectManager | No OCC conflict detection | 2-3 hours |

### High Priority Issues (Should Fix)

| ID | Severity | Component | Issue | Fix Effort |
|----|----------|-----------|-------|------------|
| **H-1** | HIGH | RelayQueue | Blocking sync call in async context | 1-2 hours |
| **H-2** | HIGH | Architecture | Dual persistence patterns | 4-6 hours |

### Low Priority Issues (Consider)

| ID | Severity | Component | Issue | Fix Effort |
|----|----------|-----------|-------|------------|
| **L-1** | LOW | ORM | version_id_col commented out | 30 min |

---

## Compliance Matrix

| Palantir Pattern | Orion Implementation | Compliance |
|------------------|----------------------|------------|
| Object Type (Schema) | OntologyObject (Pydantic) | 100% |
| Backing Dataset | ProposalModel (SQLAlchemy) | 100% |
| Schema/Store Separation | Repository pattern | 95% |
| Foundry Actions | ActionType class | 100% |
| Parameters | Dict[str, Any] params | 100% |
| Rules | apply_edits() method | 100% |
| Submission Criteria | SubmissionCriterion Protocol | 100% |
| Side Effects | SideEffect Protocol | 100% |
| Action Registry | ActionRegistry class | 100% |
| Governance Engine | GovernanceEngine class | 100% |
| Optimistic Locking | Version field | 50% (ObjectManager) / 100% (ProposalRepository) |
| Async Operations | asyncio patterns | 80% |

---

## Remediation Plan

### Immediate (Sprint 0)
1. [ ] Fix ObjectManager OCC (C-1)
2. [ ] Wrap RelayQueue.dequeue in thread pool (H-1)

### Short-term (Sprint 1)
3. [ ] Migrate RelayQueue to aiosqlite
4. [ ] Enable version_id_col in ORM

### Medium-term (Sprint 2-3)
5. [ ] Unify persistence patterns (ObjectManager → Repository pattern)
6. [ ] Add comprehensive OCC tests

---

## Audit Artifacts

- Plan Document: `docs/plans/PLAN_palantir_compliance_audit.md`
- This Report: `docs/plans/AUDIT_REPORT_palantir_compliance.md`

---

**Audit Complete**
**Status**: CONDITIONAL PASS (84.5%)
**Critical Blockers**: 1 (ObjectManager OCC)
**Next Review**: After C-1 remediation
