# Orion ODA: Ontology Action System & Architecture

**Date:** 2026-01-05
**Version:** 6.0 (Native Edition)
**Protocol:** ANTIGRAVITY_ARCHITECT_V6.0

---

## 1. Action Registry & Dispatch

The Orion Ontology-Driven Architecture (ODA) uses a centralized **Action Registry** to manage all executable functions within the ontology. This decoupled design allows for dynamic discovery and invocation.

### Core Components
- **`ActionType` Base Class**: The interface for all ontology actions. Includes `api_name`, `parameters`, `submission_criteria`, and `requires_proposal`.
- **`ActionRegistry`**: A singleton tracking all registered actions via the `@register_action(api_name)` decorator.
- **`ToolMarshaler`**: The secure entry point for all executions. It handles `ActionContext` verification, stateless instantiation, and standardized result wrapping.
- **`EditOperation`**: Represents atomic changes (CREATE, MODIFY, DELETE, LINK, UNLINK) within a transaction.

### Execution Loop
1. **Signal Dequeue**: Tasks pulled from `RelayQueue`.
2. **Cognitive Analysis**: Natural language mapped to a structured `Plan`.
3. **Governance Check**: Job evaluated against `.agent/rules/` via the `GovernanceEngine`.
4. **Execution**: Non-hazardous jobs dispatched to the `ToolMarshaler`; hazardous jobs persisted as `Proposals`.

---

## 2. Palantir AIP/Foundry Alignment

The ODA implementation is designed for **90% architectural alignment** with Palantir Foundry OSDK standards.

### Feature Mapping
| Palantir Foundry Pattern | ODA Implementation | Alignment Details |
|-------------------------|--------------------|-------------------|
| **Action Types** | `ActionType` Base Class | Defined with parameters and submission criteria. |
| **$validateOnly** | `validate_only` argument | Executes validation but skips mutation. |
| **$returnEdits** | `return_edits` argument | Includes `EditOperation` audit trail in results. |
| **modifiedEntities** | `affected_types` | Map of object types affected by the action. |
| **Transactional Mutation**| `Database.transaction()` | SQLite WAL mode for atomic writebacks. |
| **Submission Criteria** | `validate_evidence()` | Maps to ODA's anti-hallucination evidence requirement. |
| **Palantir Automate** | `execute_with_rsil()` | Implements automated retry logic (default 3) for transitions. |
| **Logic Effects** | `ThreeStageProtocol` | Chained execution stages (A -> B -> C) isomorphic to Logic Effects. |
| **$validateOnly** | `validate_only` argument | Executes validation but skips mutation. |
| **$returnEdits** | `return_edits` argument | Includes `EditOperation` audit trail in results. |
| **modifiedEntities** | `affected_types` | Map of object types affected by the action. |

### AI Ultra & API-Free Context
Since January 2024, Palantir has removed sign-up barriers for AIP (build.palantir.com), providing a "Free in perpetuity" tier (AI Ultra context for ODA):
- **Object Limit**: Up to 50 Ontology object types.
- **SDK Support**: Full OSDK 2.0 functionality.
- **Offline Protocol**: ODA operates in **API-Free** mode, using local OSDK patterns to simulate Foundry backend behavior without external billable API hits.

### Governance Gaps (v6.0 Roadmap)
- [x] **GAP-03 (Writeback)**: `validate_evidence()` prevents hallucinated writes.
- [x] **GAP-11 (RSIL)**: Programmatic retry loop for protocol execution.
- **GAP-04 (Approval Policy)**: Configurable reviewer counts for Proposals.
- **GAP-10 (@OntologyEditFunction)**: Decorator pattern for functions that mutate ontology.
- **GAP-12 (@Edits)**: Provenance tracking for edited object types.

---

## 3. OSDK Query & Connector Alignment

The OSDK implementation provides a robust query builder and database connector.

### Feature Support
| Feature | Implementation | Notes |
|---------|----------------|-------|
| **Primary Key** | String (UUIDv4) | Aligned with Palantir recommendation for JS safety. |
| **Regex Operator** | `SQLiteConnector` | Supported via `regexp_match`. |
| **Logic Trace** | `ObjectQuery` -> `Connector` | Standard OSDK data flow. |
| **Bulk Operations** | `bulk_create`, `bulk_get` | High-performance sync/async support. |

---

## 3. Ontology Modeling Standards (OSv2)

### Primary Key (PK) Restrictions
Object Storage V2 (OSv2) enforces strict modeling to ensure index stability.
- **Prohibited PK Types**: Geopoint, Geoshapes, Arrays, Time series, Real numbers (`decimal`, `double`, `float`).
- **Enforcement**: Unique primary keys are mandatory; duplicates cause indexing failure.

### Action Log Standards
Action Log objects must capture:
- **Action RID** / **UserId** / **Timestamp (UTC)**.
- **Edited Objects**: Primary key values of all objects modified during the action.

---

## 4. Runtime & Persistence Patterns

### OrionRuntime (Semantic Kernel)
- **Schema is Law**: Strict Pydantic enforcement.
- **Registry Supremacy**: No operations performed outside registered `ActionType` classes.
- **Governance Evolution**: Markdown-based rules in `.agent/rules/` are parsed natively by the `GovernanceEngine`.

### DatabaseManager
- **Connection Isolation**: Uses `contextvars` to allow database overrides (e.g., for test-specific SQLite instances).
- **WAL Mode**: Write-Ahead Logging is enforced for high-concurrency support.
- **Transactional Scope**: Async context manager for atomic operation sequences.
