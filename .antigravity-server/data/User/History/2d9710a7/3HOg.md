# Orion ODA Workspace Reorganization

## Overview
In January 2026, the Orion Ontology-Driven Architecture (ODA) was fully migrated from a sub-repository structure (`/home/palantir/orion-orchestrator-v2/`) to the root workspace (`/home/palantir/`). This consolidation establishes the root as the single source of truth for the ODA kernel, rules, and workflows, allowing them to operate globally across the environment.

## Key Changes

### 1. Hoisting the Core
All core directories are moved from the sub-directory to the root:
- `/scripts/`: The ODA kernel and MCP servers.
- `/config/`: System and environment settings.
- `/coding/` & `/governance/`: specialized ODA domains.

### 2. Path Redirection
- **MCP Configuration**: The `mcp_config.json` is updated to point to `/home/palantir/` instead of `orion-orchestrator-v2`.
- **PYTHONPATH**: Python tools now use the root as the base package directory.

### 3. Agent Metadata Consolidation
The `.agent/` directory at the root is the single source of truth:
- **Backup**: Before merging, a full backup of the root `.agent` was created. After verifying the root-based ODA stability, these backups (e.g., `/home/palantir/.agent_backup_20260104_103717/`) were deleted to maintain environment cleanliness.
- **Rules & Workflows**: Merged from the repository (`orion-orchestrator-v2/.agent/`) to the root `.agent/`.
- **Handoffs**: Migrated to the root `.agent/handoffs`.
- **Persistence**: Runtime databases (e.g., `orion_ontology.db`) and logs are maintained at the root.

### .agent/ Directory structure
The `.agent/` directory serves as the ODA's persistence and governance layer:
- `rules/`: Governance rules (kernel_v5, domain, governance).
- `workflows/`: Step-by-step procedural guides (00_start.md to 07_memory_sync.md).
- `schemas/`: Data models and validation logic.
- `logs/`: High-level execution and audit logs.
- `indexes/`: File and knowledge markers.
- `handoffs/`: Context transfer artifacts.
- `orion_ontology.db`: The core SQLite database for ontology state and proposal persistence.

### 5. Antigravity & Metadata Directories
The environment contains specialized directories for LLM-specific persistence and cross-session memory:
- **.gemini/**: Primary storage for Gemini-specific context, brain artifacts, and code trackers.
- **.antigravity/**: Traditionally expected at the root for Antigravity-specific settings. 
- **Symlink Strategy**: To maintain IDE compatibility while preserving existing data, a symlink is used: `.antigravity -> .gemini/antigravity`.
- **Restoration**: In case of a `git reset --hard` or accidental deletion, the link must be recreated to reconcile the system's "Brain" with the active workspace.

## Architectural Rationale
Consolidating to the root eliminates ambiguity between "repository" code and "active" agent code. It allows the ODA to operate on the entire codebase without needing relative path adjustments or duplicate environment setups.

## Terminal & Environment Compatibility
The ODA is designed to be compatible with standard terminal environments (e.g., Ubuntu Terminal) assuming the following conditions are met:
- **User Home**: The system relies on absolute paths rooted in `/home/palantir/`.
- **Dynamic Pathing**: Core scripts (e.g., `database.py`, `handoff.py`, `lifecycle_manager.py`) use the **Cross-Environment Compatibility Pattern**. They resolve the `.agent/` persistence location dynamically using the `HOME` environment variable, ensuring consistency between the IDE and standard terminals.
- **Python Environment**: The `/home/palantir/.venv` must contain the mandatory dependencies (`mcp`, `aiosqlite`, `sqlalchemy`, `instructor`, `prometheus_client`).
- **Integration**: Because there are no relative paths used for core persistence, the ODA can be safely managed via CLI as long as the directory structure remains at `/home/palantir/`.
