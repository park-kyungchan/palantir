---
version: GC-v7
created: 2026-02-08
feature: rtdi-sprint
complexity: COMPLEX
---

# Global Context — RTDI Sprint

## Scope

**Goal:** Transform the codebase into a Real-Time Dynamic Integration (RTDI) system across two workstreams: .claude/ infrastructure (DIA v5.0) and Palantir Ontology/Foundry docs refinement.

**In Scope:**
- Workstream A: .claude/ INFRA — DIA v5.0 optimization (CLAUDE.md, task-api-guideline.md, agents, hooks, skills)
- Workstream B: Palantir docs — Ontology.md, OSDK_Reference.md, Security_and_Governance.md, ObjectType_Reference.md refinement
- RTDI enforcement across both workstreams
- Cross-codebase impact tracking and propagation

**Out of Scope:**
- New Python code in ontology-definition package (docs only)
- New skill creation (SKL-004 deferred to next sprint)
- CI/CD pipeline changes

**Approach:** Parallel 4-teammate execution with Lead as RTDI controller

**Success Criteria:**
- AC-1 through AC-10 from DIA v5.0 design met
- Ontology docs elevated with TRUE documentation gaps addressed (not code gaps)
- Ontology Decomposition Guide added — LLM-actionable methodology for any codebase
- All cross-references consistent across the codebase
- No orphaned references after any modification

## [PERMANENT] Operational Directives

### RTDI-001: Cross-Codebase Impact Analysis
Every file modification requires:
1. Search all references to the modified concept across the entire codebase
2. Assess impact on each reference point
3. Modify ALL affected locations in the same work unit
4. Report ripple analysis in status messages to Lead
No change is ever isolated. If a protocol name changes in CLAUDE.md, every agent .md, SKILL.md, and hook that references it must change together.

### RTDI-002: MCP Tools Maximum Utilization
All agents must use available MCP tools to their full extent:
- `sequential-thinking`: Every analysis, judgment, design decision, gate evaluation
- `tavily`: Latest documentation verification, best practices
- `context7`: Library documentation lookup when relevant
- `github`: Repository exploration when needed
Never skip MCP tools when they could improve output quality.

### RTDI-003: Opus 4.6 Native Capability Limits
Before implementing any component, research via claude-code-guide agent what the latest Claude Code / Opus 4.6 capabilities are. Implement up to the native capability limits — do not leave features on the table.

### RTDI-004: Dynamic Team Management
Lead dynamically spawns/deletes teammates as requirements evolve in real-time. Teammates may be added, removed, or reassigned at any point based on user's dynamically added requirements.

### RTDI-005: Semantic Consistency
All cross-file references must resolve correctly:
- Section IDs referenced in one file must exist in the target file
- Protocol format strings must be identical across all files that use them
- Version numbers must be consistent everywhere
- Terminology must be uniform (same concept = same term everywhere)

### RTDI-006: Lead Injection Obligation
All user requirements become [PERMANENT] directives that Lead physically injects into every teammate's context via Task API directives. Not optional, not implicit — explicit injection in every [DIRECTIVE].

### RTDI-007: Lead Autonomous Feasibility Judgment
Some user requirements may not be technically feasible. Lead must autonomously judge feasibility, implement what is possible, and transparently report what was not feasible and why.

### RTDI-009: No Plan Mode — Permanently Disabled
Never spawn any teammate with `mode: "plan"`. Always use `mode: "default"` for all agent types.
Plan mode blocks MCP tools (BUG-001) and adds unnecessary approval overhead. Use `disallowedTools` in agent .md frontmatter to restrict mutations instead. This applies to ALL agent types: researcher, architect, implementer, devils-advocate, tester, integrator.

### RTDI-008: Ontology Docs as Sole LLM Reference
The `park-kyungchan/palantir/docs/` directory must serve as the SOLE reference for Opus 4.6 to accurately understand ALL Palantir Ontology Components. Requirements:
- **Self-contained**: No external references needed — everything an LLM needs is in these docs
- **Complete**: Cover ALL Ontology components (ObjectType, LinkType, ActionType, Interface, Function, Automation, Rules, Security, OSDK, etc.)
- **Unambiguous**: Precise definitions with machine-readable YAML schemas, no room for interpretation
- **Actionable**: Enable decomposing ANY codebase into Ontology Components and defining them accurately
- The docs must be the definitive guide for an LLM to perform: Source Code Analysis → Ontology Decomposition → Component Definition (ObjectType, LinkType, ActionType, etc.)

### RTDI-010: Ontology-Definition/docs as Sole Authoritative Source
All upgrades/enhancements/refinements to `park-kyungchan/palantir/docs/` must reference ONLY the files in `park-kyungchan/palantir/Ontology-Definition/docs/`:
- **palantir_ontology_1.md** (1792 lines): ObjectType, Property, SharedProperty — Core Semantic Primitives
- **palantir_ontology_2.md** (1393 lines): LinkType & Interface
- **palantir_ontology_3.md** (843 lines): ActionType — Kinetic Primitives
- **palantir_ontology_4.md** (1463 lines): Data Pipeline Layer (Dataset, Pipeline, etc.)
- **palantir_ontology_5.md** (460 lines): ObjectSet, TimeSeries, MediaSet — Collection & Specialized Storage Components
- **palantir_ontology_6.md** (1277 lines): Workshop, OSDK, Slate, REST API, Automate — Application & API Layer (5 components)
- **gap-analysis.md** (417 lines): Coverage analysis matrix
These are machine-readable YAML specifications with official Palantir source URLs, JSON schemas, semantic definitions, and code patterns. Every claim, schema, and definition in the output docs must trace back to these reference files. External web research is supplementary only — these local files are the AUTHORITATIVE source.

## Phase Pipeline Status
- Phase 1: COMPLETE (Lead Discovery — this document)
- Phase 2: COMPLETE (researcher-ontology: 12 findings, 4 true gaps, 3 updates, ~650 lines)
- Phase 6 (INFRA): COMPLETE — Gate 6 APPROVED (10/10 ACs PASS)
- Phase 6 (ONTOLOGY): IN_PROGRESS — implementer-ontology-2 implementing 5 GAPs + research findings

## Scope Correction (GC-v3)
**Critical finding by researcher-ontology:** The gap-analysis.md was written against the Python CODEBASE (ontology_definition package), NOT the documentation files. The 4 docs ALREADY cover most "gaps":
- Ontology.md already covers searchAround, groupBy, 3D aggregations, AIP Logic, Funnel/OntologySync
- OSDK_Reference.md already covers aggregations, groupBy, link traversal, subscriptions

**TRUE documentation gaps (revised + enriched by researcher-ontology Phase 2):**
1. Granular Policies — MISSING from Security_and_Governance.md. Details: 8 comparison types, user attributes, weight system, Object + Property Security Policies for cell-level security (~200 lines)
2. Ontology Manager UI metadata — MINIMAL. Details: 8 render hint types with dependency chain (Searchable → Selectable/Sortable/Low cardinality), icon/color/title/search config (~120 lines)
3. OSDK 2025-2026 SDK updates — SIGNIFICANT EXPANSION:
   - Python OSDK 2.x GA (July 2025): Major version, breaking changes, new query syntax (~50 lines)
   - Python Functions GA (July 2025): OSDK first-class, external APIs via functions.sources (~80 lines)
   - TypeScript v2 Functions GA (July 2025): Full Node.js runtime, 5GB/8CPU (~30 lines)
   - Ontology MCP (Jan 2026): MCP integration, external AI agents query Ontology (~60 lines)
4. Depth enhancements — AIP Logic block types (6 blocks + 4 LLM tool types), Writeback patterns, Rules Engine
5. Ontology Decomposition Guide — No official Palantir methodology exists. Implement as LLM-actionable guide using existing Decision Matrix as foundation

## Design References
- DIA v5.0 design: `docs/plans/2026-02-08-dia-v5-optimization-design.md`
- Ontology gap analysis: `park-kyungchan/palantir/Ontology-Definition/docs/gap-analysis.md` (targets CODE, not docs — use with caution)
- Current CLAUDE.md: `.claude/CLAUDE.md` (v5.0)
- Task API guideline: `.claude/references/task-api-guideline.md`
- claude-code-guide research: 14 hook events, RTDI pattern (PostToolUse→SharedFS→SessionStart→TaskAPI)

## Constraints
- Max 3 teammates at any time (memory optimization, reduced from 4)
- English only for all technical artifacts
- Opus 4.6 measured language (no [MANDATORY] inline, [PERMANENT] only at section headers)
- Lead operates in Delegate Mode — never modifies code directly

## Decisions Log
| # | Decision | Rationale | Phase |
|---|----------|-----------|-------|
| D-1 | 2+2 split (INFRA + Ontology) | Balanced progress on both workstreams | P1 |
| D-2 | Parallel start all teammates | RTDI approach — findings propagate in real-time | P1 |
| D-3 | claude-code-guide pre-research | Opus 4.6 native capability limits before implementation | P1 |
| D-4 | Dynamic spawn/delete | User requirements evolve dynamically | P1 |
| D-5 | Lead autonomous feasibility judgment | Some requirements may not be feasible | P1 |
| D-6 | Docs as sole LLM Ontology reference | Opus 4.6 must decompose any codebase using only these docs | P1 |
| D-7 | Scope correction: gap-analysis targets code not docs | Prevents duplicate content; narrows true gaps to 5 items | P2 |
| D-8 | claude-code-guide findings: 14 hooks, RTDI pattern | Enriches DIA v5.0 with full hook coverage + RTDI detection | P1 |
| D-9 | Plan Mode permanently disabled for all agents | BUG-001 + unnecessary overhead; use disallowedTools instead | P6 |
| D-10 | Phase 2 findings expand OSDK scope significantly | Python 2.x, Python Functions, TS v2, Ontology MCP | P2 |
| D-11 | Ontology Decomposition Guide: no official Palantir methodology | Build LLM-actionable guide from Decision Matrix foundation | P2 |
| D-12 | Gate 6 INFRA workstream APPROVED | 10/10 ACs PASS, 2 files modified out of 18 verified | P6 |
| D-13 | RTDI-010: Ontology-Definition/docs as sole authoritative source | All doc refinements must trace back to local reference files, not external web | P6 |
