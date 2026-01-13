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
    *   `e4eb473` (2026-01-04 00:54:33): fix(mcp): Windows compatibility for MCP tools

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
    # Found state: c51f45c (2026-01-04 10:25:54) matches the target window
    git checkout c51f45c
    ```

## History Restoration Status
As of **2026-01-05**, the workspace has been successfully restored to the **2026-01-04 10:25:54** state (`c51f45c`) using the upstream `orion-orchestrator-v2` repository, bridging the gap left during the initial local workspace refactor.

## Summary of History Sync
The transition to a consolidated root directory on 2026-01-04 created a "clean slate" in the primary repo, but historical continuity is maintained through the `orion-orchestrator-v2` upstream repository.
