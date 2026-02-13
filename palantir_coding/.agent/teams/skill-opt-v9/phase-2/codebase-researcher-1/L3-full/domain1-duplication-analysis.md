# Domain 1: Skill Duplication Pattern Analysis

## Raw Data — Per-Skill Section Extraction

### Skills Analyzed (9 total, 4,426 lines combined)

| # | Skill | Lines | Phase |
|---|-------|-------|-------|
| 1 | brainstorming-pipeline | 613L | P1-3 |
| 2 | agent-teams-write-plan | 362L | P4 |
| 3 | plan-validation-pipeline | 434L | P5 |
| 4 | agent-teams-execution-plan | 692L | P6 |
| 5 | verification-pipeline | 574L | P7-8 |
| 6 | delivery-pipeline | 471L | P9 |
| 7 | rsil-global | 452L | Post |
| 8 | rsil-review | 549L | Post |
| 9 | permanent-tasks | 279L | X-cut |

---

## Section-by-Section Analysis

### 1. Frontmatter

**Fields used:** `name`, `description`, `argument-hint` (all 9 skills)

**Classification:** IDENTICAL structure, UNIQUE content

```yaml
# Canonical pattern (all 9 skills):
---
name: {skill-name}
description: "{phase description}"
argument-hint: "[hint text]"
---
```

No variation in field set across all 9 skills.

### 2. Phase 0 (PERMANENT Task Check)

**Present in:** 8 of 9 skills (all except permanent-tasks, which IS the PT handler)

**Classification:** 7 IDENTICAL + 1 SIMILAR + 1 N/A

#### Group A — IDENTICAL (7 skills)
Skills: write-plan, validation, execution, verification, delivery, rsil-global, rsil-review

Canonical text (only `Continue to X.Y` destination varies):
```
Call `TaskList` and search for a task with `[PERMANENT]` in its subject.

TaskList result
     │
┌────┴────┐
found      not found
│           │
▼           ▼
TaskGet →   AskUser: "No PERMANENT Task found.
read PT     Create one for this feature?"
│           │
▼         ┌─┴─┐
Continue  Yes   No
to {X.Y}  │     │
          ▼     ▼
        /permanent-tasks    Continue to {X.Y}
        creates PT-v1       without PT
        → then {X.Y}
```

Plus 2 paragraphs about PT context and feature mismatch (also identical text).

**Variable:** Only the destination label `{X.Y}` changes: 4.1, 5.1, 6.1, 7.1, 9.1, G-0, R-0

#### Group B — SIMILAR (brainstorming-pipeline)
Different flow: handles none/1/2+ PT results differently. Creates PT at Gate 1 (not Phase 0). No /permanent-tasks invocation.

### 3. Dynamic Context

**Present in:** All 9 skills

**Classification:** UNIQUE per skill

Each skill injects different shell commands relevant to its phase:
- brainstorming: `ls -la`, `git log`, plans dir, CLAUDE.md head, `git branch`
- write-plan: pipeline output GC search, plans dir, CLAUDE.md head
- validation: pipeline output GC search, plans dir, CLAUDE.md head
- execution: plans search, pipeline output GC search, `git diff`, CLAUDE.md head
- verification: phase-6 L1 search, gate records, plans search, `git diff`, CLAUDE.md head
- delivery: gate records, archives, plans search, `git status`, CLAUDE.md head, session dirs
- rsil-global: recent sessions, gate count, L1 count, `git diff`, rsil memory, tracker
- rsil-review: hooks, settings hooks, agents, skills, CLAUDE.md head, `git diff`, protocol size, target size, rsil memory
- permanent-tasks: CLAUDE.md head, `git log`, plans dir

**Common injections across skills:**
- `head -3 /home/palantir/.claude/CLAUDE.md`: ALL 9 skills
- `ls /home/palantir/docs/plans/`: 6 of 9 (brainstorming, write-plan, validation, execution, delivery, permanent-tasks)
- `$ARGUMENTS`: ALL 9 skills
- Pipeline output GC search: 4 of 9 (write-plan, validation, execution, delivery — similar command)

### 4. Input Discovery + Validation

**Present in:** 5 of 9 skills (write-plan §4.1, validation §5.1, execution §6.1, verification §7.1, delivery §9.1)

**Classification:** SIMILAR structure, UNIQUE criteria

#### Common pattern:
1. Parse Dynamic Context
2. Look for previous phase output (GC file with specific phase status)
3. Multiple candidates → present options via AskUserQuestion
4. Single candidate → confirm with user
5. No candidates → inform user, suggest prior skill

#### Validation check table format (IDENTICAL across all 5):
```markdown
| # | Check | On Failure |
|---|-------|------------|
| V-1 | ... | Abort: "..." |
```

#### Phase-specific GC status searched:
- write-plan: `Phase 3: COMPLETE` in GC
- validation: `Phase 4: COMPLETE` in GC
- execution: `Phase 4: COMPLETE` or `Phase 5: COMPLETE` in GC
- verification: `Phase 6: COMPLETE` in GC
- delivery: Phase 7/8 gate records with `result: APPROVED`

### 5. Rollback Detection

**Present in:** 3 of 9 (validation, execution, verification)

**Classification:** IDENTICAL pattern

```
Check for `rollback-record.yaml` in downstream phase directories:
- If found: read rollback context per `pipeline-rollback-protocol.md` §3
- Include rollback context in agent directives
- If not found: proceed normally
```

Only the specific directory names differ (`phase-6/`, `phase-7/`, `phase-8/`).

### 6. Team Setup

**Present in:** 5 of 9 (brainstorming, write-plan, validation, execution, verification)

**Classification:** IDENTICAL pattern

```
TeamCreate:
  team_name: "{feature-name}-{suffix}"

Create orchestration-plan.md and copy GC-v{N} to new session directory.
```

Suffixes: (none for brainstorming), "-write-plan", "-validation", "-execution", "-verification"

### 7. Agent Spawn Patterns

**Present in:** 5 of 9 (brainstorming, write-plan, validation, execution, verification)

**Classification:** SIMILAR structure, UNIQUE configuration

#### Common 4-parameter Task tool pattern:
```
Task tool:
  subagent_type: "{type}"
  team_name: "{feature-name}-{suffix}"
  name: "{role}-{N}"
  mode: "default"
```

This exact pattern appears in all 5 spawning skills.

#### Tier-based routing table:
Present in 4 skills (write-plan, validation, execution, verification). Format IDENTICAL:
```
| Tier | Route | Agents |
|------|-------|--------|
| STANDARD | Lead-direct | ... |
| COMPLEX | Coordinator | ... |
```

### 8. Understanding Verification

**Present in:** 4 of 9 (brainstorming, write-plan, execution, verification)
**Exempt:** validation (devils-advocate exempt by design)

**Classification:** SIMILAR pattern, variable depth

Common flow:
1. Agent reads PT via TaskGet → confirms context receipt
2. Agent explains understanding to Lead
3. Lead asks N probing questions from Impact Map
4. Agent defends with evidence
5. Lead verifies or rejects (max 3 attempts)

Variable: question count and additional requirements
- brainstorming: 1 question
- write-plan: 3 questions + "propose alternative"
- execution: delegated to coordinator (AD-11), 2-level
- verification: delegated to coordinator (AD-11), 2-level

### 9. Gate Evaluation

**Present in:** 5 of 9 (brainstorming G1/G2/G3, write-plan G4, validation G5, execution G6, verification G7/G8)

**Classification:** SIMILAR structure, UNIQUE criteria

#### Common gate elements:
- Criteria table: `| # | Criterion |` format (IDENTICAL)
- On APPROVE / On ITERATE blocks (SIMILAR structure)
- "Gate Audit" clause referencing gate-evaluation-standard.md §6 (IDENTICAL text)
- gate-record.yaml output (IDENTICAL concept)
- Max 3 iterations rule (IDENTICAL)
- `sequential-thinking` for all evaluation (IDENTICAL)

#### Gate Audit variations:
- brainstorming G1: Optional for all tiers
- brainstorming G3: Mandatory for COMPLEX
- write-plan G4: Mandatory for STANDARD/COMPLEX
- validation G5: Mandatory for COMPLEX
- execution G6: Mandatory for STANDARD/COMPLEX
- verification G7: Optional STANDARD, Mandatory COMPLEX
- verification G8: Mandatory for COMPLEX

### 10. Clean Termination

**Present in:** 5 of 9 (brainstorming, write-plan, validation, execution, verification)
**Variant:** delivery (Terminal Summary), rsil-global/rsil-review (Terminal Summary), permanent-tasks (Output Summary)

**Classification:** SIMILAR pattern

Common structure:
1. Output Summary markdown block
2. Shutdown teammates via SendMessage "shutdown_request"
3. TeamDelete to clean coordination files
4. Artifacts preserved statement

Variable: summary content, shutdown target list, GC update inclusion

### 11. Cross-Cutting: RTD Index

**Present in:** ALL 9 skills

**Classification:** IDENTICAL instruction text, UNIQUE DP lists

Canonical text (verbatim in all 9):
```
At each Decision Point in this phase, update the RTD index:
1. Update `current-dp.txt` with the new DP number
2. Write an rtd-index.md entry with WHO/WHAT/WHY/EVIDENCE/IMPACT/STATUS
3. Update the frontmatter (current_phase, current_dp, updated, total_entries)
```

Only the "Decision Points for this skill:" list varies.

### 12. Cross-Cutting: Sequential Thinking

**Present in:** ALL 9 skills

**Classification:** IDENTICAL core instruction, SIMILAR details

Core instruction (present in all): "All agents use `mcp__sequential-thinking__sequentialthinking` for analysis, judgment, and verification."

5 of 9 add a per-agent timing table:
```
| Agent | When |
|-------|------|
```

### 13. Cross-Cutting: Error Handling

**Present in:** ALL 9 skills

**Classification:** SIMILAR format (table), UNIQUE content

All use the same table format:
```
| Situation | Response |
|-----------|----------|
```

Common entries across multiple skills:
- "Spawn failure → Retry once, abort with notification" (5 skills)
- "Context compact → CLAUDE.md §9 recovery" (7 skills)
- "User cancellation → Graceful shutdown, preserve artifacts" (7 skills)
- "Gate 3x iteration → Abort, present partial results" (5 skills)
- "No [prior phase] output → Inform user, suggest [prior skill]" (5 skills)

### 14. Cross-Cutting: Compact Recovery

**Present in:** 7 of 9 (all pipeline skills, not permanent-tasks or rsil-global explicitly)

**Classification:** SIMILAR pattern

Common structure:
```
- Lead: orchestration-plan → task list → gate records → L1 indexes → re-inject
- Teammates: [role-specific recovery steps]
```

### 15. Key Principles Section

**Present in:** ALL 9 skills

**Classification:** SIMILAR format, UNIQUE + overlapping content

Common principles across most skills:
- "Sequential thinking always" — 8 of 9
- "Protocol delegated — CLAUDE.md owns verification, skill owns orchestration" — 6 of 9
- "Clean termination / No auto-chaining" — 8 of 9
- "Artifacts preserved" — 8 of 9
- "Task descriptions follow task-api-guideline.md v6.0 §3" — 3 of 9

### 16. Never Section

**Present in:** ALL 9 skills

**Classification:** SIMILAR format, UNIQUE + overlapping content

Common "Never" items across multiple skills:
- "Auto-chain to [next skill] after termination" — 7 of 9
- "Proceed past Gate without all criteria met" — 5 of 9
- "Let teammates write to Task API" — 4 of 9
- "Skip understanding verification" — 3 of 9
- "Skip Phase 0 PERMANENT Task check" — 3 of 9

### 17. "When to Use" Decision Tree

**Present in:** ALL 9 skills

**Classification:** IDENTICAL format (ASCII decision tree), UNIQUE content

### 18. "Announce at start" Pattern

**Present in:** ALL 9 skills

**Classification:** IDENTICAL pattern

```
"I'm using {skill-name} to orchestrate {Phase} for this feature."
```

### 19. "vs." Comparison Line

**Present in:** 4 of 9 (brainstorming, write-plan, execution, verification)

**Classification:** SIMILAR pattern

```
"vs. {solo-skill} (solo): This skill spawns [teams]. Solo {skill} [does inline]. Use this when [justification]."
```

---

## Duplication Matrix

| Section | BP | WP | PV | EP | VP | DP | RG | RR | PT | Classification |
|---------|----|----|----|----|----|----|----|----|----|----|
| Frontmatter | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | IDENTICAL structure |
| Phase 0 PT Check | S | I | I | I | I | I | I | I | — | 7 IDENTICAL, 1 SIMILAR |
| Dynamic Context | U | U | U | U | U | U | U | U | U | UNIQUE |
| When to Use | U | U | U | U | U | U | U | U | U | UNIQUE |
| Announce at start | I | I | I | I | I | I | I | I | I | IDENTICAL pattern |
| Input Discovery | — | S | S | S | S | S | — | — | — | SIMILAR (5 skills) |
| Rollback Detection | — | — | I | I | I | — | — | — | — | IDENTICAL (3 skills) |
| Team Setup | I | I | I | I | I | — | — | — | — | IDENTICAL (5 skills) |
| Spawn Patterns | S | S | S | S | S | — | — | — | — | SIMILAR (5 skills) |
| Tier-Based Routing | S | S | S | — | S | — | — | — | — | SIMILAR (4 skills) |
| Understanding Verif | S | S | — | S | S | — | — | — | — | SIMILAR (4 skills) |
| Gate Evaluation | S | S | S | S | S | — | — | — | — | SIMILAR (5 skills) |
| Clean Termination | S | S | S | S | S | S | S | S | S | SIMILAR (9 skills) |
| RTD Index | I | I | I | I | I | I | I | I | I | IDENTICAL text |
| Sequential Thinking | I | I | I | I | I | I | I | I | I | IDENTICAL core |
| Error Handling | S | S | S | S | S | S | S | S | S | SIMILAR format |
| Compact Recovery | S | S | S | S | S | S | — | S | — | SIMILAR (7 skills) |
| Key Principles | S | S | S | S | S | S | S | S | S | SIMILAR + overlap |
| Never Section | S | S | S | S | S | S | S | S | S | SIMILAR + overlap |

**Legend:** BP=brainstorming, WP=write-plan, PV=plan-validation, EP=execution-plan, VP=verification, DP=delivery, RG=rsil-global, RR=rsil-review, PT=permanent-tasks
I=IDENTICAL, S=SIMILAR, U=UNIQUE, —=Not present

---

## Duplication Quantification

### IDENTICAL sections (highest extraction potential):
1. **Phase 0 PT Check** — ~30 lines × 7 skills = ~210 lines duplicated
2. **RTD Index instructions** — ~8 lines × 9 skills = ~72 lines duplicated
3. **Sequential Thinking core** — ~3 lines × 9 skills = ~27 lines duplicated
4. **Rollback Detection** — ~5 lines × 3 skills = ~15 lines duplicated
5. **Announce at start** — ~1 line × 9 skills = ~9 lines duplicated
6. **Team Setup** — ~5 lines × 5 skills = ~25 lines duplicated

**Total IDENTICAL duplication: ~358 lines** (8.1% of 4,426 total)

### SIMILAR sections (partial extraction potential):
1. **Input Discovery + Validation** — ~40 lines template × 5 skills = ~200 lines
2. **Error Handling** — ~12 lines per skill × 9 skills = ~108 lines (commonizable: ~50%)
3. **Clean Termination** — ~25 lines × 5 pipeline skills = ~125 lines
4. **Compact Recovery** — ~5 lines × 7 skills = ~35 lines
5. **Key Principles** — ~10 lines × 9 skills = ~90 lines (commonizable: ~40%)
6. **Never Section** — ~8 lines × 9 skills = ~72 lines (commonizable: ~30%)
7. **Gate Evaluation structure** — ~20 lines framework × 5 skills = ~100 lines
8. **Spawn Patterns** — ~8 lines × 5 skills = ~40 lines
9. **Understanding Verification** — ~15 lines × 4 skills = ~60 lines

**Total SIMILAR duplication (extractable portion): ~450 lines** (~10.2% of total)

### Combined extractable duplication: ~808 lines (18.3% of 4,426 total)

---

## Unique Orchestration Logic (Cannot Be Templated)

### brainstorming-pipeline (UNIQUE sections):
- Phase 1 Discovery (Lead-only): Structured Recon, Freeform Q&A, Category Awareness, Feasibility Check
- Phase 1.2.5 Checkpoint (anti-compact)
- Phase 1.3 Approach Exploration (comparison table)
- Phase 1.4 Scope Crystallization
- Phase 2 Research Scope Determination (researcher count algorithm)
- Phase 3 Architecture Design (component design flow)
- User Architecture Review

### agent-teams-write-plan (UNIQUE sections):
- Phase 4.1 Validation criteria (GC-v3 specific sections)
- Directive Construction (5-layer context embedding)
- 10-section plan template references (AC-0, V6, §5 specs)
- Read-First-Write-Second workflow

### plan-validation-pipeline (UNIQUE sections):
- Challenge Categories (C-1 through C-6)
- Challenge Targets (per-section targets)
- Verdict Evaluation (PASS/CONDITIONAL_PASS/FAIL flow)
- FAIL re-verification multi-turn exchange

### agent-teams-execution-plan (UNIQUE sections):
- Adaptive Spawn Algorithm (dependency graph → components → implementer count)
- Execution Coordinator [DIRECTIVE] construction (8-layer)
- Review Prompt Templates (spec-reviewer, code-reviewer)
- Two-stage review flow (spec → quality, coordinator-mediated)
- Phase 6.4.5 Mid-Execution User Update
- Cross-Boundary Issue Escalation protocol
- Per-task gate evaluation

### verification-pipeline (UNIQUE sections):
- Component Analysis (pipeline shape decision)
- Adaptive Tester Count algorithm
- Test Design Protocol (5-step)
- Phase 8 Integration Protocol (conditional phase)
- Conflict Resolution Principles
- Testing-Integration coordinator transition

### delivery-pipeline (UNIQUE sections):
- Multi-session discovery algorithm (6-step)
- Op-1: Final PT Update
- Op-2: PT → MEMORY.md Migration (with user confirmation)
- Op-3: ARCHIVE.md Creation (with template)
- Op-4: Git Commit (with Conventional Commits)
- Op-5: PR Creation
- Op-6: Session Artifact Cleanup (preserve/delete classification)
- Op-7: Task List Cleanup

### rsil-global (UNIQUE sections):
- G-0 Observation Window Classification (Type A/B/C)
- Three-Tier Reading system (Tier 1/2/3)
- Health Indicator Assessment (H-1 through H-5)
- Lens Application During Reading
- Tier escalation decisions
- AD-15 Filter
- G-4 Record (tracker + agent memory update)

### rsil-review (UNIQUE sections):
- R-0 Lead Synthesis (4-step: parse → target read → lens → axes → directives)
- Layer 1/Layer 2 definitions (comprehensive)
- Integration Audit Methodology
- Output Format specification (dual-agent)
- R-1 Parallel Research (dual agent spawn)
- R-2 Synthesis + Classification (merge + AD-15)
- R-3 Application

### permanent-tasks (UNIQUE sections):
- Step 1 PERMANENT Task Discovery (including DELIVERED handling)
- Step 2A Create New (PT Description Template)
- Step 2B Read-Merge-Write (consolidation rules: dedup, resolve, elevate)
- Teammate Notification Decision
- PT Description Template (5-section interface contract)
