
# Phase 3 Detailed Design: Simulation Substrate (The "What-If" Engine)

> **Objective**: Enable Safe Experimentation (Dry-Runs) via SQLite Savepoints.
> **Constraint**: Anti-Whack-a-Mole (Zero Accidental Commits).

---

## 1. Deep Impact Analysis: The "Session Isolation" Risk
**Finding**: In Phase 2, `UnitOfWork` creates a *fresh* `SessionLocal()` every time it runs.
**Risk**: If we wrap `ActionRunner` in a `ScenarioFork` (Transaction), the Action will ignore our Fork and commit directly to the DB because it uses a separate connection/session.
**Mitigation**: 
1. `UnitOfWork` must support **Session Injection**.
2. `ActionRunner` must be able to inherit the "Current Scenario Session".

---

## 2. Component Specifications

### 2.1 `ScenarioFork` (The Sandbox)
A Context Manager that leverages SQLAlchemy's `begin_nested()` (SAVEPOINT).
```python
class ScenarioFork:
    def __init__(self, manager: ObjectManager):
        self.manager = manager
        self.parent_session = manager.default_session # Or a specific session
    
    def __enter__(self):
        # 1. Create a Nested Transaction (Savepoint)
        self.nested_tx = self.parent_session.begin_nested()
        return self.parent_session # Identify this as the "Sandbox Session"
        
    def __exit__(self, exc_type, ...):
        # 2. ALWAYS Rollback the nested transaction at the end of simulation
        self.nested_tx.rollback() 
        # Note: We rollback to discard changes after inspecting them.
```

### 2.2 `SimulationEngine`
Orchestrates the execution of Actions within a Fork.
```python
def run_simulation(actions: List[ActionDefinition], ctx: ActionContext):
    # 1. Start Fork on the Manager's default session
    with ScenarioFork(manager) as sandbox_session:
        
        # 2. Configure Runner to use Sandbox
        # CRITICAL: UnitOfWork must use sandbox_session, NOT create new one.
        runner = ActionRunner(manager, session=sandbox_session)
        
        # 3. Execute Actions
        for action in actions:
            runner.execute(action, ctx)
            
        # 4. Calculate Diff (Session Inspection)
        diff = calculate_diff(sandbox_session)
        
        # 5. Exit (Auto-Rollback)
    return diff
```

### 2.3 Refactoring Requirements (Phase 2 Update)
**`scripts/action/core.py`**:
- Update `UnitOfWork.__init__` to accept `session: Optional[Session]`.
- Update `ActionRunner.__init__` to accept `session: Optional[Session]`.
- Update `ActionRunner.execute` to pass this session to `UnitOfWork`.

---

## 3. Implementation Plan

### Step 3.1: Refactor Action Core (Dependency Injection)
- Modify `UnitOfWork` to prefer an injected session over `SessionLocal()`.
- Ensure `UnitOfWork` does **NOT** close an injected session (it doesn't own it).
- Ensure `UnitOfWork` does **NOT** commit an injected session if it's a Nested Transaction? 
    - *Correction*: Code calls `commit()`. SQLAlchemy handles nested commit by releasing savepoint. This is fine. But we must ensures `ScenarioFork` rolls back the *parent* of the savepoint or the savepoint itself.

### Step 3.2: Implement Simulation Core
- **File**: `scripts/simulation/core.py`.
- **Classes**: `ScenarioFork`, `SimulationEngine`.
- **Diff Logic**: Inspect `session.new`, `session.dirty`, `session.deleted`.

### Step 3.3: Verification Script
- **File**: `scripts/simulation/tests/test_simulation.py`.
- **Scenario**:
    1. Base State: Server A (Status: Active).
    2. Start Simulation.
    3. Action: Set Status -> Down.
    4. Assert: `SimulationResult` says "Status changed to Down".
    5. End Simulation.
    6. Assert: Real DB Status is still "Active". (Isolation Proven).

---

## 4. Verification Checkpoints
1. **Leakage Test**: Does the simulation write to the `.db` file? (Check file mtime or content via separate connection).
2. **Diff Accuracy**: Does `session.dirty` correctly capture the exact changes?
3. **Re-usability**: Can we run 2 simulations in a row?
