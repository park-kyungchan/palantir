# Version Recovery and Restoration

This document outlines the protocols and commands for restoring the Orion ODA workspace to specific historical states, particularly when dealing with distributed repositories and migration history.

## Time-Based Git Recovery

To revert a repository to its state at a specific date and time, use the `git rev-list` command to find the nearest commit prefixing that time.

### Command Pattern

```bash
# Find the latest commit before a specific time
git rev-list -n 1 --before="YYYY-MM-DD HH:MM" HEAD

# Revert the current branch to that state (Hard Reset - WARNING: Discards changes)
git reset --hard $(git rev-list -n 1 --before="YYYY-MM-DD HH:MM" HEAD)

# Alternatively, checkout to a new branch to preserve current work
git checkout -b restore-point $(git rev-list -n 1 --before="YYYY-MM-DD HH:MM" HEAD)
```

## Repository History Distinction

In the Orion ODA project, the history may be split across different repository instances due to workspace reorganization.

### 1. Local Workspace (`/home/palantir/park-kyungchan/palantir`)
*   **Context**: Created during the consolidation of the ODA workspace to the root directory.
*   **Epoch**: History typically begins around **2026-01-04 10:45:41** (Initial commit `81c9672`).
*   **Limitation**: Does not contain pre-consolidation history.

### 2. Upstream Repository (`park-kyungchan/orion-orchestrator-v2`)
*   **URL**: `https://github.com/park-kyungchan/orion-orchestrator-v2`
*   **Context**: The primary source containing full historical logs of the ODA development, including Phase 1-6 implementation and various fixes.
*   **Extended History**: Contains commits dating back to December 2025 (e.g., `2915767` at 2026-01-04 10:03).

## Recovery Workflow

If a specific historical state is required (e.g., exactly 2026-01-04 10:00) and it is not found in the local workspace:

1.  **Clone the full history repository**:
    ```bash
    git clone https://github.com/park-kyungchan/orion-orchestrator-v2 temp_recovery
    ```
2.  **Verify commits around the target window**:
    *   `c51f45c` (2026-01-04 10:25:54): fix(mcp): handle NoneType attribute error
    *   `2915767` (2026-01-04 10:03:43): Merge PR #4 (fix windows mcp crashes)
    *   `e4eb473` (2026-01-04 09:54:33): fix(mcp): Windows compatibility for MCP tools (**Target for Jan 4, 10:00 AM**)

3.  **Perform Full Workspace Replacement** (if discarding current local state):
    ```bash
    # 1. Clear current workspace (from parent directory)
    # Note: Ensure the target directory exists after deletion if the rm command is aggressive
    rm -rf /home/palantir/park-kyungchan/palantir/* /home/palantir/park-kyungchan/palantir/.[!.]*
    mkdir -p /home/palantir/park-kyungchan/palantir

    # 2. Move contents from clone to workspace
    shopt -s dotglob
    mv temp_recovery/* /home/palantir/park-kyungchan/palantir/
    rmdir temp_recovery

    # 3. Checkout specific commit if needed
    cd /home/palantir/park-kyungchan/palantir/
    # For Jan 4, 10:00 AM state:
    git checkout e4eb473
    ```

## History Restoration Status
As of **2026-01-05**, the workspace has been successfully restored to the **2026-01-04 09:54:33** state (`e4eb473`) using the upstream `orion-orchestrator-v2` repository. This commit was identified as the closest point satisfying the "before 2026-01-04 10:00" requirement.

The active workspace is now located at: `/home/palantir/park-kyungchan/palantir/`.

## Environment Cleanup and Maintenance

After a major version restoration or repository migration, it is critical to sanitize the environment to prevent configuration drift and accidental usage of legacy artifacts.

### Cleanup Protocol
When several repository iterations or temporary folders have been created (e.g., `orion-orchestrator-v2`, `cow`, `hwpx` after migration to a consolidated root), use the following steps:

1.  **Identify the Core Workspace**: Confirm the path of the active, restored project (e.g., `/home/palantir/park-kyungchan/`).
2.  **Remove Auxiliary Directories**: Delete obsolete project clones and data folders.
    ```bash
    # Example: Delete everything except the core user directory
    # Note: Preserve hidden system files (.bashrc, .profile) if necessary, 
    # but remove agent-generated metadata like .codex or .landscape if they are legacy.
    find /home/palantir/ -maxdepth 1 ! -name 'park-kyungchan' ! -name '.' ! -name '..' -exec rm -rf {} +
    ```
3.  **Preserve System Continuity**: Ensure directories like `.gemini/` (which contains the code tracker and knowledge base) are managed based on whether they should survive the cleanup.

## Summary of History Sync
The transition to a consolidated root directory on 2026-01-04 created a "clean slate" in the primary repo, but historical continuity is maintained through the `orion-orchestrator-v2` upstream repository.
