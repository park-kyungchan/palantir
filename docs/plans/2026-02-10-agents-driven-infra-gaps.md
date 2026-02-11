# Agents-Driven Workflow — INFRA Gap Analysis (v2)

**Author:** infra-analyst (researcher)
**Date:** 2026-02-10
**Status:** ANALYSIS — v2 (revised after Lead probing + scaling update)
**PT Context:** PT-v3 "Ontology Progressive Learning System" — side-workstream
**Downstream Consumer:** Lead → Architect (INFRA evolution design)

---

## 1. Executive Summary

### Vision

The agents-driven workflow applies **1-Agent:1-Responsibility** — each agent type has a
razor-sharp focus, doing one thing extremely well. Lead composes these fine-grained agents
at spawn time. Currently 6 registered agents cover the 10-phase pipeline. The future state
targets **15-20+ agents** (30-60L each), where Lead ALWAYS delegates to a registered,
standardized agent rather than issuing ad-hoc one-shot Task calls.

**Design principle:** Fine-grained agents outperform coarse agents. Evidence: 3 parallel
verifiers (verifier-static/relational/behavioral) outperformed a single generic verifier
through deeper domain focus, parallel execution, and cleaner L1/L2 output.

### Revision Notes (v2)

v1 assumed 6→8-12 agents. After Lead's probing questions and scaling update, v2 addresses:
- **PQ-1:** Skill-agent coupling is SEMANTICALLY tight (directive content), not just string-tight
- **PQ-2:** At 20 agents, §2 table + flat decision tree insufficient → need two-level
  selection (Category → Specific Agent) via a structured Agent Catalog
- **Scaling:** 15-20+ fine-grained agents (30-60L each) fundamentally changes D1, D2, D4, D7, D9

### Key Gaps Found (Revised)

| Priority | Count | Summary |
|----------|-------|---------|
| CRITICAL | 2 | D1: Agent Catalog essential at 20 agents; D7: Two-level selection mechanism |
| HIGH | 3 | D2: Category-based phase table; D6: Semantic skill coupling; D9: Parallel agent coordination |
| MEDIUM | 3 | D3: Protocol Team Memory fix; D4: Tool permission profiles; D10: RTD metadata |
| LOW | 2 | D5: Context budget (actually improves); D8: Lifecycle (scales well) |

### Core Insight (Revised)

Per-agent scaling is **better than before** — fine-grained agents are SMALLER (30-60L vs.
66-84L), so per-spawn context cost actually DECREASES. The critical challenge is
**Lead-side coordination** at scale: selecting from 20 agents, composing multi-agent
phases, and managing N parallel agents within a single phase.

The architectural solution is an **Agent Category System**: agents group into categories
(Research, Verification, Design, Validation, Implementation, Testing, Integration), and
Lead selects in two stages — Category first, then specific agent within category.

---

## 2. Current INFRA Inventory

### Components and Sizes

| Component | File(s) | Lines | Role in Agent Lifecycle |
|-----------|---------|-------|------------------------|
| CLAUDE.md | `.claude/CLAUDE.md` | 206 | Team constitution, §2 agent-phase mapping, §6 Lead operations |
| settings.json | `.claude/settings.json` | 82 | Hooks, permissions, env vars |
| agent-common-protocol.md | `.claude/references/agent-common-protocol.md` | 108 | Shared lifecycle procedures for all agents |
| researcher.md | `.claude/agents/researcher.md` | 66 | Phase 2 agent definition |
| architect.md | `.claude/agents/architect.md` | 77 | Phase 3-4 agent definition |
| implementer.md | `.claude/agents/implementer.md` | 84 | Phase 6 agent definition |
| tester.md | `.claude/agents/tester.md` | 80 | Phase 7 agent definition |
| devils-advocate.md | `.claude/agents/devils-advocate.md` | 76 | Phase 5 agent definition |
| integrator.md | `.claude/agents/integrator.md` | 84 | Phase 8 agent definition |
| task-api-guideline.md | `.claude/references/task-api-guideline.md` | 118 | Task creation/management conventions |
| brainstorming-pipeline | `.claude/skills/brainstorming-pipeline/SKILL.md` | 581 | Phase 1-3 orchestration |
| execution-plan | `.claude/skills/agent-teams-execution-plan/SKILL.md` | 605 | Phase 6 orchestration |
| verification-pipeline | `.claude/skills/verification-pipeline/SKILL.md` | 536 | Phase 7-8 orchestration |
| 4 hooks | `.claude/hooks/on-*.sh` | ~250 | SubagentStart, PreCompact, SessionStart, PostToolUse |
| **Total** | | **~2,953** | |

### Agent Type Summary (Current 6 + Proposed)

| Agent | Phase | Max | Tools (unique) | Lines |
|-------|-------|-----|----------------|-------|
| researcher | 2 | 3 | WebSearch, WebFetch | 66 |
| architect | 3-4 | 1 | Write (design docs only) | 77 |
| devils-advocate | 5 | 1 | (read-only) | 76 |
| implementer | 6 | 4 | Edit, Write, Bash | 84 |
| tester | 7 | 2 | Write, Bash | 80 |
| integrator | 8 | 1 | Edit, Write, Bash (cross-boundary) | 84 |
| **verifier** (proposed) | 2 | 3 | Write, WebSearch, WebFetch | ~90 |

### Hook Agent-Awareness

| Hook | Agent-Aware? | Details |
|------|-------------|---------|
| SubagentStart | YES | Captures agent_type, writes to session-registry.json |
| PreCompact | NO | Fires for Lead only (teammates save proactively) |
| SessionStart | NO | Compact recovery for Lead only |
| PostToolUse | PARTIAL | Logs tool calls, session-registry resolves agent type |

---

## 3. Gap Analysis (D1-D10)

### D1: Agent Registration & Discovery Mechanism

**Current State:**
- Agent definitions live as `.md` files in `.claude/agents/`
- CLAUDE.md §2 Phase Pipeline table references agent types by name
- MEMORY.md tracks agent count ("6 types" in INFRA State table)
- No manifest, registry, or discovery mechanism beyond filesystem + documentation
- Discovery path: Lead reads §2 → knows which agents exist

**Gap at 15-20+ Agents:**
- **Filesystem listing is noise at 20 files.** `ls .claude/agents/` returns 20 entries:
  researcher.md, verifier-static.md, verifier-relational.md, verifier-behavioral.md,
  architect.md, architect-infra.md, implementer.md, implementer-schema.md, ... Lead
  cannot efficiently scan 20 filenames to identify the right agent for a task.
- **No capability metadata.** Agent .md files describe tools and constraints, but there's
  no structured index of "which agents do web verification" or "which agents write code."
- **Adding a new agent requires updating 3+ locations:** agent .md, CLAUDE.md §2,
  MEMORY.md, and any skills that should reference it.
- **No CATEGORY grouping.** At 6 agents, categories are implicit (each is unique). At 20,
  agents cluster into families (verifier-static, verifier-relational, verifier-behavioral
  are all "Verification" category) that need an organizing principle.

**Proposed Change:**
Create an **Agent Catalog Reference** at `.claude/references/agent-catalog.md` (~80-120L).
This is the ESSENTIAL scaling mechanism — a structured NL reference that:

1. **Organizes agents by CATEGORY** (the top-level grouping):
   ```
   ## Research Category
   Agents that explore, discover, and synthesize.
   | Agent | Focus | Phase | Max | Key Tools |
   | researcher | General exploration | 2 | 3 | WebSearch, WebFetch |
   | researcher-domain | Domain-specific deep dive | 2 | 3 | WebSearch, WebFetch |

   ## Verification Category
   Agents that validate claims against authoritative sources.
   | Agent | Focus | Phase | Max | Key Tools |
   | verifier-static | Schema components | 2 | 3 | WebSearch, WebFetch, Write |
   | verifier-relational | Relationships | 2 | 3 | WebSearch, WebFetch, Write |
   | verifier-behavioral | Actions/rules | 2 | 3 | WebSearch, WebFetch, Write |
   ```

2. **Provides Agent Selection Guide** (two-level: Category → Agent, see D7)
3. **Documents Tool Permission Profiles** (see D4)
4. **Lists skill coupling** per agent (which skills reference this agent)
5. **Includes directive templates** per category (reduces Lead composition overhead)

**Why a catalog, not just filesystem?** (PQ-2 answer)
At 6 agents, `§2 table → pick the one` works. At 20, Lead needs an INDEXED reference:
"I need verification for static schema claims" → Verification Category → verifier-static.
The catalog IS the index. CLAUDE.md §2 stays concise (references categories), the catalog
provides the drill-down.

**Priority:** CRITICAL — At 20 agents, without a catalog, Lead cannot efficiently
select the right agent. Every wrong selection wastes a spawn + context + tokens.

**Effort:** MEDIUM (~80-120L new document)

---

### D2: CLAUDE.md Phase Pipeline Table

**Current State:**
§2 maps each phase to exactly one agent type:
```
| 2 | Deep Research | PRE-EXEC | researcher (1-3) | max |
```

**Gap at 15-20+ Agents:**
- **Many-to-many phase:agent mapping.** Phase 2 might use researcher, verifier-static,
  verifier-relational, verifier-behavioral — all simultaneously. The current table can't
  express this without becoming 4 lines per phase.
- **Some fine-grained agents share a phase.** 3 verifier variants all operate in Phase 2.
  4 implementer variants all operate in Phase 6. The table grows from 10 rows to 20+.
- **Table must stay concise** — it's the quick reference for pipeline structure, not a
  comprehensive agent listing (that's the catalog's job).

**Proposed Change:**
Evolve §2 to use **AGENT CATEGORIES** instead of individual agent names:

```
| # | Phase | Zone | Agent Categories | Effort |
|---|-------|------|------------------|--------|
| 0 | PT Check | PRE-EXEC | Lead only | minimal |
| 1 | Discovery | PRE-EXEC | Lead only | max |
| 2 | Deep Research | PRE-EXEC | research (1-3), verification (0-3) | max |
| 3 | Architecture | PRE-EXEC | design (1) | max |
| 4 | Detailed Design | PRE-EXEC | design (1) | high |
| 5 | Plan Validation | PRE-EXEC | validation (1) | max |
| 6 | Implementation | EXEC | implementation (1-4) | high |
| 7 | Testing | EXEC | testing (1-2) | high |
| 8 | Integration | EXEC | integration (1) | high |
| 9 | Delivery | POST-EXEC | Lead only | medium |
```

Key changes:
1. "Teammate" column → "Agent Categories" — references catalog categories
2. Instance counts are per-category, not per-agent
3. Category → specific agent selection is Lead's decision, guided by the catalog
4. Table stays at 10 rows regardless of how many agents are registered

**Priority:** HIGH — The table must remain accurate as agents multiply.

**Effort:** LOW (~15L changed in CLAUDE.md §2, add "See agent-catalog.md" note)

---

### D3: Agent-Common-Protocol Scaling

**Current State:**
`agent-common-protocol.md` (108L) provides shared procedures for all 6 agents.

**Gap:**
- **Team Memory §5 hardcodes agent names:** "If you have the Edit tool (implementer,
  integrator): write discoveries" / "If you don't have Edit (researcher, architect,
  tester): message Lead for relay." Adding verifier (Write but not Edit) creates a
  third category. At 20 agents, listing names becomes impossible.
- **Protocol should stay LEAN.** At 20 agents, each agent's unique methodology lives in
  its small .md (30-60L). The shared protocol is the stable foundation — it should NOT
  grow agent-type-specific sections.

**Proposed Change:**
1. **Replace hardcoded agent names with tool-based guidance in §5:**
   ```
   - If you have the Edit tool: write discoveries to your Team Memory section.
   - If you have Write but not Edit: write to your L3 directory and message Lead.
   - If read-only: message Lead with findings for relay.
   ```
2. **No agent-type-specific extensions.** The shared-protocol + agent-.md model scales
   to 20+ agents. Each agent's .md encodes its methodology. The protocol encodes shared
   lifecycle.

**Priority:** MEDIUM — Edit/Write fix is needed now. No structural change needed.

**Effort:** LOW (~5L changed in §5)

---

### D4: Tool Permission Architecture

**Current State:**
Each agent has its own `tools:` and `disallowedTools:` in YAML frontmatter.

Common: Read, Glob, Grep, TaskList, TaskGet, sequential-thinking, tavily
Variable: Write, Edit, Bash, WebSearch, WebFetch, context7

**Gap at 15-20+ Agents:**
- **Many agents share similar tool sets.** 3 verifier variants likely have identical tools.
  4 implementer variants likely share Edit, Write, Bash. Defining tools from scratch for
  each of 20 agents is repetitive and error-prone.
- **No "base tools" concept.** When designing a new agent, the author must remember
  that all agents need Read, Glob, Grep, TaskList, TaskGet, sequential-thinking.
  Forgetting one creates a broken agent.

**Proposed Change:**
Document **Tool Permission Profiles** in agent-catalog.md:

```
## Tool Profiles

### Base (all agents)
Read, Glob, Grep, TaskList, TaskGet, mcp__sequential-thinking__sequentialthinking

### + Web Access
WebSearch, WebFetch, mcp__tavily__search

### + Document Writing
Write

### + Code Modification
Edit, Write, Bash

### + Library Research
mcp__context7__resolve-library-id, mcp__context7__query-docs

### Profile Matrix
| Category | Base | +Web | +DocWrite | +CodeMod | +LibRes |
|----------|------|------|-----------|----------|---------|
| Research | YES | YES | NO | NO | YES |
| Verification | YES | YES | YES | NO | NO |
| Design | YES | opt | YES | NO | YES |
| Validation | YES | opt | NO | NO | YES |
| Implementation | YES | NO | — | YES | YES |
| Testing | YES | NO | YES | YES (Bash) | YES |
| Integration | YES | NO | — | YES | YES |
```

Each new agent references a profile and adds/removes as needed. This is DOCUMENTATION
(for designing agents), not enforcement (Claude Code still reads per-agent YAML).

**Priority:** MEDIUM — At 20 agents, profile documentation prevents inconsistency.
Not blocking, but design-time overhead reduction.

**Effort:** LOW (~25L in agent-catalog.md)

---

### D5: Context Budget Management

**Current State:**
- Each agent .md: 66-84 lines (loaded at spawn)
- Only the SPAWNED agent's .md loads — not all agents

**Gap at 15-20+ Agents — ACTUALLY IMPROVES:**
Fine-grained agents are SMALLER (30-60L vs. 66-84L). Per-spawn context cost DECREASES:

| Scenario | Agent .md Size | Per-Spawn Load | Lead Selection |
|----------|---------------|----------------|----------------|
| 6 agents (current) | 66-84L | ~1,200 tokens | Trivial |
| 7 (+verifier) | ~90L | ~1,350 tokens | Low |
| 15-20 (fine-grained) | **30-60L** | **~600-900 tokens** | Needs catalog |

**Key insight:** 1-Agent:1-Responsibility means LESS methodology per agent → smaller
.md files → LOWER per-spawn cost. The trade-off is more agents to choose from, which
is a selection problem (D7), not a context budget problem.

BUG-002 risk is UNAFFECTED — it's driven by task complexity, not agent count.

**Proposed Change:**
No structural changes. D7 (catalog + selection) absorbs the selection overhead.
Document the per-spawn cost model in agent-catalog.md for future agent design guidance:
"Target 30-60L for fine-grained agents. 80L+ indicates the agent's responsibility
may be too broad — consider splitting."

**Priority:** LOW — Context budget actually improves with fine-grained agents.

**Effort:** MINIMAL (~5L documentation)

---

### D6: Skill-Agent Coupling

**Current State:**
Skills hardcode agent types in spawn directives:

| Skill | Lines | Hardcoded References |
|-------|-------|---------------------|
| brainstorming-pipeline | 322-325, 396-400 | `subagent_type: "researcher"`, `"architect"` |
| execution-plan | 189-193 | `subagent_type: "implementer"` |
| verification-pipeline | 168-173, 292-297 | `subagent_type: "tester"`, `"integrator"` |

**PQ-1 Answer: Two Layers of Coupling**

The coupling has TWO layers — one loose, one tight:

1. **String coupling (LOOSE):** The `subagent_type: "researcher"` literal. Lead reads the
   skill and executes the Task tool call. Lead CAN override this — spawn a verifier where
   the skill says researcher. The string is a suggestion, not enforcement.

2. **Semantic coupling (TIGHT):** The skill's directive CONTENT is written for the specific
   agent's methodology and capabilities. Evidence:
   - brainstorming-pipeline L344: "Researchers work with: Read, Glob, Grep, WebSearch..."
     → describes researcher's tool set
   - execution-plan L211: "Execute tasks in topological order within their component"
     → assumes implementer's code-writing role
   - verification-pipeline L189: "Use context7 to verify testing framework APIs"
     → tester-specific instruction

   If Lead spawns a verifier using a researcher's directive template, the methodology
   instructions don't match. The output format expectations also differ. The DIRECTIVE
   assumes the agent's capabilities, not just its name.

**Gap at 15-20+ Agents:**
- Skills can't list 5+ agent variants per phase. The current approach (one directive
  template per agent type) doesn't scale when Phase 2 might use researcher OR any of
  3 verifier variants.
- **Skill coupling becomes a FEATURE.** Skills define the orchestration FLOW (Phase 2a →
  Phase 2b). Within each flow step, Lead selects the specific agent from the catalog.
  The skill shifts from "spawn researcher-1" to "spawn a research-category agent."

**Proposed Change:**
1. **Skills reference CATEGORIES, with per-category directive templates:**
   ```
   ### 2.3 Phase 2 Agent Spawn
   Select agents from the catalog's Research and Verification categories.
   Lead determines which specific agents based on task scope.

   #### Research Category Directive Template
   [DIRECTIVE] Phase 2: {research topic}
   ...

   #### Verification Category Directive Template (conditional)
   [DIRECTIVE] Phase 2b: Verify {component list} against {source}
   ...
   ```
2. **Per-category templates, not per-agent.** All verifier variants share a directive
   structure (claims + source + scope). The domain-specific content varies, but the
   template is category-level.
3. **Document skill-coupling map in catalog:** "verifier agents → brainstorming-pipeline §2"

**Priority:** HIGH — Semantic coupling is real and compounds with agent count.
Category-level templates are the scaling mechanism.

**Effort:** MEDIUM (per-skill: ~20-40L new template content, ~5-10L category references)

---

### D7: Lead Decision Support — Two-Level Selection

**Current State:**
CLAUDE.md §6 "Before Spawning" evaluates WHETHER to spawn (3 checks: clarity, scope,
approach). No guidance on WHICH agent to spawn.

**PQ-2 Answer: Selection Mechanism at Scale**

At 6 agents, §2 table IS the selection mechanism — Lead memorizes 6 entries. At 20 agents:
- §2 table uses categories (10 rows, same as today), but each category has 2-5 members
- A flat decision tree has too many leaves (20 options at the bottom)
- Lead needs a TWO-LEVEL selection mechanism:

**Level 1: Task Nature → Agent Category (coarse, deterministic)**
This fits in CLAUDE.md §6 as a compact guide (~15L).

**Level 2: Agent Category → Specific Agent (fine, catalog-indexed)**
This lives in agent-catalog.md, under each category section.

**Proposed Change:**

### Level 1: Category Selection (in CLAUDE.md §6)

```
### Agent Category Selection

| Task Nature | Category | Key Indicator |
|-------------|----------|---------------|
| Explore, discover, synthesize | Research | Open-ended question, unknown territory |
| Verify claims vs. external source | Verification | Specific claims, authoritative source |
| Design architecture or system | Design | Components, interfaces, ADRs needed |
| Challenge/critique a design | Validation | Existing design needs review |
| Write or modify code | Implementation | Code changes within ownership |
| Write tests, run test suites | Testing | Acceptance criteria to verify |
| Merge cross-boundary code | Integration | Multiple outputs to reconcile |

Pipeline phase overrides: If in an active phase, §2 table is authoritative.
For ad-hoc work: use the table above → then consult agent-catalog.md for
specific agent within the category.
```

### Level 2: Specific Agent Selection (in agent-catalog.md)

Per category, the catalog provides:

```
## Verification Category

### Selection Criteria
| If the scope involves... | Use |
|--------------------------|-----|
| Static schema (ObjectType, Property, Struct) | verifier-static |
| Relationships (LinkType, Interface) | verifier-relational |
| Behavior (ActionType, Function, Rules) | verifier-behavioral |
| General claims (any domain, no sub-specialization) | verifier |

### When to Use Multiple
Parallel verification: spawn one verifier per domain partition.
Evidence: 3 parallel verifiers completed in ~40% of the time vs. 1 serial verifier.
```

### Registered vs. Ad-Hoc Decision

```
Does a registered agent in the catalog match?
├── YES → Use it (standardized output, shorter directive, consistent schema)
└── NO → Use closest category + focused directive
    If directive is reused 3+ times → propose new agent registration
```

**Priority:** CRITICAL — At 20 agents, without two-level selection, Lead wastes
reasoning tokens on every spawn. The category system makes 20 agents feel like 7
categories, each with a simple lookup table.

**Effort:** MEDIUM (~15L in CLAUDE.md §6, ~40-60L in agent-catalog.md per category)

---

### D8: Agent Lifecycle (Spawn → Work → Shutdown)

**Current State:**
All agents follow agent-common-protocol.md lifecycle. `maxTurns` varies by role:
30 (devils-advocate), 50 (researcher/architect/tester), 100 (implementer/integrator).

**Gap at 15-20+ Agents:**
- **No structural gap.** Fine-grained agents are SHORTER-lived (focused task, less turns).
  maxTurns in frontmatter handles this cleanly.
- **Understanding verification scales linearly.** Each agent gets verified independently.
  At N=6 parallel agents, Lead performs 6 verification rounds. This is manageable but
  see D9 for optimization.

**Proposed Change:**
Document maxTurns guidelines per category in agent-catalog.md:
- Read-only analysis (validation, research): 20-40 turns
- Write-capable analysis (verification, design): 30-50 turns
- Code-writing (implementation, testing, integration): 50-100 turns

Fine-grained agents should generally use LOWER maxTurns than their coarse counterparts.

**Priority:** LOW — Lifecycle model scales well.

**Effort:** MINIMAL (~5L documentation)

---

### D9: Cross-Agent Communication & Parallel Coordination

**Current State:**
Hub-and-spoke: Lead mediates ALL communication. No direct agent-to-agent messaging.

**Gap at 15-20+ Agents:**
The gap intensifies significantly with fine-grained parallel agents:

- **Phase 2 with 6 agents (3 researchers + 3 verifiers).** Lead must:
  1. Spawn 3 researchers — 3 understanding verification rounds
  2. Monitor 3 parallel researchers
  3. Process 3 completion reports
  4. Spawn 3 verifiers — 3 more verification rounds
  5. Monitor 3 parallel verifiers
  6. Process 3 completion reports
  That's 12 interactions for one phase. At 6 agents per phase, Lead's per-phase overhead
  is substantial.

- **Same-category batch optimization.** When spawning 3 verifier variants, the
  understanding verification is similar (same methodology, different domain). Lead could:
  - Verify the FIRST verifier thoroughly (full probing questions)
  - Apply LIGHTER verification to subsequent same-category agents (confirm domain scope
    only — methodology understanding is inherited from the category)

**Proposed Change:**

1. **Keep hub-and-spoke.** Quality control (understanding verification) justifies the
   overhead. Direct agent-to-agent communication would bypass Lead's quality gates.

2. **Add Batch Spawn + Graduated Verification pattern to CLAUDE.md §6:**
   ```
   ### Batch Spawn (Same Category)
   When spawning N agents of the same category:
   1. Spawn all N agents in parallel (Task tool supports this)
   2. Full understanding verification for the FIRST agent:
      - Confirm methodology understanding (probing questions)
      - Confirm domain scope
   3. Light verification for agents 2-N:
      - Confirm domain scope only (methodology is category-standard)
      - If agent shows confusion, escalate to full verification
   4. Approve all agents simultaneously once verification passes

   This reduces verification from N full rounds to 1 full + (N-1) light rounds.
   ```

3. **Add Batch Handoff pattern:**
   ```
   ### Batch Handoff (Phase Transition)
   When N agents complete a phase and M agents start the next:
   1. Read all N completion L1s in parallel
   2. Synthesize findings into a category-level summary
   3. Construct M directives from the category summary (not N individual reports)
   4. Spawn M agents with the synthesized context
   ```

**Priority:** HIGH — At N=6+ parallel agents per phase, verification overhead without
batch optimization becomes the pipeline bottleneck.

**Effort:** MEDIUM (~25-30L in CLAUDE.md §6)

---

### D10: Observability and RTD

**Current State:**
- PostToolUse logs tool calls → events.jsonl
- SubagentStart captures agent_type → session-registry.json
- rtd-index.md entries reference agents by name, not by type or category

**Gap at 15-20+ Agents:**
- **More agents = more events.** But events.jsonl is append-only — O(1) per write.
  Not a scaling concern.
- **RTD entries need CATEGORY metadata** alongside agent type. "Spawned verifier-static"
  is less informative than "Spawned verifier-static (Verification category, Phase 2b)."
- **session-registry.json already handles N agents.** It's a flat map — O(1) lookup.

**Proposed Change:**
1. **Add `AGENT_TYPE:` and `AGENT_CATEGORY:` fields to rtd-index.md DP entries:**
   ```
   ### DP-5: Spawn verifier-static-1
   - WHO: Lead
   - AGENT_TYPE: verifier-static
   - AGENT_CATEGORY: Verification
   - WHAT: Verify static schema claims against palantir.com/docs
   ```
2. No hook changes (AD-15). SubagentStart already captures type.
3. The category field is informational — not enforced, just convention.

**Priority:** MEDIUM — Improves observability quality at scale.

**Effort:** MINIMAL (~7L across skill RTD templates)

---

## 4. Proposed INFRA Changes (Consolidated, Revised)

Ordered by priority. Changes marked with **(v2)** are new or significantly revised.

### Change 1: Agent Catalog with Category System [CRITICAL] **(v2)**

**Target:** NEW file `.claude/references/agent-catalog.md`
**What:** Structured NL reference organizing agents by category. Includes:
- Category definitions (7 categories)
- Per-category agent listings with capabilities, phase, tools
- Per-category selection criteria (Level 2 of decision mechanism)
- Per-category directive templates
- Tool Permission Profiles (D4)
- Skill coupling map
- Agent design guidelines (size targets, maxTurns, profile selection)
**Lines:** ~120-160
**Dependencies:** None — purely additive
**Backward compat:** Full

### Change 2: Two-Level Agent Selection [CRITICAL] **(v2)**

**Target:** CLAUDE.md §6
**What:** Level 1 Category Selection table + reference to catalog for Level 2
**Lines:** ~15-20 (compact table + catalog reference)
**Dependencies:** Change 1 (catalog provides Level 2)
**Backward compat:** Full — additive guidance

### Change 3: Category-Based Phase Pipeline Table [HIGH] **(v2)**

**Target:** CLAUDE.md §2
**What:** Replace individual agent names with category references
**Lines:** ~15L changed
**Dependencies:** Change 1 (categories defined in catalog)
**Backward compat:** Full — descriptive, not enforcement

### Change 4: Skill Category Templates [HIGH] **(v2)**

**Target:** Skills that spawn agents (brainstorming-pipeline, execution-plan, verification-pipeline)
**What:** Add per-category directive templates alongside existing per-agent templates.
Skills reference categories, Lead fills in specific agent from catalog.
**Lines:** ~20-40L per skill (3 skills = ~60-120L total)
**Dependencies:** Change 1 (categories), specific agent .md files
**Backward compat:** Full — existing per-agent templates continue working

### Change 5: Batch Spawn + Graduated Verification [HIGH] **(v2 NEW)**

**Target:** CLAUDE.md §6
**What:** Pattern for spawning N same-category agents with graduated verification
(1 full + N-1 light) and batch handoff between phases
**Lines:** ~25-30
**Dependencies:** None
**Backward compat:** Full — optimization, not behavior change

### Change 6: Agent-Common-Protocol Team Memory Fix [MEDIUM]

**Target:** `.claude/references/agent-common-protocol.md` §5
**What:** Replace hardcoded agent names with tool-based guidance
**Lines:** ~5L changed
**Dependencies:** None
**Backward compat:** Full

### Change 7: RTD Category Metadata [MEDIUM]

**Target:** RTD template in skills' Cross-Cutting Requirements
**What:** Add AGENT_TYPE and AGENT_CATEGORY fields to DP entry template
**Lines:** ~7L across 7 skills
**Dependencies:** Change 1 (category definitions)
**Backward compat:** Full — optional fields

### Total Effort Summary (Revised)

| Priority | Changes | Total Lines | New Files |
|----------|---------|-------------|-----------|
| CRITICAL | 2 | ~140-180 | 1 (agent-catalog.md) |
| HIGH | 3 | ~100-165 | 0 |
| MEDIUM | 2 | ~12 | 0 |
| LOW | 0 (D5, D8 are docs only) | ~10 | 0 |
| **Total** | **7** | **~260-370** | **1** |

---

## 5. Agent Selection Mechanism (Two-Level, for §6 + Catalog)

### Level 1: Category Selection (CLAUDE.md §6)

```
### Agent Category Selection

When assigning work, classify the task into a category:

| Task Nature | Category | Key Indicator |
|-------------|----------|---------------|
| Explore, discover, synthesize | Research | Open-ended question, unknown territory |
| Verify claims vs. external source | Verification | Specific claims, authoritative source |
| Design architecture or system | Design | Components, interfaces, ADRs needed |
| Challenge/critique a design | Validation | Existing design needs review |
| Write or modify code | Implementation | Code changes within ownership |
| Write tests, run test suites | Testing | Acceptance criteria to verify |
| Merge cross-boundary code | Integration | Multiple outputs to reconcile |

Pipeline phase overrides: In an active phase, §2 is authoritative.
Multiple agents needed? Use Batch Spawn pattern (§6 below).
Specific agent selection: consult agent-catalog.md for the chosen category.
No registered agent fits? Use closest category + focused directive.
If reused 3+ times, propose registration via architect directive.
```

### Level 2: Category Drill-Down (agent-catalog.md, per category)

Example for Verification category:

```
## Verification Category

Agents that validate claims against authoritative external sources.

### Tool Profile: Base + Web Access + Document Writing

### Members
| Agent | Focus | When to Use |
|-------|-------|-------------|
| verifier | General claims (any domain) | Single-domain, no sub-specialization needed |
| verifier-static | Schema (ObjectType, Property, Struct) | Ontology static components |
| verifier-relational | Relationships (LinkType, Interface) | Ontology relational components |
| verifier-behavioral | Actions (ActionType, Function, Rules) | Ontology behavioral components |

### Multi-Agent Composition
Parallel verification: spawn one per domain partition.
Evidence: 3 parallel verifiers completed in ~40% time of 1 serial verifier.

### Directive Template
[DIRECTIVE] Phase 2b: Verify {COMPONENT_LIST} from {LOCAL_DOC_FILES}
against official documentation at {SOURCE_BASE_URL}.
Components in scope: {names}
Known risk areas: {priority claims}
Write output to: {directory}
```

### Registered vs. Ad-Hoc Decision

```
Does a registered agent in the catalog match?
├── YES → Use it
│   Benefits: standardized L1/L2 schema, shorter directive, consistent methodology
└── NO → Use closest category agent + focused directive
    Document the directive pattern in Team Memory.
    If directive is reused 3+ times → propose new agent registration.
    Registration threshold: methodology is stable AND output format should be standardized.
```

---

## 6. Context Budget Projection (Revised for Fine-Grained Agents)

### Per-Spawn Cost Model (Revised)

| Component | Current (66-84L agent) | Fine-Grained (30-60L agent) |
|-----------|----------------------|----------------------------|
| Agent .md | ~1,200 tokens | **~600-900 tokens** |
| agent-common-protocol.md | ~1,600 tokens | ~1,600 tokens (unchanged) |
| Lead's directive | 60-300 tokens | 40-150 tokens (category template) |
| PERMANENT Task | ~800 tokens | ~800 tokens |
| **Total per spawn** | **~3,660-3,900** | **~3,040-3,450** |

Fine-grained agents are **~15-20% cheaper per spawn** than current agents.

### Scaling Analysis (Revised)

| Agent Count | Avg .md Size | Per-Spawn | Lead Selection | Category Count |
|-------------|-------------|-----------|----------------|----------------|
| 6 (current) | 78L | 3,800 tok | Trivial | 6 (1:1) |
| 10 | 60L | 3,400 tok | Low (catalog) | 7 |
| 15 | 45L | 3,200 tok | Low (catalog) | 7 |
| 20 | 40L | 3,100 tok | Low (catalog) | 7 |

**Key insight:** More agents = LOWER per-spawn cost + SAME selection overhead (7 categories
regardless of agent count). The category system converts O(N) selection into O(7) + O(M)
where M = agents per category (typically 2-5).

### Lead Context Budget

- CLAUDE.md: ~206L → ~225L (+Category Selection table)
- agent-catalog.md: ~120-160L (read on-demand, not always loaded)
- Permanent cost increase: ~20L in CLAUDE.md = ~300 tokens. Acceptable.

### BUG-002 Risk

UNAFFECTED. Fine-grained agents use FEWER turns (focused tasks, smaller .md).
BUG-002 risk may actually DECREASE.

---

## 7. Meta-Analysis: infra-analyst Registration Assessment (D11)

### Revised Verdict: KEEP AS DIRECTIVE TEMPLATE

The fine-grained agent update STRENGTHENS the case against registration:

1. **1-Agent:1-Responsibility test.** "INFRA gap analysis" is NOT a single responsibility
   — it combines exploration (researcher), design evaluation (architect), cross-referencing
   (RSIL-like). It's a COMPOSED task, not an atomic responsibility.

2. **No stable methodology.** Each INFRA gap analysis has different dimensions. This one
   had D1-D11; the next might focus on hook architecture or skill optimization. A fixed
   agent .md can't encode "any INFRA analysis methodology."

3. **Frequency is low.** ~5 out of 7 INFRA changes needed gap analysis, but INFRA changes
   are becoming less frequent as the framework stabilizes.

4. **No pipeline phase.** Meta-agents without phases don't fit the 1-Agent:1-Responsibility
   model — they're COMPOSITIONS, not atoms.

5. **Researcher + directive template works.** This session proved it. The specific INFRA
   knowledge was in Lead's directive (D1-D11 dimensions, file list, analysis structure).

**Alternative:** Store the D1-D11 framework as a reusable directive template in Team Memory
or a reference doc. When Lead needs INFRA gap analysis, use: `researcher + INFRA directive
template + specific scaling target`.

---

## 8. Implementation Roadmap (Revised)

### Phase 1: Foundation — Agent Catalog + Selection (do first)

| # | Change | Effort | Files |
|---|--------|--------|-------|
| C1 | Agent Catalog with Category System | 120-160L | NEW: `.claude/references/agent-catalog.md` |
| C2 | Two-Level Agent Selection | 15-20L | `.claude/CLAUDE.md` §6 |
| C6 | Protocol Team Memory fix | 5L | `.claude/references/agent-common-protocol.md` |

**Dependencies:** None — all additive.
**Impact:** Lead has two-level selection, protocol supports new tool combos.
**Must do BEFORE registering new agents** — catalog is the canonical registry.

### Phase 2: Pipeline Evolution (after catalog + first new agents registered)

| # | Change | Effort | Files |
|---|--------|--------|-------|
| C3 | Category-Based Phase Pipeline Table | 15L | `.claude/CLAUDE.md` §2 |
| C4 | Skill Category Templates | 60-120L | 3 skill SKILL.md files |
| C5 | Batch Spawn + Graduated Verification | 25-30L | `.claude/CLAUDE.md` §6 |

**Dependencies:** C1 (catalog defines categories), at least 1 new agent registered.
**Impact:** Pipeline supports many-to-many phase:agent. Skills work with categories.

### Phase 3: Polish (after 10+ agents in practice)

| # | Change | Effort | Files |
|---|--------|--------|-------|
| C7 | RTD Category Metadata | ~7L | 7 skill SKILL.md files |

**Dependencies:** C1 (category definitions).
**Impact:** Full observability across all agent categories.

### Timeline

```
NOW ─── Phase 1 ──── Phase 2 ──── Phase 3
        (catalog +    (pipeline +   (RTD polish)
         selection)    skills)
        ~145-185L     ~100-165L     ~7L
        2 new files   3 updates     7 updates
```

### Critical Path

```
C1 (Catalog) ──→ C3 (§2 Table)
              ├─→ C4 (Skill Templates)
              ├─→ C7 (RTD Metadata)
              └─→ [New Agent Registration]

C2 (Selection) ──→ C5 (Batch Spawn)

C6 (Protocol) ──→ (independent, do anytime)
```

### Backward Compatibility

ALL changes are backward-compatible:
- Existing 6 agents: continue working. Catalog lists them under their categories.
- Existing 10 skills: continue working. Category templates are ADDITIONS to existing
  per-agent templates.
- No hook changes (AD-15 inviolable)
- No settings.json changes
- No existing behavioral changes

---

## Appendix A: Evidence Cross-Reference

| Finding | Source File | Line(s) | Evidence |
|---------|-----------|---------|---------|
| Skills hardcode agent types (string) | brainstorming-pipeline/SKILL.md | 322-325, 396-400 | `subagent_type: "researcher"`, `subagent_type: "architect"` |
| Skills hardcode agent types (string) | execution-plan/SKILL.md | 189-193 | `subagent_type: "implementer"` |
| Skills hardcode agent types (string) | verification-pipeline/SKILL.md | 168-173, 292-297 | `subagent_type: "tester"`, `subagent_type: "integrator"` |
| Skills hardcode methodology (semantic) | brainstorming-pipeline/SKILL.md | 344 | "Researchers work with: Read, Glob, Grep, WebSearch, WebFetch..." |
| Skills hardcode methodology (semantic) | verification-pipeline/SKILL.md | 189 | "Use context7 to verify testing framework APIs" |
| Skills hardcode methodology (semantic) | execution-plan/SKILL.md | 211 | "Execute tasks in topological order within their component" |
| No agent manifest | CLAUDE.md §2, agents/*.md | 17-30, all | Only §2 table + filesystem |
| Protocol hardcodes agent names | agent-common-protocol.md §5 | 54-57 | "implementer, integrator" and "researcher, architect, tester" |
| SubagentStart captures type | on-subagent-start.sh | 12-14, 33-38 | `agent_type` → session-registry.json |
| Pre-Spawn lacks selection | CLAUDE.md §6 | 79-84 | "Evaluate three concerns" (none about agent choice) |
| Verifier token savings | agent-catalog-design.md §2.7 | 327-342 | 310→60 tokens per directive |
| L1 schema inconsistency | agent-catalog-design.md §1.4 | 169-183 | 3 different schemas across 3 verifiers |
| Fine-grained outperforms coarse | agent-catalog-design.md §1.4 | 169-183 | 3 verifiers: 3 different L1 schemas = evidence of ad-hoc inconsistency |
| 3 parallel verifiers pattern | Lead's scaling update | — | Parallel execution + deeper focus + cleaner output |

## Appendix B: v1 → v2 Revision Summary

| Dimension | v1 Priority | v2 Priority | What Changed |
|-----------|-------------|-------------|-------------|
| D1 | HIGH | **CRITICAL** | 20 agents = discovery impossible without catalog |
| D2 | HIGH | HIGH | Category-based table (not just multi-agent) |
| D3 | MEDIUM | MEDIUM | No change |
| D4 | LOW | **MEDIUM** | Tool profiles needed at 20 agents |
| D5 | MEDIUM | **LOW** | Fine-grained agents = lower per-spawn cost |
| D6 | HIGH | HIGH | Added PQ-1 semantic coupling analysis |
| D7 | CRITICAL | CRITICAL | Two-level selection (not just flat tree) |
| D8 | LOW | LOW | No change |
| D9 | MEDIUM | **HIGH** | N=6+ parallel agents needs batch verification |
| D10 | MEDIUM | MEDIUM | Added category metadata |
| D11 | — | — | Strengthened case against registration |

## Appendix C: Comparison with RSIL Coverage

| Analysis Dimension | RSIL | This Analysis | Overlap |
|------|---|---|---|
| NL consistency | YES (Lens 1-2) | NO | None |
| Scaling architecture | NO | YES (D1-D10) | None |
| Context budget | PARTIAL | YES (§6) | Minimal |
| Agent selection | NO | YES (D7, §5) | None |
| Skill-agent coupling | NO | YES (D6) | None |
| Cross-agent coordination | NO | YES (D9) | None |
| Category system design | NO | YES (D1, D2) | None |
| Implementation roadmap | NO | YES (§8) | None |

RSIL and infra-analyst are complementary, not overlapping.

---

## Appendix D: Five-Dimension Decomposition Addendum (v2.1)

**Context:** Lead's directive to decompose analysis agents across 5 dimensions:
Static, Behavioral, Relational, Dynamic-Impact, Real-Time.

**Note on Scale:** v2 already models 15-20+ fine-grained agents. This addendum extends
the analysis to cover monitoring/operational agents and their INFRA requirements.

---

### D-1. Five-Dimension Decomposition of infra-analyst

The monolithic "infra-analyst" (researcher + directive) decomposes into 5 specialized roles:

| Dim | Agent Name | What It Does | Current D1-D10 Coverage | Layer 1 Feasible? |
|-----|-----------|-------------|------------------------|-------------------|
| STATIC | infra-static | Config consistency, reference integrity, schema compliance | D1, D4 (partial) | **YES** — Read + Grep cross-reference |
| BEHAVIORAL | infra-behavioral | Lifecycle correctness, permission audit, protocol compliance | D3, D8 | **PARTIAL** — Rule audit YES, runtime audit needs events.jsonl |
| RELATIONAL | infra-relational | Dependency mapping, coupling detection, interface contracts | D6, D9 | **YES** — Grep cross-refs + NL dependency graphs |
| DYNAMIC-IMPACT | infra-dynamic-impact | Ripple analysis BEFORE changes, cascade prediction, backward compat | D5 (partial), whole report is one-shot impact | **PARTIAL** — Manual trace YES, automated cascade NO |
| REAL-TIME | infra-realtime | Pipeline execution monitoring, drift detection, budget tracking | D10 (partial) | **LIMITED** — On-demand reads YES, streaming NO |

#### Layer 1 vs Layer 2 Assessment Per Dimension

**STATIC (Layer 1 = SUFFICIENT)**
- Method: Read all .claude/ files → Grep for cross-references → report inconsistencies
- Tools: Read, Glob, Grep, sequential-thinking (all available to researcher)
- Evidence: This session's D1 analysis (filesystem discovery), D4 analysis (tool permission
  consistency) are purely static. Researcher + directive template handles this.
- Layer 2 need: None. NL cross-reference is adequate at 20 agents.

**BEHAVIORAL (Layer 1 = SUFFICIENT for rules, INSUFFICIENT for runtime)**
- Layer 1 method: Read .md files → verify protocol rules → check YAML frontmatter compliance
- Layer 1 evidence: D3 (protocol hardcodes names), D8 (lifecycle maxTurns) are rule-level
  behavioral analysis. Fully achievable with file reads.
- Layer 2 gap: Runtime behavior verification ("did agent X actually follow protocol during
  execution?") requires parsing events.jsonl, correlating timestamps, detecting sequence
  violations. Shell-based analysis is possible but fragile.
- Mitigation: events.jsonl + simple grep patterns cover 80% of runtime checks. Full
  behavioral verification (state machine compliance) needs Layer 2.

**RELATIONAL (Layer 1 = SUFFICIENT)**
- Method: Grep for agent references across all files → build dependency map → detect coupling
- Tools: Grep (regex patterns like `subagent_type:`, agent names in NL), Read, sequential-thinking
- Evidence: D6 analysis (5 hardcoded references across 3 skills) was built entirely via Grep.
- Layer 2 need: None. NL dependency maps scale to 20 agents. Formal graph queries would
  help at 50+ agents but are unnecessary at the 15-20 scale.

**DYNAMIC-IMPACT (Layer 1 = PARTIAL — User Priority #1)**
- Layer 1 method: Read agent-catalog.md's skill coupling map → manually trace "if I change X,
  what references X?" → list affected files with estimated change scope
- Layer 1 evidence: This entire report IS a dynamic-impact analysis ("what breaks at 20 agents").
  But it's manual, one-shot, Lead-directed.
- Layer 1 approximation: agent-catalog.md (C1) includes a "skill coupling map" — Lead reads
  it before approving changes. Combined with D7's decision tree, Lead gets a manual
  impact-assessment workflow.
- Layer 2 gap: AUTOMATED cascade prediction ("add verifier-static.md" → automatically lists
  all affected skills, CLAUDE.md sections, hooks, and estimated change lines). This needs
  a structured dependency graph or at minimum a machine-readable cross-reference index.
- **Transition path:**
  1. NOW: Manual lookup via catalog's coupling map (Layer 1)
  2. NEXT: Cross-reference index in catalog (structured YAML, still Layer 1)
  3. FUTURE: Formal dependency graph with query engine (Layer 2)

**REAL-TIME (Layer 1 = LIMITED — User Priority #2)**
- Layer 1 method: On-demand researcher reads events.jsonl + rtd-index.md + L1/L2 files →
  reports current pipeline state, flags anomalies
- Layer 1 limitation: Not truly "real-time" — it's batch analysis triggered by Lead.
  Between checks, drift goes undetected.
- Layer 1 approximation (best available):
  - PostToolUse hook already captures events.jsonl (async, no performance impact)
  - Add simple pattern detection to hook: "if two agents write to same file → alert"
  - Lead periodically spawns an on-demand monitor agent for state checks
  - This gives ~80% of monitoring value with zero INFRA structural changes
- Layer 2 gap: Continuous monitoring (long-running agent pattern), streaming event
  processing, automated threshold alerts (context budget > 80% → warn), conflict
  detection (parallel file edits → block).
- **Transition path:**
  1. NOW: Hook-based alerts + on-demand monitor (Layer 1)
  2. NEXT: Short-burst monitor pattern — spawn, check, report, shutdown (Layer 1+)
  3. FUTURE: Long-running parallel monitor agent (Layer 2, needs cross-cutting phase model)

---

### D-2. INFRA Support for Monitoring Agents

Monitoring agents (dynamic-impact, real-time) differ fundamentally from work agents:
they run ALONGSIDE work agents, not in sequential phases.

#### Three Patterns Evaluated

**Pattern A: Parallel Teammate (Long-Running Monitor)**
```
Pipeline Start ──────────────────────────────────────── Pipeline End
  │ Phase 2  │  Phase 3  │  Phase 4  │   Phase 6   │  Phase 7  │
  │ research │ architect │  design   │ implementer │  tester   │
  ├──────────┴───────────┴───────────┴─────────────┴───────────┤
  │        realtime-monitor (continuous, read-only)             │
  └─────────────────────────────────────────────────────────────┘
```
- Spawned at pipeline start, runs through phases 2-8
- Reads events.jsonl, rtd-index.md, L1/L2 periodically
- Flags anomalies to Lead via SendMessage
- **Pros:** Continuous coverage, catches drift in real-time
- **Cons:** Permanent teammate slot, context accumulation over long sessions,
  maxTurns must be high (200+?), context compaction risk (BUG-002)
- **Layer:** 2 — Long-running agent is a new execution model for Agent Teams
- **INFRA impact:** D2 needs "Cross-Cutting" phase model, D5 needs monitor budget

**Pattern B: On-Demand (Lead-Triggered Bursts)**
```
Phase 2 ──→ [monitor burst] ──→ Gate 2 ──→ Phase 3 ──→ [monitor burst] ──→ Gate 3
```
- Lead spawns monitor before gate decisions or when suspicious
- Agent analyzes state, reports, shuts down
- **Pros:** Fresh context each time, no accumulation, no BUG-002 risk
- **Cons:** Not truly real-time, depends on Lead remembering to invoke
- **Layer:** 1 — Just a specialized researcher with a monitoring directive
- **INFRA impact:** Minimal — new entry in agent-catalog.md under Operations category

**Pattern C: Hook-Based (Event-Driven Alerts)**
```
PostToolUse fires ──→ pattern check ──→ if anomaly → write .alert file
                                      → Lead reads alerts at gate checks
```
- Extend existing PostToolUse hook with pattern detection
- Examples: same-file concurrent edits, tool call rate spike, error rate threshold
- **Pros:** Truly real-time, zero agent context cost, automatic, no AD-15 violation
  (extending existing hook, not creating new one)
- **Cons:** Limited analysis capability (shell logic), false positives, maintenance burden
- **Layer:** 1 (simple patterns), 2 (complex patterns)
- **INFRA impact:** ~20-30L added to on-rtd-post-tool.sh

#### Recommended Hybrid Strategy

| Timeframe | Dynamic-Impact | Real-Time | Layer |
|-----------|---------------|-----------|-------|
| NOW | Manual catalog lookup | Hook alerts + on-demand burst | 1 |
| NEXT | Researcher + impact directive + YAML cross-ref index | Short-burst monitor pattern (spawn→check→report→shutdown) | 1+ |
| FUTURE | Registered agent + dependency graph | Long-running parallel monitor | 2 |

**Key INFRA changes for monitoring support:**

1. **New Category: "Operations"** in agent-catalog.md (~15-20L)
   Agents that manage the pipeline itself (not the work product).
   Members: infra-dynamic-impact, infra-realtime-monitor, future ops agents.
   This changes 7 categories → 8.

2. **Cross-Cutting Section in §2** (~5-10L)
   Below the main phase table:
   ```
   ### Cross-Cutting Agents (optional, run alongside phases)
   | Category | When | Pattern | Layer |
   |----------|------|---------|-------|
   | Operations (monitor) | Phases 2-8 | On-demand burst or hook-based | 1 |
   | Operations (impact) | Before gate approvals | On-demand burst | 1 |
   ```

3. **Monitor Communication Rule** in agent-common-protocol.md (~3-5L)
   Monitoring agents have READ access to all files but ONLY send messages to Lead.
   They do NOT contact work agents directly.

---

### D-3. Impact on Existing D1-D10 Findings

The 5-dimension lens affects 5 of the 10 existing dimensions:

| Dimension | Original Priority | Addendum Impact | Revised? |
|-----------|------------------|-----------------|----------|
| D1 | CRITICAL | +1 category (Operations, ~15-20L). 7→8 categories. | YES — scope grows slightly |
| D2 | HIGH | Needs "Cross-Cutting" concept for monitoring agents (~5-10L). Sequential phases + parallel monitors. | YES — new phase model concept |
| D5 | LOW | If Pattern A (long-running monitor) adopted, context budget needs monitoring agent cost. On-demand (Pattern B) has no impact. | CONDITIONAL — only if Layer 2 adopted |
| D7 | CRITICAL | Dynamic-impact agent assists Lead's decisions. Decision tree gets: "Before approving → consult impact agent." | YES — enhancement, not structural change |
| D9 | HIGH | Monitor needs read-only access to work agents' files without disruption. Filesystem-as-shared-state handles this. New rule: monitors → Lead only. | YES — new communication rule |
| D3, D4, D6, D8, D10 | various | No change from 5-dimension analysis | NO |

**Net impact on implementation roadmap:**
- Phase 1 (Foundation): C1 grows by ~15-20L (Operations category). C2 unchanged.
- Phase 2 (Pipeline): Add Cross-Cutting section to §2 (~5-10L). C5 (Batch Spawn) unchanged.
- NEW Phase 1.5: If dynamic-impact agent methodology stabilizes, register it.
- Total additional lines: ~25-35L across catalog and CLAUDE.md.

---

### D-4. D11 Revision: Five-Dimension Registration Assessment

Original verdict (monolithic): DO NOT REGISTER infra-analyst.

**With 5-dimension decomposition:**

| Dimension | Agent | 1-Resp? | Methodology Stable? | Frequency | Phase? | Verdict |
|-----------|-------|---------|--------------------|-----------|---------|---------|
| STATIC | infra-static | YES | YES (Read+Grep cross-ref) | LOW (~15% of INFRA work) | None | **DO NOT REGISTER** — researcher + directive |
| BEHAVIORAL | infra-behavioral | YES | PARTIAL (rules YES, runtime PARTIAL) | LOW | None | **DO NOT REGISTER** — researcher + directive |
| RELATIONAL | infra-relational | YES | YES (Grep dependency map) | LOW | None | **DO NOT REGISTER** — researcher + directive |
| DYNAMIC-IMPACT | infra-dynamic-impact | YES | **EMERGING** (new capability) | **POTENTIALLY HIGH** | Pre-gate | **DEFER** — register after 3+ uses if methodology stabilizes |
| REAL-TIME | infra-realtime | YES | **EMERGING** (new capability) | **HIGH** (every pipeline) | Cross-cutting | **DEFER** — register after cross-cutting pattern established |

**Key insight:** The decomposition reveals that 3/5 dimensions (static, behavioral,
relational) are genuinely low-frequency and don't warrant registration. But 2/5
(dynamic-impact, real-time) — precisely the user's top priorities — have HIGH frequency
potential and unique value. They SHOULD eventually be registered, but the methodology
and INFRA patterns need to stabilize first.

**Registration criteria for deferred agents:**
- Dynamic-impact: Register when the catalog's cross-reference map has been used 3+ times
  for manual impact analysis AND the analysis pattern is consistent enough to encode in
  a 30-60L .md file.
- Real-time: Register when the cross-cutting agent pattern (§2 addendum) has been validated
  in 2+ pipeline runs AND the monitoring directive is stable.

**Revised D11 verdict:** PARTIAL REGISTRATION POTENTIAL. 3/5 DO NOT REGISTER.
2/5 DEFER with specific registration triggers. This is a SIGNIFICANT revision from
the original blanket "DO NOT REGISTER."

---

### D-5. Paradigm Shift Summary

| Aspect | Current (Lead-Managed) | Future (Agent-Managed) | Transition |
|--------|----------------------|----------------------|------------|
| Config audit | Lead reads files | infra-static agent | Directive template (Layer 1) |
| Permission check | Lead reviews YAML | infra-behavioral agent | Directive template (Layer 1) |
| Dependency tracking | Lead traces refs | infra-relational agent | Directive template (Layer 1) |
| Impact prediction | Lead's judgment | infra-dynamic-impact agent | Catalog cross-ref → YAML index → graph (L1→L2) |
| Execution monitoring | Lead reads rtd-index | infra-realtime agent | Hook alerts → burst monitor → long-running (L1→L2) |

The user's insight is correct: the shift is from "write rules and manually enforce"
to "deploy specialized agents that actively manage." The 5-dimension decomposition
provides the framework. The Layer 1/Layer 2 boundary provides the implementation
timeline. Dynamic-impact and real-time are the highest-leverage dimensions because
they represent genuinely NEW capabilities that no existing agent or manual process
covers well.
