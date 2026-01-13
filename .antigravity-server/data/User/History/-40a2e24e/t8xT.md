# ODA Governance: Global Git Sync Pattern

## 1. Context
In complex Ontology-Driven Architectures (ODA), the workspace often spans multiple git repositories (e.g., project-specific engines, shared libraries, and root environment configurations).

## 2. Problem Statement
Running broad commands like `git push` or `git add .` from a root directory (e.g., `/home/palantir`) risks:
1.  **Committing Sensitive Data**: Linux dotfiles (`.bash_history`, `.ssh`), shell configurations (`.bashrc`), and IDE internal states (`.gemini`, `.claude`).
2.  **Redundant Tracking**: Committing nested repositories (git-within-git) which should be managed independently.
3.  **Governance Decay**: Losing traceability of which repository owns which logic.

## 3. The Global Sync Pattern
The recommended ODA pattern for workspace-wide synchronization involves a **Repository-Specific Targeted Strategy**.

### 3.1 Repository Discovery
Identify all active git roots within the environment:
```bash
find /home/palantir -name ".git" -type d -prune
```

### 3.2 Targeted Interaction Logic
Instead of a root-level commit, iterate through identified repositories and apply context-aware actions:

1.  **Project Repositories** (`hwpx/`, `palantir/`): 
    - Full synchronization (Add, Commit, Push).
    - These represent the "Production" output of the architecture.
2.  **System/Config Repositories** (Root `/home/palantir`):
    - Sensitive scanning required.
    - Avoid bulk adding unless strictly necessary for environment-as-code.
    - **Strategy**: Skip or manually whitelist critical config files only.
3.  **Library Repositories**:
    - Manage via tags or dedicated releases to preserve versioning integrity.

### 3.3 Implementation Example
```python
repositories = ["/home/palantir/hwpx", "/home/palantir/park-kyungchan/palantir"]

for repo in repositories:
    # 1. Inspect status
    # 2. Add specific changes (avoiding bulk if possible)
    # 3. Commit with descriptive semantic messages
    # 4. Push to remote
```

## 4. Verification
- Use `git status` in each sub-repo to confirm transparency.
- Ensure the root repository does not contain untracked sensitive markers (`.env`, `*.log`).

## 5. Benefits
- **Isolation**: Changes in the HWPX engine do not accidentally leak into the general ODA library.
- **Traceability**: GitHub commit histories remain clean and focused on specific domains.
- **Security**: Reduces risk of credential or history leakage.
