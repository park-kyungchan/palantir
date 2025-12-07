
# Phase 5 Detailed Design: Consolidation & Governance (The Feedback Loop)

> **Objective**: Implement the "Memory of Action" (Provenance) and the "Synthesis of Wisdom" (Consolidation).
> **Constraint**: Anti-Whack-a-Mole (Audit Failure must not crash System, but System must capture Failure).

---

## 1. The Architectural Gap: "Amnesia"
Currently, Orion V3 performs actions perfectly but "forgets" them immediately.
*   **State**: Preserved (Server is "Active").
*   **History**: Lost (Who made it Active? Why? What failed before logic?).
*   **Consequence**: The Agent cannot learn from mistakes or reinforce success.

**Solution**: Introduce **governance** (Action Logs) and **consolidation** (Pattern Mining).

---

## 2. Component Specifications

### 2.1 The Immutable Ledger: `OrionActionLog`
A new Ontology Object dedicated to Provenance.

```python
class OrionActionLog(OrionObject):
    """
    Immutable record of a Kinetic Action attempt.
    """
    # Context
    agent_id: str          # e.g. "Antigravity"
    trace_id: str          # Job ID or Plan ID
    
    # Intent
    action_type: str       # e.g. "server.restart"
    parameters: Dict[str, Any]
    
    # Outcome
    status: str            # "SUCCESS", "FAILURE", "ROLLED_BACK"
    error: Optional[str]   # Exception message
    
    # Impact
    affected_ids: List[str] # ["SRV-001"]
    
    # Meta
    duration_ms: int
```

### 2.2 The "Dual-Transaction" Challenge
**Problem**: If an Action fails, the `UnitOfWork` rolls back the transaction. This erases any "Log Object" created within that transaction.
**Requirement**: We need to persist the *Failure Log* even when the *Action* is rolled back.
**Pattern**: "Business Transaction" (Rollback on Fail) vs. "Audit Transaction" (Always Commit).

**Implementation Strategy**:
1.  `ActionRunner` starts.
2.  Try:
    - `UnitOfWork` (Business TX).
    - Execute Action.
    - Commit Business TX.
    - Status = SUCCESS.
3.  Except:
    - Business TX Rolls back automatically (`__exit__`).
    - Catch Exception.
    - Status = FAILURE.
4.  Finally:
    - Open **New/Separate Session** (or dedicated Audit Connection).
    - Save `OrionActionLog`.
    - Commit Audit TX.

### 2.3 The Consolidation Engine (`Miner`)
A standalone service (or cron job) that reads `OrionActionLog` and updates `OrionPattern`.

*   **Logic (Heuristic v1)**:
    *   **Reinforcement**: If `action_type=X` succeeds > 5 times for `trigger=Y`, increment `OrionPattern.confidence`.
    *   **Suppression**: If `action_type=Z` fails > 3 times, add to `OrionPattern.anti_patterns`.

---

## 3. Implementation Plan

### Step 3.1: Define Governance Schema
- **File**: `scripts/ontology/schemas/governance.py`.
- **Class**: `OrionActionLog`.

### Step 3.2: Enhance Action Runner (The Audit Layer)
- **File**: `scripts/action/core.py`.
- **Refactor**: `ActionRunner.execute`.
- **Logic**: Implement the "Try/Except/Finally" block with double-commit strategy (or separate session for log).
- **Safety**: Ensure logging failure doesn't mask the original business failure (or vice versa).

### Step 3.3: Implement Miner
- **File**: `scripts/consolidation/miner.py`.
- **Function**: `mine_logs()`.

### Step 3.4: Verification
- **File**: `scripts/tests/test_phase5_governance.py`.
- **Scenario**:
    1. Run a `SuccessAction` -> Check Log (SUCCESS).
    2. Run a `FailAction` -> Check DB (Attributes Unchanged) AND Check Log (FAILURE).

---

## 4. Specific Impact Analysis (Anti-Whack-a-Mole)

| Risk | Impact | Mitigation |
| :--- | :--- | :--- |
| **Log Explosion** | DB size grows indefinitely. | Accept for V3. V4 can add Rotation/Archival. |
| **Transaction Leak** | Audit Session stays open. | Use `with SessionLocal() as log_session:` strictly. |
| **Recursion** | Action triggers Action? | `trace_id` passes through context to thread the history. |

---

## 5. Next Steps
1.  Approve Design.
2.  Create Schema.
3.  Modify Core (ActionRunner).
4.  Write Tests.
