# Orion ODA System Setup and Tooling

This document centralizes the procedures for initializing the Orion V3 workspace and managing its tool ecosystem, specifically the Model Context Protocol (MCP) servers.

## 1. Initialization Workflow (/00_start)

The `/00_start` workflow ensures environment health, resets context, and resolves path discrepancies resulting from workspace migration.

### Phase 1: Environment Health Check (MCP)
- **Goal**: Ensure all Agent Tools (MCP servers) are functional.
- **Command**:
  ```bash
  .venv/bin/python3 scripts/mcp_preflight.py --auto-disable-failed
  ```

### Phase 2: Ontology & Database Initialization
- **Goal**: Ensure the SQLite database is ready and the schema is valid.
- **Command**:
  ```bash
  .venv/bin/python3 -c "import asyncio; from scripts.ontology.storage.database import initialize_database; asyncio.run(initialize_database())"
  ```

### Phase 3: Active Memory Recall (Context Injection)
- **Goal**: Load relevant Long-Term Memory (LTM) into the System Context.
- **Command**:
  ```bash
  .venv/bin/python3 scripts/memory/recall.py "Orion Architecture" --limit 3
  ```

---

## 2. MCP Management Tooling

The Orion ODA includes specialized scripts to maintain consistency across agent interfaces and prevent IDE retry loops.

### MCP Preflight Check (`scripts/mcp_preflight.py`)
- **Startup Probing**: Checks if servers crash early (e.g., within 1.5s).
- **Auto-Disable**: Flags failing servers in `mcp_config.json` to prevent continuous restart attempts.
- **Validation**: Verifies absolute paths and command availability (supporting Windows and Linux).

### MCP Manager (`scripts/mcp_manager.py`)
- **Registry System**: Maintains a canonical registry in `.agent/mcp/registry.json`.
- **Cross-Agent Sync**: Pushes configurations to `mcp_config.json` (Gemini) and `.claude.json` (Claude).
- **Native GitHub Support**: Installs the `github-mcp-server` as a native binary, bypassing Docker requirements.

---

## 3. Common Pitfalls and Troubleshooting

### 1. JSONDecodeError in MCP Preflight
- **Cause**: `mcp_config.json` is empty (0 bytes).
- **Fix**: Initialize with at least an empty object: `echo '{"mcpServers": {}}' > /home/palantir/.gemini/antigravity/mcp_config.json`.

### 2. Externally Managed Python Environment (PEP 668)
- **Symptom**: `error: externally-managed-environment` during `pip install`.
- **Fix**: Use a project-local virtual environment:
  ```bash
  python3 -m venv .venv
  .venv/bin/pip install pydantic aiosqlite sqlalchemy -q
  ```

### 3. Deep Workspace Path Patching
- **Symptom**: `sqlite3.OperationalError` due to hardcoded legacy paths (`/home/palantir/orion-orchestrator-v2/`).
- **Fix**: Bulk update all references:
  ```bash
  # Scripts
  find scripts/ -name "*.py" -exec grep -l "/home/palantir/orion-orchestrator-v2" {} \; | xargs -I {} sed -i 's|/home/palantir/orion-orchestrator-v2|/home/palantir/park-kyungchan/palantir/|g' {}
  
  # Documentation
  find . -name "*.md" -exec grep -l "/home/palantir/orion-orchestrator-v2" {} \; | xargs -I {} sed -i 's|/home/palantir/orion-orchestrator-v2|/home/palantir/park-kyungchan/palantir/|g' {}
  ```

### 4. Circular Imports during Initialization
- **Cause**: Component interdependencies when importing `initialize_database`.
- **Remediation**: Ensure a clean entry point that doesn't trigger secondary repository imports before storage is ready.

### 5. Hardcoded Absolute Node/Binary Paths in MCP Config
- **Symptom**: `mcp_preflight.py` reports `command not found: /path/to/specific/node`.
- **Cause**: Copying configurations from other environments that use NVM or specific binary locations which do not exist in the current workspace.
- **Fix**: Use environment-agnostic commands like `npx` or ensure the binary is in the `PATH`.

### 6. Restricted Sudo Access for System Packages
- **Symptom**: `sudo apt-get install nodejs` prompts for a password that is unknown.
- **Cause**: Standard security restrictions in the development environment.
- **Fix**: Install dependencies in the user's home directory. For Node.js, use **NVM**:
  ```bash
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
  # Load NVM and install Node
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
  nvm install --lts
  ```
