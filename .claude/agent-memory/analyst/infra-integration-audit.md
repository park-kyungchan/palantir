# INFRA Integration Audit Report

**Date:** 2026-02-15
**Scope:** Cross-component integration of .claude/ INFRA (35 skills, 6 agents, 5 hooks, settings, CLAUDE.md)
**Methodology:** 5-axis integration analysis (pipeline flow, agent-skill compatibility, hook coverage, tier boundaries, failure paths)
**Prior Component Audit:** 9.2/10 health (v3 final sweep)

---

## Audit 1: Pipeline Flow Traversal

### 1.1 TRIVIAL Path: P0 -> P7 -> P9

```
  P0                          P7                          P9
  +-------------------+       +-------------------+       +-------------------+
  | brainstorm        |--+--->| execution-code    |------>| delivery-pipeline |
  | (user request)    |  |    | (implementer)     |       | (delivery-agent)  |
  +-------------------+  |    +-------------------+       +-------------------+
                         |    | execution-infra   |------>|                   |
                         +--->| (infra-impl)      |       |                   |
                              +-------------------+       +-------------------+
```

**OUTPUT_TO chain analysis:**

| Step | Skill | OUTPUT_TO declared | Next expected | Match? |
|------|-------|--------------------|---------------|--------|
| 1 | brainstorm | pre-design-validate | P7 execution-code | BREAK |
| 2 | execution-code | execution-impact, execution-review, verify domain | delivery-pipeline | INDIRECT |
| 3 | delivery-pipeline | Git repository, MEMORY.md | (terminal) | OK |

**FINDING INT-01 [MEDIUM]: TRIVIAL tier has no direct routing path from P0 to P7.**

Brainstorm's OUTPUT_TO points to `pre-design-validate`, not to execution skills. For TRIVIAL tier (P0->P7->P9), the Lead must perform an implicit routing jump from brainstorm output directly to execution-code, skipping validate/feasibility/design/research/plan/orchestration. This jump is not documented in any skill's OUTPUT_TO chain.

**Impact:** Lead must rely on CLAUDE.md Section 2 tier table to know it should skip phases. The skill L1 metadata provides no routing signal for this jump. Lead's routing intelligence (Section 3: "Routes via Skill L1 WHEN conditions") has insufficient data for the TRIVIAL shortcut.

**FINDING INT-02 [LOW]: execution-code OUTPUT_TO does not mention delivery-pipeline.**

execution-code outputs to `execution-impact, execution-review, verify domain`. For TRIVIAL tier, the expected next step after code is P9 (delivery-pipeline), but execution-code does not list it. The chain goes: execution-code -> execution-review -> verify domain -> delivery-pipeline. This means TRIVIAL still traverses P7's internal review + P8's verify domain before reaching P9.

**Implication:** The TRIVIAL path is NOT actually P0->P7->P9. It is effectively P0->P7->P8->P9 (with P8 implicit via execution-review -> verify). The declared tier "P0->P7->P9" in CLAUDE.md is misleading.

---

### 1.2 STANDARD Path: P0 -> P2 -> P3 -> P4 -> P7 -> P8 -> P9

```
P0 (pre-design)          P2 (design)              P3 (research)
+---------+  +---------+ +---------+  +---------+ +---------+  +---------+
|brainstorm|->|validate |->|feasibil.|->|architect|->|interface|->|codebase |
+---------+  +---------+ +---------+  +---------+  +---------+ +---------+
                                       |           |            ||
                                       v           v            vv
                                      +---------+ +---------+ +---------+
                                      |  risk   | |interface| | external|
                                      +---------+ +---------+ +---------+
                                                               |
                                                               v
                                                              +---------+
                                                              |  audit  |
                                                              +---------+
                                                               |
P4 (plan)                P7 (execution)           P8 (verify)  v
+---------+  +---------+ +---------+  +---------+ +---------+ +----------+
|decompose|->|interface|->|code/infra|->|impact  |->|structure|->|delivery |
+---------+  +---------+ +---------+  +---------+ +---------+ +----------+
             |           |            |           |            |
             v           v            v           v            |
            +---------+ +---------+  +---------+ +---------+  |
            |strategy | | review  |<-|cascade  | | content |  |
            +---------+ +---------+  +---------+ +---------+  |
                                                  |            |
                                                  v            |
                                                 +---------+   |
                                                 |consistncy|  |
                                                 +---------+   |
                                                  |            |
                                                  v            |
                                                 +---------+   |
                                                 | quality |   |
                                                 +---------+   |
                                                  |            |
                                                  v            |
                                                 +---------+   |
                                                 |cc-feas. |-->+
                                                 +---------+
```

**Full OUTPUT_TO -> INPUT_FROM chain:**

| # | Source Skill | OUTPUT_TO | Target Skill | TARGET's INPUT_FROM | Bidirectional? |
|---|-------------|-----------|-------------|---------------------|----------------|
| 1 | brainstorm | pre-design-validate | validate | pre-design-brainstorm | YES |
| 2 | validate | pre-design-feasibility (PASS) or brainstorm (FAIL) | feasibility | pre-design-validate | YES |
| 3 | feasibility | design-architecture | architecture | pre-design-feasibility | YES |
| 4 | architecture | design-interface, design-risk, research domain | interface | design-architecture | YES |
| 5 | architecture | design-interface, design-risk, research domain | risk | design-architecture, design-interface | PARTIAL (risk's INPUT also needs interface) |
| 6 | interface | design-risk, plan-interface | risk (for risk assessment) | design-architecture, design-interface | YES |
| 7 | risk | research domain, plan-strategy | research-codebase | design domain (generic) | PARTIAL |
| 8 | architecture | (implicit via design domain completion) | research-codebase | design domain (architecture decisions) | YES (generic match) |
| 9 | research-codebase | research-audit, plan-decomposition | research-audit | research-codebase, research-external | YES |
| 10 | research-external | research-audit, plan-strategy | research-audit | research-codebase, research-external | YES |
| 11 | research-audit | plan-decomposition, design domain (if gaps) | plan-decomposition | research-audit, design-architecture | YES |
| 12 | plan-decomposition | plan-interface, plan-strategy, orchestration-decompose | plan-interface | plan-decomposition, design-interface | YES |
| 13 | plan-interface | plan-strategy, orchestration-assign | plan-strategy | plan-decomposition, plan-interface, design-risk, research-audit | YES |
| 14 | plan-strategy | orchestration-decompose, plan-verify domain | plan-verify-correctness | plan-strategy, design-architecture | YES |
| 15 | plan-strategy | (same) | plan-verify-completeness | plan-strategy, pre-design-validate | PARTIAL* |
| 16 | plan-strategy | (same) | plan-verify-robustness | plan-strategy, design-risk | YES |
| 17 | execution-code | execution-impact, execution-review, verify domain | execution-impact | execution-code, on-implementer-done.sh | YES |
| 18 | execution-impact | execution-cascade (if recommended), execution-review | execution-cascade | execution-impact | YES |
| 19 | execution-cascade | execution-review, execution-impact (re-invoke) | execution-review | execution-code/infra/impact/cascade, design domain | YES |
| 20 | execution-review | verify domain (PASS) or execution-code/infra (FAIL) | verify-structure | execution domain | YES |
| 21 | verify-structure | verify-content (PASS) or execution (FAIL) | verify-content | verify-structure | YES |
| 22 | verify-content | verify-consistency (PASS) or execution (FAIL) | verify-consistency | verify-content | YES |
| 23 | verify-consistency | verify-quality (PASS) or execution (FAIL) | verify-quality | verify-consistency | YES |
| 24 | verify-quality | verify-cc-feasibility (PASS) or execution (FAIL) | verify-cc-feasibility | verify-quality | YES |
| 25 | verify-cc-feasibility | delivery-pipeline (all PASS) or execution (FAIL) | delivery-pipeline | verify domain (all-PASS) | YES |

**FINDING INT-03 [LOW]: plan-strategy does not list plan-verify-completeness in OUTPUT_TO.**

plan-strategy OUTPUT_TO says: `orchestration-decompose (execution strategy), plan-verify domain (complete plan for validation)`. It uses "plan-verify domain" generically. plan-verify-completeness INPUT_FROM says: `plan-strategy (complete plan), pre-design-validate (original requirements for coverage)`. This is a minor specificity gap -- plan-strategy uses generic domain reference rather than listing all 3 plan-verify skills.

**FINDING INT-04 [LOW]: design-risk OUTPUT_TO uses generic "research domain" rather than naming research-codebase/external.**

design-risk OUTPUT_TO says: `research domain (risk areas for codebase validation), plan-strategy (risk mitigation for strategy)`. The research skills INPUT_FROM says: `design domain (architecture decisions, interface designs needing codebase validation)`. Both use generic domain references. This works because Lead routes by domain, but specific skill-to-skill traceability is lost.

**FINDING INT-05 [MEDIUM]: STANDARD path skips P5 (plan-verify) and P6 (orchestration).**

CLAUDE.md declares STANDARD path as `P0->P2->P3->P4->P7->P8->P9`. But:
- plan-strategy OUTPUT_TO points to both `orchestration-decompose` AND `plan-verify domain`
- orchestration-decompose INPUT_FROM requires `plan-verify domain (PASS verdict)`
- execution-code INPUT_FROM requires `orchestration-verify (validated task-teammate matrix)`

For STANDARD tier, if P5 and P6 are skipped, execution-code has NO routing signal to start. Its WHEN condition says: "orchestration domain complete (all 3 PASS)". This WHEN condition cannot be satisfied if orchestration is skipped.

**Impact:** Either:
(a) STANDARD actually runs P5+P6 silently (making it P0->P2->P3->P4->P5->P6->P7->P8->P9, essentially COMPLEX), OR
(b) Lead must override execution-code's WHEN condition for STANDARD tier and route directly from plan-strategy to execution-code.

Neither option is documented. This is the most significant integration gap found.

---

### 1.3 COMPLEX Path: P0 -> P9 (all phases)

```
P0 ---------> P2 ---------> P3 ---------> P4 ---------> P5 ---------> P6 ---------> P7 ---------> P8 ---------> P9
brainstorm    architecture   codebase      decomposition  correctness   decompose     code/infra    structure     delivery
validate      interface      external      interface      completeness  assign        impact        content
feasibility   risk           audit         strategy       robustness    verify        cascade       consistency
                                                                                      review        quality
                                                                                                    cc-feasibility
```

**COMPLEX path analysis:**

The COMPLEX path works correctly because all skills have properly chained OUTPUT_TO -> INPUT_FROM:
- P4 plan-strategy -> P5 plan-verify-* (all three)
- P5 plan-verify-* -> P6 orchestration-decompose (if all PASS)
- P6 orchestration-verify -> P7 execution domain (after PASS)
- P7 execution-review -> P8 verify-structure
- P8 verify-cc-feasibility -> P9 delivery-pipeline

**FINDING INT-06 [ADVISORY]: orchestration-decompose INPUT_FROM says "plan-verify domain (PASS verdict), plan-decomposition (task list with dependencies)".**

It takes input from BOTH plan-verify AND plan-decomposition. This is correct -- it needs the validated plan AND the original task breakdown. The bidirectionality with plan-decomposition is partial: plan-decomposition OUTPUT_TO includes orchestration-decompose, but plan-decomposition also outputs to plan-interface and plan-strategy. This is acceptable for a many-to-one relationship.

---

### 1.4 Pipeline Flow Summary

| Tier | Declared Path | Actual Traversal | Gap? |
|------|--------------|------------------|------|
| TRIVIAL | P0->P7->P9 | P0->P7->(P8)->P9 | YES: P8 traversed implicitly |
| STANDARD | P0->P2->P3->P4->P7->P8->P9 | P0->P2->P3->P4->(?P5->P6)->P7->P8->P9 | YES: P5/P6 skip undocumented |
| COMPLEX | P0->P9 (all) | P0->P9 (all) | NO: fully chained |

---

## Audit 2: Agent-Skill Tool Compatibility

### 2.1 Agent Tool Profiles

| Agent | Profile | Tools Available | Cannot |
|-------|---------|-----------------|--------|
| analyst | B | Read, Glob, Grep, Write, sequential-thinking | Edit, Bash, Task, Web |
| researcher | C | Read, Glob, Grep, Write, WebSearch, WebFetch, sequential-thinking, context7, tavily | Edit, Bash, Task |
| implementer | D | Read, Glob, Grep, Edit, Write, Bash, sequential-thinking | Task, Web |
| infra-implementer | E | Read, Glob, Grep, Edit, Write, sequential-thinking | Bash, Task, Web |
| delivery-agent | F | Read, Glob, Grep, Edit, Write, Bash, TaskList, TaskGet, TaskUpdate, AskUserQuestion | TaskCreate |
| pt-manager | G | Read, Glob, Grep, Write, TaskList, TaskGet, TaskCreate, TaskUpdate, AskUserQuestion | Edit, Bash |

### 2.2 Skill -> Agent Mapping

| Skill | Spawns Agent | Required Capabilities | Tools Match? |
|-------|-------------|----------------------|--------------|
| **P0 pre-design-brainstorm** | analyst (STANDARD), or Lead-direct (TRIVIAL) | Read, analysis, Write | YES |
| **P0 pre-design-validate** | analyst | Read, analysis, Write | YES |
| **P0 pre-design-feasibility** | researcher ("claude-code-guide" or researcher) | Web access, Read, Write | ISSUE* |
| **P2 design-architecture** | analyst | Read, analysis, Write | YES |
| **P2 design-interface** | analyst | Read, analysis, Write | YES |
| **P2 design-risk** | analyst | Read, analysis, Write | YES |
| **P3 research-codebase** | analyst ("Spawn analyst") | Read, Glob, Grep, Write | YES |
| **P3 research-external** | researcher ("Spawn researcher") | Web access, Read, Write | YES |
| **P3 research-audit** | analyst ("Spawn analyst") | Read, analysis, Write | YES |
| **P4 plan-decomposition** | analyst | Read, analysis, Write | YES |
| **P4 plan-interface** | analyst | Read, analysis, Write | YES |
| **P4 plan-strategy** | analyst | Read, analysis, Write | YES |
| **P5 plan-verify-correctness** | analyst | Read, analysis, Write | YES |
| **P5 plan-verify-completeness** | analyst | Read, analysis, Write | YES |
| **P5 plan-verify-robustness** | analyst | Read, analysis, Write | YES |
| **P6 orchestration-decompose** | Lead-direct (always) | Auto-loaded frontmatter | YES (no spawn) |
| **P6 orchestration-assign** | Lead-direct (always) | Auto-loaded frontmatter | YES (no spawn) |
| **P6 orchestration-verify** | Lead-direct (TRIVIAL/STANDARD), analyst (COMPLEX) | Read, analysis | YES |
| **P7 execution-code** | implementer | Edit, Bash, Read, Grep | YES |
| **P7 execution-infra** | infra-implementer | Edit, Write, Read, Grep | YES |
| **P7 execution-impact** | researcher ("Spawn researcher") | Read, Grep, Write, Web (optional) | PARTIAL** |
| **P7 execution-cascade** | implementer | Edit, Read, Grep, Write | YES |
| **P7 execution-review** | analyst ("Spawn analyst") | Read, Grep, Write | YES |
| **P8 verify-structure** | analyst | Read, Glob, Grep, Write | YES |
| **P8 verify-content** | analyst | Read, Write | YES |
| **P8 verify-consistency** | analyst | Read, Grep, Write | YES |
| **P8 verify-quality** | analyst | Read, Write | YES |
| **P8 verify-cc-feasibility** | analyst + "claude-code-guide" | Read, Write, Web (optional) | ISSUE* |
| **P9 delivery-pipeline** | delivery-agent | Edit, Bash, TaskUpdate, AskUserQuestion | YES |
| **X-cut pipeline-resume** | analyst (optional) | Read, TaskList, TaskGet | ISSUE*** |
| **X-cut task-management** | pt-manager | TaskCreate, TaskUpdate, Read, Write | YES |
| **Homeo manage-infra** | analyst | Read, Glob, Grep, Write | YES |
| **Homeo manage-skills** | analyst | Read, Glob, Grep, Write | YES |
| **Homeo manage-codebase** | analyst | Read, Glob, Grep, Write | YES |
| **Homeo self-improve** | "claude-code-guide" + infra-implementer | Web (research), Edit (fixes) | ISSUE* |

### 2.3 Compatibility Findings

**FINDING INT-07 [HIGH]: "claude-code-guide" is referenced as a spawnable agent but does not exist as a defined agent.**

Three skills reference "claude-code-guide" as something to spawn:
- `pre-design-feasibility`: "Spawn claude-code-guide to check..."
- `verify-cc-feasibility`: "Spawn claude-code-guide agent..."
- `self-improve`: "Spawn claude-code-guide (if unavailable, use cc-reference cache)"

There is NO agent file at `.claude/agents/claude-code-guide.md`. This is not a defined agent type. All three skills include fallback text: "(if unavailable, use cc-reference cache in agent-memory)" -- but this fallback is only explicitly stated in self-improve and the feasibility L2 body. The pre-design-feasibility L1 description does NOT include this fallback.

**Impact:** Lead attempting to spawn `subagent_type: claude-code-guide` will fail. The fallback to cc-reference cache or spawning a researcher with web access works but is not consistently documented.

**FINDING INT-08 [MEDIUM]: execution-impact spawns researcher, but researcher has no Bash tool for running grep commands.**

execution-impact methodology says: "Spawn researcher for grep-based reverse reference analysis". The researcher agent has Grep tool (the CC native Grep), which is sufficient. However, the L2 methodology section references shell-style `grep -rl` commands. The researcher agent uses the CC Grep tool, not Bash grep. This is a documentation inconsistency -- the CC Grep tool IS available to the researcher and provides equivalent functionality.

**Revised assessment:** The researcher CAN perform the required grep analysis using its CC Grep tool. The shell-style grep syntax in the methodology is illustrative, not prescriptive. No actual capability gap.

**FINDING INT-09 [MEDIUM]: pipeline-resume L2 says "spawn analyst for complex state reconstruction" but analyst lacks Task API tools.**

pipeline-resume methodology Step 5 says "Re-spawn agents for in-progress tasks with full context" and its execution model mentions "analyst" for STANDARD/COMPLEX. But an analyst cannot call TaskList, TaskGet, or TaskCreate. The pipeline-resume L2 methodology steps 1-2 explicitly use TaskList/TaskGet -- these must be Lead-direct operations. The analyst spawn in STANDARD/COMPLEX would only assist with analysis of the recovered state, not with Task API calls.

**Impact:** LOW -- Lead performs Task API calls directly, analyst only helps with analysis. But the skill's execution model could be clearer about this split.

---

## Audit 3: Hook-Pipeline Integration

### 3.1 Hook Configuration Summary

| Hook | Event | Matcher | Timeout | Async | Script |
|------|-------|---------|---------|-------|--------|
| SubagentStart | Agent spawn | "" (all) | 10s | no | on-subagent-start.sh |
| PreCompact | Before compaction | "" (all) | 30s | no | on-pre-compact.sh |
| SessionStart | After compaction | "compact" | 15s | no | on-session-compact.sh |
| PostToolUse | Edit or Write | "Edit\|Write" | 5s | YES | on-file-change.sh |
| SubagentStop | Implementer done | "implementer" | 30s | no | on-implementer-done.sh |

### 3.2 Hook-to-Phase Mapping

```
Pipeline Phase:   P0   P1   P2   P3   P4   P5   P6   P7        P8   P9
                  |    |    |    |    |    |    |    |           |    |
SubagentStart:    *----*----*----*----*----*----*----*-----------*----*
                  (fires on every agent spawn in every phase)

PostToolUse:      -----+----+----+----+----+----+----*-----------*----*
                  (fires on Edit/Write anywhere, but P0-P2 are Lead-only
                   -- Lead editing files would trigger this, but per
                   Section 2.1 Lead never edits files directly)

SubagentStop:     -----------------------------------------------*----+
                  (matcher: "implementer" -- only fires P7 execution-code
                   and P7 execution-cascade when implementers finish)

PreCompact:       *----*----*----*----*----*----*----*-----------*----*
                  (can fire at any phase if context runs out)

SessionStart:     *----*----*----*----*----*----*----*-----------*----*
(compact)         (recovery after compaction at any phase)
```

### 3.3 Hook Coverage Analysis

**FINDING INT-10 [MEDIUM]: SubagentStop matcher "implementer" misses infra-implementer agents.**

The SubagentStop hook only matches "implementer" (line 92 of settings.json). When infra-implementer agents complete (spawned by execution-infra), no SubagentStop hook fires. This means:
- SRC Stage 2 (impact injection) only activates for code implementers, not infra implementers
- File changes made by infra-implementer are logged by PostToolUse (Stage 1) but never summarized to Lead via Stage 2
- execution-impact only receives SRC IMPACT ALERT for code changes, not infra changes

**Impact:** If execution-infra modifies .claude/ files (e.g., skill descriptions, hook scripts), those changes are tracked in the /tmp log but never injected as an impact alert. Lead must manually invoke execution-impact for infra changes or ignore SRC for infra-only modifications.

**Mitigation assessment:** The execution-impact INPUT_FROM does say "execution-code (file change manifest)" -- it takes the manifest directly, not just the hook alert. Lead CAN route to execution-impact after infra completion by reading the /tmp log manually. But the automatic hook-driven flow is broken for infra-implementer.

**FINDING INT-11 [LOW]: PostToolUse fires during P0-P2 Lead-only phases, logging analyst/researcher Write operations.**

P0-P2 use "run_in_background" agents (Section 2.1). If an analyst spawned during P2 design-architecture uses Write to produce output, PostToolUse fires and logs the file. This is harmless but adds noise to the /tmp change log. When an implementer later fires SubagentStop, the change log may contain P0-P2 analyst output files mixed with P7 code changes.

**Impact:** The on-implementer-done.sh script reads ALL entries from the session log, including P0-P2 analyst writes. These will appear as "changed files" in the SRC IMPACT ALERT. The impact alert may contain false positives (design documents mistakenly listed as code changes).

**Mitigation:** The grep-based reverse reference search in on-implementer-done.sh filters by searching for references -- analyst output files in agent-memory are excluded by the `--exclude-dir=agent-memory` flag. But any analyst output written outside agent-memory would be captured.

**FINDING INT-12 [ADVISORY]: No hook fires when analyst or researcher agents complete.**

SubagentStop matcher is "implementer" only. When analyst agents complete (used in P0-P5, P7 review, P8 verify), no hook injects their results. This is by design -- analyst results are consumed via Task API or direct L1/L2 reading. No integration gap, just documenting the design decision.

### 3.4 Hook Phase Coverage Matrix

| Phase | SubagentStart | PostToolUse | SubagentStop | PreCompact | SessionStart |
|-------|:------------:|:-----------:|:------------:|:----------:|:------------:|
| P0 (pre-design) | YES (analyst) | LOW* | -- | YES | YES |
| P2 (design) | YES (analyst) | LOW* | -- | YES | YES |
| P3 (research) | YES (analyst/researcher) | LOW* | -- | YES | YES |
| P4 (plan) | YES (analyst) | LOW* | -- | YES | YES |
| P5 (plan-verify) | YES (analyst) | LOW* | -- | YES | YES |
| P6 (orchestration) | RARELY** | -- | -- | YES | YES |
| P7 (execution) | YES (impl/infra) | YES | PARTIAL*** | YES | YES |
| P8 (verify) | YES (analyst) | LOW* | -- | YES | YES |
| P9 (delivery) | YES (delivery-agent) | YES | -- | YES | YES |

\* PostToolUse fires on analyst Write but provides limited value pre-P7.
\** Orchestration is mostly Lead-direct; analyst only for COMPLEX verify.
\*** SubagentStop only fires for "implementer", not "infra-implementer" (INT-10).

---

## Audit 4: Tier Boundary Logic

### 4.1 P0-P2: Lead-Only Verification

CLAUDE.md Section 2.1: "P0-P2 (PRE-DESIGN + DESIGN): Lead-only. Brainstorm, validate, feasibility, architecture, interface, risk -- all executed by Lead with local agents (run_in_background). No Team infrastructure needed."

**Checking skill L2 bodies for P0-P2 compliance:**

| Skill | TRIVIAL | STANDARD | COMPLEX | Team API refs? | Compliant? |
|-------|---------|----------|---------|---------------|------------|
| brainstorm | Lead-direct | 1-2 analysts (run_in_background) | 2-4 agents (run_in_background) | No | YES |
| validate | Lead-direct | analyst (run_in_background) | 2 agents (run_in_background) | No | YES |
| feasibility | Lead-direct | researcher (run_in_background) | 2 agents (run_in_background) | No | YES |
| architecture | Lead-direct | analyst (run_in_background) | 2-4 agents (run_in_background) | No | YES |
| interface | Lead-direct | analyst (run_in_background) | 2-4 agents (run_in_background) | No | YES |
| risk | Lead-direct | analyst (run_in_background) | 2-4 agents (run_in_background) | No | YES |

All P0-P2 skills correctly use "run_in_background" language and do NOT reference TeamCreate, TaskCreate, or SendMessage. COMPLIANT.

### 4.2 P3+: Team Infrastructure Verification

CLAUDE.md Section 2.1: "P3+ (RESEARCH through DELIVERY): Team infrastructure. TeamCreate, TaskCreate/Update, SendMessage for teammate coordination."

**Checking skill L2 bodies for P3+ compliance:**

| Skill | Spawn language | Team API refs? | Compliant? |
|-------|---------------|---------------|------------|
| research-codebase | "Spawn analyst" | No explicit Team API | PARTIAL |
| research-external | "Spawn researcher" | No explicit Team API | PARTIAL |
| research-audit | "Spawn analyst" | No explicit Team API | PARTIAL |
| plan-decomposition | "Spawn analyst" | No explicit Team API | PARTIAL |
| plan-interface | "Spawn analyst" | No explicit Team API | PARTIAL |
| plan-strategy | "Spawn analyst" | No explicit Team API | PARTIAL |
| plan-verify-* (3) | "Spawn analyst" | No explicit Team API | PARTIAL |
| orchestration-* (3) | "Lead-direct" | No explicit Team API | PARTIAL |
| execution-code | "Create Task with subagent_type: implementer" | YES (Task API) | YES |
| execution-infra | "Create Task with subagent_type: infra-implementer" | YES (Task API) | YES |
| execution-impact | "Spawn researcher agent with subagent_type: researcher" | YES (Task API) | YES |
| execution-cascade | "Spawn implementers with subagent_type: implementer" | YES (Task API) | YES |
| execution-review | "Spawn analyst" | No explicit Team API | PARTIAL |
| verify-* (5) | "Spawn analyst" | No explicit Team API | PARTIAL |
| delivery-pipeline | "delivery-agent (subagent_type: delivery-agent)" | YES (implicit) | YES |

**FINDING INT-13 [LOW]: P3-P5 and P8 skills say "Spawn analyst" without specifying Team API (TaskCreate) or run_in_background.**

These skills use ambiguous spawn language. They say "Spawn analyst" (or "Spawn researcher") without clarifying whether this means:
(a) `run_in_background` (Lead-only local agent, P0-P2 style), or
(b) TaskCreate with `subagent_type` (Team infrastructure, P3+ style)

The execution-* skills are explicit: "Create Task with `subagent_type: implementer`". Research/plan/verify skills are not.

**Impact:** Lead must infer the spawn mechanism. Since these are P3+ phases, Team infrastructure should be used. But the skill L2 bodies don't explicitly say so. For P3 research skills, this ambiguity means Lead might use either mechanism interchangeably.

**Practical impact:** Low -- both mechanisms work (Task tool and run_in_background both spawn agents). But it creates inconsistency in the infrastructure.

### 4.3 P2->P3 Handoff (Lead-Only to Team)

**FINDING INT-14 [MEDIUM]: No explicit handoff mechanism between P2 (Lead-only) and P3 (Team infrastructure).**

The transition from P2 to P3 requires:
1. P2 design outputs exist as Lead-internal context or written documents
2. P3 must access these outputs
3. If P2 was Lead-only (run_in_background), outputs are in Lead's conversation context
4. P3 Team agents need these outputs passed to them

The handoff relies on Lead manually including P2 outputs in P3 agent spawn prompts. No skill documents this handoff explicitly. The design-risk OUTPUT_TO says "research domain" -- but doesn't specify how outputs are transmitted across the Lead-only/Team boundary.

**Impact:** In practice, Lead carries P2 context and passes it to P3 agents via TaskCreate prompts. This works but is fragile -- if Lead compacts between P2 and P3, the P2 outputs could be lost (mitigated by PreCompact hook saving task state, but design outputs aren't in Task API).

---

## Audit 5: Failure and Recovery Paths

### 5.1 Failure Path Inventory

| Skill | FAIL OUTPUT_TO | Destination | Loop? | Termination? |
|-------|---------------|-------------|-------|-------------|
| validate | pre-design-brainstorm | P0 restart | A->B->A | Max 3 iterations |
| feasibility | brainstorm (scope reduction) | P0 restart | A->B->C->A | Max 3 revision iterations |
| research-audit | design domain (critical gaps) | P2 feedback | P3->P2->P3 | Max 3 re-research |
| plan-verify-correctness | plan domain (revision) | P4 rework | P5->P4->P5 | Max 3 iterations per phase |
| plan-verify-completeness | plan domain (revision) | P4 rework | P5->P4->P5 | Max 3 iterations |
| plan-verify-robustness | plan domain (revision) | P4 rework | P5->P4->P5 | Max 3 iterations |
| orchestration-verify | orchestration-assign (re-assign) | P6 retry | P6.3->P6.2->P6.3 | Implicit max 3 |
| execution-review | execution-code/infra (FAIL) | P7 fix loop | P7.5->P7.1/2->P7.5 | Max 3 review-fix |
| execution-cascade | execution-impact (re-invoke) | P7 re-impact | P7.4->P7.3->P7.4 | Max 3 iterations |
| verify-structure | execution domain (FAIL) | P7 rework | P8->P7->P8 | Max 3 iterations per phase |
| verify-content | execution domain (FAIL) | P7 rework | P8->P7->P8 | Max 3 |
| verify-consistency | execution domain (FAIL) | P7 rework | P8->P7->P8 | Max 3 |
| verify-quality | execution domain (FAIL) | P7 rework | P8->P7->P8 | Max 3 |
| verify-cc-feasibility | execution domain (FAIL) | P7 rework | P8->P7->P8 | Max 3 |
| delivery-pipeline | Lead (if verify not all-PASS) | Abort | No loop | Terminal abort |

### 5.2 Failure Path Diagrams

**P0 Internal Loop:**
```
brainstorm <---FAIL--- validate ---PASS---> feasibility ---PASS---> P2
   ^                                             |
   +-------------------FAIL (scope reduce)-------+

   Termination: Max 3 iterations per skill, max 3 revision iterations
```

**P5->P4 Feedback Loop:**
```
plan-strategy ----> plan-verify-correctness  ---+
                    plan-verify-completeness ---+--FAIL--> plan domain (P4)
                    plan-verify-robustness   ---+              |
                         ^                                     |
                         +--------- re-verify after P4 fix ---+

   Termination: Max 3 iterations per phase (CLAUDE.md Section 2)
```

**P7 Internal Loop:**
```
execution-code/infra ---> execution-impact --cascade_recommended--> execution-cascade
        ^                       ^                                          |
        |                       +------- convergence check ----------------+
        |
        +---------- FAIL ---------- execution-review <----- (from cascade)

   Termination: cascade max 3 iterations, review max 3 fix iterations
```

**P8->P7 Feedback Loop:**
```
verify-structure --FAIL--> execution domain (P7)
verify-content   --FAIL--> execution domain (P7)
verify-consistency --FAIL--> execution domain (P7)
verify-quality   --FAIL--> execution domain (P7)
verify-cc-feasibility --FAIL--> execution domain (P7)
        ^                          |
        +---- re-verify after fix -+

   Termination: Max 3 iterations per phase
```

### 5.3 Failure Path Findings

**FINDING INT-15 [MEDIUM]: P8->P7 failure loop is ambiguous about which P7 skill to route to.**

All 5 verify skills say "or execution domain (if FAIL, fix required)" on failure. But the "execution domain" has 5 skills. Which one should receive the failure?

- If the failure is in YAML frontmatter (verify-structure FAIL) -> execution-infra
- If the failure is in code implementation (verify-content FAIL) -> execution-code
- If the failure is cross-file inconsistency (verify-consistency FAIL) -> execution-code OR execution-infra (unclear)

The verify skills don't specify which execution sub-skill to route failures to. Lead must infer based on the failure type.

**FINDING INT-16 [LOW]: Nested failure loops could theoretically produce deep recursion.**

Consider: P8 verify-consistency FAILS -> P7 execution-code fixes -> P7 execution-review re-reviews -> P7 review FAILS -> P7 execution-code re-fixes -> (loop within P7) -> P8 re-verify -> P8 FAILS again.

This creates nested loops: P8->P7(fix->review->fix->review)->P8. The outer loop (P8->P7->P8) has "max 3 iterations per phase", and the inner loop (P7 review->fix) also has "max 3 review-fix iterations". In theory:
- 3 P8->P7 outer loops x 3 inner fix-review loops = 9 total execution cycles
- Plus 3 cascade iterations per execution = 27 cascade passes maximum

This is bounded but could be expensive in practice.

**FINDING INT-17 [ADVISORY]: delivery-pipeline has no retry loop -- it aborts on any verify FAIL.**

delivery-pipeline says: "If any FAIL: abort delivery, report to Lead for fix loop". This is correct terminal behavior -- delivery should not retry autonomously. The Lead receives the abort and must re-route through the appropriate fix path. No issue.

### 5.4 Missing Failure Paths

**FINDING INT-18 [MEDIUM]: No failure path defined for P3 (research) skills.**

- research-codebase: OUTPUT_TO only specifies success paths (research-audit, plan-decomposition). No FAIL path.
- research-external: OUTPUT_TO only specifies success paths. No FAIL path.
- research-audit: Has a FAIL path back to design domain (critical gaps). But research-codebase and research-external do not.

What happens if research-codebase finds zero codebase evidence? Or if research-external cannot validate any dependency? These scenarios are unaddressed. The skills always produce output (even if findings are minimal), so the assumption is "research never fails, just produces thin results." This may be acceptable but differs from the pattern in other domains.

**FINDING INT-19 [LOW]: No failure path defined for P6 orchestration-decompose.**

orchestration-decompose OUTPUT_TO only specifies: `orchestration-assign (decomposed tasks ready for teammate mapping)`. No failure path. If decomposition fails (e.g., tasks cannot be grouped within 4-teammate limit), the skill has no documented recovery. orchestration-verify handles assignment validation, but decomposition-level failures are unaddressed.

---

## Audit 6: Cross-Cutting Integration Issues

### 6.1 SRC (Smart Reactive Codebase) Integration

```
PostToolUse:Edit/Write      SubagentStop:implementer
       |                            |
       v                            v
on-file-change.sh           on-implementer-done.sh
(logs to /tmp)              (reads /tmp, greps, injects to Lead)
       |                            |
       v                            v
/tmp/src-changes-*.log       additionalContext -> Lead
                             "SRC IMPACT ALERT"
                                    |
                                    v
                             Lead routes to execution-impact
                                    |
                                    v
                             execution-cascade (if recommended)
```

**SRC Integration Findings:**

- PostToolUse is async (async: true) -- file logging happens non-blocking. Good.
- SubagentStop is sync -- impact injection blocks until complete (30s timeout). Good for ensuring Lead receives the alert.
- Session ID links the two stages (PostToolUse logs with session_id, SubagentStop reads same session_id). Correct.
- on-implementer-done.sh cleans up the log file after reading (line 99: `rm -f "$LOGFILE"`). This means if multiple implementers run sequentially, only the last one's changes are captured.

**FINDING INT-20 [HIGH]: Sequential implementer spawns lose earlier implementer's file changes.**

If Lead spawns implementer-1, it finishes (SubagentStop fires, log read and deleted), then Lead spawns implementer-2, it finishes (SubagentStop fires for its own shorter log). The file changes from implementer-1 are already deleted from the log before implementer-2 even starts.

In parallel spawning (multiple implementers at once), all file changes accumulate in the SAME log file (same session_id). When the FIRST implementer finishes, SubagentStop fires and reads ALL accumulated changes -- but the other implementers may not have finished writing yet.

**Scenario analysis:**
- **Parallel implementers, staggered completion:** Implementer-1 finishes first. SubagentStop reads log and finds changes from impl-1 and partial changes from impl-2 (whatever was written so far). Then `rm -f` deletes the log. When impl-2 finishes, SubagentStop fires but the log is gone.
- **Sequential implementers:** Log deleted between spawns. Second implementer's SubagentStop only sees its own changes.

**Impact:** This is a real data loss bug. The SRC impact analysis may miss file changes from implementers that finished later or whose changes weren't fully logged before the first SubagentStop fired.

**Mitigation:** The on-implementer-done.sh already noted in src-risk-assessment.md as RPN 168 (false convergence). The execution-code skill's L2 says "consolidate results" after ALL implementers complete -- Lead should invoke execution-impact with the full manifest from L1 outputs, not rely solely on the hook alert.

### 6.2 Task API Integration Points

```
pt-manager <--- /task-management ---> PT (PERMANENT Task)
                                         |
delivery-agent <--- /delivery-pipeline --+ (TaskUpdate: DELIVERED)
                                         |
SubagentStart hook ---> additionalContext: "Use TaskGet on [PERMANENT]"
                                         |
SessionStart(compact) ---> "TaskList to see all tasks"
                                         |
PreCompact ---> Saves task snapshots to /tmp
```

The Task API integration is well-connected:
- SubagentStart injects PT context reference to every spawned agent
- PreCompact preserves task state before compaction
- SessionStart(compact) provides recovery instructions
- delivery-agent marks PT as DELIVERED
- pt-manager manages full lifecycle

No integration gaps found in Task API chain.

### 6.3 Context Budget Integration

| Component | Budget Impact | Risk |
|-----------|-------------|------|
| 35 skill L1 descriptions | ~28,565/32,000 chars (89%) | HIGH utilization |
| 6 agent L1 descriptions | Auto-loaded in Task tool def | Separate budget |
| CLAUDE.md | ~47 lines, always loaded | Fixed cost |
| MEMORY.md | Variable, truncated at 200 lines | Managed |
| additionalContext (hooks) | Ephemeral, single-turn | Low risk |
| Skill L2 bodies | Loaded only on invocation | On-demand |

**FINDING INT-21 [ADVISORY]: L1 budget at 89% leaves only ~3,435 chars for future skills.**

At 28,565/32,000 chars used, adding a single new skill would push to ~90-91%. Adding 3+ skills would require trimming existing descriptions or increasing the SLASH_COMMAND_TOOL_CHAR_BUDGET env var.

---

## Summary

### Finding Inventory

| ID | Severity | Category | Summary |
|----|----------|----------|---------|
| INT-01 | MEDIUM | Pipeline Flow | TRIVIAL tier: no direct OUTPUT_TO from P0 to P7 |
| INT-02 | LOW | Pipeline Flow | TRIVIAL actually traverses P7->P8->P9, not P7->P9 |
| INT-03 | LOW | Pipeline Flow | plan-strategy uses generic "plan-verify domain" in OUTPUT_TO |
| INT-04 | LOW | Pipeline Flow | design-risk uses generic "research domain" in OUTPUT_TO |
| INT-05 | MEDIUM | Pipeline Flow | STANDARD path: P5/P6 skip is undocumented in skill chains |
| INT-06 | ADVISORY | Pipeline Flow | orchestration-decompose has multi-source INPUT_FROM |
| INT-07 | HIGH | Agent-Skill | "claude-code-guide" referenced but not a defined agent type |
| INT-08 | MEDIUM | Agent-Skill | execution-impact L2 uses shell grep syntax, but researcher uses CC Grep (cosmetic) |
| INT-09 | MEDIUM | Agent-Skill | pipeline-resume analyst lacks Task API (actually Lead-direct) |
| INT-10 | MEDIUM | Hook-Pipeline | SubagentStop only matches "implementer", misses infra-implementer |
| INT-11 | LOW | Hook-Pipeline | PostToolUse logs P0-P2 analyst writes (noise in SRC log) |
| INT-12 | ADVISORY | Hook-Pipeline | No SubagentStop for analyst/researcher (by design) |
| INT-13 | LOW | Tier Boundary | P3-P5/P8 skills use ambiguous "Spawn" without specifying mechanism |
| INT-14 | MEDIUM | Tier Boundary | No explicit P2->P3 handoff (Lead-only to Team) |
| INT-15 | MEDIUM | Failure Path | P8 failure routes to generic "execution domain" -- unclear sub-skill |
| INT-16 | LOW | Failure Path | Nested P8->P7->P8 loops bounded but potentially expensive |
| INT-17 | ADVISORY | Failure Path | delivery-pipeline aborts on FAIL (correct terminal behavior) |
| INT-18 | MEDIUM | Failure Path | P3 research-codebase/external have no FAIL paths defined |
| INT-19 | LOW | Failure Path | P6 orchestration-decompose has no FAIL path |
| INT-20 | HIGH | SRC | Sequential/parallel implementer SubagentStop deletes log, losing data |
| INT-21 | ADVISORY | Budget | L1 budget at 89%, limited headroom |

### Severity Distribution

| Severity | Count |
|----------|-------|
| HIGH | 2 |
| MEDIUM | 7 |
| LOW | 7 |
| ADVISORY | 5 |
| **Total** | **21** |

### Top 3 Integration Risks

1. **INT-20 [HIGH]: SRC log deletion on first SubagentStop** -- Real data loss risk when multiple implementers are involved. The rm -f in on-implementer-done.sh (line 99) deletes the change log after the FIRST implementer finishes, losing data for subsequent or concurrent implementers.

2. **INT-07 [HIGH]: Ghost agent "claude-code-guide"** -- Three skills reference an agent that doesn't exist. Fallback documentation is inconsistent. Lead attempting to spawn this will fail at runtime.

3. **INT-05 [MEDIUM]: STANDARD tier P5/P6 skip gap** -- The skill-level routing chain requires P5 and P6 (execution-code WHEN condition needs orchestration domain PASS), but STANDARD tier skips these phases. No documentation explains how Lead should bridge this gap.

### Agent-Skill Compatibility Matrix (Condensed)

```
                 analyst  researcher  implementer  infra-impl  delivery  pt-mgr
                   (B)       (C)         (D)         (E)        (F)      (G)
P0 brainstorm      X
P0 validate        X
P0 feasibility              X(*)
P2 architecture    X
P2 interface       X
P2 risk            X
P3 codebase        X
P3 external                  X
P3 audit           X
P4 decomposition   X
P4 interface       X
P4 strategy        X
P5 correctness     X
P5 completeness    X
P5 robustness      X
P6 decompose       (Lead-direct)
P6 assign          (Lead-direct)
P6 verify          X
P7 code                                  X
P7 infra                                              X
P7 impact                    X
P7 cascade                               X
P7 review          X
P8 structure       X
P8 content         X
P8 consistency     X
P8 quality         X
P8 cc-feasibility  X(*)
P9 delivery                                                     X
X  resume          X(partial)
X  task-mgmt                                                              X
H  manage-infra    X
H  manage-skills   X
H  manage-codebase X
H  self-improve              (*)                      X

(*) = references "claude-code-guide" which does not exist as an agent
```

### Hook Coverage Map (Condensed)

```
               SubStart  PostTool  SubStop  PreCompact  SessionStart
P0 pre-design    [x]       [~]      [ ]       [x]          [x]
P2 design        [x]       [~]      [ ]       [x]          [x]
P3 research      [x]       [~]      [ ]       [x]          [x]
P4 plan          [x]       [~]      [ ]       [x]          [x]
P5 plan-verify   [x]       [~]      [ ]       [x]          [x]
P6 orchestrate   [~]       [ ]      [ ]       [x]          [x]
P7 execution     [x]       [x]      [~]       [x]          [x]
P8 verify        [x]       [~]      [ ]       [x]          [x]
P9 delivery      [x]       [x]      [ ]       [x]          [x]

[x] = fully active, [~] = partially active, [ ] = not active
```

---

## Overall Integration Score

| Axis | Score (1-10) | Rationale |
|------|:---:|-----------|
| Pipeline Flow (P0->P9) | 6.5 | COMPLEX path fully chained; TRIVIAL/STANDARD have undocumented gaps |
| Agent-Skill Compatibility | 7.5 | 32/35 skills match correctly; 3 reference phantom agent |
| Hook-Pipeline Integration | 7.0 | SRC log deletion bug; infra-implementer SubagentStop gap |
| Tier Boundary Logic | 7.5 | P0-P2 compliant; P3+ spawn language ambiguous; P2->P3 handoff implicit |
| Failure and Recovery | 7.0 | All loops bounded; P3/P6 missing FAIL paths; P8->P7 routing ambiguous |

**Overall Integration Score: 7.1 / 10**

Component health is excellent (9.2/10), but integration has meaningful gaps especially in tier-specific routing and SRC hook lifecycle management. The COMPLEX tier path works well end-to-end. The TRIVIAL and STANDARD tiers rely on Lead intelligence to bridge gaps that should be documented in skill metadata.

### Priority Recommendations

1. **Fix on-implementer-done.sh log deletion** (INT-20): Change `rm -f` to an append-and-mark strategy, or move deletion to execution-impact after reading the full manifest.
2. **Define "claude-code-guide" handling** (INT-07): Either create a minimal agent file, or consistently document the fallback (spawn researcher with web scope) across all 3 referencing skills.
3. **Document STANDARD tier P5/P6 handling** (INT-05): Either explicitly state STANDARD runs P5+P6 (updating CLAUDE.md tier table), or add override documentation to execution-code skill for non-orchestrated invocation.
4. **Add infra-implementer to SubagentStop matcher** (INT-10): Change matcher from `"implementer"` to `"implementer|infra-implementer"` or use empty matcher with script-level filtering.
5. **Specify P8 failure sub-routing** (INT-15): Each verify skill should specify whether failures route to execution-code or execution-infra based on failure type.
