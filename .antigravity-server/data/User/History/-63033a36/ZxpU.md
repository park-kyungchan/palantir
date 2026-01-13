# Initialization and Preflight Workflow (/00_start)

The Orion V3 workspace uses a standardized initialization procedure called the `/00_start` workflow. This workflow ensures environment health, resets context, and prepares the Ontology-Driven Architecture (ODA) for operation.

## Workflow: /00_start

### 1. Environment Health Check (MCP)
- **Goal**: Ensure all Agent Tools (MCP servers) are functional.
- **Action**: Run the MCP Preflight script.
- **Command**:
  ```bash
  python3 scripts/mcp_preflight.py --auto-disable-failed
  ```

### 2. Ontology & Database Initialization
- **Goal**: Ensure the SQLite database is ready and the schema is valid.
- **Action**: Run the database initialization check.
- **Command**:
  ```bash
  python3 -c "import asyncio; from scripts.ontology.storage.database import initialize_database; asyncio.run(initialize_database())"
  ```

### 3. Active Memory Recall (Context Injection)
- **Goal**: Load relevant Long-Term Memory (LTM) into the System Context.
- **Action**: Scan for recent topics.
- **Command**:
  ```bash
  python3 scripts/memory/recall.py "Orion Architecture" --limit 3
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
