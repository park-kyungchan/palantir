# RTDI Codebase Assessment — Layer 1 Achievement & Layer 2 Gap Analysis

> **Purpose:** Comprehensive assessment of how far the Real-Time-Dynamic-Integration
> Codebase vision has been achieved through Layer 1 alone, what structural gaps remain,
> and how Layer 2 (Ontology Framework) addresses each gap. This document serves as a
> brainstorming topic for `/brainstorming-pipeline` to design the Layer 1 → Layer 2
> integration strategy.
>
> **Format:** English only. Machine-readable for Opus 4.6.
> **Date:** 2026-02-10
> **Companion doc:** `docs/plans/2026-02-08-ontology-bridge-handoff.md` (Ontology topics T-1~T-4)
> **Prerequisite reading:** This document first, then ontology-bridge-handoff for component details.

---

## 0. Document Relationships

```
This Document (RTDI Assessment)
├── WHY Layer 2 is needed (gap analysis with evidence)
├── WHAT Layer 2 must solve (structural requirements)
├── WHERE each gap maps to Ontology Components
│
└──→ ontology-bridge-handoff.md
     ├── HOW each Ontology Component is defined (T-1~T-4)
     ├── Reference doc inventory (9 Palantir docs, 5 bridge refs)
     └── Brainstorming session methodology
```

Other related artifacts:
- `MEMORY.md` → "Next Topics → Ontology Framework — Brainstorming Chain" section (index entry)
- `MEMORY.md` → "Current INFRA State (v7.0, 2026-02-10)" section (Layer 1 completion context)
- `docs/plans/2026-02-10-ontology-sequential-protocol.md` → Sequential calling protocol (T-0~T-4)
- `.claude/skills/rsil-review/SKILL.md` → Layer 1/2 boundary definitions (Static Layer)
- `.claude/skills/rsil-global/SKILL.md` → Category C DEFER items (Layer 2 evidence)
- `docs/plans/2026-02-08-narrow-rsil-tracker.md` → §6 Deferred Items (concrete L2 gaps)

---

## 1. What "Real-Time-Dynamic-Integration Codebase" Means

The RTDI Codebase is a self-documenting, self-improving, observable AI agent
orchestration framework written entirely in natural language. Each word in the
name describes a distinct architectural property.

### 1.1 Real-Time

The infrastructure observes, records, and reacts to events as they happen —
not retrospectively.

| Capability | Mechanism | Status |
|-----------|-----------|--------|
| Tool call capture | PostToolUse hook → events.jsonl (8-field JSONL, async) | DONE |
| Decision logging | rtd-index.md (WHO/WHAT/WHY/EVIDENCE/IMPACT/STATUS per DP) | DONE |
| State preservation | PreCompact hook → snapshot before context loss | DONE |
| Session recovery | SessionStart hook → RTD injection on resume | DONE |
| Agent attribution | session-registry.json (BUG-003: best-effort only) | PARTIAL |
| Live dashboard | Not implemented (events.jsonl exists but no consumer) | NOT DONE |
| Cross-session timeline | events.jsonl persists but no query/aggregation tool | NOT DONE |

**Defining characteristic:** An agent's actions are recorded at the moment they
occur, not reconstructed afterward. The temporal dimension is first-class data.

### 1.2 Dynamic

The infrastructure evolves, adapts, and self-improves rather than being static
configuration.

| Capability | Mechanism | Status |
|-----------|-----------|--------|
| Living requirements | PERMANENT Task Read-Merge-Write (PT-v{N}, monotonic) | DONE |
| Self-improvement loop | RSIL 8-Lens review → findings → apply → verify | DONE |
| Context-aware loading | Dynamic Context Injection (`!`shell`` in skills) | DONE |
| Adaptive verification | Understanding Verification (1-3 probing questions) | DONE |
| Adaptive parallelism | Spawn algorithm based on dependency graph analysis | DONE |
| Cross-session learning | RSIL agent memory (72 findings, 92% acceptance) | DONE |
| Per-agent memory | Only RSIL initialized; 6 agent types have empty memory | PARTIAL |
| Self-healing | RSIL observes+proposes but cannot auto-apply | NOT DONE |
| Predictive adaptation | No capability to anticipate failures before they occur | NOT DONE |

**Defining characteristic:** The infrastructure is not a static document tree —
it modifies itself through structured feedback loops. Each pipeline execution
potentially improves the infrastructure for the next one.

### 1.3 Integration

All components reference, validate, and depend on each other coherently.
No component exists in isolation.

| Capability | Mechanism | Status |
|-----------|-----------|--------|
| Dependency chain | CLAUDE.md → protocol → agents → skills → hooks → settings | DONE |
| Cross-file audit | RSIL Integration Audit (bidirectional consistency) | DONE |
| Phase gate system | Phase 0-9 with entry/exit conditions per phase | DONE |
| File ownership | Non-overlapping sets per implementer, integrator only crosses | DONE |
| Version alignment | v6.0 refs across 4 skills verified in E2E check | DONE |
| Ripple tracking | Codebase Impact Map in PERMANENT Task | DONE |
| RSIL coverage | S-1~S-4 complete (7/10 targets); S-5~S-7 pending | 70% |
| Formal contracts | NL assertion only (e.g., "section headers are interface contract") | NL ONLY |
| Schema validation | No mechanism to validate YAML/MD structure programmatically | NOT DONE |
| Dependency propagation | Manual ripple tracking; no automated cascade detection | NOT DONE |

**Defining characteristic:** Changing one file creates ripple effects that
propagate through the dependency chain. The system can detect some of these
ripples (RSIL audit) but cannot automatically trace or enforce all of them.

### 1.4 Codebase

The `.claude/` directory itself IS the codebase — natural language files that
function as executable specifications for AI agents.

| Analogy | Traditional Codebase | RTDI Codebase |
|---------|---------------------|---------------|
| Entry point | main.py | CLAUDE.md v7.0 (205L) |
| Class definitions | class files | 6 agent .md files (461L) |
| Functions | function definitions | 9 skills (4203L) |
| Event handlers | event listeners | 4 hooks (389L) |
| Configuration | config files | settings.json + frontmatter |
| API spec | OpenAPI/protobuf | task-api-guideline v6.0 (118L) |
| Shared interfaces | shared libraries | agent-common-protocol v3.0 (107L) |
| Test framework | test suite | RSIL 8-Lens system (549L + 452L) |
| CI/CD | pipeline config | Phase 0-9 gate system |
| Monitoring | observability stack | RTD 4-Layer system |
| Compiler | language compiler | Opus 4.6 (interprets NL instructions) |

**Total infrastructure size:** ~6,000 lines of markdown across ~30 files.

**Defining characteristic:** Natural Language as Programming Language. The
"compiler" (Opus 4.6) interprets nuanced multi-paragraph instructions with
high fidelity but without formal guarantees. This is the fundamental tension
that Layer 2 must resolve.

---

## 2. Layer 1 Achievement Assessment

### 2.1 Quantitative Summary

```
Infrastructure components:
  CLAUDE.md v7.0             205L   Root authority (§0-§10)
  agent-common-protocol v3.0 107L   Shared procedures
  task-api-guideline v6.0    118L   Task field requirements (78% reduced from v5.0)
  6 agent .md files          461L   Role-specific guidance + constraints
  9 skill .md files         4203L   Pipeline skills + RSIL + permanent-tasks
  4 hook scripts             389L   Lifecycle event handlers
  settings.json               ~80L   Configuration
  ─────────────────────────────────
  Total                    ~5563L   Layer 1 infrastructure

Observability:
  RTD System (4 layers)     ~360L   Created in INFRA v7.0 sprint
  events.jsonl               auto   PostToolUse captures all tool calls
  rtd-index.md               auto   Lead-maintained decision log
  session-registry.json      auto   Agent-to-session mapping

Quality system:
  RSIL reviews completed        9   (global: 1, narrow: 4, retroactive: 4)
  Cumulative findings          72   across all reviews
  Acceptance rate              92%  (66/72 accepted)
  Cross-cutting patterns        5   (P-1 through P-5, universally applicable)
  Lenses                        8   (L1 through L8, evolving)

Production usage:
  Full pipeline executions      3   COW v2.0, RTD system, INFRA v7.0 Integration
  Skills optimized              9   All with NLP v6.0 + Phase 0 + RTD template
  Commits (infra-only)        ~15   Since initial Agent Teams rebuild (2026-02-07)
```

### 2.2 Per-Dimension Scoring

| Dimension | Score | Justification |
|-----------|-------|---------------|
| **[R] Real-Time** | 85% | RTD 4-Layer complete. Agent attribution partial (BUG-003). No dashboard. |
| **[T] (reserved)** | — | — |
| **[D] Dynamic** | 80% | PT lifecycle + RSIL loop + DCI all working. Agent memory sparse. No self-healing. |
| **[I] Integration** | 75% | Dependency chain + gates + RSIL audit working. 70% RSIL coverage. No formal contracts. |
| **Codebase maturity** | 80% | NLP v6.0 complete. Version-controlled. 3 production runs. No automated validation. |
| **Overall** | **~70%** | Weighted: Layer 1 alone ~90% complete. Layer 2 at 0% drags overall to ~70%. |

### 2.3 What Layer 1 Does Well

**Self-referential quality loop.** RSIL observes infrastructure → discovers
patterns (P-1~P-5) → patterns applied to skills → results verified by RSIL.
72 findings at 92% acceptance demonstrates the system meaningfully improves itself.

**NL-as-Code paradigm works.** Opus 4.6 reliably executes 205 lines of
CLAUDE.md to orchestrate 6 agent types across a 9-phase pipeline. Results are
reproducible, version-controlled, and verifiable through gates.

**Observability is comprehensive.** Every tool call is captured (Layer 0),
every decision is logged (Layer 1), context is preserved across compaction
(Layer 2-3). Recovery from session interruption is functional.

**Pipeline architecture is mature.** Phase 0-9 with understanding verification,
file ownership isolation, two-stage review (spec + code), and graduated gates.
Three successful production runs validate the design.

---

## 3. Layer 1 Structural Limits — Where Layer 2 Is Needed

This section documents the specific gaps that Layer 1 cannot resolve, with
evidence from actual infrastructure operation. Each gap maps to an Ontology
Framework component from `ontology-bridge-handoff.md`.

### 3.1 NL Assertion Fragility

**Problem:** All integration contracts are expressed as natural language
assertions that Opus 4.6 must interpret correctly every time.

**Evidence from RSIL:**
- EP-1 (S-4 CRITICAL): V-3 referenced "§3 (File Ownership)" — but §3 is only
  valid for the current 10-section plan template. If the template evolves, V-3
  silently breaks. Fixed with semantic wording, but the fix is still NL.
- permanent-tasks SKILL.md declares "section headers are the interface contract
  for Phase 0 blocks" (line 201) — but no mechanism enforces this. If someone
  renames a header, Phase 0 silently fails to parse.
- task-api-guideline v6.0 §3 is referenced by 4 skills — but the reference is
  a string match, not a typed import. §3 could change without notifying consumers.

**What Layer 2 provides:**
- ObjectType schema with typed properties → section headers become typed fields
  that can be validated programmatically (→ T-1 ObjectType)
- Interface contracts → shared property shapes that enforce consistency across
  consumers (→ T-2 Interface)
- Preconditions on mutations → any change to a contracted section must pass
  validation before taking effect (→ T-3 ActionType Preconditions)

**Layer 2 gap category:** Formal interface contract verification beyond NL assertions.

### 3.2 Unstructured State Tracking

**Problem:** Pipeline state is scattered across multiple markdown files with
no unified query capability.

**Evidence from operation:**
- PERMANENT Task state (PT-v{N}) lives in Task API description field — queryable
  only by TaskGet on a specific ID, not by structured field queries.
- Orchestration-plan.md tracks teammate status, phase progress, and gate history
  in free-form markdown — no way to query "which phases are COMPLETE?" without
  reading and parsing the entire file.
- L1/L2/L3 artifacts are directories of files — no index beyond L1-index.yaml.
  Cross-task queries (e.g., "which tasks modified auth module?") require reading
  all L2 summaries.
- RSIL tracker uses markdown tables — 72 findings are human-readable but not
  machine-queryable. "Show me all L5 findings across all reviews" requires
  manual table scanning.

**What Layer 2 provides:**
- ObjectType instances with typed, queryable properties → PT becomes a typed
  object with status fields that support structured queries (→ T-1 ObjectType)
- LinkType relationships → "Phase → Task → Files" traversable as a graph
  instead of embedded text references (→ T-2 LinkType, Search Around)
- Storage + Query engine → YAML-on-disk with schema validation and graph
  traversal (→ T-4 Integration Architecture)

**Layer 2 gap category:** Structured state machines with formal transitions and queries.

### 3.3 Cross-Session Knowledge Fragmentation

**Problem:** Knowledge accumulated across sessions is preserved only in
unstructured markdown files with no relationship model.

**Evidence from operation:**
- MEMORY.md is a flat append-log (despite consolidation rules). Finding
  "what decisions affected hook design?" requires reading the entire file.
- RSIL agent memory tracks lens statistics but not finding relationships.
  "Which findings in S-4 were cascaded from S-1?" is answerable by reading
  the tracker, but not by querying the memory.
- infrastructure-history.md records major changes but has no formal link to
  the files that were actually modified. The "DIA evolution v1→v4" entry
  doesn't link to the specific commits or file versions.
- Team Memory (TEAM-MEMORY.md) is session-scoped and not linked to the
  cross-session MEMORY.md. Discoveries from one session don't automatically
  propagate to the next.

**What Layer 2 provides:**
- Cross-session knowledge graph → findings, decisions, patterns linked as
  ObjectType instances with LinkType relationships (→ T-1, T-2)
- Structured audit trails → each finding is an ObjectType with properties
  (lens, severity, status, target, session) queryable across all sessions
  (→ T-1 ObjectType)
- Version-linked artifacts → decisions linked to specific file versions
  and commits through typed relationships (→ T-2 LinkType)

**Layer 2 gap category:** Cross-session knowledge graphs with structured queries.

### 3.4 Validation Without Enforcement

**Problem:** RSIL discovers issues but cannot prevent them. All enforcement
is advisory.

**Evidence from RSIL data:**
- 72 findings discovered, 27 applied in the latest sprint alone. Each required
  manual Lead review → user approval → manual file editing. No automation.
- Category C (DEFER) items: P9-R7 (compact recovery state marker) was deferred
  because "requires persistent state across compaction" — this is exactly what
  a formal state machine would provide.
- P4-R4 (skill preload templates), P5-R4 (effort parameter per agent) were
  deferred because they require API-level or structured system support.
- The "Never" sections in skills (e.g., "Never create multiple [PERMANENT]
  tasks") are NL directives with no enforcement mechanism. An agent could
  violate them and no system would catch it.

**What Layer 2 provides:**
- Preconditions → "Never create multiple [PERMANENT] tasks" becomes a typed
  constraint that blocks the action before execution (→ T-3 Preconditions)
- Postconditions → "After gate approval, all L1/L2/L3 must exist" becomes
  an automated verification check (→ T-3 Postconditions)
- Schema validation → "Section headers must match exactly" becomes a YAML
  schema that rejects malformed documents at write time (→ T-4 Validation)

**Layer 2 gap category:** Constraint enforcement and automated validation.

### 3.5 Agent Attribution Gap

**Problem:** The RTD system cannot reliably attribute tool calls to specific
agents due to BUG-003 ($CLAUDE_SESSION_ID not available in hook contexts).

**Evidence:**
- GitHub issue #17188 OPEN. All events.jsonl entries fall back to "lead"
  attribution when session ID cannot be resolved.
- Workaround (AD-29): session-registry.json maps SubagentStart's parent SID
  to agent names, but this is best-effort and fails for nested spawns.
- Impact: observability data is partially blind to "who did what" — the
  temporal dimension (WHEN) is accurate but the agent dimension (WHO) is not.

**What Layer 2 provides:**
- Agent as ObjectType with formal identity → each agent instance has a typed
  ID that persists through its lifecycle (→ T-1 ObjectType)
- ActionType audit trail → every action records the agent ObjectType instance
  that performed it, not just a session ID string (→ T-3 ActionType)
- This gap may also resolve at Layer 1 level if Claude Code exposes
  $CLAUDE_SESSION_ID in future versions. Monitor GitHub #17188.

**Layer 2 gap category:** Structured audit trails with reliable agent attribution.

### 3.6 Ripple Detection Without Automation

**Problem:** The Codebase Impact Map tracks module dependencies manually, but
there's no automated mechanism to detect when a change in one file affects
dependent files.

**Evidence:**
- E2E verification required manual grep across all .claude/ files to verify
  cross-references. This took ~15 tool calls and produced useful results but
  is not repeatable without Lead effort.
- The RSIL Integration Audit is powerful but manual — Lead must define axes
  and Explore agent must read all file pairs. No persistent watcher.
- When task-api-guideline went from v5.0 to v6.0 (78% reduction), four skills
  needed v6.0 reference updates. This was discovered through RSIL audit, not
  through an automated dependency checker.

**What Layer 2 provides:**
- Module → Module LinkType with dependency semantics → changes to a file
  automatically surface all dependent files for review (→ T-2 LinkType)
- Automation triggers → "when file X changes, validate all files that
  reference X" (→ T-3/T-4 Automation, aligns with ontology_7.md)
- Constraint propagation engine → formal dependency analysis that traces
  ripple paths automatically (→ T-4 Integration Architecture)

**Layer 2 gap category:** Constraint propagation and automated dependency analysis.

---

## 4. Gap-to-Ontology Component Mapping

This section maps each Layer 1 gap to the specific Ontology Component that
addresses it, creating a direct bridge to `ontology-bridge-handoff.md` T-1~T-4.

### 4.1 Mapping Table

| # | Gap | Primary Ontology Component | Secondary | Bridge Doc Topic |
|---|-----|---------------------------|-----------|-----------------|
| 3.1 | NL Assertion Fragility | Interface (typed contracts) | ObjectType (schema) | T-1, T-2 |
| 3.2 | Unstructured State Tracking | ObjectType (typed state) | LinkType (graph queries) | T-1, T-2, T-4 |
| 3.3 | Knowledge Fragmentation | LinkType (knowledge graph) | ObjectType (findings as entities) | T-1, T-2 |
| 3.4 | Validation Without Enforcement | ActionType (Pre/Postconditions) | — | T-3 |
| 3.5 | Agent Attribution Gap | ObjectType (Agent identity) | ActionType (audit trail) | T-1, T-3 |
| 3.6 | Ripple Detection | LinkType (dependencies) | Automation (triggers) | T-2, T-4 |

### 4.2 Component Demand Analysis

```
T-1 (ObjectType): Referenced by ALL 6 gaps
  → Highest priority. Everything depends on typed entity definitions.
  → Must be designed first. Confirms ontology-bridge-handoff.md topic ordering.

T-2 (LinkType + Interface): Referenced by 5 of 6 gaps
  → Second priority. Relationships and contracts are the integration mechanism.
  → Directly addresses the "I" in RTDI.

T-3 (ActionType + Conditions): Referenced by 3 of 6 gaps
  → Third priority. Enforcement and audit are the "Dynamic" completers.
  → Directly addresses the "D" in RTDI.

T-4 (Integration Architecture): Referenced by 3 of 6 gaps
  → Fourth priority. Storage, query, and automation are runtime infrastructure.
  → Directly addresses the "R" in RTDI (real-time query capability).
```

### 4.3 Ontology Component → RTDI Dimension Mapping

```
                    R (Real-Time)   D (Dynamic)   I (Integration)
                    ─────────────   ───────────   ──────────────
T-1 ObjectType      ██░░░░ (state)  ██████ (typed) ██████ (schema)
T-2 LinkType        ██████ (graph)  ██░░░░        ██████ (contracts)
T-3 ActionType      ██████ (audit)  ██████ (enforce) ██░░░░
T-4 Integration     ██████ (query)  ██████ (auto)  ██████ (validate)
```

Each RTDI dimension needs all four Ontology Components, but with different
emphasis. T-1 and T-2 are integration-heavy; T-3 and T-4 are runtime-heavy.

---

## 5. Concrete Layer 2 Scenarios

To make the gap analysis tangible, here are specific scenarios showing
how Layer 2 would change actual infrastructure operations.

### 5.1 Scenario: Skill Contract Validation

**Today (Layer 1 only):**
```
1. Developer edits permanent-tasks SKILL.md, renames "### User Intent" to "### Goal"
2. No error occurs at edit time
3. Next pipeline run: Phase 0 searches for "### User Intent" in PT description
4. Silent failure — Phase 0 doesn't find the section, proceeds without context
5. Discovered only when an observant Lead notices missing context
```

**With Layer 2 (ObjectType + Interface + Precondition):**
```
1. PERMANENT Task defined as ObjectType with Interface "PTContract"
   PTContract requires: user_intent (STRING), impact_map (STRUCT), ...
2. Developer attempts to rename the section
3. Precondition check: "All PTContract fields must exist in description"
4. Validation FAILS → edit blocked with specific error message
5. Zero silent failures possible for contracted interfaces
```

### 5.2 Scenario: RSIL Finding Query

**Today (Layer 1 only):**
```
Q: "Which L5 SCOPE BOUNDARIES findings have been applied across all reviews?"
A: Read narrow-rsil-tracker.md (400+ lines), manually scan each §3.N section,
   filter by Lens column = L5, check Status column = APPLIED.
   Result: ~13 findings, but requires ~5 minutes of manual parsing.
```

**With Layer 2 (ObjectType + LinkType + Query):**
```
Q: "Which L5 SCOPE BOUNDARIES findings have been applied across all reviews?"
A: Query: Finding.where(lens="L5", status="APPLIED")
   → Returns 13 structured objects with full metadata in <1 second.
   Bonus: Finding.related(review).where(target="execution-plan")
   → Scoped to specific review targets through LinkType traversal.
```

### 5.3 Scenario: Dependency Cascade Detection

**Today (Layer 1 only):**
```
1. task-api-guideline.md v6.0 changes §3 field requirements
2. Lead must remember that 4 skills reference §3
3. Lead manually greps for "task-api-guideline" across .claude/skills/
4. Lead manually reads each skill to check if §3 reference is still valid
5. If Lead forgets, stale references persist until next RSIL audit
```

**With Layer 2 (LinkType + Automation):**
```
1. task-api-guideline.md v6.0 changes §3 field requirements
2. LinkType: task-api-guideline §3 ←REFERENCED_BY→ [4 skills]
3. Automation trigger: "on change to referenced section, notify consumers"
4. System automatically flags 4 skills for review
5. Precondition on commit: "all REFERENCED_BY links must be validated"
6. Zero possibility of stale references persisting undetected
```

---

## 6. Achievement vs. Vision — Honest Assessment

### 6.1 What's Been Achieved

The RTDI Codebase at Layer 1 is a **functioning, self-improving, observable
AI agent orchestration framework** — this is not theoretical. Evidence:

- 3 production pipeline executions (COW v2.0, RTD system, INFRA v7.0)
- 72 self-discovered quality findings at 92% acceptance rate
- 4-Layer observability capturing every tool call and decision
- 9-phase pipeline with understanding verification and two-stage review
- ~6,000 lines of NL infrastructure, version-controlled and cross-referenced

This is substantially more than a collection of config files. It's a paradigm
where natural language functions as executable specification, with built-in
quality feedback loops.

### 6.2 What's Not Achieved

The fundamental tension: **NL is expressive but not enforceable**.

Layer 1 can express any contract ("section headers must match exactly"),
but cannot enforce it. Layer 1 can discover any inconsistency (RSIL audit),
but only after the fact and through manual effort. Layer 1 can track state
(PERMANENT Task), but cannot query it structurally.

The 70% overall score decomposes as:
- Layer 1 capability: ~90% of what's possible within NL + hooks + Task API
- Layer 2 capability: 0% (not started)
- The missing 30% is structurally unreachable through Layer 1 alone

### 6.3 The Meta-Observation

The most telling evidence of Layer 2's necessity comes from the RSIL system
itself. RSIL was designed to review infrastructure quality — and it works.
But the RSIL review process itself generates unstructured findings stored in
markdown tables, discovered through manual audit, and tracked through a
process that Layer 2 would formalize.

**The quality system that validates the infrastructure cannot validate itself
using only the infrastructure's own mechanisms.** This recursive gap is the
strongest argument for Layer 2.

---

## 7. Brainstorming Topic Definition

This document itself is the brainstorming topic. When invoking
`/brainstorming-pipeline`, use this document as the primary input alongside
`ontology-bridge-handoff.md`.

### 7.1 Proposed Brainstorming Scope

```
Topic: RTDI Layer 2 Integration Strategy
Scope: Design the bridge between Layer 1 infrastructure (as-is) and
       Layer 2 Ontology Framework (to-be), with focus on:
       1. Which INFRA entities become ObjectTypes first?
       2. What LinkTypes connect them?
       3. What Preconditions enforce current "Never" rules?
       4. What storage format supports both NL readability and queries?

Inputs:
  - This document (gap analysis with evidence)
  - ontology-bridge-handoff.md (Ontology Component definitions)
  - Bridge reference files (5 files, 3842 lines in bridge-reference/)
  - Current INFRA state (CLAUDE.md v7.0, 9 skills, 4 hooks, etc.)

Expected output:
  - Design file: docs/plans/YYYY-MM-DD-rtdi-layer2-design.md
  - ObjectType candidates derived from actual INFRA entities
  - LinkType candidates derived from actual cross-references
  - Precondition candidates derived from actual "Never" rules
  - Storage format decision (YAML-on-disk vs alternatives)
  - Migration strategy: how to transition from NL-only to NL+Schema
```

### 7.2 Key Questions for Brainstorming

1. **Entity Discovery:** Which of these INFRA concepts should become ObjectTypes?
   - PERMANENT Task (versioned state container)
   - Pipeline Phase (state machine: PENDING → IN_PROGRESS → COMPLETE)
   - RSIL Finding (typed: lens, severity, category, status, target)
   - Skill Definition (typed: name, phases, dependencies, frontmatter)
   - Agent Instance (typed: role, session, status, owned files)
   - Decision Point (typed: who, what, why, evidence, impact)
   - Gate Record (typed: phase, criteria, results)

2. **Relationship Discovery:** What connections exist?
   - Phase → Task (one-to-many containment)
   - Skill → Phase (many-to-many: skills span phases)
   - Finding → Skill (many-to-one: target)
   - Finding → Lens (many-to-one: classification)
   - Finding → Finding (cascade: S-1 → S-2 → S-3)
   - Decision → Phase (one-to-one: approved by)
   - File → File (many-to-many: dependency graph)

3. **Enforcement Discovery:** What rules need formal Pre/Postconditions?
   - "Never create multiple [PERMANENT] tasks" → Precondition on TaskCreate
   - "Section headers must match exactly" → Schema validation on write
   - "No concurrent edits to the same file" → Precondition on file assignment
   - "Gate approval requires all criteria met" → Postcondition on gate transition
   - "Understanding must be verified before plan approval" → Precondition on approve action

4. **Storage Decision:** How should Layer 2 data coexist with Layer 1?
   - Option A: YAML schema files alongside .md files (dual representation)
   - Option B: YAML-only with NL generated from schema (single source)
   - Option C: MD remains primary, YAML validates MD structure (validator layer)
   - Previous recommendation (ontology-bridge-handoff.md §9): Option A (YAML-on-disk)

### 7.3 Forward-Compatibility Requirements

Any Layer 2 design must:
- Preserve Layer 1 readability (markdown must remain human-parseable)
- Not require new hooks (AD-15: 4 hooks inviolable)
- Support incremental adoption (not big-bang migration)
- Enable RSIL to validate Layer 2 schemas (self-referential quality loop preserved)
- Work within Opus 4.6 context limits (~200K, 128K output)

---

## 8. Deferred Items Inventory (Layer 2 Evidence)

These items were explicitly deferred to Layer 2 during RSIL reviews.
They serve as concrete evidence of what Layer 1 cannot achieve.

| Source | Item | Why Layer 1 Cannot | Layer 2 Component |
|--------|------|-------------------|-------------------|
| P4-R4 | Skill preload templates | Requires typed template system | T-1 ObjectType |
| P5-R4 | Adaptive thinking effort per agent | API-level parameter, not NL | T-4 Integration |
| P9-R7 | Compact recovery state marker | Requires persistent state machine | T-3 ActionType |
| P5-R3 | Structured output via tool schema | API-level feature, not CC CLI | T-4 Integration |
| RSIL | Formal contract verification | NL assertion not enforceable | T-2 Interface |
| RTD | Agent attribution (BUG-003) | $CLAUDE_SESSION_ID not exposed | T-1 ObjectType (partial) |
| General | Automated dependency cascade | No watcher mechanism in Layer 1 | T-2 LinkType + T-4 Automation |
| General | Machine-queryable findings | Markdown tables not queryable | T-1 ObjectType + T-4 Query |

---

## 9. Operational Constraints for Brainstorming

Carried forward from `ontology-bridge-handoff.md` §10, plus new constraints
from INFRA v7.0 experience:

- Max 2 teammates spawned concurrently (local PC memory)
- Shift-left 80%+ effort in Phases 1-5
- Max token usage (Claude Max X20, no conservation)
- Sequential and thorough execution
- claude-code-guide research mandatory before any design
- Each design file must include Forward-Compatibility section
- **NEW:** Layer 2 must not invalidate any RSIL finding (72 findings, all remain valid)
- **NEW:** Layer 2 adoption must be incremental (one ObjectType at a time, not big-bang)
- **NEW:** First domain for Ontology Framework is the INFRA itself (bootstrap: INFRA defines its own schema)
- **NEW:** RSIL Category C items (§8 inventory) are the minimum viable Layer 2 scope

---

## 10. Success Criteria for Layer 2

When Layer 2 is "done enough," the following should be true:

| # | Criterion | Measurement |
|---|-----------|-------------|
| SC-1 | Section header renames are caught at write time | Schema validation blocks malformed PT |
| SC-2 | "Show me all L5 findings" returns structured results | Query engine returns typed objects |
| SC-3 | File dependency changes auto-flag consumers | Automation trigger fires on reference change |
| SC-4 | "Never create multiple [PERMANENT] tasks" is enforced | Precondition blocks the second TaskCreate |
| SC-5 | RSIL findings are queryable across sessions | Finding ObjectType with cross-session persistence |
| SC-6 | Gate approval requires all criteria with evidence | Postcondition validates criteria before state transition |
| SC-7 | Layer 1 markdown remains human-readable | Dual representation (MD + YAML) or MD-primary with schema |
| SC-8 | RSIL can validate Layer 2 schemas | Self-referential quality loop extends to Layer 2 |

When SC-1 through SC-8 are met, the RTDI Codebase achieves ~95% of its vision.
The remaining 5% (live dashboard, predictive adaptation, self-healing) are
future extensions that build on the Layer 2 foundation.
