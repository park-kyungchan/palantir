
# Phase 2 Detailed Design: The Kinetic Action Framework

> **Objective**: Implement "Governed Mutation" where all state changes are encapsulated in Transactional Actions.
> **Constraint**: Anti-Whack-a-Mole (Zero Regressions, Strict Verification).

---

## 1. Architectural Gap: Transaction Management
**Current State (Phase 1)**: `ObjectManager.save(obj)` commits immediately (`session.commit()`).
**Problem**: An Action might update 3 objects. If the 3rd update fails, the first 2 are already committed (Partial State). This violates ACID.
**Solution**: Refactor `ObjectManager` to decouple `flush` from `commit`. Introduce a `UnitOfWork` context.

---

## 2. Component Specifications

### 2.1 `UnitOfWork` (The Atomic Wrapper)
A context manager that controls the `SQLAlchemy` session lifecycle.
```python
with UnitOfWork(object_manager) as uow:
    # Action Logic runs here
    server.status = "Down"
    uow.register_dirty(server)
    # No SQL execution yet
# On Exit: Check Validation -> Flush -> Commit -> Close
```

### 2.2 `ActionDefinition` (The Interface)
An abstract base class (ABC) that enforces the Palantir Action Lifecycle.
```python
class ActionDefinition(ABC):
    @classmethod
    def id(cls) -> str: ...
    
    @abstractmethod
    def validate(self, ctx: ActionContext) -> bool:
        """Read-Only checks. Returns True if executable."""
        
    @abstractmethod
    def apply(self, ctx: ActionContext):
        """Pure state mutation. NO I/O allowed."""

    def describe_side_effects(self, ctx: ActionContext) -> List[SideEffect]:
        """Declarative description of what happens after commit."""
```

### 2.3 `ActionRunner` (The Engine)
The core logic that executes the lifecycle.
1. **Initialize**: Create `ActionContext` and `UnitOfWork`.
2. **Phase 1 (Validation)**: Call `validate()`. If Fail -> Raise `ActionValidationError`.
3. **Phase 2 (Mutation)**: Call `apply()`. Catch logic errors.
4. **Phase 3 (Commit)**: `uow.commit()`. This pushes all dirty objects to SQLite transactionally.
5. **Phase 4 (Effects)**: If Commit success, execute Side Effects (e.g., print to stdout or async queue).

---

## 3. Implementation Plan (Step-by-Step)

### Step 3.1: Transaction Support in ObjectManager
- **Refactor**: Modify `scripts/ontology/manager.py`.
- **Change**: `save(obj)` will become `register(obj)` or `flush(obj)`.
- **New Method**: `commit()` (explicit calls).
- **Safe-guard**: Keep `save()` for backward compatibility (auto-commit=True default), but allow `auto-commit=False`.

### Step 3.2: Create Action Core
- **File**: `scripts/action/core.py`.
- **Content**: `ActionDefinition`, `ActionContext`, `UnitOfWork`.

### Step 3.3: Reference Implementation
- **File**: `scripts/action/builtins.py`.
- **Content**: Example `UpdateServerStatus` action to prove the pattern.

### Step 3.4: Verification Script
- **File**: `scripts/action/tests/test_transaction.py`.
- **Scenario**:
    1. Update Object A.
    2. Update Object B.
    3. Raise Error manually.
    4. **Assert**: Object A is NOT updated in DB (Rollback verification).

---

## 4. Verification Checkpoints
1. **ACID Test**: Does an error in step 2 rollback step 1?
2. **Isolation Test**: Are changes visible inside `apply()` before commit?
3. **Purity Test**: Does `apply()` fail if it tries to print/network? (Hard to enforce mechanically in Python, but we will enforce via `Lint` rules or convention).
