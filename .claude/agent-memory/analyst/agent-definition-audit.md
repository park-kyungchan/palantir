# Agent Definition Audit

**Date**: 2026-02-15
**Scope**: 6 agent definitions, settings.json, 35 skill frontmatter cross-references
**Methodology**: 5-axis evaluation (tool-capability, memory, model, cross-agent consistency, skill routing)

---

## Summary

| Metric | Value |
|--------|-------|
| Total findings | 18 |
| CRITICAL | 0 |
| HIGH | 2 |
| MEDIUM | 5 |
| LOW | 7 |
| ADVISORY | 4 |

Overall agent health: **8.5/10** -- agents are well-designed with clear separation of concerns. Issues are primarily at integration boundaries (skill-agent routing mismatches) rather than internal agent defects.

---

## Agent Inventory

| Agent | Profile | Tools | Memory | Model | maxTurns | Color |
|-------|---------|-------|--------|-------|----------|-------|
| analyst | B (ReadAnalyzeWrite) | Read,Glob,Grep,Write,seq-think | project | default (opus) | 25 | magenta |
| researcher | C (ReadAnalyzeWriteWeb) | Read,Glob,Grep,Write,WebSearch,WebFetch,seq-think,context7,tavily | project | default (opus) | 30 | yellow |
| implementer | D (CodeImpl) | Read,Glob,Grep,Edit,Write,Bash,seq-think | project | default (opus) | 50 | green |
| infra-implementer | E (InfraImpl) | Read,Glob,Grep,Edit,Write,seq-think | project | default (opus) | 35 | red |
| delivery-agent | F (ForkDelivery) | Read,Glob,Grep,Edit,Write,Bash,TaskList,TaskGet,TaskUpdate,AskUser | none | haiku | 20 | cyan |
| pt-manager | G (ForkPT) | Read,Glob,Grep,Write,TaskList,TaskGet,TaskCreate,TaskUpdate,AskUser | none | haiku | 20 | blue |

---

## Findings

### AGT-01 [HIGH] execution-impact routes to researcher, but analyst would be more appropriate

**File**: `/home/palantir/.claude/skills/execution-impact/SKILL.md` (lines 21-22, 39)
**Evidence**: The skill says "Spawn researcher for grep-based reverse reference analysis" and "Researcher performs `grep -rl <basename>`". However, the researcher agent (Profile-C) is designed for *web-enabled research* -- its differentiator over analyst is WebSearch, WebFetch, context7, and tavily. The execution-impact skill uses NONE of these web tools. It only needs Read, Glob, Grep, and Write -- exactly the analyst's (Profile-B) tool set.

**Impact**: Wasted context. The researcher agent description (Profile-C) loads web-tool instructions into its context, consuming tokens on capabilities never used by execution-impact. The researcher also costs more in terms of MCP tool availability checks (context7, tavily connections attempted but unused).

**Recommendation**: Change execution-impact routing from `researcher` to `analyst`. The analyst has all necessary tools (Read, Glob, Grep, Write) and no unnecessary web overhead. Update L1 description and L2 body references.

---

### AGT-02 [HIGH] P0-P2 skills reference "spawn analyst" / "launch analyst" but Section 2.1 says P0-P2 is Lead-only

**Files**:
- `/home/palantir/.claude/skills/pre-design-brainstorm/SKILL.md` (line 23): "Launch 1-2 analysts (run_in_background)"
- `/home/palantir/.claude/skills/pre-design-validate/SKILL.md` (line 21): "Launch analyst (run_in_background)"
- `/home/palantir/.claude/skills/design-architecture/SKILL.md` (line 22): "Launch analyst (run_in_background)"
- `/home/palantir/.claude/skills/design-interface/SKILL.md` (line 21): "Launch analyst (run_in_background)"
- `/home/palantir/.claude/skills/design-risk/SKILL.md` (line 21): "Launch analyst (run_in_background)"

**Evidence**: CLAUDE.md Section 2.1 states: "P0-P2 (PRE-DESIGN + DESIGN): Lead-only. Brainstorm, validate, feasibility, architecture, interface, risk -- all executed by Lead with local agents (run_in_background). No Team infrastructure needed."

**Analysis**: The phrase "Lead with local agents (run_in_background)" is ambiguous. It could mean Lead uses `run_in_background` for spawning agents (which IS Team infrastructure via Task tool), or it means Lead does the analysis itself in the background. The skills say "Launch analyst (run_in_background)" which implies agent spawning. However, `run_in_background` is a Task tool parameter, so this IS agent spawning -- contradicting "Lead-only."

**Clarification needed**: Either Section 2.1 should explicitly permit `run_in_background` agent spawns during P0-P2, or the skills should be rewritten to say "Lead-direct" for STANDARD tier during P0-P2. This was previously identified in infra-audit-v3-iter4 (finding about P0-P2 skills saying "spawn analyst") but remains unresolved.

**Recommendation**: Resolve the ambiguity by updating Section 2.1 to: "P0-P2: Lead with optional local agents (run_in_background). No Team infrastructure (no TeamCreate/SendMessage)."

---

### AGT-03 [MEDIUM] delivery-agent has Edit tool but description says "fork agent" -- potential MEMORY.md corruption risk

**File**: `/home/palantir/.claude/agents/delivery-agent.md` (lines 10-21, 36-37)
**Evidence**: The delivery-agent has both `Edit` and `Write` tools. Its body says "Update MEMORY.md using Read-Merge-Write (read first, merge, then write)". Since memory is `none`, the agent has no project memory to inform its merge decisions. It operates on the global MEMORY.md file with no context about prior edits.

**Impact**: With `model: haiku` and `memory: none`, the delivery-agent has the least context of all agents yet is tasked with editing the most critical persistent artifact (MEMORY.md). Haiku may produce lower-quality merge decisions compared to the default opus model.

**Mitigation present**: The skill body requires "USER CONFIRMATION via AskUserQuestion" for MEMORY.md writes. This is a strong safeguard but relies on the user catching haiku-generated errors.

**Recommendation**: Consider whether the MEMORY.md update step should be promoted to Lead-direct (opus-quality) or whether the delivery-agent should have `memory: project` specifically for this task.

---

### AGT-04 [MEDIUM] researcher's tavily MCP tool not in settings.json permissions allow-list

**Files**:
- `/home/palantir/.claude/agents/researcher.md` (line 20): `mcp__tavily__search`
- `/home/palantir/.claude/settings.json` (lines 12-22): No `mcp__tavily__search` in allow list
- `/home/palantir/.claude/settings.local.json` (line 17): tavily in `enabledMcpjsonServers`

**Evidence**: The tavily MCP server is enabled in settings.local.json, but `mcp__tavily__search` is NOT listed in `settings.json > permissions.allow`. This means the researcher will get a permission prompt when trying to use tavily, potentially interrupting automated agent flows.

**Impact**: Non-blocking (prompt will appear), but disrupts smooth agent execution. The researcher body says "Use context7 for library docs, tavily for broader searches" suggesting tavily is a core capability.

**Recommendation**: Add `"mcp__tavily__search"` to `settings.json > permissions.allow` to match the researcher's expected capabilities.

---

### AGT-05 [MEDIUM] pt-manager lacks Edit tool but skill methodology implies file modification

**Files**:
- `/home/palantir/.claude/agents/pt-manager.md` (line 8): "CANNOT: Edit, Bash"
- `/home/palantir/.claude/skills/task-management/SKILL.md` (line 80): "Write detail files for tasks needing extended documentation"

**Evidence**: The task-management skill says pt-manager should "Write detail files for tasks needing extended documentation" (step 3.3). The pt-manager has `Write` but not `Edit`. This means the pt-manager can create new detail files but cannot update existing ones. If a detail file already exists and needs modification, the pt-manager would have to overwrite it entirely via Write (losing precise edit capability).

**Impact**: Low-to-medium. Write-only is acceptable for new detail file creation. But if the pt-manager needs to update an existing detail file (e.g., adding new task metadata), it must read the full file first and rewrite entirely. This is the documented Write tool behavior ("must read before writing"), so it's functional but less precise than Edit.

**Recommendation**: Acceptable as-is. The pt-manager's primary job is Task API operations, not file editing. Detail files are auxiliary. No change needed.

---

### AGT-06 [MEDIUM] orchestration-decompose lists only 4 of 6 agents in capability reference

**File**: `/home/palantir/.claude/skills/orchestration-decompose/SKILL.md` (lines 33-37)
**Evidence**: The skill lists:
- analyst (Profile-B)
- researcher (Profile-C)
- implementer (Profile-D)
- infra-implementer (Profile-E)

Missing:
- delivery-agent (Profile-F)
- pt-manager (Profile-G)

**Impact**: Low in practice -- delivery-agent and pt-manager are "fork agents" for specific skills (delivery-pipeline and task-management) and are never assigned general tasks. But the omission could confuse the Lead model if it considers the list exhaustive.

**Recommendation**: Add a note clarifying that Profile-F and Profile-G are fork agents, not assignable for general task decomposition.

---

### AGT-07 [MEDIUM] self-improve references "claude-code-guide" which does not exist as an agent

**File**: `/home/palantir/.claude/skills/self-improve/SKILL.md` (lines 4, 9, 20, 27-28, 45, 68, 91)
**Evidence**: The self-improve skill references "claude-code-guide" 7 times:
- "Researches CC native capabilities via claude-code-guide" (L1 description)
- "Spawn claude-code-guide for CC native feature research" (L2 methodology)
- "1 claude-code-guide + 1-2 infra-implementer waves" (execution model)
- etc.

There is NO agent file at `/home/palantir/.claude/agents/claude-code-guide.md`. A fallback is provided ("if unavailable, use cc-reference cache") but the primary path implies spawning a nonexistent agent.

**Note**: This was previously identified as INT-07 in the integration audit and a fallback was standardized. The "(if unavailable, use cc-reference cache)" fallback exists in 3 skills: self-improve, pre-design-feasibility, verify-cc-feasibility. However, the primary verb "spawn claude-code-guide" still implies it should exist.

**Impact**: Every invocation of these skills will fail to spawn claude-code-guide and fall back to cache, adding unnecessary routing attempts.

**Recommendation**: Either create a claude-code-guide agent (researcher profile with specific CC documentation focus) or rewrite the skills to make cc-reference cache the PRIMARY path with web research as the fallback.

---

### AGT-08 [LOW] analyst cannot delete files, but manage-skills methodology says "For DELETE: remove skill directory"

**File**: `/home/palantir/.claude/skills/manage-skills/SKILL.md` (line 56)
**Evidence**: "For DELETE: remove skill directory". The manage-skills skill routes to analyst (lines 20-21). The analyst has Read, Glob, Grep, Write, and sequential-thinking. It has NO Bash (for `rm -r`) and NO Edit. Write can create/overwrite files but cannot delete them.

**Impact**: The DELETE action in manage-skills is unimplementable by the analyst agent. If manage-skills detects an orphaned skill needing deletion, the analyst cannot execute it.

**Recommendation**: Either route DELETE actions to infra-implementer (who also lacks Bash but has Edit -- still can't delete), or acknowledge that DELETE requires Lead to perform via a separate agent with Bash access (implementer), or simply flag deletion for manual user action.

---

### AGT-09 [LOW] infra-implementer body says "Cannot delete files" but its constraint is based on tool limitations, not explicit policy

**File**: `/home/palantir/.claude/agents/infra-implementer.md` (line 36)
**Evidence**: "Cannot delete files -- only create and modify". This is stated as a behavioral constraint in the body. However, the infra-implementer has Write tool, and technically Write can overwrite a file with empty content (not deletion but content destruction). The real constraint is the absence of Bash (no `rm` command).

**Impact**: Negligible. The behavioral guideline is correct in practice. The Write tool cannot truly delete a file (remove from filesystem) -- it can only overwrite content.

**Recommendation**: No action needed. The constraint is accurate.

---

### AGT-10 [LOW] delivery-agent's Bash access creates .claude/ modification risk despite implementer boundary

**File**: `/home/palantir/.claude/agents/delivery-agent.md` (lines 6-11)
**Evidence**: The delivery-agent has Bash access (for `git add`, `git commit`). The implementer explicitly says "Never modify .claude/ directory files (use infra-implementer for that)". But delivery-agent has no such constraint and could theoretically use Bash to modify .claude/ files.

**Mitigation present**: The delivery-agent body focuses exclusively on git operations and MEMORY.md updates. Its `AskUserQuestion` requirement for external actions provides a guardrail.

**Impact**: Low. The delivery-agent is only invoked for the terminal delivery-pipeline skill and its behavior is well-constrained by the skill methodology.

**Recommendation**: Add an explicit constraint to delivery-agent body: "Never modify .claude/ infrastructure files -- only source/doc files and MEMORY.md."

---

### AGT-11 [LOW] WebFetch domain restriction in settings.json limits researcher to github.com only

**Files**:
- `/home/palantir/.claude/settings.json` (lines 15-16): `WebFetch(domain:github.com)`, `WebFetch(domain:raw.githubusercontent.com)`
- `/home/palantir/.claude/agents/researcher.md` (line 16): `WebFetch` (unrestricted)

**Evidence**: The researcher lists `WebFetch` as a tool without domain restrictions. But settings.json only pre-approves `WebFetch` for github.com and raw.githubusercontent.com. Any other domain will trigger a permission prompt.

**Impact**: The researcher's behavioral guideline says "WebFetch for specific pages" implying arbitrary domain access. In practice, fetching official docs from non-GitHub domains (e.g., palantir.com/docs, docs.python.org) will prompt for permission each time.

**Recommendation**: Either expand WebFetch permissions to include common documentation domains, or document this limitation in the researcher body.

---

### AGT-12 [LOW] analyst Write tool capability inconsistency with "read-only" identity

**File**: `/home/palantir/.claude/agents/analyst.md` (lines 21-23, 33)
**Evidence**: The body says "You are a read-only analysis agent" (line 23) and "Write output to assigned paths only -- never modify source files" (line 33). However, the analyst HAS the Write tool (line 14). The "read-only" identity is misleading -- the analyst can create and overwrite files.

**Impact**: Cosmetic. The behavioral constraint ("write output to assigned paths only") is the actual policy, and "read-only" refers to not modifying *existing source files*, not filesystem read-only.

**Recommendation**: Change "read-only analysis agent" to "analysis and documentation agent" for precision. The constraint "Write output to assigned paths only" is sufficient.

---

### AGT-13 [LOW] implementer maxTurns (50) is 2x higher than any other agent -- potential context bloat risk

**File**: `/home/palantir/.claude/agents/implementer.md` (line 19)
**Evidence**: maxTurns comparison: implementer=50, infra-implementer=35, researcher=30, analyst=25, delivery-agent=20, pt-manager=20. The implementer's 50 turns is appropriate for complex coding tasks but means it could accumulate substantial context before completing, increasing compaction risk (BUG-002).

**Impact**: Known risk documented in BUG-002 ("Large-task teammates auto-compact before L1/L2"). The 50-turn budget makes this more likely for implementer than other agents.

**Recommendation**: No change -- 50 turns is necessary for complex implementation tasks. BUG-002 workaround ("Keep prompts focused, avoid context bloat") applies.

---

### AGT-14 [LOW] delivery-agent and pt-manager both have AskUserQuestion but no skill explicitly documents the user interaction pattern

**Files**:
- `/home/palantir/.claude/agents/delivery-agent.md` (line 20): `AskUserQuestion`
- `/home/palantir/.claude/agents/pt-manager.md` (line 19): `AskUserQuestion`

**Evidence**: Both fork agents have AskUserQuestion tool. delivery-pipeline skill documents when to use it (line 39: "Every external action requires USER CONFIRMATION"). But task-management skill mentions it only once in passing (line 29: "If user intent unclear -> AskUserQuestion"). Neither agent body documents the UX pattern for user interactions (how to phrase questions, when to ask vs proceed, language policy for questions).

**Impact**: Low. Both agents are invoked for specific skills with well-defined methodologies. But language policy (Korean for user-facing) is not enforced in agent bodies.

**Recommendation**: Add a behavioral guideline to both fork agents: "User-facing questions via AskUserQuestion must be in Korean (per Language Policy)."

---

### AGT-15 [ADVISORY] sequential-thinking MCP tool is pre-approved in settings but only 4/6 agents use it

**Files**:
- `/home/palantir/.claude/settings.json` (line 14): `mcp__sequential-thinking__sequentialthinking` in allow
- delivery-agent and pt-manager do NOT list sequential-thinking in tools

**Evidence**: Analyst, researcher, implementer, and infra-implementer all have sequential-thinking. Delivery-agent and pt-manager do not. Given their simpler tasks (git operations, Task API calls) and haiku model, this is appropriate -- haiku may not benefit from structured thinking to the same degree.

**Impact**: None. Design decision is correct.

**Recommendation**: No change needed. This is by-design separation.

---

### AGT-16 [ADVISORY] No agent has ListFiles/LS tool -- all directory exploration goes through Glob

**Evidence**: None of the 6 agents list a `ListFiles` or `LS` tool. Directory contents are discovered exclusively through Glob patterns. This is adequate for structured exploration but means agents cannot simply "ls" a directory to see what's there.

**Impact**: Negligible. Glob("*") achieves the same result. The Read tool can also read directory contents in some implementations.

**Recommendation**: No change needed.

---

### AGT-17 [ADVISORY] researcher agent-memory contains stale operational notes

**File**: `/home/palantir/.claude/agent-memory/researcher/MEMORY.md` (lines 12, 55-57)
**Evidence**: Contains operational tips like "WebFetch on official docs (platform.claude.com, code.claude.com) returns excellent structured data" and "Palantir official docs are at palantir.com/docs". These are useful cross-session notes. However, the notes about MCP tool availability ("Fallback: WebSearch replaces tavily") overlap with the agent body guidance.

**Impact**: Minor context duplication between agent body and agent memory.

**Recommendation**: Acceptable. Agent memory supplements the body with runtime learnings.

---

### AGT-18 [ADVISORY] Color scheme has no semantic system documented

**Evidence**: Colors assigned: analyst=magenta, researcher=yellow, implementer=green, infra-implementer=red, delivery-agent=cyan, pt-manager=blue. The color assignments appear arbitrary -- no documentation explains why (e.g., red=danger for infra changes, green=code implementation).

**Impact**: Purely cosmetic. Colors serve as visual differentiators in tmux, not semantic indicators.

**Recommendation**: No change needed. Colors are functional as-is.

---

## Cross-Reference Matrix: Skills to Agents

| Skill | Expected Agent | Capability Match | Issue? |
|-------|---------------|------------------|--------|
| pre-design-brainstorm | analyst | YES (Read,Grep,Write) | AGT-02 (P0-P2 Lead-only conflict) |
| pre-design-validate | analyst | YES | AGT-02 |
| pre-design-feasibility | researcher | YES (WebSearch for CC docs) | AGT-07 (claude-code-guide ghost) |
| design-architecture | analyst | YES | AGT-02 |
| design-interface | analyst | YES | AGT-02 |
| design-risk | analyst | YES | AGT-02 |
| research-codebase | analyst | YES (Read,Glob,Grep,Write) | -- |
| research-external | researcher | YES (WebSearch,WebFetch,context7) | -- |
| research-audit | analyst | YES | -- |
| plan-decomposition | analyst | YES | -- |
| plan-interface | analyst | YES | -- |
| plan-strategy | analyst | YES | -- |
| plan-verify-correctness | analyst | YES | -- |
| plan-verify-completeness | analyst | YES | -- |
| plan-verify-robustness | analyst | YES | -- |
| orchestration-decompose | Lead-direct | N/A | -- |
| orchestration-assign | Lead-direct | N/A | -- |
| orchestration-verify | analyst | YES | -- |
| execution-code | implementer | YES (Edit,Bash) | -- |
| execution-infra | infra-implementer | YES (Edit,Write) | -- |
| execution-impact | researcher | PARTIAL | **AGT-01** (no web tools used) |
| execution-cascade | implementer+infra-impl | YES | -- |
| execution-review | analyst | YES | -- |
| verify-structure | analyst | YES | -- |
| verify-content | analyst | YES | -- |
| verify-consistency | analyst | YES | -- |
| verify-quality | analyst | YES | -- |
| verify-cc-feasibility | analyst | YES | AGT-07 (claude-code-guide ghost) |
| delivery-pipeline | delivery-agent | YES (Bash,TaskUpdate,AskUser) | -- |
| task-management | pt-manager | YES (TaskCreate,TaskUpdate) | -- |
| pipeline-resume | Lead+analyst | YES | -- |
| manage-infra | analyst | YES | -- |
| manage-skills | analyst | PARTIAL | AGT-08 (cannot delete) |
| manage-codebase | analyst | YES | -- |
| self-improve | infra-implementer | YES (Edit,Write) | AGT-07 (claude-code-guide ghost) |

**Routing accuracy**: 32/35 skills have correct agent routing (91%). 3 have issues:
- execution-impact: wrong agent profile (researcher instead of analyst)
- manage-skills: incomplete capability (analyst cannot delete)
- 3 skills reference nonexistent claude-code-guide (fallback exists)

---

## Memory Configuration Assessment

| Agent | Memory | Rationale | Verdict |
|-------|--------|-----------|---------|
| analyst | project | Accumulates analysis patterns, past audit results | CORRECT |
| researcher | project | Remembers doc sources, MCP tool availability | CORRECT |
| implementer | project | Learns codebase patterns, test commands | CORRECT |
| infra-implementer | project | Remembers .claude/ structure decisions | CORRECT |
| delivery-agent | none | Stateless fork, each delivery is independent | CORRECT (but see AGT-03) |
| pt-manager | none | Stateless fork, Task API is the persistence layer | CORRECT |

---

## Model Selection Assessment

| Agent | Model | Task Complexity | Verdict |
|-------|-------|----------------|---------|
| analyst | opus (default) | High (multi-factor analysis, structured reasoning) | CORRECT |
| researcher | opus (default) | High (synthesis across multiple sources, judgment) | CORRECT |
| implementer | opus (default) | High (code writing, test reasoning, debugging) | CORRECT |
| infra-implementer | opus (default) | High (YAML precision, cross-file consistency) | CORRECT |
| delivery-agent | haiku | Low (git commands, file staging, MEMORY.md merge) | MOSTLY CORRECT (see AGT-03 re: MEMORY.md quality) |
| pt-manager | haiku | Low-Medium (Task API calls, ASCII formatting) | CORRECT |

---

## Prioritized Recommendations

1. **[HIGH] AGT-01**: Change execution-impact agent from researcher to analyst -- zero web tools used, analyst has all needed tools
2. **[HIGH] AGT-02**: Resolve P0-P2 "Lead-only" vs "spawn analyst (run_in_background)" ambiguity in CLAUDE.md Section 2.1
3. **[MEDIUM] AGT-07**: Decide on claude-code-guide: create it or make cc-reference cache the primary path
4. **[MEDIUM] AGT-04**: Add `mcp__tavily__search` to settings.json permissions
5. **[MEDIUM] AGT-03**: Evaluate delivery-agent model for MEMORY.md editing quality
6. **[LOW] AGT-10**: Add .claude/ modification restriction to delivery-agent body
7. **[LOW] AGT-14**: Add Korean language policy to fork agent bodies
