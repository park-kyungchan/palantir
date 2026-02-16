# Agent Definition Quality and Communication Patterns Audit

**Date**: 2026-02-17
**Scope**: 6 agent definitions (.claude/agents/*.md), communication model, dual-mode operation
**Prior audit**: agent-definition-audit.md (2026-02-15, 18 findings, 8.5/10 health)
**References**: ref_agents.md, ref_teams.md, CLAUDE.md v10.9

---

## 1. Per-Agent Assessment

### 1.1 Field Compliance Matrix

| Field | analyst | researcher | implementer | infra-impl | delivery-agent | pt-manager | Required? |
|-------|---------|------------|-------------|------------|----------------|------------|-----------|
| name | YES | YES | YES | YES | YES | YES | YES |
| description | YES | YES | YES | YES | YES | YES | YES |
| tools | YES (5) | YES (10) | YES (7) | YES (6) | YES (10) | YES (9) | no (default=all) |
| model | OMIT (=opus) | OMIT (=opus) | OMIT (=opus) | OMIT (=opus) | haiku | haiku | no |
| maxTurns | 25 | 20 | 50 | 35 | 20 | 20 | no |
| memory | project | project | project | project | none | none | no |
| color | magenta | yellow | green | red | cyan | blue | no |
| hooks | NONE | NONE | YES (2) | YES (2) | YES (1) | NONE | no |
| permissionMode | OMIT | OMIT | OMIT | OMIT | OMIT | OMIT | no |
| skills | OMIT | OMIT | OMIT | OMIT | OMIT | OMIT | no |
| mcpServers | OMIT | OMIT | OMIT | OMIT | OMIT | OMIT | no |
| disallowedTools | OMIT | OMIT | OMIT | OMIT | OMIT | OMIT | no |

**Non-native fields used**: None detected. All agents use only CC-recognized frontmatter fields.

**Field compliance score**: 10/10. All required fields present. Optional fields used deliberately (not left to defaults where it matters).

---

### 1.2 Description (L1) Quality Assessment

The description field is auto-loaded into the Task tool definition and serves as Lead's routing intelligence for agent selection. Quality criteria: (a) PROFILE tag present, (b) WHEN condition clear, (c) TOOLS/CANNOT listed, (d) within reasonable length.

| Agent | Profile Tag | WHEN Condition | TOOLS Listed | CANNOT Listed | Char Count | L1 Score |
|-------|-------------|----------------|--------------|---------------|------------|----------|
| analyst | B-ReadAnalyzeWrite | Clear | YES (5) | YES (4) | 396 | 9/10 |
| researcher | C-ReadAnalyzeWriteWeb | Clear | YES (9) | YES (3) | 428 | 9/10 |
| implementer | D-CodeImpl | Clear | YES (7) | YES (3) | 370 | 9/10 |
| infra-impl | E-InfraImpl | Clear | YES (6) | YES (4) | 338 | 9/10 |
| delivery-agent | F-ForkDelivery | Clear | YES (10) | YES (2) | 377 | 8/10 |
| pt-manager | G-ForkPT | Clear | YES (9) | YES (2) | 372 | 8/10 |

**Observations**:

1. All 6 agents follow the exact same L1 template: `[Profile-X-Name]` + role sentence + blank line + `WHEN:` + `TOOLS:` + `CANNOT:` + `PROFILE:`. This consistency is excellent for Lead parsing.

2. delivery-agent and pt-manager scored 8/10 because their WHEN conditions reference specific skill invocations ("/delivery-pipeline" and "/task-management") rather than capability-based conditions. This is correct for fork agents but makes them invisible to generic routing -- they can only be invoked through their specific skills.

3. All descriptions are well under the 1024-char L1 budget limit (max is 428 chars for researcher).

4. Total L1 budget consumed by all 6 agents: ~2,281 chars. Well within the 32,000-char system-wide budget.

---

### 1.3 Agent Body Quality Assessment

The body (below frontmatter) is loaded as the agent's system prompt in its isolated context window. Quality criteria: (a) role clarity, (b) behavioral guidelines, (c) completion protocol, (d) constraints, (e) communication instructions.

| Agent | Role Clarity | Behavioral Guidelines | Completion Protocol | Constraints | Body Score |
|-------|-------------|----------------------|--------------------|--------------|----|
| analyst | Clear | 3 guidelines | Full | 1 constraint | 7/10 |
| researcher | Clear | 4 guidelines | Full | 4 constraints | 8/10 |
| implementer | Clear | 1 guideline | Full | 1 constraint | 6/10 |
| infra-impl | Clear | 1 guideline | Full | 3 constraints | 7/10 |
| delivery-agent | Clear | 4 guidelines | Full | 6 constraints | 9/10 |
| pt-manager | Clear | 4 guidelines | Full | 4 constraints | 8/10 |

**Detailed Body Findings**:

**ANALYST (7/10)**: Good role description, good behavioral guidelines (read-first, seq-thinking, hierarchical output). Missing: no mention of how to handle Write vs Read-only boundary. The constraint "Never attempt to use Edit tool" is critical and present.

**RESEARCHER (8/10)**: Strongest non-fork body. Has operational workflow (cc-reference cache first, then web). Has source citation requirement. Has output structure guidance (finding-source-confidence-implications). Has conflict resolution strategy.

**IMPLEMENTER (6/10)**: Weakest body among all agents. Only 1 behavioral guideline ("Run relevant tests after every modification"). Missing: no guidance on code style, no debugging strategy, no file scope verification, no mention of git operations. The implementer is the highest-stakes agent (Bash + Edit + Write on source code) but has the least behavioral guidance.

**INFRA-IMPLEMENTER (7/10)**: Adequate. Has seq-thinking guidance for complex edits. Clear constraints about no Bash and no deletion. Missing: no guidance on YAML formatting precision (critical for frontmatter editing), no cross-reference verification instructions.

**DELIVERY-AGENT (9/10)**: Best body overall. Comprehensive behavioral guidelines (verify all-PASS, git diff before commit, individual staging, commit style, Read-Merge-Write). Extensive safety constraints (user confirmation, no force push, sensitive file exclusion, no .claude/ modification, terminal phase). Stop hook adds automated verification.

**PT-MANAGER (8/10)**: Good operational guidelines (TaskList first, merge-not-overwrite, metadata requirements, cycle verification). Safety constraints on PT integrity are well-defined.

---

## 2. Communication Model Assessment

### 2.1 Dual-Mode Operation Analysis

Per CLAUDE.md Section 2.1:
- **P0-P1 (Subagent mode)**: `run_in_background` -- agent returns up to 30K chars to parent Lead
- **P2+ (Teammate mode)**: Team infrastructure -- must use SendMessage for result exchange

**Critical question**: Do agent bodies account for this dual-mode operation?

| Agent | Subagent Mode (P0-P1) | Teammate Mode (P2+) | Dual-Mode Aware? |
|-------|----------------------|---------------------|------------------|
| analyst | Not mentioned | "When working as a teammate (team_name provided)" | PARTIAL |
| researcher | Not mentioned | Same conditional | PARTIAL |
| implementer | Not mentioned | Same conditional | PARTIAL |
| infra-impl | Not mentioned | Same conditional | PARTIAL |
| delivery-agent | N/A (P8 only) | Same conditional | N/A |
| pt-manager | N/A (fork only) | Same conditional | N/A |

**Finding COMM-01 [HIGH]**: All 4 general-purpose agents (analyst, researcher, implementer, infra-implementer) have identical Completion Protocol text that says "When working as a teammate (team_name provided)" -- implying SendMessage is used ONLY when `team_name` is provided. But they provide NO explicit instructions for the subagent (non-teammate) case. The implicit assumption is that in subagent mode, the agent's final response IS the return value (up to 30K chars). This is technically correct (CC injects the response back to parent) but is never explicitly stated.

**Gap**: An agent in subagent mode does not know:
- That its final output will be returned to the parent (and possibly truncated at 30K chars)
- That it should structure its output for parent consumption (summary first, details after)
- That writing to files and THEN summarizing is the safest pattern (full output survives truncation)

**Finding COMM-02 [MEDIUM]**: The Completion Protocol says "send L1 summary to Lead via SendMessage" but none of the 4 general-purpose agents have SendMessage in their `tools` list. In teammate mode, CC provides SendMessage automatically to all teammates. But the explicit absence from the tools list creates a documentation inconsistency -- the body references a tool not listed in the frontmatter.

Tool list verification:

```
analyst tools:     Read, Glob, Grep, Write, sequential-thinking      -- NO SendMessage
researcher tools:  Read, Glob, Grep, Write, WebSearch, WebFetch, sequential-thinking, context7, tavily  -- NO SendMessage
implementer tools: Read, Glob, Grep, Edit, Write, Bash, sequential-thinking  -- NO SendMessage
infra-impl tools:  Read, Glob, Grep, Edit, Write, sequential-thinking  -- NO SendMessage
delivery-agent:    Read, Glob, Grep, Edit, Write, Bash, TaskList, TaskGet, TaskUpdate, AskUserQuestion  -- NO SendMessage
pt-manager:        Read, Glob, Grep, Write, TaskList, TaskGet, TaskCreate, TaskUpdate, AskUserQuestion  -- NO SendMessage
```

Zero agents list SendMessage, yet all 6 bodies instruct "send L1 summary to Lead via SendMessage." This works in practice because SendMessage is automatically available to all teammates (per ref_teams.md: teammates can message anyone). But the tools field is supposed to be the tool allowlist -- if it's explicit, does an unlisted tool get blocked?

**Analysis**: Per ref_agents.md: "tools: Tool allowlist (explicit = ONLY these)." If this is strictly enforced, SendMessage would be blocked for all agents. However, Agent Teams infrastructure tools (SendMessage, etc.) may be injected separately from the tools allowlist -- they're part of the team coordination layer, not the agent's task-execution tools. This needs verification but is likely safe given the system works.

**Finding COMM-03 [MEDIUM]**: delivery-agent and pt-manager are fork agents (invoked for specific skills only). Their Completion Protocol still says "When working as a teammate (team_name provided)" with SendMessage instructions. But per CLAUDE.md, these agents are ALWAYS invoked as teammates (P8 for delivery, task-management for PT). The conditional "when team_name provided" is misleading -- they should ALWAYS use SendMessage.

### 2.2 Result Delivery Pattern Assessment

Per ref_teams.md Section 4: "There is no shared memory. No sockets, no pipes, no IPC."

Three result delivery channels exist:
1. **Subagent return**: Agent's final text response injected to parent (up to 30K chars)
2. **SendMessage**: Write to recipient's inbox JSON
3. **File write**: Agent writes to disk, recipient reads from known path

| Agent | Channel 1 (Subagent) | Channel 2 (SendMessage) | Channel 3 (File Write) |
|-------|---------------------|------------------------|----------------------|
| analyst | Implicit (no guidance) | Body says "L1 summary via SendMessage" | Uses Write tool for analysis outputs |
| researcher | Implicit (no guidance) | Body says "L1 summary via SendMessage" | Uses Write tool for research outputs |
| implementer | Implicit (no guidance) | Body says "L1 summary via SendMessage" | Uses Write/Edit for source code |
| infra-impl | Implicit (no guidance) | Body says "L1 summary via SendMessage" | Uses Write/Edit for .claude/ files |
| delivery-agent | N/A | Body says "L1 summary via SendMessage" | Uses Write for MEMORY.md |
| pt-manager | N/A | Body says "L1 summary via SendMessage" | Uses Write for detail files |

**Finding COMM-04 [LOW]**: No agent body explicitly instructs "write detailed output to file FIRST, then send L1 summary." This is the optimal pattern because:
- File writes persist beyond context window
- SendMessage L1 summary is small (~200 tokens) and gives Lead routing information
- If the agent hits maxTurns or crashes, file output survives but SendMessage may not

The analyst memory (MEMORY.md) has learned this pattern: "Write findings immediately after analysis -- do not wait for gate approval." But this is a runtime learning, not baked into the body.

---

## 3. Missing Agent Capabilities

### 3.1 Coverage Analysis

| Capability Need | Covered By | Gap? |
|----------------|-----------|------|
| Codebase analysis | analyst | NO |
| Web research | researcher | NO |
| Source code editing | implementer | NO |
| Infrastructure editing | infra-implementer | NO |
| Git commit + delivery | delivery-agent | NO |
| Task lifecycle management | pt-manager | NO |
| File deletion | NONE | YES -- no agent has `rm` capability except implementer (Bash) |
| CC native doc research | NONE (ghost: claude-code-guide) | YES -- researcher can partially cover |
| Cross-agent coordination | Lead only | NO (by design) |
| Database operations | NONE | NO (not needed for current project) |
| Image/media analysis | NONE | UNCLEAR (depends on Read tool multimodal support) |

**Finding CAP-01 [LOW]**: The claude-code-guide ghost agent (AGT-07 from prior audit) remains unresolved. Three skills reference it with fallback to cc-reference cache. No agent file exists.

### 3.2 Tool Coverage Matrix

| Tool | analyst | researcher | implementer | infra-impl | delivery | pt-mgr |
|------|---------|------------|-------------|------------|----------|--------|
| Read | YES | YES | YES | YES | YES | YES |
| Glob | YES | YES | YES | YES | YES | YES |
| Grep | YES | YES | YES | YES | YES | YES |
| Edit | -- | -- | YES | YES | YES | -- |
| Write | YES | YES | YES | YES | YES | YES |
| Bash | -- | -- | YES | -- | YES | -- |
| WebSearch | -- | YES | -- | -- | -- | -- |
| WebFetch | -- | YES | -- | -- | -- | -- |
| seq-thinking | YES | YES | YES | YES | -- | -- |
| context7 | -- | YES | -- | -- | -- | -- |
| tavily | -- | YES | -- | -- | -- | -- |
| TaskList | -- | -- | -- | -- | YES | YES |
| TaskGet | -- | -- | -- | -- | YES | YES |
| TaskCreate | -- | -- | -- | -- | -- | YES |
| TaskUpdate | -- | -- | -- | -- | YES | YES |
| AskUserQuestion | -- | -- | -- | -- | YES | YES |

**Tool profile uniqueness**: Each agent has a distinct tool profile. No two agents are identical. The profiles form a clear hierarchy:
- B (analyst): Read+Write+Analyze -- base analytical profile
- C (researcher): B + Web -- extends analyst with web access
- D (implementer): B + Edit + Bash -- code modification with execution
- E (infra-impl): B + Edit -- code modification without execution (safe for config)
- F (delivery): D + Task API subset -- implementer-like with task management
- G (pt-manager): B + Full Task API -- analyst-like with full task management

---

## 4. Consolidated Findings

### New Findings (this audit)

| ID | Severity | Title | Agent(s) | Impact |
|----|----------|-------|----------|--------|
| COMM-01 | HIGH | No subagent-mode completion instructions | analyst, researcher, implementer, infra-impl | Agents in P0-P1 subagent mode have no guidance on output format/truncation |
| COMM-02 | MEDIUM | SendMessage referenced in body but absent from tools list | All 6 | Documentation inconsistency; may cause confusion if tools field strictly enforced |
| COMM-03 | MEDIUM | Fork agents have conditional teammate protocol but always run as teammates | delivery-agent, pt-manager | Misleading conditional; should be unconditional |
| COMM-04 | LOW | No "write-first, summarize-second" pattern in bodies | All 6 | Suboptimal resilience; output may be lost on crash/truncation |
| BODY-01 | MEDIUM | Implementer has weakest body despite highest-stakes tools | implementer | Only 1 behavioral guideline for agent with Bash+Edit+Write |
| REF-01 | LOW | ref_agents.md example uses `allowed-tools` but field table and all agents use `tools` | N/A (reference doc) | Inconsistency in reference documentation |

### Prior Findings Status (from agent-definition-audit.md, 2026-02-15)

| ID | Severity | Status | Notes |
|----|----------|--------|-------|
| AGT-01 | HIGH | OPEN | execution-impact still routes to researcher instead of analyst |
| AGT-02 | HIGH | RESOLVED | CLAUDE.md Section 2.1 now says "Lead with local agents (run_in_background)" -- explicitly permits agent spawns in P0-P1 |
| AGT-03 | MEDIUM | OPEN | delivery-agent haiku + no memory for MEMORY.md editing |
| AGT-04 | MEDIUM | OPEN | tavily not in settings.json allow list |
| AGT-05 | MEDIUM | CLOSED (by-design) | pt-manager Write-only is acceptable |
| AGT-06 | MEDIUM | OPEN | orchestration-decompose missing fork agents |
| AGT-07 | MEDIUM | OPEN | claude-code-guide ghost agent |
| AGT-10 | LOW | RESOLVED | delivery-agent body now includes ".claude/" restriction (line 57) |
| AGT-14 | LOW | OPEN | Korean language policy not in fork agent bodies |

---

## 5. Severity Distribution

| Severity | Count (New) | Count (Open Prior) | Total Active |
|----------|-------------|-------------------|-------------|
| CRITICAL | 0 | 0 | 0 |
| HIGH | 1 | 1 | 2 |
| MEDIUM | 3 | 4 | 7 |
| LOW | 2 | 1 | 3 |
| TOTAL | 6 | 6 | 12 |

**Overall Health Score**: 7.5/10

Down from 8.5/10 in prior audit due to communication model gaps now assessed. Agent definitions themselves remain well-designed (field compliance 10/10, L1 quality 9/10 average). The primary gap is in the body's handling of dual-mode communication (subagent vs teammate), particularly for the 4 general-purpose agents.

---

## 6. Prioritized Recommendations

### P1 -- High Priority

**R1. Add subagent-mode completion instructions to all 4 general-purpose agents.**
Currently, only teammate mode is addressed ("When working as a teammate"). Add a parallel section:

```markdown
## Completion Protocol
When working as a subagent (no team_name):
- Write detailed output to assigned file path FIRST
- Final response = structured summary (will be returned to parent, max 30K chars)
- Structure: status line, key findings/changes, file paths written, next-step recommendation
- Put most important information FIRST (truncation cuts from the end)

When working as a teammate (team_name provided):
- Write detailed output to assigned file path FIRST
- Send L1 summary to Lead via SendMessage (~200 tokens)
- Include: status (PASS/FAIL), files changed, key metrics, routing recommendation
```

**R2. Strengthen implementer body with behavioral guidelines.**
The implementer has the most dangerous tool set (Bash + Edit + Write on source code) but the fewest behavioral guidelines (1). Add:
- Read existing code before modifying (understand context)
- Verify file ownership before editing (non-overlapping ownership)
- Use sequential-thinking for multi-file refactoring plans
- Stage changes incrementally; test after each logical unit
- Never modify .claude/ directory files (use infra-implementer for that)

### P2 -- Medium Priority

**R3. Resolve SendMessage tool listing inconsistency.**
Two options:
- (a) Accept that Agent Teams tools (SendMessage, etc.) are injected automatically outside the tools allowlist -- document this in ref_agents.md
- (b) Add SendMessage to all agent tools lists (adds clutter, may cause issues in subagent mode)
Option (a) is recommended.

**R4. Make fork agent completion protocol unconditional.**
Change delivery-agent and pt-manager from "When working as a teammate (team_name provided)" to simply "Always send L1 summary to Lead via SendMessage" since they are always invoked as teammates.

**R5. Route execution-impact from researcher to analyst** (carried forward from AGT-01).

**R6. Resolve claude-code-guide ghost** (carried forward from AGT-07). Recommend: make cc-reference cache the primary path in the 3 affected skills.

### P3 -- Low Priority

**R7. Add "write-first, summarize-second" pattern to all agent bodies** as explicit behavioral guideline.

**R8. Fix ref_agents.md example** to use `tools` instead of `allowed-tools` for consistency with field table and all 6 agent files.

**R9. Add Korean language policy** to delivery-agent and pt-manager bodies for AskUserQuestion interactions.

---

## 7. Researcher maxTurns Discrepancy

Note: The prior audit (agent-definition-audit.md line 29) lists researcher maxTurns as 30, but the actual file shows maxTurns: 20. The prior audit data was incorrect. Current value is 20.

---

## Appendix: Communication Flow Diagrams

### P0-P1 Subagent Mode
```
Lead ──[Task(run_in_background)]──> Agent (isolated context)
                                      │
                                      ├── [works...]
                                      │
                                      └── returns text (max 30K chars) ──> Lead
                                           (no SendMessage, no team infrastructure)
```

### P2+ Teammate Mode
```
Lead ──[TeamCreate]──> Team Infrastructure
  │
  ├──[TaskCreate]──> Task Files (disk)
  │
  └──[spawn]──> Teammate Agent (own tmux pane)
                    │
                    ├── claims task (file lock)
                    ├── [works...]
                    ├── writes output to file (disk)
                    └── SendMessage(lead, "L1 summary") ──> Lead's inbox
```

### Key Difference
- Subagent: output = return value (injected into parent context)
- Teammate: output = SendMessage to inbox (Lead must check inbox)
- Both: file writes to disk as persistent artifact
