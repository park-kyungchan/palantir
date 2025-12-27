# Orion ODA V3.5 Internal Architecture Analysis
> **Generated**: 2025-12-27
> **Context**: Post-Audit Deep Dive & E2E Verification
> **Status**: APPROVED

## 1. Executive Summary
This document records the **actual, implemented state** of the Orion Orchestrator V3.5 as of late 2025. It diverges slightly from high-level documentation by capturing the physical realities of the codebase (file paths, specific library versions, and architectural decisions).

**Critical Finding**: The system is a **Hybrid Async-Sync** architecture using `asyncio` for the Kernel Loop but leveraging `RelayQueue` (SQLite) for inter-process communication.

---

## 2. Component Topology (Physical Layout)

### 2.1 The Runtime Kernel (`scripts/runtime/`)
- **EntryPoint**: `scripts.runtime.kernel.OrionRuntime`
- **Loop**: Asyncio Event Loop (`while running: await ...`)
- **Key Dependency**: `scripts.relay.queue.RelayQueue` (See 2.2)
- **AI Client**: `scripts.llm.instructor_client.InstructorClient`
    - Uses `instructor` library for Pydantic Schema enforcement.
    - Uses `tenacity` for Retry logic.

### 2.2 The Relay System (`scripts/relay/`)
- **Location**: `scripts/relay/queue.py` (NOT in `scripts/runtime/`)
- **Mechanism**: SQLite-based Queue with WAL mode (`PRAGMA journal_mode=WAL`).
- **Async Wrapper**: Implements `dequeue_async` using `asyncio.to_thread` to prevent blocking the Kernel's event loop.
- **Why Important**: This is the "Nervous System" connecting Agents (Handoffs) to the Kernel.

### 2.3 The Governance Layer (`scripts/ontology/`)
- **Action Registry**: `scripts.ontology.actions.action_registry`
    - Architecture: Decorator-based registration (`@register_action`).
    - **Hazard Control**: `requires_proposal=True` flags strictly enforce the `GovernanceEngine` check in the Kernel.
- **Marshaler**: `scripts.runtime.marshaler.ToolMarshaler`
    - Role: Secure Execution Gateway. No action runs raw; all pass through `execute_action`.

### 2.4 The Persistence Layer (`scripts/ontology/storage/`)
- **Framework**: SQLAlchemy 2.0 Async ORM (`sqlite+aiosqlite`).
- **Repository**: `ProposalRepository`
    - **Concurrency**: Optimistic Locking via `version` column. Raises `ConcurrencyError` on mismatch.
    - **Audit**: `ProposalHistoryModel` records every state transition.
- **Models**: `scripts.ontology.storage.models`
    - Strictly typed using `Mapped[]` and `mapped_column` (SQLAlchemy 2.0 style).

---

## 3. Workflow Audit & Restoration Log
**Date**: 2025-12-27
**Incident**: System Prompt declared 6 workflows; Filesystem had 1.

| ID | Workflow | Status | Resolution |
|----|----------|--------|------------|
| 00 | Start | MISSING | Created. Links `mcp_preflight` + `db_init` + `recall`. |
| 01 | Plan | ACTIVE | Existing. |
| 02 | Memory | MISSING | Created (Manual Guide). |
| 03 | Maintain | MISSING | Created. Implemented `rebuild_db.py`. |
| 04 | Audit | MISSING | Created. |
| 05 | Consolidate | MISSING | Created. Links `consolidate.py`. |

---

## 4. Known Gotchas & Constraints

### 4.1 SQLAlchemy 2.0 Strict Mode
- **Issue**: `session.execute("VACUUM")` fails.
- **Rule**: All raw SQL strings **MUST** be wrapped in `sqlalchemy.text()`.
- **Fix Applied**: `scripts/maintenance/rebuild_db.py` updated.

### 4.2 Python Environment
- **Path**: `/home/palantir/.venv/bin/python`
- **Constraint**: System `python3` lacks dependencies (`pydantic`). ALWAYS use venv.

### 4.3 Missing Files (Resolved)
- `scripts/runtime/relay.py` was assumed but does not exist.
- **Correct Path**: `scripts/relay/queue.py`.

---

## 5. E2E Validation Flow
The system integrity is verified by `scripts/tests/test_workflow_e2e.py` which:
1.  **Wipes DB** (Rebuild).
2.  **Plans** (Generates Handoff MD).
3.  **Executes** (Simulates Kernel Logic -> Relay -> Action).
4.  **Persists** (Verifies Tuple in SQLite).

This document serves as the **CODE-LEVEL TRUTH** for the Orion Architecture.
