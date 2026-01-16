# Orion Framework V3.0 (Palantir AIP Edition)

The **Orion Framework** is a "Decision-Centric" Agentic IDE Architecture, designed to mimic the **Palantir Ontology**.

## 🏗️ Architecture

### 1. Conceptual Pillars
*   **Schema-First**: Ontology types are exported from the runtime registry via `python -m scripts.ontology.registry` into `.agent/schemas/ontology_registry.json` (legacy JSON schema generation remains in `scripts/build_ontology.sh`).
*   **Action Mandate**: State mutation is ONLY allowed via `ActionDispatcher`. Raw `open(..., 'w')` is prohibited for logic.
*   **Eventual Consistency**: All changes are logged to the Audit Ledger (`.agent/logs/ontology.db`) before execution.

### 2. Core Components (`scripts/`)
*   **`engine.py`**: The CLI Entrypoint. Bootstraps the workspace and dispatches initial Plans.
*   **`governance.py`**: The **Action Dispatcher**. Enforces Rule 1.1 (Action Mandate) and Rule 4.1 (Audit).
*   **`loop.py`**: The **Hybrid Executor**. Runs both Tier 1 (Governed Class) and Tier 2 (Function Tool) Actions.
*   **`actions.py`**: The Tool Registry for LLM capabilities (Read/Write/Grep).
*   **`ontology/`**: Auto-generated Python Models (Do not edit manually).

### 3. Digital Twin App (`math/`)
A reference implementation demonstrating the Ontology alignment.
*   **Backend**: FastAPI with `NumberAnalysis` schema.
*   **Frontend**: React with `openapi-typescript` generated client.

## 🚀 Usage

### Initialize Workspace
```bash
python3 scripts/engine.py init
```

### Dispatch a Task via Router (Rule-Based)
```bash
python3 scripts/engine.py dispatch "read file README.md"
```

### Dispatch a Plan Manually
```bash
python3 scripts/engine.py dispatch --file .agent/plans/my_plan.json
```

## 🔒 Governance Rules (CIP-PALANTIR-V1)
1.  **NEVER** write to files directly in logic code. Use `OrionAction`.
2.  **ALWAYS** validate parameters using Pydantic.
3.  **ALWAYS** define new Actions in the Ontology first.
