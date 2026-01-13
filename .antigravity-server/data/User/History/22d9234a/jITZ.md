# HWPX ODA Alignment Audit Plan (Jan 2026)

## 1. Overview
Following the successful audit and remediation of the Orion ODA (Jan 2026), this plan outlines the steps to bring the **HWPX Reconstruction Pipeline** into full compliance with the improved ODA standards. The goal is to ensure LLM independence, robust auditability, and semantic safety.

## 2. Audit Phases

### Stage A: SURFACE SCAN (Structure & Config)
**Objective**: Detect and remove hard-coded dependencies.
- **LLM Routing**: Audit `lib/ingestors/` and `convert_pipeline.py` to ensure they use `scripts/llm/config.py` for model selection.
- **MCP Integration**: Verify the pipeline consumes `ANTIGRAVITY_MCP_CONFIG_PATH` for API-Free operation.
- **Ontology Alignment**: Identify all HWP Actions in `lib/models.py` that need to be registered in the central `OntologyRegistry`.

### Stage B: LOGIC TRACE (Process & Safety)
**Objective**: Enforce "Audit-Before-Execution" and data flow integrity.
- **ActionRunner Migration**: Wrap the reconstruction loop in an `ActionRunner` (based on `scripts/simulation/core.py`) to ensure `PENDING` state is logged before Windows automation begins.
- **De-rendering Logic**: Refactor Gemini-based vision de-rendering into `LogicFunction` modules mediated by the `LogicEngine`.
- **Exception Audit**: Scan for bare `except Exception: pass` patterns (as found in the ODA audit) particularly in `executor_win.py` and `core_bridge.py`.

### Stage C: QUALITY GATE (E2E Verification)
**Objective**: Confirm functional pureness and visual fidelity.
- **Pilot Test Run**: Execute the `sample.pdf` reconstruction pipeline and verify the resulting `OrionActionLog` audit trail.
- **Registry Export**: Generate `.agent/schemas/hwpx_ontology.json` to verify the semantic map of HWP actions.

## 3. Reference ODA Standards
This plan is modeled after the remediation master report:
- **LLM Independence**: `load_llm_config()` pattern.
- **Atomic Logging**: `status="PENDING"` before mutation.
- **Logic Engine**: Semantic dispatch via `ExecuteLogicAction`.

---
**Status**: 🛠️ PLANNING (In Progress)
**Owner**: Antigravity Architect
