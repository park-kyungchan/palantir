# Context Engineering RSI — Diagnosis Report

> **Date**: 2026-02-15
> **Analyst**: analyst agent (CE RSI Diagnosis Phase)
> **Scope**: All 33 skills + 6 agents + CLAUDE.md + conventions.md
> **Protocol Under Audit**: CLAUDE.md §2.1 Execution Mode by Phase

## Executive Summary

**Health Score: 3/10** — Protocol exists but has ZERO implementation across INFRA.

The Context Engineering (CE) protocol established in CLAUDE.md §2.1 and conventions.md defines three critical rules for P2+ phases:
1. Task tool MUST include `team_name` parameter (teammate session)
2. Lead NEVER reads TaskOutput directly — results via SendMessage only
3. Teammate outputs stay in teammate context, summaries come to Lead

**Finding**: These rules are stated but have zero enforcement or implementation in any skill DPS template, agent definition, or operational convention. Every P2+ agent interaction would violate the protocol as currently documented.

## Severity Distribution

| Severity | Count | Category |
|----------|-------|----------|
| CRITICAL | 6     | Systemic gaps: agent defs, DPS templates, format spec |
| HIGH     | 5     | Explicit TaskOutput reading, missing team_name guidance |
| MEDIUM   | 8     | Homeostasis ambiguity, implicit violations, precedent |
| LOW      | 3     | Documentation completeness, template standardization |
| **TOTAL** | **22** | |

## Category 1: DPS Templates Missing SendMessage Protocol

**Severity: CRITICAL** — Systemic gap across all P2+ skills

Every P2+ skill that spawns agents has a DPS (Context/Task/Constraints/Expected Output) template that tells the agent WHAT output format to produce, but NONE include instructions for HOW the agent should deliver results back to Lead via SendMessage.

### Phase Classification

| Phase | Skills | Agent Spawn? | CE Mode | CE Violation? |
|-------|--------|-------------|---------|---------------|
| P0 | brainstorm, validate, feasibility | Yes (run_in_background) | Local | EXEMPT |
| P1 | architecture, interface, risk | Yes (run_in_background) | Local | EXEMPT |
| P2 | codebase, external, audit | Yes (Team) | Team | **YES** |
| P3 | decomposition, interface, strategy | Yes (Team) | Team | **YES** |
| P4 | plan-verify | Yes (Team) | Team | **YES** |
| P5 | decompose, assign, verify | No (Lead-direct) | Team | EXEMPT (no spawn) |
| P6 | code, infra, impact, cascade, review | Yes (Team) | Team | **YES** |
| P7 | structural-content, consistency, quality, cc-feasibility | Yes (Team) | Team | **YES** |
| P8 | delivery-pipeline | Yes (delivery-agent fork) | Team | **YES** |
| Homeostasis | self-diagnose, self-implement, manage-infra, manage-skills, manage-codebase | Yes | Phase-dependent | **CONDITIONAL** |
| Cross-cutting | task-management | Yes (pt-manager fork) | Phase-dependent | **CONDITIONAL** |
| Cross-cutting | pipeline-resume | Lead-direct + optional analysts | Phase-dependent | **CONDITIONAL** |

### Affected Skills (22 total)

#### CE-DPS-01 through CE-DPS-17: P2-P8 Skills (17 skills) — CRITICAL

All 17 P2+ phase skills with agent spawning lack SendMessage in their DPS Expected Output section:

| ID | Skill | Phase | Agent Type | DPS Expected Output (current) |
|----|-------|-------|------------|-------------------------------|
| CE-DPS-01 | research-codebase | P2 | researcher | "L1 YAML pattern inventory, L2 markdown findings" |
| CE-DPS-02 | research-external | P2 | researcher | "L1 YAML dependency validation matrix, L2 markdown doc summary" |
| CE-DPS-03 | research-audit | P2 | analyst | "L1 YAML consolidated inventory, L2 markdown gap analysis" |
| CE-DPS-04 | plan-decomposition | P3 | analyst | "L1 YAML task list with assignments+deps, L2 task descriptions" |
| CE-DPS-05 | plan-interface | P3 | analyst | "L1 YAML interface registry per task, L2 dependency ordering" |
| CE-DPS-06 | plan-strategy | P3 | analyst | "L1 YAML execution sequence with parallel groups, L2 strategy" |
| CE-DPS-07 | plan-verify | P4 | analyst | "L1 YAML per-dimension PASS/FAIL + overall, L2 per-dimension analysis" |
| CE-DPS-08 | execution-code | P6 | implementer | "L1 YAML manifest, L2 summary" |
| CE-DPS-09 | execution-infra | P6 | infra-implementer | "L1 YAML infra change manifest, L2 markdown change summary" |
| CE-DPS-10 | execution-impact | P6 | analyst | "L1 YAML impact report with impacts array, L2 markdown analysis" |
| CE-DPS-11 | execution-cascade | P6 | implementer | "L1 YAML cascade result with iteration_details, L2 markdown update log" |
| CE-DPS-12 | execution-review | P6 | analyst | "L1 YAML review verdict per reviewer, L2 markdown consolidated review report" |
| CE-DPS-13 | verify-structural-content | P7 | analyst | "L1 YAML PASS/FAIL per file, L2 combined integrity report" |
| CE-DPS-14 | verify-consistency | P7 | analyst | "L1 YAML relationship matrix, L2 markdown inconsistency report" |
| CE-DPS-15 | verify-quality | P7 | analyst | "L1 YAML quality score per file, L2 markdown quality report" |
| CE-DPS-16 | verify-cc-feasibility | P7 | analyst/guide | "L1 YAML native compliance per file, L2 markdown feasibility report" |
| CE-DPS-17 | delivery-pipeline | P8 | delivery-agent | "L1 YAML with commit_hash, files_changed, pt_status" |

**What's missing**: Every DPS Expected Output should end with: "Send L1 summary to Lead via SendMessage(type:message, recipient:{lead-name}) upon completion."

#### CE-DPS-18 through CE-DPS-23: Homeostasis + Cross-cutting Skills (6 skills) — MEDIUM

These skills can be invoked at any phase. When invoked during P2+, they must use Team infra and SendMessage. Current DPS templates make no distinction between P0-P1 (local) and P2+ (Team) execution modes.

| ID | Skill | Agent Type | Issue |
|----|-------|------------|-------|
| CE-DPS-18 | self-diagnose | analyst | No phase-aware execution mode |
| CE-DPS-19 | self-implement | infra-implementer | No phase-aware execution mode |
| CE-DPS-20 | manage-infra | analyst | No phase-aware execution mode |
| CE-DPS-21 | manage-skills | analyst + infra-impl | No phase-aware execution mode |
| CE-DPS-22 | manage-codebase | analyst | No phase-aware execution mode |
| CE-DPS-23 | task-management | pt-manager | No phase-aware execution mode |

**Note**: pipeline-resume is Lead-direct with optional analyst spawns, handled similarly.

---

## Category 2: Agent Definitions Missing Result Reporting

**Severity: CRITICAL** — All 6 agents lack SendMessage completion protocol

Agent definition files (`.claude/agents/*.md`) define the agent's role, tools, and behavioral guidelines. These files are loaded into the agent's context at spawn time. NONE of the 6 agents include instructions for sending structured results back to Lead via SendMessage upon task completion.

| ID | Agent | File | Tools Listed | SendMessage Mentioned? | Result Reporting Protocol? |
|----|-------|------|-------------|----------------------|--------------------------|
| CE-AGT-01 | analyst | agents/analyst.md | Read, Glob, Grep, Write, sequential-thinking, Edit | **NO** | **NONE** |
| CE-AGT-02 | researcher | agents/researcher.md | Read, Glob, Grep, Write, WebSearch, WebFetch, sequential-thinking, context7, tavily, Edit | **NO** | **NONE** |
| CE-AGT-03 | implementer | agents/implementer.md | Read, Glob, Grep, Edit, Write, Bash, sequential-thinking | **NO** | **NONE** |
| CE-AGT-04 | infra-implementer | agents/infra-implementer.md | Read, Glob, Grep, Edit, Write, sequential-thinking | **NO** | **NONE** |
| CE-AGT-05 | delivery-agent | agents/delivery-agent.md | Read, Glob, Grep, Edit, Write, Bash, TaskUpdate, TaskGet, TaskList, AskUserQuestion | **NO** | **NONE** |
| CE-AGT-06 | pt-manager | agents/pt-manager.md | Read, Glob, Grep, Write, TaskCreate, TaskUpdate, TaskGet, TaskList, AskUserQuestion | **NO** | **NONE** |

**Critical Insight**: The SendMessage tool is available to ALL teammate agents automatically (it's a Team infrastructure tool, not an agent-defined tool). But since no agent definition mentions it and no skill DPS template instructs its use, agents never know they should use it.

**Recommended Fix**: Add a "Completion Protocol" section to each agent definition:
```markdown
## Completion Protocol
When working as a teammate (team_name provided):
- Upon task completion, send L1 summary to Lead via SendMessage
- Include: status, key metrics, files changed, output file path (if applicable)
- Keep summary concise (L1 only). L2 detail stays in your context.
- If task fails: send failure summary with reason and blocker details.
```

---

## Category 3: Skills Explicitly Referencing TaskOutput/Lead-Reads-Output

**Severity: HIGH** — Direct protocol contradictions in P2+ skills

Several P2+ skills explicitly instruct Lead to read agent output directly, contradicting the SendMessage-only rule in §2.1.

| ID | Skill | Phase | File:Line | Violating Text | Severity |
|----|-------|-------|-----------|----------------|----------|
| CE-TO-01 | execution-code | P6 | SKILL.md:~89 | "Read implementer L1 output for completion status" | HIGH |
| CE-TO-02 | execution-infra | P6 | SKILL.md:~103 | "Read infra-implementer L1 output for completion status" | HIGH |
| CE-TO-03 | execution-code | P6 | SKILL.md:~33 | "Lead already has...from a previous implementer's output" | HIGH |
| CE-TO-04 | self-implement | Homeostasis | SKILL.md:~59 | "Monitor completion. If a wave fails, re-spawn" | MEDIUM |
| CE-TO-05 | design-architecture | P1 | SKILL.md:43 | "Communication is one-way: Lead reads agent output, no back-and-forth messaging" | MEDIUM (P1=EXEMPT but sets wrong precedent for CE protocol) |

**Note on CE-TO-05**: design-architecture is P1 (EXEMPT from CE rules since P0-P1 use local agents). However, the explicit statement "no back-and-forth messaging" contradicts the P2+ paradigm where messaging IS the communication channel. If this pattern is copied to P2+ skills, it would be a direct violation.

### Implicit Violations (MEDIUM)

Several skills describe monitoring or reading agent results without specifying the mechanism, implicitly assuming TaskOutput:

| ID | Skill | Phase | Issue |
|----|-------|-------|-------|
| CE-TO-06 | execution-cascade | P6 | Methodology step says "After updates: re-run grep check" — implies Lead can see agent's grep results |
| CE-TO-07 | execution-review | P6 | Two-stage review methodology implies Lead reads Stage 1 analyst output before spawning Stage 2 |
| CE-TO-08 | verify-cc-feasibility | P7 | "Lead escalates to claude-code-guide only if analyst flags ambiguous fields" — implies Lead reads analyst flags |

---

## Category 4: conventions.md Completeness

**Severity: HIGH** — Rules stated but implementation structure undefined

`/home/palantir/.claude/rules/conventions.md` (lines 32-35) states the Context Isolation rules:
```
## Context Isolation
- P2+ phases: Task tool MUST include `team_name` parameter (teammate session)
- Lead NEVER reads TaskOutput directly — results via SendMessage only
- Teammate outputs stay in teammate context, summaries come to Lead
```

### Missing Elements

| ID | Missing Element | Severity | Impact |
|----|----------------|----------|--------|
| CE-CONV-01 | **SendMessage Summary Format Spec** | HIGH | Without a standard format, each agent sends ad-hoc summaries. Lead cannot reliably parse results. |
| CE-CONV-02 | **Required Fields in Completion Message** | HIGH | Should specify: status, key_metrics, files_changed, output_file_path, routing_recommendation |
| CE-CONV-03 | **L1 vs L2 Delivery Split** | MEDIUM | Should clarify: L1 summary → SendMessage to Lead. L2 detail → stays in agent context or written to file. |
| CE-CONV-04 | **Failure Reporting via SendMessage** | MEDIUM | Should specify: how agents report failures, blockers, and partial results via SendMessage |
| CE-CONV-05 | **team_name Injection Pattern** | LOW | Should specify: Lead includes team_name in Task tool spawn for P2+ phases. Currently implied but not documented as a convention. |

### Proposed Addition to conventions.md

```markdown
## SendMessage Completion Protocol (P2+ phases)
- Teammate sends L1 summary to Lead via SendMessage upon completion
- Required fields: status (PASS/FAIL/partial), key metrics, files changed count
- Optional fields: output file path, routing recommendation, blockers
- L2 detail stays in teammate context (Lead does NOT request full output)
- On failure: include failure reason, affected files, suggested route
- Format: plain text summary, not raw YAML (Lead can parse narrative)
```

---

## Category 5: CLAUDE.md Protocol Completeness

**Severity: MEDIUM** — Rule exists but lacks actionable implementation guidance

`/home/palantir/.claude/CLAUDE.md` §2.1 (lines 38-40):
```
- P0-P1 (PRE-DESIGN + DESIGN): Lead with local agents (run_in_background).
  No Team infrastructure (no TeamCreate/SendMessage).
- P2+ (RESEARCH through DELIVERY): Team infrastructure ONLY.
  TeamCreate, TaskCreate/Update, SendMessage.
  Local agents (team_name omitted) PROHIBITED.
  Lead MUST NOT use TaskOutput to read full agent results — use SendMessage for result exchange.
```

### Missing Elements

| ID | Missing Element | Severity | Impact |
|----|----------------|----------|--------|
| CE-CMD-01 | **SendMessage result format spec** | MEDIUM | §2.1 says "use SendMessage" but doesn't define the message structure agents should use |
| CE-CMD-02 | **team_name parameter requirement** | LOW | §2.1 says "Local agents (team_name omitted) PROHIBITED" but skill DPS templates don't include team_name |
| CE-CMD-03 | **Lead result routing from SendMessage** | LOW | §2.1 doesn't explain how Lead uses received SendMessage summaries for pipeline routing decisions |

**Note**: CLAUDE.md is intentionally protocol-only (54L). Detailed implementation guidance belongs in conventions.md and skill DPS templates. The §2.1 rule is correctly stated at the right level of abstraction. The implementation gap is in downstream enforcement (skills + agents), not in CLAUDE.md itself.

---

## Cross-Category Analysis

### Root Cause

The CE protocol (§2.1) was added to CLAUDE.md and conventions.md as a rule, but the rule was never propagated to the INFRA components that must implement it:

```
CLAUDE.md §2.1 (rule exists) ──→ conventions.md (rule restated) ──→ ???
                                                                      │
                                                                      ├─ Agent definitions: NO implementation
                                                                      ├─ Skill DPS templates: NO implementation
                                                                      └─ SendMessage format: NOT defined
```

The gap is between **rule declaration** and **rule implementation**. This is a classic CE anti-pattern: the protocol is in the right document but never reaches the execution layer.

### Impact Matrix

| Component | Rule Awareness | Implementation | Gap |
|-----------|---------------|----------------|-----|
| CLAUDE.md | 100% (rule stated) | N/A (protocol layer) | None |
| conventions.md | 100% (rule restated) | 20% (rules stated but format undefined) | Format spec |
| Agent definitions (6) | 0% (no mention) | 0% (no completion protocol) | Full |
| Skill DPS templates (22) | 0% (no mention) | 0% (no SendMessage instruction) | Full |
| P0-P1 skills (6) | N/A (exempt) | N/A (correctly use run_in_background) | None |
| P5 skills (3) | N/A (Lead-direct) | N/A (no agent spawn) | None |

### Systemic Nature

This is NOT a per-skill fix. It's a systemic gap requiring:
1. **Agent-level fix**: Add completion protocol to all 6 agent definitions (one-time, affects all spawns)
2. **Skill-level fix**: Add SendMessage instruction to all 22 P2+ skill DPS templates
3. **Convention-level fix**: Define SendMessage summary format in conventions.md
4. **Cross-cutting resolution**: Define phase-aware execution mode for homeostasis skills

---

## Findings Summary Table

| ID | Category | Severity | Component | Issue | Fix Scope |
|----|----------|----------|-----------|-------|-----------|
| CE-DPS-01..17 | Cat 1 | CRITICAL | 17 P2-P8 skills | DPS Expected Output lacks SendMessage instruction | Each skill's DPS template |
| CE-DPS-18..23 | Cat 1 | MEDIUM | 6 homeostasis/x-cut skills | No phase-aware execution mode distinction | Each skill's Execution Model |
| CE-AGT-01..06 | Cat 2 | CRITICAL | All 6 agent definitions | No completion/result reporting protocol | Each agent .md file |
| CE-TO-01..03 | Cat 3 | HIGH | execution-code, execution-infra | Explicitly says "Read L1 output" | Remove/replace wording |
| CE-TO-04 | Cat 3 | MEDIUM | self-implement | "Monitor completion" implies TaskOutput | Clarify mechanism |
| CE-TO-05 | Cat 3 | MEDIUM | design-architecture | "One-way: Lead reads output" (P1=exempt but sets precedent) | Add phase caveat |
| CE-TO-06..08 | Cat 3 | MEDIUM | cascade, review, cc-feasibility | Implicit TaskOutput assumption in methodology | Clarify mechanism |
| CE-CONV-01..02 | Cat 4 | HIGH | conventions.md | Missing SendMessage format spec and required fields | Add new section |
| CE-CONV-03..04 | Cat 4 | MEDIUM | conventions.md | Missing L1/L2 split and failure reporting | Add to new section |
| CE-CONV-05 | Cat 4 | LOW | conventions.md | Missing team_name injection convention | Add to existing section |
| CE-CMD-01 | Cat 5 | MEDIUM | CLAUDE.md §2.1 | Missing SendMessage result format | Consider adding to §2.1 |
| CE-CMD-02..03 | Cat 5 | LOW | CLAUDE.md §2.1 | Missing team_name and routing guidance | Low priority, downstream fixes suffice |

---

## Implementation Recommendations

### Priority Order

1. **P1 — Agent Definitions (CRITICAL)**: Add completion protocol to all 6 agent definitions. This is the highest-leverage fix — every agent spawn across all skills will inherit the protocol. Single change point, maximum coverage.

2. **P2 — conventions.md Format Spec (HIGH)**: Define the SendMessage summary format and required fields. This creates the standard that agents and skills reference.

3. **P3 — Skill DPS Templates (CRITICAL but numerous)**: Update all 22 P2+ skill DPS Expected Output sections to include SendMessage instruction. Can be batched in waves by phase.

4. **P4 — TaskOutput Reference Cleanup (HIGH)**: Remove or rephrase "Read L1 output" instructions in execution-code, execution-infra, and other affected skills.

5. **P5 — Homeostasis Phase-Awareness (MEDIUM)**: Add phase-conditional execution mode to homeostasis skills (if P0-P1: local agent, if P2+: Team infra with SendMessage).

### Estimated Scope

| Fix | Files Changed | Complexity |
|-----|--------------|------------|
| Agent definitions | 6 files | Low (add section to each) |
| conventions.md | 1 file | Low (add new section) |
| Skill DPS templates | 22 files | Medium (batch update per phase) |
| TaskOutput cleanup | 3-5 files | Low (wording changes) |
| Homeostasis phase-awareness | 6 files | Medium (conditional logic) |
| **Total** | **~37 files** | Medium overall |

### Key Design Decision Needed

**Who adds SendMessage to agent context — the agent definition or the skill DPS?**

| Approach | Pros | Cons |
|----------|------|------|
| **Agent definition only** | Single point of change. Every spawn inherits. | Less specific (agent doesn't know WHAT to include in summary). |
| **Skill DPS only** | Specific per-skill output format. | Must update 22 DPS templates. Agents still don't know the generic protocol. |
| **Both (recommended)** | Agent definition sets the generic protocol ("always SendMessage on completion"). Skill DPS specifies the output format ("include these specific fields"). | Slightly redundant but most robust. |

---

## Convergence Forecast

| Iteration | Scope | Expected Findings After |
|-----------|-------|------------------------|
| Current (diagnosis) | Full INFRA scan | 22 findings |
| Iter 1 | Agent defs + conventions.md + top-5 explicit violations | ~12 remaining |
| Iter 2 | Skill DPS batch update (P2-P4, P6-P8) | ~4 remaining |
| Iter 3 | Homeostasis phase-awareness + residual cleanup | 0 remaining |

**Estimated convergence**: 3 iterations, ~37 files changed.

---

## Appendix: Files Scanned

### Skills (33)
- P0: pre-design-brainstorm, pre-design-validate, pre-design-feasibility
- P1: design-architecture, design-interface, design-risk
- P2: research-codebase, research-external, research-audit
- P3: plan-decomposition, plan-interface, plan-strategy
- P4: plan-verify
- P5: orchestration-decompose, orchestration-assign, orchestration-verify
- P6: execution-code, execution-infra, execution-impact, execution-cascade, execution-review
- P7: verify-structural-content, verify-consistency, verify-quality, verify-cc-feasibility
- P8: delivery-pipeline
- Homeostasis: self-diagnose, self-implement, manage-infra, manage-skills, manage-codebase
- Cross-cutting: task-management, pipeline-resume

### Agents (6)
- analyst.md, researcher.md, implementer.md, infra-implementer.md, delivery-agent.md, pt-manager.md

### Protocol Files (2)
- CLAUDE.md (§2.1 Execution Mode by Phase)
- conventions.md (Context Isolation section)
