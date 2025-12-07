
# Orion End-to-End (E2E) Verification Specification

> **Objective**: Validate the holistic integration of Object Kernel, Kinetic Actions, Simulation Engine, and Semantic Memory.
> **Scenario**: "Cognitive Auto-Remediation"
> **Complexity**: High (Multi-Phase Integration)

---

## 1. Scenario Narrative
The system encounters a "High Memory Usage" alert on a Server.
1.  **Memory Recall**: The Agent queries the Ontology Kernel for relevant `OrionPattern`s regarding "high memory".
2.  **Simulation (Option A)**: The Agent tries a "Restart" action in a Sandbox.
    - *Result*: The specific Server type prevents simple restarts (Constraint Violation).
    - *Outcome*: Transaction Rolled Back. Safe.
3.  **Refinement**: The Agent reads the Pattern details, which suggest "Clear Cache" before "Restart".
4.  **Simulation (Option B)**: The Agent tries "Clear Cache" -> "Restart" in a Sandbox.
    - *Result*: Success. Diff shows status change.
5.  **Commit**: The Agent executes the plan on the Real DB.

## 2. Components Under Test
| Component | Function | Phase |
| :--- | :--- | :--- |
| **Object Kernel** | Persistence, Dirty Tracking, FTS Query | Phase 1/4 |
| **Kinetic Action** | `UnitOfWork`, `ActionDefinition` | Phase 2 |
| **Simulation** | `ScenarioFork`, `SimulationDiff` | Phase 3 |
| **Memory** | `OrionPattern` (Pydantic Schema) | Phase 4 |

## 3. Test Implementation Plan

### 3.1 Setup (Fixtures)
- **Target Object**: `SimulationServer` (ID: `SRV-E2E-001`, Status: `Unstable`, Type: `Legacy`).
- **Knowledge**: `OrionPattern` (ID: `PAT-E2E-001`, Trigger: `memory_leak`, Solution: `Must clear cache first`).

### 3.2 Action Definitions
- `RestartServer`: Fails if `server.type == "Legacy"` and `cache_cleared` is False.
- `ClearCache`: Sets `cache_cleared = True`.

### 3.3 Execution Flow
```python
def test_e2e_scenario():
    # 1. Setup Data (Real DB)
    
    # 2. Knowledge Retrieval (FTS)
    # Search for "memory_leak" -> Find Pattern.
    
    # 3. Simulation 1 (The Fail)
    # Action: RestartServer
    # Expect: Exception (Constraint Check)
    # Verify: Real DB untouched.
    
    # 4. Simulation 2 (The Success)
    # Action: ClearCache, then RestartServer
    # Expect: Diff shows [Updated(SRV-001)]
    
    # 5. Application (Real World)
    # Execute Option B Context.
    # Verify: Real DB updated.
```

## 4. Success Criteria
1. **FTS Correctness**: Must find the pattern via text search.
2. **ACID Integrity**: The failed simulation must NOT change the DB.
3. **Simulation Accuracy**: The successful simulation must capture the Diff.
4. **Final Persistence**: The final state must be saved to SQLite.
