# Pre-Design Feasibility — Detailed Methodology

> On-demand reference. Contains DPS specifics, scoring rubric, and alternative patterns.

## DPS for Researchers

**TRIVIAL** (Lead-direct):
```
Lead check sequence (cc-reference cache at memory/cc-reference/):
1. Read native-fields.md     → maps to known field?
2. Read hook-events.md       → involves hook event?
3. Read context-loading.md   → depends on context loading?
4. Verdict from cache alone
```

**STANDARD** (single researcher):
- **Context**: Technical requirements list with CC capability category per item. cc-reference cache path: `memory/cc-reference/`.
- **Task**: "Verify CC native support per requirement. Read cc-reference first. If stale/ambiguous, use claude-code-guide. Per requirement: verdict, CC feature, limitations, alternative if infeasible, source."
- **Constraints**: Research-only. Priority: cc-reference → claude-code-guide → WebSearch.
- **Delivery**: Lead reads directly (P0-P1)

**COMPLEX** (two researchers):
| Researcher | Scope | maxTurns |
|------------|-------|----------|
| A | Core CC (tools, skills, agents, context) | 15 |
| B | MCP/plugin, hooks, external integrations | 20 |

## Scoring Rubric

| Criterion | Weight | Range | Description |
|-----------|--------|-------|-------------|
| CC Native Support | 40% | 0-10 | Direct tool/feature exists? |
| Implementation Complexity | 25% | 0-10 | Steps/workarounds needed? |
| Reliability | 20% | 0-10 | Works consistently? |
| Maintenance Burden | 15% | 0-10 | Will break on CC updates? |

**Thresholds**: feasible ≥7.0, partial 4.0-6.9, infeasible <4.0

## Common Alternative Patterns

| Infeasible Requirement | CC Workaround | Effort |
|------------------------|---------------|--------|
| Real-time file watching | PostToolUse hook on edit events + /tmp log | Low |
| Cross-agent shared state | /tmp files or Task metadata (Read-Merge-Write) | Low |
| Persistent database | JSON files + Bash jq | Medium |
| GUI/visual output | HTML generation + Bash open | Medium |
| External API calls | Bash curl with error handling | Medium |
| Background daemon | Hook-based event system | High |
| Binary file manipulation | Bash CLI tools (imagemagick, ffmpeg) | High |
| Interactive prompts | AskUserQuestion at gate checkpoints only | Low |

## MCP Feasibility Checks

| Check | Method | Failure Action |
|-------|--------|----------------|
| MCP configured | Read settings.json → mcpServers | Mark MCP-dependent as infeasible |
| Tool available | Verify tool in MCP tool list | Suggest CC-native alternative |
| Permissions | Check allowedTools | Add permission as alternative |
| Health | Not checkable at design time | Flag as runtime risk |

## Terminal FAIL AskUserQuestion
After 3 iterations without resolution:
```
"Feasibility failed after 3 iterations.
Infeasible requirements: [list with attempted alternatives]
Options:
1. Proceed with limitations (infeasible removed)
2. Modify requirements (return to brainstorm)
3. Abandon task"
```
