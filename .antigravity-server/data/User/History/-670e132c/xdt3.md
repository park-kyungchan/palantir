# Palantir AIP/Foundry Alignment Mapping (v3.0)

This document provides a technical mapping between the Orion ODA implementation and parent Palantir AIP/Foundry architectural patterns.

## 1. Action Types & Execution

| Palantir Foundry Pattern | ODA Implementation | Alignment Details |
|-------------------------|--------------------|-------------------|
| **Action Types** | `ActionType` (Base Class) | Defined with `api_name`, `parameters`, and `submission_criteria`. |
| **$validateOnly** | `validate_only` arg | Executes `validate()` but skips `apply_edits()`. |
| **$returnEdits** | `return_edits` arg | Conditionally includes `edits` (Audit Trail) in the result. |
| **modifiedEntities** | `affected_types` | Map of object types created/modified/deleted during the action. |
| **Transactional Mutation**| `Database.transaction()` | Uses SQLite WAL mode to ensure atomic writebacks. |
| **Concurrency Retry** | `MAX_RETRIES` (3) | Exponential backoff for `ConcurrencyError` (Optimistic Locking). |

## 2. Submission Criteria (Validation)

Orion ODA implements a `SubmissionCriterion` protocol that maps directly to Palantir Foundry constraint types.

| Palantir Constraint | ODA Validator Class | Implementation Segment |
|---------------------|----------------------|------------------------|
| `required` | `RequiredField` | `actions/__init__.py:125` |
| `enum` | `AllowedValues` | `actions/__init__.py:146` |
| `maxLength` | `MaxLength` | `actions/__init__.py:178` |
| `arraySize` | `ArraySizeValidator` | `actions/__init__.py:227` |
| `STRING_LENGTH` | `StringLengthValidator`| `actions/__init__.py:279` |
| `RANGE` | `RangeValidator` | `actions/__init__.py:333` |
| `regex` | *(GAP-05)* | Not yet implemented. |

## 3. Side Effects & Writebacks

Palantir Foundry distinguishes between logic that must succeed for the action to commit (**Writebacks**) and logic that can fail without affecting the commit (**Side Effects**).

| Feature | timing | Failure Impact | ODA Status |
|---------|--------|----------------|------------|
| **Writeback** | Pre-Mutation | Aborts Action | **GAP-03** |
| **Side Effect** | Post-Mutation | Logged warning | ✅ Implemented |

**ODA Implementation Context**:
- Logic for Side Effects is encapsulated in the `SideEffect` protocol.
- Executed in `ActionType._execute_side_effect_with_retry()`.
- Supports `LogSideEffect`, `WebhookSideEffect`, `SlackNotification`, and `EventBusSideEffect`.

## 4. Governance & Proposals

| Palantir Governance | ODA Governance | Alignment Details |
|---------------------|----------------|-------------------|
| **Propose Change** | `create_proposal` | Creates `Proposal` object with `status=PENDING`. |
| **Review / Diff** | `ProposalHistory` | Tracks transitions and stores payload for diffing. |
| **Approval Policy** | *(GAP-04)* | Missing `eligible_reviewers` and `required_approvals`. |
| **Writeback Rules** | `requires_proposal` | ActionRegistry flag that blocks direct execution. |

## 5. Architectural Verdict

The Orion ODA v3.0 codebase demonstrates a **90% architectural alignment** with Palantir AIP/Foundry OSDK standards. The remaining 10% (Gaps 03-05) are advanced governance and validation features slated for the v3.1 Roadmap.
