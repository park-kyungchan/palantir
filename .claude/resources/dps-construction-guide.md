# DPS Construction Guide

> Lead constructs per-Agent DPS when spawning subagents. DPS = task-unique information ONLY. Agent body handles output format, scope rules, error handling.

## Per-Agent DPS Structure

Each agent type has a minimal DPS template. Lead constructs DPS to maximize agent working memory.

**Read-only agents** (analyst, researcher):
```
OBJECTIVE: {1 sentence — what to analyze/research}
READ: {comma-separated full file paths}
OUTPUT: {full output file path}
```

**Synthesis agent** (coordinator):
```
OBJECTIVE: Synthesize P{N} {dimension list} (N-to-1)
INPUT: [{path1}, {path2}, ...]
OUTPUT: {full output file path}
```

**Edit agents** (implementer, infra-implementer):
```
OBJECTIVE: {what to implement/modify}
PLAN:
1. {file_path}: {specific change}
2. {file_path}: {specific change}
OUTPUT: {full output file path}
[CRITERIA: {only for complex multi-section reworks}]
```

**Terminal agent** (delivery-agent):
```
OBJECTIVE: Deliver pipeline results — {scope summary}
CRITERIA: {what to commit, what to exclude}
```

### Token Targets
| Agent | Max DPS | Rationale |
|-------|---------|-----------|
| coordinator | 80 | Reads INPUT files for context |
| analyst | 100 | Reads files in READ |
| researcher | 100 | Uses MCP for discovery |
| delivery-agent | 100 | Reads PT for context |
| implementer | 150 | PLAN needs step detail |
| infra-implementer | 200 | PLAN may need old→new values |

## D11 Priority Rule

DPS construction follows **D11 priority**: cognitive focus > token efficiency.

- INCLUDE what helps the agent focus on the RIGHT task
- EXCLUDE what would distract or cause scope creep

## What Goes in DPS (task-unique only)
| Data | When | Example |
|------|------|---------|
| File paths to read | Always for pipeline skills | `READ: {WORK_DIR}/coordinator/p2-synthesis.md` |
| Specific change instructions | Edit agents | `PLAN: 1. file.md: change X to Y` |
| Scope restriction | Multi-agent splits | `Scope: src/api/ only` |

## What Does NOT Go in DPS (agent body handles)
| Data | Why |
|------|-----|
| Output format (L1/L2/L3) | Defined in agent body |
| Read-before-edit rules | Defined in agent body |
| Scope boundaries | Defined in agent body |
| Error handling | Defined in agent body |
| WARNING blocks | Agent body has equivalent rules |
| Full pipeline state | Agent gets OBJECTIVE only |

## Delivery Instruction
Always include OUTPUT path in DPS:
```
OUTPUT: {WORK_DIR}/{agent_name}/{phase}-{skill}.md
```
Agent writes L1 micro-signal as first line, L2 detail below. Lead reads micro-signal from completion notification.

## DPS Principles (Mandatory)

- **Self-Containment**: DPS must be self-contained for the task; spawned instance has zero parent context access.
- **Output Cap**: 30K characters. Large results → write file + send path.
- **File Ownership**: Parallel instances MUST NOT edit the same file.
- **Input via File Reference**: Pass file paths via `$ARGUMENTS`, NOT content. Avoids data relay.
