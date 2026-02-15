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

## Current INFRA State (v11.0-L2opt, 2026-02-15)

| Component | Version | Size | Key Feature |
|-----------|---------|------|-------------|
| CLAUDE.md | v11.0 | 55L | Protocol-only + §2.1 CE + 44 skills (8 pipeline + 5 homeostasis + 3 cross-cutting) |
| Agents | v10.9+CE | 6 files | All 6 have Completion Protocol section (SendMessage on task completion) |
| Skills | v11.0+L2opt | 54 dirs | 44 INFRA + 10 crowd_works. All 44 L1+L2 CE/PE optimized. Budget: ~47,000/56,000 (16% headroom) |
| Settings | v11.0 | ~110L | SLASH_COMMAND_TOOL_CHAR_BUDGET: 56000 |
| Hooks | 8 scripts | ~380L | 6 global events + 5 agent-scoped hooks (SRC moved to agent scope) |
| Conventions | v11.0 | ~60L | +SendMessage signal format + error taxonomy + checkpoint micro-format |
| Agent Memory | -- | 7 files | +rsi-ce-diagnosis.md (342L, CE health 3/10→~7/10) |

### Architecture (v10 Native Optimization)
- **Routing**: Skill L1 auto-loaded in system-reminder, Agent L1 auto-loaded in Task tool definition
- **L1 (frontmatter)**: WHEN/DOMAIN/INPUT_FROM/OUTPUT_TO/METHODOLOGY -- routing intelligence, 1024 chars max
- **L2 (body)**: Execution Model + Methodology (5 steps) + Quality Gate + Output -- loaded on invocation
- **CLAUDE.md**: Protocol-only (43L), zero routing data -- all routing via auto-loaded metadata
- **Lead**: Pure Orchestrator, never edits files directly, routes via skills+agents

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

### RSI CE -- DONE (2026-02-15)
Context Engineering RSI Loop: 3 iterations, 22/22 findings resolved. Health 3/10 → 9/10.
- Iter 1 (034e925): 6 agents + conventions.md + 3 TaskOutput fixes
- Iter 2 (7c13807): 16 P2-P8 skill Delivery lines + residual
- Iter 3 (729157d): 6 homeostasis Phase-Aware + Delivery + CE optimization (A/B/D/F)
- 10/10 gap: micro-signal format runtime validation pending (next COMPLEX pipeline)

### Phase Efficiency Optimization -- COMPLETE (2026-02-15)
4-dimension pattern + L1 CE/PE bulk optimization. Two phases:
- **Pilot** (6 agents): +19 new, -8 deleted, +11 net. 44 INFRA + 7 crowd_works = 51 total.
- **L1 CE/PE** (4 teammates T1-T4): All 44 INFRA L1 descriptions optimized.
  - Canonical structure: `[Phase·Domain·Role] UniqueVerb` → WHEN → DOMAIN → INPUT_FROM → OUTPUT_TO → METHODOLOGY
  - 44 unique verbs, zero within-domain collisions
  - conventions.md: +SendMessage signal format, +error taxonomy (4 types), +checkpoint micro-format
  - 3 stale refs fixed (design-architecture, design-interface, design-risk)
  - 3 DMI:true flags (brainstorm, task-management, pipeline-resume) — self-diagnose already false
  - Budget: 47 auto-loaded skills = 44,138 chars / 48,000 budget (8% headroom)
  - 10 over-1024 skills trimmed → 0 INFRA violations

### Meta-Cognition INFRA Update -- Largely Implemented (2026-02-14)
Core ideas from meta-cognition brainstorming have been implemented in v10:
- CLAUDE.md Protocol-Only transition: DONE (43L)
- Homeostasis System: DONE (manage-infra + manage-skills + 5 verify-* skills)
- Self-describing components (frontmatter routing): DONE (31 skills with full L1/L2)
- Root Exemption Zone concept: Applied in manage-skills self-management detection
Remaining: Enhanced Frontmatter v2 (routing/meta_cognition blocks) NOT adopted -- using native fields only.
Details: `memory/meta-cognition-infra.md`

### L2 Body Design -- COMPLETE (2026-02-15)
All 44 INFRA skills L2 bodies CE/PE optimized. Commit 798b9dc on `infra` branch. PR #53.
- 11 batches (B1-B9+B10a+B10b), 3 waves, 50 files, +2930/-1110
- DMI:true→false: brainstorm, task-management, pipeline-resume
- Budget: 48,000→56,000 (SLASH_COMMAND_TOOL_CHAR_BUDGET)
- All 44: DPS 5-field, tier DPS, Decision Points, maxTurns, Anti-Patterns >=3, Transitions 3 tables

## Session History

Branch: `infra`. Latest commit: 798b9dc. PR #53.
- 798b9dc: L2 Body CE/PE Optimization (50 files, +2930/-1110, 44 skills L2 optimized)
- c768d37: crowd_works Pipeline B skills (3 new, 7→10 total)
- f24b294: Phase Efficiency Optimization + L1 CE/PE bulk (61 files, +19/-8 skills, 44 L1 optimized)
- Previous on `test`: 9830714..a153d18 (~20 commits, ~300 files)
- Full history: `memory/infrastructure-history.md`

## Topic Files Index
- `memory/infrastructure-history.md` -- Delivery records (INFRA v7.0, RTD, COW v2.0, RSIL), DIA evolution, Agent Teams redesign
- `memory/skill-optimization-history.md` -- SKL-001~SKL-005 detailed records
- `memory/agent-teams-bugs.md` -- BUG-001~BUG-004 details and workarounds
- `memory/ontology-pls.md` -- Ontology PLS full handoff (30+ connected docs, AD-1~AD-13)
- `memory/meta-cognition-infra.md` -- Meta-Cognition INFRA Update handoff (14 decisions)
- `memory/context-engineering.md` -- CC native field reference, context loading order, critical findings
- `memory/cc-reference/` -- Machine-readable CC native reference (5 files):
  - `native-fields.md` -- Skill + Agent frontmatter field tables, flag combos, permissionMode details
  - `context-loading.md` -- Session loading order, L1 budget, invocation flow, compaction, context budget
  - `hook-events.md` -- All 14 hook events, types, input/output format, matchers, our configuration
  - `arguments-substitution.md` -- $ARGUMENTS, dynamic context injection, env vars, argument-hint
  - `skill-disambiguation.md` -- Sub-skill naming (flat only, 64 chars), semantic disambiguation, incremental cache, L1 budget impact
