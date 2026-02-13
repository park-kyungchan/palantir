# Layer 1/Layer 2 Boundary Model

> Opus 4.6's NL strength determines the boundary between what agents can achieve
> (Layer 1) and what requires formal systems (Layer 2).

## Core Premise

Opus 4.6 follows nuanced NL instructions with high fidelity, infers intent from context,
and performs complex multi-step reasoning without structured markers. This dramatically
expands what NL agents can accomplish vs structural solutions.

AD-15 (hook addition prohibited) is philosophical alignment:
- 4 hooks = minimal structural backbone (SubagentStart, PreCompact, SessionStart, PostToolUse)
- Everything else through NL agent instructions
- Adding hooks → more structural dependency → less NL leverage

## 5-Dimension Coverage

### STATIC (95% Layer 1)

**L1 Procedure:**
1. Agent uses Glob to discover all config/reference files
2. Read each file's content
3. NL comparison: "Does CLAUDE.md §2 agent list match .claude/agents/ directory?"
4. Grep for cross-references → Read target → verify match
5. Report inconsistencies with file:line evidence

**L2 would add:** CI-style automated validation without agent spawn. But agent IS the
validation engine — making L2 unnecessary for most cases.

**Primary agent:** `infra-static-analyst` (INFRA Quality, X-cut)
**Phase 2b variant:** `static-verifier` (external source verification)

### BEHAVIORAL (90% Layer 1)

**L1 Procedure:**
1. Read each agent .md YAML frontmatter
2. Verify disallowedTools match role (e.g., spec-reviewer has no Write/Edit/Bash)
3. Compare agent behavior (from L2 output) against agent-common-protocol.md procedures
4. Verify lifecycle: spawn → understand → plan → execute → L1/L2/L3 → report

**L2 would add:** Runtime enforcement (blocking tools during execution). Already solved
by Claude Code's disallowedTools frontmatter — a L1-native structural mechanism.

**Primary agent:** `infra-behavioral-analyst` (INFRA Quality, X-cut)
**Phase 2b variant:** `behavioral-verifier` (external source verification)

### RELATIONAL (85% Layer 1)

**L1 Procedure:**
1. Grep: find all files referencing target file
2. Grep: find all files target references
3. For each (A ↔ B) pair: Read both → verify bidirectional consistency
4. PT's Codebase Impact Map serves as NL dependency graph
5. Sequential-thinking for "A → B → C" chain reasoning

**L2 would add:** Persistent queryable dependency graph with formal traversal. But 200K
context window makes re-reading practically sufficient.

**Primary agent:** `infra-relational-analyst` (INFRA Quality, X-cut)
**Phase 2b variant:** `relational-verifier` (external source verification)

### DYNAMIC-IMPACT (75% Layer 1)

**L1 Procedure:**
1. TaskGet → read PT's Codebase Impact Map
2. Analyze proposed change with sequential-thinking
3. Grep: find all files referencing the changed component
4. Read each referencing file → assess impact scope
5. Cascade reasoning: "Change A → B needs update → C also affected"
6. Produce checklist: "N files to verify before proceeding"

**Why this works:** PT's Impact Map provides NL dependency graph. Agent reads it + uses
sequential-thinking for ripple analysis. Grep supplements for references Impact Map missed.

**L1 limitation:** Completeness not guaranteed — Grep patterns may be incomplete. But
Opus 4.6 + sequential-thinking + systematic Grep = ~90%+ practical coverage.

**L2 would add:** Formal graph traversal, guaranteed completeness, typed edge queries.

**Primary agents:** `dynamic-impact-analyst` (Phase 6+), `infra-impact-analyst` (INFRA Quality)
**Phase 2d variant:** `impact-verifier` (correction cascade analysis)

### REAL-TIME (50% Layer 1)

**L1 Procedure (Polling Model):**
Monitor agent (spawned as parallel teammate):
1. Read events.jsonl (PostToolUse hook records all tool calls)
2. Read implementer L1 files → check progress
3. Grep modified files → compare against plan
4. Anomaly detected → SendMessage to Lead

**Response time spectrum:**

| Approach | Layer | Response | Miss Risk |
|----------|-------|----------|-----------|
| Lead manual check every 15min | L1 | ~15min | HIGH |
| Monitor agent per-task check | L1 | ~2-5min | MEDIUM |
| Monitor agent events.jsonl poll | L1 | ~1-2min | LOW-MED |
| Event bus + push notification | L2 | <1sec | NEAR-ZERO |
| Formal state machine + guaranteed delivery | L2 | <1sec | ZERO |

**Practical question:** Agent work units are minutes-to-hours. 1-2min polling catches
most drift/conflicts. True real-time only needed for file conflicts — already prevented
by file ownership rules (CLAUDE.md §5).

**L1 limitation:** No push — agents poll, not react. Token cost per poll cycle.
Sub-second impossible.

**Primary agent:** `execution-monitor` (Phase 6+)

## AD-15 Relationship

```
Structural (hooks, scripts)  ←──────→  NL (agent instructions)
        │                                      │
4 existing hooks ───┤           ← AD-15 boundary →          │
        │                                      │
    Layer 2                              Layer 1
  (formal systems)                    (Opus 4.6 NL)
        │                                      │
  real-time streaming              dynamic-impact analysis
  guaranteed delivery              behavioral verification
  schema validation                static comparison
  state machines                   relational tracing
```

**Principle:** Instead of adding hooks, make agent NL instructions more sophisticated.
- "New hook for file change detection" → "Monitor agent polls events.jsonl"
- "Hook for permission verification" → "Behavioral-analyst reads frontmatter"
- Result: same goal, NL-based, flexible, modifiable per context.

## Practical Sufficiency

For the Agent Teams orchestration system:
- Static + Behavioral + Relational = 90%+ coverage through NL agents alone
- Dynamic-Impact = 75% coverage, sufficient for most practical needs
- Real-Time = 50% coverage, adequate given file ownership prevents the highest-risk conflicts
- Combined: Layer 1 achieves approximately 80% of what a full Layer 2 system would provide
- The remaining 20% (formal guarantees, sub-second response, schema validation) is
  Layer 2 territory — deferred until a concrete use case demands it

## Coordinator Orchestration (Layer 1)

The hybrid coordinator model (AD-8, AD-12) is a direct application of Layer 1 principles.
Coordinators manage multi-agent categories through NL instructions alone:

- Task distribution via peer messaging (SendMessage)
- Understanding verification delegation (AD-11) using Impact Map excerpts
- Review dispatch (execution-coordinator manages spec-reviewer + code-reviewer)
- Progress monitoring and findings consolidation
- Fallback to Lead-direct mode on failure (Mode 3)

No hooks, no scripts, no structural enforcement — coordinators follow `.md` instructions
and use the same tools (Read, Glob, Grep, Write, TaskList, TaskGet) as any agent.
This validates the core premise: Opus 4.6 NL strength makes formal orchestration systems
unnecessary for this use case. Eight coordinators replace what would traditionally require
a message bus, state machine, or workflow engine.

## Agent Mapping

Each dimension has two agent tiers:

| Dimension | INFRA Quality Agent (internal) | Phase 2b/2d Agent (external) |
|-----------|-------------------------------|------------------------------|
| STATIC | `infra-static-analyst` | `static-verifier` |
| BEHAVIORAL | `infra-behavioral-analyst` | `behavioral-verifier` |
| RELATIONAL | `infra-relational-analyst` | `relational-verifier` |
| DYNAMIC-IMPACT | `infra-impact-analyst` / `dynamic-impact-analyst` | `impact-verifier` |
| REAL-TIME | `execution-monitor` | — (no external variant) |

**Internal agents** (INFRA Quality): Analyze .claude/ infrastructure using L1 procedures above.
**External agents** (Phase 2b/2d): Verify claims against authoritative web sources.
