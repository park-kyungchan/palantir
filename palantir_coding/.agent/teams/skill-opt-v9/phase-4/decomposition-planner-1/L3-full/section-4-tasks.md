# §4 Task Breakdown

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
  See §5 Per-File Specifications, "protocol-pair" group.

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
  See §5 Per-File Specifications, "fork-cluster-1" group.

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
  - AC-7: Both skills have §Interface section with PT Read/Write per C-1 table
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
  See §5 Per-File Specifications, "fork-cluster-2" group.

  ## Acceptance Criteria
  - AC-0: For MODIFY files, read current content BEFORE editing.
  - AC-1: rsil-agent.md frontmatter matches risk-architect L3 §1.3 design
    (includes Task tool for R-1/G-2 spawning, disallowedTools: [TaskCreate])
  - AC-2: BOTH skills reference agent:"rsil-agent" (ADR-S5, same agent)
  - AC-3: rsil-global stays within ~2000 token observation budget constraint
  - AC-4: rsil-review R-1 section references Task tool for spawning
    (aligned with rsil-agent.md tools list)
  - AC-5: Both skills have §Interface section with PT Read/Write per C-1 table
  - AC-6: Both skills have RISK-8 $ARGUMENTS fallback subsection
  - AC-7: Both skills have inline cross-cutting (ADR-S8)
  - AC-8: Skill body (not agent .md) differentiates behavior between global and review

activeForm: "Creating rsil-agent and restructuring RSIL skills (cluster 2)"
```

---

## Task B: Coordinator-Based Skills (impl-b)

```
subject: "Restructure 5 coordinator-based SKILL.md files to new template"

description: |
  ## Objective
  Restructure all 5 coordinator-based skills to the new 4-section template
  (A:Spawn + B:Core Workflow + C:Interface + D:Cross-Cutting) with PT-centric
  interface (D-7), GC reduction (D-14), and coordinator spawn instructions.

  ## Context
  - Phase: 6 (Implementation)
  - Architecture: structure-architect L3 §1.2 (coordinator template skeleton),
    §6.2 (per-skill section inventory), interface-architect L3 §1.2 (PT contract)
  - Coupling Group: coord-skills (loose coupling to coordinator .md via pre-existing names)
  - Upstream: None (independent — coordinator names are pre-existing)
  - Downstream: Task V validates subagent_type references

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
  See §5 Per-File Specifications, "coord-skills" group.

  ## Acceptance Criteria
  - AC-0: For each file, read current content BEFORE editing. Verify section
    inventory matches structure-architect L3 §6.2-6.3 section classification.
  - AC-1: All 5 skills have §A (Spawn) with coordinator spawn using mode:"default" (BUG-001)
  - AC-2: All 5 skills have §B (Core Workflow) preserving 60-80% unique logic
  - AC-3: All 5 skills have §C (Interface Section) with correct PT Read/Write per C-1
  - AC-4: All 5 skills have §D (Cross-Cutting) with 1-line CLAUDE.md references
  - AC-5: All 5 skills have Phase 0 PT Check (IDENTICAL canonical flow)
  - AC-6: GC write instructions REMOVED from all 5 (D-14: GC = scratch only)
  - AC-7: GC read instructions REMOVED; replaced by PT + predecessor L2 discovery (D-7)
  - AC-8: Dynamic Context uses $ARGUMENTS for feature input
  - AC-9: Tier-Based Routing table present with correct agent types per skill
  - AC-10: Unique core workflow content preserved (not lost in restructure)

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
  See §5 Per-File Specifications, "coord-convergence" group.

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
  For each of 8 coordinator .md §Workers sections:
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
