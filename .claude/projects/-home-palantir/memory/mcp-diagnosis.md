# MCP Server Diagnosis — CC 2.1.45 / WSL2

## Date: 2026-02-18

## Key Finding: "Propagation Failure" → "Wrong Config File"

Previous MEMORY incorrectly recorded: "MCP 전파 안 됨 (tmux)"
Corrected diagnosis chain:
1. First correction: "propagation failure" → "startup failure" (servers not starting)
2. **ROOT CAUSE**: CC reads MCP servers from `.claude.json` (project config), NOT `settings.json`
   - `.claude.json` project mcpServers only had github-mcp-server
   - `settings.json` mcpServers had all 4 but was IGNORED for MCP loading
   - Propagation mechanism itself works correctly

## Fix Applied (2026-02-18)
1. `.claude.json`: Added sequential-thinking, context7, tavily to project mcpServers
2. `.claude.json`: Added "context7" to disabledMcpjsonServers (prevent plugin marketplace conflict)
3. `settings.json`: Removed mcpServers section entirely (was being ignored, caused confusion)
4. `settings.local.json`: Added mcp__tavily__search to permission allow list
5. **Requires CC restart** to take effect (new session needed)

## Evidence

### Test 1: Process-level (ps aux)
| MCP Server | Process Running? | Source |
|---|---|---|
| claude-in-chrome | YES (CC internal binary) | CC built-in |
| github-mcp-server | YES (node via npx) | settings.json mcpServers |
| sequential-thinking | NO | settings.json mcpServers |
| context7 | NO | settings.json mcpServers + plugin marketplace |
| tavily | NO | settings.json mcpServers |

### Test 2: Tool Availability
| MCP Server | Lead has tools? | Teammate has tools? |
|---|---|---|
| claude-in-chrome | YES | YES |
| github-mcp-server | YES | YES (auth error is runtime, not availability) |
| sequential-thinking | NO | NO |
| context7 | NO | NO |
| tavily | NO | NO |

### Test 3: npx Cache Timestamps
| Hash | Package | Created | Creator |
|---|---|---|---|
| 3dfbf5a9eea4a1b3 | mcp-server-github | 14:46 | CC session startup |
| de2bd410102f5eda | sequential-thinking | 14:49 | Manual test (not CC) |
| eea2bd7412d4593b | context7-mcp | 14:50 | Manual test (not CC) |
| 3a4829a0511b3281 | tavily-mcp | 14:50 | Manual test (not CC) |

CC only started github-mcp-server. Never attempted to start the other 3.

### Test 4: Manual Package Verification
All 3 packages install and run correctly via manual `npx -y`:
- `@modelcontextprotocol/server-sequential-thinking` → starts on stdio
- `@upstash/context7-mcp` → starts with --transport stdio
- `tavily-mcp@latest` → starts with --help

## Propagation Mechanism (Verified Working)
- In-process teammate mode: teammates inherit MCP tools from Lead
- If Lead has the tool (server running), teammate gets it
- If Lead doesn't have the tool (server not running), teammate can't get it
- This is NOT a propagation bug — it's expected behavior

## Potential Root Causes (Unverified Hypotheses)

### H1: Plugin Marketplace Conflict
- context7 registered in BOTH settings.json AND `.claude/plugins/.../external_plugins/context7/.mcp.json`
- This does NOT explain sequential-thinking and tavily failures (no plugin duplicates)

### H2: CC MCP Startup Timeout
- npx-based servers may exceed CC's connection timeout on first run
- Counter-evidence: github-mcp-server also uses npx and succeeds

### H3: CC Selective MCP Loading
- CC might have internal criteria for which servers to start
- Possibly based on permission lists, plugin conflicts, or load order

### H4: WSL2 Environment Issue
- Node.js path, npm cache, or process spawning differences in WSL2
- Counter-evidence: github-mcp-server works fine in same environment

### H5: Settings Merge Order
- settings.json + settings.local.json + plugin .mcp.json merge might cause conflicts
- settings.local.json has permission allows for MCP tools but no mcpServers

## Configuration Files

### settings.json mcpServers (4 entries)
```json
"mcpServers": {
    "sequential-thinking": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"] },
    "context7": { "command": "npx", "args": ["-y", "@upstash/context7-mcp"] },
    "tavily": { "command": "npx", "args": ["-y", "tavily-mcp@latest"], "env": { "TAVILY_API_KEY": "..." } },
    "github-mcp-server": { "command": "npx", "args": ["-y", "@modelcontextprotocol/server-github"], "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "..." } }
}
```

### settings.local.json
- Has permission allows for `mcp__sequential-thinking__*`, `mcp__context7__*`
- Does NOT have mcpServers section
- Does NOT have tavily permission

### Plugin Marketplace context7
- Path: `.claude/plugins/.../external_plugins/context7/.mcp.json`
- Content: `{ "context7": { "command": "npx", "args": ["-y", "@upstash/context7-mcp"] } }`
- NOT in enabledPlugins list

## Environment
- CC: 2.1.45
- Node: v24.13.1 (nvm)
- npm: 11.8.0
- npx: 11.8.0
- OS: Linux 6.6.87.2-microsoft-standard-WSL2
- teammateMode: in-process

## Impact on Pipeline Operations
- Teammate research: Use WebSearch/WebFetch builtins (not MCP-dependent)
- Sequential thinking: Not available — use analyst agent with write-based reasoning
- GitHub MCP: Available (fix auth token if needed)
- Chrome automation: Available

## Next Steps
1. Check `/mcp` command output for CC's own MCP status reporting
2. Try removing duplicate context7 from plugin marketplace
3. CC restart with fresh settings and observe MCP startup logs
4. Test with `--verbose` flag or debug logging if available
