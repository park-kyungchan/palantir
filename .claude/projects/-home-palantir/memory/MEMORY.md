# Claude Code Memory

## Permanent Rules

### Language Policy (2026-02-07)
- User-facing conversation: Korean only
- All technical artifacts: English only

### Phase-Gated Skill Loading (2026-02-20) ← CRITICAL CE RULE
- **Anti-pattern**: Reading ALL phase skills at once (P1+P2+P3 loaded together = context waste)
- **Correct pattern**: Load ONLY current phase's skills → spawn → DONE → next phase
- **Command**: `sed -n '/^---$/,/^---$/p' ~/.claude/skills/$skill/SKILL.md | head -20`
- **Phase-to-domain mapping**: Use grep to find §2.0 Phase Definitions (see Pipeline Flow Reference)
- Example: P1 → read `design-*` L1 only. P2 → read `research-*` + `audit-*` L1 only.

### Pipeline Flow Reference [ALWAYS READ BEFORE SPAWNING]
- **Canonical source**: `~/.claude/CLAUDE.md` §2.0 Phase Definitions table (P0-P8 + skills per phase)
- Before spawning: `grep -n "2.0 Phase Definitions" ~/.claude/CLAUDE.md` → get line N → `Read CLAUDE.md offset:N limit:20`
- **P2 full skill set**: research-codebase, research-external, evaluation-criteria (FIRST), audit-static, audit-behavioral, audit-relational, audit-impact → research-coordinator
- **evaluation-criteria runs FIRST** in P2, before research-codebase/external

### TaskOutput 절대금지 (2026-02-19)
- `TaskOutput` tool call is PERMANENTLY PROHIBITED for Lead
- Pattern: `run_in_background:true` → auto-notification → Read output file if needed

### Skill Optimization Process (2026-02-07)
- claude-code-guide agent research required for every skill optimization
- Process: claude-code-guide research -> design doc -> SKILL.md -> validation -> commit

### claude-code-guide Output Management (2026-02-11)
- claude-code-guide agent has NO Write tool -> output stored only in volatile /tmp
- Lead must read output immediately after completion — /tmp/ cleaned on timer
- If lost: use `resume` parameter to retrieve from agent context

### MCP Server Config [RESOLVED 2026-02-18]
- CC reads MCP from `.claude.json`, not `settings.json`. Fix applied, 5/5 connected.

### Verification-First Rule (2026-02-18)
- Corrections are also claims. Empirical verification required before updating CLAUDE.md/MEMORY.md.
- Pattern: Observe → Hypothesize → Test → Verify → THEN document

### CE Hooks (2026-02-20)
- 4 runtime hooks optimize Grep/Read token consumption
- `ce-pre-read-section-anchor.sh`: PreToolUse(Read) — section map for .md >100L (advisory, exit 0)
- `ce-pre-grep-optimize.sh`: PreToolUse(Grep) — warn missing head_limit or path (advisory, exit 0)
- `ce-post-grep-guard.sh`: PostToolUse(Grep) — warn >50 result lines (advisory, exit 0)
- `ce-pre-grep-block.sh`: PreToolUse(Grep) — BLOCK Grep without path parameter (blocking, exit 2)
- Registered in settings.json

## Current INFRA State (v13, 2026-02-20)

| Component | Version | Key Feature |
|-----------|---------|-------------|
| CLAUDE.md | v13 | 209L, Semantic Integrity INVIOLABLE block, 200-250L policy |
| Agents | v13 | 8 files (agent-organizer.md deleted), Completion Protocol |
| Skills | v13 | 87 dirs — added verify-coordinator, manage-codebase |
| Resources | 6 files | .claude/resources/ +DPS Principles in dps-construction-guide |
| Hooks | 20 scripts | +ce-pre-grep-block.sh (BLOCKING: exit 2, Grep without path) |
| Rules | CE-optimized | 4,167 chars (was 5,299), legacy refs removed |

### Architecture (v12 3-Stage Progressive Disclosure)
- Stage 1 (Metadata): YAML frontmatter — auto-loaded
- Stage 2 (Instructions): L2 body ≤200L — on invocation
- Stage 3 (Resources): `resources/methodology.md` — on-demand Read
- **Lead**: Pure Orchestrator, never edits files directly

### Known Bugs
| ID | Severity | Summary | Workaround |
|----|----------|---------|------------|
| BUG-001 | CRITICAL | `permissionMode: plan` blocks MCP tools | Always spawn with `mode: "default"` |
| BUG-002 | HIGH | Large-task teammates auto-compact before L1/L2 | Keep prompts focused |
| BUG-006 | MEDIUM | `allowed-tools` frontmatter NOT_ENFORCED (CC #18837) | Use `tools` in agent frontmatter |
| BUG-007 | MEDIUM | Global hooks fire in ALL contexts | session_id guard in command hooks |

Details: `memory/agent-teams-bugs.md`

## Active Topics

### Ontology Communication Protocol [ALWAYS ACTIVE]
Active whenever Ontology/Foundry concepts arise. User = concept-level decision-maker.
4-step pattern: **TEACH -> IMPACT ASSESS -> RECOMMEND -> ASK**

### Math Portfolio
- math-question-bank W4: P6 waves PASS, DB push pending (terminal: `pnpm --filter @freewheelin/db db:push`)
- math-problem-design.html: DLAT in progress (P2 running, DLAT_BASE: `~/.claude/doing-like-agent-teams/projects/math-problem-design-portfolio/`)
- Details: `memory/math-question-bank.md`

## Topic Files Index

### CC Architecture Reference
- `memory/CC_SECTIONS.md` -- L1 (ALWAYS READ): routing shortcuts for all ref files
- `memory/ref_hooks.md` -- R3: 14 hook events, I/O contract, exit codes
- `memory/ref_skills.md` -- R4: Skill frontmatter, $ARGUMENTS, shell preprocessing
- `memory/ref_agents.md` -- R5: Agent fields, permissionMode, subagent comparison
- `memory/ref_teams.md` -- R6: Agent Teams coordination, task sharing, inbox messaging
- `memory/ref_model_integration.md` -- R7: Model config, cost benchmarks, MCP
- `memory/agent-teams-bugs.md` -- BUG-001~BUG-008 details and workarounds
- `memory/math-question-bank.md` -- Math portfolio: D1-D24, W4 plan, DLAT_BASE refs
- `memory/infrastructure-history.md` -- Full delivery history (INFRA, RSIL, etc.)
- `memory/grep-optimization-handoff.md` -- Grep pattern audit + CE optimization results (2026-02-20)
