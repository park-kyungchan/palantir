---
design_id: SKL-001-BRAINSTORMING-PIPELINE
version: "1.0"
date: "2026-02-07"
author: "Lead (Opus 4.6)"
status: DRAFT
parent: "Agent Teams Infrastructure v3.0 (DIA + LDAP)"
scope: "New custom skill — Phase 1-3 PRE-EXEC Orchestrator"
format: "Markdown + YAML frontmatter (Machine-Readable for Opus 4.6)"
output_format_standard: "YAML (structured) + Markdown (narrative) — applies to ALL skill redesigns"
related:
  - "docs/plans/2026-02-07-superpowers-agent-teams-compatibility-analysis.md (G-07)"
  - "docs/plans/2026-02-07-ch001-ldap-design.yaml (DIA v3.0)"
  - ".claude/CLAUDE.md (Team Constitution v3.0)"
---

# brainstorming-pipeline — Skill Design Document

## 1. Problem Statement

### Current State

The existing `brainstorming` skill (superpowers v4.2.0) is designed for **single-agent** Claude Code
sessions. It operates as Lead ↔ User dialogue producing a design document, then chains to
`using-git-worktrees` → `writing-plans` → `executing-plans` for implementation.

**Compatibility Analysis (G-07):** brainstorming OVERLAPS with Agent Teams Phases 1-3. The
post-brainstorming chain (worktree → writing-plans → executing-plans) is INCOMPATIBLE with
Agent Teams' persistent pipeline, DIA enforcement, and Task API.

### Solution: Split Strategy

| Skill | Mode | Status |
|-------|------|--------|
| `brainstorming` (superpowers) | Solo mode — unchanged | PRESERVE |
| `brainstorming-pipeline` (custom) | Agent Teams Phase 1-3 orchestrator | NEW |

The split preserves solo-mode functionality while providing an Agent Teams-native alternative
that integrates with DIA v3.0 (CIP + DIAVP + LDAP).

### Design Principles

1. **Phase 1-3 Only** — Discovery + Deep Research + Architecture. Clean termination after Phase 3.
2. **Phase 4+ Delegated** — Detailed Design → `writing-plans` (separate skill). Validation → separate skill. EXEC → separate skills. One skill per optimization, sequential.
3. **Full Script Phase 1** — More advanced than current brainstorming. Structured Recon + Freeform Q&A with Category Awareness + Structured Trade-off Matrix + Scope Crystallization.
4. **DIA Delegation** — Skill specifies Phase/Tier/Intensity. Actual protocol execution delegated to CLAUDE.md [PERMANENT] §7.
5. **global-context.md Native** — Phase 1 output = GC v1. No separate "design brief" file.
6. **Sequential Thinking Mandatory** — ALL agents (Lead + Teammates) use `mcp__sequential-thinking__sequentialthinking` for every analysis, judgment, design, and verification task.
7. **Output Format** — YAML (structured: L1, gate-record) + Markdown (narrative: L2, GC, orchestration-plan). NOT XML. Token efficiency > tag verbosity.

---

## 2. Architecture Overview

```
brainstorming-pipeline (Lead executes this skill)
│
├── Phase 1: Discovery ─────────────────── Lead Only, LDAP: NONE
│   ├── 1.1 Structured Recon (3-Layer)
│   ├── 1.2 Freeform Q&A (Category Awareness)
│   ├── 1.3 Approach Exploration (Trade-off Matrix)
│   ├── 1.4 Scope Crystallization
│   └── 1.5 Gate 1 → global-context.md v1
│
├── Phase 2: Deep Research ─────────────── researcher(1-3), LDAP: MEDIUM(1Q)
│   ├── 2.1 Research Scope Determination
│   ├── 2.2 TeamCreate + orchestration-plan
│   ├── 2.3 Researcher Spawn + DIA (TIER 3 + LDAP 1Q)
│   ├── 2.4 Research Execution + L1/L2 Handoff
│   └── 2.5 Gate 2 → global-context.md v2
│
├── Phase 3: Architecture ──────────────── architect(1), LDAP: MAXIMUM(3Q+alt)
│   ├── 3.1 Architect Spawn + CIP (GC v2 + research L2)
│   ├── 3.2 DIA (TIER 2 + LDAP 3Q + ALTERNATIVE_DEMAND)
│   ├── 3.3 Architecture Design + L1/L2/L3 Handoff
│   └── 3.4 Gate 3 → global-context.md v3
│
└── Clean Termination
    ├── Output summary to user
    ├── Teammate shutdown (all)
    └── TeamDelete
```

### DIA Responsibility Matrix

| Phase | Agent | DIA Tier | LDAP Intensity | Protocol Source |
|-------|-------|----------|----------------|----------------|
| 1 | Lead only | N/A | NONE | N/A |
| 2 | researcher | TIER 3 (3 IAS, 5 RC) | MEDIUM (1Q) | CLAUDE.md [PERMANENT] §7 |
| 3 | architect | TIER 2 (4 IAS, 7 RC) | MAXIMUM (3Q + alt) | CLAUDE.md [PERMANENT] §7 |

### Output Directory Structure

```
.agent/teams/{session-id}/
├── orchestration-plan.md          # Lead maintains
├── global-context.md              # GC-v1 (P1) → v2 (P2) → v3 (P3)
├── phase-1/
│   └── gate-record.yaml           # Gate 1 evaluation
├── phase-2/
│   ├── gate-record.yaml           # Gate 2 evaluation
│   └── researcher-1/
│       ├── L1-index.yaml
│       ├── L2-summary.md
│       ├── L3-full/
│       └── task-context.md
├── phase-3/
│   ├── gate-record.yaml           # Gate 3 evaluation
│   └── architect-1/
│       ├── L1-index.yaml
│       ├── L2-summary.md
│       ├── L3-full/
│       │   └── architecture-design.md
│       └── task-context.md
```

---

## 3. Phase 1 — Discovery (Full Script)

**Executor:** Lead only | **LDAP:** NONE | **Duration:** Variable (user-driven)

### 3.1 Structured Recon (3-Layer)

Before any user interaction, Lead performs systematic context gathering:

**Layer A — Codebase Recon:**
- Project structure scan (Glob top-level directories)
- Recent change history (git log --oneline -20)
- Configuration state (.claude/, settings, agent files)
- Active branches and PR status

**Layer B — Domain Recon:**
- Existing design documents (docs/plans/*.md, *.yaml)
- MEMORY.md for related prior work and lessons learned
- Infrastructure version (CLAUDE.md version, DIA tier)

**Layer C — Constraint Recon:**
- Dependency/conflict potential with existing systems
- User-provided arguments parsing (skill invocation args)
- Available teammate types and current team state

Lead uses `sequential-thinking` to synthesize Recon findings into an internal mental model.
No separate file is created — findings inform the Q&A phase.

**[MANDATORY] sequential-thinking usage:**
Lead MUST use `mcp__sequential-thinking__sequentialthinking` to analyze Recon results
before proceeding to Q&A. This ensures structured reasoning about project state.

### 3.2 Freeform Q&A with Category Awareness

**Core Principle:** Question count is NOT fixed. Q&A continues until user approves
Scope Crystallization (3.4). Lead follows the natural conversation flow.

**Category Awareness (guide, NOT constraint):**

Lead internally tracks which categories have been explored during Q&A:

| Category | Description | Explored? |
|----------|-------------|-----------|
| PURPOSE | What are we building and why? | |
| SCOPE | Where are the boundaries? | |
| CONSTRAINTS | What are the invariants/limitations? | |
| APPROACH | Which method/strategy? (triggers 3.3) | |
| RISK | What can go wrong? | |
| INTEGRATION | How does it connect to existing systems? | |

- Categories may be covered in any order, driven by user conversation
- Not all categories must be explicitly asked — natural coverage counts
- Lead tracks internally and may gently steer toward uncovered categories
- One question per message — multiple choice preferred via `AskUserQuestion`

**[MANDATORY] sequential-thinking usage:**
Lead MUST use `mcp__sequential-thinking__sequentialthinking` after each user response
to analyze the answer, update category coverage, and determine the next question.

**Transition to 3.3:** When APPROACH category naturally arises, Lead presents
the Structured Trade-off Matrix before returning to remaining Q&A if needed.

### 3.3 Approach Exploration (Structured Trade-off Matrix)

When the conversation reaches approach/strategy decisions, Lead presents
a structured comparison:

```markdown
| Criterion         | Option A: {name}  | Option B: {name}  | Option C: {name} |
|-------------------|--------------------|--------------------|--------------------|
| Complexity        | LOW / MED / HIGH   |                    |                    |
| Risk              | LOW / MED / HIGH   |                    |                    |
| Phase 2 Research  | {scope description}|                    |                    |
| Phase 3 Arch      | {expected effort}  |                    |                    |
| File Count (est)  | ~N files           |                    |                    |
| Recommendation    | * (recommended)    |                    |                    |
```

- Always 2-3 options. Lead recommends one with explicit reasoning.
- User selects via `AskUserQuestion`.
- After selection, Q&A may continue for remaining uncovered categories.

**[MANDATORY] sequential-thinking usage:**
Lead MUST use `mcp__sequential-thinking__sequentialthinking` to analyze trade-offs
and formulate the recommendation before presenting to user.

### 3.4 Scope Crystallization

When Lead judges sufficient understanding has been reached, propose a Scope Statement
to the user for approval:

```markdown
## Scope Statement

**Goal:** {one sentence}
**In Scope:**
- {item 1}
- {item 2}

**Out of Scope:**
- {item 1}
- {item 2}

**Approach:** {selected option summary}
**Success Criteria:**
- {measurable outcome 1}
- {measurable outcome 2}

**Estimated Complexity:** SIMPLE / MEDIUM / COMPLEX
**Phase 2 Research Needs:**
- {research topic 1}
- {research topic 2}

**Phase 3 Architecture Needs:**
- {architectural decision 1}
- {architectural decision 2}
```

- If user rejects → return to Q&A (3.2). No iteration limit on Phase 1 Q&A.
- If user approves → proceed to Gate 1 (3.5).

**[MANDATORY] sequential-thinking usage:**
Lead MUST use `mcp__sequential-thinking__sequentialthinking` to synthesize all Q&A
responses into the Scope Statement before presenting to user.

### 3.5 Gate 1 → global-context.md v1

**Gate 1 Criteria:**

| # | Criterion | Check |
|---|-----------|-------|
| G1-1 | Scope Statement approved by user | YES/NO |
| G1-2 | Complexity classification confirmed | YES/NO |
| G1-3 | Phase 2 research scope defined | YES/NO |
| G1-4 | Phase 3 entry conditions clear | YES/NO |
| G1-5 | No unresolved critical ambiguities | YES/NO |

**On APPROVE:**
1. Create `.agent/teams/{session-id}/global-context.md` (GC-v1)
2. Create `.agent/teams/{session-id}/orchestration-plan.md`
3. Create `.agent/teams/{session-id}/phase-1/gate-record.yaml`
4. Proceed to Phase 2

**global-context.md v1 Template:**

```markdown
---
version: GC-v1
created: {YYYY-MM-DD}
feature: {feature-name}
complexity: {SIMPLE|MEDIUM|COMPLEX}
---

# Global Context — {Feature Name}

## Scope
{Scope Statement from 3.4 — full content}

## Phase Pipeline Status
- Phase 1: COMPLETE (Gate 1 APPROVED)
- Phase 2: PENDING
- Phase 3: PENDING

## Constraints
{Extracted from Q&A}

## Decisions Log
| # | Decision | Rationale | Phase |
|---|----------|-----------|-------|
| D-1 | {approach choice} | {reason} | P1 |
```

---

## 4. Phase 2 — Deep Research

**Executor:** researcher(1-3) | **DIA:** TIER 3 + LDAP MEDIUM(1Q) | **Protocol:** CLAUDE.md [PERMANENT] §7

### 4.1 Research Scope Determination (Lead Only)

Lead reads GC-v1 "Phase 2 Research Needs" section and determines:

| Research Domains | Researcher Count | Strategy |
|------------------|------------------|----------|
| 1 domain | 1 researcher | Single assignment |
| 2-3 independent domains | 2-3 researchers | Parallel spawn |
| Domains with dependencies | 1 researcher (sequential) | Or sequential spawn |

**[MANDATORY] sequential-thinking usage:**
Lead MUST use `mcp__sequential-thinking__sequentialthinking` to decompose research
needs into discrete domains and determine spawn strategy.

### 4.2 TeamCreate + Orchestration

If Team does not yet exist (first time entering Phase 2):

```
TeamCreate:
  team_name: "{feature-name}"

orchestration-plan.md:
  current_phase: 2
  active_teammates: []  # populated after spawn
  gc_version: GC-v1
  gate_history:
    phase_1: APPROVED
```

### 4.3 Researcher Spawn + DIA Protocol

**Spawn Configuration:**

```
Task tool:
  subagent_type: "researcher"
  team_name: "{feature-name}"
  name: "researcher-{N}"
  mode: "plan"
```

**[DIRECTIVE] Construction:**

```
[DIRECTIVE] Phase 2: {research topic}
Files: {investigation targets}
[INJECTION] GC-v1:
{--- full global-context.md content embedded ---}
task-context.md:
{--- research scope, expected deliverables, exclusions ---}
```

**DIA Flow (delegated to CLAUDE.md [PERMANENT] §7):**

1. Researcher → `[STATUS] CONTEXT_RECEIVED GC-v1`
2. Researcher → `[IMPACT-ANALYSIS]` (TIER 3: 3 sections, 5 RC items)
   - [MANDATORY] Researcher uses `sequential-thinking` for analysis
3. Lead → RC checklist verification
   - [MANDATORY] Lead uses `sequential-thinking` for evaluation
4. Lead → `[CHALLENGE]` LDAP MEDIUM (1Q)
   - Category: context-dependent selection from 7 LDAP categories
   - [MANDATORY] Lead uses `sequential-thinking` to generate challenge
5. Researcher → `[CHALLENGE-RESPONSE]` with specific evidence
   - [MANDATORY] Researcher uses `sequential-thinking` for defense
6. Lead → `[IMPACT_VERIFIED] Proceed.` or `[IMPACT_REJECTED]` (max 3 attempts)
   - [MANDATORY] Lead uses `sequential-thinking` for final evaluation

### 4.4 Research Execution + L1/L2 Handoff

**Researcher Capabilities:**
- Codebase exploration: Read, Glob, Grep
- External research: WebSearch, WebFetch
- Documentation lookup: mcp__context7__resolve-library-id, mcp__context7__query-docs
- Analysis: mcp__sequential-thinking__sequentialthinking [MANDATORY]

**Output Artifacts:**

```
.agent/teams/{session-id}/phase-2/researcher-{N}/
├── L1-index.yaml    (YAML, ≤50 lines)
│   - files_examined: [list]
│   - key_findings: [list]
│   - gaps_identified: [list]
│   - recommendations: [list]
│
├── L2-summary.md    (Markdown, ≤200 lines)
│   - Research narrative
│   - Detailed findings with evidence
│   - Constraints discovered
│   - Recommendations for Phase 3
│
└── L3-full/         (directory)
    - Raw research data, code snippets, external docs
```

**Completion:**
Researcher → Lead: `[STATUS] Phase 2 | COMPLETE` via SendMessage

### 4.5 Gate 2 → global-context.md v2

**Gate 2 Criteria:**

| # | Criterion | Check |
|---|-----------|-------|
| G2-1 | All researcher L1/L2 artifacts exist | YES/NO |
| G2-2 | All "Phase 2 Research Needs" from GC-v1 covered | YES/NO |
| G2-3 | Sufficient information for Phase 3 Architecture | YES/NO |
| G2-4 | No unresolved critical unknowns | YES/NO |
| G2-5 | Researcher L1/L2 quality meets standard | YES/NO |

**[MANDATORY] sequential-thinking usage:**
Lead MUST use `mcp__sequential-thinking__sequentialthinking` to evaluate all Gate 2
criteria, cross-referencing researcher outputs against GC-v1 research needs.

**On APPROVE:**
1. Update global-context.md → GC-v2 (add research findings)
2. Shutdown researcher(s): `SendMessage type: "shutdown_request"`
3. Write `phase-2/gate-record.yaml`
4. Proceed to Phase 3

**On ITERATE (max 3):**
- Identify gaps → re-direct existing researcher or spawn new one
- Update task-context.md with specific gap instructions

**GC-v2 Additions:**

```markdown
## Research Findings
{Synthesized from all researcher L2 summaries}

## Codebase Constraints
{Discovered technical limitations}

## Phase 3 Architecture Input
{Key information the architect needs}

## Phase Pipeline Status
- Phase 1: COMPLETE
- Phase 2: COMPLETE (Gate 2 APPROVED)
- Phase 3: PENDING
```

---

## 5. Phase 3 — Architecture

**Executor:** architect(1) | **DIA:** TIER 2 + LDAP MAXIMUM(3Q+alt) | **Protocol:** CLAUDE.md [PERMANENT] §7

### 5.1 Architect Spawn + CIP

**Spawn Configuration:**

```
Task tool:
  subagent_type: "architect"
  team_name: "{feature-name}"
  name: "architect-1"
  mode: "plan"
```

**[DIRECTIVE] Construction:**

```
[DIRECTIVE] Phase 3: {architecture task}
Files: {target scope from P1 + P2 discoveries}
[INJECTION] GC-v2:
{--- full global-context.md v2 embedded ---}
task-context.md:
{--- Phase 1 scope, Phase 2 research L2 summaries, architecture expectations ---}
```

### 5.2 DIA: TIER 2 + LDAP MAXIMUM

Phase 3 carries the **highest verification intensity** in the entire brainstorming-pipeline.

**DIA Flow (delegated to CLAUDE.md [PERMANENT] §7):**

1. Architect → `[STATUS] CONTEXT_RECEIVED GC-v2`
2. Architect → `[IMPACT-ANALYSIS]` (TIER 2: 4 sections, 7 RC items)
   - [MANDATORY] Architect uses `sequential-thinking` for analysis
3. Lead → RC checklist verification (7 items)
   - [MANDATORY] Lead uses `sequential-thinking` for evaluation
4. Lead → `[CHALLENGE]` LDAP MAXIMUM (3Q + ALTERNATIVE_DEMAND)
   - Q1: Select from {INTERCONNECTION_MAP, SCOPE_BOUNDARY, RIPPLE_TRACE, FAILURE_MODE, DEPENDENCY_RISK, ASSUMPTION_PROBE}
   - Q2: Different category from Q1
   - Q3: Different category from Q1, Q2
   - +ALT: ALTERNATIVE_DEMAND — "Propose one alternative to your architecture and defend why current proposal is superior with specific evidence"
   - [MANDATORY] Lead uses `sequential-thinking` for challenge generation
5. Architect → `[CHALLENGE-RESPONSE]` × 3 + alternative defense
   - [MANDATORY] Architect uses `sequential-thinking` for each defense
6. Lead → Defense quality evaluation
   - [MANDATORY] Lead uses `sequential-thinking` for evaluation
   - STRONG defense → `[IMPACT_VERIFIED] Proceed.`
   - WEAK defense → `[IMPACT_REJECTED]` + specific feedback (max 3 attempts → ABORT)

### 5.3 Architecture Design + L1/L2/L3 Handoff

**Architect submits [PLAN] before execution:**

```
[PLAN] Phase 3 | Files: {design artifacts} | Changes: {architecture decisions} | Risk: {assessment}
```

Lead approves [PLAN] → Architect proceeds.

**[MANDATORY] sequential-thinking usage:**
Architect MUST use `mcp__sequential-thinking__sequentialthinking` for ALL design work:
- Component decomposition
- Interface definition
- Trade-off analysis
- Risk identification

**Architecture Design Content (L3-full/architecture-design.md):**

```markdown
# Architecture Design — {Feature Name}

## Component Overview
{Component diagram / hierarchy}

## Interface Definitions
{Component-to-component contracts}

## Data Flow
{Input → Processing → Output for key paths}

## Error Handling Strategy
{Failure modes and recovery}

## Key Decisions
| # | Decision | Alternatives Considered | Rationale |
|---|----------|------------------------|-----------|

## Phase 4 Input Requirements
{What the Detailed Design phase needs from this architecture}

## Risk Register
| # | Risk | Probability | Impact | Mitigation |
|---|------|-------------|--------|------------|
```

**Output Artifacts:**

```
.agent/teams/{session-id}/phase-3/architect-1/
├── L1-index.yaml    (YAML, ≤50 lines)
│   - components: [list]
│   - interfaces: [list]
│   - decisions: [list with IDs]
│   - risks: [list with severity]
│   - phase_4_inputs: [list]
│
├── L2-summary.md    (Markdown, ≤200 lines)
│   - Architecture narrative and rationale
│   - Key trade-offs explained
│   - Phase 4 readiness assessment
│
└── L3-full/
    └── architecture-design.md  (full design, no length limit)
```

**Completion:**
Architect → Lead: `[STATUS] Phase 3 | COMPLETE` via SendMessage

### 5.4 Gate 3 → global-context.md v3 + Clean Termination

**Gate 3 Criteria:**

| # | Criterion | Check |
|---|-----------|-------|
| G3-1 | Architect L1/L2/L3 artifacts exist | YES/NO |
| G3-2 | Architecture satisfies Phase 1 Scope Statement | YES/NO |
| G3-3 | Phase 2 research findings reflected in design | YES/NO |
| G3-4 | Component interfaces clearly defined | YES/NO |
| G3-5 | Phase 4 entry requirements specified in design | YES/NO |
| G3-6 | No unresolved architectural risks (HIGH+) | YES/NO |
| G3-7 | Architecture decisions documented with rationale | YES/NO |

**[MANDATORY] sequential-thinking usage:**
Lead MUST use `mcp__sequential-thinking__sequentialthinking` to evaluate all Gate 3
criteria, cross-referencing architect outputs against GC-v2 and Phase 1 scope.

**On APPROVE:**
1. Update global-context.md → GC-v3 (add architecture decisions)
2. Write `phase-3/gate-record.yaml`
3. Proceed to Clean Termination

**On ITERATE (max 3):**
- Specific redesign instructions to architect
- Update task-context.md with revision guidance

**GC-v3 Additions:**

```markdown
## Architecture Decisions
{Synthesized from architect L1/L2}

## Component Map
{Component list with responsibilities}

## Interface Contracts
{Key interfaces between components}

## Phase 4 Entry Requirements
{What Detailed Design needs — feeds into writing-plans skill}

## Phase Pipeline Status
- Phase 1: COMPLETE
- Phase 2: COMPLETE
- Phase 3: COMPLETE (Gate 3 APPROVED)
- Phase 4: PENDING (use writing-plans skill)
```

---

## 6. Clean Termination

After Gate 3 APPROVE, the skill terminates cleanly:

### 6.1 Output Summary to User

```markdown
## brainstorming-pipeline Complete (Phase 1-3)

**Feature:** {feature-name}
**Complexity:** {SIMPLE|MEDIUM|COMPLEX}
**Phases Completed:** 3/3

**Artifacts:**
- `{session-dir}/global-context.md` (GC-v3 — full project context)
- `{session-dir}/orchestration-plan.md` (pipeline state)
- `{session-dir}/phase-2/researcher-{N}/L2-summary.md` (research)
- `{session-dir}/phase-3/architect-1/L3-full/architecture-design.md` (architecture)

**Next Step:**
Phase 4 (Detailed Design) — use the optimized `writing-plans` skill.
Input: `{session-dir}/` directory (all artifacts above).
```

### 6.2 Teammate Shutdown

```
For each active teammate:
  SendMessage type: "shutdown_request"
  Wait for shutdown_response (approve)
```

Note: Researchers should already be shut down after Gate 2.
Only architect-1 should remain at this point.

### 6.3 TeamDelete

```
TeamDelete — removes team and task directories
```

**Important:** The `.agent/teams/{session-id}/` directory with all artifacts
is preserved. Only the team coordination files are cleaned up.

---

## 7. Cross-Cutting Requirements

### 7.1 Sequential Thinking — MANDATORY

**Applies to:** Lead AND all Teammates, ALL Phases.

| Agent | When | Purpose |
|-------|------|---------|
| Lead (P1) | After Recon, after each user response, before Scope Statement, at each Gate | Structured reasoning about project state and user intent |
| Lead (P2-3) | DIA verification, LDAP challenge generation, Gate evaluation, GC updates | Rigorous protocol evaluation |
| Researcher (P2) | Research strategy, findings synthesis, L2 writing | Systematic investigation |
| Architect (P3) | Component design, trade-off analysis, interface definition, L2 writing | Architectural reasoning |

**Enforcement:** Skill document states [MANDATORY] at every decision point.
Agent .md files reinforce via Protocol section.

### 7.2 Error Handling

| Error | Response |
|-------|----------|
| Teammate spawn failure | Retry once, then ABORT phase with user notification |
| DIA verification 3x FAIL | ABORT teammate, re-spawn with enhanced CIP |
| Gate criteria not met after 3 iterations | ABORT phase, present partial results to user |
| Context compact mid-phase | Follow CLAUDE.md §8 Compact Recovery protocol |
| User cancellation | Graceful shutdown of all teammates, preserve artifacts |

### 7.3 Compact Recovery

Follows CLAUDE.md §8 exactly:

**Lead recovery:**
1. Read orchestration-plan.md
2. Read Shared Task List
3. Read current phase gate-record.yaml
4. Read active teammates' L1 indexes
5. Re-inject [DIRECTIVE]+[INJECTION] with latest GC-v{N}

**Teammate recovery:**
1. Receive [INJECTION] from Lead
2. Read own L1 → L2 → L3 as needed
3. Re-submit [IMPACT-ANALYSIS]
4. Wait for [IMPACT_VERIFIED]

### 7.4 Skill Invocation

**Trigger:** User invokes `brainstorming-pipeline` (custom skill, not superpowers plugin).

**Arguments:** Free-form text describing the feature/task. Parsed during Phase 1.1 Recon.

**Prerequisites:**
- Agent Teams mode enabled (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`)
- CLAUDE.md v3.0+ (DIA + LDAP)
- tmux session active

---

## 8. Comparison: brainstorming vs brainstorming-pipeline

| Aspect | brainstorming (solo) | brainstorming-pipeline (Agent Teams) |
|--------|---------------------|--------------------------------------|
| Mode | Single agent | Multi-agent pipeline |
| Phases | Implicit (Q&A → design) | Explicit (P1 → P2 → P3) |
| Context Scan | "Check project state" | 3-Layer Structured Recon |
| Q&A | Freeform, one at a time | Freeform + Category Awareness |
| Approaches | "2-3 with trade-offs" | Structured Trade-off Matrix |
| Scope Definition | Implicit in design doc | Explicit Scope Crystallization |
| Research | Lead does inline | Dedicated researcher teammates |
| Architecture | Lead does inline | Dedicated architect teammate |
| DIA | N/A | Full 3-Layer (CIP + DIAVP + LDAP) |
| Sequential Thinking | Optional | MANDATORY for all agents |
| Output | docs/plans/ design doc | .agent/teams/ GC + L1/L2/L3 |
| Next Step | worktree → writing-plans | Clean termination → writing-plans |
| Post-chain | Auto-chain to worktree | No chain — user controls |

---

## 9. Implementation Notes

### Skill File Location
`.claude/skills/brainstorming-pipeline/SKILL.md`

### Skill File Structure
```
.claude/skills/brainstorming-pipeline/
└── SKILL.md    (single file — all instructions inline)
```

### Implementation Scope
- 1 new file: `SKILL.md`
- 0 existing files modified (brainstorming untouched, CLAUDE.md unchanged)
- Custom skill — independent of superpowers plugin lifecycle

### Dependencies
- CLAUDE.md v3.0 (DIA + LDAP enforcement)
- Agent Teams experimental flag
- sequential-thinking MCP server
- 6 agent types available (.claude/agents/)
