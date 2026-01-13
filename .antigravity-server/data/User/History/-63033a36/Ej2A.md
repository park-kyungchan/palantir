The Orion V3 workspace uses a standardized initialization procedure called the `/00_start` workflow. This workflow ensures environment health, resets context, resolves path discrepancies resulting from workspace migration, and prepares the Ontology-Driven Architecture (ODA) for operation.

## Workflow: /00_start

### 1. Environment Health Check (MCP)
- **Goal**: Ensure all Agent Tools (MCP servers) are functional.
- **Action**: Run the MCP Preflight script.
- **Command**:
  ```bash
  # Best practice: use the project-local virtual environment
  .venv/bin/python3 scripts/mcp_preflight.py --auto-disable-failed
  ```

### 2. Ontology & Database Initialization
- **Goal**: Ensure the SQLite database is ready and the schema is valid.
- **Action**: Run the database initialization check.
- **Command**:
  ```bash
  .venv/bin/python3 -c "import asyncio; from scripts.ontology.storage.database import initialize_database; asyncio.run(initialize_database())"
  ```

### 3. Active Memory Recall (Context Injection)
- **Goal**: Load relevant Long-Term Memory (LTM) into the System Context.
- **Action**: Scan for recent topics.
- **Command**:
  ```bash
  .venv/bin/python3 scripts/memory/recall.py "Orion Architecture" --limit 3
  ```

### 4. Status Reporting
- **Goal**: Confirm architectural readiness.
- **Expected Output**:
  > "Orion V3 Workspace Initialized. MCP Tools: [Status], DB: [Status], Memory: [Injected]."

## Active Workspace Context
As of January 2026, the primary working directory is consolidated and isolated from the root `/home/palantir/` into a user-specific path:
- **Path**: `/home/palantir/park-kyungchan/palantir/`
- **Scope**: All ODA operations (scripts, coding, governance, tests) are contained within this directory.

## Common Pitfalls and Troubleshooting

### 1. JSONDecodeError in MCP Preflight
- **Symptom**: `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)` when running `scripts/mcp_preflight.py`.
- **Cause**: The `mcp_config.json` file (default at `/home/palantir/.gemini/antigravity/mcp_config.json`) is empty (0 bytes), which is not valid JSON.
- **Fix**: Initialize the file with a valid minimal JSON object (empty servers):
  ```bash
  echo '{"mcpServers": {}}' > /home/palantir/.gemini/antigravity/mcp_config.json
  ```

### 2. Path Mismatch in GEMINI.md
- **Symptom**: Brain operations fail to find knowledge bases or workflows.
- **Cause**: `.gemini/GEMINI.md` or `coding/SYSTEM_DIRECTIVE.md` references the old `/home/palantir/orion-orchestrator-v2/` path.
- **Fix**: Perform a global string replacement of the base path:
  ```bash
  sed -i 's|/home/palantir/orion-orchestrator-v2/|/home/palantir/park-kyungchan/palantir/|g' /home/palantir/.gemini/GEMINI.md
  ```
- **Caution**: Verify that subdirectories match (e.g., if a middle directory like `palantir-fde-learning/` was dropped during consolidation).

### 3. Externally Managed Python Environment (PEP 668)
- **Symptom**: `error: externally-managed-environment` when running `pip install`.
- **Cause**: Modern Linux distributions prevent system-wide `pip` installs to protect the OS.
- **Fix**: Initialize and use a local virtual environment:
  ```bash
  python3 -m venv .venv
  .venv/bin/pip install pydantic aiosqlite sqlalchemy -q
  ```

### 4. Hardcoded Paths in Scripts and Documents
- **Symptom**: `sqlite3.OperationalError: unable to open database file` or missing files/workflows despite them being present.
- **Cause**: Many scripts and markdown files may have hardcoded legacy paths (e.g., `/home/palantir/orion-orchestrator-v2/`).
- **Fix**: Perform a **Deep Workspace Patch** using `sed` to update all references to the new paths:
  ```bash
  # Patch all Python scripts
  find scripts/ -name "*.py" -exec grep -l "/home/palantir/orion-orchestrator-v2" {} \; | xargs -I {} sed -i 's|/home/palantir/orion-orchestrator-v2|/home/palantir/park-kyungchan/palantir|g' {}

  # Patch all Markdown documentation/workflows
  find . -name "*.md" -exec grep -l "/home/palantir/orion-orchestrator-v2" {} \; | xargs -I {} sed -i 's|/home/palantir/orion-orchestrator-v2|/home/palantir/park-kyungchan/palantir|g' {}
  ```

### 5. Circular Import during Initialization
- **Symptom**: `cannot import name 'InsightRepository' from partially initialized module 'scripts.ontology.storage'`.
- **Cause**: Interdependencies between ontology components when importing `initialize_database`.
- **Status**: Occurs if `InsightRepository` or similar sub-modules (like `ActionRepository`) are imported before the storage initialization is complete.
- **Remediation**: Ensure `initialize_database` is called from a clean entry point that does not prematurely trigger secondary repository imports.
