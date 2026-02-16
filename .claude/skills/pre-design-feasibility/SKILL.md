---
name: pre-design-feasibility
description: |
  [P0·PreDesign·Feasibility] Verifies CC native implementability per requirement. Checks cc-reference cache or spawns claude-code-guide. Scores feasible/partial/infeasible. Terminal pre-design skill.

  WHEN: After pre-design-validate PASS. Requirements complete but CC feasibility unconfirmed.
  DOMAIN: pre-design (skill 3 of 3).
  INPUT_FROM: pre-design-validate (validated, complete requirements).
  OUTPUT_TO: design-architecture (PASS) | pre-design-brainstorm (FAIL: scope re-negotiation).

  METHODOLOGY: (1) Map each requirement to CC native capability, (2) Check cc-reference cache, (3) Spawn claude-code-guide for gaps, (4) Score feasibility, (5) Produce verdict with alternatives.
  OUTPUT_FORMAT: L1 YAML (feasibility verdict per requirement), L2 CC capability mappings with alternatives.
user-invocable: true
disable-model-invocation: false
---

# Pre-Design — Feasibility

## Execution Model
- **TRIVIAL**: Lead-direct. Quick assessment against known CC capabilities.
- **STANDARD**: Launch researcher (run_in_background, maxTurns: 20) with claude-code-guide (if unavailable, use cc-reference cache in `memory/cc-reference/`) + web access for CC docs lookup.
- **COMPLEX**: Launch 2 background agents (run_in_background, maxTurns: 15-20). Split: core CC features vs MCP/plugin capabilities.

## Decision Points

### Tier Classification for Feasibility

| Tier | Indicator | Action |
|------|-----------|--------|
| TRIVIAL | 1-2 CC-native requirements, obvious feasibility (basic file ops, simple shell) | Lead checks cc-reference cache directly, no agent spawn |
| STANDARD | 3-6 requirements spanning multiple CC capability categories | Single researcher with cc-reference + claude-code-guide fallback |
| COMPLEX | 7+ requirements OR novel CC capability questions (undocumented hooks, new MCP integrations) | 2 researchers: core CC + MCP/plugin split |

### CC Capability Category Decision Tree

```
Requirement received
├─ Maps to known CC tool (Bash, Read, Edit, Write, Glob, Grep, Task, WebSearch)?
│  └─ YES → cc-reference cache → feasible (or spawn claude-code-guide if ambiguous)
├─ Involves hook timing, MCP integration, or undocumented behavior?
│  └─ YES → claude-code-guide (or WebSearch if unavailable, confidence: low)
├─ Involves external library, plugin, or third-party integration?
│  └─ YES → WebSearch first → verdict based on docs (infeasible if undocumented)
└─ No known category → Classify COMPLEX, full researcher with cc-reference + web
```

### Skip Conditions

| Condition | Action | Justification |
|-----------|--------|---------------|
| All requirements are basic file operations (Read/Edit/Write/Glob/Grep only) | Skip feasibility, proceed to design-architecture | These are core CC primitives, always feasible |
| All requirements verified feasible in a previous pipeline run (same session) | Skip feasibility, cite prior verdict | Avoid redundant research |
| User explicitly skips with justification | Skip feasibility, log user override in L1 output | User authority overrides process |

> **WARNING**: Skip conditions do NOT apply if requirements involve hooks, MCP, or agent spawning patterns. These categories always require explicit feasibility verification.

### Partial Feasibility Handling

```
Some requirements feasible, some partial/infeasible
├─ All infeasible have alternatives → PASS with alternatives → design-architecture
├─ Some infeasible without alternatives
│  ├─ Non-critical → Scope reduction: remove infeasible → PASS (reduced)
│  ├─ Critical → FAIL → pre-design-brainstorm for re-scoping
│  └─ Iteration < 3 → Re-iterate: brainstorm → validate → feasibility
└─ All infeasible → Terminal FAIL after 3 iterations → AskUserQuestion
```

### MCP Server Feasibility

| Check | Method | Failure Action |
|-------|--------|----------------|
| MCP server configured in settings.json | Read `/home/palantir/.claude/settings.json`, check `mcpServers` key | Mark MCP-dependent requirements as infeasible |
| MCP tool availability | Verify tool name exists in configured MCP server's tool list | Suggest alternative CC-native approach |
| MCP server permissions | Check `allowedTools` in settings.json for the specific MCP tool | Add permission to settings.json as alternative |
| MCP server health | Not checkable at design time | Flag as runtime risk, document in feasibility report |

## Methodology

### 1. Extract Technical Requirements
From validated requirement document, list each item needing CC implementation:
- File operations (Read, Edit, Write, Glob, Grep)
- Shell execution (Bash)
- Agent spawning (Task tool)
- Web access (WebSearch, WebFetch)
- MCP tools (sequential-thinking, context7, tavily)
- Hooks (SubagentStart, PreCompact, SessionStart, etc.)
- Skills (frontmatter, L2 body, argument-hint)

### 2. Map Requirements to CC Capabilities
For each requirement, identify the CC native feature that implements it.

#### Tier-Specific DPS Variations

**TRIVIAL** (Lead-direct, no agent spawn):
```
Lead check sequence (cc-reference cache at memory/cc-reference/):
1. Read native-fields.md   → requirement maps to known frontmatter field?
2. Read hook-events.md     → requirement involves a hook event?
3. Read context-loading.md → requirement depends on context loading?
4. Verdict based on cache content alone (no agent spawn)
```

**STANDARD** (single researcher, DPS delegation):
- **Context**: Paste the technical requirements list from Step 1 (each requirement with its CC capability category: file ops, shell, agents, web, MCP, hooks, skills). Include the cc-reference cache path: `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/` (files: native-fields.md, context-loading.md, hook-events.md, arguments-substitution.md).
- **Task**: "For each requirement, verify whether Claude Code natively supports it. Read the cc-reference cache files at the provided path first for CC-specific capability questions. If cc-reference is stale or ambiguous, use claude-code-guide agent for supplementary verification. For each requirement: provide feasibility verdict, the specific CC feature that enables it, and any limitations or workarounds needed."
- **Constraints**: Research-only (researcher agent with web access). Prioritize cc-reference cache for CC internals. Use claude-code-guide for supplementary verification when cc-reference is stale or ambiguous. Fall back to WebSearch for CC documentation if both unavailable.
- **Expected Output**: Per-requirement feasibility entry: requirement text, verdict (feasible/partial/infeasible), CC feature mapping (exact tool or API name), limitations if partial, alternative approach if infeasible, source of verdict (claude-code-guide / cc-reference / web docs).
- **Delivery**: Lead reads background agent output directly (P0-P1 mode, no SendMessage)

**Priority chain for STANDARD**: cc-reference cache (fastest, most reliable) → claude-code-guide agent (authoritative but slow) → WebSearch for CC docs (last resort, set confidence: low).

**COMPLEX** (two researchers, split strategy):

| Researcher | Scope | maxTurns | Focus |
|------------|-------|----------|-------|
| Researcher A | Core CC features (tools, skills, agents, context loading) | 15 | cc-reference cache + claude-code-guide |
| Researcher B | MCP/plugin capabilities, hook timing, external integrations | 20 | settings.json MCP config + WebSearch + claude-code-guide |

Both researchers receive the full requirements list but are assigned disjoint subsets. Lead merges results after both complete.

### 3. Assess Feasibility

| Verdict | Meaning | Action |
|---------|---------|--------|
| feasible | Direct CC native implementation exists | Include in design scope |
| partial | Possible with workarounds or limitations | Document workaround, flag as risk |
| infeasible | Cannot be done with CC native features | Propose alternative or escalate |

#### Scoring Rubric

| Criterion | Weight | Score Range | Description |
|-----------|--------|-------------|-------------|
| CC Native Support | 40% | 0-10 | Does a CC tool/feature directly implement the requirement? |
| Implementation Complexity | 25% | 0-10 | How many steps/workarounds needed? (10=trivial, 0=impossible) |
| Reliability | 20% | 0-10 | Will the implementation work consistently? (hooks, timing, etc.) |
| Maintenance Burden | 15% | 0-10 | Will this break on CC updates? (10=stable API, 0=undocumented hack) |

**Verdict thresholds**:
- **feasible**: weighted score >= 7.0
- **partial**: weighted score 4.0 - 6.9
- **infeasible**: weighted score < 4.0

### 4. Propose Alternatives for Infeasible Items
For each infeasible/partial item:
- Suggest scope reduction or alternative approach
- Identify if MCP server or plugin could solve it
- Estimate effort for workaround

#### Common Alternative Patterns

| Infeasible Requirement | CC Workaround | Effort |
|------------------------|---------------|--------|
| Real-time file watching | PostToolUse hook on file_edit events + /tmp log | Low |
| Cross-agent shared state | /tmp files or PERMANENT Task metadata (Read-Merge-Write) | Low |
| Persistent database | JSON files in project directory + Bash jq operations | Medium |
| GUI/visual output | HTML file generation + Bash `open` command | Medium |
| External API calls (non-web) | Bash curl commands with error handling | Medium |
| Background daemon process | Hook-based event system (SubagentStart/Stop triggers) | High |
| Binary file manipulation | Bash with external CLI tools (imagemagick, ffmpeg, etc.) | High |
| Interactive user prompts mid-execution | AskUserQuestion tool at gate checkpoints only | Low |

### 5. Gate Decision
- All feasible → PASS, forward to design-architecture
- Any infeasible without alternative → FAIL, return to brainstorm for scope reduction
- Max 3 revision iterations

**Terminal FAIL**: After 3 brainstorm→validate→feasibility iterations without resolution, report FAIL to Lead with all infeasible items listed. Lead escalates to user via AskUserQuestion:

```
AskUserQuestion wording (Terminal FAIL):

"Feasibility assessment failed after 3 iterations.

The following requirements cannot be implemented with Claude Code native features:
[list each infeasible requirement with attempted alternatives]

Options:
1. Proceed with known limitations (infeasible items removed from scope)
2. Modify requirements (return to brainstorm with adjusted constraints)
3. Abandon task (pipeline terminated)

Which option do you prefer?"
```

## Failure Handling

### claude-code-guide Unavailable

```
claude-code-guide unavailable
├─ cc-reference cache available → use cache verdicts (confidence: medium)
├─ Cache stale/missing → WebSearch for CC docs (confidence: low)
└─ Document fallback source in L2, set all fallback verdicts confidence: low
```

### cc-reference Cache Stale or Missing

| Situation | Action |
|-----------|--------|
| Cache files exist but outdated (>30 days since last refresh) | Trigger self-diagnose skill to refresh cc-reference, then retry feasibility |
| Cache files missing entirely | Trigger self-diagnose skill to create cc-reference, then retry feasibility |
| Self-diagnose also fails | Fall back to claude-code-guide + WebSearch (document cache gap) |

### Ambiguous Verdicts

When a requirement is "maybe feasible" (conflicting sources, uncertain CC behavior):
1. Classify as `partial` with explicit uncertainty flag
2. Document the conflicting evidence in L2 report
3. Recommend a proof-of-concept spike in execution phase (P7)
4. Add risk marker: `confidence: low, poc_recommended: true`

### All Requirements Infeasible

```
All infeasible
├─ Iteration < 3 → FAIL → pre-design-brainstorm (reduced scope) → re-iterate
├─ Iteration = 3 → Terminal FAIL → AskUserQuestion (see Gate Decision above)
└─ Pipeline blocked until user responds
```

### Pipeline Impact
- **Blocking**: Infeasible requirements halt the pipeline until resolved or descoped.
- **Non-blocking**: Partial verdicts with alternatives allow pipeline to proceed with risk flags.
- **Scope**: Only pre-design phase is affected. No downstream phases start until feasibility resolves.

## Anti-Patterns

| # | DO NOT | Reason |
|---|--------|--------|
| 1 | Trust stale CC reference as authoritative | cc-reference cache may lag behind CC updates. Always check cache freshness. If in doubt, supplement with claude-code-guide or WebSearch. |
| 2 | Skip feasibility for "obviously possible" requirements | Even simple requirements may have edge cases (e.g., file size limits, permission restrictions, hook ordering). Explicit verification prevents design-phase surprises. |
| 3 | Spawn claude-code-guide for every requirement | Batch questions into a single claude-code-guide session. Use cc-reference first for known capabilities. claude-code-guide is expensive (high token cost). |
| 4 | Mark partial as feasible | Partial means a workaround is needed. Must document the workaround approach, effort estimate, and risk. Treating partial as feasible hides implementation debt. |
| 5 | Loop indefinitely on infeasible items | Max 3 brainstorm→validate→feasibility iterations, then escalate to user via AskUserQuestion. Infinite loops waste pipeline budget. |
| 6 | Assess feasibility without version context | CC capabilities change across versions. Always note which CC version/model the assessment targets. A feature available in Opus 4.6 may not exist in earlier models. |

## Transitions

### Receives From

| Source Skill | Data Expected | Format |
|---|---|---|
| pre-design-validate | Validated, complete requirements | L1 YAML: `requirements[]`, `status: PASS` |

### Sends To

| Target Skill | Data Produced | Trigger Condition |
|---|---|---|
| design-architecture | Feasibility-confirmed requirements with CC capability mappings | PASS verdict (all feasible or partial with documented alternatives) |
| pre-design-brainstorm | Scope reduction request with infeasible items list | FAIL verdict (infeasible items without viable alternatives, iteration < 3) |

### Failure Routes

| Failure Type | Route To | Data Passed |
|---|---|---|
| All requirements infeasible after 3 iterations | User (AskUserQuestion) | Full infeasible list with attempted alternatives, iteration history |
| cc-reference + claude-code-guide both unavailable | self-diagnose (refresh cc-reference) | Stale cache details, missing file paths |
| CC Feasibility FAIL (critical infeasible, no alternatives) | pre-design-brainstorm | Infeasible items list with scope reduction request, iteration count |
| Partial verdicts with low confidence | design-architecture (proceed with risk flags) | Partial report with risk markers, `poc_recommended: true` items |

## Quality Gate
- Every requirement has explicit feasibility verdict (feasible/partial/infeasible)
- CC capability source cited for each verdict (cc-reference / claude-code-guide / web docs)
- No "unknown" verdicts remaining (all resolved to feasible/partial/infeasible)
- Infeasible items have documented alternatives or scope reduction
- Partial items have documented workaround approach with effort estimate
- claude-code-guide consulted for uncertain items (or fallback documented)
- Max 3 iteration limit enforced (iteration count tracked in L1 output)

## Output

### L1
```yaml
domain: pre-design
skill: feasibility
status: PASS|FAIL
iteration: 1
feasible: 0
partial: 0
infeasible: 0
items:
  - requirement: ""
    verdict: feasible|infeasible|partial
    confidence: high|medium|low
    cc_feature: ""
    source: cc-reference|claude-code-guide|web-docs
    alternative: ""
    poc_recommended: false
```

### L2
- Per-requirement feasibility verdict with CC capability mapping
- Scoring rubric results (weighted scores per requirement)
- Alternatives for infeasible items with effort estimates
- Workaround details for partial items
- claude-code-guide consultation summary (or fallback documentation)
- Risk flags for low-confidence verdicts
- Iteration history (if multiple passes)
