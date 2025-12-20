# 🚀 Handoff Protocol: ODA Architecture Repair
> **Target Agent**: Web Claude (Architectural Reasoning Focus)
> **From**: Antigravity (Gemini 3.0 Pro - Orchestrator)
> **Context**: WSL2 Ubuntu / Orion Orchestrator V2 / Antigravity IDE
> **Date**: 2025-12-20

---

## 1. System Anatomy & Environmental Context
**Environment**:
- **OS**: Linux (WSL2 Ubuntu)
- **Root**: `/home/palantir/orion-orchestrator-v2`
- **Architecture**: **Ontology-Driven Architecture (ODA)** (Modeled after Palantir AIP).
- **Core Philosophy**: "Schema is Law." Logic should be derived from data structures (Ontology), not hardcoded in runtime loops.

**Current State**:
We are in a **"Potemkin Village"** state.
- **The Ontology Layer** (`scripts/ontology/`) is rich, well-typed (Pydantic), and robust.
- **The Runtime Layer** (`scripts/runtime/kernel.py`) is a **Facade**. It ignores the Ontology definitions entirely and operates on hardcoded strings and loose dictionaries.
- **Risk**: Creating new Actions in the Ontology has **Zero Impact** on the runtime behavior ("Ghost Actions").

---

## 2. Dynamic Impact Analysis (Deep Code Level)
I have performed a deep-dive analysis of the causal verification implementation. Here are the 5 Critical Structural Failures found:

### 🔴 Failure 1: The Disconnected Kernel (Critical)
**Location**: `scripts/runtime/kernel.py` vs `scripts/ontology/objects/task_actions.py`
- **The Lie**: The system claims to run "Actions".
- **The Truth**:
    - `task_actions.py` defines `DeployServiceAction` (API Name: `deploy_service`).
    - `kernel.py` (Line 95) checks for a hardcoded string `"deploy_production"`.
- **Impact**: The Runtime is invoking a phantom action. The rigorous validation logic in `DeployServiceAction` (SemVer checks, Environment constraints) is **Dead Code**. It is never loaded.

### 🔴 Failure 2: Governance by If-Statement
**Location**: `scripts/runtime/kernel.py` (Lines 84-110)
- **The Lie**: "Hazardous Actions automatically trigger Proposals."
- **The Truth**: 
    - Proposal creation is manually triggered: `if action == "deploy_production": ...`
    - The `ActionType.requires_proposal = True` flag in `actions.py` is ignored.
- **Impact**: Adding a new hazardous action (e.g., `DeleteDatabase`) will bypass governance unless a dev remembers to edit the `kernel.py` loop manually. Security relying on memory is fatal.

### 🔴 Failure 3: Dictionary-Driven Planning (Type Unsafety)
**Location**: `scripts/ontology/plan.py` vs `kernel.py`
- **The Lie**: AI Plans are structured objects.
- **The Truth**: 
    - `Plan` model exists in `plan.py`.
    - `kernel.py` iterates over raw dictionaries (`plan["plan"]`).
- **Impact**: The Kernel accepts *any* garbage structure from the LLM. There is no validation that `priority` is a valid Enum or that `action` exists in the Registry.

### 🔴 Failure 4: Identity Crisis (Duplicate Base Classes)
**Location**: `scripts/ontology/core.py` vs `scripts/ontology/ontology_types.py`
- **The Issue**: Two Base Classes exist.
    - `OrionObject` (`core.py`): Uses `uuid6`, `_is_dirty`.
    - `OntologyObject` (`ontology_types.py`): Uses `uuid4`, `touch()`.
- **Impact**: `Proposal` uses `OntologyObject`. If any legacy code imports `OrionObject`, type checks `isinstance(obj, OntologyObject)` will fail. `core.py` must be purged.

### 🔴 Failure 5: Manual Persistence Coupling
**Location**: `scripts/ontology/storage/`
- **The Issue**: No ORM. 
- **The Truth**: 
    1. Python Object (`Proposal`)
    2. Manual Serializer (`_serialize_proposal`)
    3. Manual Deserializer (`_deserialize_proposal`)
    4. SQL String Migration (`001_create_proposals`)
- **Impact**: Adding 1 field requires 4 coordinated edits. Discrepancies lead to silent data loss (fields not saved) or runtime crashes (SQL syntax errors).

---

## 3. The Codebase Map (Source of Truth)

### A. The Ontology (valid but ignored)
- **`scripts/ontology/actions.py`**: The Action Framework. Defines `ActionType`, `SubmissionCriteria`, `ActionRegistry`.
- **`scripts/ontology/objects/task_actions.py`**: The concrete implementations. Contains the *real* logic we want to run.
- **`scripts/ontology/objects/proposal.py`**: The Governance State Machine (Draft -> Pending -> Approved).

### B. The Runtime (The "Offender")
- **`scripts/runtime/kernel.py`**: The "v3" kernel. It is currently a glorified script using `print` statements and hardcoded logic.
- **`scripts/ontology/storage/proposal_repository.py`**: The manual persistence layer.

---

## 4. Architectural Planning Prompt (For Web Claude)

**Your Mission**: Design the "Re-Coupling" Plan.
We need to refactor `kernel.py` to stop being a "script" and start being a "Generic Engine".

**Constraints**:
1.  **Registry Supremacy**: The Kernel MUST NOT know about specific actions like "deploy_service". It must ask the `ActionRegistry`.
2.  **Type Safety**: The Kernel must deserialize LLM output into the `Plan` Pydantic model.
3.  **Governance Enforcement**: The Kernel must check `action_instance.requires_proposal`. If True, it auto-generates a Proposal. If False, it executes immediately.

**Required Deliverable (The Plan)**:
Please generate a detailed **Implementation Plan** (Markdown) that covers:

1.  **Cleanup Phase**:
    - Deletion of `scripts/ontology/core.py`.
    - Identification of any other dead code.
2.  **Kernel Refactoring Phase**:
    - How to rewrite `_process_task_cognitive` to use `Plan.model_validate()`.
    - How to dynamic import/lookup actions using `action_registry.get()`.
    - Logic for the `ExecutionValidator` (checks `requires_proposal`).
3.  **Persistence Strategy**:
    - Recommendation on whether to stick with manual SQL (for transparency) or introduce a lightweight ORM (SQLModel) to fix Failure #5. (Prefer stability/speed for now).

**Goal**: When this plan is executed, `kernel.py` should be <100 lines of generic code that can run *any* action defined in the Ontology without modification.
