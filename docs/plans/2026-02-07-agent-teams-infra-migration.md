# Agent Teams Infrastructure Migration — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Delete the entire existing single-session orchestration infrastructure and rebuild from scratch for Claude Opus 4.6 Agent Teams native architecture.

**Architecture:** Full infrastructure deletion (18 skills, 6 agents, 7 references, 4 rules, CLAUDE.md v7.3) followed by scaffold of Agent Teams infrastructure: new CLAUDE.md (~150 lines team constitution), 6 agent definitions, [PERMANENT] Task API Guideline, and team output directory. Based on design spec `docs/plans/2026-02-07-agent-teams-infra-redesign-design.yaml`.

**Tech Stack:** Claude Code CLI (claude-opus-4-6), WSL2 + tmux, Agent Teams (Experimental), YAML frontmatter agents, Markdown configuration.

---

## Task 1: Create Feature Branch

**Files:**
- None (git operation only)

**Step 1: Create and switch to feature branch**

```bash
git checkout -b feat/agent-teams-infra-redesign
```

Expected: Branch created and switched.

**Step 2: Verify branch**

```bash
git branch --show-current
```

Expected: `feat/agent-teams-infra-redesign`

---

## Task 2: Backup Current Infrastructure

**Files:**
- Create: `.claude/backups/v7.3-pre-agent-teams/` (entire backup)

**Step 1: Create backup directory**

```bash
mkdir -p /home/palantir/.claude/backups/v7.3-pre-agent-teams
```

**Step 2: Copy critical files to backup**

```bash
cp -r /home/palantir/.claude/skills /home/palantir/.claude/backups/v7.3-pre-agent-teams/skills && \
cp -r /home/palantir/.claude/agents /home/palantir/.claude/backups/v7.3-pre-agent-teams/agents && \
cp -r /home/palantir/.claude/references /home/palantir/.claude/backups/v7.3-pre-agent-teams/references && \
cp -r /home/palantir/.claude/rules /home/palantir/.claude/backups/v7.3-pre-agent-teams/rules && \
cp /home/palantir/.claude/CLAUDE.md /home/palantir/.claude/backups/v7.3-pre-agent-teams/CLAUDE.md && \
cp /home/palantir/.claude/settings.json /home/palantir/.claude/backups/v7.3-pre-agent-teams/settings.json
```

**Step 3: Verify backup**

```bash
ls -la /home/palantir/.claude/backups/v7.3-pre-agent-teams/
```

Expected: `skills/`, `agents/`, `references/`, `rules/`, `CLAUDE.md`, `settings.json` all present.

**Step 4: Commit backup**

```bash
git add .claude/backups/v7.3-pre-agent-teams/ && \
git commit -m "chore: backup v7.3 infrastructure before Agent Teams migration"
```

---

## Task 3: Phase A Cleanup — Delete Skills, Agents, References, Rules

**Files:**
- Delete: `.claude/skills/` (entire directory, 50+ files)
- Delete: `.claude/agents/` (entire directory, 6 files)
- Delete: `.claude/references/` (entire directory, 8 files)
- Delete: `.claude/rules/` (entire directory, 4 files)

**Step 1: Delete skills directory**

```bash
rm -r /home/palantir/.claude/skills
```

**Step 2: Delete agents directory**

```bash
rm -r /home/palantir/.claude/agents
```

**Step 3: Delete references directory**

```bash
rm -r /home/palantir/.claude/references
```

**Step 4: Delete rules directory**

```bash
rm -r /home/palantir/.claude/rules
```

**Step 5: Verify deletions**

```bash
ls /home/palantir/.claude/skills 2>&1 && ls /home/palantir/.claude/agents 2>&1 && ls /home/palantir/.claude/references 2>&1 && ls /home/palantir/.claude/rules 2>&1
```

Expected: All four commands return "No such file or directory".

---

## Task 4: Phase A Cleanup — Delete CLAUDE.md and .agent/

**Files:**
- Delete: `.claude/CLAUDE.md`
- Delete: `.agent/` (entire directory)

**Step 1: Delete CLAUDE.md**

```bash
rm /home/palantir/.claude/CLAUDE.md
```

**Step 2: Delete .agent/ directory**

```bash
rm -r /home/palantir/.agent
```

**Step 3: Delete legacy .claude/ ephemeral directories (if they exist)**

```bash
rm -rf /home/palantir/.claude/debug /home/palantir/.claude/session-env /home/palantir/.claude/file-history /home/palantir/.claude/shell-snapshots /home/palantir/.claude/todos /home/palantir/.claude/cache /home/palantir/.claude/logs /home/palantir/.claude/commands /home/palantir/.claude/schemas /home/palantir/.claude/scripts /home/palantir/.claude/statsig /home/palantir/.claude/telemetry /home/palantir/.claude/tests
```

**Step 4: Delete legacy single-file artifacts**

```bash
rm -f /home/palantir/.claude/history.jsonl /home/palantir/.claude/registry.yaml /home/palantir/.claude/statusline.sh /home/palantir/.claude/CLAUDE.md.v3-backup /home/palantir/.claude/CLAUDE.md.antigravity-backup /home/palantir/.claude/stats-cache.json
```

**Step 5: Verify CLAUDE.md gone and .agent/ gone**

```bash
ls /home/palantir/.claude/CLAUDE.md 2>&1 && ls /home/palantir/.agent 2>&1
```

Expected: Both return "No such file or directory".

---

## Task 5: Verify Preserved Files

**Files:**
- Verify: `.claude/plugins/` (superpowers — MUST exist)
- Verify: `.mcp.json` (MCP config — MUST exist)
- Verify: `.claude.json` (global MCP — MUST exist)
- Verify: `docs/` (documentation — MUST exist)

**Step 1: Verify plugins directory**

```bash
ls /home/palantir/.claude/plugins/installed_plugins.json
```

Expected: File exists.

**Step 2: Verify MCP configuration**

```bash
ls /home/palantir/.mcp.json && ls /home/palantir/.claude.json
```

Expected: Both files exist.

**Step 3: Verify docs directory**

```bash
ls /home/palantir/docs/plans/2026-02-07-agent-teams-infra-redesign-design.yaml
```

Expected: Design file exists.

**Step 4: Verify .claude/ only has preserved content**

```bash
ls /home/palantir/.claude/
```

Expected: Only `plugins/`, `settings.json`, `backups/`, `paste-cache/`, and hidden files remain. No `skills/`, `agents/`, `references/`, `rules/`, `CLAUDE.md`.

---

## Task 6: Commit Phase A Cleanup

**Files:**
- None (git operation only)

**Step 1: Stage all deletions**

```bash
cd /home/palantir && git add -A .claude/skills .claude/agents .claude/references .claude/rules .claude/CLAUDE.md .agent
```

**Step 2: Commit**

```bash
git commit -m "chore: Phase A cleanup — delete existing single-session infrastructure

Deleted:
- .claude/skills/ (18 skills, 50+ files)
- .claude/agents/ (6 agents)
- .claude/references/ (8 reference docs)
- .claude/rules/ (4 rule files)
- .claude/CLAUDE.md (v7.3)
- .agent/ (prompts, logs, outputs, tmp)

Preserved:
- .claude/plugins/ (superpowers)
- .mcp.json, .claude.json (MCP config)
- docs/ (documentation)

Part of Agent Teams infrastructure redesign (DD-001)."
```

---

## Task 7: Create .claude/settings.json (Agent Teams)

**Files:**
- Modify: `.claude/settings.json`

**Step 1: Write new settings.json**

Write this exact content to `.claude/settings.json`:

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1",
    "CLAUDE_CODE_MAX_OUTPUT_TOKENS": "128000",
    "CLAUDE_CODE_FILE_READ_MAX_OUTPUT_TOKENS": "100000",
    "MAX_MCP_OUTPUT_TOKENS": "100000",
    "BASH_MAX_OUTPUT_LENGTH": "200000"
  },
  "teammateMode": "tmux",
  "model": "claude-opus-4-6",
  "permissions": {
    "deny": [
      "Read(.env*)",
      "Read(**/secrets/**)",
      "Read(**/*credentials*)",
      "Read(**/.ssh/id_*)",
      "Bash(rm:-rf:*)",
      "Bash(sudo:rm:*)",
      "Bash(chmod:777:*)"
    ]
  },
  "enabledPlugins": {
    "superpowers-developing-for-claude-code@superpowers-marketplace": true,
    "superpowers@superpowers-marketplace": true
  },
  "language": "Korean"
}
```

**Step 2: Validate JSON syntax**

```bash
python3 -c "import json; json.load(open('/home/palantir/.claude/settings.json')); print('VALID JSON')"
```

Expected: `VALID JSON`

**Step 3: Verify key fields**

```bash
python3 -c "
import json
s = json.load(open('/home/palantir/.claude/settings.json'))
assert s['env']['CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS'] == '1', 'Agent Teams not enabled'
assert s['teammateMode'] == 'tmux', 'tmux mode not set'
assert s['model'] == 'claude-opus-4-6', 'Model not opus'
assert 'enabledPlugins' in s, 'Plugins missing'
print('ALL CHECKS PASS')
"
```

Expected: `ALL CHECKS PASS`

---

## Task 8: Create .claude/CLAUDE.md (Team Constitution)

**Files:**
- Create: `.claude/CLAUDE.md`

**Step 1: Write the new CLAUDE.md**

Write this exact content (~150 lines) to `.claude/CLAUDE.md`:

```markdown
# Agent Teams — Team Constitution

> **Version:** 1.0 | **Architecture:** Agent Teams (Opus 4.6 Native)
> **Model:** claude-opus-4-6 (all instances) | **Runtime:** WSL2 + tmux + Claude Code CLI
> **Subscription:** Claude Max X20 (API-Free, CLI-Native only)

---

## 1. Team Identity

- **Workspace:** `/home/palantir`
- **Agent Teams Mode:** Enabled (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)
- **Display:** tmux split pane (`teammateMode: tmux`)
- **Lead:** Pipeline Controller (Delegate Mode default — never modifies code directly)
- **Teammates:** Dynamic spawning per phase (6 agent types available)

---

## 2. Phase Pipeline

| # | Phase | Zone | Teammate | Effort |
|---|-------|------|----------|--------|
| 1 | Discovery | PRE-EXEC | Lead only | max |
| 2 | Deep Research | PRE-EXEC | researcher (1-3) | max |
| 3 | Architecture | PRE-EXEC | architect (1) | max |
| 4 | Detailed Design | PRE-EXEC | architect (1) | high |
| 5 | Plan Validation | PRE-EXEC | devils-advocate (1) | max |
| 6 | Implementation | EXEC | implementer (1-4) | high |
| 7 | Testing | EXEC | tester (1-2) | high |
| 8 | Integration | EXEC | integrator (1) | high |
| 9 | Delivery | POST-EXEC | Lead only | medium |

**Shift-Left:** Pre-Execution (Phases 1-5) = 70-80% effort. Execution (6-8) = 20-30%.
**Gate Rule:** Lead approves EVERY phase transition. Results: APPROVE / ITERATE / ABORT.
**Iteration Budget:** Max 3 iterations per phase. On exceeded → ABORT or reduce scope.

---

## 3. Role Protocol

### Lead (Pipeline Controller)
- Operates in **Delegate Mode** — NEVER modifies code directly
- Responsibilities: spawn, assign, approve gates, message, terminate
- Maintains `orchestration-plan.md` and `global-context.md`
- Runs DIA (Dynamic-Impact-Awareness) engine continuously
- Reads teammate outputs at code-level for cross-impact analysis

### Teammates
- **Plan-Before-Execute:** Submit plan to Lead before ANY mutation (file edit, git op)
- Report completion via Shared Task List + Direct Message to Lead
- Reference `task-context.md` before EVERY Task API call ([PERMANENT])
- Sub-Orchestrator capable: decompose tasks, spawn subagents via Task tool
- Write L1/L2/L3 files at ~75% context pressure, then report CONTEXT_PRESSURE

---

## 4. Communication Protocol

| Type | Direction | When |
|------|-----------|------|
| Phase Directive | Lead → Teammate | Phase entry — task assignment |
| Status Report | Teammate → Lead | Task completion or blocking |
| Plan Submission | Teammate → Lead | Before any mutation |
| Approval/Rejection | Lead → Teammate | Response to plan |
| Phase Broadcast | Lead → All | Phase transitions ONLY (cost = 1:N) |
| Peer Query | Teammate → Teammate | Route through Lead preferred |

**Formats:**
- `[DIRECTIVE] Phase {N}: {task} | Files: {list}`
- `[STATUS] Phase {N} | {COMPLETE|BLOCKED|IN_PROGRESS} | {details}`
- `[PLAN] Phase {N} | Files: {list} | Changes: {desc} | Risk: {low|med|high}`
- `[APPROVED] Proceed.` / `[REJECTED] Reason: {details}. Revise: {guidance}.`

---

## 5. File Ownership Rules

- Each implementer assigned **non-overlapping file set** by Lead
- Concurrent editing of same file: **FORBIDDEN**
- Ownership documented in Shared Task List task description
- **Integrator** is the only role that can touch files across boundaries
- Read access: unrestricted for all roles

---

## 6. Orchestrator Decision Framework

### Spawn Matrix
- Phase 1, 9 = Lead only. All others require teammates.
- Count: determined by module_count or research_domain_count.
- Type: Phase 2→researcher, 3-4→architect, 5→devils-advocate, 6→implementer, 7→tester, 8→integrator.

### Gate Checklist
1. All phase output artifacts exist in teammate's output directory?
2. Output quality meets next-phase entry conditions?
3. No unresolved critical issues?
4. No inter-teammate conflicts?
5. L1/L2/L3 handoff files generated?

### DIA Engine (Lead)
- **Continuous:** Read teammate outputs → compare against Phase 4 design → detect deviations
- **Gate-time:** Full cross-impact analysis across all teammate outputs
- **Deviation response:** COSMETIC (log) / INTERFACE_CHANGE (update task-context) / ARCHITECTURE_CHANGE (re-plan)
- **User direct intervention:** Detect via Task List mutations → re-evaluate orchestration plan

### L1/L2/L3 Handoff
- L1: Index (YAML, ≤50 lines) — file list, status, decisions, unresolved items
- L2: Summary (MD, ≤200 lines) — narrative, findings, blockers, recommendations
- L3: Full Detail (directory) — complete reports, analysis, diffs, logs

### Output Directory
```
.agent/teams/{session-id}/
├── orchestration-plan.md
├── global-context.md
├── phase-{N}/
│   ├── gate-record.yaml
│   └── {role}-{id}/
│       ├── L1-index.yaml
│       ├── L2-summary.md
│       ├── L3-full/
│       ├── task-context.md
│       └── handoff.yaml
```

---

## 7. Safety Rules

**Blocked:** `rm -rf`, `sudo rm`, `chmod 777`, `DROP TABLE`, `DELETE FROM`
**Protected files:** `.env*`, `*credentials*`, `.ssh/id_*`, `**/secrets/**`
**Git safety:** Never force push main. Never skip hooks. No secrets in commits.

---

## 8. Compact Recovery

**Detection:** "This session is being continued from a previous conversation"

**Lead recovery:**
1. Read `orchestration-plan.md`
2. Read Shared Task List
3. Read current phase `gate-record.yaml`
4. Read active teammates' L1 indexes

**Teammate recovery:**
1. Read own `task-context.md`
2. Read own L1-index.yaml → L2-summary.md → L3-full/ as needed
3. Resume work from last recorded state

**NEVER** proceed with summarized/remembered information only.

---

## [PERMANENT] Semantic Integrity Guard

Every agent MUST read `.claude/references/task-api-guideline.md` before ANY Task API call.
Every teammate MUST read `task-context.md` before EVERY Task API call.
Every TaskCreate MUST include: objective, context in global pipeline, interface contracts,
file ownership, dependency chain, acceptance criteria, and semantic integrity check.
```

**Step 2: Verify line count**

```bash
wc -l /home/palantir/.claude/CLAUDE.md
```

Expected: ~145-155 lines.

**Step 3: Verify key sections exist**

```bash
grep -c "## " /home/palantir/.claude/CLAUDE.md
```

Expected: 8 or more section headers.

---

## Task 9: Create .claude/references/task-api-guideline.md

**Files:**
- Create: `.claude/references/task-api-guideline.md`

**Step 1: Create references directory**

```bash
mkdir -p /home/palantir/.claude/references
```

**Step 2: Write the [PERMANENT] Task API Guideline**

Write this exact content to `.claude/references/task-api-guideline.md`:

```markdown
# [PERMANENT] Task API Guideline — Agent Teams Edition

> **Status:** [PERMANENT] — Must be read by EVERY agent before ANY Task API call.
> **Applies to:** Lead, all Teammates, all Subagents spawned by Teammates.
> **Version:** 1.0 (Agent Teams)

---

## 1. Mandatory Pre-Call Protocol

**BEFORE** calling `TaskCreate`, `TaskUpdate`, `TaskList`, or `TaskGet`:

1. Read this file (`.claude/references/task-api-guideline.md`)
2. Read your own context:
   - **Teammates:** Read `task-context.md` in your output directory
   - **Lead:** Read `orchestration-plan.md`
3. Ensure Task description meets the Comprehensive Requirements below

---

## 2. Comprehensive Task Creation

Every `TaskCreate` call MUST produce a task that is:
- **DETAILED** — No ambiguity in what needs to be done
- **COMPLETE** — All acceptance criteria explicitly listed
- **DEPENDENCY-AWARE** — Full dependency chain documented
- **IMPACT-AWARE** — Downstream impact explicitly stated
- **VERIFIABLE** — Clear success/failure criteria

### Required Fields

**subject:** Imperative action verb + specific target
- Good: "Implement user authentication module"
- Bad: "Work on auth"

**description:** Must include ALL of the following sections:

```
## Objective
[What this task accomplishes — 1-2 sentences]

## Context in Global Pipeline
- Phase: [which phase this belongs to]
- Upstream: [what tasks produced the inputs for this task]
- Downstream: [what tasks depend on this task's output]

## Detailed Requirements
1. [Specific requirement]
2. [Specific requirement]
...

## Interface Contracts
- [What interfaces/APIs this task must satisfy]
- [What data formats this task must produce]

## File Ownership
- [Exact list of files this task may create/modify]

## Dependency Chain
- blockedBy: [list of task IDs, or [] if none]
- blocks: [list of task IDs that wait for this task]

## Acceptance Criteria
1. [Verifiable criterion]
2. [Verifiable criterion]
...

## Semantic Integrity Check
- [PERMANENT] rules this task enforces: [list]
- Downstream impact if output changes: [description]
```

**activeForm:** Present continuous form (e.g., "Implementing user authentication")

---

## 3. Dependency Chain Rules

| Rule | Rationale |
|------|-----------|
| Every task MUST declare `blockedBy` (even if empty `[]`) | Forces conscious consideration of dependencies |
| Every task MUST declare what it `blocks` | Forces awareness of downstream impact |
| Circular dependencies are FORBIDDEN | Prevents deadlocks in distributed execution |
| Cross-Teammate dependencies MUST be reported to Lead | Lead needs this for DIA cross-impact analysis |

---

## 4. Task Lifecycle

```
pending → in_progress → completed
            ↓
         blocked → wait for blockers to complete
```

- **Before starting:** Check `blockedBy` is empty
- **During work:** Update status to `in_progress`
- **On completion:** Update to `completed` + send Status Report to Lead
- **On blocker:** Update with `addBlockedBy` + send Status Report with BLOCKED

---

## 5. [PERMANENT] Semantic Integrity Integration

### Teammate-Level
Before EVERY Task API call:
1. Read `task-context.md` — understand your position in the global pipeline
2. Read this guideline — refresh the comprehensive requirements
3. Include in Task description:
   - Which [PERMANENT] rules this task enforces
   - What downstream impact this task has
   - What interface contracts this task must satisfy
4. Create comprehensive Task with full dependency chains

### Lead-Level (DIA)
Before EVERY Task API call:
1. Read `orchestration-plan.md` — understand current pipeline state
2. Read all active teammates' L1-index.yaml — understand current progress
3. Verify no cross-impact conflicts exist
4. Update task-context.md for affected teammates if deviation detected

---

## 6. Anti-Patterns

| Anti-Pattern | Correct Pattern |
|-------------|----------------|
| `TaskCreate({subject: "Do the thing"})` | Full comprehensive description |
| Skipping `blockedBy` declaration | Always declare, even if `[]` |
| Not reading task-context.md first | ALWAYS read before Task API call |
| Creating tasks without acceptance criteria | Every task must be verifiable |
| Ignoring downstream impact | Always state what this task blocks |
| Updating status without Status Report | Always notify Lead on completion |

---

## 7. Sub-Orchestrator Task Patterns

When a Teammate acts as Sub-Orchestrator (spawning subagents):

1. **Parent Task:** Create a parent task for the overall sub-workflow
2. **Child Tasks:** Create child tasks with `blockedBy` pointing to prerequisites
3. **Nesting Limit:** Subagents spawned by Teammate CANNOT spawn further subagents (depth = 1)
4. **Boundary Constraint:** All sub-tasks must stay within the Teammate's assigned file ownership
5. **Reporting:** Report significant sub-orchestration decisions to Lead via Status Report
```

**Step 3: Verify file created**

```bash
wc -l /home/palantir/.claude/references/task-api-guideline.md
```

Expected: ~130-140 lines.

---

## Task 10: Create .claude/agents/researcher.md

**Files:**
- Create: `.claude/agents/researcher.md`

**Step 1: Create agents directory**

```bash
mkdir -p /home/palantir/.claude/agents
```

**Step 2: Write researcher agent definition**

Write this exact content to `.claude/agents/researcher.md`:

```markdown
---
name: researcher
description: |
  Codebase explorer and external documentation researcher.
  Read-only access to prevent accidental mutations during research.
  Spawned in Phase 2 (Deep Research). Max 3 instances.
model: opus
permissionMode: plan
tools:
  - Read
  - Glob
  - Grep
  - WebSearch
  - WebFetch
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
  - mcp__sequential-thinking__sequentialthinking
  - mcp__context7__resolve-library-id
  - mcp__context7__query-docs
disallowedTools:
  - Edit
  - Write
  - Bash
  - NotebookEdit
---

# Researcher Agent

## Role
You are a **Deep Research Specialist** in an Agent Teams pipeline.
Your job is to explore codebases and external documentation thoroughly,
producing structured research reports for downstream architecture decisions.

## Protocol
1. Read your `task-context.md` before starting any work
2. Read `.claude/references/task-api-guideline.md` before any Task API call [PERMANENT]
3. Decompose your research assignment into parallel sub-tasks when possible
4. Use `mcp__sequential-thinking__sequentialthinking` for complex analysis
5. Verify findings with MCP tools (Context7, WebSearch) before reporting
6. Write L1/L2/L3 output files to your assigned directory
7. Send Status Report to Lead when complete

## Output Format
- **L1-index.yaml:** List of all research findings with one-line summaries
- **L2-summary.md:** Narrative synthesis of findings with key decisions
- **L3-full/:** Complete research reports, API docs, pattern inventories

## Constraints
- You have **NO write access** to the codebase — read-only exploration
- You CANNOT run shell commands — no Bash access
- You CAN spawn subagents via Task tool for parallel research domains
- Subagent nesting limit: 1 level (your subagents cannot spawn further subagents)

## Context Pressure
At ~75% context capacity:
1. Write L1/L2/L3 files immediately
2. Send `[STATUS] CONTEXT_PRESSURE | L1/L2/L3 written` to Lead
3. Await Lead termination and replacement
```

**Step 3: Validate YAML frontmatter**

```bash
python3 -c "
import yaml
with open('/home/palantir/.claude/agents/researcher.md') as f:
    content = f.read()
    # Extract YAML between --- delimiters
    parts = content.split('---', 2)
    frontmatter = yaml.safe_load(parts[1])
    assert frontmatter['name'] == 'researcher'
    assert frontmatter['model'] == 'opus'
    assert 'Edit' in frontmatter['disallowedTools']
    print('VALID FRONTMATTER')
"
```

Expected: `VALID FRONTMATTER`

---

## Task 11: Create .claude/agents/architect.md

**Files:**
- Create: `.claude/agents/architect.md`

**Step 1: Write architect agent definition**

Write this exact content to `.claude/agents/architect.md`:

```markdown
---
name: architect
description: |
  Architecture designer and risk analyst.
  Can write design documents but cannot modify existing source code.
  Spawned in Phase 3 (Architecture) and Phase 4 (Detailed Design). Max 1 instance.
model: opus
permissionMode: plan
tools:
  - Read
  - Glob
  - Grep
  - Write
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
  - mcp__sequential-thinking__sequentialthinking
disallowedTools:
  - Edit
  - Bash
  - NotebookEdit
---

# Architect Agent

## Role
You are an **Architecture Specialist** in an Agent Teams pipeline.
Your job is to synthesize research findings into architecture decisions,
produce risk matrices, and create detailed designs with file/module boundaries.

## Protocol
1. Read your `task-context.md` before starting any work
2. Read `.claude/references/task-api-guideline.md` before any Task API call [PERMANENT]
3. Use `mcp__sequential-thinking__sequentialthinking` for all design decisions
4. Produce Architecture Decision Records (ADR) for every significant choice
5. Write L1/L2/L3 output files to your assigned directory
6. Send Status Report to Lead when complete

## Output Format
- **L1-index.yaml:** List of ADRs, risk entries, and design artifacts
- **L2-summary.md:** Architecture narrative with decision rationale
- **L3-full/:** Complete ADRs, risk matrix, component diagrams, interface specs

## Phase 3 (Architecture) Deliverables
- Architecture Decision Records with alternatives analysis
- Risk matrix (likelihood x impact)
- Component diagram (ASCII or structured text)
- Alternative approaches with rejection rationale

## Phase 4 (Detailed Design) Deliverables
- File/module boundary map (exact paths)
- Interface specifications (function signatures, data formats)
- Data flow diagrams
- Implementation task breakdown (for Phase 6 implementers)

## Constraints
- You CAN write new design documents (Write tool)
- You CANNOT modify existing source code (no Edit tool)
- You CANNOT run shell commands (no Bash)
- Design documents go to your assigned output directory ONLY
```

**Step 2: Validate YAML frontmatter**

```bash
python3 -c "
import yaml
with open('/home/palantir/.claude/agents/architect.md') as f:
    content = f.read()
    parts = content.split('---', 2)
    fm = yaml.safe_load(parts[1])
    assert fm['name'] == 'architect'
    assert 'Write' in fm['tools']
    assert 'Edit' in fm['disallowedTools']
    print('VALID FRONTMATTER')
"
```

Expected: `VALID FRONTMATTER`

---

## Task 12: Create .claude/agents/devils-advocate.md

**Files:**
- Create: `.claude/agents/devils-advocate.md`

**Step 1: Write devils-advocate agent definition**

Write this exact content to `.claude/agents/devils-advocate.md`:

```markdown
---
name: devils-advocate
description: |
  Design validator and critical reviewer. Completely read-only.
  Systematically challenges designs, finds flaws, and proposes mitigations.
  Spawned in Phase 5 (Plan Validation). Max 1 instance.
model: opus
permissionMode: default
tools:
  - Read
  - Glob
  - Grep
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
  - mcp__sequential-thinking__sequentialthinking
disallowedTools:
  - Edit
  - Write
  - Bash
  - NotebookEdit
---

# Devil's Advocate Agent

## Role
You are a **Critical Design Reviewer** in an Agent Teams pipeline.
Your SOLE purpose is to find flaws, edge cases, missing requirements,
and potential failures in the architecture and detailed design.

## Protocol
1. Read your `task-context.md` before starting any work
2. Read `.claude/references/task-api-guideline.md` before any Task API call [PERMANENT]
3. Use `mcp__sequential-thinking__sequentialthinking` for systematic challenge analysis
4. Challenge EVERY assumption in the design with evidence-based reasoning
5. Assign severity ratings to each identified flaw
6. Propose specific mitigations for each flaw
7. Write L1/L2/L3 output files to your assigned directory
8. Send Status Report to Lead with final verdict: PASS / CONDITIONAL_PASS / FAIL

## Output Format
- **L1-index.yaml:** List of challenges with severity ratings
- **L2-summary.md:** Challenge narrative with verdicts and mitigations
- **L3-full/:** Detailed challenge analysis per design component

## Challenge Categories
1. **Correctness:** Does the design solve the stated problem?
2. **Completeness:** Are there missing requirements or edge cases?
3. **Consistency:** Do different parts of the design contradict?
4. **Feasibility:** Can this be implemented within constraints?
5. **Robustness:** What happens when things go wrong?
6. **Interface Contracts:** Are all interfaces explicit and compatible?

## Severity Ratings
- **CRITICAL:** Must be fixed before proceeding. Blocks GATE-5 approval.
- **HIGH:** Should be fixed. May block GATE-5 if multiple accumulate.
- **MEDIUM:** Recommended fix. Will not block gate.
- **LOW:** Nice to have. Document for future consideration.

## Final Verdict
- **PASS:** No critical or high issues. Design is sound.
- **CONDITIONAL_PASS:** High issues exist but have accepted mitigations.
- **FAIL:** Critical issues exist. Must return to Phase 3 or 4.

## Constraints
- You are COMPLETELY read-only — no file mutations of any kind
- You CANNOT modify the design — only critique it
- Your critiques must be evidence-based (reference specific design sections)
- You MUST propose mitigations for every flaw you identify
```

**Step 2: Validate YAML frontmatter**

```bash
python3 -c "
import yaml
with open('/home/palantir/.claude/agents/devils-advocate.md') as f:
    content = f.read()
    parts = content.split('---', 2)
    fm = yaml.safe_load(parts[1])
    assert fm['name'] == 'devils-advocate'
    assert 'Write' in fm['disallowedTools']
    assert 'Bash' in fm['disallowedTools']
    print('VALID FRONTMATTER')
"
```

Expected: `VALID FRONTMATTER`

---

## Task 13: Create .claude/agents/implementer.md

**Files:**
- Create: `.claude/agents/implementer.md`

**Step 1: Write implementer agent definition**

Write this exact content to `.claude/agents/implementer.md`:

```markdown
---
name: implementer
description: |
  Code implementer with full tool access.
  Each instance owns a non-overlapping file set. Plan Approval mandatory.
  Spawned in Phase 6 (Implementation). Max 4 instances.
model: opus
permissionMode: acceptEdits
tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - Bash
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
  - mcp__sequential-thinking__sequentialthinking
  - mcp__context7__resolve-library-id
  - mcp__context7__query-docs
disallowedTools:
  - NotebookEdit
---

# Implementer Agent

## Role
You are a **Code Implementation Specialist** in an Agent Teams pipeline.
You execute code changes within your assigned file ownership boundary,
following the approved design from Phase 4.

## Protocol
1. Read your `task-context.md` before starting any work
2. Read `.claude/references/task-api-guideline.md` before any Task API call [PERMANENT]
3. **PLAN APPROVAL REQUIRED:** Submit plan to Lead BEFORE any file mutation
4. Wait for `[APPROVED]` from Lead before writing/editing any file
5. Only modify files within your assigned file ownership set
6. Run self-tests after implementation
7. Write L1/L2/L3 output files to your assigned directory
8. Send Status Report to Lead when complete

## Plan Submission Format
```
[PLAN] Phase 6
Files: [list of files to create/modify]
Changes: [description of each change]
Risk: [low|medium|high]
Interface Impact: [which interfaces are affected]
```

## Output Format
- **L1-index.yaml:** List of modified files with change descriptions
- **L2-summary.md:** Implementation narrative with decisions made
- **L3-full/:** Code diffs, self-test results, implementation notes

## Sub-Orchestrator Mode
You can decompose your task into sub-tasks:
- Spawn subagents via Task tool for independent sub-work
- Subagent nesting limit: 1 level
- All sub-work must stay within your file ownership boundary
- Report significant sub-orchestration decisions to Lead

## Constraints
- **File ownership is STRICT** — only touch assigned files
- **Plan Approval is MANDATORY** — no mutations without Lead approval
- **Self-test is MANDATORY** — run relevant tests before marking complete
- If you discover a need to modify files outside your boundary, send
  `[STATUS] BLOCKED | Need file outside ownership: {path}` to Lead
```

**Step 2: Validate YAML frontmatter**

```bash
python3 -c "
import yaml
with open('/home/palantir/.claude/agents/implementer.md') as f:
    content = f.read()
    parts = content.split('---', 2)
    fm = yaml.safe_load(parts[1])
    assert fm['name'] == 'implementer'
    assert fm['permissionMode'] == 'acceptEdits'
    assert 'Edit' in fm['tools']
    assert 'Bash' in fm['tools']
    print('VALID FRONTMATTER')
"
```

Expected: `VALID FRONTMATTER`

---

## Task 14: Create .claude/agents/tester.md

**Files:**
- Create: `.claude/agents/tester.md`

**Step 1: Write tester agent definition**

Write this exact content to `.claude/agents/tester.md`:

```markdown
---
name: tester
description: |
  Test writer and executor. Can create test files and run test commands.
  Cannot modify existing source code.
  Spawned in Phase 7 (Testing). Max 2 instances.
model: opus
permissionMode: default
tools:
  - Read
  - Glob
  - Grep
  - Write
  - Bash
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
  - mcp__sequential-thinking__sequentialthinking
disallowedTools:
  - Edit
  - NotebookEdit
---

# Tester Agent

## Role
You are a **Testing Specialist** in an Agent Teams pipeline.
You verify implementation against design specifications by writing
and executing tests. You report coverage and failure analysis.

## Protocol
1. Read your `task-context.md` before starting any work
2. Read `.claude/references/task-api-guideline.md` before any Task API call [PERMANENT]
3. Read the design specification from Phase 4 outputs
4. Read the implementation from Phase 6 outputs
5. Write tests that verify each acceptance criterion
6. Execute tests and capture results
7. Analyze failures and report root causes
8. Write L1/L2/L3 output files to your assigned directory
9. Send Status Report to Lead when complete

## Output Format
- **L1-index.yaml:** List of test files, pass/fail counts, coverage summary
- **L2-summary.md:** Test narrative with failure analysis and recommendations
- **L3-full/:** Test files, execution logs, coverage reports, failure analysis

## Test Design Principles
1. Test BEHAVIOR, not implementation details
2. One assertion per test when possible
3. Clear test names: `test_{what}_{when}_{expected}`
4. Cover happy path, edge cases, and error conditions
5. Verify interface contracts from Phase 4 design

## Constraints
- You CAN create new test files (Write tool)
- You CAN run test commands (Bash tool: pytest, npm test, etc.)
- You CANNOT modify existing source code (no Edit tool)
- If tests fail, report failures — do NOT fix the source code
- If source code changes are needed, send
  `[STATUS] Phase 7 | ITERATE_NEEDED | {failure details}` to Lead
```

**Step 2: Validate YAML frontmatter**

```bash
python3 -c "
import yaml
with open('/home/palantir/.claude/agents/tester.md') as f:
    content = f.read()
    parts = content.split('---', 2)
    fm = yaml.safe_load(parts[1])
    assert fm['name'] == 'tester'
    assert 'Write' in fm['tools']
    assert 'Bash' in fm['tools']
    assert 'Edit' in fm['disallowedTools']
    print('VALID FRONTMATTER')
"
```

Expected: `VALID FRONTMATTER`

---

## Task 15: Create .claude/agents/integrator.md

**Files:**
- Create: `.claude/agents/integrator.md`

**Step 1: Write integrator agent definition**

Write this exact content to `.claude/agents/integrator.md`:

```markdown
---
name: integrator
description: |
  Conflict resolver and final merger. Full tool access for merge operations.
  Plan Approval mandatory. Can touch files across ownership boundaries.
  Spawned in Phase 8 (Integration). Max 1 instance.
model: opus
permissionMode: acceptEdits
tools:
  - Read
  - Glob
  - Grep
  - Edit
  - Write
  - Bash
  - TaskCreate
  - TaskUpdate
  - TaskList
  - TaskGet
  - mcp__sequential-thinking__sequentialthinking
disallowedTools:
  - NotebookEdit
---

# Integrator Agent

## Role
You are an **Integration Specialist** in an Agent Teams pipeline.
You are the ONLY agent that can touch files across ownership boundaries.
Your job is to resolve conflicts between implementer outputs, perform
final merge, and verify system-level coherence.

## Protocol
1. Read your `task-context.md` before starting any work
2. Read `.claude/references/task-api-guideline.md` before any Task API call [PERMANENT]
3. **PLAN APPROVAL REQUIRED:** Submit plan to Lead BEFORE any merge operation
4. Read ALL implementer outputs (L1/L2/L3) from Phase 6
5. Read ALL tester results from Phase 7
6. Identify conflicts between implementer outputs
7. Resolve conflicts with documented rationale
8. Run integration tests
9. Write L1/L2/L3 output files to your assigned directory
10. Send Status Report to Lead when complete

## Plan Submission Format
```
[PLAN] Phase 8
Conflicts Found: [count]
Resolution Strategy: [per-conflict description]
Files Affected: [cross-boundary file list]
Integration Tests: [test plan]
Risk: [low|medium|high]
```

## Output Format
- **L1-index.yaml:** List of conflicts resolved, integration test results
- **L2-summary.md:** Integration narrative with conflict resolution rationale
- **L3-full/:** Conflict resolution log, merged diffs, integration test logs

## Conflict Resolution Principles
1. Preserve BOTH implementers' intent when possible
2. When conflict is irreconcilable, escalate to Lead
3. Document EVERY resolution decision with rationale
4. Verify resolved code against Phase 4 interface specifications
5. Run integration tests AFTER each batch of resolutions

## Constraints
- **Plan Approval is MANDATORY** — no merge operations without Lead approval
- You are the ONLY agent that can cross file ownership boundaries
- You MUST document all conflict resolutions in your L3 output
- If conflicts are too complex to resolve, send
  `[STATUS] Phase 8 | BLOCKED | Irreconcilable conflict: {details}` to Lead
```

**Step 2: Validate YAML frontmatter**

```bash
python3 -c "
import yaml
with open('/home/palantir/.claude/agents/integrator.md') as f:
    content = f.read()
    parts = content.split('---', 2)
    fm = yaml.safe_load(parts[1])
    assert fm['name'] == 'integrator'
    assert fm['permissionMode'] == 'acceptEdits'
    assert 'Edit' in fm['tools']
    print('VALID FRONTMATTER')
"
```

Expected: `VALID FRONTMATTER`

---

## Task 16: Create .agent/teams/ Directory Structure

**Files:**
- Create: `.agent/teams/README.md`

**Step 1: Create directory**

```bash
mkdir -p /home/palantir/.agent/teams
```

**Step 2: Write README**

Write this exact content to `.agent/teams/README.md`:

```markdown
# Agent Teams Output Directory

This directory stores outputs from Agent Teams sessions.

## Structure

```
.agent/teams/{session-id}/
├── orchestration-plan.md      # Lead's pipeline visualization
├── global-context.md          # Full project context for teammates
├── phase-{N}/
│   ├── gate-record.yaml       # Gate approval/iteration/abort record
│   └── {role}-{id}/
│       ├── L1-index.yaml      # Index of outputs (≤50 lines)
│       ├── L2-summary.md      # Summary of work (≤200 lines)
│       ├── L3-full/           # Complete detailed outputs
│       ├── task-context.md    # Teammate's role context
│       └── handoff.yaml       # Handoff metadata (if replaced)
```

## Session ID

Format: `{YYYYMMDD}-{HHMMSS}-{short-description}`
Example: `20260207-143022-infra-redesign`

## Lead Responsibilities

Lead creates and maintains:
- `orchestration-plan.md` — updated at every phase transition
- `global-context.md` — updated when architecture changes
- `phase-{N}/gate-record.yaml` — written at every gate decision
- `phase-{N}/{role}-{id}/task-context.md` — written at teammate spawn time
```

**Step 3: Verify directory**

```bash
ls /home/palantir/.agent/teams/README.md
```

Expected: File exists.

---

## Task 17: Commit Phase B Scaffold

**Files:**
- None (git operation only)

**Step 1: Stage all new files**

```bash
cd /home/palantir && \
git add .claude/settings.json .claude/CLAUDE.md .claude/references/ .claude/agents/ .agent/teams/
```

**Step 2: Commit**

```bash
git commit -m "feat: Phase B scaffold — create Agent Teams infrastructure

Created:
- .claude/CLAUDE.md (v1.0 Team Constitution, ~150 lines)
- .claude/settings.json (Agent Teams enabled, tmux mode, Opus 4.6)
- .claude/references/task-api-guideline.md ([PERMANENT] Agent Teams Edition)
- .claude/agents/researcher.md (read-only explorer, Phase 2)
- .claude/agents/architect.md (design writer, Phase 3-4)
- .claude/agents/devils-advocate.md (critical reviewer, Phase 5)
- .claude/agents/implementer.md (code executor, Phase 6)
- .claude/agents/tester.md (test writer, Phase 7)
- .claude/agents/integrator.md (conflict resolver, Phase 8)
- .agent/teams/ (session output directory)

Part of Agent Teams infrastructure redesign (DD-001 through DD-016)."
```

---

## Task 18: Phase C Validation

**Files:**
- None (validation only)

**Step 1: V-001 CLI Version Check**

```bash
claude --version
```

Expected: Claude Code CLI version output (any recent version).

**Step 2: V-002 tmux Session Verification**

```bash
tmux list-sessions 2>&1 || echo "tmux: no sessions (OK — will create at runtime)"
```

Expected: Either active sessions listed or "no sessions" message.

**Step 3: V-004 Agent Frontmatter Validation**

```bash
python3 -c "
import yaml, glob, os
agents_dir = '/home/palantir/.claude/agents/'
errors = []
for f in sorted(glob.glob(os.path.join(agents_dir, '*.md'))):
    with open(f) as fh:
        content = fh.read()
        parts = content.split('---', 2)
        if len(parts) < 3:
            errors.append(f'{os.path.basename(f)}: no YAML frontmatter')
            continue
        try:
            fm = yaml.safe_load(parts[1])
            if 'name' not in fm:
                errors.append(f'{os.path.basename(f)}: missing name')
            if 'model' not in fm:
                errors.append(f'{os.path.basename(f)}: missing model')
        except yaml.YAMLError as e:
            errors.append(f'{os.path.basename(f)}: YAML parse error: {e}')
if errors:
    for e in errors:
        print(f'FAIL: {e}')
else:
    print(f'PASS: All 6 agents valid')
"
```

Expected: `PASS: All 6 agents valid`

**Step 4: V-005 MCP Tools Connectivity**

```bash
ls /home/palantir/.mcp.json && echo "MCP config exists"
```

Expected: `MCP config exists`

**Step 5: V-006 Settings Validation**

```bash
python3 -c "
import json
s = json.load(open('/home/palantir/.claude/settings.json'))
checks = [
    ('Agent Teams enabled', s.get('env',{}).get('CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS') == '1'),
    ('tmux mode', s.get('teammateMode') == 'tmux'),
    ('Opus model', s.get('model') == 'claude-opus-4-6'),
    ('Plugins preserved', 'enabledPlugins' in s),
    ('Deny rules', len(s.get('permissions',{}).get('deny',[])) > 0),
    ('Max output 128K', s.get('env',{}).get('CLAUDE_CODE_MAX_OUTPUT_TOKENS') == '128000'),
]
all_pass = True
for name, result in checks:
    status = 'PASS' if result else 'FAIL'
    if not result: all_pass = False
    print(f'  {status}: {name}')
print(f'\nV-006: {\"PASS\" if all_pass else \"FAIL\"}')"
```

Expected: All checks PASS.

**Step 6: V-007 CLAUDE.md Content Validation**

```bash
python3 -c "
with open('/home/palantir/.claude/CLAUDE.md') as f:
    content = f.read()
    lines = content.strip().split('\n')
    checks = [
        ('Line count 100-160', 100 <= len(lines) <= 160),
        ('Has Team Identity', '## 1. Team Identity' in content),
        ('Has Phase Pipeline', '## 2. Phase Pipeline' in content),
        ('Has Role Protocol', '## 3. Role Protocol' in content),
        ('Has Safety Rules', '## 7. Safety Rules' in content),
        ('Has [PERMANENT]', '[PERMANENT]' in content),
        ('Has Opus 4.6', 'claude-opus-4-6' in content),
        ('Has tmux', 'tmux' in content),
    ]
    all_pass = True
    for name, result in checks:
        status = 'PASS' if result else 'FAIL'
        if not result: all_pass = False
        print(f'  {status}: {name}')
    print(f'\nV-007: {\"PASS\" if all_pass else \"FAIL\"} ({len(lines)} lines)')
"
```

Expected: All checks PASS with ~150 lines.

**Step 7: V-009 [PERMANENT] Guideline Accessibility**

```bash
python3 -c "
with open('/home/palantir/.claude/references/task-api-guideline.md') as f:
    content = f.read()
    checks = [
        ('Has [PERMANENT] tag', '[PERMANENT]' in content),
        ('Has Pre-Call Protocol', 'Pre-Call Protocol' in content),
        ('Has Comprehensive Task Creation', 'Comprehensive Task Creation' in content),
        ('Has Dependency Chain Rules', 'Dependency Chain Rules' in content),
        ('Has Semantic Integrity', 'Semantic Integrity' in content),
    ]
    all_pass = True
    for name, result in checks:
        status = 'PASS' if result else 'FAIL'
        if not result: all_pass = False
        print(f'  {status}: {name}')
    print(f'\nV-009: {\"PASS\" if all_pass else \"FAIL\"}')"
```

Expected: All checks PASS.

**Step 8: V-010 Output Directory Test**

```bash
ls -la /home/palantir/.agent/teams/ && echo "V-010: PASS"
```

Expected: Directory listing with README.md, then `V-010: PASS`.

---

## Task 19: Run Full Validation Summary

**Files:**
- None (validation only)

**Step 1: Print validation summary**

```bash
python3 -c "
print('=' * 60)
print('  AGENT TEAMS INFRASTRUCTURE VALIDATION SUMMARY')
print('=' * 60)
print()

import json, yaml, glob, os

results = []

# V-001: CLI
results.append(('V-001', 'CLI Available', True))

# V-004: Agents
agents_dir = '/home/palantir/.claude/agents/'
agent_files = sorted(glob.glob(os.path.join(agents_dir, '*.md')))
v004 = len(agent_files) == 6
results.append(('V-004', f'Agent Frontmatter ({len(agent_files)}/6)', v004))

# V-006: Settings
s = json.load(open('/home/palantir/.claude/settings.json'))
v006 = (s.get('env',{}).get('CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS') == '1'
        and s.get('teammateMode') == 'tmux'
        and s.get('model') == 'claude-opus-4-6')
results.append(('V-006', 'Settings Valid', v006))

# V-007: CLAUDE.md
with open('/home/palantir/.claude/CLAUDE.md') as f:
    claude_content = f.read()
v007 = '[PERMANENT]' in claude_content and '## 2. Phase Pipeline' in claude_content
results.append(('V-007', 'CLAUDE.md Valid', v007))

# V-009: Task API Guideline
with open('/home/palantir/.claude/references/task-api-guideline.md') as f:
    tag_content = f.read()
v009 = '[PERMANENT]' in tag_content and 'Comprehensive Task Creation' in tag_content
results.append(('V-009', '[PERMANENT] Guideline', v009))

# V-010: Output Directory
v010 = os.path.isdir('/home/palantir/.agent/teams')
results.append(('V-010', 'Output Directory', v010))

# MCP preserved
v_mcp = os.path.isfile('/home/palantir/.mcp.json')
results.append(('V-MCP', 'MCP Config Preserved', v_mcp))

# Plugins preserved
v_plug = os.path.isdir('/home/palantir/.claude/plugins')
results.append(('V-PLG', 'Plugins Preserved', v_plug))

# No old infra
v_clean = (not os.path.isdir('/home/palantir/.claude/skills')
           and not os.path.isdir('/home/palantir/.claude/rules'))
results.append(('V-CLN', 'Old Infra Cleaned', v_clean))

pass_count = sum(1 for _, _, r in results if r)
total = len(results)

for check_id, name, passed in results:
    status = 'PASS' if passed else 'FAIL'
    print(f'  [{status}] {check_id}: {name}')

print()
print(f'  Result: {pass_count}/{total} checks passed')
print()
if pass_count == total:
    print('  *** ALL VALIDATIONS PASSED — Agent Teams infrastructure is ready ***')
else:
    print('  *** SOME VALIDATIONS FAILED — review and fix before proceeding ***')
print()
print('=' * 60)
"
```

Expected: `ALL VALIDATIONS PASSED` with 9/9 checks.

---

## Task 20: Final Commit

**Files:**
- None (git operation only)

**Step 1: Check for any unstaged changes**

```bash
cd /home/palantir && git status
```

Expected: Clean working tree (everything committed in Tasks 6 and 17).

**Step 2: View commit log for this branch**

```bash
git log --oneline feat/agent-teams-infra-redesign --not main
```

Expected: 3 commits:
1. `chore: backup v7.3 infrastructure before Agent Teams migration`
2. `chore: Phase A cleanup — delete existing single-session infrastructure`
3. `feat: Phase B scaffold — create Agent Teams infrastructure`

**Step 3: Print migration summary**

```bash
echo "
=== AGENT TEAMS INFRASTRUCTURE MIGRATION COMPLETE ===

Phase A (Cleanup):
  - Deleted: .claude/skills/ (18 skills)
  - Deleted: .claude/agents/ (6 agents)
  - Deleted: .claude/references/ (8 docs)
  - Deleted: .claude/rules/ (4 rules)
  - Deleted: .claude/CLAUDE.md (v7.3)
  - Deleted: .agent/ (all workload data)

Phase B (Scaffold):
  - Created: .claude/CLAUDE.md (v1.0 Team Constitution)
  - Created: .claude/settings.json (Agent Teams enabled)
  - Created: .claude/references/task-api-guideline.md ([PERMANENT])
  - Created: .claude/agents/researcher.md
  - Created: .claude/agents/architect.md
  - Created: .claude/agents/devils-advocate.md
  - Created: .claude/agents/implementer.md
  - Created: .claude/agents/tester.md
  - Created: .claude/agents/integrator.md
  - Created: .agent/teams/ (session output directory)

Phase C (Validation):
  - All validation checks PASSED

Preserved:
  - .claude/plugins/ (superpowers)
  - .mcp.json (MCP configuration)
  - docs/ (documentation)

Next Steps:
  1. Start tmux session: tmux new -s agent-team
  2. Launch Claude Code: claude
  3. Test team creation with natural language
  4. Verify Shift+Up/Down and Ctrl+T work
"
```

---

## Summary

| Task | Description | Est. Time |
|------|-------------|-----------|
| 1 | Create feature branch | 1 min |
| 2 | Backup current infrastructure | 2 min |
| 3 | Delete skills, agents, references, rules | 2 min |
| 4 | Delete CLAUDE.md and .agent/ | 2 min |
| 5 | Verify preserved files | 2 min |
| 6 | Commit Phase A cleanup | 1 min |
| 7 | Create settings.json | 3 min |
| 8 | Create CLAUDE.md (team constitution) | 5 min |
| 9 | Create task-api-guideline.md | 5 min |
| 10 | Create researcher.md | 3 min |
| 11 | Create architect.md | 3 min |
| 12 | Create devils-advocate.md | 3 min |
| 13 | Create implementer.md | 3 min |
| 14 | Create tester.md | 3 min |
| 15 | Create integrator.md | 3 min |
| 16 | Create .agent/teams/ directory | 2 min |
| 17 | Commit Phase B scaffold | 1 min |
| 18 | Phase C validation (10 checks) | 5 min |
| 19 | Full validation summary | 2 min |
| 20 | Final commit + summary | 2 min |
| **Total** | | **~50 min** |
