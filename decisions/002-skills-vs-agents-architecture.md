# Decision 002: Skills vs Agents Architecture — Redundancy Analysis

**Status:** PENDING USER DECISION  
**Date:** 2026-02-11  
**Context:** CLAUDE.md v6.0 · 10 Skills · 27 Agents · 10 Categories  
**Depends on:** Decision 001 (Pipeline Routing Strategy)

---

## 1. Problem Statement

Four interrelated design questions require resolution:

1. **If the Lead already routes dynamically via §6 Selection Flow, are pipeline Skills redundant?**  
   (Exclude brainstorming-pipeline — it is marked for enhancement, not removal.)
2. **Is "Teammate Spawn = Agent Invocation" sufficiently enforced?**
3. **What is the actual relationship between Skills and Agents?**
4. **If Skills are minimized, what is the impact on Agents?**

---

## 2. Current Architecture Analysis

### 2.1 What Skills Actually Do

Each Skill is a **procedural script** that tells the Lead:
- Which Phase(s) to execute
- Which Agents to spawn, in what order
- What context to inject into Agent directives
- What Gate criteria to evaluate
- How to handle errors and compact recovery
- When to terminate (no auto-chaining)

**Complete Skill → Phase → Agent Mapping:**

| Skill | Phase(s) | Agents Spawned | Lead Routing Needed? |
|-------|----------|----------------|---------------------|
| `permanent-tasks` | P0 | None (Lead-only) | NO — utility, not pipeline |
| `brainstorming-pipeline` | P0-P3 | research-coordinator, codebase-researcher, external-researcher, auditor, architect | YES — complex multi-phase |
| `agent-teams-write-plan` | P0, P4 | architect | MINIMAL — single agent |
| `plan-validation-pipeline` | P0, P5 | devils-advocate | MINIMAL — single agent |
| `agent-teams-execution-plan` | P0, P6 | execution-coordinator, implementer(s), spec-reviewer, code-reviewer | YES — complex coordination |
| `verification-pipeline` | P0, P7-P8 | testing-coordinator, tester(s), integrator | YES — conditional phases |
| `delivery-pipeline` | P9 | None (Lead-only) | NO — Lead-only terminal |
| `rsil-global` | G0-G4 | codebase-researcher (Tier 3 only) | NO — meta-cognition |
| `rsil-review` | R0-R4 | claude-code-guide, codebase-researcher | NO — meta-cognition |
| `palantir-dev` | N/A | None (Lead-only) | NO — educational utility |

### 2.2 What Skills Are NOT

Skills are **not** Agent definitions. They do not define:
- Agent permissions, tools, or constraints (that's `.claude/agents/*.md`)
- Agent identity or behavioral rules (that's `agent-common-protocol.md`)
- Agent routing logic (that's `CLAUDE.md` §6 + `agent-catalog.md`)

### 2.3 The Actual Relationship

```
SKILLS ──────────────────── AGENTS
│                            │
│  "HOW to orchestrate"      │  "WHO does the work"
│  Procedural playbook       │  Identity + Permissions
│  Phase sequence            │  Tool matrix
│  Gate criteria             │  Behavioral constraints
│  Directive templates       │  Output format rules
│  Error recovery            │  Protocol compliance
│                            │
└── Lead reads Skill ──→ Lead spawns Agent(s) defined by Skill
```

**Key insight:** Skills are orchestration scripts. Agents are worker definitions. Skills tell the Lead WHICH agents to spawn and HOW to coordinate them. Agents define WHAT each worker can do and WHAT rules it follows.

### 2.4 The Redundancy Question

The Lead's "free discretion" in routing comes from CLAUDE.md §6:

```
Category has coordinator? → Route to coordinator
Category is Lead-direct?  → Spawn agent directly
```

This routing logic tells the Lead **which agent type** to pick. But it does NOT tell the Lead:

1. What context to include in the directive (PT-ID, GC version, plan paths)
2. What Gate criteria to evaluate at phase boundaries
3. How many workers to spawn (adaptive spawn algorithm)
4. What error handling and recovery procedures to follow
5. What understanding verification questions to ask
6. How to construct review prompt templates
7. What artifacts to create and where

**These are ALL defined in Skills, not in CLAUDE.md or agent-catalog.md.**

---

## 3. Question 1: Are Pipeline Skills Redundant?

### Answer: NO — but some are over-specified

**Skills that provide irreplaceable orchestration logic:**

| Skill | Why Irreplaceable |
|-------|-------------------|
| `brainstorming-pipeline` | Multi-phase Q&A flow, approach exploration, scope crystallization — cannot be derived from agent definitions alone. USER MANDATED: enhance, not remove. |
| `agent-teams-execution-plan` | Adaptive spawn algorithm, two-stage review lifecycle, cross-boundary escalation protocol, consolidated reporting format. 644 lines of orchestration logic that agents cannot self-derive. |
| `verification-pipeline` | Conditional Phase 8 trigger, coordinator transition protocol, conflict resolution principles. Complex conditional flow. |

**Skills that ARE potentially redundant (single-agent, thin orchestration):**

| Skill | Lines | What It Adds Beyond "Spawn Agent X" |
|-------|-------|--------------------------------------|
| `agent-teams-write-plan` | 342 | Directive template for architect (PT-ID injection, CH-001 exemplar path, 10-section template reference). Gate 4 criteria. GC-v3→v4 update format. |
| `plan-validation-pipeline` | 405 | Directive template for devils-advocate (6 challenge categories, severity ratings, MCP tool instructions). Gate 5 criteria. Verdict-driven gating. |

**Analysis of "thin" Skills:** Even these 300-400 line Skills contain ~50% unique procedural content (directive construction, gate criteria, GC update format) that would need to live SOMEWHERE if the Skill were removed. The alternative is embedding all of this in CLAUDE.md or agent-catalog.md, which would bloat those files significantly.

### Recommendation

**Do NOT remove any pipeline Skills.** The orchestration logic they contain is not redundant with agent definitions — it is complementary. Removing Skills would require relocating their procedural content to CLAUDE.md (already 337 lines) or agent .md files (wrong abstraction level — agents should define identity, not orchestration).

**Exception:** `permanent-tasks`, `palantir-dev`, `rsil-global`, and `rsil-review` are utility/meta-cognition Skills — they are orthogonal to the pipeline and should remain regardless.

---

## 4. Question 2: Is "Teammate Spawn = Agent Invocation" Sufficiently Enforced?

### Current State

The user wants: **Every Teammate Spawn MUST use a registered Agent from `.claude/agents/*.md`.**

**Existing enforcement mechanisms:**

| Mechanism | Location | Enforcement Level |
|-----------|----------|-------------------|
| "Use exact `subagent_type` to spawn" | CLAUDE.md Line 17 | NL instruction (MEDIUM) |
| "never generic built-ins (Explore, general-purpose)" | CLAUDE.md Line 62 | NL prohibition (MEDIUM) |
| `subagent_type` table listing all 27 agents | CLAUDE.md Lines 24-59 | Reference table (LOW — informational) |
| Agent .md files in `.claude/agents/` | File system | Definition exists but no spawning constraint |
| `mode: "default"` always | CLAUDE.md Line 63 | NL instruction (MEDIUM) |

**Gaps identified:**

1. **No explicit statement that Teammate = Agent.** CLAUDE.md uses both terms but never states they are identical. A sufficiently creative Lead could interpret "teammate" as any spawned subagent, including built-in types not registered in `.claude/agents/`.

2. **No negative constraint.** The instruction says "use exact `subagent_type`" but does NOT say "spawning a subagent without a corresponding `.claude/agents/*.md` file is PROHIBITED."

3. **No enforcement hook.** There is no `on-subagent-start` validation that checks whether the `subagent_type` matches a registered agent file. (Note: proposing a new hook would violate AD-15. This is documented as a Layer 2 gap.)

4. **Built-in `claude-code-guide` exception.** Line 59 lists it as "not a custom agent" — it has no `.claude/agents/claude-code-guide.md` file. This creates an inconsistency: a spawnable type exists without an agent definition file.

### Proposed Fix (Category B — NL text change)

Add to CLAUDE.md §1 or §6, immediately after the spawning rules:

```markdown
**Teammate = Agent. No exceptions.**
Every spawned subagent (Task tool invocation) MUST use a `subagent_type` value 
that has a corresponding `.claude/agents/{subagent_type}.md` definition file.
Spawning ANY subagent without a registered agent definition is PROHIBITED.
The only exception is the built-in `claude-code-guide` (CC documentation lookup — 
no agent definition required because it is a platform capability, not a custom agent).
```

**Enforcement level after fix:** STRONG (explicit NL prohibition + identity statement).  
**Layer 2 gap:** Runtime validation via hook is not possible under AD-15. The NL instruction is the maximum achievable enforcement at Layer 1.

---

## 5. Question 3: Skills ↔ Agents Relationship

### Formal Definition

```
┌─────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION LAYER                       │
│                                                              │
│  CLAUDE.md §6    ── "WHICH category/agent type to pick"      │
│  agent-catalog   ── "WHEN to spawn, routing rules"           │
│  Skills (SKILL.md)── "HOW to orchestrate the full phase"     │
│                                                              │
│  Relationship:   Lead reads Skill → Skill tells Lead which   │
│                  Agents to spawn and how to coordinate them   │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                    EXECUTION LAYER                           │
│                                                              │
│  Agents (.md)    ── "WHO the worker is"                      │
│  agent-common-protocol ── "WHAT rules all workers follow"    │
│                                                              │
│  Relationship:   Agent spawns → reads its .md definition     │
│                  → follows agent-common-protocol              │
│                  → produces L1/L2/L3 artifacts                │
│                                                              │
└─────────────────────────────────────────────────────────────┘

Dependency Direction:
  Skills DEPEND ON Agents (Skills reference specific subagent_types)
  Agents DO NOT depend on Skills (Agents work from directives, not Skills)
```

### Key Implications

1. **Skills are consumed by Lead only.** Agents never read Skill files.
2. **Agents are consumed by the Claude Code runtime.** The `subagent_type` parameter triggers the runtime to load the corresponding `.claude/agents/*.md` file.
3. **Removing a Skill does NOT remove the Agent.** The Agent definition persists and can be spawned by Lead's discretion.
4. **Removing an Agent BREAKS Skills** that reference that `subagent_type`.

---

## 6. Question 4: If Skills Are Minimized, What Happens to Agents?

### Scenario Analysis

**If we remove pipeline Skills** (write-plan, plan-validation, execution-plan, verification, delivery):

| Impact Area | What Happens |
|-------------|-------------|
| **Agent definitions** | UNCHANGED. All 27 `.claude/agents/*.md` files remain. Agents are NOT deleted. |
| **Agent spawning** | Lead would need to derive orchestration logic from CLAUDE.md §6 + agent-catalog.md "WHEN to Spawn" table ALONE. |
| **Directive construction** | LOST. Skills contain detailed directive templates (what PT-ID format to use, what GC version to reference, what exemplar paths to include). Lead would need to improvise directives. |
| **Gate criteria** | LOST. Skills define specific G1-1 through G8-6 criteria. Lead would need to derive gate criteria from general principles. |
| **Error recovery** | LOST. Skills define compact recovery procedures, fix loop limits, escalation protocols. Lead would fall back to generic CLAUDE.md §9 recovery. |
| **Adaptive algorithms** | LOST. The execution-plan adaptive spawn algorithm (dependency graph → connected components → implementer count) would need to be reinvented by Lead each time. |
| **Review templates** | LOST. Spec-reviewer and code-reviewer prompt templates would need to be improvised. |
| **Quality consistency** | DEGRADED. Each pipeline run would vary in orchestration quality based on Lead's context window state and reasoning capacity. |

### Net Effect on Agents

**Direct impact: ZERO.** Agent definition files are unchanged. Agent permissions, tools, and constraints remain identical.

**Indirect impact: SIGNIFICANT.** Agents receive their context from Lead's directives. Without Skills to standardize directive construction, directive quality becomes dependent on Lead's improvisation. This means:

1. Agents may receive incomplete context (missing PT-ID, wrong GC version)
2. Agents may be spawned at wrong phases (no gate enforcement)
3. Agents may produce inconsistent artifacts (no L1/L2/L3 format enforcement from Skill)
4. Understanding verification may be skipped (no explicit verification protocol in Skill)

### Conclusion

**Minimizing Skills does not remove Agents but degrades the quality and consistency of Agent coordination.** Skills are the mechanism that translates the declarative Agent roster into repeatable, verified orchestration procedures.

---

## 7. Decision Matrix

| Option | Description | Risk | Consistency |
|--------|-------------|------|-------------|
| **A. Keep All Skills** | No changes. Current architecture preserved. | LOW | HIGH |
| **B. Remove Thin Skills Only** | Remove write-plan + plan-validation. Embed their orchestration in CLAUDE.md or agent-catalog.md. Keep complex Skills. | MEDIUM | MEDIUM — two sources of orchestration logic |
| **C. Remove All Pipeline Skills** | Lead uses CLAUDE.md §6 + agent-catalog.md only. | HIGH | LOW — Lead improvises orchestration |
| **D. Keep All Skills + Add Enforcement** | Add explicit "Teammate = Agent" constraint to CLAUDE.md. Enhance brainstorming-pipeline. | LOW | HIGHEST |

### Recommendation: **Option D**

1. **Keep all Skills** — they provide irreplaceable orchestration logic
2. **Add "Teammate = Agent" enforcement** (Section 4 proposed text)
3. **Enhance brainstorming-pipeline** (per user mandate — separate decision)
4. **Do NOT remove any Agent definitions** — Skills depend on them
5. **Consider adding a routing preamble to CLAUDE.md** that explains Skills are orchestration playbooks, not alternatives to Agents

---

## 8. Proposed CLAUDE.md Amendment

Add immediately after Line 67 (`Full agent details and tool matrix...`):

```markdown
### Skills ↔ Agents Relationship

- **Skills** = orchestration playbooks. They define HOW to coordinate a phase 
  (directive templates, gate criteria, error recovery, adaptive algorithms).
  Lead reads the relevant Skill file to execute a phase. Skills reference 
  specific `subagent_type` agents.
- **Agents** = worker identities. They define WHO does the work 
  (permissions, tools, constraints, output format). Agent definitions in 
  `.claude/agents/*.md` are loaded by the runtime when `subagent_type` is used.
- **Dependency direction:** Skills depend on Agents. Agents do not depend on Skills.
- **Teammate = Agent. No exceptions.** Every Task tool invocation MUST use a 
  `subagent_type` with a corresponding `.claude/agents/{type}.md` file.
  The only exception is `claude-code-guide` (platform built-in, no agent file).
  Spawning any subagent without a registered agent definition is PROHIBITED.
```

---

## 9. User Decision Items

- [ ] **Option A** — Keep all Skills, no changes
- [ ] **Option B** — Remove thin Skills (write-plan, plan-validation), embed in CLAUDE.md
- [ ] **Option C** — Remove all pipeline Skills, Lead improvises
- [ ] **Option D** — Keep all Skills + add enforcement (RECOMMENDED)
- [ ] **Other** — alternative direction

### Sub-decisions (if Option D selected):

- [ ] Approve Section 4 "Teammate = Agent" text for CLAUDE.md
- [ ] Approve Section 8 "Skills ↔ Agents Relationship" text for CLAUDE.md
- [ ] Confirm brainstorming-pipeline enhancement scope (separate decision document)

---

## 10. Claude Code Directive (Fill after decision)

```
DECISION: Option [A/B/C/D]
SCOPE:
  - CLAUDE.md: Add §Skills↔Agents relationship block after Line 67
  - CLAUDE.md: Add Teammate=Agent enforcement to spawning rules
  - brainstorming-pipeline: [ENHANCE — scope TBD in separate decision]
CONSTRAINTS:
  - No Agent .md files modified
  - No Skill files removed (Option D)
  - AD-15 inviolable (no new hooks)
  - All text in English
PRIORITY: Consistency > Safety > Speed
```
