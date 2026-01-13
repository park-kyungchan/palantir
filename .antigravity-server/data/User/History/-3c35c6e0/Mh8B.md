# MCP Server Directory and Configuration

This document lists the recommended Model Context Protocol (MCP) servers for the Orion ODA environment, providing their npm/npx execution patterns and typical configurations.

## 1. Search and Retrieval

### Tavily MCP (`tavily-mcp` or `npx -y @tavily/mcp`)
- **Purpose**: High-performance AI-optimized web search.
- **Tools**: `search`, `research`, `extract`.
- **Requirements**: `TAVILY_API_KEY` environment variable.
- **Config Pattern**:
  ```json
  "tavily": {
    "command": "npx",
    "args": ["-y", "@tavily/mcp"],
    "env": {
      "TAVILY_API_KEY": "YOUR_API_KEY"
    }
  }
  ```

### Context7 (`@upstash/context7-mcp` or `npx -y @upstash/context7-mcp`)
- **Purpose**: Enhances context with up-to-date documentation and library-specific code examples.
- **Tools**: Resolving library IDs, querying documentation.
- **Config Pattern**:
  ```json
  "context7": {
    "command": "npx",
    "args": ["-y", "@upstash/context7-mcp"]
  }
  ```

---

## 2. Reasoning and Logic

### Sequential Thinking (`@modelcontextprotocol/server-sequential-thinking`)
- **Purpose**: Provides a structured, step-by-step reasoning tool for complex problem-solving.
- **Tools**: `sequential_thinking`.
- **Config Pattern**:
  ```json
  "sequential-thinking": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
  }
  ```

---

## 3. Platform Integrations

### GitHub MCP (`@modelcontextprotocol/server-github`)
- **Purpose**: Direct interaction with GitHub repositories, issues, PRs, and projects.
- **Tools**: `create_issue`, `list_repos`, `get_file_contents`, etc.
- **Requirements**: `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable.
- **Config Pattern**:
  ```json
  "github": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-github"],
    "env": {
      "GITHUB_PERSONAL_ACCESS_TOKEN": "YOUR_TOKEN"
    }
  }
  ```

### Sentry
- **Purpose**: Accessing error logs and performance monitoring data.
- **Requirements**: `SENTRY_AUTH_TOKEN`, `SENTRY_ORG`.
- **Config Pattern**:
  ```json
  "sentry": {
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-sentry"],
    "env": {
      "SENTRY_AUTH_TOKEN": "YOUR_TOKEN",
      "SENTRY_ORG": "YOUR_ORG"
    }
  }
  ```

---

## 4. Jan 05, 2026 Integration Attempt: The "Standard Suit"

A specific effort was made to integrate a 5-tool suite to satisfy both reasoning and platform needs.

### Final Successful Configuration
After troubleshooting path dependencies and limited `sudo` access, the following configuration was successfully implemented using **NVM (Node Version Manager)**:

- **github-mcp-server**: Platform management.
- **tavily**: Web research.
- **context7**: Live documentation context.
- **sequential-thinking**: Complex reasoning.
- **oda-ontology**: Workspace-specific ontology server (at `park-kyungchan/palantir/`).

### Configuration Snippet (NVM / Global NPM)
```json
{
    "mcpServers": {
        "github-mcp-server": {
            "command": "/home/palantir/.nvm/versions/node/v24.12.0/bin/node",
            "args": ["/home/palantir/.nvm/versions/node/v24.12.0/lib/node_modules/@modelcontextprotocol/server-github/dist/index.js"],
            "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "..." }
        },
        "tavily": {
            "command": "/home/palantir/.nvm/versions/node/v24.12.0/bin/node",
            "args": ["/home/palantir/.nvm/versions/node/v24.12.0/lib/node_modules/tavily-mcp/build/index.js"],
            "env": { "TAVILY_API_KEY": "..." }
        },
        "context7": {
            "command": "/home/palantir/.nvm/versions/node/v24.12.0/bin/node",
            "args": ["/home/palantir/.nvm/versions/node/v24.12.0/lib/node_modules/@upstash/context7-mcp/dist/index.js"]
        },
        "sequential-thinking": {
            "command": "/home/palantir/.nvm/versions/node/v24.12.0/bin/node",
            "args": ["/home/palantir/.nvm/versions/node/v24.12.0/lib/node_modules/@modelcontextprotocol/server-sequential-thinking/dist/index.js"]
        },
        "oda-ontology": {
            "command": "/home/palantir/park-kyungchan/palantir/.venv/bin/python",
            "args": ["-m", "scripts.mcp.ontology_server"],
            "cwd": "/home/palantir/park-kyungchan/palantir"
        }
    }
}
```

**Note on `oda-ontology`**: This server requires the Python `mcp` SDK to be installed in the virtual environment. Run `.venv/bin/pip install mcp` if preflight fails with a `ModuleNotFoundError`.

### Critical Insight: NVM for Non-Root Environments
Since `sudo apt-get install nodejs` may be restricted, **NVM** is the recommended method for ensuring a stable Node.js environment.

**Guideline**: If `npx` commands are not found or fail during preflight, install Node via NVM and point the configuration to the absolute binaries within the `.nvm` directory.

## 5. Initialization and Verification

When adding a new server to `mcp_config.json`:
1.  **Add Entry**: Insert the server definition into the `mcpServers` object.
2.  **Run Preflight**: Execute `.venv/bin/python3 scripts/mcp_preflight.py` from the project root.
3.  **Verify Status**: Ensure the server starts correctly and reports its tools without crashing.
4.  **Auto-Disable**: Use the `--auto-disable-failed` flag to prevent broken servers from blocking the agent startup.
