# ODA 3-Stage Planning Protocol (v6.0)

## 1. Overview
The Planning Protocol is the primary mechanism for transforming user intent into a governed, executable implementation plan. It is enforced via the `@/01_plan` workflow and ensures all development work adheres to the Orion ODA standards.

## 2. Protocol Stages

### Stage A: BLUEPRINT (Surface Scan)
**Goal:** Establish requirements and remove guesswork by grounding the request in actual codebase reality.

- **Actions:**
  1. **Context Check**: Verify local documentation and project structure.
  2. **Codebase Scan**: Search for existing tools, modules, or patterns that can be reused.
  3. **Scope Definition**: Identify boundaries, constraints, and target files.
  4. **Complexity Assessment**: Categorize the task magnitude (Small/Medium/Large).
- **Evidence Required:**
  - `files_viewed`: List of paths analyzed.
  - `requirements`: List of core functional and non-functional needs.
  - `complexity`: String indicator of task scale.

### Stage B: INTEGRATION TRACE (Logic Analysis)
**Goal:** Prevent integration failures by tracing the actual data flow and validating dependencies.

- **Actions:**
  1. **Import Verification**: Confirm that all required modules and external libraries exist.
  2. **Signature Matching**: Ensure new code or changes align with existing API signatures.
  3. **TDD Breakdown**: Define implementation phases using Test-Driven Development (RED -> GREEN -> REFACTOR).
- **Evidence Required:**
  - Phase structure with explicit "Quality Gates" (Build + Lint + Tests).

### Stage C: QUALITY GATE (Verification)
**Goal:** Final pre-execution audit to ensure the plan is sound.

- **Actions:**
  - **Build & Test Verification**: Confirm the current project builds and existing tests pass.
  - **Risk Assessment**: Identify Technical and Integration risks with probability and mitigation.
- **Evidence Required:**
  - Pass/Fail verdict for the plan.

## 3. Implementation Workflow (`/01_plan.md`)
The protocol is operationalized through a standardized markdown workflow that the agent must follow sequentially.

- **Protocol implementation:** `scripts/ontology/protocols/planning_protocol.py`
- **Handoff mechanism:** `python -m scripts.ontology.handoff`

## 4. Operational Constraints
- **NO SKIPPING**: Stages A, B, and C must be completed in order.
- **EVIDENCE INJECTION**: The agent must provide explicit evidence logs for each stage to satisfy the `GovernanceEngine` compliance checks.
