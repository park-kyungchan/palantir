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

## 4. Initialization and Verification

When adding a new server to `mcp_config.json`:
1.  **Add Entry**: Insert the server definition into the `mcpServers` object.
2.  **Run Preflight**: Execute `.venv/bin/python3 scripts/mcp_preflight.py` from the project root.
3.  **Verify Status**: Ensure the server starts correctly and reports its tools without crashing.
