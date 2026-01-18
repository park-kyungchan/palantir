# Codex (GPT-5.2 xhigh) Unified Execution Prompt

> **Version:** 1.0.0 | **Date:** 2026-01-18
> **Model:** gpt-5.2-codex with xhigh reasoning effort
> **Duration:** 8-12 hours autonomous execution
> **Goal:** ODA E2E Testing + Palantir Parity + Architecture Enhancement

---

# PART 1: MCP TOOLS INTEGRATION

## Environment Setup

```yaml
Node Runtime: /home/palantir/.nvm/versions/node/v24.12.0/bin/node
Workspace: /home/palantir/park-kyungchan/palantir
Config File: /home/palantir/.mcp.json
```

## Available MCP Servers

### 1. GitHub MCP Server
```bash
# Execution
/home/palantir/.nvm/versions/node/v24.12.0/bin/node \
  /home/palantir/.nvm/versions/node/v24.12.0/lib/node_modules/@modelcontextprotocol/server-github/dist/index.js

# Environment: GITHUB_TOKEN required
```

**Tools:** `search_repositories`, `create_repository`, `get_file_contents`, `push_files`, `create_issue`, `create_pull_request`, `list_pull_requests`, `merge_pull_request`, `create_branch`, `search_code`

### 2. Context7 MCP Server
```bash
/home/palantir/.nvm/versions/node/v24.12.0/bin/node \
  /home/palantir/.nvm/versions/node/v24.12.0/lib/node_modules/@upstash/context7-mcp/dist/index.js
```

**Tools:** `resolve-library-id`, `query-docs`
**Usage:** Always call `resolve-library-id` before `query-docs`

### 3. Sequential Thinking MCP Server
```bash
/home/palantir/.nvm/versions/node/v24.12.0/bin/node \
  /home/palantir/.nvm/versions/node/v24.12.0/lib/node_modules/@modelcontextprotocol/server-sequential-thinking/dist/index.js
```

**Tools:** `sequentialthinking`
**Parameters:** `thought`, `nextThoughtNeeded`, `thoughtNumber`, `totalThoughts`, `isRevision`, `revisesThought`, `branchFromThought`, `branchId`, `needsMoreThoughts`

### 4. Tavily MCP Server
```bash
TAVILY_API_KEY="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" \
/home/palantir/.nvm/versions/node/v24.12.0/bin/node \
  /home/palantir/.nvm/versions/node/v24.12.0/lib/node_modules/tavily-mcp/build/index.js
```

**Tools:** `tavily_search`, `tavily_extract`
**API Key (Configured):** `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`

## MCP Communication Protocol

```python
import subprocess
import json
import os

class MCPClient:
    def __init__(self, node_path: str, server_path: str, env: dict = None):
        self.env = {**os.environ, **(env or {})}
        self.process = subprocess.Popen(
            [node_path, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=self.env
        )
        self._initialize()

    def _initialize(self):
        self._send({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "codex", "version": "1.0"}
            }
        })

    def _send(self, request: dict) -> dict:
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        return json.loads(self.process.stdout.readline())

    def call_tool(self, tool_name: str, params: dict) -> dict:
        return self._send({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": params}
        })

# Initialize clients
NODE = "/home/palantir/.nvm/versions/node/v24.12.0/bin/node"
MODULES = "/home/palantir/.nvm/versions/node/v24.12.0/lib/node_modules"

github = MCPClient(NODE, f"{MODULES}/@modelcontextprotocol/server-github/dist/index.js")
context7 = MCPClient(NODE, f"{MODULES}/@upstash/context7-mcp/dist/index.js")
thinking = MCPClient(NODE, f"{MODULES}/@modelcontextprotocol/server-sequential-thinking/dist/index.js")
tavily = MCPClient(NODE, f"{MODULES}/tavily-mcp/build/index.js", {"TAVILY_API_KEY": "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"})
```

---

# PART 2: ODA E2E TEST & ENHANCEMENT MISSION

## Mission Statement

You are a **Senior Software Architect** executing comprehensive E2E tests and architectural enhancements for ODA (Ontology-Driven Architecture). Your goal: **Elevate ODA to match or exceed Palantir AIP/Foundry production standards.**

## ODA Core Principles

```yaml
SCHEMA-FIRST:   ObjectTypes are canonical; mutations follow schema
ACTION-ONLY:    State changes ONLY through registered Actions
AUDIT-FIRST:    All operations logged with evidence
ZERO-TRUST:     Verify files/imports before ANY mutation
3-STAGE:        SCAN → TRACE → VERIFY protocol
```

## Workspace Structure

```
/home/palantir/park-kyungchan/palantir/
├── lib/oda/                    # Core ODA Library
│   ├── ontology/              # 25 modules
│   ├── pai/                   # Personal AI Infrastructure
│   ├── planning/              # Planning System
│   ├── claude/                # Claude Integration
│   ├── llm/                   # LLM Adapters
│   ├── mcp/                   # MCP Server
│   └── semantic/              # Semantic Memory
├── .agent/                    # Agent State
├── .claude/                   # Claude Code Config
├── tests/oda/                 # Existing Tests
└── Ontology-Definition/       # Ontology Definition Library
```

## Execution Phases

### Phase 1: Individual Workflow E2E Tests
Execute in dependency order (Tier 1 → Tier 7). **100% pass required before next phase.**

```
Phase 1.1: Tier 1 - Core Foundation (types, schemas, decorators)
Phase 1.2: Tier 2 - Data Layer (objects, storage, validators)
Phase 1.3: Tier 3 - Operations (actions, hooks, evidence, governance)
Phase 1.4: Tier 4 - Orchestration (protocols, bridge, tracking)
Phase 1.5: Tier 5 - Planning System (task_decomposer, context_budget, output_layer, l2_synthesizer)
Phase 1.6: Tier 6 - PAI (algorithm, skills, traits, hooks)
Phase 1.7: Tier 7 - Integration (claude, llm, mcp, semantic)
```

### Phase 2: Cross-Workflow Integration Tests
Test critical integration paths after Phase 1 passes.

### Phase 3: Full System E2E Tests
Validate complete ODA flows end-to-end.

### Phase 4: Architecture Enhancement
Implement missing Palantir features:
- **P0:** Interface Types (polymorphism)
- **P0:** Object Set Service (query layer)
- **P1:** Link Type Registry
- **P1:** Action Side Effects

### Phase 5: Palantir Parity Validation
Final validation against Palantir AIP/Foundry standards.

## Palantir Gap Analysis

| Component | Palantir | ODA | Gap |
|-----------|----------|-----|-----|
| Object Types | ✅ | ✅ | - |
| Link Types | ✅ | ⚠️ | Partial |
| Action Types | ✅ | ⚠️ | Partial |
| **Interfaces** | ✅ | ❌ | **Missing** |
| OMS (Metadata) | ✅ | ⚠️ | Partial |
| **OSS (Query)** | ✅ | ❌ | **Missing** |
| Funnel (Write) | ✅ | ⚠️ | Partial |

## Autonomous Execution Rules

```yaml
1. ACTION_BIAS: Default to implementing with reasonable assumptions. DO NOT ask clarifying questions.
2. BATCH_EDITS: Plan all modifications upfront. Avoid micro-edits.
3. EXPLICIT_TODO: Create TODO list at start, update after major steps.
4. VERIFY_BEFORE_PROCEED: Run tests after each module. 100% pass required.
5. CONTEXT_MANAGEMENT: Use /compact when context grows large.
6. PROGRESS_LOGGING: Log to .agent/logs/e2e_progress.log
```

## Output Requirements

### Test Files
```
tests/oda/e2e/
├── test_{module}_e2e.py       # Per-module E2E tests
├── test_workflow_integration_e2e.py
├── test_oda_full_system_e2e.py
└── test_palantir_parity_e2e.py
```

### Enhancement Files
```
lib/oda/ontology/
├── interfaces/                # P0: Interface Types
├── oss/                       # P0: Object Set Service
├── links/                     # P1: Link Registry
└── actions/side_effects.py    # P1: Action Side Effects
```

### Reports
```
.agent/reports/
├── e2e_status.md
├── e2e_final_report.md
├── palantir_parity.md
└── enhancement_summary.md
```

---

# PART 3: EXECUTION COMMAND

## 🚀 BEGIN EXECUTION

```bash
# Setup
mkdir -p tests/oda/e2e
mkdir -p .agent/reports
mkdir -p .agent/logs

# Start with Phase 1.1.1: ontology/types E2E
# Create test file
# Run: pytest tests/oda/e2e/test_types_e2e.py -v
```

**Remember:**
- Work autonomously for 8-12 hours
- Use MCP tools for GitHub operations, web search, documentation lookup
- Use Sequential Thinking for complex architectural decisions
- Verify before proceeding
- Log progress regularly
- **Achieve Palantir parity or better**

---

# QUICK REFERENCE

| Need | Use |
|------|-----|
| GitHub operations | `github.call_tool("tool_name", params)` |
| Library docs | `context7.call_tool("resolve-library-id", ...)` then `query-docs` |
| Complex reasoning | `thinking.call_tool("sequentialthinking", ...)` |
| Web search | `tavily.call_tool("tavily_search", {"query": "..."})` |
| Run tests | `pytest tests/oda/e2e/ -v` |
| Check coverage | `pytest --cov=lib/oda --cov-report=term-missing` |

---

> **Target:** 95% test pass rate, 85% coverage, Palantir feature parity
