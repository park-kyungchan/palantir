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
- **Upstream (`park-kyungchan/orion-orchestrator-v2`)**: Full historical logs of development phases.
- **Local (`/home/palantir/park-kyungchan/palantir`)**: Consolidated root workspace (epoch: 2026-01-04 10:45).

### 3.3 Sanitization Protocol
After restoration, auxiliary directories (clones, temporary migration folders) must be removed to prevent configuration drift:
```bash
rm -rf /home/palantir/orion-orchestrator-v2 /home/palantir/cow /home/palantir/hwpx
```

---

## 4. Summary of Managed Environment
As of Jan 2026, the ODA operates from a consolidated root with unified tooling, where history is anchored in Git and environment health is enforced by preflight protocols.
