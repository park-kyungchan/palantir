# Decision 009: Agent Memory Architecture

**Status:** PENDING USER DECISION  
**Date:** 2026-02-11  
**Context:** CLAUDE.md v6.0 · 27 agents (→42 with D-005) · D-007 BN-005  
**Depends on:** Decision 005, Decision 007

---

## 1. Problem Statement

Agents have persistent memory at `~/.claude/agent-memory/{role}/MEMORY.md`.
With D-005 expanding to 42 agents, the memory architecture faces these challenges:

1. **Fragmentation:** 42 individual MEMORY.md files, many sparse or empty
2. **No cross-agent learning:** What `structure-architect` discovers about the codebase
   is invisible to `interface-architect` unless both happen to record the same finding
3. **Cold start penalty:** New D-005 agents start with zero memory — no accumulated wisdom
4. **Memory quality varies:** Some agents accumulate actionable patterns, others store
   session-specific noise despite protocol prohibiting it
5. **Read cost:** Lead or coordinator reading 42 MEMORY.md files for context is impractical

**Core question:** What memory granularity maximizes cross-agent learning while
preserving role-specific specialization?

---

## 2. Current State

### 2.1 Memory Protocol (from `agent-common-protocol.md` §Agent Memory)

```
Check: ~/.claude/agent-memory/{role}/MEMORY.md
Operations: Read-Merge-Write (read current, merge new, write back)

What to save:
  - Patterns confirmed across multiple tasks (not one-off observations)
  - Key file paths and conventions for your role
  - Solutions to recurring problems
  - Lessons learned from review feedback

What NOT to save:
  - Session-specific context (current task details, temporary state)
  - Anything that duplicates protocol or agent .md instructions
```

### 2.2 Current Memory Files (if any exist)

With 27 agents, up to 27 MEMORY.md files could exist:
```
~/.claude/agent-memory/
  architect/MEMORY.md
  codebase-researcher/MEMORY.md
  external-researcher/MEMORY.md
  implementer/MEMORY.md
  ... (up to 27)
```

### 2.3 Category Structure (Current 10 → 13 with D-005)

| Category | Current Agents | D-005 Agents | Memory Sharing Opportunity |
|----------|:---------:|:--------:|-------------|
| Research | 3 (coordinator + 2 workers) | 3 (no change) | HIGH — all read same codebase |
| Verification | 4 (coordinator + 3 workers) | 5 (add impact-verifier) | HIGH — all verify same claims |
| Architecture | 1 (architect) | **4** (coordinator + 3) | **VERY HIGH** — all analyze same system |
| Planning | 1 (plan-writer) | **4** (coordinator + 3) | **VERY HIGH** — all plan same system |
| Validation | 1 (devils-advocate) | **4** (coordinator + 3) | **VERY HIGH** — all challenge same plan |
| Implementation | 2 (coordinator + implementer) | 2 (no change) | LOW — file ownership isolates work |
| Review | 2 (spec + code reviewer) | **4** (add contract + regression) | HIGH — all review same code |
| Testing | 3 (coordinator + tester + integrator) | **4-6** (split tester) | HIGH — all test same code |
| Monitoring | 1 (execution-monitor) | 1 (no change) | N/A — single agent |
| INFRA Quality | 5 (coordinator + 4 analysts) | 5 (no change) | HIGH — all analyze .claude/ |
| P2d Impact | 1 (impact-verifier) | 0 (merged to Verification) | N/A |
| Dynamic Impact | 1 (dynamic-impact-analyst) | 1 (no change) | N/A — single agent |
| INFRA Impl | 1 (infra-implementer) | 1 (no change) | N/A — single agent |

---

## 3. Analysis: Memory Granularity Options

### 3.1 Option A: Per-Agent Memory (Current)

```
~/.claude/agent-memory/
  structure-architect/MEMORY.md
  interface-architect/MEMORY.md
  risk-architect/MEMORY.md
  architecture-coordinator/MEMORY.md
  ... (42 files)
```

**Pros:**
- Maximum role specialization — each agent builds expertise in its specific dimension
- No merge conflicts between agents
- Zero read overhead (agent only reads its own file)

**Cons:**
- No cross-agent learning within category
- 42 files, many will be empty or sparse
- Cold start for all D-005 new agents
- `structure-architect` discovers "this codebase uses monorepo pattern" but
  `interface-architect` doesn't know this on next run

### 3.2 Option B: Category-Level Memory

```
~/.claude/agent-memory/
  architecture/MEMORY.md     ← shared by structure/interface/risk-architect + coordinator
  planning/MEMORY.md         ← shared by decomposition/interface/strategy-planner + coordinator
  validation/MEMORY.md       ← shared by correctness/completeness/robustness-challenger + coordinator
  research/MEMORY.md         ← shared by codebase-researcher + external-researcher + coordinator
  verification/MEMORY.md     ← shared by 3-4 verifiers + coordinator
  review/MEMORY.md           ← shared by spec/code/contract/regression-reviewer
  testing/MEMORY.md          ← shared by unit/contract/regression-tester + coordinator
  implementation/MEMORY.md   ← shared by implementer + coordinator
  infra-quality/MEMORY.md    ← shared by 4 analysts + coordinator
  monitoring/MEMORY.md       ← execution-monitor only (singleton)
  dynamic-impact/MEMORY.md   ← dynamic-impact-analyst only (singleton)
  infra-impl/MEMORY.md       ← infra-implementer only (singleton)
  delivery/MEMORY.md         ← Lead-only phase (singleton)
```

**13 files instead of 42.**

**Pros:**
- Cross-agent learning within category (structure-architect's "monorepo" finding
  visible to interface-architect)
- Fewer files, denser information
- New agents inherit category memory immediately
- Coordinator can curate category memory

**Cons:**
- Merge conflicts when 2+ agents write simultaneously (Read-Merge-Write race condition)
- Role-specific patterns may be drowned by category-general patterns
- Agent must distinguish "my patterns" from "sibling's patterns"

### 3.3 Option C: Hierarchical Memory (Category + Role)

```
~/.claude/agent-memory/
  architecture/
    SHARED.md                ← category-wide patterns (read by all category members)
    structure-architect.md   ← role-specific patterns
    interface-architect.md   ← role-specific patterns
    risk-architect.md        ← role-specific patterns
    coordinator.md           ← coordination patterns
  planning/
    SHARED.md
    decomposition-planner.md
    interface-planner.md
    strategy-planner.md
    coordinator.md
  ... (same pattern for all categories)
```

**Protocol:**
```
On start:  Read SHARED.md + my-role.md
On finish: Write to my-role.md (role-specific patterns)
           Propose additions to SHARED.md (via coordinator or Lead)
```

**Pros:**
- Best of both — cross-agent learning + role specialization
- No merge conflicts (each agent writes to its own file)
- SHARED.md is curated (not free-for-all writes)
- Clear separation of concerns

**Cons:**
- More files (13 SHARED + 42 role = 55 files, though most role files will be small)
- SHARED.md curation requires a process (who writes to it?)
- More complex protocol in agent-common-protocol.md
- Increased read cost on start (2 files instead of 1)

### 3.4 Option D: Category Memory + Tagging (Recommended)

```
~/.claude/agent-memory/
  architecture/MEMORY.md
  planning/MEMORY.md
  ... (13 files, same as Option B)
```

**But with structured content:**
```markdown
# Architecture Category Memory

## Shared Patterns
These patterns apply to ALL architecture agents.
- [2026-02-10] This codebase uses monorepo with package-based isolation
- [2026-02-11] Primary API pattern: REST with OpenAPI specs in /docs/

## Structure-Specific
Patterns specific to structural analysis.
- [2026-02-11] Config files are YAML, not JSON
- [2026-02-11] Naming convention: kebab-case for files, PascalCase for classes

## Interface-Specific  
Patterns specific to interface analysis.
- [2026-02-10] All modules export named functions, no default exports

## Risk-Specific
Patterns specific to risk analysis.
- [2026-02-11] No error handling in data pipeline — recurring risk

## Coordinator Notes
Cross-dimension synthesis observations.
- [2026-02-11] Structure decisions affect interface design — always verify alignment
```

**Protocol:**
```
On start:  Read category MEMORY.md (full file)
On finish: 
  1. Read current MEMORY.md (for merge)
  2. Add entries to "Shared Patterns" if cross-agent applicable
  3. Add entries to own "{Role}-Specific" section
  4. Write back (Read-Merge-Write)
```

**Pros:**
- Single file per category — simple like Option B
- Role-specific sections prevent drowning — like Option C
- New agents see ALL accumulated knowledge on first run
- Coordinator can curate during synthesis phase
- Tags with dates enable staleness detection

**Cons:**
- Merge conflict risk (same as Option B) — mitigated by section-based writes
- File grows large over time (needs periodic curation)
- Agents must be disciplined about section boundaries

---

## 4. Merge Conflict Mitigation

The primary risk of shared memory (Options B, C, D) is simultaneous writes.

### 4.1 Current Situation
In Agent Teams, agents within a category can run concurrently (e.g., 3 architecture workers).
If all 3 finish simultaneously and try Read-Merge-Write on the same file, the last writer wins.

### 4.2 Mitigation Strategies

| Strategy | Layer | Effectiveness | Complexity |
|----------|-------|---------------|-----------|
| **Coordinator-mediated writes** | L1 | HIGH | LOW |
| File locking with `flock` | L1 | MEDIUM | MEDIUM |
| Append-only writes (no merge) | L1 | HIGH | LOW |
| Ontology ObjectType (atomics) | L2 | VERY HIGH | HIGH |

**Recommended: Coordinator-mediated writes**

Since every D-005 category has a coordinator, the protocol becomes:
```
Worker finishes → reports memory findings to coordinator via SendMessage
Coordinator consolidates → writes to category MEMORY.md once
Workers never write to MEMORY.md directly
```

**For singleton agents (no coordinator):** Traditional Read-Merge-Write (no conflict
because only 1 agent writes).

**For Lead-direct agents (no coordinator but concurrent):** Append-only model — agents
append to their own section using `## {role}` anchor (already in agent-common-protocol
for TEAM-MEMORY.md).

---

## 5. Cold Start Strategy for D-005 New Agents

When D-005 agents are first created, they have zero memory. Options:

### 5.1 Seed from Existing Agent Memory
- `structure-architect` → seed from `architect/MEMORY.md` (structural patterns)
- `interface-architect` → seed from `architect/MEMORY.md` (interface patterns)
- `risk-architect` → seed from `architect/MEMORY.md` (risk patterns)
- `decomposition-planner` → seed from `plan-writer/MEMORY.md`
- `correctness-challenger` → seed from `devils-advocate/MEMORY.md`

**Process:** When creating D-005 agents, if predecessor memory exists:
1. Read predecessor MEMORY.md
2. Classify each entry into new category/role section
3. Write as initial category MEMORY.md

### 5.2 Start Fresh
New agents start with empty memory. They accumulate naturally over pipeline runs.

**Recommendation:** Seed from existing (§5.1) where predecessors exist. Start fresh for
entirely new roles (contract-reviewer, regression-reviewer, contract-tester).

---

## 6. Memory Lifecycle

### 6.1 Staleness Detection

Memory entries should have dates. Entries older than N sessions can be flagged for review:
```markdown
- [2026-01-15] ~~This codebase uses Express.js~~ ← STALE (codebase migrated to Fastify)
- [2026-02-11] This codebase uses Fastify
```

**Who curates?** The coordinator during post-phase synthesis, or INFRA Quality during RSIL review.

### 6.2 Memory Size Limit

To prevent unbounded growth:
- Each category MEMORY.md should target ≤100 lines
- When exceeding: coordinator merges redundant entries, removes stale entries
- Maximum read cost: 100 lines × 13 categories = 1300 lines (unreachable in practice —
  agent only reads its own category)

---

## 7. Options Summary

| Aspect | A: Per-Agent | B: Category | C: Hierarchical | **D: Category+Tags** |
|--------|:---:|:---:|:---:|:---:|
| Files | 42 | 13 | 55 | **13** |
| Cross-learning | ❌ | ✅ | ✅ | **✅** |
| Role separation | ✅ | ❌ | ✅ | **✅** (via sections) |
| Cold start | ❌ | ✅ | ✅ | **✅** |
| Merge safety | ✅ | ❌ | ✅ | **✅** (coordinator-mediated) |
| Protocol complexity | LOW | LOW | HIGH | **MEDIUM** |
| Coordinator curation | N/A | Possible | Required | **Natural** |
| L2 migration path | Complex | Simple | Complex | **Simple** (1 ObjectType/category) |

---

## 8. Interaction with Other Decisions

| Decision | Interaction |
|----------|------------|
| D-005 (Agent Decomposition) | Memory architecture must accommodate 42 agents across 13 categories |
| D-007 (BN-005) | This decision directly resolves BN-005 |
| D-011 (Handoff Protocol) | Memory feeds into cross-phase handoff (accumulated patterns inform next phase) |
| D-013 (Coordinator Protocol) | Memory write delegation becomes part of coordinator shared protocol |
| D-016 (CLAUDE.md Redesign) | agent-common-protocol §Agent Memory needs update |
| Future L2 | `ObjectType: CategoryKnowledge` maps to category MEMORY.md |

---

## 9. User Decision Items

- [ ] Which option? (A / B / C / **D recommended**)
- [ ] Accept coordinator-mediated writes for merge safety?
- [ ] Accept 13-category structure per §3.4?
- [ ] Seed from existing agent memory (§5.1) or start fresh (§5.2)?
- [ ] Accept 100-line soft limit per category?
- [ ] Accept date-tagged entries for staleness detection?

---

## 10. Claude Code Directive (Fill after decision)

```
DECISION: Agent memory architecture — Option [X]
SCOPE:
  - agent-common-protocol.md §Agent Memory: update memory path and protocol
  - Memory structure: ~/.claude/agent-memory/{category}/MEMORY.md
  - Sections: Shared Patterns / {Role}-Specific / Coordinator Notes
  - Write protocol: coordinator-mediated for coordinated categories, direct for singletons
  - Seed: migrate existing agent memory to category structure
CONSTRAINTS:
  - Read-Merge-Write preserved for singletons
  - Coordinator-mediated for concurrent category members
  - 100-line soft limit per category
  - Date-tagged entries
  - No memory writes during active phase work (only at completion)
PRIORITY: Cross-agent learning > Role specialization > File count reduction
DEPENDS_ON: D-005 (agent count), D-013 (coordinator protocol)
```
