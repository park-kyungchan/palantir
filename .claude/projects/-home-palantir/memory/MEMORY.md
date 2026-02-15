# Claude Code Memory

## Permanent Rules

### Language Policy (2026-02-07)
- User-facing conversation: Korean only
- All technical artifacts: English only
- Rationale: token efficiency for Opus 4.6, cross-agent parsing consistency

### Skill Optimization Process (2026-02-07)
- claude-code-guide agent research required for every skill optimization
- Common improvements: Dynamic Context Injection, $ARGUMENTS, Opus 4.6 Measured Language, argument-hint frontmatter
- Per-skill improvements derived from claude-code-guide research (different each time)
- Process: claude-code-guide research -> design doc -> SKILL.md -> validation -> commit

### claude-code-guide Output Management (2026-02-11)
- claude-code-guide agent has NO Write tool -> output stored only in volatile /tmp
- **Lead must read output immediately after task completion** -- /tmp/ files are cleaned up on a timer
- If output is lost: use `resume` parameter to retrieve from agent context
- Never substitute domain knowledge for CC research -- always re-request if output is lost

### ASCII Status Visualization (2026-02-08)
- Lead outputs ASCII visualization when updating orchestration-plan.md or reporting state
- Include: phase pipeline, workstream progress bars, teammate status, key metrics

### Environment: Claude Code CLI (2026-02-13)
- **Claude Code CLI (tmux)**: Agent Teams multi-instance. Reads CLAUDE.md as constitution. Full pipeline with spawned teammates.
- teammateMode: tmux (settings.json)

## Current INFRA State (v10.9+CE, 2026-02-15)

| Component | Version | Size | Key Feature |
|-----------|---------|------|-------------|
| CLAUDE.md | v10.9+CE | 54L | Protocol-only + §2.1 CE context isolation (P2+ teammate-only, SendMessage-only) |
| Agents | v10.9+CE | 6 files | All 6 have Completion Protocol section (SendMessage on task completion) |
| Skills | v10.9+CE | 33 dirs | 32→33 (self-improve split → self-diagnose+self-implement) + 16 skills with Delivery lines |
| Settings | v10.9 | ~110L | teammateMode:tmux, alwaysThinkingEnabled, matcher expanded + tavily permission |
| Hooks | 8 scripts | ~380L | 6 global events + 5 agent-scoped hooks (SRC moved to agent scope) |
| Conventions | v10.9+CE | 44L | Context Isolation + SendMessage Completion Protocol (P2+ phases) |
| Agent Memory | -- | 7 files | +rsi-ce-diagnosis.md (342L, CE health 3/10→~7/10) |

### Architecture (v10 Native Optimization)
- **Routing**: Skill L1 auto-loaded in system-reminder, Agent L1 auto-loaded in Task tool definition
- **L1 (frontmatter)**: WHEN/DOMAIN/INPUT_FROM/OUTPUT_TO/METHODOLOGY -- routing intelligence, 1024 chars max
- **L2 (body)**: Execution Model + Methodology (5 steps) + Quality Gate + Output -- loaded on invocation
- **CLAUDE.md**: Protocol-only (43L), zero routing data -- all routing via auto-loaded metadata
- **Lead**: Pure Orchestrator, never edits files directly, routes via skills+agents

### Skills (33 total: 25 pipeline + 5 homeostasis + 3 cross-cutting)

| Domain | Skills | Phase |
|--------|--------|-------|
| pre-design | brainstorm, validate, feasibility | P0 |
| design | architecture, interface, risk | P1 |
| research | codebase, external, audit | P2 |
| plan | decomposition, interface, strategy | P3 |
| plan-verify | (unified: correctness+completeness+robustness) | P4 |
| orchestration | decompose, assign, verify | P5 |
| execution | code, infra, **impact, cascade**, review | P6 |
| verify | structural-content, consistency, quality, cc-feasibility | P7 |
| homeostasis | manage-infra, manage-skills, manage-codebase, **self-diagnose, self-implement** | X-cut |
| cross-cutting | delivery-pipeline, pipeline-resume, task-management | P8/X-cut |

### Pipeline Tiers

| Tier | Criteria | Phases |
|------|----------|--------|
| TRIVIAL | <=2 files, single module | P0->P6->P8 |
| STANDARD | 3 files, 1-2 modules | P0->P1->P2->P3->P6->P7->P8 |
| COMPLEX | >=4 files, 2+ modules | P0->P8 (all phases) |

### Known Bugs

| ID | Severity | Summary | Workaround |
|----|----------|---------|------------|
| BUG-001 | CRITICAL | `permissionMode: plan` blocks MCP tools | Always spawn with `mode: "default"` |
| BUG-002 | HIGH | Large-task teammates auto-compact before L1/L2 | Keep prompts focused, avoid context bloat |
| BUG-004 | HIGH | No cross-agent compaction notification | tmux monitoring + protocol self-report |

Details: `memory/agent-teams-bugs.md`

## Next Topics

### Ontology Communication Protocol [ALWAYS ACTIVE] (2026-02-10)

Active whenever Ontology/Foundry concepts arise. User = concept-level decision-maker.
4-step pattern: **TEACH -> IMPACT ASSESS -> RECOMMEND -> ASK**

### Ontology PLS -- Deferred (2026-02-10)
All phases complete (P0-P3). Next: T-0 brainstorming. Details: `memory/ontology-pls.md`

### RSI CE Iter 3 -- Pending (2026-02-15)
Context Engineering RSI Loop: Iter 1+2 DONE (034e925, 7c13807). Iter 3 NOT started.
- **Remaining**: 6 homeostasis skills need phase-awareness + Delivery lines
- **Residual**: verify-cc-feasibility missing Delivery line (Iter 2 miss)
- **Residual**: self-implement "Monitor completion" implicit TaskOutput (CE-TO-04)
- **Scope**: ~8 files. After Iter 3: re-diagnose to confirm convergence.
- Diagnosis report: `agent-memory/analyst/rsi-ce-diagnosis.md` (342L, 22 findings)

### Phase Efficiency Optimization -- Pending (2026-02-15)
Deferred from v10.8 session. Candidates identified by efficiency analysis:
- **P4 Plan-Verify (4/10)**: 3 parallel analysts = redundant with P7. Consider merge to 1 skill or make optional.
- **P7 Verify (5/10)**: 5 sequential stages, mainly .claude/ only. Consider conditional execution or consolidation.
- **P2 Research audit (6/10)**: Consider COMPLEX-only.
- **P1 Design interface+risk (7/10)**: Consider STANDARD running architecture-only.
- **P3 Plan strategy (7/10)**: Consider STANDARD running decomposition-only.
Scope: Structural pipeline change — skill deletion/merging, tier path optimization.

### Meta-Cognition INFRA Update -- Largely Implemented (2026-02-14)
Core ideas from meta-cognition brainstorming have been implemented in v10:
- CLAUDE.md Protocol-Only transition: DONE (43L)
- Homeostasis System: DONE (manage-infra + manage-skills + 5 verify-* skills)
- Self-describing components (frontmatter routing): DONE (31 skills with full L1/L2)
- Root Exemption Zone concept: Applied in manage-skills self-management detection
Remaining: Enhanced Frontmatter v2 (routing/meta_cognition blocks) NOT adopted -- using native fields only.
Details: `memory/meta-cognition-infra.md`

## Session History

### SRP Optimization Pipeline + RSI CE (2026-02-15, branch: test)
Full COMPLEX pipeline (P0→P8) for SRP Optimization (6 targets, 20+ files).
- **SRP Pipeline** (9830714): P0-P5 complete, P6 4 waves (conventions.md, verify WHEN, SRC persistence, dashboard+self-improve split, hook pipeline state, sync-dashboard 3 new functions, template.html 4 enrichments), P7 verify, P8 delivery. 26 files, +1807/-307.
- **RSI CE Iter 1** (034e925): Completion Protocol added to all 6 agents, conventions.md SendMessage spec, 3 explicit TaskOutput refs fixed. 12 files.
- **RSI CE Iter 2** (7c13807): Delivery lines in 16 P2-P8 skill DPS templates (11 standard + COMPLEX variants), cascade/review implicit TaskOutput fixes. 16 files.
- **RSI CE Iter 3**: NOT STARTED. 8 files remaining (6 homeostasis + verify-cc-feasibility residual + self-implement fix). See Next Topics.
- Key architectural decision: §2.1 CE protocol — P2+ must use team_name, Lead uses SendMessage (not TaskOutput), 3-channel orchestration.

### Earlier Sessions (2026-02-14~15, branch: test)
Consolidated to `memory/infrastructure-history.md`. Summary:
- v10.1: L2 bodies for 30 skills. v10.2: CC native compliance. v10.3: Description quality.
- v10.4: SRC (impact/cascade). v10.5: RSI 5 iters (9.2/10). v10.6: Integration deep-dive.
- RSI L3-L6: Progressive deep-dive (structure→integration→logic→CE/PE→dashboard→transitions).
- v10.8: Phase renumbering P0-P8. Dashboard build. v10.9: CC native optimization 4 phases.
- Total: ~300 files changed across ~20 commits on test branch.

## Topic Files Index
- `memory/infrastructure-history.md` -- Delivery records (INFRA v7.0, RTD, COW v2.0, RSIL), DIA evolution, Agent Teams redesign
- `memory/skill-optimization-history.md` -- SKL-001~SKL-005 detailed records
- `memory/agent-teams-bugs.md` -- BUG-001~BUG-004 details and workarounds
- `memory/ontology-pls.md` -- Ontology PLS full handoff (30+ connected docs, AD-1~AD-13)
- `memory/meta-cognition-infra.md` -- Meta-Cognition INFRA Update handoff (14 decisions)
- `memory/context-engineering.md` -- CC native field reference, context loading order, critical findings
- `memory/cc-reference/` -- Machine-readable CC native reference (4 files):
  - `native-fields.md` -- Skill + Agent frontmatter field tables, flag combos, permissionMode details
  - `context-loading.md` -- Session loading order, L1 budget, invocation flow, compaction, context budget
  - `hook-events.md` -- All 14 hook events, types, input/output format, matchers, our configuration
  - `arguments-substitution.md` -- $ARGUMENTS, dynamic context injection, env vars, argument-hint
