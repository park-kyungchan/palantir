# Decision 007: Bottleneck Analysis & Opus-4.6 / Layer-2 Boundary Definition

**Status:** PENDING USER DECISION  
**Date:** 2026-02-11  
**Context:** CLAUDE.md v6.0 · Opus-4.6 · Agent Teams · Palantir Ontology/Foundry Layer-2  
**Depends on:** Decision 005, Decision 006

---

## 1. Problem Statement

Identify all bottlenecks and inefficiencies in the current INFRA, with explicit boundary definitions for:
1. **What Opus-4.6 + Agent Teams can handle (Layer-1)**
2. **What requires Palantir Ontology/Foundry (Layer-2)**
3. **What is ambiguous and needs explicit boundary assignment**

---

## 2. Opus-4.6 Characteristics Relevant to Agent Teams

### 2.1 Strengths (Exploit These in L1)

| Characteristic | Impact on Agent Teams |
|---------------|----------------------|
| **200K context window** | Agents can read entire codebases, plans, and multi-file cross-references without external memory |
| **High NL instruction fidelity** | Complex orchestration rules (CLAUDE.md, Skills, agent-common-protocol) are followed reliably |
| **Multi-step reasoning** | Impact analysis, cascade prediction, architectural risk assessment — all achievable in-context |
| **Long-form output** | L1/L2/L3 files can be comprehensive without artificial truncation |
| **Tool chaining** | Agents can perform Glob→Grep→Read→Write chains without explicit state machines |
| **Intent inference** | Lead can construct directives from minimal input; agents infer what downstream consumers need |

### 2.2 Limitations (These Define L2 Boundary)

| Limitation | Impact on Agent Teams | Layer-2 Requirement |
|-----------|----------------------|---------------------|
| **No persistent memory across sessions** | Agent loses all context on session compact. Recovery depends on L1/L2 files + PERMANENT Task | L2: Persistent object store (Ontology ObjectType per agent session) |
| **No sub-second reactivity** | Polling model only (1-2 min intervals). Cannot detect file conflicts in real-time | L2: Event bus with push notification (ActionType trigger) |
| **No guaranteed exhaustive traversal** | Grep patterns may miss references. Impact analysis is best-effort (~90%) | L2: Formal dependency graph (LinkType traversal with Search Around) |
| **No schema enforcement at creation time** | Agent `.md` files can have wrong frontmatter, missing fields, wrong tool lists | L2: ValueTypeConstraint on ObjectType properties |
| **No cross-agent state sharing** | Agents share state only via files (L1/L2) or messaging (SendMessage) | L2: Shared ObjectType instances (real-time updates) |
| **Context window is finite** | 42-agent catalog + Skills + references may exceed comfortable read-budget for Lead | L2: Ontology search (find agents by phase/dimension without reading full catalog) |
| **No atomic multi-file operations** | Agent edits files sequentially — race conditions possible with parallel agents | L2: ActionType with transactional edits |

### 2.3 Agent Teams Characteristics

| Property | Current State | Impact |
|----------|--------------|--------|
| **Max 1 team per session** | Cannot have nested teams or multi-team coordination | Lead must orchestrate ALL phases in one team lifecycle |
| **No nested teammates** | Workers cannot spawn sub-workers | Coordinators manage workers but workers cannot delegate further |
| **Team-scoped Task API** | Tasks visible within team only | PERMANENT Task may not be accessible if scoped wrong (ISS-003) |
| **SendMessage is fire-and-forget** | No delivery guarantee, no acknowledgment protocol | Messages can be lost if recipient compacts |
| **No teammate re-spawn on crash** | Crashed teammates must be re-created by Lead | Lead must detect crashes (via monitoring or silence) |
| **File ownership is NL-enforced** | No structural prevention of cross-boundary writes | Ownership violations detected post-hoc by execution-monitor |

---

## 3. Identified Bottlenecks

### BN-001: Lead Context Saturation (CRITICAL)

**Current:** Lead reads CLAUDE.md (~340 lines) + agent-catalog.md Level 1 (~300 lines) + PERMANENT Task + phase status + agent L1/L2 outputs.

**With D-005:** Lead needs to manage 42 agents across 13 categories with 8 coordinators. The routing table grows significantly. Lead's context for a COMPLEX-tier pipeline execution approaches:
- CLAUDE.md: ~400 lines (post D-001/D-003 updates)
- agent-catalog Level 1: ~600 lines (post D-005)
- Active Skill: ~300-600 lines
- PERMANENT Task: ~200 lines
- Active agent L1/L2 outputs: ~200-400 lines per agent
- **Total: 2000-4000+ lines just for orchestration context**

**Impact:** Lead may truncate or skip reading lower-priority contexts, leading to suboptimal routing decisions or forgotten agents.

**Boundary Assignment:**
| Solution | Layer | Effectiveness |
|----------|-------|---------------|
| Compress CLAUDE.md routing tables | L1 | Medium — reduces readiness but not zero |
| Two-phase catalog read (L1 quick → L2 detail) | L1 | High — already designed but under-enforced |
| Ontology query: "Find agents for Phase 3 with STATIC dimension" | **L2** | **Very High — eliminates manual catalog scanning** |

**Recommendation:** 
- **L1 now:** Enforce strict Level 1/2 catalog separation (F-010 from D-006). Add Skill Index (D-003).
- **L2 later:** `SearchAround(phase=3, dimension="STATIC")` → returns `structure-architect` directly

---

### BN-002: Coordinator Spawn Overhead (HIGH)

**Current:** For a coordinated category, Lead spawns: 1 coordinator + N workers = N+1 agent creations.

**With D-005:** Phase 3 alone requires: 1 architecture-coordinator + 3 architects = 4 agents. Phases 3+4+5 combined: 12 agents + 3 coordinators = 15 spawns before any implementation begins.

**Token cost of spawning:**
```
Per agent spawn:
  - Lead constructs directive (read PT + read plan + read Impact Map + construct NL) ≈ 2000 tokens
  - Agent reads PERMANENT Task + agent-common-protocol ≈ 1500 tokens  
  - Understanding verification exchange ≈ 500 tokens
  - Total per spawn: ~4000 tokens

15 PRE spawns × 4000 tokens = 60,000 tokens just for spawning PRE-phase agents
```

**Impact:** This is NOT a concern per the user's Shift-Left philosophy ("토큰소비 고려하지말고"). But it's a TIME bottleneck — sequential spawning creates a wall-clock delay.

**Boundary Assignment:**
| Solution | Layer | Effectiveness |
|----------|-------|---------------|
| Parallel pre-spawn all workers before coordinator sends assignments | L1 | High — workers spawn in parallel, then coordinator distributes |
| Batch spawn directive template (coordinator + workers in one call) | **L2** | **Very High — reduces spawn to single orchestrated action** |

**Recommendation:**
- **L1 now:** Ensure Skills pre-spawn workers in parallel (already done in `agent-teams-execution-plan`). Apply pattern to new P3/P4/P5 Skills.
- **L2 later:** `ActionType: SpawnTeam` — single action that creates coordinator + workers atomically

---

### BN-003: Cross-Phase Context Handoff (HIGH)

**Current:** Phase N output → Lead reads L1/L2 → Lead constructs Phase N+1 directive → Lead spawns next agents.

**Problem:** Lead is the single point of context transfer. If Lead's context window is under pressure:
1. Lead may not read ALL of Phase N's L1/L2/L3 output
2. Lead may construct incomplete Phase N+1 directives
3. Downstream agents receive degraded context

**With D-005:** The handoff surface area increases:
- P3 architecture-coordinator produces consolidated L2 from 3 architects
- Lead must read this L2, interpret it, and construct P4 planning-coordinator directive
- P4 planning-coordinator produces consolidated L2 from 3 planners
- Lead must read this L2 and construct P5 validation-coordinator directive
- Each handoff is a potential information loss point

**Boundary Assignment:**
| Solution | Layer | Effectiveness |
|----------|-------|---------------|
| Standardized L2 format with mandatory "Downstream Handoff" section | L1 | Medium — reduces interpretation burden |
| PERMANENT Task as persistent context (already exists) | L1 | High — PT survives across phases |
| Ontology ObjectType: `PhaseOutput` with typed properties consumed by next phase | **L2** | **Very High — formal contract between phases** |

**Recommendation:**
- **L1 now:** Add "Downstream Handoff" mandatory section to coordinator L2 output format. Include: key decisions, unresolved items, interface contracts, risk warnings.
- **L2 later:** `ObjectType: PhaseOutput` → `LinkType: HandoffTo(Phase N+1)` → formal typed handoff

---

### BN-004: Gate Evaluation Consistency (MEDIUM)

**Current:** Gates are NL-evaluated by Lead. Each Skill defines gate criteria differently. No standard gate evaluation procedure.

**Examples of inconsistency:**
- `brainstorming-pipeline` Gate 2: "Research sufficient?"
- `agent-teams-execution-plan` Gate 6: "All tasks PASS both review stages?"
- `verification-pipeline` Gate 7: "All acceptance criteria covered?"

**Problem:** Lead applies different rigor to different gates depending on context pressure. A TRIVIAL feature's Gate 2 may receive 10% of the scrutiny of a COMPLEX feature's.

**Boundary Assignment:**
| Solution | Layer | Effectiveness |
|----------|-------|---------------|
| Standardized gate checklist with minimum evidence requirements | L1 | High — reusable across all gates |
| Gate severity tiers (PASS/CONDITIONAL_PASS/FAIL) already exist | L1 | Already done (in plan-validation) |
| SubmissionCriteria on `ActionType: PassGate` — formal validation before gate passes | **L2** | **Very High — prevents premature gate passage** |

**Recommendation:**
- **L1 now:** Create `.claude/references/gate-evaluation-standard.md` with minimum checklist per gate.
- **L2 later:** `ActionType: PassGate` with `SubmissionCriteria` requiring minimum evidence count

---

### BN-005: Agent Memory Fragmentation (MEDIUM)

**Current:** Agent memory at `~/.claude/agent-memory/{role}/MEMORY.md` — agents are instructed to read-merge-write.

**With D-005:** 42 agents × individual memory files = 42 potential memory files. Some agents may never accumulate enough runs to build useful memory. Others (like `implementer`) may have very rich memory.

**Problem:** No cross-agent knowledge sharing. What `structure-architect` learns about codebase patterns is not accessible to `interface-architect` unless both read the same MEMORY.md.

**Boundary Assignment:**
| Solution | Layer | Effectiveness |
|----------|-------|---------------|
| Shared category-level memory (e.g., `architecture-category/MEMORY.md`) | L1 | Medium — requires merge discipline |
| Read-only access to sibling agent memory | L1 | Low — increases context load |
| Ontology ObjectType: `AgentKnowledge` shared across category | **L2** | **High — queryable, category-scoped** |

**Recommendation:**
- **L1 now:** Define memory at CATEGORY level, not agent level. `~/.claude/agent-memory/architecture/MEMORY.md` shared by all 3 architects + coordinator. Read-merge-write per agent.
- **L2 later:** `ObjectType: CategoryKnowledge` with per-agent annotations via `LinkType: ContributedBy`

---

### BN-006: No Rollback or Undo Mechanism (MEDIUM)

**Current:** If Phase 6 implementation is partially completed and Gate 7 fails, there's no automated rollback. Lead must manually coordinate reversal or re-assign.

**Boundary Assignment:**
| Solution | Layer | Effectiveness |
|----------|-------|---------------|
| Git-based checkpoints at each gate passage | L1 | High — `git stash` or branch per phase |
| Skill-level rollback instructions | L1 | Medium — manual but documented |
| ActionType: `RollbackPhase` with automated file restoration | **L2** | **Very High — formal undo** |

**Recommendation:**
- **L1 now:** Add git checkpoint instruction to delivery-pipeline Skill. Lead creates a branch or tag at each gate passage.
- **L2 later:** `ActionType: RollbackPhase` → reverts all file changes since last gate

---

### BN-007: Silent Skill Failure (LOW)

**Current:** If a Skill encounters an error mid-execution, there's no guaranteed notification. Lead continues with potentially corrupted state.

**Boundary Assignment:** L1 — Add explicit error handling sections to all Skills. Ensure every Skill terminates with either SUCCESS or FAIL signal.

---

## 4. Opus-4.6 / Layer-2 Boundary Definition

### 4.1 Definitive Boundary Table

| Capability | Layer | Rationale |
|-----------|-------|-----------|
| Agent definition and role assignment | **L1** | NL + YAML frontmatter sufficient |
| Pipeline phase ordering | **L1** | CLAUDE.md + Skills sufficient |
| Agent spawning and directive construction | **L1** | Opus-4.6 NL strength |
| Understanding verification | **L1** | NL exchange via SendMessage |
| Gate evaluation | **L1** | NL checklist + Lead judgment |
| L1/L2/L3 output production | **L1** | Write tool + NL format |
| File ownership enforcement | **L1** | NL instruction (monitor detects violations) |
| Cross-phase context handoff | **L1** (now), **L2** (future) | L1 via PT + L2, L2 via typed PhaseOutput |
| Dependency graph traversal | **L2** | Grep insufficient for guaranteed completeness |
| Schema validation at creation time | **L2** | No L1 mechanism to prevent invalid agent definitions |
| Real-time event streaming | **L2** | Polling is best L1 can do |
| Cross-agent state sharing | **L2** | No L1 mechanism beyond files + messaging |
| Rollback and undo | **L1** (git), **L2** (formal) | Git checkpoints for L1, ActionType for L2 |
| Agent catalog query by property | **L2** | Reading 600+ line catalog is inefficient |
| Memory sharing across categories | **L1** (file), **L2** (queryable) | File-based sharing for L1, Ontology for L2 |
| Batch agent spawning | **L2** | L1 spawns sequentially |

### 4.2 The "Gray Zone" — Items That COULD BE Either Layer

| Item | L1 Approach | L2 Approach | Recommendation |
|------|------------|------------|----------------|
| Gate evidence collection | Lead reads agent L1/L2 manually | `SearchAround: PhaseOutput.evidence` | **Start L1, migrate to L2 when stable** |
| Pipeline tier classification (D-001) | Lead reads request, classifies using CLAUDE.md criteria | `ActionType: ClassifyRequest` with rule-based branching | **L1 now, L2 when tiers are proven** |
| Agent competency matching | Lead reads catalog, matches phase + dimension | `SearchAround: AgentDefinition WHERE phase=X AND dimension=Y` | **L1 now, L2 when catalog exceeds 50 agents** |
| Cross-coordinator communication | Via Lead relay (current) | Direct `LinkType: CoordinatorHandoff` | **L1 now, L2 if parallel phases needed** |

### 4.3 Anti-Patterns to Avoid in L2 Design

From `ontology-communication-protocol.md` §3:

| Anti-Pattern | Risk if Applied to Agent INFRA |
|-------------|-------------------------------|
| **OT-1 Over-Normalization** | Don't create separate ObjectTypes for every agent property. `tools` should be an Array, not linked ObjectTypes |
| **OT-2 Non-Deterministic PK** | Agent PKs must be stable: use `name` (e.g., "structure-architect"), not auto-generated IDs |
| **LT-2 Spiderweb** | Don't link every agent to every phase/skill/output. Use Interfaces for common patterns |
| **IF-3 Over-Abstraction** | Don't create Interfaces with only 1 implementor. Min 2 agents per Interface |
| **ACT-1 FUNCTION_RULE + Other** | `SpawnAgent` action: either rule-based OR function-backed, never mixed |

---

## 5. Summary: Priority-Ordered Action Items

### Immediate (L1 — This Session)
1. ✅ D-005 agent decomposition approved — proceed with implementation
2. Apply D-006 INFRA fixes (F-007, F-009, F-010, F-012, F-015)
3. Create gate-evaluation-standard.md reference
4. Enforce category-level agent memory (not per-agent)
5. Add "Downstream Handoff" section to coordinator output format

### Short-term (L1 — Next 2-3 Sessions)
6. Create D-005 agent `.md` files (12 workers + 3 coordinators)
7. Create D-005 Skills (architecture-orchestration, planning-orchestration, validation-orchestration)
8. Update existing Skills for new agent routing
9. Update CLAUDE.md with D-003 Skill Index + D-002 enforcement text
10. Stabilize: run 1-2 pipeline executions with new agents

### Medium-term (L2 Preparation)
11. Design L2 Ontology schema (ObjectType: AgentDefinition, SkillDefinition)
12. Define L2 sync direction (L2→L1 generation)
13. Implement L2 ObjectTypes for agent catalog
14. Implement L2 SearchAround for agent routing

### Long-term (L2 Overlay)
15. Implement L2 ActionTypes (SpawnTeam, PassGate, RollbackPhase)
16. Implement L2 event streaming for real-time monitoring
17. Replace NL gate evaluation with SubmissionCriteria validation
18. Full L2 dependency graph for impact analysis

---

## 6. User Decision Items

- [ ] Confirm Opus-4.6 / Layer-2 boundary as defined in §4.1?
- [ ] Confirm category-level agent memory instead of per-agent?
- [ ] Confirm "Downstream Handoff" section for coordinator output?
- [ ] Confirm gate-evaluation-standard.md creation?
- [ ] Confirm git checkpoint at each gate passage?
- [ ] Confirm L2 priority order: Catalog query → Dependency graph → Event streaming → ActionTypes?

---

## 7. Claude Code Directive (Fill after decision)

```
DECISION: Boundary confirmed, actions prioritized
SCOPE:
  L1 Immediate:
    - Apply D-006 INFRA fixes
    - Create gate-evaluation-standard.md
    - Implement category-level memory
    - Add Downstream Handoff to coordinator format
  L1 Short-term:
    - D-005 agent files + Skills
    - CLAUDE.md updates (D-002, D-003)
  L2 Preparation:
    - Ontology schema design (post L1 stabilization)
CONSTRAINTS:
  - AD-15 (no new hooks)
  - L2 work blocked until L1 stable (min 1 successful pipeline run)
  - L2 sync direction: decided at L2 design phase
  - Token consumption: unrestricted (Shift-Left investment)
PRIORITY: L1 stability > BN resolution > L2 preparation
DEPENDS_ON: D-005 (agent count determines L2 schema), D-006 (INFRA quality baseline)
```
