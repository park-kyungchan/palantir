# COA System Overview — Inter-COA Architecture

## Layered Topology

The 5 COA gaps form an interconnected layered system, NOT 5 independent additions.

```
Layer 0: COA-2 (Self-Location Signal) — the heartbeat pulse
   │
   ├──feeds──→ Layer 1: COA-1 (Sub-Workflow Dashboard) — Lead aggregation
   │                │
   ├──triggers──→ Layer 2: COA-3 (Documentation Checkpoint) — evidence production
   │                                    │
   └──triggers──→ Layer 3: COA-4 (Re-Verification Framework) ←──consumes evidence──┘
                        │                    ↑
                        └──contains──→ COA-5 (MCP Check Type)

                   COA-1 anomalies ──trigger──→ COA-4 (on-demand)
```

## Relationship Matrix

| Source → Target | Relationship Type | Mechanism |
|----------------|-------------------|-----------|
| COA-2 → COA-1 | Data Feed (producer-consumer) | [SELF-LOCATE] messages consumed by Lead for sub-workflow table |
| COA-2 → COA-3 | Trigger | Self-location checkpoints trigger documentation obligation |
| COA-2 → COA-4 | Prerequisite + Data | Position awareness required before re-verification; MCP field feeds COA-5 |
| COA-1 → COA-4 | Anomaly Trigger | ATTENTION status in sub-workflow table triggers re-verification |
| COA-3 → COA-4 | Evidence Enabler | L1/L2 intermediate artifacts are evidence COA-4 consumes |
| COA-4 ⊃ COA-5 | Containment | MCP usage verification is a specific check type within COA-4 framework |

## Design Principles

1. **Single Signal Source:** COA-2 self-location is the heartbeat. All other COAs consume or are triggered by it.
2. **Separation of Concerns:** COA-1 is Lead-side aggregation; COA-2 is teammate-side signal; COA-3 is evidence production; COA-4 is re-verification logic; COA-5 is a specific check.
3. **Layered Depth:** COA-2 (lightweight ping) → COA-3 (document obligation) → COA-4 (comprehension check) — escalating depth at each layer.
4. **No Duplication with DIA:** Entry-gate DIA (CIP/DIAVP/LDAP) remains unchanged. COA adds mid-execution monitoring that DIA currently lacks.
5. **Minimal Token Cost:** Self-location is ~50 tokens. Documentation checkpoints produce artifacts that serve double duty (recovery + verification). Re-verification is triggered only on anomaly.

## New Format Strings (additions to CLAUDE.md §4)

| Format | Direction | Purpose |
|--------|-----------|---------|
| `[SELF-LOCATE]` | Teammate → Lead | Periodic position + status signal |
| `[REVERIFY]` | Lead → Teammate | Mid-execution re-verification request |
| `[REVERIFY-RESPONSE]` | Teammate → Lead | Response to re-verification |

## Integration Summary (files affected)

| File | Sections Affected | COAs Involved |
|------|-------------------|---------------|
| CLAUDE.md §3 | Teammates obligations | COA-2, COA-3 |
| CLAUDE.md §4 | Communication Protocol formats | COA-2, COA-4 |
| CLAUDE.md §6 | Orchestrator Framework (sub-workflow, DIA Engine, Gate Checklist) | COA-1, COA-4 |
| CLAUDE.md §7 | MCP Tools (verification triggers) | COA-5 |
| CLAUDE.md §9 | Compact Recovery (documentation triggers) | COA-3 |
| CLAUDE.md [PERMANENT] | DIA Enforcement (mid-execution extension) | COA-4 |
| task-api-guideline.md §11 | DIA Protocol (re-verification section) | COA-4 |
| All 6 agent .md | Protocol execution phases | COA-2, COA-3, COA-4 |
| 4 SKILL.md files | Orchestration templates | COA-1, COA-2 |
