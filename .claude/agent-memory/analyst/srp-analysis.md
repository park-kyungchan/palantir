# SRP Analysis of .claude/ INFRA

> Analyst: SRP (Single Responsibility Principle) audit of entire .claude/ infrastructure
> Date: 2026-02-15
> Scope: 35 skills, 6 agents, 5 hooks, settings, CLAUDE.md
> Input: All SKILL.md files, all agent .md files, all hook scripts, settings.json

---

## Part 1: SRP Violations in Existing Skills

### Assessment Criteria

For each skill, I evaluate whether the L2 body contains:
- Multiple **distinct** responsibilities (not just multiple steps in one responsibility)
- Methodology steps that are separable into independent skills
- Concerns that are unrelated to the primary skill name/domain

A skill with 5 steps all serving one goal is NOT a violation. A skill that does
two unrelated things under one name IS.

### Skills with SRP Violations

#### SRP-01: `self-improve` (SEVERITY: HIGH)

**File**: `/home/palantir/.claude/skills/self-improve/SKILL.md`

**Evidence**: This skill does FIVE distinct responsibilities in its L2 body:
1. **CC native research** (Step 1) -- spawning claude-code-guide, reading cc-reference cache, updating reference files
2. **INFRA diagnostics** (Step 2) -- field compliance, routing integrity, budget analysis, hook validity, settings consistency
3. **Implementation** (Step 3) -- spawning infra-implementer agents for fixes
4. **Verification** (Step 4) -- re-scanning all files, verifying routing and budget
5. **Git operations** (Step 5) -- staging, committing, updating MEMORY.md

**Violation details**:
- Step 1 is `research-external` territory (web research for CC capabilities)
- Step 2 is `manage-infra` territory (health diagnostics)
- Step 3 is `execution-infra` territory (spawning infra-implementers)
- Step 4 is `verify-*` territory (structural + content + CC feasibility checks)
- Step 5 is `delivery-pipeline` territory (commit + archive)

This skill is essentially a **mini-pipeline** (research -> diagnose -> fix -> verify -> commit) compressed into a single skill. It overlaps with at least 5 other skills.

**SRP assessment**: This is the most severe violation. The skill owns the entire improvement lifecycle rather than a single responsibility. However, it may be *intentionally designed as an orchestration shortcut* for a common workflow.

**Recommendation**: TOLERATE with documentation. The self-improve workflow is intentionally a compressed end-to-end cycle. Splitting it into 5 separate invocations would be impractical for its use case (periodic maintenance). The compression is a design decision, not an oversight. Add a comment in the SKILL.md noting this is an intentional pipeline-in-a-skill.

---

#### SRP-02: `task-management` (SEVERITY: MEDIUM)

**File**: `/home/palantir/.claude/skills/task-management/SKILL.md`

**Evidence**: This skill has 6 distinct operations:
1. PT Creation
2. PT Update (Read-Merge-Write)
3. Work Task Batch Creation
4. Real-Time Update Protocol
5. ASCII Visualization
6. PT Completion

**Violation details**:
- Operations 1-2 (PT lifecycle) are conceptually different from Operation 3 (work task batch creation from plan outputs)
- Operation 5 (ASCII visualization) is a reporting/display concern, not a lifecycle management concern
- The skill recognizes this internally by routing "heavy ops" to pt-manager and "light ops" to Lead-direct

**SRP assessment**: MODERATE violation. The skill covers two distinct responsibility clusters:
(A) Task CRUD operations (create, update, complete PT + batch create work tasks)
(B) Task visualization/status reporting (ASCII viz)

**Recommendation**: TOLERATE. The Task API is a single external tool surface, and splitting would create overhead for a tightly coupled concern. The internal routing (heavy vs light ops) already handles the split practically. The ASCII visualization, while different in nature, is inseparable from the task state it displays.

---

#### SRP-03: `execution-review` (SEVERITY: LOW)

**File**: `/home/palantir/.claude/skills/execution-review/SKILL.md`

**Evidence**: The skill has a 2-stage methodology:
1. Stage 1: **Spec compliance review** (design decisions)
2. Stage 2: **Code quality review** (patterns, conventions, security)
3. Optional: **Contract review** for interface compliance

**Violation details**:
- Spec compliance (does it match the architecture?) and code quality (is it well-written?) are conceptually distinct review dimensions
- The skill acknowledges this by spawning separate analysts per stage

**SRP assessment**: MINOR violation. Both stages serve the same overarching responsibility: "validate implementation quality." The two-stage approach is a methodology choice, not a responsibility split. Splitting into `execution-review-spec` and `execution-review-quality` would create unnecessary overhead.

**Recommendation**: TOLERATE. This is a single responsibility (implementation validation) with two sub-concerns. The skill already handles this by using separate analysts.

---

#### SRP-04: `manage-codebase` (SEVERITY: LOW)

**File**: `/home/palantir/.claude/skills/manage-codebase/SKILL.md`

**Evidence**: The skill handles three modes:
1. Full generation (initial scan)
2. Incremental update (post-pipeline)
3. Staleness detection (maintenance)

**Violation details**:
- Full generation is a fundamentally different operation from incremental update
- Staleness detection is a monitoring concern separate from map construction

**SRP assessment**: MINOR violation. All three modes serve the same single responsibility: "maintain codebase dependency map." The modes are just different execution paths for one responsibility. The `argument-hint: "[full|incremental]"` cleanly separates them.

**Recommendation**: TOLERATE. Single artifact ownership (codebase-map.md) with multiple maintenance strategies is acceptable SRP.

---

#### SRP-05: `design-risk` (SEVERITY: LOW)

**File**: `/home/palantir/.claude/skills/design-risk/SKILL.md`

**Evidence**: The methodology covers three analysis dimensions:
1. Failure Mode Analysis (FMEA)
2. Security Assessment (OWASP)
3. Performance Analysis (bottlenecks)

**Violation details**:
- FMEA, security, and performance are distinct analytical domains
- A dedicated security audit skill could go deeper

**SRP assessment**: MINOR. All three serve the single responsibility of "risk identification." Risk naturally has multiple dimensions. Splitting by dimension would be premature abstraction.

**Recommendation**: TOLERATE. Risk analysis inherently spans multiple concern areas. The FMEA framework unifies them under a single methodology.

---

### Skills with Clean SRP (No Violations)

The remaining 30 skills have clean single-responsibility ownership:

| Skill | Single Responsibility |
|-------|----------------------|
| pre-design-brainstorm | Requirement gathering via questions |
| pre-design-validate | Requirement completeness check |
| pre-design-feasibility | CC capability feasibility check |
| design-architecture | Component structure definition |
| design-interface | Interface contract definition |
| research-codebase | Local codebase pattern discovery |
| research-external | External documentation research |
| research-audit | Finding consolidation + gap analysis |
| plan-decomposition | Task breakdown from architecture |
| plan-interface | Inter-task contract specification |
| plan-strategy | Execution sequencing + risk mitigation |
| plan-verify-correctness | Logical correctness validation |
| plan-verify-completeness | Coverage gap detection |
| plan-verify-robustness | Edge case + failure mode challenge |
| orchestration-decompose | Task-to-group decomposition |
| orchestration-assign | Group-to-agent assignment |
| orchestration-verify | Assignment validation |
| execution-code | Source code implementer spawning |
| execution-infra | Infra implementer spawning |
| execution-impact | Post-implementation dependency analysis |
| execution-cascade | Recursive affected-file updating |
| verify-structure | File structural integrity |
| verify-content | Content completeness check |
| verify-consistency | Cross-file relationship integrity |
| verify-quality | Routing effectiveness scoring |
| verify-cc-feasibility | CC native field compliance |
| manage-infra | INFRA health monitoring |
| manage-skills | Skill lifecycle management |
| delivery-pipeline | Pipeline-end delivery |
| pipeline-resume | Session recovery |

### Part 1 Summary

| ID | Skill | Severity | Verdict |
|----|-------|----------|---------|
| SRP-01 | self-improve | HIGH | TOLERATE (intentional pipeline-in-skill) |
| SRP-02 | task-management | MEDIUM | TOLERATE (tightly coupled API surface) |
| SRP-03 | execution-review | LOW | TOLERATE (sub-concerns of one responsibility) |
| SRP-04 | manage-codebase | LOW | TOLERATE (multiple modes for one artifact) |
| SRP-05 | design-risk | LOW | TOLERATE (risk spans dimensions by nature) |

**Bottom line**: No skills require splitting. The 5 flagged violations are all cases where compression is intentional or the sub-concerns are too tightly coupled to separate.

---

## Part 2: Uncovered Responsibilities (CREATE Candidates)

### Current L1 Budget Context

From `settings.json`: `SLASH_COMMAND_TOOL_CHAR_BUDGET: 32000`
Current usage: ~84% (~26,880 chars), leaving ~5,120 chars headroom.
Each new skill description requires ~800-1024 chars of L1 budget.
Maximum new skills before budget exhaustion: ~5-6 at 800 chars each.

### Candidate Analysis

#### CAND-01: Integration Verification

**Proposed responsibility**: Verify cross-component pipeline flow -- INPUT_FROM/OUTPUT_TO chains resolve end-to-end, skill-agent-hook wiring is complete, and pipeline routing would work for TRIVIAL/STANDARD/COMPLEX tiers.

**Domain**: verify (would become skill 6 of 6)

**Distinct methodology?**: YES.
- The existing 5 verify-* skills check INDIVIDUAL component health:
  - verify-structure: file-level integrity (does YAML parse?)
  - verify-content: content completeness (are orchestration keys present?)
  - verify-consistency: reference bidirectionality (does A ref B and B ref A?)
  - verify-quality: routing effectiveness (is WHEN specific enough?)
  - verify-cc-feasibility: native field compliance (all fields are CC native?)
- NONE of these verify that the **entire pipeline would work end-to-end**:
  - Does a TRIVIAL task route through P0->P7->P9 without hitting a dead end?
  - Does the COMPLEX tier's P0->P9 chain have all required skill handoffs?
  - Are there skills that output to a skill that doesn't accept that input?
  - Do agent profile capabilities actually match the skill requirements they're assigned to?

**Evidence of gap**: The INFRA integration audit (`/home/palantir/.claude/agent-memory/analyst/infra-integration-audit.md`) scored Integration Health at 7.1/10 vs Component Health at 9.2/10. This 2.1-point gap exists precisely because no skill owns integration testing.

**Currently handled by**: Partially by verify-consistency (INPUT_FROM/OUTPUT_TO bidirectionality), but consistency only checks that references point both ways -- it does NOT check that a full pipeline execution path exists for each tier, or that the agent tool profiles can actually execute the skills they're assigned.

**Budget impact**: ~900 chars estimated for L1 description.

**Verdict**: **CREATE -- MEDIUM priority**. The gap is real and measured (7.1 vs 9.2), but integration audits are done manually via analyst agent spawns currently. The gap is not causing production failures -- it is a quality assurance enhancement. Given the 84% budget, one more skill is feasible but not urgent.

---

#### CAND-02: Pipeline Flow Testing (Dry Run)

**Proposed responsibility**: Simulate a pipeline run without executing it. Trace a hypothetical task through tier classification, phase routing, skill selection, and agent assignment to verify the routing would work.

**Domain**: verify or orchestration

**Distinct methodology?**: PARTIALLY.
- This is conceptually a "flight simulator" for the pipeline
- orchestration-verify already checks agent-task matching, dependency acyclicity, and capacity
- plan-verify-correctness already checks plan-to-architecture mapping
- The gap: nobody checks "given this raw user request, would Lead correctly route it through the full pipeline?"

**Currently handled by**: Partially by orchestration-verify (assignment validation) and plan-verify-correctness (spec compliance). The full end-to-end routing simulation is not covered, but this is essentially what Lead does by nature during actual execution.

**Budget impact**: ~850 chars.

**Verdict**: **NO-CREATE -- LOW priority**. This is testing the orchestrator's behavior, which is inherently a Lead runtime concern. A "dry run" skill would duplicate what Lead already does but without actually executing. The value is marginal because the real test is execution itself. If integration verification (CAND-01) is created, it would subsume most of this need.

---

#### CAND-03: Security Audit

**Proposed responsibility**: Dedicated security scanning of hooks (command injection, path traversal), permissions (deny list completeness), settings (env var exposure), and agent tool profiles (privilege escalation).

**Domain**: verify or research

**Distinct methodology?**: PARTIALLY.
- design-risk Step 3 covers security assessment (OWASP checks)
- plan-verify-robustness Step 4 covers security challenge (data exposure, permission escalation, input injection)
- The SRC risk assessment (`/home/palantir/.claude/agent-memory/analyst/src-risk-assessment.md`) found security issues: /tmp symlink attack, grep scope too broad -- these were found by analyst agent, not by a skill

**Evidence of overlap**:
- `design-risk` methodology Step 3: "Check against relevant OWASP categories: Input validation (command injection, path traversal), Access control (agent tool restrictions, file permissions), Data exposure"
- `plan-verify-robustness` methodology Step 4: "Sensitive data exposure, Permission escalation, Input injection"
- Both skills already cover security -- a dedicated security audit would need to provide DEEPER coverage to justify itself

**Currently handled by**: design-risk (security assessment), plan-verify-robustness (security challenge), and ad-hoc analyst spawns for specific audits. The coverage is adequate for the INFRA scope.

**Budget impact**: ~900 chars.

**Verdict**: **NO-CREATE -- LOW priority**. Security is already covered by two skills at appropriate depth. A dedicated security audit skill would provide diminishing returns for the INFRA domain. If the system expands to application source code, revisit this.

---

#### CAND-04: Budget Monitoring

**Proposed responsibility**: Dedicated L1 budget tracking -- calculate total description chars, track per-skill usage, project headroom, and alert when approaching limits.

**Domain**: homeostasis or verify

**Distinct methodology?**: NO.
- verify-content Step 1 already measures character utilization per file
- manage-skills Step 3 tracks domain coverage and implicitly budget
- self-improve Step 2 includes budget analysis as part of diagnostics
- Budget monitoring is a **metric**, not a responsibility. It's a number that existing skills already compute.

**Currently handled by**: verify-content (measures utilization), self-improve (budget analysis), manage-skills (coverage awareness). All three compute budget as part of their primary responsibility.

**Budget impact**: ~700 chars.

**Verdict**: **NO-CREATE -- LOW priority (premature abstraction)**. Budget is a metric, not a responsibility. Creating a skill just to count characters is "premature abstraction." The existing skills that compute budget incidentally are sufficient. If budget management becomes complex (e.g., priority-based allocation, dynamic pruning), revisit.

---

#### CAND-05: Agent Optimization

**Proposed responsibility**: Dedicated agent tuning -- optimize model selection (opus/haiku), maxTurns, memory policy, tool sets, and descriptions for each agent profile.

**Domain**: homeostasis

**Distinct methodology?**: PARTIALLY.
- self-improve Step 2-3 covers agent configuration as part of INFRA diagnostics
- manage-infra covers agent file health monitoring
- No skill specifically owns "is the analyst's maxTurns optimal? Should delivery-agent use haiku?"

**Evidence of need**: INFRA audit v3 found optimization opportunities (delivery-agent model:haiku, memory:none for delivery-agent/pt-manager) -- these were found by analyst, acted on by self-improve. The workflow worked fine without a dedicated skill.

**Currently handled by**: self-improve (agent config as part of INFRA diagnostics). Works adequately.

**Budget impact**: ~800 chars.

**Verdict**: **NO-CREATE -- LOW priority (premature abstraction)**. Agent tuning happens infrequently (a few times per INFRA version bump) and is adequately handled by self-improve. Creating a separate skill for a quarterly activity is not justified.

---

#### CAND-06: Hook Lifecycle Management

**Proposed responsibility**: Dedicated hook creation, update, testing, and validation. Currently hooks are created/modified by infra-implementer through self-improve or manage-infra.

**Domain**: homeostasis or execution

**Distinct methodology?**: PARTIALLY.
- manage-infra Step 3-4 covers hook validation (scripts reference valid paths)
- verify-structure could check hook script existence
- self-improve Step 2 checks hook validity
- The gap: no skill owns "create a new hook from scratch" as a primary methodology

**Evidence of need**: SRC implementation created 2 new hooks (on-file-change.sh, on-implementer-done.sh). These were created by the execution-infra skill pathway through infra-implementer. The process worked -- the hooks were created correctly.

**Currently handled by**: execution-infra (hook creation via infra-implementer), manage-infra (hook monitoring), self-improve (hook validation). The responsibility is distributed but functional.

**Budget impact**: ~850 chars.

**Verdict**: **NO-CREATE -- LOW priority**. Hook creation/modification is rare (5 hooks total, 2 created in the last major version). The existing pathway (infra-implementer with instructions from Lead) works. A dedicated skill would be invoked perhaps 1-2 times per quarter.

---

#### CAND-07: Context Window Management

**Proposed responsibility**: Skill for managing/optimizing what goes into agent context windows -- monitoring context consumption, recommending prompt size reductions, managing compaction strategy.

**Domain**: homeostasis

**Distinct methodology?**: PARTIALLY.
- The PreCompact hook handles state preservation before compaction
- The SessionStart(compact) hook handles recovery
- self-improve analyzes budget (which is related to context)
- No skill owns "optimize what agents receive in their context"

**Evidence of need**: BUG-002 ("Large-task teammates auto-compact before L1/L2") shows context management is a real concern. However, the mitigation is "keep prompts focused" -- a behavioral guideline, not a skill-automatable process.

**Currently handled by**: Hooks (PreCompact, SessionStart), behavioral guidelines in agent .md files, and manual prompt engineering by Lead.

**Budget impact**: ~800 chars.

**Verdict**: **NO-CREATE -- LOW priority (not skill-automatable)**. Context window management is primarily about runtime prompt engineering, which Lead does by nature. A skill cannot optimize what another agent receives in real-time. The hooks handle the mechanical parts (state preservation). This is a human-judgment concern, not a methodology-able skill.

---

#### CAND-08: Documentation Generation

**Proposed responsibility**: Auto-generating documentation from current INFRA state -- skill inventories, agent profiles, pipeline diagrams, hook documentation.

**Domain**: homeostasis or cross-cutting

**Distinct methodology?**: YES.
- No skill currently generates documentation artifacts
- manage-infra produces a health report (L1/L2) but not persistent docs
- manage-codebase produces codebase-map.md (but dependency data, not docs)

**Evidence of need**: The cc-reference directory (`memory/cc-reference/`) was manually curated. MEMORY.md is manually updated by delivery-pipeline. There is no auto-generation of INFRA documentation.

**Currently handled by**: Manual analyst spawns, self-improve (updates MEMORY.md), delivery-pipeline (archives to MEMORY.md). Documentation is a side effect of other skills, not a primary concern.

**Budget impact**: ~800 chars.

**Verdict**: **NO-CREATE -- LOW priority**. Documentation generation is a convenience, not a gap. MEMORY.md and cc-reference serve as documentation and are maintained by existing skills. Auto-generating docs would produce artifacts that quickly become stale without a maintenance loop -- which would itself need a skill. Premature.

---

### Part 2 Summary

| ID | Candidate | Domain | Distinct? | Gap Real? | Budget | Priority | Verdict |
|----|-----------|--------|-----------|-----------|--------|----------|---------|
| CAND-01 | Integration Verification | verify | YES | YES (7.1 vs 9.2) | ~900 chars | MEDIUM | **CREATE** (conditional) |
| CAND-02 | Pipeline Flow Testing | verify | PARTIAL | MARGINAL | ~850 chars | LOW | NO-CREATE |
| CAND-03 | Security Audit | verify | PARTIAL | NO (covered) | ~900 chars | LOW | NO-CREATE |
| CAND-04 | Budget Monitoring | homeostasis | NO | NO (metric) | ~700 chars | LOW | NO-CREATE |
| CAND-05 | Agent Optimization | homeostasis | PARTIAL | NO (infrequent) | ~800 chars | LOW | NO-CREATE |
| CAND-06 | Hook Lifecycle | homeostasis | PARTIAL | NO (rare) | ~850 chars | LOW | NO-CREATE |
| CAND-07 | Context Window Mgmt | homeostasis | PARTIAL | NO (not automatable) | ~800 chars | LOW | NO-CREATE |
| CAND-08 | Documentation Gen | homeostasis | YES | MARGINAL | ~800 chars | LOW | NO-CREATE |

Only CAND-01 (Integration Verification) has both a distinct methodology AND a measured gap. All others fail at least one of: distinct methodology, genuine unmet need, or frequency of use.

---

## Part 3: SRP Violations in Existing Agents

### Agent Assessment

#### analyst (Profile-B: ReadAnalyzeWrite)

**Tools**: Read, Glob, Grep, Write, sequential-thinking
**Responsibility**: Read-only analysis + structured documentation output

**SRP assessment**: CLEAN. Single responsibility: analyze and document. All tools serve this purpose. The Write tool is for OUTPUT documents (analysis results), not source modification. The constraint "Write output to assigned paths only -- never modify source files" keeps it focused.

**Risk of over-specialization**: NO. This agent is used by 15+ skills across nearly every domain (design, research, plan, plan-verify, orchestration-verify, execution-review, verify-*, manage-*). Very high reuse.

---

#### researcher (Profile-C: ReadAnalyzeWriteWeb)

**Tools**: Read, Glob, Grep, Write, WebSearch, WebFetch, sequential-thinking, context7, tavily
**Responsibility**: Web-enabled research + structured output

**SRP assessment**: CLEAN. Extends analyst with web access. Single responsibility: gather information from external sources. The 4 web tools (WebSearch, WebFetch, context7, tavily) are all variations of the same capability.

**Risk of over-specialization**: MINOR CONCERN. Only used by 3 skills: research-external, pre-design-feasibility, and execution-impact. The web capability is narrowly needed. However, when needed, no other agent can substitute.

---

#### implementer (Profile-D: CodeImpl)

**Tools**: Read, Glob, Grep, Edit, Write, Bash, sequential-thinking
**Responsibility**: Source code modification + testing

**SRP assessment**: CLEAN. Single responsibility: modify application source files and verify changes via shell execution. The Bash tool is essential for testing (not a separate responsibility).

**Potential concern**: The implementer is used by execution-cascade to update `.claude/` INFRA files as well (e.g., updating skill descriptions that reference renamed files). This blurs the line with infra-implementer.

**Evidence**: execution-cascade Step 2 spawns implementers for "affected files" -- some of which may be .claude/ files. The implementer agent body says "Never modify .claude/ directory files (use infra-implementer for that)" but cascade might need to update .claude/ files. This is a boundary ambiguity, not an SRP violation in the agent itself.

---

#### infra-implementer (Profile-E: InfraImpl)

**Tools**: Read, Glob, Grep, Edit, Write, sequential-thinking
**Responsibility**: .claude/ directory file modification (no shell access)

**SRP assessment**: CLEAN. Single responsibility: modify infrastructure configuration files. The lack of Bash is a deliberate safety constraint (cannot accidentally run scripts during config changes).

**Concern about tool overlap**: infra-implementer has exactly the same tools as implementer minus Bash. This raises the question: could one agent serve both purposes? The answer is NO -- the separation enforces a security boundary (.claude/ files vs application code) and prevents accidental shell execution during config changes.

---

#### delivery-agent (Profile-F: ForkDelivery)

**Tools**: Read, Glob, Grep, Edit, Write, Bash, TaskList, TaskGet, TaskUpdate, AskUserQuestion
**Responsibility**: Pipeline delivery -- consolidate, commit, archive

**SRP assessment**: CLEAN but WIDE. This agent does three related things:
1. Consolidate outputs (read/analysis)
2. Git operations (Bash for git commit)
3. Task API updates (mark PT DELIVERED)
4. MEMORY.md updates (archive)

These are all parts of the single "delivery" responsibility. The agent is intentionally fork-context (model: haiku, memory: none) to prevent bloat.

**Risk of over-specialization**: NO. Only used by delivery-pipeline, which is invoked once per pipeline completion. But that's by design -- terminal phase agent.

---

#### pt-manager (Profile-G: ForkPT)

**Tools**: Read, Glob, Grep, Write, TaskList, TaskGet, TaskCreate, TaskUpdate, AskUserQuestion
**Responsibility**: Task lifecycle management

**SRP assessment**: CLEAN. Single responsibility: CRUD operations on tasks via Task API. Notably has TaskCreate (which delivery-agent lacks) and lacks Edit/Bash (which delivery-agent has). The tool sets are complementary, not overlapping.

**Risk of over-specialization**: MINOR CONCERN. Only used by task-management skill. But this is by design -- task operations are a specialized domain requiring full Task API access.

---

### Agent SRP Summary

| Agent | SRP Status | Concern | Verdict |
|-------|-----------|---------|---------|
| analyst | CLEAN | None | No changes |
| researcher | CLEAN | Low reuse (3 skills) | No changes (needed when needed) |
| implementer | CLEAN | Cascade may blur .claude/ boundary | Document boundary |
| infra-implementer | CLEAN | Tool overlap with implementer | Intentional security boundary |
| delivery-agent | CLEAN (wide) | Multiple delivery steps | All steps serve delivery |
| pt-manager | CLEAN | Low reuse (1 skill) | Specialized by design |

**No agent requires splitting or merging.**

**One boundary clarification needed**: execution-cascade should explicitly use infra-implementer (not implementer) when the affected files are in `.claude/`. The current cascade methodology does not distinguish this, which could cause the implementer to violate its own constraint ("Never modify .claude/ directory files").

---

## Part 4: Recommendations

### CREATE Verdicts

| # | Candidate | Verdict | Priority | Budget Impact | Rationale |
|---|-----------|---------|----------|---------------|-----------|
| 1 | verify-integration | **CREATE** (conditional) | MEDIUM | ~900 chars (85% -> 88%) | Measured gap: 7.1 vs 9.2 component health. Distinct methodology: end-to-end pipeline path verification vs individual component checks. BUT: only worth creating if integration audits become recurring (>2x per quarter). Currently done ad-hoc via analyst spawns. |
| 2 | Pipeline Flow Testing | NO-CREATE | LOW | N/A | Subsumed by CAND-01 + what Lead does naturally |
| 3 | Security Audit | NO-CREATE | LOW | N/A | Covered by design-risk + plan-verify-robustness |
| 4 | Budget Monitoring | NO-CREATE | LOW | N/A | Budget is a metric, not a responsibility |
| 5 | Agent Optimization | NO-CREATE | LOW | N/A | Infrequent activity, covered by self-improve |
| 6 | Hook Lifecycle | NO-CREATE | LOW | N/A | Rare activity, existing pathway works |
| 7 | Context Window Mgmt | NO-CREATE | LOW | N/A | Not skill-automatable, runtime concern |
| 8 | Documentation Gen | NO-CREATE | LOW | N/A | Convenience, not a gap |

### SPLIT Verdicts (from Part 1)

| # | Skill | Verdict | Rationale |
|---|-------|---------|-----------|
| 1 | self-improve | NO-SPLIT | Intentional pipeline-in-a-skill for maintenance workflow |
| 2 | task-management | NO-SPLIT | Tightly coupled Task API surface |
| 3 | execution-review | NO-SPLIT | Sub-concerns of single "validate implementation" responsibility |
| 4 | manage-codebase | NO-SPLIT | Multiple modes for single artifact ownership |
| 5 | design-risk | NO-SPLIT | Risk naturally spans dimensions |

### Agent Verdicts (from Part 3)

| # | Agent | Verdict | Action |
|---|-------|---------|--------|
| 1-6 | All 6 agents | NO-CHANGE | No splits, no merges needed |

### Action Items

1. **DOCUMENT**: Add a note to `self-improve/SKILL.md` body acknowledging it is an intentional compressed pipeline (research->diagnose->fix->verify->commit), not a skill to be decomposed.

2. **CLARIFY**: Update `execution-cascade/SKILL.md` Step 2 to explicitly state: "For affected files in `.claude/` scope, spawn `infra-implementer` instead of `implementer`." This resolves the agent boundary ambiguity found in Part 3.

3. **CONDITIONAL CREATE**: If integration audits become recurring (>2x per quarter), create `verify-integration` as verify skill 6 of 6 with methodology:
   - (1) Extract full pipeline paths per tier (TRIVIAL/STANDARD/COMPLEX)
   - (2) Trace each path: skill A OUTPUT_TO -> skill B INPUT_FROM
   - (3) Verify agent tool profiles match skill requirements
   - (4) Test hook trigger conditions against actual matchers
   - (5) Report dead ends, capability mismatches, unresolvable paths

4. **MONITOR**: Track L1 budget at each skill modification. Current headroom (~5,120 chars) allows 5-6 new skills maximum. Any new skill creation should be weighed against this finite budget.

---

## Appendix: Full Skill Inventory with SRP Grades

| # | Skill | Domain | SRP Grade | Notes |
|---|-------|--------|-----------|-------|
| 1 | pre-design-brainstorm | pre-design | A | Clean |
| 2 | pre-design-validate | pre-design | A | Clean |
| 3 | pre-design-feasibility | pre-design | A | Clean |
| 4 | design-architecture | design | A | Clean |
| 5 | design-interface | design | A | Clean |
| 6 | design-risk | design | B+ | 3 dimensions, unified FMEA |
| 7 | research-codebase | research | A | Clean |
| 8 | research-external | research | A | Clean |
| 9 | research-audit | research | A | Clean |
| 10 | plan-decomposition | plan | A | Clean |
| 11 | plan-interface | plan | A | Clean |
| 12 | plan-strategy | plan | A | Clean |
| 13 | plan-verify-correctness | plan-verify | A | Clean |
| 14 | plan-verify-completeness | plan-verify | A | Clean |
| 15 | plan-verify-robustness | plan-verify | A | Clean |
| 16 | orchestration-decompose | orchestration | A | Clean |
| 17 | orchestration-assign | orchestration | A | Clean |
| 18 | orchestration-verify | orchestration | A | Clean |
| 19 | execution-code | execution | A | Clean |
| 20 | execution-infra | execution | A | Clean |
| 21 | execution-impact | execution | A | Clean |
| 22 | execution-cascade | execution | A | Clean (boundary note) |
| 23 | execution-review | execution | B+ | 2-stage, same responsibility |
| 24 | verify-structure | verify | A | Clean |
| 25 | verify-content | verify | A | Clean |
| 26 | verify-consistency | verify | A | Clean |
| 27 | verify-quality | verify | A | Clean |
| 28 | verify-cc-feasibility | verify | A | Clean |
| 29 | manage-infra | homeostasis | A | Clean |
| 30 | manage-skills | homeostasis | A | Clean |
| 31 | manage-codebase | homeostasis | B+ | 3 modes, single artifact |
| 32 | self-improve | homeostasis | C+ | Mini-pipeline, intentional |
| 33 | delivery-pipeline | cross-cutting | A | Clean |
| 34 | pipeline-resume | cross-cutting | A | Clean |
| 35 | task-management | cross-cutting | B | 6 operations, 2 clusters |

**Grade distribution**: A: 28 (80%), B+: 4 (11%), B: 1 (3%), C+: 1 (3%), C or below: 0
**Overall SRP health**: STRONG. 91% of skills have clean A/B+ grades.
