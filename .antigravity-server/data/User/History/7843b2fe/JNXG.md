# January 2026 ODA Refactoring Audit: Stage A (Surface Scan)

This document records the findings of the **Stage A: Surface Scan (Landscape)** performed as part of the large-scale ODA refactoring under the **ANTIGRAVITY_ARCHITECT_V5.0** protocol.

## 1. Audit Overview
- **Date**: January 5, 2026
- **Protocol**: ANTIGRAVITY_ARCHITECT_V5.0 (FINAL_HYBRID)
- **Target**: Holistic workspace refactoring for Palantir AIP/Foundry standards.
- **State**: `[CONTEXT_NULL]` → `[STAGE_B_COMPLETE]` → `[STAGE_C_IN_PROGRESS]`

## 2. Landscape Scan Findings

### 2.1. AIP-KEY Legacy Status
- **Status**: **[CLEAN]**
- **Details**: Recursive grep search for `AIP-KEY` and `AIP_KEY` yielded no results in the current workspace. Legacy key storage has been successfully removed.

### 2.2. Subscription Gate & Entry Points
- **Status**: **[VALID]**
- **Primary Entry Point**: `scripts/infrastructure/redis_bus.py`
    - Class: `RedisBus`
    - Subscription Logic: Manage `_subscriptions` dictionary and `_subscription_task`.
- **Secondary Entry Point**: `scripts/infrastructure/event_bus.py`
    - Class: `EventBus`
- **Knowledge Context**: Subscription patterns (WebSocket for real-time Foundry updates) are documented in `/coding/knowledge_bases/`.

### 2.3. Path Remnants (Legacy: orion-orchestrator-v2)
- **Status**: **[FIXED]**
- **Legacy Path**: `/home/palantir/orion-orchestrator-v2`
- **Detection Log**:
    - `tests/e2e/test_monolith.py:13`: `sys.path.append("/home/palantir/orion-orchestrator-v2")`
    - `tests/e2e/test_v3_full_stack.py:7`: `sys.path.append("/home/palantir/orion-orchestrator-v2")`
    - `tests/e2e/test_v3_production.py:9`: `sys.path.append("/home/palantir/orion-orchestrator-v2")`
    - `package.json`: Legacy repository URLs in `url` and `homepage` fields.
- **Remediation Plan**: Update all instances to `/home/palantir/park-kyungchan/palantir`. (**COMPLETE**: Verified via recursive grep)

### 2.4. Action Registry Mapping
- **Action Location**: `scripts/ontology/actions/`
- **Core implementation**: `__init__.py` (35KB) contains the base Action classes and validation logic following Palantir Foundry standards (Submission Criteria, Side Effects).

## 3. Logic Trace Findings (Stage B)

### 3.1. Dependency Resolution
- **Status**: **[REMEDIATED]**
- **Actions**: Installed missing dependencies in `.venv`:
    - `instructor`: Required for AIP logic clients.
    - `pytest`, `pytest-asyncio`, `fastapi`, `httpx`: Required for E2E suite.
    - `mcp`: Required for Python-based MCP servers.

### 3.2. E2E Verification Trace
- **Objective**: Execute full integration suite to verify ODA v3 regression safety.
- **Trace**: `Request -> ontology_server.py -> action_registry -> ActionType.execute() -> Database`.
- **Result**: **[SUCCESS]**
    - Total Tests: 123
    - Passed: 123 (100%)
    - Environment: SQLite WAL mode confirmed via `test_wal_mode_enabled`.

## 4. Atomic Quality Audit (Stage C)

### 4.1. Micro-Issue Detection
- **Issue**: **Deprecated `datetime.utcnow()` Usage**
- **Severity**: Low (Maintenance)
- **Detection Log**:
    - `scripts/ontology/plans/models.py:124`
    - `scripts/llm/ollama_client.py:199`
    - `scripts/tools/yt/state_machine.py:40`
    - `scripts/ontology/actions/workflow_actions.py:35`
- **Requirement**: Replace with `datetime.now(timezone.utc)` for compliance with modern Python standards and ODA UTC-aware mandates.

### 4.2. Code Smells & Logic Risks
- **Issue**: **Bare `except:` Catch-All Blocks**
- **Severity**: Medium (Safety)
- **Detection Log**:
    - `scripts/ontology/actions/memory_actions.py:39`: Swallows all exceptions during status parsing.
    - `scripts/ontology/actions/memory_actions.py:119`: Swallows all exceptions during pattern status parsing.
- **Risk**: Swallowing `SystemExit` or `KeyboardInterrupt` can prevent proper process termination. Silent failure during status parsing leads to data drift (incorrect status being saved as default `ACTIVE`).

### 4.3. Documentation Syntax Warnings
- **Issue**: **Invalid escape sequence `\,` in docstring**
- **File**: `scripts/mcp_preflight.py:2`
- **Fix**: Convert to raw string `r"""..."""`.

## 5. Holistic Impact Simulation (XML Sec 5.1)

### Simulation_Target: `Bare except: blocks in memory_actions.py`

**Execution_Trace:**
1. **Initial_State**: `SaveInsightAction.apply_edits()` parses `status` from parameters.
2. **Mutation**: User/Client passes an invalid status string (e.g., `"voodoo"`). `ObjectStatus("voodoo")` raises a `ValueError`.
3. **Ripple_Effect**: The bare `except: pass` catches the error. The logic proceeds with the default `status = ObjectStatus.ACTIVE`.
4. **Verdict**: **[MEDIUM_RISK]**. Silent data corruption occurs. The user expects one status, but the system saves another without any audit log or warning. This erodes the "Zero-Trust on Context" principle of ODA v3.0.

*Remediation*: Replace with `except ValueError as e:` and log a warning/error.

## 6. Compliance Matrix (Preliminary)
- `Domain_Invariants (Sec 2.5)`: **[PASS]** (Legacy paths cleaned, core data flow verified).
- `Layer_Architecture (Sec 3.5)`: **[PASS]** (Verification confirms strict separation of action logic and storage).

## 7. Next Steps
Continue **Stage C: Atomic Quality Audit** to patch deprecations and verify per-line safety in critical action handlers.
