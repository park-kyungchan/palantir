# Orion Orchestrator V2 - Codebase Map
> **Last Updated:** 2025-12-21
> **Status:** ODA V3 Prototype (Cleaned & Optimized)

## 1. Directory Structure

### `scripts/ontology/` ( The Kernel )
The core of the Ontology-Driven Architecture.
*   **`actions.py`**: Declarative Action Definitions (The logic).
*   **`ontology_types.py`**: Base Pydantic models (The types).
*   **`manager.py`**: `ObjectManager` implementation (The gatekeeper).
*   **`storage/`**: SQLAlchemy Async ORM & Repository layer.
    *   `database.py`: Async Engine management.
    *   `models.py`: SQLAlchemy Table definitions (`AsyncOntologyObject`).
    *   `proposal_repository.py`: Persistence logic for Proposals.
*   **`jobs/`**: Background jobs (Cleanup, etc.).

### `scripts/api/` ( The Interface )
*   **`main.py`**: FastAPI entry point.
*   **`routes.py`**: API Endpoints mapping to Actions.

### `scripts/runtime/` ( The Loop )
*   **`kernel.py`**: The ODA Runtime loop (Plan -> Act -> Reflect).

### `data/` ( Persistence )
*   **`ontology.db`**: The SQLite production database (WAL enabled).

### `.agent/` ( Agent Memory )
*   **`plans/`**: JSON execution plans.
*   **`handoffs/`**: Inter-agent communication artifacts.
*   **`logs/`**: Execution traces.

### `coding/palantir-fde-learning/` ( Context )
Educational resources and research Archives.
*   **`knowledge_bases/`**: The 8 Core Curriculum Markdown files.
*   **`archives/`**: Research prompts and dumps.

---

## 2. Key Architecture Concepts
1.  **Identity Unification**: Domain Objects (`ontology_types.py`) and Persistence Models (`storage/models.py`) are decoupled but mapped 1:1.
2.  **Action Supremacy**: All mutations MUST go through `ActionService` (conceptually) or `ActionType.execute`.
3.  **Human-in-the-Loop**: Hazardous actions require `Proposal` objects managed by `ProposalRepository`.

## 3. Maintenance Notes
*   **Schema Changes**: Run `scripts/migration/` scripts (if any) or rely on `Database.initialize()` for dev.
*   **Testing**: E2E tests are in `tests/e2e/`.
