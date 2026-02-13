# Agent Inventory — Complete (43 Agents)

## Summary Statistics

| Metric | Value |
|--------|-------|
| Total agents | 43 |
| Workers | 35 |
| Coordinators | 8 |
| Categories | 14 |
| Min maxTurns | 15 (gate-auditor) |
| Max maxTurns | 100 (implementer, integrator) |
| Agents with Bash | 4 (implementer, tester, contract-tester, integrator) |
| Agents with Write | 33 |
| Agents with Edit | 5 (implementer, infra-implementer, integrator, contract-reviewer, regression-reviewer) |
| Agents with WebSearch | 7 (external-researcher, static/relational/behavioral-verifier, impact-verifier) |
| Agents with acceptEdits | 2 (implementer, integrator) |

## Workers by Category (35 Total)

### Category 1: Research (3 workers) — Phase 2

| Agent | Color | MaxTurns | Key Tools | Description |
|-------|-------|----------|-----------|-------------|
| codebase-researcher | cyan | 50 | Read, Glob, Grep, Write, seq-thinking | Local codebase exploration specialist |
| external-researcher | cyan | 50 | Read, Glob, Grep, Write, WebSearch, WebFetch, tavily, context7 | Web-based documentation researcher |
| auditor | cyan | 50 | Read, Glob, Grep, Write, seq-thinking | Systematic artifact analyst, inventory/gap |

### Category 2: Verification (4 workers) — Phase 2b

| Agent | Color | MaxTurns | Key Tools | Description |
|-------|-------|----------|-----------|-------------|
| static-verifier | yellow | 40 | Read, Glob, Grep, Write, WebSearch, WebFetch, tavily | Structural/schema claims verifier (ARE lens) |
| relational-verifier | yellow | 40 | Read, Glob, Grep, Write, WebSearch, WebFetch, tavily | Relationship/dependency claims verifier (RELATE lens) |
| behavioral-verifier | yellow | 40 | Read, Glob, Grep, Write, WebSearch, WebFetch, tavily | Action/rule/behavior claims verifier (DO lens) |
| impact-verifier | yellow | 40 | Read, Glob, Grep, Write, WebSearch, WebFetch, tavily | Correction cascade analyst (IMPACT lens) |

### Category 3: Architecture (4 workers) — Phase 3

| Agent | Color | MaxTurns | Key Tools | Lens | Description |
|-------|-------|----------|-----------|------|-------------|
| structure-architect | — | 30 | Read, Glob, Grep, Write, context7, tavily | ARE | Component structure, module boundaries |
| interface-architect | — | 30 | Read, Glob, Grep, Write, context7, tavily | RELATE | API contracts, cross-module interfaces |
| risk-architect | — | 30 | Read, Glob, Grep, Write, context7, tavily | IMPACT | Risk assessment, failure modes, mitigation |
| architect | blue | 50 | Read, Glob, Grep, Write, context7, tavily | All | Legacy general-purpose (Phase 3-4) |

### Category 4: Planning (4 workers) — Phase 4

| Agent | Color | MaxTurns | Key Tools | Description |
|-------|-------|----------|-----------|-------------|
| decomposition-planner | — | 30 | Read, Glob, Grep, Write, context7, tavily | Task breakdown, file assignments, ownership |
| interface-planner | — | 30 | Read, Glob, Grep, Write, context7, tavily | Interface contracts, dependency ordering |
| strategy-planner | — | 30 | Read, Glob, Grep, Write, context7, tavily | Implementation sequencing, risk mitigation |
| plan-writer | blue | 50 | Read, Glob, Grep, Write, context7, tavily | Legacy 10-section implementation planner |

### Category 5: Validation (3 workers) — Phase 5

| Agent | Color | MaxTurns | Key Tools | Description |
|-------|-------|----------|-----------|-------------|
| correctness-challenger | — | 25 | Read, Glob, Grep, Write, seq-thinking | Logical correctness, spec compliance |
| completeness-challenger | — | 25 | Read, Glob, Grep, Write, seq-thinking | Gap analysis, missing elements, coverage |
| robustness-challenger | — | 25 | Read, Glob, Grep, Write, seq-thinking | Edge cases, failure modes, security |

### Category 6: Review (5 workers) — Phase 6

| Agent | Color | MaxTurns | Key Tools | Has Write | Description |
|-------|-------|----------|-----------|-----------|-------------|
| devils-advocate | red | 30 | Read, Glob, Grep, Write, context7, tavily | Yes (L1/L2) | Design validator, critical reviewer |
| spec-reviewer | orange | 20 | Read, Glob, Grep, seq-thinking | No | Spec compliance with file:line evidence |
| code-reviewer | orange | 20 | Read, Glob, Grep, seq-thinking | No | Quality, architecture, safety assessment |
| contract-reviewer | — | 20 | Read, Glob, Grep, Write, Edit, seq-thinking | Yes | Interface contract compliance |
| regression-reviewer | — | 20 | Read, Glob, Grep, Write, Edit, seq-thinking | Yes | Regression and side-effect detection |

### Category 7: Implementation (2 workers) — Phase 6

| Agent | Color | MaxTurns | Permission | Key Tools | Description |
|-------|-------|----------|------------|-----------|-------------|
| implementer | green | 100 | acceptEdits | Read, Glob, Grep, Edit, Write, Bash, context7, tavily | App source code, full tool access |
| infra-implementer | green | 50 | default | Read, Glob, Grep, Edit, Write, seq-thinking | .claude/ infrastructure files only |

### Category 8: Testing (2 workers) — Phase 7

| Agent | Color | MaxTurns | Key Tools | Description |
|-------|-------|----------|-----------|-------------|
| tester | yellow | 50 | Read, Glob, Grep, Write, Bash, context7, tavily | Test writer and executor |
| contract-tester | — | 30 | Read, Glob, Grep, Write, Edit, Bash, context7, tavily | Interface contract test writer |

### Category 9: Integration (1 worker) — Phase 8

| Agent | Color | MaxTurns | Permission | Key Tools | Description |
|-------|-------|----------|------------|-----------|-------------|
| integrator | magenta | 100 | acceptEdits | Read, Glob, Grep, Edit, Write, Bash, context7, tavily | Cross-boundary merger, conflict resolver |

### Category 10: INFRA Quality (4 workers) — Cross-cutting

| Agent | Color | MaxTurns | Lens | Key Tools | Description |
|-------|-------|----------|------|-----------|-------------|
| infra-static-analyst | white | 30 | ARE | Read, Glob, Grep, Write, seq-thinking | Config/naming/reference integrity |
| infra-relational-analyst | white | 30 | RELATE | Read, Glob, Grep, Write, seq-thinking | Dependency/coupling mapping |
| infra-behavioral-analyst | white | 30 | DO | Read, Glob, Grep, Write, seq-thinking | Lifecycle/protocol compliance |
| infra-impact-analyst | white | 40 | IMPACT | Read, Glob, Grep, Write, seq-thinking | Change ripple prediction |

### Category 11: Impact (1 worker) — Phase 2d, 6+

| Agent | Color | MaxTurns | Key Tools | Description |
|-------|-------|----------|-----------|-------------|
| dynamic-impact-analyst | magenta | 30 | Read, Glob, Grep, Write, seq-thinking | Change cascade prediction before implementation |

### Category 12: Audit (1 worker) — G3-G8

| Agent | Color | MaxTurns | Key Tools | Description |
|-------|-------|----------|-----------|-------------|
| gate-auditor | red | 15 | Read, Glob, Grep, Write, seq-thinking | Independent gate evaluation, no Edit/Bash |

### Category 13: Monitoring (1 worker) — Phase 6+

| Agent | Color | MaxTurns | Key Tools | Description |
|-------|-------|----------|-----------|-------------|
| execution-monitor | magenta | 40 | Read, Glob, Grep, Write, seq-thinking | Real-time drift/conflict/budget detection |

## Coordinators (8 Total)

| Coordinator | Color | MaxTurns | Workers Managed | Phase | Key Tools |
|-------------|-------|----------|-----------------|-------|-----------|
| research-coordinator | cyan | 50 | codebase-researcher, external-researcher, auditor | P2 | Read, Glob, Grep, Write, seq-thinking |
| verification-coordinator | yellow | 40 | static-verifier, relational-verifier, behavioral-verifier | P2b | Read, Glob, Grep, Write, seq-thinking |
| architecture-coordinator | — | 40 | structure-architect, interface-architect, risk-architect | P3 | Read, Glob, Grep, Write, seq-thinking |
| planning-coordinator | — | 40 | decomposition-planner, interface-planner, strategy-planner | P4 | Read, Glob, Grep, Write, seq-thinking |
| validation-coordinator | — | 40 | correctness-challenger, completeness-challenger, robustness-challenger | P5 | Read, Glob, Grep, Write, seq-thinking |
| execution-coordinator | green | 80 | implementer(s), infra-implementer, spec-reviewer, code-reviewer, contract-reviewer, regression-reviewer | P6 | Read, Glob, Grep, Write, seq-thinking |
| testing-coordinator | magenta | 50 | tester, contract-tester, integrator | P7-8 | Read, Glob, Grep, Write, seq-thinking |
| infra-quality-coordinator | white | 40 | infra-static/relational/behavioral/impact-analyst | X-cut | Read, Glob, Grep, Write, seq-thinking |

**Coordinator common pattern:**
- All block: TaskCreate, TaskUpdate, Edit, Bash (except execution-coordinator only blocks Edit/Bash)
- All use: Read, Glob, Grep, Write, seq-thinking
- All follow: agent-common-protocol.md + coordinator-shared-protocol.md
- All write: progress-state.yaml + L1/L2/L3 + Downstream Handoff section

## Tool Distribution Matrix

| Tool | Worker Count | Coordinator Count | Total |
|------|-------------|-------------------|-------|
| Read | 35 | 8 | 43 |
| Glob | 35 | 8 | 43 |
| Grep | 35 | 8 | 43 |
| Write | 31 | 8 | 39 |
| Edit | 5 | 0 | 5 |
| Bash | 4 | 0 | 4 |
| TaskList | 35 | 8 | 43 |
| TaskGet | 35 | 8 | 43 |
| seq-thinking | 35 | 8 | 43 |
| WebSearch | 5 | 0 | 5 |
| WebFetch | 5 | 0 | 5 |
| tavily | 16 | 0 | 16 |
| context7 | 13 | 0 | 13 |

**Note:** spec-reviewer and code-reviewer have NO Write tool — they communicate results via SendMessage only.
