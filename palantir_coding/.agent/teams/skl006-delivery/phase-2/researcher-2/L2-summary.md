# L2 Summary: INFRA Pattern Analysis + Improvement Opportunities

## Executive Summary

The .claude/ infrastructure comprises 24 core files (~4845 lines) organized into 6 categories: CLAUDE.md (172L), 6 agents (442L), 6 skills (2549L), 8 hooks (362L), 2 references (620L), and 3 settings files (691L). The NLP v6.0 conversion was thorough for CLAUDE.md, agents, and skills, but **task-api-guideline.md (536L) and 2 hook scripts still contain legacy protocol markers** — the largest remaining NLP debt. The skill files show excellent structural consistency but contain **~200+ lines of duplicated content** (Phase 0, Clean Termination, Cross-Cutting) that could be extracted to a shared reference. The global-context.md → PERMANENT Task migration is incomplete — brainstorming-pipeline still creates GC as primary artifact.

## Detailed Findings

### 1. CLAUDE.md (172 lines) — Well-Structured, One Dead Reference

The Team Constitution v6.0 is clean, well-organized (§0-§10), and uses natural language throughout. Effective structure: Pipeline table, Role definitions, Communication flows, Safety rules, Recovery procedures, Integrity Principles. **One issue:** §10 line 155 references "Archive to MEMORY.md + ARCHIVE.md at work end" — ARCHIVE.md is never defined anywhere in the infrastructure. This is either a dead reference or an unimplemented feature that Phase 9 should operationalize.

### 2. Agent Files (6 files, 442 lines) — Consistent with Minor Gaps

All 6 agents share a consistent pattern: YAML frontmatter (name, description, model, permissionMode, memory, color, maxTurns, tools, disallowedTools) + Role + Before Starting Work + Probing Questions + How to Work + Output Format + Constraints.

**Strengths:** Uniform `disallowedTools: [TaskCreate, TaskUpdate]`, consistent L1/L2/L3 output format, role-appropriate tool lists.

**Issues:**
- **researcher.md tool mismatch**: The agent system definition for "researcher" shows it gets `Write, Edit` tools, but the .md file frontmatter lists Read/Glob/Grep/WebSearch/WebFetch/TaskList/TaskGet/MCP only (no Write/Edit). The system definitions override .md frontmatter for tool access. However, the body text says "Read-only access to prevent accidental mutations" which conflicts with the system-level Write+Edit access.
- **maxTurns variance undocumented**: devils-advocate=30, researcher/architect/tester=50, implementer/integrator=100. The rationale is clear (work intensity) but not documented.
- **tester.md** lists Write (for test files) but not Edit — intentional and correct for "create tests, don't modify source."

### 3. Skill Files (6 files, 2549 lines) — Largest DRY Opportunity

Skills are the largest INFRA category. All 5 pipeline skills share an excellent common structure: frontmatter → announcement → core flow → when to use → dynamic context → Phase 0 → phase-specific sections → clean termination → cross-cutting → key principles → never.

**DRY Violations (quantified):**

| Repeated Pattern | Lines per Skill | x5 Skills | Total Waste |
|-----------------|-----------------|-----------|-------------|
| Phase 0 PT Check | ~28 | 5 | ~112 lines |
| Clean Termination | ~15 | 5 | ~60 lines |
| Cross-Cutting Sequential Thinking | ~8 | 5 | ~32 lines |
| Error Handling table | ~10 | 5 | ~40 lines |
| Compact Recovery | ~3 | 5 | ~12 lines |
| Dynamic Context (common commands) | ~5 | 5 | ~20 lines |
| **TOTAL** | | | **~276 lines** |

Extracting these to a shared reference (e.g., `references/skill-common-patterns.md`) could reduce each skill by ~60 lines and total skill lines by ~220+.

**global-context.md Legacy:** brainstorming-pipeline still creates GC-v1→v3 as its primary artifact, with PERMANENT Task as a parallel system. The skills after brainstorming (write-plan, validation, execution, verification) also reference GC versions. This dual-track (GC + PT) adds complexity. Full PT migration would simplify by having one source of truth.

### 4. Hook Scripts (8 files, 362 lines) — Functional but Legacy Markers

All hooks follow a consistent pattern: read JSON stdin, parse with jq, log to .agent/teams/, output structured JSON.

**NLP v6.0 Violations:**
- `on-session-compact.sh`: Uses `[DIA-RECOVERY]`, `[DIRECTIVE]+[INJECTION]`, `[STATUS] CONTEXT_RECEIVED` — old protocol markers
- `on-subagent-start.sh`: Uses `[DIA-HOOK]` prefix — legacy marker

**Functional Assessment:**
- `on-teammate-idle.sh` + `on-task-completed.sh`: L1/L2 validation gates (exit 2 blocking) — effective
- `on-subagent-start.sh`: PT/GC context injection — complex 3-path logic, works but has legacy branch for GC
- `on-subagent-stop.sh`: L1/L2 existence check + logging — effective
- `on-pre-compact.sh`: Task snapshot preservation — effective
- `on-task-update.sh`: Simple logging — lightweight
- `on-tool-failure.sh`: Failure logging — lightweight

**Missing Hook Opportunities:**
- No `PostToolUse(TaskCreate)` hook — could validate comprehensive task descriptions per §3
- No pre-commit hook — Phase 9 could benefit from commit message validation

### 5. Settings (3 files, 691 lines)

- `settings.json` (133L): Core config with hooks, permissions, plugins. Well-structured. **Security concern:** Contains API keys/PATs for GitHub MCP and Tavily in plaintext project config. These should be in environment variables.
- `settings.local.json` (22L): Permission overrides. Clean.
- `.claude.json` (536L): Auto-generated stats, skill usage, migration flags. No action needed.

### 6. References (2 files, 620 lines)

- `agent-common-protocol.md` (84L): Clean, concise, NLP-native. Good.
- `task-api-guideline.md` (536L): **The largest NLP debt in the infrastructure.** Contains 32+ protocol markers: `[DIRECTIVE]`, `[STATUS]`, `[IMPACT-ANALYSIS]`, `[IMPACT_VERIFIED]`, `[VERIFICATION-QA]`, `[CHALLENGE]`, `[CHALLENGE-RESPONSE]`, `[ACK-UPDATE]`, `[CONTEXT-UPDATE]`, `[RE-EDUCATION]`, `[IMPACT_REJECTED]`, `[IMPACT_ABORT]`, etc. §11 (DIA Enforcement Protocol) alone is ~220 lines of ceremony-heavy protocol (DIAVP tiers, LDAP challenge categories, RC-01~10 checklists). The CLAUDE.md and skills now embed verification naturally — much of §11-§14 is redundant with the NLP v6.0 approach already in place.

### 7. Phase 9 Delivery Analysis

**What exists:**
- CLAUDE.md §2 defines Phase 9 as "Delivery | POST-EXEC | Lead only | medium"
- CLAUDE.md §10 says "Archive to MEMORY.md + ARCHIVE.md at work end"
- verification-pipeline outputs "Phase 9 Entry Conditions" in its clean termination
- Each skill's clean termination pattern: shutdown teammates → TeamDelete → preserve artifacts → output summary with "Next: Phase N"

**What doesn't exist:**
- No ARCHIVE.md definition or template anywhere
- No commit/PR automation or guidelines specific to Phase 9
- No PT → MEMORY.md migration procedure
- No session cleanup procedure (which .agent/teams/ files to keep vs delete)
- No pre-compact snapshot cleanup (29+ files accumulating in .agent/teams/)

**Phase 9 Operations (derived from analysis):**
1. **Final PT Update** — Mark all phases COMPLETE, add final metrics
2. **PT → MEMORY.md Migration** — Extract durable lessons from PT into project MEMORY.md
3. **ARCHIVE.md Creation** — Full pipeline record (all gate records, key decisions, metrics)
4. **Git Operations** — Stage, commit, optionally PR (per CLAUDE.md §8 safety)
5. **Session Cleanup** — Archive .agent/teams/ artifacts, clean pre-compact snapshots, clean task list
6. **User Summary** — Final report with all deliverables, metrics, lessons learned

### 8. Layer 2 Readiness Assessment

**Ready:** Phase pipeline, agent types, L1/L2/L3, PT template, skill frontmatter — all domain-agnostic.

**Needs Change:** Hardcoded paths (`/home/palantir`, `docs/plans/`, `.agent/teams/`), domain-specific gate criteria (CH-001 exemplar reference in write-plan), GAP-001~005 codes in task-api-guideline.

**Not a Blocker:** These are all config-level changes, not architectural. Layer 2 can be added alongside without restructuring the pipeline.

## Cross-Impact Matrix

| Finding | CLAUDE.md | Agents | Skills | Hooks | task-api | Protocol |
|---------|-----------|--------|--------|-------|----------|----------|
| IMP-001 task-api NLP | | | | | PRIMARY | |
| IMP-002/003 hook NLP | | | | PRIMARY | | |
| IMP-004 ARCHIVE.md | NEEDS FIX | | | | | Phase 9 |
| IMP-005 Phase 0 DRY | | | PRIMARY | | | New ref |
| IMP-006 GC→PT migration | | | PRIMARY | AFFECTED | | Design |
| IMP-009 §11 trim | | | | | PRIMARY | |
| IMP-011 API keys | | | | | | Security |

## Prioritized Recommendations

1. **task-api-guideline.md NLP conversion** — Highest impact, 530L→~200L possible by removing §11-§14 protocol ceremony that skills now handle natively
2. **Hook NLP conversion** — Quick win, 2 files, ~10 changed lines
3. **Skill DRY extraction** — Create `references/skill-common-patterns.md` with Phase 0, Clean Termination, Cross-Cutting, Error Handling templates
4. **ARCHIVE.md design** — Define template for Phase 9 delivery skill
5. **GC→PT migration path** — Plan for brainstorming-pipeline to use PT-only (medium-term)
6. **API key extraction** — Move to env vars (security hygiene)

## MCP Tools Usage Report

MCP tools were NOT required for this research — all analysis was internal .claude/ infrastructure audit using local file reads, Grep pattern analysis, and Bash line counts. This matches the pattern documented in my persistent memory: "For internal .claude/ audits, MCP external tools are NOT needed."
