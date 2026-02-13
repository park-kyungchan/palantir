# Structural Design — Items 1, 5, 6

> Structure Architect · ARE Lens · Phase 3 · Skill Optimization v9.0

---

## Item 1: Two Skill Template Variants

### 1.1 Fundamental Structural Distinction

The two template variants differ at the **consumer identity** level:

| Property | Coordinator-Based | Fork-Based |
|----------|:----------------:|:-----------:|
| Consumer of skill text | Lead (pipeline controller) | Fork agent (isolated subagent) |
| Execution model | Lead reads skill, orchestrates teammates | Skill body IS agent's operating instruction |
| History inheritance | Full conversation context available | No conversation history (clean start) |
| Spawn mechanism | Lead calls Task tool directly | CC forks automatically via frontmatter |
| State interface | PT + GC (session scratch) + predecessor L2 | PT (via TaskGet) + $ARGUMENTS + Dynamic Context |
| Team interaction | Creates team, spawns coordinator+workers | No team creation (operates solo or spawns own) |

This distinction drives ALL downstream structural decisions.

### 1.2 Coordinator-Based Template (5 Pipeline Core Skills)

**Applies to:** brainstorming-pipeline, agent-teams-write-plan, plan-validation-pipeline, agent-teams-execution-plan, verification-pipeline

#### Structural Skeleton

```
---
name: {skill-name}
description: "{Phase N description}. Requires Agent Teams mode and CLAUDE.md v6.0+."
argument-hint: "{hint}"
---

# {Skill Title}

{1-2 sentence purpose statement. Names the phase(s) this skill orchestrates.}

**Announce at start:** "I'm using {name} to orchestrate {phase} for this feature."

**Core flow:** {phase sequence summary}

## When to Use
{Decision tree — unique per skill}

## Dynamic Context
{!commands for session state — unique per skill}
**Feature Input:** $ARGUMENTS

---

## A) Phase 0: PERMANENT Task Check                    ← TEMPLATE SECTION
{Canonical PT check flow — IDENTICAL across 7 skills}

---

## B) Phase {N}: {Phase-Specific Workflow}              ← UNIQUE PER SKILL
{60-80% of skill content lives here}

### B.1) Input Discovery + Validation                   ← SIMILAR (criteria unique)
### B.2) Team Setup                                     ← TEMPLATE SECTION
### B.3) Spawn Section                                  ← PARTIALLY TEMPLATE

#### Tier-Based Routing (D-001)
| Tier | Route | Agents |
|------|-------|--------|
| TRIVIAL | {skill-specific} | {agents} |
| STANDARD | Lead-direct | {single agent} |
| COMPLEX | Coordinator | {coordinator + workers} |

#### Spawn Parameters
{Task tool parameters — template structure, unique values}

#### Directive Construction
{embed/reference/omit matrix — UNIQUE per skill}

#### Understanding Verification
{Probing question guidance — SIMILAR structure, unique depth}

### B.4) {Core Workflow}                                ← UNIQUE PER SKILL
### B.5) Gate {N}                                       ← SIMILAR (criteria unique)

---

## C) Interface Section

### Input
- PT-v{N} (via TaskGet on PERMANENT Task)
- Predecessor phase L1/L2/L3 files (paths from PT §Phase Status or Dynamic Context)
- {Skill-specific additional inputs}

### Output
- PT-v{N+1} (via TaskUpdate or /permanent-tasks)
- Current phase L1/L2/L3 files (in .agent/teams/{session}/phase-{N}/)
- Gate record (phase-{N}/gate-record.yaml)
- {Skill-specific additional outputs}

### Next
{What the next skill needs, how to invoke it}

---

## D) Cross-Cutting                                     ← TEMPLATE SECTION

### RTD Index
At each Decision Point, update the RTD index. Decision Points for this skill:
{DP list — unique per skill}

### Error Handling
| Situation | Response |
|-----------|----------|
{Skill-specific errors — UNIQUE per skill}

### Clean Termination
{Shutdown sequence — SIMILAR structure, unique artifacts}

## Key Principles
{4-8 principles — PARTIALLY SHARED}

## Never
{5-10 prohibitions — PARTIALLY SHARED}
```

#### Section Classification

| Section | Classification | Lines (avg) | Notes |
|---------|:-------------:|:-----------:|-------|
| Frontmatter | UNIQUE | 5L | name, description, argument-hint vary |
| Title + Intro | UNIQUE | 5L | Purpose and phase names vary |
| Announce | IDENTICAL | 1L | Template: "I'm using {name} to..." |
| When to Use | UNIQUE | 15L | Decision tree unique per skill |
| Dynamic Context | UNIQUE | 15L | !commands unique per skill |
| Phase 0 PT Check | IDENTICAL | 30L | Canonical flow, only destination varies |
| Input Discovery | SIMILAR | 25L | 5-step pattern shared; criteria unique |
| Team Setup | IDENTICAL | 5L | TeamCreate + orchestration-plan |
| Tier-Based Routing | SIMILAR | 8L | Table structure shared; agents unique |
| Spawn Parameters | SIMILAR | 10L | Task tool structure shared; types unique |
| Directive Construction | UNIQUE | 20-40L | embed/reference/omit per skill |
| Understanding Verification | SIMILAR | 15L | Flow shared; depth/questions unique |
| Core Workflow | UNIQUE | 100-350L | 60-80% of skill content |
| Gate Evaluation | SIMILAR | 20L | Table format shared; criteria unique |
| Interface Section | NEW | 15L | D-7 PT-centric (replaces GC writes) |
| RTD Index | IDENTICAL | 8L | Template text; DP list unique |
| Error Handling | SIMILAR | 10L | 5 common entries + skill-specific |
| Clean Termination | SIMILAR | 15L | 4-step pattern; artifacts vary |
| Key Principles | SIMILAR | 8L | 4 shared + skill-specific extras |
| Never | SIMILAR | 8L | 5 shared + skill-specific extras |

**Extraction yield:** ~90L IDENTICAL + ~80L SIMILAR template = ~170L per skill × 5 skills = ~850L addressable. But since each skill is still a standalone file, "extraction" means consistent structure, not literal deduplication. The template ensures structural consistency, not code sharing.

### 1.3 Fork-Based Template (4 Lead-Only+RSIL Skills)

**Applies to:** delivery-pipeline, permanent-tasks, rsil-global, rsil-review

#### Structural Skeleton

```
---
name: {skill-name}
description: "{description}"
argument-hint: "{hint}"
context: fork
agent: "{agent-name}"
---

# {Skill Title}

{Purpose statement — written for the fork agent, not for Lead.}
{This entire skill body is YOUR operating instruction.}

**Announce at start:** "{announcement}"

**Core flow:** {phase sequence}

## When to Use
{Decision tree — unique per skill}

## Dynamic Context
{!commands resolve BEFORE fork — agent sees rendered output}
**Feature Input:** $ARGUMENTS

---

## Phase 0: PERMANENT Task Check                        ← TEMPLATE SECTION
{Same canonical flow, but fork agent executes it directly}
{Uses TaskList + TaskGet (fork agents with Task API)}

---

## {Core Workflow}                                       ← UNIQUE PER SKILL
{Entire unique logic of the skill}
{Written in second person for fork agent: "Read the file", "Update the tracker"}

---

## Interface

### Input
- $ARGUMENTS: {what the invoking Lead passes}
- Dynamic Context: {session state rendered before fork}
- PT: via TaskGet on PERMANENT Task (if available)

### Output
- PT update: via TaskUpdate (if fork agent has Task API)
- File artifacts: {tracker, L1/L2/L3, ARCHIVE, MEMORY}
- Terminal summary: {displayed to invoking Lead on fork return}

---

## Cross-Cutting

### Error Handling
| Situation | Response |
|-----------|----------|
{Skill-specific errors}

## Key Principles
{Principles — unique per skill}

## Never
{Prohibitions — unique per skill}
```

#### Key Structural Differences from Coordinator-Based

| Aspect | Coordinator-Based | Fork-Based |
|--------|:-----------------:|:----------:|
| Frontmatter | name, description, argument-hint | + `context: fork`, `agent: "{name}"` |
| Voice | "Lead does X" (third person) | "You do X" (second person — fork agent) |
| Phase 0 | Lead executes | Fork agent executes |
| Team Setup | Present | Absent |
| Spawn Section | Detailed (tier routing, coordinator+workers) | Absent (fork IS the spawn) |
| Directive Section | embed/reference/omit matrix | Absent (skill body IS the directive) |
| Understanding Verification | Present | Absent (no coordinator/Lead verification loop) |
| Gate Evaluation | Present (Lead evaluates) | Absent or self-evaluated |
| Interface Section | PT + GC + L1/L2/L3 | PT + $ARGUMENTS + Dynamic Context → file artifacts |
| Clean Termination | TeamDelete, shutdown teammates | Fork auto-terminates on completion |
| Cross-Cutting | Compact Recovery, RTD, sequential-thinking refs | Error handling + principles only |

#### Fork Frontmatter → Agent .md Mapping (D-11)

| Skill | `agent:` value | Agent .md file | Key Tools |
|-------|:-------------:|:--------------:|-----------|
| permanent-tasks | `pt-manager` | .claude/agents/pt-manager.md | TaskCreate, TaskUpdate, AskUserQuestion |
| delivery-pipeline | `delivery-agent` | .claude/agents/delivery-agent.md | TaskUpdate, Bash, Edit, AskUserQuestion |
| rsil-global | `rsil-agent` | .claude/agents/rsil-agent.md | TaskUpdate, Task, Edit, AskUserQuestion |
| rsil-review | `rsil-agent` | .claude/agents/rsil-agent.md | TaskUpdate, Task, Edit, AskUserQuestion |

**Structural decision: rsil-global and rsil-review share `rsil-agent`** because:
1. Their tool requirements are identical (TaskUpdate, Task for Tier 3 spawning, Edit for applying fixes)
2. The agent .md body provides role context, but the SKILL body provides the actual operating instructions
3. The skill body (not agent .md body) differentiates behavior: Three-Tier (global) vs R-0~R-5 (review)
4. One shared agent .md reduces maintenance surface

### 1.4 Structural ADR: Template Boundary Decision

**ADR-S1: Two templates, not three**

The fork-based skills have internal structural variation (delivery-pipeline is complex with user gates, while rsil-global is relatively simple). However, the *template-level* structure is the same for all 4:

- Same frontmatter pattern: `context: fork` + `agent:` + standard fields
- Same voice: second person (fork agent)
- Same interface pattern: $ARGUMENTS + Dynamic Context + PT → file artifacts
- Same lifecycle: auto-start, execute, auto-terminate

The variation is in the *content* of the core workflow section, not in the *structural skeleton*. Therefore: 2 templates (coordinator-based + fork-based), not 3. Skill-specific complexity is handled within the UNIQUE sections of the fork-based template.

**Evidence:** All 4 fork candidates share the same structural elements (frontmatter, Phase 0, Interface, Cross-Cutting). The "simple vs complex" distinction (rsil-global vs delivery-pipeline) is about content volume, not about different section types.

---

## Item 5: Coordinator .md Convergence

### 5.1 Current State

Two templates in practice:

**Template A (verbose, 5 coordinators):** research (105L), verification (115L), execution (151L), testing (98L), infra-quality (120L)
- Avg body: 93L
- Inline shared protocol content (Worker Management, Communication Protocol, Understanding Verification, Failure Handling, Coordinator Recovery)
- Missing: reference to coordinator-shared-protocol.md
- Present: color, memory, full disallowedTools

**Template B (lean, 3 coordinators):** architecture (61L), planning (58L), validation (60L)
- Avg body: 39L
- Reference both shared protocols
- Missing: color, memory, Edit+Bash in disallowedTools

### 5.2 Unified Coordinator .md Template

**Target: Template B pattern** — reference protocols, retain only unique logic.

#### Frontmatter Schema (Complete — fills all 25 gaps)

```yaml
---
name: {coordinator-name}
description: |
  {Category} category coordinator. Manages {worker list}.
  {1-2 sentence unique description}.
  Spawned in Phase {N} ({phase name}). Max 1 instance.
model: opus
permissionMode: default
memory: project                     # was: "user" (5) or missing (3) → unified to "project"
color: {color}                      # assign to 3 missing: arch=purple, plan=orange, valid=yellow
maxTurns: {40|50|80}                # tier by category complexity
tools:
  - Read
  - Glob
  - Grep
  - Write
  - TaskList
  - TaskGet
  - mcp__sequential-thinking__sequentialthinking
disallowedTools:                    # unified 4-item list for all 8
  - TaskCreate
  - TaskUpdate
  - Edit
  - Bash
---
```

**Frontmatter decisions:**

| Field | Current | Unified | Rationale |
|-------|---------|---------|-----------|
| memory | "user" (5) / missing (3) | "project" (all 8) | Cross-session learning at project scope |
| color | present (5) / missing (3) | assigned (all 8) | Visual identification in tmux |
| disallowedTools | 4-item (5) / 2-item (3) | 4-item (all 8) | +Edit +Bash for architecture, planning, validation |
| skills | missing (all 8) | still missing (DEFER) | Token cost unfavorable (D-14/RISK-4), Dynamic Context is better |
| hooks | missing (all 8) | still missing (DEFER) | No clear need; CC hooks not well-documented |
| mcpServers | missing (all 8) | still missing (DEFER) | sequential-thinking already in tools list |

**New fields NOT adopted:** `skills:` (token cost), `hooks:` (no clear need), `mcpServers:` (no need). All deferred per YAGNI.

#### Body Structure (Unified Template)

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
{Unique orchestration logic per coordinator}
{Only content NOT covered by coordinator-shared-protocol.md}

## Output Format
Follow L1/L2 canonical format from agent-common-protocol.md.
- **L1-index.yaml:** {coordinator-specific schema notes}
- **L2-summary.md:** {coordinator-specific section notes}
- **L3-full/:** {coordinator-specific contents}

## Constraints
- Do NOT modify code or infrastructure — L1/L2/L3 output only
- Follow sub-gate protocol before reporting completion
- Write L1/L2/L3 proactively
- Write `progress-state.yaml` after every worker stage transition
{Additional unique constraints}
```

#### Sections Removed (→ protocol reference)

| Section | Was in Template A? | Now handled by |
|---------|:------------------:|----------------|
| Workers list (detailed) | Yes (5/5) | coordinator-shared-protocol.md §2 |
| Worker Management boilerplate | Yes (5/5) | coordinator-shared-protocol.md §2 |
| Communication Protocol boilerplate | Yes (5/5) | coordinator-shared-protocol.md §2.2-2.3 |
| Understanding Verification (AD-11) | Yes (5/5) | coordinator-shared-protocol.md §2.2 |
| Failure Handling boilerplate | Yes (5/5) | coordinator-shared-protocol.md §6 |
| Coordinator Recovery | Yes (5/5) | coordinator-shared-protocol.md §7 |

#### Sections Retained (unique logic only)

| Section | Unique Content | Lines Est. |
|---------|---------------|:----------:|
| Role | Unique role + worker list | 3-5L |
| Before Starting Work | Unique focus areas | 4-6L |
| How to Work | Unique orchestration logic | 0-45L |
| Output Format | Unique schema notes | 4-6L |
| Constraints | Unique additions to base | 5-8L |

#### Per-Coordinator Unique Logic Inventory

| Coordinator | Unique Logic (How to Work) | Est. Lines |
|-------------|---------------------------|:----------:|
| research | Research distribution rules (codebase/external/audit routing) | 7L |
| verification | Cross-dimension synthesis cascade rules | 10L |
| architecture | (fully delegates to protocols) | 0L |
| planning | Non-overlapping file assignment, P3→P4 handoff rules | 5L |
| validation | No understanding verification for challengers, verdict types | 5L |
| execution | Two-stage review dispatch (AD-9), fix loop rules, consolidated report format | 45L |
| testing | Sequential P7→P8 lifecycle, conditional Phase 8, per-worker examples | 20L |
| infra-quality | Score aggregation formula, cross-dimension synthesis | 18L |

#### Expected Size After Convergence

| Coordinator | Current | After Convergence | Reduction |
|-------------|:-------:|:-----------------:|:---------:|
| research | 105L | ~45L | -60L |
| verification | 115L | ~48L | -67L |
| architecture | 61L | ~38L | -23L |
| planning | 58L | ~40L | -18L |
| validation | 60L | ~40L | -20L |
| execution | 151L | ~83L | -68L |
| testing | 98L | ~55L | -43L |
| infra-quality | 120L | ~53L | -67L |
| **Total** | **768L** | **~402L** | **-366L (-48%)** |

### 5.3 Structural ADR: Coordinator Convergence Approach

**ADR-S2: Template B convergence with execution-coordinator exemption**

All 8 coordinators converge to Template B (lean, protocol-referencing). However, execution-coordinator retains a longer "How to Work" section (~45L) because its unique logic (two-stage review dispatch, fix loops, consolidated report format) is too complex to delegate entirely to protocols. This is not a Template A holdout — the unique logic is genuinely unique and must be inline.

**ADR-S3: memory: project for all coordinators**

Change from "user" to "project" for 5 coordinators, add "project" for 3 missing. Rationale: coordinators learn project-specific patterns (worker capabilities, common failure modes) that should persist at project scope, not user scope. This aligns with agent-common-protocol.md §Agent Memory (category memory is project-scoped).

**ADR-S4: Skills preload DEFERRED**

0/8 coordinators get `skills:` preload. Rationale:
- Each skill is 280-692L → 400-600L token cost per coordinator
- Dynamic Context Injection (Lead embeds relevant context at spawn time) achieves the same awareness benefit without the permanent token cost
- Skills preload is a permanent cost for every spawn; Dynamic Context is pay-per-use
- If needed later, can be added without structural changes

---

## Item 6: Per-Skill Delta from Template

### 6.1 Classification Matrix

| # | Skill | Template | Unique Lines | Template-as-is Lines | Customized Lines |
|---|-------|:--------:|:------------:|:-------------------:|:----------------:|
| 1 | brainstorming-pipeline | Coordinator | ~400L (65%) | ~90L (15%) | ~123L (20%) |
| 2 | agent-teams-write-plan | Coordinator | ~220L (61%) | ~85L (24%) | ~57L (16%) |
| 3 | plan-validation-pipeline | Coordinator | ~280L (64%) | ~88L (20%) | ~66L (15%) |
| 4 | agent-teams-execution-plan | Coordinator | ~480L (69%) | ~85L (12%) | ~127L (18%) |
| 5 | verification-pipeline | Coordinator | ~370L (64%) | ~90L (16%) | ~114L (20%) |
| 6 | delivery-pipeline | Fork | ~350L (74%) | ~50L (11%) | ~71L (15%) |
| 7 | rsil-global | Fork | ~340L (75%) | ~45L (10%) | ~67L (15%) |
| 8 | rsil-review | Fork | ~400L (73%) | ~45L (8%) | ~104L (19%) |
| 9 | permanent-tasks | Fork | ~200L (72%) | ~35L (13%) | ~44L (16%) |

### 6.2 Per-Skill Detail — Coordinator-Based

#### Skill 1: brainstorming-pipeline (613L → ~613L target)

**Template as-is sections:**
- Frontmatter (standard 3 fields): 5L
- Announce: 1L
- Phase 0 PT Check: 30L
- Team Setup: 5L
- RTD Index template: 8L
- Sequential thinking reference: 3L (moves to Cross-Cutting 1-liner)

**Template customized sections (structure shared, content unique):**
- Dynamic Context: unique !commands (project structure, git log, branches)
- Input Discovery: brainstorming-specific — no predecessor phase, uses $ARGUMENTS only
- Spawn: Phase 2 (research-coordinator or direct) + Phase 3 (architect or architecture-coordinator)
- Tier-Based Routing: unique tier table (Phase 2+3 have different routing)
- Understanding Verification: Phase 2 and Phase 3 separate verification flows
- Gate Evaluation: Gates 1, 2, 3 (three gates — more than any other skill)
- Error Handling: unique entries (user doesn't want formal pipeline, feasibility check fails)
- Clean Termination: unique artifacts (GC-v3 instead of standard GC update)
- Key Principles + Never: partially shared + brainstorming-specific items

**Unique sections (no template correspondence):**
- Phase 1: Discovery (Lead-only Q&A + feasibility check) — unique orchestration
- Phase 1.5: Gate 1 + /permanent-tasks sub-skill invocation — unique gate structure
- Phase 2: Deep Research directive construction — unique per-worker directives
- Phase 3: Architecture directive construction — unique per-architect directives
- Approach Exploration (within Phase 1) — unique discovery methodology
- Feasibility Check (AD-2) — unique brainstorming-only feature

**NEW sections needed:**
- Interface Section (C): Input ($ARGUMENTS only) → Output (PT-v{N+1}, GC-v3, Phase 3 L1/L2/L3) → Next (write-plan)

#### Skill 2: agent-teams-write-plan (362L → ~362L target)

**Template as-is sections:**
- Frontmatter: 5L
- Announce: 1L
- Phase 0 PT Check: 30L
- Team Setup: 5L
- RTD Index: 8L

**Template customized sections:**
- Dynamic Context: unique !commands (previous pipeline output, existing plans)
- Input Discovery + Validation: V-1/V-2/V-3 checks specific to Phase 3 output
- Spawn: architect (STANDARD) or planning-coordinator + 3 planners (COMPLEX)
- Directive Construction: 5-layer context (PT, GC, L2, L3 path, exemplar)
- Understanding Verification: includes "propose alternative decomposition" — unique depth
- Gate 4: 8 criteria specific to 10-section plan format
- Error Handling: brainstorming output not found, GC-v3 incomplete
- Clean Termination: GC-v3→GC-v4, PT update with plan reference

**Unique sections:**
- Phase 4.4: Plan Generation — 10-section template guidance
- User Review: plan summary presentation before gate
- Directive embed/reference/omit matrix — unique to write-plan

**NEW sections needed:**
- Interface Section (C): Input (PT-v{N}, Phase 3 L1/L2/L3) → Output (PT-v{N+1}, docs/plans/ file) → Next (validation)

#### Skill 3: plan-validation-pipeline (434L → ~434L target)

**Template as-is sections:**
- Frontmatter: 5L
- Announce: 1L
- Phase 0 PT Check: 30L
- RTD Index: 8L

**Template customized sections:**
- Dynamic Context: unique !commands (Phase 4 plan file, GC-v4)
- Input Discovery: validates Phase 4 plan existence
- Spawn: devils-advocate (STANDARD) or validation-coordinator + 3 challengers (COMPLEX)
- Gate 5: validation verdict (PASS/CONDITIONAL/FAIL)
- Error Handling: plan not found, challenger unresponsive
- Clean Termination: conditional GC update based on verdict

**Unique sections:**
- 6 Challenge Categories — unique to validation
- Verdict flow (PASS/CONDITIONAL/FAIL) — unique decision tree
- Re-verification after plan updates — unique iterative loop
- Devils-advocate-specific guidance — no understanding verification (AD exemption)

**NEW sections needed:**
- Interface Section (C): Input (PT-v{N}, Phase 4 plan) → Output (verdict, PT-v{N+1} if CONDITIONAL) → Next (execution or write-plan revision)

#### Skill 4: agent-teams-execution-plan (692L → ~692L target)

**Template as-is sections:**
- Frontmatter: 5L
- Announce: 1L
- Phase 0 PT Check: 30L
- Team Setup: 5L
- RTD Index: 8L

**Template customized sections:**
- Dynamic Context: unique !commands (Phase 4 plan, implementation task list)
- Input Discovery: validates plan + task decomposition
- Spawn: complex adaptive algorithm (implementer count from connected components)
- Directive Construction: per-implementer context layers
- Understanding Verification: per-implementer plan verification
- Gate 6: per-task + cross-task 2-level evaluation
- Error Handling: implementer crash, reviewer disagreement, cross-boundary escalation
- Clean Termination: extended (multiple implementers + reviewers to shutdown)

**Unique sections (largest unique content of all skills):**
- Adaptive Spawn Algorithm (connected components graph analysis) — unique
- Two-Stage Review (spec → code quality) — unique review dispatch
- Cross-Boundary Escalation Protocol — unique
- Fix Loop Management — unique
- execution-coordinator + execution-monitor integration — unique

**NEW sections needed:**
- Interface Section (C): Input (PT-v{N}, Phase 4 plan, Phase 5 verdict) → Output (PT-v{N+1}, implemented files) → Next (verification)

#### Skill 5: verification-pipeline (574L → ~574L target)

**Template as-is sections:**
- Frontmatter: 5L
- Announce: 1L
- Phase 0 PT Check: 30L
- Team Setup: 5L
- RTD Index: 8L

**Template customized sections:**
- Dynamic Context: unique !commands (Phase 6 output, test results)
- Input Discovery: validates Phase 6 implementation completeness
- Spawn: tester (Phase 7) then integrator (Phase 8, conditional)
- Gate 7: test coverage, contract validation
- Gate 8: integration verification (conditional)
- Error Handling: test failures, integration conflicts
- Clean Termination: conditional Phase 8 transition

**Unique sections:**
- Component Analysis Protocol — unique test design methodology
- Test Design Protocol — unique per-component test generation
- Integration Protocol — unique cross-boundary merge guidance
- Coordinator Transition (P7→P8) — unique sequential lifecycle
- Contract Test Guidance (D-014) — unique to verification

**NEW sections needed:**
- Interface Section (C): Input (PT-v{N}, Phase 6 files) → Output (PT-v{N+1}, test results, merged code) → Next (delivery)

### 6.3 Per-Skill Detail — Fork-Based

#### Skill 6: delivery-pipeline (471L → ~471L target)

**Template as-is sections:**
- Frontmatter: 5L (+ `context: fork`, `agent: delivery-agent`)
- Announce: 1L
- Phase 0 PT Check: 30L (fork agent executes directly)

**Template customized sections:**
- Dynamic Context: unique !commands (gate records, archives, git status)
- Error Handling: unique entries (git conflict, ARCHIVE too large, cleanup failure)
- Key Principles + Never: delivery-specific items

**Unique sections (most complex fork skill):**
- 9.1 Input Discovery: multi-session discovery, PT + GC dual input
- 9.2 Consolidation: PR summary, commit message generation
- 9.3 Delivery: 7 operations (PT update, MEMORY migrate, ARCHIVE create, git commit, git push, PR create, session cleanup)
- 9.4 Cleanup: classify preserve/delete for session artifacts
- Terminal Summary: final status with PR URL
- 5+ User Confirmation Gates: each delivery op needs user approval

**NEW sections needed:**
- Interface Section: Input ($ARGUMENTS, Dynamic Context, PT-v{N}) → Output (PT-v{Final}, git commit, PR, ARCHIVE.md)

**Fork-specific structural concern:** delivery-pipeline has 5+ AskUserQuestion calls. Fork agent must handle user interaction directly. The `delivery-agent` .md must include AskUserQuestion in tools.

#### Skill 7: rsil-global (452L → ~452L target)

**Template as-is sections:**
- Frontmatter: 5L (+ `context: fork`, `agent: rsil-agent`)
- Announce: 1L
- Phase 0 PT Check: 30L

**Template customized sections:**
- Dynamic Context: unique !commands (session dirs, gate records, git diff, RSIL memory)
- Error Handling: unique entries (no git diff, tier 0 misclassification, budget exceeded)
- Key Principles + Never: RSIL-specific items

**Unique sections:**
- G-0 Observation Window Classification: Type A/B/C classification
- G-1 Tiered Reading + Health Assessment: Tier 1/2 reading with 5 health indicators + 8 lens application
- G-2 Discovery (Tier 3 only): codebase-researcher spawning — **uses Task tool from fork**
- G-3 Classification + Presentation: AD-15 filter application, user presentation
- G-4 Record: tracker update, agent memory update
- Static Layer: 8 Meta-Research Lenses (embedded reference, ~40L)
- Static Layer: AD-15 Filter (embedded reference, ~25L)

**NEW sections needed:**
- Interface Section: Input ($ARGUMENTS, Dynamic Context) → Output (tracker update, agent memory update, terminal summary)

#### Skill 8: rsil-review (549L → ~549L target)

**Template as-is sections:**
- Frontmatter: 5L (+ `context: fork`, `agent: rsil-agent`)
- Announce: 1L
- Phase 0 PT Check: 30L

**Template customized sections:**
- Dynamic Context: unique !commands (target files, tracker, RSIL memory)
- Error Handling: unique entries (target not found, lens not applicable)
- Key Principles + Never: RSIL-specific items

**Unique sections (most complex RSIL skill):**
- R-0 Lead Synthesis: pre-research analysis
- R-1 Research: dual-agent spawn (claude-code-guide + codebase-researcher) — **uses Task tool from fork**
- R-2 Analysis: 8 lens application with evidence
- R-3 Integration Audit: cross-file consistency checks
- R-4 Corrections: apply FIX items, update PT, update tracker
- R-5 Commit: git operations
- Layer 1/2 Definitions: embedded reference (~30L)
- Integration Audit Protocol: unique structural analysis

**NEW sections needed:**
- Interface Section: Input ($ARGUMENTS target, Dynamic Context) → Output (corrections applied, tracker updated, agent memory updated)

#### Skill 9: permanent-tasks (279L → ~279L target)

**Template as-is sections:**
- Frontmatter: 5L (+ `context: fork`, `agent: pt-manager`)
- Announce: 1L
- Phase 0 PT Check: repurposed — Step 1 is PT discovery (structurally similar but the whole point of this skill)

**Template customized sections:**
- Dynamic Context: unique !commands (infrastructure version, recent changes, plans)
- Error Handling: unique entries (TaskList empty, TaskGet fails, description too large)
- Key Principles + Never: PT-specific items

**Unique sections:**
- Step 1: PT Discovery — TaskList search, DELIVERED handling, multi-PT deduplication
- Step 2A: Create New PT — TaskCreate with PT Description Template
- Step 2B: Update Existing PT (Read-Merge-Write) — consolidation rules, teammate notification
- Step 3: Output Summary — CREATE vs UPDATE presentation
- PT Description Template — canonical interface contract (~30L)

**NEW sections needed:**
- Interface Section: Input ($ARGUMENTS, Dynamic Context) → Output (PT-v1 or PT-v{N+1})

**Fork-specific structural concern:** permanent-tasks currently extracts from "full conversation + $ARGUMENTS" (Step 2A). In fork context, conversation is unavailable. $ARGUMENTS must carry the full payload. This is a content concern, not a template structure concern — the template skeleton is the same.

### 6.4 Summary Heatmap: Template Applicability

```
Section               BP  WP  PV  EP  VP | DP  RG  RR  PT
                     (Coordinator-Based)  | (Fork-Based)
────────────────────────────────────────────────────────────
Frontmatter           T   T   T   T   T  | Tf  Tf  Tf  Tf
Announce              T   T   T   T   T  | T   T   T   T
When to Use           U   U   U   U   U  | U   U   U   U
Dynamic Context       U   U   U   U   U  | U   U   U   U
Phase 0 PT Check      T   T   T   T   T  | T   T   T   ~
Input Discovery       C   C   C   C   C  | U   —   —   —
Team Setup            T   T   —   T   T  | —   —   —   —
Tier-Based Routing    C   C   C   —   C  | —   —   —   —
Spawn Parameters      C   C   C   C   C  | —   —   —   —
Directive Construct   U   U   U   U   U  | —   —   —   —
Understanding Verif   C   C   —   C   C  | —   —   —   —
Core Workflow         U   U   U   U   U  | U   U   U   U
Gate Evaluation       C   C   C   C   C  | —   —   —   —
Interface Section     N   N   N   N   N  | N   N   N   N
RTD Index             T   T   T   T   T  | —   —   —   —
Error Handling        C   C   C   C   C  | C   C   C   C
Clean Termination     C   C   C   C   C  | —   —   —   —
Key Principles        C   C   C   C   C  | C   C   C   C
Never                 C   C   C   C   C  | C   C   C   C

Legend: T=Template as-is, Tf=Template+fork fields, C=Customized (template structure, unique content),
        U=Unique (no template), N=New section, ~=Structurally similar but repurposed, —=Absent
```

---

## Structural Decisions Summary

| ID | Decision | Rationale |
|----|----------|-----------|
| ADR-S1 | 2 templates, not 3 | Fork complexity varies in content, not structure |
| ADR-S2 | Template B convergence, execution-coordinator extended | Unique logic (45L) justified for review dispatch |
| ADR-S3 | memory: project for all coordinators | Project-scoped learning > user-scoped |
| ADR-S4 | Skills preload DEFERRED | Token cost unfavorable; Dynamic Context better |
| ADR-S5 | Shared rsil-agent for both RSIL skills | Same tools, skill body differentiates behavior |
| ADR-S6 | Interface Section (C) is NEW for all 9 skills | D-7 PT-centric interface has no current structural home |
| ADR-S7 | Phase 0 PT Check stays in fork skills | Fork agent needs PT context; same flow, different executor |
| ADR-S8 | Cross-Cutting collapses to 1-liners for coordinator-based only | Fork skills keep inline references (no CLAUDE.md in fork agent context) |

---

## Implementation Constraints for Phase 4

1. **Big Bang (D-8):** All 9 skills + 8 coordinators + 3 new agents + CLAUDE.md §10 must be changed simultaneously
2. **YAGNI:** No speculative template features beyond what research identified
3. **Line targets:** No compression goal — reorganize, don't shrink
4. **Worker agents NOT in scope:** Only coordinator .md files are redesigned
5. **Template is structural guidance, not literal deduplication:** Each skill remains a standalone file
6. **Fork frontmatter is the ONLY mechanism change:** Everything else is content reorganization
