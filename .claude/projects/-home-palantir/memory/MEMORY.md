# Claude Code Memory

## Permanent Rules

### Language Policy (2026-02-07)
- User-facing conversation: Korean only
- All technical artifacts: English only

### Empirical Verification Mandate (2026-02-20) ← CRITICAL
- ALL INFRA decisions = empirical verification first
- Pattern: Observe → Hypothesize → Test → Verify → THEN implement
- Corrections are also claims → same verification required
- Verified references: `~/.claude/references/` (NOT memory/ref_*.md — all deprecated)

### Task API Verified Behavior (2026-02-20) ← CRITICAL
- **metadata is WRITE-ONLY**: stored on disk, NOT returned by TaskGet or TaskList
- TaskList returns: id, subject, status, owner, blockedBy
- TaskGet returns: id, subject, status, description, blockedBy
- Lead reads metadata via: `Read("~/.claude/tasks/{LIST_ID}/{id}.json")`
- Full details: `~/.claude/references/task-api-verified.md`

### Agent tools Field (2026-02-20) ← VERIFIED
- `tools` field in agent .md IS enforced (agents get ONLY listed tools)
- `Task(analyst, researcher)` syntax = SILENTLY DROPPED by runtime
- Agents without `model` field inherit Lead's model (Opus = 10x cost)

### TaskOutput 절대금지 (2026-02-19)
- `TaskOutput` tool call is PERMANENTLY PROHIBITED for Lead
- Pattern: `run_in_background:true` → auto-notification → Read output file if needed

### Lead Orchestration Intelligence = Description Engineering (2026-02-20) ← CORE
- Lead's primary value = writing agent-optimized task descriptions
- DPS = minimal (per-Agent profile: OBJECTIVE+PLAN or OBJECTIVE+READ+OUTPUT)
- Description (TaskGet) = comprehensive, self-contained, dependency-aware
- Agent body (stable) + DPS (task-unique) = no overlap, no waste
- **DPS token = agent work token 감소** → minimize DPS, maximize agent working memory
- Per-Agent DPS profiles: infra-impl OBJ+PLAN, analyst OBJ+READ+OUTPUT, coordinator OBJ+INPUT+OUTPUT

### Phase-Gated Skill Loading (2026-02-20)
- Load ONLY current phase's skills → spawn → DONE → next phase
- Phase-to-domain: `~/.claude/CLAUDE.md` §2.0 Phase Definitions table

### CE Hooks (2026-02-20)
- 4 runtime hooks: ce-pre-read-section-anchor, ce-pre-grep-optimize, ce-post-grep-guard, ce-pre-grep-block (BLOCKING)

## INFRA v15 COMPLETE (2026-02-20)
- W1: Agent files (model:sonnet ×4, coordinator rework, delivery-agent fix, resource paths, coordinator MEMORY)
- W2: DLAT SKILL.md + methodology.md (state.md→PT, DLAT_BASE→WORK_DIR, per-Agent DPS)
- W3: CLAUDE.md §3-§5 + dps-construction-guide.md (PT 3-tier, DPS reform, metadata→description)
- Skill audit: freewheelin deleted, pipeline-resume→disabled
- Architecture: v15 = PT description as primary state + per-Agent DPS profiles + 3-Tier Data Access

### Key Decisions
- D01: 3-Tier Data Access (TaskList/TaskGet/Read)
- D02: metadata = Lead-only disk Read
- D03: tool-level enforcement > DPS-level > prompt-level
- D04: DPS에 Task API context 불필요 (tool 없는 agent에게는 noise)
- D05: DLAT projects/ → tasks/{LIST_ID}/outputs/ 통합
- D06: PT description = primary state, metadata = secondary (Read-only)

## Active Topics

### Math Portfolio (PAUSED)
- math-problem-design-v3.html MS version: PAUSED pending INFRA v15
- math-question-bank W4: P6 PASS, DB push pending
- Details: `memory/math-question-bank.md`

### Ontology Communication Protocol [ALWAYS ACTIVE]
4-step pattern: TEACH → IMPACT ASSESS → RECOMMEND → ASK

## Topic Files Index
- `~/.claude/references/task-api-verified.md` — Task API empirical evidence
- `memory/pipeline-bugs.md` — BUG-001~BUG-008
- `memory/math-question-bank.md` — Math portfolio details
- `memory/infrastructure-history.md` — Delivery history
- `memory/grep-optimization-handoff.md` — Grep CE optimization
