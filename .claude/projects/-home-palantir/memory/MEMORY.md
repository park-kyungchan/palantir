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

### Environment: Claude Code CLI (2026-02-19 verified)
- **Claude Code CLI (tmux)**: Agent Teams tmux mode. Reads CLAUDE.md as constitution. Full pipeline with spawned teammates.
- teammateMode: tmux (settings.json) — verified 2026-02-19 via actual spawn test

### MCP Server Config [RESOLVED 2026-02-18]
- Root cause: CC reads MCP from `.claude.json`, not `settings.json`. Fix applied, 5/5 connected, in-process 4/4 PASS.
- Details: `memory/mcp-diagnosis.md`

### Verification-First Rule (2026-02-18)
- **Anti-pattern**: Modifying documentation based on unverified claims, even when "correcting" previous errors
- **Rule**: Corrections are also claims. External docs/community sources contradicting current conclusions do NOT exempt from empirical verification
- **Pattern**: Observe → Hypothesize → Test → Verify → THEN document
- **Trigger**: Any time Lead is about to update CLAUDE.md, ref cache, or MEMORY.md with behavioral claims

## Current INFRA State (v12.0+PDA, 2026-02-19)

| Component | Version | Size | Key Feature |
|-----------|---------|------|-------------|
| CLAUDE.md | v11.0 | 55L | Protocol-only + §2.0 Phase Defs + §2.1 CE + 45 pipeline + 20 web-design skills |
| Agents | v10.9+CE | 8 files | +coordinator.md +agent-organizer.md. All 6 INFRA have Completion Protocol |
| Skills | v12.0+PDA | 79 dirs | 49 INFRA + 20 web-design + 10 crowd_works. Budget: ~56,000/56,000 |
| Resources | 6 files | shared | .claude/resources/: phase-aware-execution, dps-construction-guide, failure-escalation-ladder, output-micro-signal-format, transitions-template, quality-gate-checklist |
| Settings | v11.0 | ~110L | SLASH_COMMAND_TOOL_CHAR_BUDGET: 56000 |
| Hooks | 16 scripts | ~420L | +block-web-fallback.sh +on-mcp-failure.sh |
| Conventions | DELETED | 0L | Content distributed: agent bodies (SendMessage), CLAUDE.md §2.1 (isolation), skill L2 (output) |
| Agent Memory | -- | 7 files | +rsi-ce-diagnosis.md (342L, CE health 3/10→~7/10) |

### Architecture (v12 3-Stage Progressive Disclosure)
- **Stage 1 (Metadata)**: YAML frontmatter — auto-loaded at session start (discovery)
- **Stage 2 (Instructions)**: L2 body ≤200L — loaded on invocation (activation)
- **Stage 3 (Resources)**: `resources/methodology.md` — zero token cost until Read (execution)
- **Shared resources**: `.claude/resources/` — 6 protocol files linked from all skills
- **Routing**: Skill L1 auto-loaded in system-reminder, Agent L1 auto-loaded in Task tool definition
- **CLAUDE.md**: Protocol-only (55L), zero routing data — all routing via auto-loaded metadata
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
| BUG-006 | MEDIUM | `allowed-tools` in skill/agent frontmatter NOT_ENFORCED at runtime (CC #18837) | Remove field; use `tools` in agent frontmatter |
| BUG-007 | MEDIUM | Global hooks fire in ALL contexts (lead+teammates+subagents) | session_id guard pattern in command hooks |
| BUG-008 | LOW | SubagentStop prompt hooks cannot block termination (CC #20221) | Use command-type hooks for SubagentStop |

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

### Phase Efficiency + Meta-Cognition -- DONE (2026-02-15)
L1 CE/PE bulk (44 skills), 4-dimension pattern, CLAUDE.md protocol-only (55L), homeostasis system (5 skills), self-describing frontmatter routing. Details: `memory/meta-cognition-infra.md`

### INFRA Health Repair -- DONE (2026-02-17)
CC runtime 5건 실증 검증 후 3-wave 수리. 72%→94% health. PR #59 (da232ba).
- Verifications: allowed-tools NOT_ENFORCED, Stop prompt BROKEN, memory:none INVALID, TaskCompleted prompt NOT_SUPPORTED, global hooks fire EVERYWHERE
- Wave 1: 45 skills metadata/allowed-tools, Stop prompt→command (~$0.35/session savings), orphans, session_id guards
- Wave 2: ref_hooks §8.5-8.6 + §9, ref_agents memory default, CC_SECTIONS R9, counts
- Wave 3: manage-skills phantom refs (4 skills)
- Net: 57 files, +92/-503

### ECC Integration + Evaluation Criteria -- DONE (2026-02-18)
- ECC plugin pruned: 43→12 items (4 agents, 3 commands, 5 skills). scope: user.
- 13 rules promoted to `~/everything-claude-code/.claude/rules/` (common/ 8 + typescript/ 5).
- New skill: `evaluation-criteria` (P2 research domain, CDST methodology, Lead-direct).
- CLAUDE.md §5 Agent Teams section enhanced with isolation/shared table, file-based architecture detail.
- ECC upstream PR: affaan-m/everything-claude-code#245 (prune 530+ files, -111K lines).

### CC 2.1.45 INFRA Reflection -- DONE (2026-02-18)
- Sonnet 4.6 added to R7 (model ID: claude-sonnet-4-6, aliases updated)
- 3 bugs RESOLVED: #23561 (Agent Teams Bedrock/Vertex tmux env), #22087 (Task tool crash), #21654 (macOS sandbox)
- +spinnerTipsOverride setting (R2), --add-dir enabledPlugins support (R2)
- Skill subagent compaction fix + budget 2% scaling confirmed (R4)
- 6 files, 15 edits, all verified dates → 2026-02-18

### L2 Body Design -- DONE (2026-02-15)
44 INFRA skills L2 CE/PE optimized. PR #53. Budget: 48K→56K. All 44: DPS 5-field, tier DPS, Decision Points, maxTurns, Anti-Patterns >=3.

### D11-D17 Skill Patch -- DONE (2026-02-18)
48 INFRA skills patched. PR #61 (b3cecb2). D17 path migration, D12 escalation, D11 context, D15 iteration. +manage-skill, +walkthrough.

### Web Design Template Skills -- DONE (2026-02-18)
20 web-* skills extracted from portfolio.html. 3-layer architecture: Foundation (1) + Atoms (9) + Organisms (10).
- Foundation: `web-design-tokens` (oklch, @property, glass morphism, 3 palette variants)
- Atoms: glass-card, chip, progress-bar, nav-dots, scroll-progress, floating-orbs, icon-badge, status-badge, code-block
- Organisms: hero-section, card-grid, section-wrapper, split-layout, stat-dashboard, cta-section, dual-panel, gap-matrix, deep-dive, pipeline-steps
- Modern CSS/JS: oklch, CSS Scroll-Driven Animation, WAAPI, Container Queries, IntersectionObserver
- Agent Teams pipeline: 6 teammates (atoms-a/b, orgs-b/c, orch-enhance), 11 tasks, OOM crash recovery
- orchestrate-* 5-GAP enhancement + CLAUDE.md §2.0 Phase Definitions added
- Stale reference fix: plan-strategy→plan-behavioral, plan-interface→plan-relational, plan-decomposition→plan-static (9 files)
- Commit: 66e0cae (75 files, +9,983/-153)

### 3-Stage PDA Optimization -- DONE (2026-02-19)
44 INFRA SKILL.md ≤200L + 44 resources/methodology.md + 6 shared .claude/resources/. Commit ab8c885.
- All 9 phase domains: Pre-Design(3), Design(3), Research(8), Plan(4), Plan-Verify(5), Orchestrate(5), Execution(5), Verify(3+1pilot), Homeostasis(5), Cross-cutting(3)
- RSI loop: self-diagnose scan (81% health) + manage-skill 400L→184L fix
- New skill: doing-like-agent-teams (`context:fork` + coordinator, single-session COMPLEX-tier mirror; resources/methodology.md: P0→P8 DPS templates + state file + recovery)
- 138 files, +11,757/-7,615

### RSIL Pilot — verify-ui-* SRP Skills DONE (2026-02-19)
28 findings (9H/8M/11L). Wave 1: 6 files — added Execution Model, Methodology DPS, Transitions, D17 to all 5 verify-ui-* skills + browser-verifier.md. Wave 2: rsil/SKILL.md (Lead RECEIVE anti-pattern), rsil/resources/methodology.md (Lead Anti-Patterns table), CLAUDE.md §3 (scope note: TaskOutput(block:true) = Data Relay Tax). Key insight: Data Relay Tax applies in ALL modes (DLAT, RSIL, pipeline, direct). Health: 28 findings resolved.

### Math Portfolio Pipeline -- RESTART FROM P2 (2026-02-18)
COMPLEX tier (P0→P8). Freewheelin (MathFlat) 정수론 문제은행 포트폴리오.
- **Previous P0-P3 artifacts**: `~/tmp/math-portfolio-handoff/` (5 files + HANDOFF.md)
- **Restart**: P2 Research부터 fresh context. New PT needed.

## Session History

Branch: `main`. Latest commit: ab8c885.
- ab8c885: 3-Stage PDA for 44 INFRA skills + doing-like-agent-teams skill (138 files)
- c892d93: PR #62 — 20 web design template skills + stale ref fix + MEMORY.md archive
- b3cecb2: D11-D17 design decision patches across 48 INFRA skills + cleanup, PR #61
- 583de23: ECC integration + evaluation-criteria skill + CLAUDE.md §5 enhancement, PR #60
- da232ba: Health repair — CC runtime verified, 57 files, PR #59
- 59cae35: Merge branch 'infra' (cc-reference + MEMORY.md into main)
- 9e35a4c: MEMORY.md L2 Body Design COMPLETE
- b596365: cc-reference cache-first rule + 6 missing memory files tracked
- 520c772: Merge PR #53 (L2 Body CE/PE Optimization)
- 798b9dc: L2 Body CE/PE Optimization (50 files, +2930/-1110, 44 skills L2 optimized)
- c768d37: crowd_works Pipeline B skills (3 new, 7→10 total)
- f24b294: Phase Efficiency Optimization + L1 CE/PE bulk (61 files, +19/-8 skills, 44 L1 optimized)
- Previous on `test`: 9830714..a153d18 (~20 commits, ~300 files)
- Full history: `memory/infrastructure-history.md`

## Topic Files Index

### CC Architecture Reference (L1/L2 Pattern)
- `memory/CC_SECTIONS.md` -- **L1 (ALWAYS READ)**: Section descriptions + routing shortcuts for all ref files
- `memory/ref_runtime_security.md` -- R1: Agentic loop, 20+ tools, permission system, sandboxing
- `memory/ref_config_context.md` -- R2: 5-layer config, CLAUDE.md, 200K context, compaction, session map
- `memory/ref_hooks.md` -- R3: 14 hook events, 3 handler types, I/O contract, exit codes, 6 scopes
- `memory/ref_skills.md` -- R4: Skill frontmatter, $ARGUMENTS, shell preprocessing, disambiguation, budget
- `memory/ref_agents.md` -- R5: Agent fields, permissionMode, memory config, subagent comparison
- `memory/ref_teams.md` -- R6: Agent Teams coordination, task sharing, inbox messaging
- `memory/ref_model_integration.md` -- R7: Model config (Opus 4.6 + Sonnet 4.6), cost benchmarks, MCP, plugins
- `memory/ref_community.md` -- R8: 10 post-Opus 4.6 community tools

### Project History & Domain
- `memory/infrastructure-history.md` -- Delivery records (INFRA v7.0, RTD, COW v2.0, RSIL), DIA evolution, Agent Teams redesign
- `memory/skill-optimization-history.md` -- SKL-001~SKL-005 detailed records
- `memory/agent-teams-bugs.md` -- BUG-001~BUG-008 details and workarounds
- `memory/ontology-pls.md` -- Ontology PLS full handoff (30+ connected docs, AD-1~AD-13)
- `memory/meta-cognition-infra.md` -- Meta-Cognition INFRA Update handoff (14 decisions)
- `memory/context-engineering.md` -- CC native field reference, context loading order, critical findings
- `memory/mcp-diagnosis.md` -- MCP server startup failure diagnosis (3/4 fail), propagation OK, root cause TBD
