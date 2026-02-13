# §5 Per-File Specifications

> **Read-First-Write-Second:** Every MODIFY spec assumes implementer reads the current file
> before editing. AC-0 validates plan-vs-reality alignment.
>
> **Verification Levels:** VL-1 (visual inspection), VL-2 (cross-reference check), VL-3 (full spec validation)
>
> **RISK-8 Fallback Delta:** Fork-related files include subsection for $ARGUMENTS fallback if
> task list scope is isolated.

---

## Group 1: protocol-pair (infra-d)

### File #21: `.claude/CLAUDE.md` — §10 Modification

**Operation:** MODIFY | **VL:** VL-1 | **Change:** ~5 lines added

**Current State (line 364):**
```markdown
- Only Lead creates and updates tasks (enforced by disallowedTools restrictions).
```

**Target State:**
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

**Authority:** interface-architect L3 §2.2 (exact text)

**Cross-References:**
- Agent names MUST match file #22 (agent-common-protocol.md)
- Agent names MUST match files #1, #3, #5 (fork agent .md filenames)
- Permission scopes MUST match agent .md frontmatter tools/disallowedTools

---

### File #22: `.claude/references/agent-common-protocol.md` — §Task API

**Operation:** MODIFY | **VL:** VL-1 | **Change:** ~8 lines replaced

**Current State (lines 72-76):**
```markdown
## Task API

Tasks are read-only for you: use TaskList and TaskGet to check status, find your assignments,
and read the PERMANENT Task for project context. Task creation and updates are Lead-only
(enforced by tool restrictions).
```

**Target State:**
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

**Authority:** interface-architect L3 §2.2 (exact text)

**Cross-References:**
- Agent names MUST match file #21 (CLAUDE.md §10)

---

## Group 2: fork-cluster-1 (impl-a1)

### File #1: `.claude/agents/pt-manager.md` — CREATE

**Operation:** CREATE | **VL:** VL-3

**Full Spec Source:** risk-architect L3 §1.1 (lines 7-85)

**Content:** The implementer should create this file using the COMPLETE agent .md design
from risk-architect L3 §1.1. The design includes full frontmatter (name, description,
model, permissionMode, memory, color, maxTurns, tools, disallowedTools) and full body
(Role, Context Sources, How to Work, Error Handling, Key Principles, Constraints, Never).

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

**Target Structure (~279L target, fork-based template):**
```
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
5. **NEW §Interface:** Add per interface-architect L3 §1.2 fork-skill row:
   - Input: $ARGUMENTS (update content), Dynamic Context (git log, plans, infra version), PT (full, for merge)
   - Output: PT-v{N+1} (any section, user-directed)
6. **Cross-Cutting:** Inline error handling (ADR-S8), not 1-line CLAUDE.md refs
7. **REMOVE:** Any references to "Lead invokes" or "ask Lead" — fork agent has no Lead
8. **ADD:** AskUserQuestion for missing context (replaces conversation extraction)

**Key Concern (RISK-2):** Current Step 2A says "extract from full conversation + $ARGUMENTS."
In fork context, conversation is empty. The skill must be rewritten to rely on:
1. $ARGUMENTS (primary — pipeline or user provides structured input)
2. Dynamic Context (git log, plans, infra version)
3. AskUserQuestion (when $ARGUMENTS insufficient)

**Preserved Content:** Steps 1/2A/2B/3 core logic, PT Description Template, Read-Merge-Write protocol, "Never" list items.

**Cross-References:**
- `agent: "pt-manager"` must match file #1 filename
- Tool assumptions must align with pt-manager.md tools list

#### RISK-8 Fallback Delta
If task list scope is isolated:
- Step 1 (TaskList discovery) fails
- **Fallback:** Dynamic Context injects TaskList output pre-fork via `!command`.
  Fork agent parses rendered output for [PERMANENT] task ID. If found, uses TaskGet
  directly. If not found, proceeds to Step 2A (create).
- **Skill change needed:** Add to Dynamic Context:
  `!cd /home/palantir && claude task list 2>/dev/null | head -20`
  Add Step 1 variant: "If Dynamic Context shows task list, parse for [PERMANENT]."

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

**Target Structure (~471L target, fork-based template):**
```
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
6. **NEW §Interface:**
   - Input: $ARGUMENTS (session-id/feature), Dynamic Context (gate records, git status), PT (all sections)
   - Output: PT-vFinal (DELIVERED), git commit, PR (optional), ARCHIVE.md
7. **Cross-Cutting:** Inline error handling (ADR-S8)
8. **REMOVE:** References to "Lead" as executor
9. **KEEP:** All 5+ user confirmation gates (AskUserQuestion in fork context)

**Preserved Content:** 9.1-9.4 core logic, 7 delivery operations, user gate protocol, idempotent design, multi-session discovery.

**Cross-References:**
- `agent: "delivery-agent"` must match file #3 filename
- Tool assumptions (Bash for git, Edit for MEMORY.md) must align with delivery-agent.md tools

#### RISK-8 Fallback Delta
Same pattern: Dynamic Context injects task list pre-fork. delivery-agent parses for PT ID.

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

**Target Structure (~452L target, fork-based template):**
```
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
6. **NEW §Interface:**
   - Input: $ARGUMENTS (optional concern), Dynamic Context (.agent/ tree, CLAUDE.md excerpt)
   - Output: Tracker update, agent memory update, terminal summary
7. **Cross-Cutting:** Inline error handling (ADR-S8)
8. **Budget constraint (~2000 tokens) PRESERVED** in core workflow

**Preserved Content:** Three-Tier Observation Window, 8 Meta-Research Lenses, AD-15 Filter, G-0→G-4 flow, tier classification logic.

**Cross-References:**
- `agent: "rsil-agent"` must match file #5 filename (same as file #7)

#### RISK-8 Fallback Delta
Minimal impact — PT is optional context for rsil-global. If isolated, skip PT read.

---

### File #7: `.claude/skills/rsil-review/SKILL.md` — Fork Restructure

**Operation:** MODIFY | **VL:** VL-3

**Current Structure (~549L):**
- Standard frontmatter — NO context:fork, NO agent:
- Lead-executed body
- R-0 → R-1 → R-2 → R-3 → R-4 → R-5 flow
- No Interface Section

**Target Structure (~549L target, fork-based template):**
```
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
5. **NEW §Interface:**
   - Input: $ARGUMENTS (target + scope), Dynamic Context (.agent/ tree, recent changes)
   - Output: Corrections applied, tracker updated, agent memory updated
6. **Cross-Cutting:** Inline error handling (ADR-S8)

**Preserved Content:** R-0→R-5 flow, 8 lens application, integration audit protocol, Layer 1/2 definitions, correction cascade logic.

**Cross-References:**
- `agent: "rsil-agent"` must match file #5 filename (same as file #6)
- R-1 Task tool spawning: subagent_type "claude-code-guide" and "codebase-researcher" must be valid

#### RISK-8 Fallback Delta
If isolated: PT optional context. R-4 PT update becomes terminal summary output instead.

---

## Group 4: coord-skills (impl-b)

> **Template Reference:** structure-architect L3 §1.2 (coordinator-based template skeleton)
> **Per-Skill Section Inventory:** structure-architect L3 §6.2
> **Interface Contract:** interface-architect L3 §1.2 (per-skill PT Read/Write table)

### Common Changes Across All 5 Skills

These changes apply to EVERY coordinator-based skill. Per-skill unique specs follow.

1. **NEW §C Interface Section** — Per interface-architect L3 §1.2 contract table:
   ```
   ## C) Interface Section
   ### Input
   - PT-v{N} (via TaskGet on PERMANENT Task)
   - Predecessor phase L1/L2/L3 files (paths from PT §Phase Status)
   - {Skill-specific inputs}
   ### Output
   - PT-v{N+1} (via TaskUpdate or /permanent-tasks)
   - Current phase L1/L2/L3 files
   - Gate record (phase-{N}/gate-record.yaml)
   ### Next
   {What next skill needs, how to invoke}
   ```

2. **GC REMOVAL (D-14):** Remove all GC write instructions (Phase N Entry Requirements).
   Remove GC read instructions for cross-phase state. Keep GC for scratch only (metrics, version).

3. **PT Discovery Protocol Change (D-7):**
   Replace: "Read GC for Phase N-1 status"
   With: "TaskGet PT → §phase_status.P{N-1}.l2_path → read predecessor L2 §Downstream Handoff"

4. **Phase 0 PT Check:** IDENTICAL canonical flow across all 5 (currently exists, verify consistency).

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

**§C Interface Section Content:**
- Input: $ARGUMENTS (feature description) — no predecessor phase (pipeline start)
- Output: PT-v1 (created by /permanent-tasks at Gate 1), GC-v3 (scratch only), Phase 3 L1/L2/L3
- Next: /agent-teams-write-plan (reads arch-coord/L2 §Downstream Handoff)

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

**§C Interface Section Content:**
- Input: PT-v{N}, Phase 3 L1/L2/L3 (paths from PT §phase_status.P3.l2_path)
- Output: PT-v{N+1} (adds Implementation Plan pointer), docs/plans/ file
- Next: /plan-validation-pipeline (reads planning-coord/L2 §Downstream Handoff)

**Per-Skill Restructure Notes:**
- Restructure Phase 4 spawn to §A template (tier-based routing)
- Preserve 10-section plan format guidance (unique)
- Preserve directive embed/reference/omit matrix (unique)
- Remove GC-v3→GC-v4 update instruction; replace with PT update

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

**§C Interface Section Content:**
- Input: PT-v{N}, Phase 4 plan file (path from PT §implementation_plan.l3_path)
- Output: Validation verdict, PT-v{N+1} if CONDITIONAL_PASS (adds mitigations)
- Next: /agent-teams-execution-plan if PASS/CONDITIONAL; /agent-teams-write-plan if FAIL

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

**§C Interface Section Content:**
- Input: PT-v{N}, Phase 4 plan, Phase 5 verdict (from planning-coord/L2 + validation-coord/L2)
- Output: PT-v{N+1} (adds Implementation Results pointer), implemented files
- Next: /verification-pipeline (reads exec-coord/L2 §Downstream Handoff)

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

**§C Interface Section Content:**
- Input: PT-v{N}, Phase 6 implementation files (from PT §implementation_results.l3_path)
- Output: PT-v{N+1} (adds Verification Summary), test results, merged code
- Next: /delivery-pipeline (reads testing-coord/L2 §Downstream Handoff)

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

**Frontmatter Changes:**
- `memory: user` → `memory: project`

**Body Changes — REMOVE (→ coordinator-shared-protocol.md):**
- §Worker Management (detailed boilerplate) — retain only research-specific routing rules
- §Communication Protocol (detailed) — REMOVE entirely
- §Understanding Verification (AD-11) — REMOVE (in shared protocol)
- §Failure Handling — REMOVE (in shared protocol)
- §Coordinator Recovery — REMOVE (in shared protocol)

**Body Changes — RETAIN (unique logic):**
- §Role: unique role + 3 workers
- §Before Starting Work: research-specific focus areas (3 bullets)
- §How to Work: research distribution rules (~7L) — route by source type (codebase/external/audit)
- §Output Format: research-specific schema notes
- §Constraints: unique constraints

---

#### File #14: `.claude/agents/verification-coordinator.md`

**Operation:** MODIFY | **VL:** VL-2 | **Current:** 107L | **Target:** ~48L

**Frontmatter Changes:**
- `memory: user` → `memory: project`

**Body Changes — REMOVE:**
- §Worker Management (detailed)
- §Communication Protocol (detailed)
- §Understanding Verification
- §Failure Handling
- §Coordinator Recovery

**Body Changes — RETAIN (unique logic):**
- §Role: unique role + 3 verifier workers
- §Before Starting Work: verification-specific focus areas
- §How to Work: Cross-Dimension Synthesis cascade rules (~10L) — unique
- §Output Format: per-dimension scores
- §Constraints: unique constraints

---

#### File #18: `.claude/agents/execution-coordinator.md`

**Operation:** MODIFY | **VL:** VL-2 | **Current:** 151L | **Target:** ~83L

**Frontmatter Changes:**
- `memory: user` → `memory: project`

**Body Changes — REMOVE:**
- §Communication Protocol (general boilerplate) — retain Consolidated Report Format (unique)
- §Understanding Verification (generic part) — REMOVE, but retain 1-2 line reference
- §Failure Handling (generic) — REMOVE, retain unique items (reviewer timeout, fix loop exhaustion)
- §Coordinator Recovery — REMOVE
- §Mode 3 Fallback — REMOVE (in shared protocol)

**Body Changes — RETAIN (ADR-S2 exemption: ~45L unique):**
- §Worker Management: full Task Distribution + Review Dispatch Protocol (AD-9) + Fix Loop Rules
- §Communication Protocol: Consolidated Report Format only (~10L)
- §Failure Handling: execution-specific items only (reviewer timeout, cross-boundary escalation)
- This is the LONGEST "How to Work" section — justified by unique review dispatch logic

---

#### File #19: `.claude/agents/testing-coordinator.md`

**Operation:** MODIFY | **VL:** VL-2 | **Current:** 118L | **Target:** ~55L

**Frontmatter Changes:**
- `memory: user` → `memory: project`

**Body Changes — REMOVE:**
- §Communication Protocol (general)
- §Understanding Verification (generic part)
- §Failure Handling (generic)
- §Coordinator Recovery

**Body Changes — RETAIN (unique logic ~20L):**
- §How to Work: Phase 7 testing → Phase 8 integration sequential lifecycle
- §How to Work: Conditional Phase 8 trigger logic
- §Constraints: "Enforce tester→integrator ordering" (unique)

---

#### File #20: `.claude/agents/infra-quality-coordinator.md`

**Operation:** MODIFY | **VL:** VL-2 | **Current:** 113L | **Target:** ~53L

**Frontmatter Changes:**
- `memory: user` → `memory: project`

**Body Changes — REMOVE:**
- §Communication Protocol (general)
- §Understanding Verification (generic)
- §Failure Handling (generic)
- §Coordinator Recovery

**Body Changes — RETAIN (unique logic ~18L):**
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
