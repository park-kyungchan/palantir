# Relationship Map — Component Interconnections

## 1. Skill-to-Agent Spawning Map

Each skill orchestrates specific agents through coordinators or direct spawn.

### Pipeline Skills → Coordinator → Workers

```
brainstorming-pipeline (P0-3)
├── research-coordinator
│   ├── codebase-researcher
│   ├── external-researcher
│   └── auditor
└── architecture-coordinator (COMPLEX only)
    ├── structure-architect
    ├── interface-architect
    └── risk-architect
    (TRIVIAL/STANDARD: architect directly)

agent-teams-write-plan (P4)
└── planning-coordinator (COMPLEX only)
    ├── decomposition-planner
    ├── interface-planner
    └── strategy-planner
    (TRIVIAL/STANDARD: plan-writer or architect directly)

plan-validation-pipeline (P5)
└── validation-coordinator (COMPLEX only)
    ├── correctness-challenger
    ├── completeness-challenger
    └── robustness-challenger
    (TRIVIAL/STANDARD: devils-advocate directly)

agent-teams-execution-plan (P6)
└── execution-coordinator
    ├── implementer (1-4 instances)
    ├── infra-implementer (0-2 instances)
    ├── spec-reviewer (dispatched for review)
    ├── code-reviewer (dispatched for review)
    ├── contract-reviewer (dispatched for review)
    └── regression-reviewer (dispatched for review)

verification-pipeline (P7-8)
└── testing-coordinator
    ├── tester (1-2 instances)
    ├── contract-tester (1 instance)
    └── integrator (1 instance, conditional: 2+ implementers in P6)
```

### Lead-Direct Agent Spawning (no coordinator)

```
Any phase ──→ dynamic-impact-analyst (P2d, P6+)
Any phase ──→ devils-advocate (P5, TRIVIAL/STANDARD)
Any phase ──→ execution-monitor (P6+, parallel)
Gate points ─→ gate-auditor (G3-G8, tier-dependent)
```

### Cross-Cutting Skills

```
rsil-global / rsil-review ──→ infra-quality-coordinator
                                ├── infra-static-analyst
                                ├── infra-relational-analyst
                                ├── infra-behavioral-analyst
                                └── infra-impact-analyst

permanent-tasks ──→ Lead-only (no agents spawned)
delivery-pipeline ──→ Lead-only (no agents spawned)
palantir-dev ──→ Lead-only (no agents spawned)
```

---

## 2. Hook-to-Event Binding Map

```
Claude Code Lifecycle Events
│
├── SubagentStart ──→ on-subagent-start.sh (sync, 10s)
│   ├── Fires: Every agent spawn
│   ├── Produces: teammate-lifecycle.log, session-registry.json
│   └── Injects: additionalContext (PT guidance or GC version)
│
├── PreCompact ──→ on-pre-compact.sh (sync, 30s)
│   ├── Fires: Before context compaction
│   ├── Produces: pre-compact-tasks-{ts}.json, compact-events.log
│   ├── Produces: snapshots/{ts}-pre-compact.json (RTD)
│   └── Injects: hookSpecificOutput WARNING if missing L1/L2
│
├── SessionStart(compact) ──→ on-session-compact.sh (sync, 15s, once)
│   ├── Fires: After context compaction recovery
│   ├── Produces: compact-events.log entry
│   └── Injects: hookSpecificOutput with recovery steps (RTD-enhanced or generic)
│
└── PostToolUse ──→ on-rtd-post-tool.sh (async, 5s)
    ├── Fires: After every tool call (all agents, all sessions)
    ├── Reads: session-registry.json, current-dp.txt
    └── Produces: events/{session_id}.jsonl (JSONL events)
```

### Hook Dependency Chain

```
SubagentStart ──writes──→ session-registry.json ──read-by──→ PostToolUse
                                                              (resolves agent name)

Lead writes ──→ current-dp.txt ──read-by──→ PostToolUse
                                            (associates DP with events)

PreCompact ──reads──→ rtd-index.md ──to──→ snapshots/
SessionStart ──reads──→ rtd-index.md ──injects──→ recovery context
```

---

## 3. Reference-to-Consumer Map

### Direct Reference Chains

```
agent-common-protocol.md
├── Referenced by: ALL 43 agent .md files (first line of body: "Read and follow...")
├── Referenced by: CLAUDE.md §10 (Integrity Principles)
├── Referenced by: coordinator-shared-protocol.md
└── Referenced by: agent-catalog.md

coordinator-shared-protocol.md
├── Referenced by: 8 coordinator .md files
├── Referenced by: CLAUDE.md §3 (Roles: Coordinators)
└── Referenced by: research/verification/execution/testing/infra-quality/architecture/planning/validation-coordinator.md

agent-catalog.md
├── Referenced by: CLAUDE.md §6 (Before Spawning, Agent Selection)
├── Read by: Lead before every orchestration cycle
└── Contains: full details for all 43 agents

gate-evaluation-standard.md
├── Referenced by: CLAUDE.md §2 (Pipeline)
├── Referenced by: All skill SKILL.md files (Phase 0 gate blocks)
├── Referenced by: gate-auditor.md
└── Read by: Lead at every phase transition

ontological-lenses.md
├── Referenced by: agent-catalog.md (INFRA Quality category)
├── Referenced by: infra-static/relational/behavioral/impact-analyst.md
├── Referenced by: structure-architect.md (ARE lens)
├── Referenced by: interface-architect.md (RELATE lens)
└── Referenced by: risk-architect.md (IMPACT lens)

task-api-guideline.md
├── Referenced by: CLAUDE.md §7 (implied)
├── Read by: Lead (TaskCreate/TaskUpdate)
└── Read by: All agents (TaskList/TaskGet)

layer-boundary-model.md
├── Referenced by: CLAUDE.md §10 (See also)
├── Referenced by: rsil-global SKILL.md
└── Referenced by: rsil-review SKILL.md

ontology-communication-protocol.md
├── Referenced by: MEMORY.md (always-active protocol)
└── Read by: Lead when Ontology/Foundry topics arise

pipeline-rollback-protocol.md
├── Referenced by: plan-validation-pipeline SKILL.md
├── Referenced by: verification-pipeline SKILL.md
└── Referenced by: agent-teams-execution-plan SKILL.md
```

### Reference Fan-In (most consumed)

| Reference | Consumer Count | Criticality |
|-----------|---------------|-------------|
| agent-common-protocol.md | 43+ (all agents) | CRITICAL — universal |
| agent-catalog.md | 1 (Lead) | CRITICAL — routing decisions |
| gate-evaluation-standard.md | 12+ (Lead, skills, gate-auditor) | HIGH — phase transitions |
| coordinator-shared-protocol.md | 8 (coordinators) | HIGH — coordinator identity |
| ontological-lenses.md | 7 (4 INFRA + 3 arch) | MEDIUM — lens framework |
| pipeline-rollback-protocol.md | 3 (skills) | MEDIUM — rollback paths |
| task-api-guideline.md | 43+ (all agents) | HIGH — task API |
| layer-boundary-model.md | 3 (Lead, RSIL skills) | LOW — design philosophy |
| ontology-communication-protocol.md | 1 (Lead) | LOW — domain-specific |

---

## 4. Pipeline Flow with Full Component Mapping

```
                        ┌─────────────────────────────────────────────┐
                        │           PERMANENT TASK (PT-v{N})          │
                        │  User Intent + Impact Map + Decisions       │
                        │  Created by: permanent-tasks skill          │
                        │  Updated by: Lead (Read-Merge-Write)        │
                        └─────────────────────┬───────────────────────┘
                                              │
   ╔══════════════════════════════════════════╪═══════════════════════════╗
   ║  PRE (70-80% effort)                    │                           ║
   ║                                          │                           ║
   ║  P0 ─── Lead: Tier Classification ───────┤                           ║
   ║         (TRIVIAL / STANDARD / COMPLEX)   │                           ║
   ║         Gate: gate-evaluation-standard    │                           ║
   ║                                          │                           ║
   ║  P1 ─── Lead: Discovery ────────────────┤                           ║
   ║         (identify scope, dependencies)   │                           ║
   ║                                          │                           ║
   ║  P2 ─── research-coordinator ────────────┤                           ║
   ║         ├── codebase-researcher          │                           ║
   ║         ├── external-researcher          │                           ║
   ║         └── auditor                      │                           ║
   ║         Gate G2: gate-evaluation-standard│                           ║
   ║                                          │                           ║
   ║  P2b ── verification-coordinator ────────┤ (can overlap P2)         ║
   ║         ├── static-verifier              │                           ║
   ║         ├── relational-verifier          │                           ║
   ║         └── behavioral-verifier          │                           ║
   ║         Gate G2b                         │                           ║
   ║                                          │                           ║
   ║  P2d ── dynamic-impact-analyst ──────────┤ (can overlap P3)         ║
   ║         (Lead-direct)                    │                           ║
   ║                                          │                           ║
   ║  P3 ─── architecture-coordinator ────────┤ (COMPLEX)                ║
   ║         ├── structure-architect (ARE)    │                           ║
   ║         ├── interface-architect (RELATE) │                           ║
   ║         └── risk-architect (IMPACT)      │                           ║
   ║         OR architect (TRIVIAL/STANDARD)  │                           ║
   ║         Gate G3 [+ gate-auditor]         │                           ║
   ║                                          │                           ║
   ║  P4 ─── planning-coordinator ────────────┤ (COMPLEX)                ║
   ║         ├── decomposition-planner        │                           ║
   ║         ├── interface-planner            │                           ║
   ║         └── strategy-planner             │                           ║
   ║         OR plan-writer (TRIVIAL/STANDARD)│                           ║
   ║         Gate G4 [+ gate-auditor]         │                           ║
   ║                                          │                           ║
   ║  P5 ─── validation-coordinator ──────────┤ (COMPLEX)                ║
   ║         ├── correctness-challenger       │                           ║
   ║         ├── completeness-challenger      │                           ║
   ║         └── robustness-challenger        │                           ║
   ║         OR devils-advocate (STANDARD)    │                           ║
   ║         Gate G5 [+ gate-auditor]         │                           ║
   ╚══════════════════════════════════════════╪═══════════════════════════╝
                                              │
   ╔══════════════════════════════════════════╪═══════════════════════════╗
   ║  EXEC                                   │                           ║
   ║                                          │                           ║
   ║  P6 ─── execution-coordinator ───────────┤                           ║
   ║         ├── implementer(s) [1-4]        │                           ║
   ║         ├── infra-implementer(s) [0-2]  │                           ║
   ║         ├── spec-reviewer (Stage 1)     │                           ║
   ║         ├── code-reviewer (Stage 2)     │                           ║
   ║         ├── contract-reviewer           │                           ║
   ║         └── regression-reviewer         │                           ║
   ║         Gate G6 [+ gate-auditor]         │                           ║
   ║                                          │                           ║
   ║  P6+ ── execution-monitor ───────────────┤ (parallel with P6)       ║
   ║         (drift, conflict, budget)        │                           ║
   ║                                          │                           ║
   ║  P7 ─── testing-coordinator ─────────────┤                           ║
   ║         ├── tester(s) [1-2]             │                           ║
   ║         └── contract-tester [1]         │                           ║
   ║         Gate G7 [+ gate-auditor]         │                           ║
   ║                                          │                           ║
   ║  P8 ─── testing-coordinator ─────────────┤ (conditional: 2+ impl)   ║
   ║         └── integrator [1]              │                           ║
   ║         Gate G8 [+ gate-auditor]         │                           ║
   ╚══════════════════════════════════════════╪═══════════════════════════╝
                                              │
   ╔══════════════════════════════════════════╪═══════════════════════════╗
   ║  POST                                   │                           ║
   ║                                          │                           ║
   ║  P9 ─── Lead-only (delivery-pipeline) ───┤                           ║
   ║         (consolidate, commit, archive)   │                           ║
   ║         Gate G9                          │                           ║
   ║                                          │                           ║
   ║  Post ── rsil-global (auto-invoke) ──────┘                           ║
   ║          infra-quality-coordinator                                   ║
   ║          ├── infra-static-analyst                                    ║
   ║          ├── infra-relational-analyst                                ║
   ║          ├── infra-behavioral-analyst                                ║
   ║          └── infra-impact-analyst                                    ║
   ╚══════════════════════════════════════════════════════════════════════╝
```

### Rollback Paths (from pipeline-rollback-protocol.md)

```
P5 ──FAIL──→ P4  (critical design flaws)
P6 ──FAIL──→ P4  (design inadequacy)
P6 ──FAIL──→ P3  (architecture insufficient, requires user confirm)
P7 ──FAIL──→ P6  (code changes needed)
P7 ──FAIL──→ P4  (design flaws revealed by tests)
P8 ──FAIL──→ P6  (implementation fixes needed)
```

---

## 5. Cross-Cutting Relationships

### Observability System

```
.agent/observability/
├── .current-project ← Written by Lead at pipeline start
│                       Read by all hooks
├── {project-slug}/
│   ├── manifest.json ← Created by Lead
│   ├── rtd-index.md ← Written by Lead at decision points
│   │                    Read by SessionStart hook, PreCompact hook
│   ├── current-dp.txt ← Written by Lead before DPs
│   │                      Read by PostToolUse hook
│   ├── session-registry.json ← Written by SubagentStart hook
│   │                            Read by PostToolUse hook
│   ├── events/{session}.jsonl ← Written by PostToolUse hook
│   │                             Read by execution-monitor, Lead
│   └── snapshots/ ← Written by PreCompact hook
│                     Read by Lead during recovery
```

### Agent Memory System

```
~/.claude/agent-memory/
├── {role}/MEMORY.md ← Read/written by agents at start/end
│                       7 roles have persistent memory
└── {category}/MEMORY.md ← Written by coordinators only
                            Read by all category workers
```

### Team Output System

```
.agent/teams/{session-id}/
├── orchestration-plan.md ← Written by Lead
├── TEAM-MEMORY.md ← Written by Lead + agents with Edit
├── phase-{N}/
│   ├── gate-record.yaml ← Written by Lead
│   ├── gate-audit.yaml ← Written by gate-auditor
│   ├── phase-context.md ← Written by Lead (COMPLEX only, D-012)
│   └── {role}-{id}/
│       ├── L1-index.yaml ← Written by agent/coordinator
│       ├── L2-summary.md ← Written by agent/coordinator
│       ├── L3-full/ ← Written by agent/coordinator
│       ├── task-context.md ← Written by Lead
│       └── progress-state.yaml ← Written by coordinators
```

---

## 6. Configuration Hierarchy

```
.claude.json (project-level)
├── MCP servers: github, context7, sequential-thinking, tavily
│
.claude/settings.json (team-level)
├── env: Agent Teams, token limits, tool search
├── permissions.deny: protected files/commands
├── hooks: 4 lifecycle hooks
├── plugins: 2 superpowers plugins
├── language: Korean
├── model: claude-opus-4-6
│
.claude/settings.local.json (local overrides)
├── permissions.allow: Bash, MCP tools, TaskCreate/TaskUpdate
├── enabledMcpjsonServers: 8 servers
└── enableAllProjectMcpServers: true
```

Settings merge order: `.claude.json` → `settings.json` → `settings.local.json` (local overrides take precedence).
