# Decision 003: How Lead Discovers and Routes to Skills

**Status:** PENDING USER DECISION  
**Date:** 2026-02-11  
**Context:** CLAUDE.md v6.0 · 10 Skills · Skill YAML frontmatter · Claude Code CLI Skill System  
**Depends on:** Decision 001 (Pipeline Routing), Decision 002 (Skills vs Agents)

---

## 1. Problem Statement

Does the Lead Agent discover and select Skills **solely from YAML frontmatter `description` fields**? Or are there other discovery mechanisms? If the description is the only signal, is it sufficient?

---

## 2. Skill Discovery Mechanisms — Complete Audit

### 2.1 How Claude Code CLI Discovers Skills

The Claude Code CLI discovers Skills via the filesystem: `.claude/skills/*/SKILL.md`. Each Skill file has YAML frontmatter containing:

```yaml
---
name: skill-name
description: "Multi-line description of what the skill does"
argument-hint: "[optional: what arguments to pass]"
---
```

**The CLI presents Skills to the Lead as slash commands** (e.g., `/brainstorming-pipeline`, `/delivery-pipeline`). The frontmatter `description` is what the Lead (and the user) sees when listing available commands.

### 2.2 What Signals Does the Lead Currently Have?

| Signal | Source | What It Provides | Lead Access |
|--------|--------|-------------------|-------------|
| **Skill `description`** | YAML frontmatter | 1-3 line summary of purpose | ✅ Automatic (CLI presents) |
| **CLAUDE.md §2** | Constitution | "Phase-agent mapping defined in Custom Agents Reference table" | ✅ Always loaded |
| **CLAUDE.md Line 94** | Constitution | "/rsil-global" mentioned explicitly | ✅ Always loaded |
| **CLAUDE.md Line 335** | Constitution | "/permanent-tasks skill (mid-work updates)" mentioned | ✅ Always loaded |
| **agent-catalog.md Line 183** | Reference | "Core (spawned by pipeline skills directly)" | ✅ On-demand read |
| **Skill `name` field** | YAML frontmatter | Slash command name | ✅ Automatic |
| **Skill `argument-hint`** | YAML frontmatter | Expected arguments pattern | ✅ Automatic |
| **Skill body (full SKILL.md)** | Markdown body | Complete orchestration logic | ❌ Only after explicit `/skill-name` invocation |

### 2.3 Critical Gap: Skills Are NOT Referenced by Name in CLAUDE.md

**CLAUDE.md does NOT contain a Skill index.** The only Skill references are:

1. Line 94: `Lead invokes /rsil-global for INFRA health assessment` — names ONE Skill
2. Line 335: `/permanent-tasks skill (mid-work updates)` — names ONE Skill

**The remaining 8 Skills are NEVER mentioned by name in CLAUDE.md:**
- `/brainstorming-pipeline` — NOT referenced
- `/agent-teams-write-plan` — NOT referenced
- `/plan-validation-pipeline` — NOT referenced
- `/agent-teams-execution-plan` — NOT referenced
- `/verification-pipeline` — NOT referenced
- `/delivery-pipeline` — NOT referenced
- `/rsil-review` — NOT referenced
- `/palantir-dev` — NOT referenced

### 2.4 What This Means

The Lead knows:
- **WHAT** the Phase Pipeline is (CLAUDE.md §2 — phases, agents, gates)
- **WHO** to spawn (CLAUDE.md §Custom Agents Reference — 27 agents)
- **WHEN** to spawn (agent-catalog.md — Decision Triggers)

The Lead does **NOT** know from CLAUDE.md:
- **HOW** to orchestrate a specific phase (that's in the Skill body)
- **WHICH Skill** covers which Phase(s)
- **WHETHER** a Skill should be invoked vs. Lead improvising

---

## 3. Discovery Models

### 3.1 Current Model: User-Initiated + Description-Only

```
User types /brainstorming-pipeline
    │
    ↓
CLI loads SKILL.md file → Lead reads full body
    │
    ↓
Lead executes orchestration logic from Skill body
```

**Lead does NOT self-select Skills.** The user (or CLAUDE.md explicit instruction for /rsil-global) initiates Skill invocation.

### 3.2 Gap: No Self-Selection Mechanism

If the user types a natural language prompt like "Research and implement feature X", the Lead has:
1. CLAUDE.md §2: "pipeline flows PRE → EXEC → POST"
2. agent-catalog.md: "WHEN to Spawn" table
3. **NO mapping** from "Research and implement feature X" → "Start with `/brainstorming-pipeline`"

The Lead would need to either:
- **A.** Know the Skill-Phase mapping from memory/context
- **B.** Improvise using CLAUDE.md §2 + agent-catalog.md (no Skill, Lead constructs its own orchestration)
- **C.** Be told by the user which Skill to invoke

Currently: **Option C is the operational reality.** Users manually invoke Skills.

---

## 4. Analysis

### 4.1 Is Description-Only Sufficient?

**For user-initiated invocation: YES.** The user reads the Skill name (which is descriptive: `brainstorming-pipeline`, `delivery-pipeline`) and invokes it. The description field provides enough context for the user to decide.

**For Lead self-selection: NO.** The Lead cannot:
- List available Skills programmatically during pipeline execution
- Map a natural language request to the correct Skill
- Determine the optimal Skill sequence for a given task complexity

### 4.2 Frontmatter Description Quality Audit

| Skill | Description Quality | Routing Signal Strength |
|-------|--------------------|-----------------------|
| `permanent-tasks` | "Single source of truth for pipeline requirements" — CLEAR | HIGH |
| `brainstorming-pipeline` | Not shown in audit (marked for enhancement) | — |
| `agent-teams-write-plan` | Not shown in audit | MEDIUM |
| `agent-teams-execution-plan` | Describes Phase 6 orchestration | HIGH |
| `plan-validation-pipeline` | Not shown in audit | MEDIUM |
| `verification-pipeline` | Describes Phases 7-8 | HIGH |
| `delivery-pipeline` | Describes Phase 9 terminal delivery | HIGH |
| `rsil-global` | Very detailed, includes "auto-invoked by Lead" | HIGHEST |
| `rsil-review` | Very detailed, includes "Lead-only, no teammates" | HIGH |
| `palantir-dev` | Korean description, educational focus | HIGH (for its domain) |

---

## 5. Options

### Option A: Status Quo (User-Initiated Only)

No changes. Users manually invoke Skills. Lead does not self-select.

**Pros:** Simple, no INFRA changes needed.  
**Cons:** Lead cannot autonomously orchestrate full pipeline. User must know Skill→Phase mapping.

### Option B: Add Skill Index to CLAUDE.md

Add a **Skill Reference Table** to CLAUDE.md mapping Skills to Phases:

```markdown
## Skill Reference

| Skill | Phases | When to Invoke |
|-------|--------|----------------|
| `/permanent-tasks` | P0 | Pipeline start or mid-work PT update |
| `/brainstorming-pipeline` | P0-P3 | New feature requiring research + architecture |
| `/agent-teams-write-plan` | P4 | Architecture complete, need implementation plan |
| `/plan-validation-pipeline` | P5 | Implementation plan ready for critique |
| `/agent-teams-execution-plan` | P6 | Plan validated, ready for implementation |
| `/verification-pipeline` | P7-P8 | Implementation complete, testing needed |
| `/delivery-pipeline` | P9 | All gates passed, commit and archive |
| `/rsil-global` | Post-pipeline | After P9 or .claude/ changes (auto-invoked) |
| `/rsil-review` | On-demand | Deep INFRA quality review (user-initiated) |
| `/palantir-dev` | N/A | Programming language learning (user-initiated) |
```

**Pros:**
- Lead can self-select appropriate Skill based on current Phase
- Enables future auto-chaining or pipeline automation
- Single source of truth for Skill→Phase mapping
- Low implementation cost (add ~15 lines to CLAUDE.md)

**Cons:**
- Risk of Lead auto-invoking Skills when user expects manual control
- Skill→Phase mapping becomes a maintained artifact (can go stale)
- Does NOT solve the fundamental question of whether Lead should auto-chain

### Option C: Add Skill Index + Auto-Selection Directive

Option B plus an explicit instruction for Lead to self-select Skills:

```markdown
When the user provides a natural language task (not a slash command):
1. Classify task complexity (Decision 001 tier)
2. Select appropriate Skill(s) from the Skill Reference table
3. Present selected pipeline to user for approval before invoking
4. Execute approved Skill sequence
```

**Pros:** Full autonomy for Lead pipeline construction.  
**Cons:** Conflicts with "no auto-chaining" principle in current Skills. Requires updating all Skills to allow Lead-initiated invocation.

### Option D: Add Skill Index + Recommendation-Only

Option B plus a passive recommendation directive:

```markdown
When the user provides a natural language task (not a slash command):
1. Classify task complexity
2. Recommend the appropriate Skill sequence from the Skill Reference table
3. Present recommendation to user — user decides whether to invoke
```

**Pros:** Lead provides guidance without overstepping. User retains control.  
**Cons:** Extra conversation turn for every request.

---

## 6. Recommendation

**Option B (Add Skill Index to CLAUDE.md)** as the minimum viable change.

**Rationale:**
1. The Lead currently has NO awareness of which Skills exist beyond `/rsil-global` and `/permanent-tasks`
2. A Skill Reference Table makes the Skill→Phase mapping explicit and discoverable
3. It does NOT force auto-chaining (preserves current user-initiated model)
4. It enables future upgrade to Option C or D without restructuring
5. It solves Decision 002's point that Skills are "orchestration playbooks" — the index makes this relationship visible to Lead

**If Decision 001 selects Option B (Tiered Fixed Pipelines):** The Skill Index becomes essential because complexity tiers need to map to Skill sequences. Without the index, Lead cannot determine which Skills to skip for TRIVIAL/SIMPLE tiers.

---

## 7. User Decision Items

- [ ] **Option A** — Status Quo (user-initiated only, no Skill index)
- [ ] **Option B** — Add Skill Index to CLAUDE.md (RECOMMENDED)
- [ ] **Option C** — Skill Index + Lead auto-selection
- [ ] **Option D** — Skill Index + recommendation-only

### Sub-decisions (if Option B/C/D selected):

- [ ] Should the Skill Index include "When to Invoke" criteria? (Yes/No)
- [ ] Should Lead be allowed to recommend Skills to the user? (Yes/No)
- [ ] Should the Skill Index reference Decision 001 tiers? (Depends on D-001 outcome)

---

## 8. Claude Code Directive (Fill after decision)

```
DECISION: Option [A/B/C/D]
SCOPE:
  - CLAUDE.md: Add Skill Reference Table after §2 Phase Pipeline
  - If Option C/D: Add routing directive to §2
CONSTRAINTS:
  - Current Skill "no auto-chaining" principle preserved unless Option C selected
  - All Skill files unchanged (index is a CLAUDE.md addition only)
  - English only (Opus 4.6)
PRIORITY: Discoverability > Autonomy > Simplicity
DEPENDS_ON: Decision 001 (tier classification determines Skill sequence)
```
