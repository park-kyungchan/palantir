# Orion ODA: Workflow Utility Guide

## 1. Overview of Workflow Core (27 Actions)

The Orion workspace provides 9 specialized workflows in `.agent/workflows/` to manage the end-to-end lifecycle of document reconstruction.

## 2. High-Frequency Workflows (Primary)

| Workflow | Purpose | Rationale |
|:---|:---|:---|
| `/00_start` | Session Initialization | Loads LTM, checks MCP health, and prepares the DB context. |
| `/01_plan` | 3-Stage Planning | Enforces Stage A (Blueprint) -> B (Trace) -> C (Gate) before any code is written. |
| `/deep-audit` | Structural Verification | RSIL-based logic trace to prevent integration regressions. |

## 3. Maintenance & Safety Workflows (Secondary)

| Workflow | Purpose | Target |
|:---|:---|:---|
| `/06_deprecation_check` | Pre-commit Audit | Checks for Pydantic V2/Datetime/Pytest regressions before push. |
| `/03_maintenance` | Environment Repair | Rebuilds SQLite schemas and clears stale temporary artifacts. |

## 4. Knowledge & Memory Workflows (LTM)

| Workflow | Purpose | Impact |
|:---|:---|:---|
| `/05_consolidate` | Knowledge Extraction | Merges execution traces into permanent Patterns and Insights. |
| `/02_manage_memory` | Schema Injection | Manually injects external knowledge (e.g., KS X 6101 specs) into semantic memory. |
| `/07_memory_sync` | CLI-ODA Handoff | Synchronizes background research results with the main ODA instance. |

## 5. Recommended Workflow Chain

For maximized visual fidelity in HWPX reconstruction, follow this sequence:

1. **Start**: `/00_start` (Initialize session)
2. **Plan**: `/01_plan` (Define OWPML tags and builder state)
3. **Execute**: (Standard code generation)
4. **Audit**: `/deep-audit` (Verify XML nesting logic)
5. **Finalize**: `/06_deprecation_check` (Ensure stability)
6. **Learn**: `/05_consolidate` (Preserve lessons found in HWPX edge cases)

---
**Status**: ACTIVE. Current agent focus is restricted to `/01_plan` and `/deep-audit` for pipeline stability.
