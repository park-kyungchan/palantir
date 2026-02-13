# Infrastructure Inventory — Hooks, References, Settings, Config

## 1. Hooks (4 scripts, ~416 lines total)

### H-1: SubagentStart — on-subagent-start.sh

| Property | Value |
|----------|-------|
| Path | `.claude/hooks/on-subagent-start.sh` |
| Lines | 93 |
| Event | SubagentStart |
| Matcher | (empty — matches all) |
| Timeout | 10s |
| Mode | sync |
| Status Message | "Injecting team context to new agent" |

**Purpose:** Context injection for newly spawned agents.

**Behavior:**
1. Parses agent_type, agent_name, team_name from JSON stdin
2. Logs spawn event to `.agent/teams/teammate-lifecycle.log`
3. Updates RTD session registry (maps session_id to agent name)
4. Injects additionalContext via hookSpecificOutput:
   - If team has `global-context.md` → injects GC version (legacy path)
   - If team has no GC → injects PT guidance message
   - If no team → falls back to most recent GC across all teams

**Dependencies:** jq, `.agent/observability/.current-project`, RTD session-registry.json

---

### H-2: PreCompact — on-pre-compact.sh

| Property | Value |
|----------|-------|
| Path | `.claude/hooks/on-pre-compact.sh` |
| Lines | 123 |
| Event | PreCompact |
| Matcher | (empty — matches all) |
| Timeout | 30s |
| Mode | sync |
| Status Message | "Saving orchestration state before compaction" |

**Purpose:** Preserve orchestration state before context loss.

**Behavior:**
1. Logs compact event to `compact-events.log`
2. Saves task list snapshot as JSON to `.agent/teams/pre-compact-tasks-{ts}.json`
3. Scans agent output dirs for missing L1/L2 files — emits WARNING
4. Creates RTD state snapshot (project slug, last DP, active phase) to `snapshots/{ts}-pre-compact.json`
5. If missing agents found: outputs hookSpecificOutput with WARNING message

**Dependencies:** jq, CLAUDE_CODE_TASK_LIST_ID (optional), `.agent/observability/`

---

### H-3: SessionStart(compact) — on-session-compact.sh

| Property | Value |
|----------|-------|
| Path | `.claude/hooks/on-session-compact.sh` |
| Lines | 54 |
| Event | SessionStart |
| Matcher | "compact" |
| Timeout | 15s |
| Mode | sync, once: true |
| Status Message | "Recovery after compaction" |

**Purpose:** RTD-centric auto-compact recovery context injection.

**Behavior:**
1. Logs compact recovery event
2. Attempts RTD-enhanced recovery:
   - Reads `.agent/observability/.current-project` for slug
   - Extracts phase, last DP, recent DPs from rtd-index.md
   - Builds recovery message with RTD context
3. Falls back to generic recovery message if no RTD data
4. Outputs hookSpecificOutput with recovery steps

**Dependencies:** jq (optional — graceful fallback), `.agent/observability/`

---

### H-4: PostToolUse — on-rtd-post-tool.sh

| Property | Value |
|----------|-------|
| Path | `.claude/hooks/on-rtd-post-tool.sh` |
| Lines | 146 |
| Event | PostToolUse |
| Matcher | (empty — matches all) |
| Timeout | 5s |
| Mode | async (zero latency impact) |

**Purpose:** Capture ALL tool calls from ALL sessions as JSONL events for observability.

**Behavior:**
1. Parses session_id, tool_name, tool_use_id from stdin
2. Resolves agent name from session-registry.json (falls back to "lead")
3. Reads current decision point from current-dp.txt
4. Builds tool-specific input_summary and output_summary per tool type:
   - Write: file_path, content_lines, content_bytes
   - Edit: file_path, old/new preview, replace_all
   - Read: file_path, offset, limit → lines count
   - Bash: command preview, exit_code
   - Glob: pattern, path → count
   - Grep: pattern, path, glob → count
   - Task: description preview, subagent_type
   - Default: first 3 keys from tool_input
5. Appends JSONL event to `events/{session_id}.jsonl`

**Dependencies:** jq (required), `.agent/observability/.current-project`, session-registry.json

---

## 2. References (9 documents, ~2,643 lines total)

### R-1: agent-catalog.md

| Property | Value |
|----------|-------|
| Path | `.claude/references/agent-catalog.md` |
| Version | v3.0 |
| Lines | 1,489 |
| Source Decisions | D-002 (Skills vs Agents), D-005 (Domain Decomposition) |
| Consumers | Lead (routing decisions at every orchestration cycle) |

Two-level catalog: Level 1 (~280L, Lead reads before spawning) + Level 2 (~1200L, on-demand detail). Contains P1 framework (One Agent, One Responsibility), WHEN/WHY/HOW decision triggers, phase dependency chain, and all 43 agent descriptions.

---

### R-2: agent-common-protocol.md

| Property | Value |
|----------|-------|
| Path | `.claude/references/agent-common-protocol.md` |
| Version | v4.0 |
| Lines | 247 |
| Source Decisions | D-009 (Agent Memory), D-011 (Cross-Phase Handoff), D-017 (Error Handling) |
| Consumers | All 43 agents (mandatory read) |

Shared procedures: task assignment handling, context change protocol, completion protocol, coordinator interaction, Task API usage, Team Memory, L1/L2/L3 format standards, downstream handoff (coordinator-only), edge cases, context loss recovery, agent memory, error handling tiers (1-3).

---

### R-3: coordinator-shared-protocol.md

| Property | Value |
|----------|-------|
| Path | `.claude/references/coordinator-shared-protocol.md` |
| Version | v1.0 |
| Lines | 135 |
| Source Decisions | D-013 (Coordinator Shared Protocol), D-008, D-009, D-011, D-017 |
| Consumers | 8 coordinators |

Coordinator-specific protocol: identity, worker management, understanding verification (AD-11), sub-gate protocol, failure handling, recovery, and progress-state.yaml tracking.

---

### R-4: gate-evaluation-standard.md

| Property | Value |
|----------|-------|
| Path | `.claude/references/gate-evaluation-standard.md` |
| Version | v1.0 |
| Lines | 151 |
| Source Decisions | D-008 (Gate Evaluation Standardization) |
| Consumers | Lead (phase transitions), gate-auditor (independent evaluation) |

Universal gate structure: 5-element gate record (evidence, checklist, verdict, justification, conditions). Per-gate criteria for G0-G9. Tier-specific gate depth (TRIVIAL: 3-item, STANDARD: 5-item, COMPLEX: 7-10 item).

---

### R-5: ontological-lenses.md

| Property | Value |
|----------|-------|
| Path | `.claude/references/ontological-lenses.md` |
| Version | v1.0 |
| Lines | 84 |
| Source Decisions | D-010 (Ontological Lenses Design), D-005 (Agent Decomposition) |
| Consumers | 4 INFRA analysts, 3 architecture agents (structure/interface/risk-architect) |

Four complementary perspectives: ARE (static/structural), RELATE (relational/dependency), DO (behavioral/lifecycle), IMPACT (change/ripple). Each lens maps to a specific INFRA analyst and Palantir Ontology alignment.

---

### R-6: task-api-guideline.md

| Property | Value |
|----------|-------|
| Path | `.claude/references/task-api-guideline.md` |
| Version | v6.0 |
| Lines | 80 |
| Consumers | Lead (TaskCreate/TaskUpdate), all agents (TaskList/TaskGet) |

NLP-consolidated Task API guide. Storage scoping (team vs solo), configuration, PERMANENT Task format, search patterns.

---

### R-7: layer-boundary-model.md

| Property | Value |
|----------|-------|
| Path | `.claude/references/layer-boundary-model.md` |
| Version | v1.0 |
| Lines | 130 |
| Source | AD-15 (hook addition prohibited) |
| Consumers | Lead, RSIL skills |

Defines the boundary between Layer 1 (NL-achievable via Opus 4.6) and Layer 2 (formal systems required). 5-dimension coverage: Static (95% L1), Relational (90% L1), Behavioral (85% L1), Impact (80% L1), Meta-Cognition. Coordinator orchestration section.

---

### R-8: ontology-communication-protocol.md

| Property | Value |
|----------|-------|
| Path | `.claude/references/ontology-communication-protocol.md` |
| Version | v1.0 |
| Lines | 318 |
| Consumers | Lead (when Ontology/Foundry topics arise) |

TEACH -> IMPACT ASSESS -> RECOMMEND -> ASK pattern. Verified against official palantir.com/docs. 3 researcher verifications, 40+ official pages, 60+ source URLs.

---

### R-9: pipeline-rollback-protocol.md

| Property | Value |
|----------|-------|
| Path | `.claude/references/pipeline-rollback-protocol.md` |
| Version | v1.0 |
| Lines | 74 |
| Source | GAP-5 |
| Consumers | plan-validation-pipeline, verification-pipeline, agent-teams-execution-plan |

Supported rollback paths: P5->P4, P6->P4, P6->P3, P7->P6, P7->P4, P8->P6. Rollback >2 phases requires user confirmation. Freeze-Archive-Rollback-Resume procedure.

---

## 3. Settings

### settings.json (84 lines)

**Environment Variables:**
| Variable | Value | Purpose |
|----------|-------|---------|
| CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS | "1" | Enable Agent Teams mode |
| CLAUDE_CODE_MAX_OUTPUT_TOKENS | "128000" | Max output token limit |
| CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS | "100000" | File read token limit |
| MAX_MCP_OUTPUT_TOKENS | "100000" | MCP tool output limit |
| BASH_MAX_OUTPUT_LENGTH | "200000" | Bash output limit |
| ENABLE_TOOL_SEARCH | "auto:7" | MCP tool search with threshold 7 |

**Permissions (deny):**
| Permission | Pattern |
|------------|---------|
| Read | .env*, **/secrets/**, **/*credentials*, **/.ssh/id_* |
| Bash | rm -rf *, sudo rm *, chmod 777 * |

**Hooks:** 4 (SubagentStart, PreCompact, SessionStart, PostToolUse) — see section 1 above

**Plugins:** 2 enabled
- superpowers-developing-for-claude-code@superpowers-marketplace
- superpowers@superpowers-marketplace

**Other:** language: Korean, teammateMode: auto, model: claude-opus-4-6

---

### settings.local.json (29 lines)

**Permissions (allow):**
| Permission | Purpose |
|------------|---------|
| Bash(*) | Unrestricted bash |
| mcp__sequential-thinking__sequentialthinking | Sequential thinking MCP |
| WebFetch(domain:github.com) | GitHub fetch |
| WebFetch(domain:raw.githubusercontent.com) | Raw GitHub content |
| WebSearch | Web search |
| mcp__context7__resolve-library-id | Context7 library resolution |
| mcp__context7__query-docs | Context7 doc queries |
| Skill(orchestrate) | Orchestrate skill |
| TaskUpdate | Task updates (Lead) |
| TaskCreate | Task creation (Lead) |

**MCP JSON Servers (8 enabled):**
oda-ontology, tavily, cow-ingest, cow-ocr, cow-vision, cow-review, cow-export, cow-storage

**Other:** enableAllProjectMcpServers: true, outputStyle: default

---

### .claude.json (project-level config)

**MCP Servers (4):**
| Server | Type | Command |
|--------|------|---------|
| github-mcp-server | stdio | npx @modelcontextprotocol/server-github |
| context7 | stdio | npx @upstash/context7-mcp |
| sequential-thinking | stdio | npx @modelcontextprotocol/server-sequential-thinking |
| tavily | stdio | npx tavily-mcp |

---

## 4. CLAUDE.md

| Property | Value |
|----------|-------|
| Path | `.claude/CLAUDE.md` |
| Version | v9.0 (Team Constitution) |
| Lines | 317 |
| Decisions integrated | D-001 through D-017 |

**Sections:**
| # | Section | Content |
|---|---------|---------|
| 0 | Language Policy | Korean user-facing, English technical |
| 1 | Team Identity | Workspace, Agent Teams config, Lead/Teammates |
| 2 | Phase Pipeline | Phase-agent mapping, tiers (D-001), gate standard |
| 3 | Roles | Lead (orchestrator), Coordinators (managers), Teammates (workers) |
| 4 | Communication | Lead->Teammate, Teammate->Lead, Lead->All |
| 5 | File Ownership | Non-overlapping, integrator exception |
| 6 | How Lead Operates | Agent Selection (6-step), Coordinator Management (Mode 1+3), Spawning, Understanding Verification, Monitoring, Observability (RTD), Phase Gates, Status Visualization, Coordination Infrastructure |
| 7 | Tools | sequential-thinking, tavily, context7, github tools |
| 8 | Safety | Blocked commands, protected files, git safety |
| 9 | Recovery | Lead recovery (RTD-centric), Teammate recovery |
| 10 | Integrity Principles | Lead and Teammate responsibilities |

**Key tables:** Custom Agents Reference (42 agents, 13 categories), Pipeline Tiers, Coordinator table, Lead-Direct agents, All Agents table, Skill Reference Table

---

## 5. Agent Memory (7 persistent files)

| Path | Contents |
|------|----------|
| `.claude/agent-memory/implementer/MEMORY.md` | Implementer cross-session lessons |
| `.claude/agent-memory/tester/MEMORY.md` | Tester cross-session lessons |
| `.claude/agent-memory/integrator/MEMORY.md` | Integrator cross-session lessons |
| `.claude/agent-memory/researcher/MEMORY.md` | Researcher cross-session lessons |
| `.claude/agent-memory/devils-advocate/MEMORY.md` | Devils-advocate cross-session lessons |
| `.claude/agent-memory/rsil/MEMORY.md` | RSIL cross-session lessons |
| `.claude/agent-memory/architect/MEMORY.md` | Architect lessons |
| `.claude/agent-memory/architect/lead-arch-redesign.md` | Architecture redesign topic file |

---

## 6. Complete File Count

| Component | File Count | Total Lines |
|-----------|------------|-------------|
| Agents (.md) | 43 | ~2,580 |
| Skills (SKILL.md) | 10 | ~3,374 |
| Hooks (.sh) | 4 | ~416 |
| References (.md) | 9 | ~2,643 |
| Settings (.json) | 2 | ~113 |
| CLAUDE.md | 1 | ~317 |
| Agent Memory | 8 | varies |
| .claude.json | 1 | ~568 |
| **Total infrastructure** | **78** | **~10,011** |
