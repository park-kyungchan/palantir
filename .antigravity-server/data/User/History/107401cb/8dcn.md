# Orion ODA: Setup, Maintenance, and Recovery

This document centralizes environment management, tooling, and restoration protocols for the Orion ODA workspace.

---

## 1. Environment Initialization

The `/00_start` workflow ensures environment health and injects required context for the session.

### 1.1 Health Checks & Tooling
The environment depends on Model Context Protocol (MCP) servers. Maintenance includes:
- **MCP Preflight (`scripts/mcp_preflight.py`)**: Checks for startup crashes and auto-disables failing servers in `mcp_config.json`.
- **MCP Manager (`scripts/mcp_manager.py`)**: Synchronizes configurations between Gemini (`mcp_config.json`) and Claude (`.claude.json`).

### 1.2 Path Patching
During workspace migrations (e.g., from `/home/palantir/orion-orchestrator-v2/` to `/home/palantir/park-kyungchan/palantir/`), absolute paths must be patched:
```bash
find scripts/ -name "*.py" -exec sed -i 's|/old/path|/new/path|g' {} +
```

---

## 2. Troubleshooting & Common Pitfalls

### 2.1 Environment Context & Misalignment
In multi-WSL or multi-machine setups, it is common to find tools "missing" if the session is anchored to the wrong host.
- **Hostname Awareness**: Check the current host using `hostname`. (Example: `kc-palantir` is the primary WSL2 instance for document reconstruction).
- **Missing Global Tools**: If a tool like `codex` or `npm` is reported as "not found" despite being previously used, verify:
    - You are in the correct WSL distribution (`wsl.exe -l -v`).
    - You are on the correct physical machine (if using remote SSH or multiple PCs).
- **MOTD (Message of the Day)**: Ubuntu/WSL displays standard guidance such as `To run a command as administrator (user "root"), use "sudo <command>"`. This is normal system noise and does not indicate an error.

### 2.2 Functional Issues
- **PEP 668 (Externally Managed Environment)**: Use a local `.venv` for library isolation.
- **Node.js/NVM**: Install Node.js via NVM in the home directory to bypass sudo restrictions.
- **Git Identity**: If `git commit` fails with "Author identity unknown", set it locally or globally:
  ```bash
  git config --global user.email "park.kyungchan@example.com"
  git config --global user.name "Park Kyungchan"
  ```
- **GitHub Push Protection (Secrets)**: GitHub blocks pushes containing secrets (PATs, OAuth tokens).
  - Common locations: `.mcp.json`, `.claude/projects/`, `.antigravity/sessions/`.
  - Resolution: Use the GitHub unblock URL provided in the terminal output OR clean history and update `.gitignore`.
- **Git History Cleanup (Secrets Disposal)**: To remove secrets from the entire repository history (required for push protection):
  ```bash
  # 1. Update .gitignore to exclude sensitive paths
  # 2. Add .gitignore, remove cached files
  git rm -r --cached .mcp.json .claude/ .antigravity/ *.jsonl
  # 3. Force-purge secrets from history
  git filter-branch --force --index-filter \
    'git rm -rf --cached --ignore-unmatch .mcp.json .claude/ .antigravity/ *.jsonl' \
    --prune-empty HEAD
  # 4. Force push to master (use with caution)
  git push origin master --force
  # 5. Post-Cleanup Optimization (Reflog & GC)
  rm -rf .git/refs/original/ && git reflog expire --expire=now --all && git gc --prune=now --aggressive
  ```
- **MCP Library**: Ensure `pip install mcp` is present in the Python environment for native ontology servers.

---

## 3. Version Recovery and Restoration

ODA uses time-based recovery to restore stable states across distributed repositories.

### 3.1 Time-Based Git Recovery
```bash
# Find latest commit before target time
git rev-list -n 1 --before="YYYY-MM-DD HH:MM" HEAD
# Hard reset to stable state
git reset --hard $(git rev-list -n 1 --before="YYYY-MM-DD HH:MM" HEAD)
```

### 3.2 Repository Lineage
- **Upstream (`park-kyungchan/palantir`)**: The primary repository containing the consolidated ODA root.
- **Local (`/home/palantir/park-kyungchan/palantir`)**: Consolidated root workspace.

### 3.3 Sanitization Protocol
After consolidation, auxiliary and redundant repositories were purged (Jan 2026 cleanup):
- **Previously Purged (Jan 2026)**: `orion-orchestrator-v2`, `cow`, `reasoning-lab`, `kc-palantir-math`.
- **Re-Evaluated**: `hwpx-automation` - Re-cloned and subjected to Deep Audit (v6.0) for high-fidelity document reconstruction integration.
- Tool: GitHub Web Settings + Git CLI history scrubbing (`filter-branch`).

---

## 4. Summary of Managed Environment
As of Jan 2026, the ODA operates from a consolidated root with unified tooling, where history is anchored in Git and environment health is enforced by preflight protocols.
