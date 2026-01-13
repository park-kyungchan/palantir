# ODA Agent Workflows

## Overview
The ODA uses a sequence of markdown workflows to guide high-level agent behavior. These are located in `/home/palantir/.agent/workflows/` and serve as procedural "runbooks" for the system's core capabilities.

## Workflow Inventory

| Sequence | File Name | Purpose |
| :--- | :--- | :--- |
| 00 | `00_start.md` | Session initialization, protocol injection, and bootstrap. |
| 01 | `01_plan.md` | Strategic planning and task decomposition. |
| 02 | `02_manage_memory.md` | Working memory and episodic recall optimization. |
| 03 | `03_maintenance.md` | Routine environment and code health checks. |
| 04 | `04_governance_audit.md` | Verification of protocol compliance (Kernel v5.0). |
| 05 | `05_consolidate.md` | Information synthesis and KI consolidation logic. |
| 06 | `06_deprecation_check.md` | Legacy code and rule identification / cleanup. |
| 07 | `07_memory_sync.md` | Persistence of learned insights to long-term storage. |
| DA | `deep_audit.md` | Core implementation of the Kernel v5.0 Deep-Dive-Audit. |
| FL | `fde_learn.md` | Activation of the Palantir FDE Learning Protocol v2.0. |

## Prompt Optimization Strategy (Slash Commands)
To maximize context windows and token efficiency, the system avoids monolithic boilerplates and instead uses **Slash Command Workflows**.

- **Challenge**: Boilerplate prompts (e.g., v5.0 Kernel) consume 1500+ tokens per turn.
- **Solution**: Encapsulate logic in `.agent/workflows/` files triggered by commands like `/deep-audit`.
- **Token Economy**: Transitioning to file-based workflows results in a **~95% reduction** in redundant token overhead (~1500 tokens → ~20 tokens).

### Trigger Syntax
- **Explicit**: `/deep-audit [target]`
- **Keyword**: `[KERNEL_V5_AUDIT]`
- **Workflow**: `/01_plan` (contains embedded audit gates)

## Execution Model
Workflows are typically read by the agent at the start of a relevant phase. They are designed to be "living documents" that the ODA can refine via iterative feedback loops.
