```python
# 🔍 DEEP RESEARCH CONTEXT SNIPPET
# Target: Web Claude (Architecture Research)
# Source: Active Codebase State Analysis

# Q1: Kernel State
# File: scripts/runtime/kernel.py (Total Lines: 120)
# Method: _process_task_cognitive (Lines 68-112)
# Status: SCRIPT-LIKE / UNTYPED
# Evidence:
# - Manual Dict Parsing: `title = step.get("title", "Untitled")`
# - Hardcoded Logic: `if action == "deploy_production": ...`
# - Dead Code: Ignores `ActionRegistry` entirely.

# Q2: Plan Model
# File: scripts/ontology/plan.py
# Status: DEFINED BUT IGNORED
# Schema Mismatch:
# - Kernel expects matches: `json_schema={"plan": []}` (List of dicts)
# - Pydantic Model expects: `class Plan(BaseModel): jobs: List[Job] ...`
# - Action Required: Kernel must be updated to prompt for the Pydantic Schema, not the ad-hoc dict.

# Q3: Persistence Strategy Recommendation (Antigravity Opinion)
# Current: Manual SQL (aio-sqlite) + Manual Serialization in `proposal_repository.py`.
# Recommendation: **MIGRATE TO SQLMODEL (or SQLAlchemy Async)**
# Reason: 'Manual Persistence Mapping' is identified as Failure #5 (Maintenance Nightmare).
# Constraint: Must remain Async (aiosqlite underlying driver is fine, but need ORM layer).
# Priority: Safety (Type-Checked Schema) > Speed of Implementation.
```
