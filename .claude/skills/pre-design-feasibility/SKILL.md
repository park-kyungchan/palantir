---
name: pre-design-feasibility
description: |
  [P0·PreDesign·Feasibility] Claude Code native capabilities verification. Spawns claude-code-guide to check whether requirements can be implemented using CC native features (tools, skills, agents, hooks, MCP).

  WHEN: After pre-design-validate PASS. Requirements complete but CC feasibility unconfirmed.
  DOMAIN: pre-design (skill 3 of 3). Sequential: brainstorm -> validate -> feasibility. Terminal skill.
  INPUT_FROM: pre-design-validate (validated, complete requirements).
  OUTPUT_TO: design-architecture (feasibility-confirmed requirements ready for architecture).

  METHODOLOGY: (1) Extract technical requirements from validated document, (2) Spawn claude-code-guide to verify CC native implementability, (3) Analyze response for blockers, (4) If infeasible: identify alternatives or scope reduction, (5) If feasible: approve and pass to design. Max 3 iterations.
  OUTPUT_FORMAT: L1 YAML feasibility verdict per requirement, L2 markdown feasibility report with alternatives for infeasible items.
user-invocable: true
disable-model-invocation: false
---

# Pre-Design — Feasibility

## Execution Model
- **TRIVIAL**: Lead-direct. Quick assessment against known CC capabilities.
- **STANDARD**: Launch researcher (run_in_background) with claude-code-guide (if unavailable, use cc-reference cache in `memory/cc-reference/`) + web access for CC docs lookup.
- **COMPLEX**: Launch 2 background agents (run_in_background). Split: core CC features vs MCP/plugin capabilities.

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
For STANDARD/COMPLEX tiers, construct the delegation prompt for the researcher with:
- **Context**: Paste the technical requirements list from Step 1 (each requirement with its CC capability category: file ops, shell, agents, web, MCP, hooks, skills). Include the cc-reference cache path: `/home/palantir/.claude/projects/-home-palantir/memory/cc-reference/` (files: native-fields.md, context-loading.md, hook-events.md, arguments-substitution.md).
- **Task**: "For each requirement, verify whether Claude Code natively supports it. Use claude-code-guide agent first for CC-specific capability questions. If claude-code-guide is unavailable, read the cc-reference cache files at the provided path. For each requirement: provide feasibility verdict, the specific CC feature that enables it, and any limitations or workarounds needed."
- **Constraints**: Research-only (researcher agent with web access). Prioritize claude-code-guide over web search for CC internals. Fall back to cc-reference cache + WebSearch for CC documentation if claude-code-guide unavailable.
- **Expected Output**: Per-requirement feasibility entry: requirement text, verdict (feasible/partial/infeasible), CC feature mapping (exact tool or API name), limitations if partial, alternative approach if infeasible, source of verdict (claude-code-guide / cc-reference / web docs).

### 3. Assess Feasibility

| Verdict | Meaning |
|---------|---------|
| feasible | Direct CC native implementation exists |
| partial | Possible with workarounds or limitations |
| infeasible | Cannot be done with CC native features |

### 4. Propose Alternatives for Infeasible Items
For each infeasible/partial item:
- Suggest scope reduction or alternative approach
- Identify if MCP server or plugin could solve it
- Estimate effort for workaround

### 5. Gate Decision
- All feasible → PASS, forward to design-architecture
- Any infeasible without alternative → FAIL, return to brainstorm for scope reduction
- Max 3 revision iterations

**Terminal FAIL**: After 3 brainstorm→validate→feasibility iterations without resolution, report FAIL to Lead with all infeasible items listed. Lead escalates to user via AskUserQuestion: "proceed with known limitations" or "abandon task".

## Quality Gate
- Every requirement has explicit feasibility verdict
- Infeasible items have documented alternatives or scope reduction
- claude-code-guide consulted for uncertain items

## Output

### L1
```yaml
domain: pre-design
skill: feasibility
status: PASS|FAIL
feasible: 0
infeasible: 0
items:
  - requirement: ""
    verdict: feasible|infeasible|partial
    alternative: ""
```

### L2
- Per-requirement feasibility verdict with CC capability mapping
- Alternatives for infeasible items
- claude-code-guide consultation summary
