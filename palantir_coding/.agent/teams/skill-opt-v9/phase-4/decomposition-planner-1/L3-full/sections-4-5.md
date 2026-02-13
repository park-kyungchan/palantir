# §4 Task Breakdown + §5 Per-File Specifications (Enhanced)

> **Enhanced with interface-planner data:**
> - §C Interface Section verbatim content from interface-design.md §1 (all 9 skills)
> - GC Read/Write Map line references from dependency-matrix.md §6 (all 5 coordinator-based skills)
>
> **Read-First-Write-Second:** Every MODIFY spec assumes implementer reads the current file
> before editing. AC-0 validates plan-vs-reality alignment.
>
> **Verification Levels:** VL-1 (visual inspection), VL-2 (cross-reference check), VL-3 (full spec validation)
>
> **RISK-8 Fallback Delta:** Fork-related files include subsection for $ARGUMENTS fallback.

---

# §4 TASK BREAKDOWN

> Each task includes AC-0 (plan-vs-reality verification) as its first acceptance criterion.
> Tasks are independent — all can execute in parallel. Task V depends on all others.

---

## Task D: Protocol Edits (infra-d)

```
subject: "Apply §10 fork agent exception to CLAUDE.md and agent-common-protocol.md"

description: |
  ## Objective
  Add the fork agent Task API exception clause to CLAUDE.md §10 (line 364) and
  agent-common-protocol.md §Task API (lines 72-76). These 2 edits establish the
  permission model that all fork agent .md files reference.

  ## Context
  - Phase: 6 (Implementation)
  - Architecture: interface-architect L3 §2.2 (EXACT text provided)
  - Coupling Group: protocol-pair (both files must name the same 3 agents)
  - Upstream: None (independent)
  - Downstream: Task V validates naming consistency

  ## File Ownership
  1. .claude/CLAUDE.md — §10 first bullet modification only
  2. .claude/references/agent-common-protocol.md — §Task API replacement

  ## Detailed Specs
  See §5, Group 1 (protocol-pair).

  ## Acceptance Criteria
  - AC-0: Read current §10 (line 364) and §Task API (lines 72-76) before editing.
    Verify insertion points still match plan. If text has shifted, find correct
    location by content search, not line number.
  - AC-1: CLAUDE.md §10 first bullet includes exception clause naming exactly:
    pt-manager (TaskCreate+TaskUpdate), delivery-agent (TaskUpdate only),
    rsil-agent (TaskUpdate only)
  - AC-2: agent-common-protocol.md §Task API includes fork-context exception
    paragraph naming the same 3 agents
  - AC-3: Agent names in both files are IDENTICAL (cross-reference check)

activeForm: "Editing CLAUDE.md §10 and agent-common-protocol.md"
```

---

## Task A1: Fork Cluster 1 (impl-a1)

```
subject: "Create pt-manager + delivery-agent and restructure permanent-tasks + delivery-pipeline to fork"

description: |
  ## Objective
  Create 2 new fork agent .md files (pt-manager, delivery-agent) and restructure
  2 existing skills (permanent-tasks, delivery-pipeline) to fork-based template
  with context:fork + agent: frontmatter.

  ## Context
  - Phase: 6 (Implementation)
  - Architecture: risk-architect L3 §1.1 (pt-manager), §1.2 (delivery-agent),
    structure-architect L3 §6.3 (fork skill template), §1.3 (fork template skeleton)
  - Interface: interface-architect L3 §1.2 fork-based §C content (verbatim in §5)
  - Coupling Group: fork-cluster-1 (skill agent: ↔ agent .md filename)
  - Upstream: None (independent)
  - Downstream: Task V validates agent resolution

  ## Internal Execution Order
  1. CREATE pt-manager.md (from risk-architect L3 §1.1)
  2. MODIFY permanent-tasks/SKILL.md (references pt-manager capabilities)
  3. CREATE delivery-agent.md (from risk-architect L3 §1.2)
  4. MODIFY delivery-pipeline/SKILL.md (references delivery-agent capabilities)

  ## File Ownership
  1. .claude/agents/pt-manager.md — CREATE
  2. .claude/skills/permanent-tasks/SKILL.md — MODIFY (fork restructure)
  3. .claude/agents/delivery-agent.md — CREATE
  4. .claude/skills/delivery-pipeline/SKILL.md — MODIFY (fork restructure)

  ## Detailed Specs
  See §5, Group 2 (fork-cluster-1). Includes verbatim §C Interface Section content
  and RISK-8 Fallback Delta for each file.

  ## Acceptance Criteria
  - AC-0: For MODIFY files, read current content BEFORE editing. Verify the current
    section structure matches what the plan expects. If structure has changed since
    P3 research, report discrepancy before proceeding.
  - AC-1: pt-manager.md frontmatter matches risk-architect L3 §1.1 design
    (tools, disallowedTools, maxTurns, memory:user, permissionMode:default)
  - AC-2: permanent-tasks/SKILL.md frontmatter has context:fork, agent:"pt-manager"
  - AC-3: permanent-tasks/SKILL.md uses second-person voice ("You do X")
  - AC-4: delivery-agent.md frontmatter matches risk-architect L3 §1.2 design
  - AC-5: delivery-pipeline/SKILL.md frontmatter has context:fork, agent:"delivery-agent"
  - AC-6: delivery-pipeline/SKILL.md does NOT invoke /permanent-tasks (RISK-3)
  - AC-7: Both skills have §C Interface section matching verbatim content in §5
  - AC-8: Both skills have RISK-8 $ARGUMENTS fallback subsection
  - AC-9: Both skills have inline cross-cutting (ADR-S8), not 1-line CLAUDE.md refs
  - AC-10: BUG-001: any spawn examples use mode:"default"

activeForm: "Creating fork agents and restructuring fork skills (cluster 1)"
```

---

## Task A2: Fork Cluster 2 (impl-a2)

```
subject: "Create rsil-agent and restructure rsil-global + rsil-review to fork"

description: |
  ## Objective
  Create 1 shared fork agent .md file (rsil-agent) and restructure 2 existing
  skills (rsil-global, rsil-review) to fork-based template with context:fork
  + agent:rsil-agent frontmatter.

  ## Context
  - Phase: 6 (Implementation)
  - Architecture: risk-architect L3 §1.3 (rsil-agent), structure-architect L3 §6.3,
    ADR-S5 (shared agent for both RSIL skills)
  - Interface: interface-architect L3 §1.2 fork-based §C content (verbatim in §5)
  - Coupling Group: fork-cluster-2 (shared agent: ↔ 2 skills)
  - Upstream: None (independent)
  - Downstream: Task V validates agent resolution

  ## Internal Execution Order
  1. CREATE rsil-agent.md (from risk-architect L3 §1.3)
  2. MODIFY rsil-global/SKILL.md (references rsil-agent capabilities)
  3. MODIFY rsil-review/SKILL.md (references rsil-agent capabilities)

  ## File Ownership
  1. .claude/agents/rsil-agent.md — CREATE
  2. .claude/skills/rsil-global/SKILL.md — MODIFY (fork restructure)
  3. .claude/skills/rsil-review/SKILL.md — MODIFY (fork restructure)

  ## Detailed Specs
  See §5, Group 3 (fork-cluster-2). Includes verbatim §C Interface Section content
  and RISK-8 Fallback Delta for each file.

  ## Acceptance Criteria
  - AC-0: For MODIFY files, read current content BEFORE editing.
  - AC-1: rsil-agent.md frontmatter matches risk-architect L3 §1.3 design
    (includes Task tool for R-1/G-2 spawning, disallowedTools: [TaskCreate])
  - AC-2: BOTH skills reference agent:"rsil-agent" (ADR-S5, same agent)
  - AC-3: rsil-global stays within ~2000 token observation budget constraint
  - AC-4: rsil-review R-1 section references Task tool for spawning
    (aligned with rsil-agent.md tools list)
  - AC-5: Both skills have §C Interface section matching verbatim content in §5
  - AC-6: Both skills have RISK-8 $ARGUMENTS fallback subsection
  - AC-7: Both skills have inline cross-cutting (ADR-S8)
  - AC-8: Skill body (not agent .md) differentiates behavior between global and review

activeForm: "Creating rsil-agent and restructuring RSIL skills (cluster 2)"
```

---

## Task B: Coordinator-Based Skills (impl-b)

```
subject: "Restructure 5 coordinator-based SKILL.md files to new template with GC migration"

description: |
  ## Objective
  Restructure all 5 coordinator-based skills to the new 4-section template
  (A:Spawn + B:Core Workflow + C:Interface + D:Cross-Cutting) with PT-centric
  interface (D-7), GC migration (D-14), and coordinator spawn instructions.

  ## Context
  - Phase: 6 (Implementation)
  - Architecture: structure-architect L3 §1.2 (coordinator template skeleton),
    §6.2 (per-skill section inventory), interface-architect L3 §1.2 (PT contract)
  - GC Migration: interface-planner dependency-matrix.md §6 (exact line references
    per skill for GC operations to remove/replace/keep)
  - Interface: interface-planner interface-design.md §1.1 (§C content per skill)
  - Coupling Group: coord-skills (loose coupling to coordinator .md via pre-existing names)
  - Upstream: None (independent — coordinator names are pre-existing)
  - Downstream: Task V validates subagent_type references

  ## GC Migration Summary (from dependency-matrix.md §6)

  ### brainstorming-pipeline GC Operations
  - L230-246: CREATE GC-v1 → KEEP scratch sections only (remove Research Findings,
    Codebase Constraints, Phase 3 Input from template)
  - L377-387: UPDATE GC-v2 → REMOVE (Research→research-coord/L2, Constraints→PT, Phase 3→L2)
  - L500-511: UPDATE GC-v3 → REMOVE (Arch Summary→arch-coord/L2, Decisions→PT, Entry→L2)

  ### agent-teams-write-plan GC Operations
  - L91: READ Discovery → REPLACE with PT §phase_status.P3.status check
  - L106: READ V-1 → REPLACE with PT check
  - L108: READ V-3 → REPLACE with arch-coord/L2 §Downstream Handoff content check
  - L123: COPY GC-v3 → REMOVE (read L2 directly)
  - L166: EMBED GC-v3 → REPLACE with PT + arch-coord/L2 embed
  - L263-265: UPDATE GC-v4 → REMOVE (all 6 sections → PT/planning-coord/L2)

  ### plan-validation-pipeline GC Operations
  - L91: READ Discovery → REPLACE with PT §phase_status.P4.status check
  - L110: READ V-1 → REPLACE with PT check
  - L113: READ V-4 → REPLACE with planning-coord/L2 §Downstream Handoff
  - L128: COPY GC-v4 → REMOVE (read L2 directly)
  - L312-315: UPDATE Gate 5 → REMOVE (Phase 5 status→PT, mitigations→PT §Constraints)

  ### agent-teams-execution-plan GC Operations
  - L97: READ Discovery → REPLACE with PT §phase_status.P4/P5 check
  - L119: READ V-1 → REPLACE with PT check
  - L135: COPY GC-v4 → REMOVE (read L2 directly)
  - L553-580: UPDATE GC-v5 → REMOVE (Results→PT, Changes→PT, Entry→exec-coord/L2)

  ### verification-pipeline GC Operations
  - L116: READ V-1 → REPLACE with PT §phase_status.P6.status check
  - L149: COPY GC-v5 → REMOVE (read L2 directly)
  - L317: UPDATE Gate 7 → REMOVE (→ PT §phase_status.P7)
  - L427: UPDATE Gate 8 → REMOVE (→ PT §phase_status.P8)
  - L445-462: UPDATE termination → REMOVE (Results→PT, Entry→testing-coord/L2)
  - KEEP: Phase Pipeline Status inline scratch updates

  ## Processing Order (smallest to largest, build template familiarity)
  1. agent-teams-write-plan (362L)
  2. plan-validation-pipeline (434L)
  3. brainstorming-pipeline (613L)
  4. verification-pipeline (574L)
  5. agent-teams-execution-plan (692L, most complex)

  ## File Ownership
  1. .claude/skills/brainstorming-pipeline/SKILL.md — MODIFY
  2. .claude/skills/agent-teams-write-plan/SKILL.md — MODIFY
  3. .claude/skills/plan-validation-pipeline/SKILL.md — MODIFY
  4. .claude/skills/agent-teams-execution-plan/SKILL.md — MODIFY
  5. .claude/skills/verification-pipeline/SKILL.md — MODIFY

  ## Detailed Specs
  See §5, Group 4 (coord-skills). Each skill spec includes verbatim §C content
  and per-skill GC migration instructions with exact line references.

  ## Acceptance Criteria
  - AC-0: For each file, read current content BEFORE editing. Verify section
    inventory matches structure-architect L3 §6.2-6.3 section classification.
  - AC-1: All 5 skills have §A (Spawn) with coordinator spawn using mode:"default" (BUG-001)
  - AC-2: All 5 skills have §B (Core Workflow) preserving 60-80% unique logic
  - AC-3: All 5 skills have §C (Interface Section) matching verbatim content in §5
  - AC-4: All 5 skills have §D (Cross-Cutting) with 1-line CLAUDE.md references
  - AC-5: All 5 skills have Phase 0 PT Check (IDENTICAL canonical flow)
  - AC-6: GC write instructions REMOVED per GC Migration Summary above
  - AC-7: GC read instructions REMOVED; replaced by PT + predecessor L2 discovery (D-7)
  - AC-8: Dynamic Context uses $ARGUMENTS for feature input
  - AC-9: Tier-Based Routing table present with correct agent types per skill
  - AC-10: Unique core workflow content preserved (not lost in restructure)
  - AC-11: GC KEEP items retained as scratch-only (no cross-phase authority)

activeForm: "Restructuring 5 coordinator-based skills to new template"
```

---

## Task C: Coordinator Convergence (infra-c)

```
subject: "Converge 8 coordinator .md files to unified Template B"

description: |
  ## Objective
  Converge all 8 coordinator .md files to the unified Template B pattern
  (lean, protocol-referencing) per structure-architect L3 §5.2. Unified
  frontmatter (memory:project, color, 4-item disallowedTools) and 5-section
  body (Role, Before Starting Work, How to Work, Output Format, Constraints).

  ## Context
  - Phase: 6 (Implementation)
  - Architecture: structure-architect L3 §5.2 (Template B design, per-coordinator
    unique logic inventory, expected sizes)
  - Coupling Group: coord-convergence (all 8 converge to same pattern)
  - Upstream: None (independent)
  - Downstream: Task V validates frontmatter consistency

  ## Current State Gap Analysis

  ### Frontmatter Gaps
  | Coordinator | memory | color | disallowedTools |
  |-------------|--------|-------|-----------------|
  | research | user→project | cyan (ok) | 4-item (ok) |
  | verification | user→project | yellow (ok) | 4-item (ok) |
  | architecture | MISSING→project | MISSING→purple | 2→4-item (+Edit,+Bash) |
  | planning | MISSING→project | MISSING→orange | 2→4-item (+Edit,+Bash) |
  | validation | MISSING→project | MISSING→yellow | 2→4-item (+Edit,+Bash) |
  | execution | user→project | green (ok) | 4-item (ok) |
  | testing | user→project | magenta (ok) | 4-item (ok) |
  | infra-quality | user→project | white (ok) | 4-item (ok) |

  ### Body Gaps (Template A → Template B convergence needed for 5 coordinators)
  research (105→~45L), verification (115→~48L), execution (151→~83L),
  testing (98→~55L), infra-quality (120→~53L) — remove inlined protocol,
  add 2-line protocol references, retain unique logic only.

  architecture (61→~38L), planning (58→~40L), validation (60→~40L) —
  already Template B structure, minor adjustments only.

  ## File Ownership
  1-8. All 8 .claude/agents/*-coordinator.md files — MODIFY

  ## Detailed Specs
  See §5, Group 5 (coord-convergence).

  ## Acceptance Criteria
  - AC-0: For each file, read current content BEFORE editing. Verify which
    template (A or B) the file currently uses. Apply appropriate delta.
  - AC-1: All 8 have memory:project (change from "user" for 5, add for 3)
  - AC-2: All 8 have color assigned (add to architecture:purple, planning:orange,
    validation:yellow)
  - AC-3: All 8 have 4-item disallowedTools [TaskCreate, TaskUpdate, Edit, Bash]
  - AC-4: All 8 reference agent-common-protocol.md (first line after frontmatter)
  - AC-5: All 8 reference coordinator-shared-protocol.md (second line)
  - AC-6: All 8 have 5-section body (Role, Before Starting Work, How to Work,
    Output Format, Constraints)
  - AC-7: execution-coordinator retains ~45L unique review dispatch logic in
    How to Work section (ADR-S2 exemption)
  - AC-8: All 8 have progress-state.yaml writing constraint
  - AC-9: Inlined boilerplate REMOVED from Template A coordinators (Worker
    Management, Communication Protocol, Understanding Verification, Failure
    Handling, Coordinator Recovery — all in coordinator-shared-protocol.md now)

activeForm: "Converging 8 coordinator .md files to Template B"
```

---

## Task V: Cross-Reference Verification (verifier)

```
subject: "Validate cross-references across all 22 modified files"

description: |
  ## Objective
  After all 5 implementers complete, validate that all cross-references between
  files are consistent. This is the quality gate before atomic commit.

  ## Context
  - Phase: 6.V (Verification)
  - Upstream: Tasks D, A1, A2, B, C (ALL must be complete)
  - Downstream: Gate 6 → Phase 9 atomic commit

  ## Verification Checks (8 total)

  ### Check 1: Fork Agent Resolution
  For each of 4 fork SKILL.md frontmatter `agent:` fields:
  - Verify `.claude/agents/{agent-name}.md` file exists
  - Expected: permanent-tasks→pt-manager, delivery-pipeline→delivery-agent,
    rsil-global→rsil-agent, rsil-review→rsil-agent

  ### Check 2: Fork Agent Tool Assumptions
  For each fork skill body, verify it does not assume tools the agent .md
  does not grant. Key checks:
  - permanent-tasks uses TaskCreate? → pt-manager has TaskCreate ✓
  - delivery-pipeline uses Bash? → delivery-agent has Bash ✓
  - rsil-review uses Task (spawning)? → rsil-agent has Task ✓
  - rsil-global does NOT assume Task for Tier 1/2 (NL constraint)

  ### Check 3: §10 Fork Agent Names
  CLAUDE.md §10 lists exactly 3 agents: pt-manager, delivery-agent, rsil-agent.
  Verify each resolves to a `.claude/agents/{name}.md` file.

  ### Check 4: §Task API Fork Agent Names
  agent-common-protocol.md §Task API fork exception names match CLAUDE.md §10 names.

  ### Check 5: Skill §A subagent_type References
  For each of 5 coordinator-based SKILL.md §A (Spawn) sections:
  - Verify every `subagent_type` reference resolves to `.claude/agents/{name}.md`
  - Covers coordinator names AND worker names

  ### Check 6: Coordinator §Workers Lists
  For each of 8 coordinator .md files:
  - Verify every worker name resolves to `.claude/agents/{name}.md`

  ### Check 7: Interface Section Consistency
  For all 9 SKILL.md §C (Interface) sections:
  - Verify PT Read/Write sections match interface-architect L3 §1.2 contract table
  - Verify predecessor L2 paths follow deterministic pattern

  ### Check 8: Coordinator Frontmatter Schema
  For all 8 coordinator .md files:
  - memory:project present
  - color present (non-empty)
  - disallowedTools has exactly 4 items [TaskCreate, TaskUpdate, Edit, Bash]
  - permissionMode:default

  ## Acceptance Criteria
  - AC-0: Verify file ownership table (§3) matches actual files modified. Flag
    any unexpected file changes or missing expected changes.
  - AC-1: All 8 checks PASS
  - AC-2: Zero naming mismatches across all cross-references
  - AC-3: Report any findings as PASS/FAIL with file:line evidence

activeForm: "Validating cross-references across 22 files"
```

---

# §5 PER-FILE SPECIFICATIONS

---

## Group 1: protocol-pair (infra-d)

### File #21: `.claude/CLAUDE.md` — §10 Modification

**Operation:** MODIFY | **VL:** VL-1 | **Change:** ~5 lines added

**Current State (line 364):**
```markdown
- Only Lead creates and updates tasks (enforced by disallowedTools restrictions).
```

**Target State (from interface-architect L3 §2.1):**
```markdown
- Only Lead creates and updates tasks (enforced by disallowedTools restrictions),
  except for Lead-delegated fork agents (pt-manager, delivery-agent, rsil-agent)
  which receive explicit Task API access via their agent .md frontmatter. Fork agents
  execute skills that Lead invokes — they are extensions of Lead's intent, not
  independent actors. Fork Task API access is:
  - pt-manager: TaskCreate + TaskUpdate (creates and maintains PT)
  - delivery-agent: TaskUpdate only (marks PT as DELIVERED)
  - rsil-agent: TaskUpdate only (updates PT Phase Status with review results)
```

**Authority:** interface-architect L3 §2.1 (exact text)

**Cross-References:**
- Agent names MUST match file #22 (agent-common-protocol.md)
- Agent names MUST match files #1, #3, #5 (fork agent .md filenames)
- Permission scopes MUST match agent .md frontmatter tools/disallowedTools

---

### File #22: `.claude/references/agent-common-protocol.md` — §Task API

**Operation:** MODIFY | **VL:** VL-1 | **Change:** ~8 lines added (ADDITIVE, not replace)

**Current State (lines 72-76):**
```markdown
## Task API

Tasks are read-only for you: use TaskList and TaskGet to check status, find your assignments,
and read the PERMANENT Task for project context. Task creation and updates are Lead-only
(enforced by tool restrictions).
```

**Target State (from interface-architect L3 §2.2):**
```markdown
## Task API

Tasks are read-only for you: use TaskList and TaskGet to check status, find your
assignments, and read the PERMANENT Task for project context. Task creation and
updates are Lead-only (enforced by tool restrictions).

**Exception — Fork-context agents:** If your agent .md frontmatter does NOT include
TaskCreate/TaskUpdate in `disallowedTools`, you have explicit Task API write access.
This applies only to Lead-delegated fork agents (pt-manager, delivery-agent,
rsil-agent). You are an extension of Lead's intent — use Task API only for the
specific PT operations defined in your skill's instructions.
```

**Authority:** interface-architect L3 §2.2 (exact text, ADDITIVE — append after existing)

**Cross-References:**
- Agent names MUST match file #21 (CLAUDE.md §10)

---

## Group 2: fork-cluster-1 (impl-a1)

### File #1: `.claude/agents/pt-manager.md` — CREATE

**Operation:** CREATE | **VL:** VL-3

**Full Spec Source:** risk-architect L3 §1.1 (lines 7-85)

**Content:** Create using the COMPLETE agent .md design from risk-architect L3 §1.1.
The design includes full frontmatter (name, description, model, permissionMode, memory,
color, maxTurns, tools, disallowedTools) and full body (Role, Context Sources, How to
Work, Error Handling, Key Principles, Constraints, Never).

**Key Frontmatter Values:**
- `name: pt-manager`
- `model: opus`
- `permissionMode: default` (BUG-001)
- `memory: user` (cross-project reuse)
- `color: cyan`
- `maxTurns: 30`
- `tools:` Read, Glob, Grep, Write, TaskList, TaskGet, TaskCreate, TaskUpdate, AskUserQuestion
- `disallowedTools: []` (full Task API access — D-10 exception)

**Cross-References:**
- Filename `pt-manager.md` must match skill #2 frontmatter `agent: "pt-manager"`
- Filename must match CLAUDE.md §10 (file #21) and agent-common-protocol.md (file #22)

#### RISK-8 Fallback Delta
If task list scope is isolated (fork agent cannot see main session tasks):
- pt-manager becomes non-functional for Step 1 (TaskList discovery fails)
- **Fallback:** Pass PT task ID via $ARGUMENTS. Skill Dynamic Context injects
  `!TaskList` output pre-fork. pt-manager uses rendered task ID directly.
- **Agent .md change needed:** Add Step 0: "If $ARGUMENTS contains task_id:{N},
  skip TaskList discovery and use TaskGet({N}) directly."

---

### File #2: `.claude/skills/permanent-tasks/SKILL.md` — Fork Restructure

**Operation:** MODIFY | **VL:** VL-3

**Current Structure (279L):**
- Standard frontmatter (name, description, argument-hint) — NO context:fork, NO agent:
- Lead-executed body (third person or imperative voice for Lead)
- Steps 1, 2A, 2B, 3 — PT lifecycle management
- No Interface Section

**Target Frontmatter:**
```yaml
---
name: permanent-tasks
description: "{updated description mentioning fork agent}"
argument-hint: "[requirement description or context]"
context: fork
agent: "pt-manager"
---
```

**Structural Changes:**
1. **Frontmatter:** Add `context: fork` and `agent: "pt-manager"`
2. **Voice:** Change to second person ("You search TaskList..." not "Lead searches...")
3. **Phase 0:** Repurpose Step 1 as fork-executed PT discovery (same logic, different executor)
4. **Core Workflow:** Steps 2A/2B/3 retained, voice changed to second person
5. **NEW §C Interface (verbatim from interface-architect L3 §1.2):**

```markdown
## Interface

### Input
- **$ARGUMENTS:** Update content, requirements description, or context payload
- **Dynamic Context:** Infrastructure version, recent changes (git log), plans list, orchestration-plan.md (pre-rendered before fork)
- **PT** (via TaskGet, if exists): Full PT content for Read-Merge-Write merge

### Output
- **PT-v1** (via TaskCreate, if CREATE): New PERMANENT Task with User Intent, Codebase Impact Map, Architecture Decisions, Phase Status, Constraints, Budget Constraints
- **PT-v{N+1}** (via TaskUpdate, if UPDATE): Merged/refined current state — never append-only
- **Terminal summary:** CREATE vs UPDATE status, PT version, key changes summary, notification needs for Lead relay

### RISK-8 Fallback — CRITICAL
permanent-tasks IS the PT lifecycle manager. If isolated task list:
- TaskList/TaskGet in wrong scope → cannot discover or read PT
- TaskCreate creates PT in wrong list → Lead cannot find it
- **Fallback:** $ARGUMENTS must carry full PT content. Fork agent writes PT content to a file (`permanent-tasks-output.md`). Lead reads file and applies via TaskUpdate/TaskCreate manually.
- This is the HIGHEST IMPACT RISK-8 scenario. Pre-deployment validation MUST test this case.
```

6. **Cross-Cutting:** Inline error handling (ADR-S8), not 1-line CLAUDE.md refs
7. **REMOVE:** Any references to "Lead invokes" or "ask Lead" — fork agent has no Lead
8. **ADD:** AskUserQuestion for missing context (replaces conversation extraction)

**Key Concern (RISK-2):** Current Step 2A says "extract from full conversation + $ARGUMENTS."
In fork context, conversation is empty. Rewrite to rely on:
1. $ARGUMENTS (primary), 2. Dynamic Context, 3. AskUserQuestion (when insufficient)

**Preserved Content:** Steps 1/2A/2B/3 core logic, PT Description Template, Read-Merge-Write protocol, "Never" list items.

**Cross-References:**
- `agent: "pt-manager"` must match file #1 filename
- Tool assumptions must align with pt-manager.md tools list

---

### File #3: `.claude/agents/delivery-agent.md` — CREATE

**Operation:** CREATE | **VL:** VL-3

**Full Spec Source:** risk-architect L3 §1.2 (lines 109-212)

**Content:** Create from COMPLETE design in risk-architect L3 §1.2.

**Key Frontmatter Values:**
- `name: delivery-agent`
- `model: opus`
- `permissionMode: default` (BUG-001)
- `memory: user`
- `color: yellow`
- `maxTurns: 50`
- `tools:` Read, Glob, Grep, Edit, Write, Bash, TaskList, TaskGet, TaskUpdate, AskUserQuestion
- `disallowedTools: [TaskCreate]`

**Cross-References:**
- Filename `delivery-agent.md` must match skill #4 frontmatter `agent: "delivery-agent"`
- Filename must match CLAUDE.md §10 (file #21) and agent-common-protocol.md (file #22)

#### RISK-8 Fallback Delta
Same pattern as pt-manager: $ARGUMENTS carries PT task ID if task list is isolated.
delivery-agent only needs TaskUpdate (not TaskCreate), so fallback is simpler.

---

### File #4: `.claude/skills/delivery-pipeline/SKILL.md` — Fork Restructure

**Operation:** MODIFY | **VL:** VL-3

**Current Structure (~471L):**
- Standard frontmatter — NO context:fork, NO agent:
- Lead-executed body (Phase 9 orchestration)
- 9.1 Input Discovery → 9.2 Consolidation → 9.3 Delivery → 9.4 Cleanup
- Invokes /permanent-tasks if no PT found
- No Interface Section

**Target Frontmatter:**
```yaml
---
name: delivery-pipeline
description: "{updated description mentioning fork agent}"
argument-hint: "[feature name or session-id]"
context: fork
agent: "delivery-agent"
---
```

**Structural Changes:**
1. **Frontmatter:** Add `context: fork` and `agent: "delivery-agent"`
2. **Voice:** Change to second person
3. **Phase 0:** Fork agent executes PT check directly (TaskList + TaskGet)
4. **CRITICAL — REMOVE /permanent-tasks invocation (RISK-3):**
   Current: "If no PT found, invoke /permanent-tasks"
   Target: "If no PT found, inform user: 'No PERMANENT Task found. Please run
   /permanent-tasks first, then re-run /delivery-pipeline.'" (no double-fork)
5. **Core Workflow:** 9.1-9.4 retained, voice changed, user gates via AskUserQuestion
6. **NEW §C Interface (verbatim from interface-architect L3 §1.2):**

```markdown
## Interface

### Input
- **$ARGUMENTS:** Feature name, session ID, or delivery options
- **Dynamic Context:** File tree, git log, gate record paths, ARCHIVE templates, L2 paths (pre-rendered before fork)
- **PT** (via TaskGet): All sections — final consolidation read for delivery summary

### Output
- **PT-vFinal** (via TaskUpdate): §phase_status all phases COMPLETE, subject → "[DELIVERED] {feature}", final metrics summary
- **ARCHIVE.md:** Consolidated session artifact archive
- **MEMORY.md:** Updated with pipeline learnings (Read-Merge-Write)
- **Git commit:** Staged implementation files committed
- **PR:** Created via `gh pr create` (if user approves)
- **Terminal summary:** Delivery status with commit hash, PR URL, archived artifact count

### RISK-8 Fallback
If fork sees isolated task list (TaskList returns empty despite PT existing):
- Skip PT-based discovery. Use Dynamic Context (which pre-renders PT content before fork).
- Skip TaskUpdate for PT-vFinal. Report "PT update needed" in terminal summary for Lead to apply manually.
- All other operations (git, ARCHIVE, MEMORY) proceed normally.
```

7. **Cross-Cutting:** Inline error handling (ADR-S8)
8. **REMOVE:** References to "Lead" as executor
9. **KEEP:** All 5+ user confirmation gates (AskUserQuestion in fork context)

**GC Migration (delivery-pipeline only — from dependency-matrix.md §6.6):**
- Current V-1 fallback (L127): "PT exists with Phase 7/8 COMPLETE — OR — GC exists"
- **REMOVE GC fallback entirely.** PT is the sole authority.
- If PT §phase_status.P7.status != COMPLETE → abort with guidance message.

**Preserved Content:** 9.1-9.4 core logic, 7 delivery operations, user gate protocol, idempotent design, multi-session discovery.

**Cross-References:**
- `agent: "delivery-agent"` must match file #3 filename
- Tool assumptions (Bash for git, Edit for MEMORY.md) must align with delivery-agent.md tools

---

## Group 3: fork-cluster-2 (impl-a2)

### File #5: `.claude/agents/rsil-agent.md` — CREATE

**Operation:** CREATE | **VL:** VL-3

**Full Spec Source:** risk-architect L3 §1.3 (lines 246-353)

**Content:** Create from COMPLETE design in risk-architect L3 §1.3.

**Key Frontmatter Values:**
- `name: rsil-agent`
- `model: opus`
- `permissionMode: default` (BUG-001)
- `memory: user`
- `color: purple`
- `maxTurns: 50`
- `tools:` Read, Glob, Grep, Edit, Write, Task, TaskList, TaskGet, TaskUpdate, AskUserQuestion
- `disallowedTools: [TaskCreate]`

**Shared Agent Note (ADR-S5):** This single agent .md serves BOTH rsil-global and rsil-review.
The skill body differentiates behavior — rsil-global is lightweight (G-0→G-4), rsil-review
is deep (R-0→R-5). The agent .md body includes sections for both workflows.

**Cross-References:**
- Filename `rsil-agent.md` must match BOTH skill #6 AND skill #7 `agent: "rsil-agent"`
- Filename must match CLAUDE.md §10 (file #21) and agent-common-protocol.md (file #22)
- Task tool in tools list enables R-1 spawning (rsil-review) and G-2 spawning (rsil-global Tier 3)

#### RISK-8 Fallback Delta
rsil-agent is less affected (PT is optional context, not required for core RSIL workflow).
If isolated: skip TaskGet for PT, rely on Dynamic Context and $ARGUMENTS for scope.

---

### File #6: `.claude/skills/rsil-global/SKILL.md` — Fork Restructure

**Operation:** MODIFY | **VL:** VL-3

**Current Structure (~452L):**
- Standard frontmatter — NO context:fork, NO agent:
- Lead-executed body
- G-0 → G-1 → G-2 → G-3 → G-4 flow
- No Interface Section

**Target Frontmatter:**
```yaml
---
name: rsil-global
description: "{existing description}"
argument-hint: "[optional: specific area of concern]"
context: fork
agent: "rsil-agent"
---
```

**Structural Changes:**
1. **Frontmatter:** Add `context: fork` and `agent: "rsil-agent"`
2. **Voice:** Change to second person
3. **Phase 0:** Fork agent executes PT check (optional — PT is context, not required)
4. **Core Workflow:** G-0→G-4 retained, voice changed
5. **G-2 (Tier 3 spawning):** Verify Task tool usage aligns with rsil-agent tools list
6. **NEW §C Interface (verbatim from interface-architect L3 §1.2):**

```markdown
## Interface

### Input
- **$ARGUMENTS:** Optional concern description, observation budget override
- **Dynamic Context:** .agent/ directory tree, CLAUDE.md excerpt, git diff (recent changes), RSIL agent memory (pre-rendered before fork)
- **PT** (via TaskGet, optional): §Phase Status (for pipeline awareness), §Constraints

### Output
- **Tracker update:** `~/.claude/agent-memory/rsil/` narrow tracker (append findings)
- **Agent memory update:** `~/.claude/agent-memory/rsil/MEMORY.md` (universal Lens patterns only)
- **Terminal summary:** Observation type (A/B/C), tier reached (1/2/3), findings count by severity, score delta
- **PT-v{N+1}** (via TaskUpdate, rare): Only if actionable findings require §Constraints update

### RISK-8 Fallback
PT access is OPTIONAL for rsil-global. If isolated task list:
- Skip PT read. Use Dynamic Context for pipeline awareness (pre-rendered).
- Skip PT update (rare case eliminated). Report in terminal summary if findings would warrant PT update.
- Core assessment fully functional without PT.
```

7. **Cross-Cutting:** Inline error handling (ADR-S8)
8. **Budget constraint (~2000 tokens) PRESERVED** in core workflow

**Preserved Content:** Three-Tier Observation Window, 8 Meta-Research Lenses, AD-15 Filter, G-0→G-4 flow, tier classification logic.

**Cross-References:**
- `agent: "rsil-agent"` must match file #5 filename (same as file #7)

---

### File #7: `.claude/skills/rsil-review/SKILL.md` — Fork Restructure

**Operation:** MODIFY | **VL:** VL-3

**Current Structure (~549L):**
- Standard frontmatter — NO context:fork, NO agent:
- Lead-executed body
- R-0 → R-1 → R-2 → R-3 → R-4 → R-5 flow
- No Interface Section

**Target Frontmatter:**
```yaml
---
name: rsil-review
description: "{existing description}"
argument-hint: "[target skill/component/scope + specific concerns]"
context: fork
agent: "rsil-agent"
---
```

**Structural Changes:**
1. **Frontmatter:** Add `context: fork` and `agent: "rsil-agent"`
2. **Voice:** Change to second person
3. **Phase 0:** Fork agent executes PT check
4. **R-1 (Parallel Research):** Verify Task tool spawning aligns with rsil-agent tools
   - Spawns claude-code-guide + codebase-researcher via Task tool
   - These are one-shot invocations, no team context needed
5. **NEW §C Interface (verbatim from interface-architect L3 §1.2):**

```markdown
## Interface

### Input
- **$ARGUMENTS:** Target file(s) path, review scope description
- **Dynamic Context:** .agent/ directory tree, recent git changes, narrow tracker, RSIL agent memory (pre-rendered before fork)
- **PT** (via TaskGet, optional): §Phase Status (pipeline awareness)

### Output
- **Corrections applied:** FIX items applied to target files via Edit (after user approval at R-3)
- **Tracker update:** `~/.claude/agent-memory/rsil/` narrow tracker (findings + corrections)
- **Agent memory update:** `~/.claude/agent-memory/rsil/MEMORY.md` (universal Lens patterns)
- **PT-v{N+1}** (via TaskUpdate): §Phase Status updated with review results (R-4)
- **Terminal summary:** Findings by severity (FIX/WARN/INFO), corrections applied count, score

### RISK-8 Fallback
If isolated task list:
- Skip PT read. Use Dynamic Context for pipeline awareness.
- Skip R-4 PT update. Report "PT update needed: {review results}" in terminal summary for Lead.
- All other operations (R-0~R-3, corrections, tracker, memory) proceed normally.
```

6. **Cross-Cutting:** Inline error handling (ADR-S8)

**Preserved Content:** R-0→R-5 flow, 8 lens application, integration audit protocol, Layer 1/2 definitions, correction cascade logic.

**Cross-References:**
- `agent: "rsil-agent"` must match file #5 filename (same as file #6)
- R-1 Task tool spawning: subagent_type "claude-code-guide" and "codebase-researcher" must be valid

---

## Group 4: coord-skills (impl-b)

> **Template Reference:** structure-architect L3 §1.2 (coordinator-based template skeleton)
> **Per-Skill Section Inventory:** structure-architect L3 §6.2
> **Interface Contract:** interface-architect L3 §1.2 (per-skill PT Read/Write table)
> **GC Migration Evidence:** interface-planner dependency-matrix.md §6

### Common Changes Across All 5 Skills

These changes apply to EVERY coordinator-based skill. Per-skill unique specs follow.

1. **NEW §C Interface Section** — Verbatim content per skill from interface-architect L3 §1.1

2. **GC REMOVAL (D-14):** Remove all GC write instructions that carry cross-phase state.
   Remove GC read instructions for cross-phase discovery. Keep GC for scratch only.
   **Use line references from dependency-matrix.md §6 to locate exact GC operations.**

3. **PT Discovery Protocol Change (D-7):**
   Replace: "Read GC for Phase N-1 status"
   With: "TaskGet PT → §phase_status.P{N-1}.l2_path → read predecessor L2 §Downstream Handoff"

4. **Phase 0 PT Check:** IDENTICAL canonical flow across all 5 (verify consistency).

5. **Dynamic Context:** Ensure $ARGUMENTS is present for feature input.

6. **Cross-Cutting §D:** Collapse to 1-line CLAUDE.md references (coordinator skills have CLAUDE.md in context).

7. **BUG-001:** All spawn examples use `mode: "default"`.

---

### File #8: `.claude/skills/brainstorming-pipeline/SKILL.md`

**Operation:** MODIFY | **VL:** VL-3 | **Current:** ~613L | **Target:** ~613L

**Unique Characteristics:**
- Covers Phase 1 (Discovery) + Phase 2 (Research) + Phase 3 (Architecture) — widest phase span
- 3 gates (Gates 1, 2, 3) — most gates of any skill
- Phase 1 is Lead-only (Q&A + feasibility check) — no spawn
- Feasibility Check (AD-2) is brainstorming-only
- Creates PT-v1 (via /permanent-tasks) — unique: it CREATES PT, others UPDATE

**§C Interface Section (verbatim from interface-architect L3 §1.1):**

```markdown
## C) Interface

### Input
- **$ARGUMENTS:** Feature description or topic (seed for User Intent)
- **No predecessor L2:** This is the pipeline start — no prior phase output
- **No prior PT:** This skill creates the PERMANENT Task (via /permanent-tasks at Gate 1)

### Output
- **PT-v1** (created via /permanent-tasks): User Intent, Codebase Impact Map, Architecture Decisions, Phase Status (P1-P3=COMPLETE), Constraints
- **L1/L2/L3:** research-coordinator L1/L2/L3, architecture-coordinator L1/L2/L3 (COMPLEX) or researcher/architect L1/L2/L3 (STANDARD)
- **Gate records:** gate-record.yaml for Gates 1, 2, 3
- **GC scratch:** Phase Pipeline Status, execution metrics, version marker (session-scoped only)

### Next
Invoke `/agent-teams-write-plan "$ARGUMENTS"`.
Write-plan needs:
- PT §phase_status.P3.status == COMPLETE
- PT §phase_status.P3.l2_path → arch-coordinator/L2 §Downstream Handoff (contains Architecture Decisions, Constraints, Interface Contracts, Risks)
```

**GC Migration (from dependency-matrix.md §6):**

| Gate/Step | GC Op | Current | Migration Action |
|-----------|-------|---------|-----------------|
| Gate 1 (L230-246) | CREATE GC-v1 | Frontmatter + Scope + Status + Constraints + Decisions | KEEP scratch sections only — REMOVE Research Findings, Codebase Constraints, Phase 3 Input from GC CREATE template |
| Gate 2 (L377-387) | UPDATE→GC-v2 | +Research Findings, +Codebase Constraints, +Phase 3 Input | REMOVE: Research→research-coord/L2, Constraints→PT §Constraints (via /permanent-tasks), Phase 3→research-coord/L2 §Downstream Handoff |
| Gate 3 (L500-511) | UPDATE→GC-v3 | +Arch Summary, +Arch Decisions, +Phase 4 Entry | REMOVE: Arch Summary→arch-coord/L2, Decisions→PT §Architecture Decisions, Entry→arch-coord/L2 §Downstream Handoff |

**Implementation instruction:** At Gates 2 and 3, replace GC UPDATE instructions with:
"Verify PT §phase_status updated via /permanent-tasks. Verify coordinator L2 §Downstream Handoff written."
Keep Gate 1 GC CREATE but remove cross-phase sections from the template (keep scratch only).

**Per-Skill Restructure Notes:**
- Retain Phase 1 Lead-only Q&A (unique, no spawn)
- Restructure Phase 2/3 spawn sections to §A template format (tier-based routing)
- Phase 2: research-coordinator (COMPLEX) or codebase-researcher (STANDARD)
- Phase 3: architecture-coordinator (COMPLEX) or architect (STANDARD)
- Preserve Feasibility Check, Approach Exploration, Gate 1/2/3 unique logic

---

### File #9: `.claude/skills/agent-teams-write-plan/SKILL.md`

**Operation:** MODIFY | **VL:** VL-3 | **Current:** ~362L | **Target:** ~362L

**Unique Characteristics:**
- Phase 4 (Detailed Design) only
- Spawn: architect (STANDARD) or planning-coordinator + 3 planners (COMPLEX)
- 5-layer directive context (PT, GC, L2, L3 path, exemplar)
- "Propose alternative decomposition" understanding verification — unique depth
- 10-section plan template guidance

**§C Interface Section (verbatim from interface-architect L3 §1.1):**

```markdown
## C) Interface

### Input
- **PT-v{N}** (via TaskGet): §User Intent, §Codebase Impact Map, §Architecture Decisions, §Constraints
- **Predecessor L2:** arch-coordinator/L2 §Downstream Handoff (path from PT §phase_status.P3.l2_path)
  - Contains: Decisions Made, Risks Identified, Interface Contracts, Constraints, Open Questions, Artifacts Produced
- **CH-001 exemplar:** `docs/plans/2026-02-07-ch001-ldap-implementation.md` (10-section format reference)

### Output
- **PT-v{N+1}** (via /permanent-tasks or TaskUpdate): adds §Implementation Plan (l3_path, task_count, file_ownership), §phase_status.P4=COMPLETE
- **L1/L2/L3:** planning-coordinator L1/L2/L3 (COMPLEX) or architect L1/L2/L3 (STANDARD)
- **Gate record:** gate-record.yaml for Gate 4
- **Implementation plan file:** `docs/plans/{date}-{feature}-implementation.md` (10-section format)
- **GC scratch:** Phase Pipeline Status update (session-scoped only)

### Next
Invoke `/plan-validation-pipeline "$ARGUMENTS"`.
Validation needs:
- PT §phase_status.P4.status == COMPLETE
- PT §phase_status.P4.l2_path → planning-coordinator/L2 §Downstream Handoff (contains Task Decomposition, File Ownership, Validation Targets, Commit Strategy)
- PT §implementation_plan.l3_path → detailed plan for challenge
```

**GC Migration (from dependency-matrix.md §6):**

| Gate/Step | GC Op | Current | Migration Action |
|-----------|-------|---------|-----------------|
| Discovery (L91) | READ | Scan for `Phase 3: COMPLETE` | REPLACE: TaskGet PT → §phase_status.P3.status == COMPLETE |
| V-1 (L106) | READ | GC exists with `Phase 3: COMPLETE` | REPLACE: PT exists AND §phase_status.P3.status check |
| V-3 (L108) | READ | GC-v3 contains Scope, Component Map, Interface Contracts | REPLACE: arch-coord/L2 §Downstream Handoff content |
| Phase 4.2 (L123) | COPY | Copy GC-v3 to session dir | REMOVE: read L2 directly from path |
| Directive (L166) | EMBED | GC-v3 full embedding | REPLACE: embed PT excerpt + arch-coord/L2 §Downstream Handoff |
| Gate 4 (L263-265) | UPDATE→GC-v4 | +6 sections (Plan, Tasks, Ownership, Entry, Targets, Strategy) | REMOVE: all 6 → PT §implementation_plan + planning-coord/L2 §Downstream Handoff |

**KEEP:** Phase Pipeline Status scratch update.

**Per-Skill Restructure Notes:**
- Restructure Phase 4 spawn to §A template (tier-based routing)
- Preserve 10-section plan format guidance (unique)
- Preserve directive embed/reference/omit matrix (unique)

---

### File #10: `.claude/skills/plan-validation-pipeline/SKILL.md`

**Operation:** MODIFY | **VL:** VL-3 | **Current:** ~434L | **Target:** ~434L

**Unique Characteristics:**
- Phase 5 (Validation) only
- Spawn: devils-advocate (STANDARD) or validation-coordinator + 3 challengers (COMPLEX)
- Devils-advocate AD exemption (no understanding verification)
- 6 challenge categories
- PASS/CONDITIONAL/FAIL verdict tree — unique decision tree
- Re-verification loop after plan updates

**§C Interface Section (verbatim from interface-architect L3 §1.1):**

```markdown
## C) Interface

### Input
- **PT-v{N}** (via TaskGet): §User Intent, §Architecture Decisions, §Constraints, §Implementation Plan (pointer to L3)
- **Predecessor L2:** planning-coordinator/L2 §Downstream Handoff (path from PT §phase_status.P4.l2_path)
  - Contains: Task Decomposition, File Ownership Map, Phase 5 Validation Targets, Commit Strategy
- **Implementation plan file:** path from PT §implementation_plan.l3_path

### Output
- **PT-v{N+1}** (via /permanent-tasks or TaskUpdate): adds §Validation Verdict (PASS | CONDITIONAL_PASS | FAIL), §phase_status.P5=COMPLETE. If CONDITIONAL_PASS: adds mitigations to §Constraints
- **L1/L2/L3:** validation-coordinator L1/L2/L3 (COMPLEX) or devils-advocate L1/L2/L3 (STANDARD)
- **Gate record:** gate-record.yaml for Gate 5
- **GC scratch:** Phase Pipeline Status update (session-scoped only)

### Next
If PASS or CONDITIONAL_PASS: invoke `/agent-teams-execution-plan "$ARGUMENTS"`.
If FAIL: return to `/agent-teams-write-plan` for plan revision.
Execution needs:
- PT §phase_status.P4.status == COMPLETE (reads plan)
- PT §validation_verdict (PASS or CONDITIONAL_PASS)
- PT §phase_status.P4.l2_path → planning-coordinator/L2 (for plan context)
- PT §phase_status.P5.l2_path → validation-coordinator/L2 §Downstream Handoff (for validation conditions)
```

**GC Migration (from dependency-matrix.md §6):**

| Gate/Step | GC Op | Current | Migration Action |
|-----------|-------|---------|-----------------|
| Discovery (L91) | READ | Scan for `Phase 4: COMPLETE` | REPLACE: TaskGet PT → §phase_status.P4.status == COMPLETE |
| V-1 (L110) | READ | GC exists with `Phase 4: COMPLETE` | REPLACE: PT exists AND §phase_status.P4.status check |
| V-4 (L113) | READ | GC-v4 contains Scope, Phase 4 decisions, task breakdown | REPLACE: planning-coord/L2 §Downstream Handoff content |
| Phase 5.2 (L128) | COPY | Copy GC-v4 to session dir | REMOVE: read L2 directly |
| Gate 5 (L312-315) | UPDATE | Phase 5 status + conditional mitigations + version bump | REMOVE: Phase 5 status → PT §phase_status.P5, mitigations → PT §Constraints via /permanent-tasks |

**KEEP:** Phase Pipeline Status scratch update.

**Per-Skill Restructure Notes:**
- No Team Setup section (plan-validation may not create team for STANDARD tier)
- Restructure spawn to §A template (devils-advocate for STANDARD, coordinator for COMPLEX)
- Preserve 6 challenge categories, verdict flow, re-verification loop

---

### File #11: `.claude/skills/agent-teams-execution-plan/SKILL.md`

**Operation:** MODIFY | **VL:** VL-3 | **Current:** ~692L | **Target:** ~692L

**Unique Characteristics (MOST COMPLEX skill):**
- Phase 6 (Implementation) only
- Adaptive spawn algorithm (connected components graph analysis) — unique
- execution-coordinator + execution-monitor integration — unique
- Two-stage review dispatch (spec → code) — unique, via exec-coordinator
- Fix loop management — unique
- Cross-boundary escalation protocol — unique
- Per-implementer context layers in directive — unique
- contract-reviewer + regression-reviewer dispatch — unique to this skill

**§C Interface Section (verbatim from interface-architect L3 §1.1):**

```markdown
## C) Interface

### Input
- **PT-v{N}** (via TaskGet): §User Intent, §Codebase Impact Map, §Architecture Decisions, §Implementation Plan (l3_path, file_ownership), §Constraints
- **Predecessor L2 (dual):**
  - planning-coordinator/L2 §Downstream Handoff (path from PT §phase_status.P4.l2_path) — plan details
  - validation-coordinator/L2 §Downstream Handoff (path from PT §phase_status.P5.l2_path) — validation conditions
- **Implementation plan file:** path from PT §implementation_plan.l3_path

### Output
- **PT-v{N+1}** (via /permanent-tasks or TaskUpdate): adds §Implementation Results (l3_path, summary), §phase_status.P6=COMPLETE, updates §Codebase Impact Map if interface changes detected at Gate 6
- **L1/L2/L3:** execution-coordinator L1/L2/L3, per-implementer L1/L2/L3
- **Gate record:** gate-record.yaml for Gate 6
- **Implemented source files:** per file_ownership assignment
- **GC scratch:** Phase Pipeline Status, execution metrics (session-scoped only)

### Next
Invoke `/verification-pipeline "$ARGUMENTS"`.
Verification needs:
- PT §phase_status.P6.status == COMPLETE
- PT §phase_status.P6.l2_path → execution-coordinator/L2 §Downstream Handoff (contains Implementation Results, Interface Changes, Test Targets)
- PT §implementation_results.l3_path → detailed implementation output
```

**GC Migration (from dependency-matrix.md §6):**

| Gate/Step | GC Op | Current | Migration Action |
|-----------|-------|---------|-----------------|
| Discovery (L97) | READ | Scan for `Phase 4: COMPLETE` or `Phase 5: COMPLETE` | REPLACE: TaskGet PT → §phase_status.P4 AND §phase_status.P5 check |
| V-1 (L119) | READ | GC exists with Phase 4/5 COMPLETE | REPLACE: PT exists AND §phase_status checks |
| Phase 6.2 (L135) | COPY | Copy GC-v4 to session dir | REMOVE: read L2 directly |
| Phase 6.7 (L553-580) | UPDATE→GC-v5 | +Pipeline Status, +Results, +Changes, +G6 Record, +P7 Entry | REMOVE: Results→PT §implementation_results, Changes→PT §codebase_impact_map, Entry→exec-coord/L2 §Downstream Handoff |

**KEEP:** Phase Pipeline Status (scratch), Gate 6 record embed (scratch).

**Per-Skill Restructure Notes:**
- Restructure spawn to §A template, but spawn logic is inherently complex (adaptive algorithm)
- Preserve adaptive spawn, two-stage review, fix loops, cross-boundary escalation — ALL unique
- This skill has the most unique content (69% unique, 12% shared)
- Carefully restructure without losing any orchestration logic

---

### File #12: `.claude/skills/verification-pipeline/SKILL.md`

**Operation:** MODIFY | **VL:** VL-3 | **Current:** ~574L | **Target:** ~574L

**Unique Characteristics:**
- Phase 7 (Testing) + Phase 8 (Integration, conditional) — dual phase
- Spawn: tester (Phase 7) then integrator (Phase 8, conditional)
- testing-coordinator manages sequential P7→P8 lifecycle
- Contract test guidance (D-014)
- Component analysis protocol — unique test design
- Conditional Phase 8 (only if 2+ implementers in Phase 6)

**§C Interface Section (verbatim from interface-architect L3 §1.1):**

```markdown
## C) Interface

### Input
- **PT-v{N}** (via TaskGet): §User Intent, §Codebase Impact Map, §Implementation Results (pointer to L3), §Constraints
- **Predecessor L2:** execution-coordinator/L2 §Downstream Handoff (path from PT §phase_status.P6.l2_path)
  - Contains: Implementation Results, Interface Changes from Spec, Test Coverage Targets, Phase 7 Entry Conditions

### Output
- **PT-v{N+1}** (via /permanent-tasks or TaskUpdate): adds §Verification Summary (test_count, pass_rate, l2_path), §phase_status.P7=COMPLETE, §phase_status.P8=COMPLETE (if Phase 8 runs)
- **L1/L2/L3:** testing-coordinator L1/L2/L3, per-tester/integrator L1/L2/L3
- **Gate records:** gate-record.yaml for Gate 7, Gate 8 (conditional)
- **GC scratch:** Phase Pipeline Status updates (session-scoped only)

### Next
Invoke `/delivery-pipeline "$ARGUMENTS"`.
Delivery needs:
- PT §phase_status with P7==COMPLETE (and P8==COMPLETE if applicable)
- PT §phase_status.P7.l2_path → testing-coordinator/L2 §Downstream Handoff (contains Verification Results, Phase 9 Entry Conditions)
```

**GC Migration (from dependency-matrix.md §6):**

| Gate/Step | GC Op | Current | Migration Action |
|-----------|-------|---------|-----------------|
| V-1 (L116) | READ | GC exists with `Phase 6: COMPLETE` | REPLACE: TaskGet PT → §phase_status.P6.status == COMPLETE |
| Phase 7.2 (L149) | COPY | Copy GC-v5 to session dir | REMOVE: read L2 directly |
| Gate 7 (L317) | UPDATE | `Phase 7: COMPLETE` | REMOVE: → PT §phase_status.P7 = COMPLETE |
| Gate 8 (L427) | UPDATE | `Phase 8: COMPLETE` | REMOVE: → PT §phase_status.P8 = COMPLETE |
| Termination (L445-462) | UPDATE | +Verification Results, +Phase 9 Entry Conditions | REMOVE: Results→PT §verification_summary, Entry→testing-coord/L2 §Downstream Handoff |

**KEEP:** Phase Pipeline Status inline scratch updates (P7, P8).

**Per-Skill Restructure Notes:**
- Restructure spawn to §A template (testing-coordinator + tester + optional integrator)
- Preserve sequential P7→P8 lifecycle (unique)
- Preserve contract test guidance, component analysis protocol
- Conditional Phase 8 transition logic must be preserved

---

## Group 5: coord-convergence (infra-c)

> **Template Reference:** structure-architect L3 §5.2 (unified Template B)
> **Protocol References to add:** agent-common-protocol.md, coordinator-shared-protocol.md

### Common Template B Changes (All 8 Coordinators)

**Frontmatter (ALL 8):**
- `memory: project` (change from "user" for 5, ADD for 3 missing)
- `color: {assigned}` (ADD for 3 missing: architecture→purple, planning→orange, validation→yellow)
- `disallowedTools: [TaskCreate, TaskUpdate, Edit, Bash]` (ADD Edit+Bash for 3 missing)

**Body Template (ALL 8):**
```markdown
# {Coordinator Name}

Read and follow `.claude/references/agent-common-protocol.md` for shared procedures.
Read `.claude/references/coordinator-shared-protocol.md` for coordinator-specific protocol.

## Role
{1-3 sentences unique role description}
{Worker list with roles}

## Before Starting Work
Read the PERMANENT Task via TaskGet. Message Lead with:
{3-4 bullet points — unique per coordinator}

## How to Work
{Unique orchestration logic per coordinator — ONLY content NOT in coordinator-shared-protocol.md}

## Output Format
Follow L1/L2 canonical format from agent-common-protocol.md.
- **L1-index.yaml:** {coordinator-specific notes}
- **L2-summary.md:** {coordinator-specific notes}
- **L3-full/:** {coordinator-specific contents}

## Constraints
- Do NOT modify code or infrastructure — L1/L2/L3 output only
- Follow sub-gate protocol before reporting completion
- Write L1/L2/L3 proactively
- Write `progress-state.yaml` after every worker stage transition
{Additional unique constraints}
```

---

### Files #13-#17: Template A → Template B (5 coordinators requiring body restructure)

#### File #13: `.claude/agents/research-coordinator.md`

**Operation:** MODIFY | **VL:** VL-2 | **Current:** 105L | **Target:** ~45L

**Frontmatter Changes:** `memory: user` → `memory: project`

**Body — REMOVE (→ coordinator-shared-protocol.md):**
- §Worker Management (detailed boilerplate) — retain only research-specific routing rules
- §Communication Protocol (detailed) — REMOVE entirely
- §Understanding Verification (AD-11) — REMOVE (in shared protocol)
- §Failure Handling — REMOVE (in shared protocol)
- §Coordinator Recovery — REMOVE (in shared protocol)

**Body — RETAIN (unique logic):**
- §Role: unique role + 3 workers
- §Before Starting Work: research-specific focus areas (3 bullets)
- §How to Work: research distribution rules (~7L) — route by source type (codebase/external/audit)
- §Output Format: research-specific schema notes
- §Constraints: unique constraints

---

#### File #14: `.claude/agents/verification-coordinator.md`

**Operation:** MODIFY | **VL:** VL-2 | **Current:** 107L | **Target:** ~48L

**Frontmatter Changes:** `memory: user` → `memory: project`

**Body — REMOVE:** §Worker Management, §Communication Protocol, §Understanding Verification, §Failure Handling, §Coordinator Recovery

**Body — RETAIN (unique logic):**
- §Role: unique role + 3 verifier workers
- §Before Starting Work: verification-specific focus areas
- §How to Work: Cross-Dimension Synthesis cascade rules (~10L) — unique
- §Output Format: per-dimension scores
- §Constraints: unique constraints

---

#### File #18: `.claude/agents/execution-coordinator.md`

**Operation:** MODIFY | **VL:** VL-2 | **Current:** 151L | **Target:** ~83L

**Frontmatter Changes:** `memory: user` → `memory: project`

**Body — REMOVE:**
- §Communication Protocol (general boilerplate) — retain Consolidated Report Format (unique)
- §Understanding Verification (generic part) — REMOVE, but retain 1-2 line reference
- §Failure Handling (generic) — REMOVE, retain unique items (reviewer timeout, fix loop exhaustion)
- §Coordinator Recovery — REMOVE
- §Mode 3 Fallback — REMOVE (in shared protocol)

**Body — RETAIN (ADR-S2 exemption: ~45L unique):**
- §Worker Management: full Task Distribution + Review Dispatch Protocol (AD-9) + Fix Loop Rules
- §Communication Protocol: Consolidated Report Format only (~10L)
- §Failure Handling: execution-specific items only (reviewer timeout, cross-boundary escalation)
- This is the LONGEST "How to Work" section — justified by unique review dispatch logic

---

#### File #19: `.claude/agents/testing-coordinator.md`

**Operation:** MODIFY | **VL:** VL-2 | **Current:** 118L | **Target:** ~55L

**Frontmatter Changes:** `memory: user` → `memory: project`

**Body — REMOVE:** §Communication Protocol, §Understanding Verification, §Failure Handling, §Coordinator Recovery

**Body — RETAIN (unique logic ~20L):**
- §How to Work: Phase 7 testing → Phase 8 integration sequential lifecycle
- §How to Work: Conditional Phase 8 trigger logic
- §Constraints: "Enforce tester→integrator ordering" (unique)

---

#### File #20: `.claude/agents/infra-quality-coordinator.md`

**Operation:** MODIFY | **VL:** VL-2 | **Current:** 113L | **Target:** ~53L

**Frontmatter Changes:** `memory: user` → `memory: project`

**Body — REMOVE:** §Communication Protocol, §Understanding Verification, §Failure Handling, §Coordinator Recovery

**Body — RETAIN (unique logic ~18L):**
- §How to Work: Score Aggregation formula (weighted average with 4 weights)
- §How to Work: Cross-Dimension Synthesis rules
- §Constraints: unique constraints

---

### Files #15-#17: Template B → Template B (3 coordinators requiring minor adjustments)

These 3 already follow Template B structure. Changes are frontmatter-only + minor body tweaks.

#### File #15: `.claude/agents/architecture-coordinator.md`

**Operation:** MODIFY | **VL:** VL-1 | **Current:** 61L | **Target:** ~38L

**Frontmatter Changes:**
- ADD `memory: project`
- ADD `color: purple`
- ADD to disallowedTools: `Edit`, `Bash` (currently only TaskCreate, TaskUpdate)

**Body Changes:** Minimal. Already Template B. Verify 5-section structure present.

---

#### File #16: `.claude/agents/planning-coordinator.md`

**Operation:** MODIFY | **VL:** VL-1 | **Current:** 61L | **Target:** ~40L

**Frontmatter Changes:**
- ADD `memory: project`
- ADD `color: orange`
- ADD to disallowedTools: `Edit`, `Bash`

**Body Changes:** Minimal. Already Template B. Verify 5-section structure present.

---

#### File #17: `.claude/agents/validation-coordinator.md`

**Operation:** MODIFY | **VL:** VL-1 | **Current:** 61L | **Target:** ~40L

**Frontmatter Changes:**
- ADD `memory: project`
- ADD `color: yellow`
- ADD to disallowedTools: `Edit`, `Bash`

**Body Changes:** Minimal. Already Template B. Verify 5-section structure.
Note: validation-coordinator has unique constraint "no understanding verification needed for challengers" — PRESERVE this.

---

## PT Goal Linkage

| PT Decision | §4/§5 Contribution |
|-------------|-------------------|
| D-7 (PT-centric) | All 9 skill specs include new §C Interface Section with PT Read/Write contract |
| D-8 (Big Bang) | 22-file atomic commit, Task V validates cross-references before commit |
| D-11 (3 fork agents) | Tasks A1+A2 create 3 agent .md files from risk-architect L3 §1 |
| D-13 (Coordinator convergence) | Task C converges 8 coordinators to Template B with gap analysis |
| D-14 (GC 14→3) | All 5 coordinator skill specs include GC migration tables with line references |
| C-5 (§10 exception) | Task D applies exact text from interface-architect L3 §2.1-2.2 |
| RISK-8 ($ARGUMENTS fallback) | All fork file specs include RISK-8 fallback subsections |
| ADR-S1 (2 templates) | §5 Groups 2-3 use fork template, Group 4 uses coordinator template |
| ADR-S2 (exec-coord exemption) | File #18 retains ~45L unique review dispatch logic |
| ADR-S5 (shared rsil-agent) | Files #6 and #7 both reference agent:"rsil-agent" |
| ADR-S8 (inline cross-cutting) | Fork skills inline error handling; coordinator skills use 1-line CLAUDE.md refs |

## Evidence Sources

| Source | Count | Key References |
|--------|:-----:|----------------|
| Phase 3 architecture (read) | 4 | arch-coord L2, structure/interface/risk architect L3 |
| Phase 4 interface-planner (read) | 2 | interface-design.md §1-§5, dependency-matrix.md §6-§8 |
| Current file reads (verification) | 14 | 8 coordinator .md, 4 fork skill headers, 2 protocol sections |
| CH-001 exemplar (format) | 1 | Task structure, cross-reference verification pattern |
| Sequential-thinking (design) | 3 | §3 ownership, Q1/Q2 AD-11, §4/§5 batching |
| **Total** | **24** | |
