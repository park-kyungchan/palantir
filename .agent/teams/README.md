# Agent Teams Output Directory

This directory stores outputs from Agent Teams sessions.

## Structure

```
.agent/teams/{session-id}/
├── orchestration-plan.md      # Lead's pipeline visualization
├── global-context.md          # Full project context for teammates
├── phase-{N}/
│   ├── gate-record.yaml       # Gate approval/iteration/abort record
│   └── {role}-{id}/
│       ├── L1-index.yaml      # Index of outputs (≤50 lines)
│       ├── L2-summary.md      # Summary of work (≤200 lines)
│       ├── L3-full/           # Complete detailed outputs
│       ├── task-context.md    # Teammate's role context
│       └── handoff.yaml       # Handoff metadata (if replaced)
```

## Session ID

Format: `{YYYYMMDD}-{HHMMSS}-{short-description}`
Example: `20260207-143022-infra-redesign`

## Lead Responsibilities

Lead creates and maintains:
- `orchestration-plan.md` — updated at every phase transition
- `global-context.md` — updated when architecture changes
- `phase-{N}/gate-record.yaml` — written at every gate decision
- `phase-{N}/{role}-{id}/task-context.md` — written at teammate spawn time
