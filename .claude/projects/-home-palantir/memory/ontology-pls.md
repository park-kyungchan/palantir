# Ontology Progressive Learning System — Session Handoff

Deferred to new session (2026-02-10). All phases complete, no implementation needed.

## Status
- PT #3 completed and archived
- Communication Protocol: ACTIVE in MEMORY.md (always-on trigger)
- Next action: T-0 brainstorming via `/brainstorming-pipeline`

## Architecture Decisions (AD-1 ~ AD-13)
1. Learning = Communication Protocol, not state tracking
2. 4-step pattern: TEACH → IMPACT ASSESS → RECOMMEND → ASK
3. Always active trigger — any Ontology topic in any context
4. MEMORY.md core + reference doc at .claude/references/
5. 3-axis IMPACT ASSESS + 4 risk dimensions
6. 3-layer knowledge: Palantir / Methodology / Bridge
7. 15 corrections applied (2C, 8H, 5M), 5M + 5L deferred
8. Two-Tier Protocol Activation (MEMORY trigger + on-demand reference)
9. Protocol subsumes brainstorming Rule 7
10. Three-Tier Knowledge Retrieval (reference → per-topic → bridge files)
11. Deferred corrections as teaching opportunities
12. Implicit state via PT + design files + MEMORY.md
13. Layer-ordered teaching: A (Palantir) → B (Methodology) → C (Bridge)

## Connected Documents — Complete Index

### INFRA References (always active)
- `.claude/references/ontology-communication-protocol.md` (~388L) — Protocol reference with dependency map, anti-patterns, decision trees, scale limits, corrections

### Design/Plan Documents
| File | Lines | Role |
|------|-------|------|
| `docs/plans/2026-02-10-rtdi-codebase-assessment.md` | 660L | WHY: Layer 1/2 boundary analysis |
| `docs/plans/2026-02-08-ontology-bridge-handoff.md` | ~450L | WHAT: bridge concept + handoff |
| `docs/plans/2026-02-10-ontology-sequential-protocol.md` | ~418L | HOW: sequential component definition |
| `docs/plans/2026-02-10-ontology-docs-corrections.md` | — | Corrections tracker (15 applied, 10 deferred) |
| `docs/plans/2026-02-10-ontology-learning-architecture.md` | 882L | Architecture (validates existing INFRA sufficient) |

### Source Documents (Ontology Definition)
| Path | Count | Description |
|------|-------|-------------|
| `park-kyungchan/palantir/Ontology-Definition/docs/palantir_ontology_{1-9}.md` | 9 files | Core Ontology docs (~15K lines) |
| `park-kyungchan/palantir/Ontology-Definition/docs/LLM-Agnostic_vs_Palantir_Ontology_Architecture.md` | 1 file | Architecture comparison |
| `park-kyungchan/palantir/Ontology-Definition/docs/bridge-reference/bridge-ref-{objecttype,linktype,methodology,actiontype,secondary}.md` | 5 files | Bridge reference docs |

### Research Outputs (session artifacts)
| Path | Description |
|------|-------------|
| `.agent/ontology-research/researcher-{1,2,3}/L2-summary.md` | 3 researcher outputs (Phase 1-2) |
| `.agent/ontology-research/verifier-{static,relational,behavioral}/L2-summary.md` | 3 verifier outputs (Phase 2) |
| `.agent/ontology-research/agent-designer/L2-summary.md` | Agent designer output |

## Brainstorming Chain (T-0 ~ T-4)

Layer 2 initiative. Entry via `/brainstorming-pipeline`.
Layer 1 ~70% (RTDI). Layer 2 = 0% → target ~30%.
Brainstorming = Dual Purpose: decision-making + progressive learning.

| Topic | Name | Depends On | Output |
|-------|------|------------|--------|
| T-0 | RTDI Layer 2 Strategy | — | L2 scope, bootstrap domain |
| T-1 | ObjectType + Property + Struct | T-0 | Schema definitions |
| T-2 | LinkType + Interface | T-1 | Relationship + abstraction |
| T-3 | ActionType + Pre/Postconditions | T-1 | Mutation + constraints |
| T-4 | Framework Integration | T-1,T-2,T-3 | Runtime architecture |

## 3-Layer Knowledge (verified 2026-02-10, 40+ official palantir.com/docs)
- **Palantir Concepts**: 8 core components, type system, cardinality, anti-patterns — transferable
- **Our Methodology**: 8-phase decomposition, decision trees, indicator counts — locally synthesized
- **Bridge Adaptations**: YAML, filesystem, CLI, NL enforcement — local implementation

## Constraints
- Max protocol cost: 12,650 tokens (6.3% of context)
- BUG-002 aware: teaching materials add context load
- Layer 1 only: structured learning tracking is Layer 2 (defer)
- Ontology docs must reflect REAL Palantir concepts (MCP-verified)
