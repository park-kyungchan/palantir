# Skill Optimization v9.0 — All Skills Deep Redesign

> **Phase:** 1 (Discovery) — Gate 1 APPROVED
> **Pipeline Tier:** COMPLEX
> **Date:** 2026-02-12
> **Skills:** 9 (excluding palantir-dev)

---

## 1. Decisions Made (Phase 1 Q&A)

| # | Decision | Rationale |
|---|----------|-----------|
| D-1 | Exclude palantir-dev (9 skills only) | Non-pipeline learning skill, unrelated to INFRA optimization |
| D-2 | All Deep Redesign (no tiering) | User: "현재 INFRA에 가장 최적화 되도록" — README.md as ground truth |
| D-3 | A+B only (Spawn Order + Prompt Template) | Lead's Orchestration Define = spawn sequence + directive content. Gate/Error/Communication delegated to CLAUDE.md |
| D-4 | No compression target | v9.0 alignment focus, YAGNI only constraint |
| D-5 | Common 1x CC research | Shared Agent Teams spawn mechanism research, not per-skill |
| D-6 | Option A: Precision Refocus | Spawn + Directive + Interface centered restructure. Remove CLAUDE.md duplication |
| D-7 | PT-centric interface | GC → session scratch. PT = sole cross-skill source of truth |
| D-8 | Big Bang (simultaneous) | All 9 skills changed at once. Interface consistency guaranteed |
| D-9 | 4 Lead-only skills → context:fork | delivery, rsil-global, rsil-review, permanent-tasks isolated in subagent |
| D-10 | CLAUDE.md §10 rule modification | Fork agent Task API allowed ("Lead-delegated fork agents" exception) |
| D-11 | 3 new fork-context agent .md files | delivery-agent, rsil-agent, pt-manager (new agents for context:fork) |

## 2. Agent Teams Spawn Mechanism (Confirmed Understanding)

```
Lead calls Task tool
  → subagent_type: "implementer"  (→ .claude/agents/implementer.md loaded as system instructions)
  → team_name: "feature-x"       (→ joins team)
  → name: "impl-1"               (→ SendMessage identifier)
  → prompt: "[DIRECTIVE]..."      (→ first user message to agent)
  → mode: "default"              (→ permission mode, always "default" per BUG-001)
  → Result: new tmux pane, independent Claude Code instance
```

**Key constraints:**
- agent .md body = persistent system instructions (loaded with CLAUDE.md)
- prompt = one-time task directive (first user message)
- Coordinators have NO Task tool → cannot spawn agents → Lead pre-spawns workers
- Only Lead can spawn agents

## 3. Redesign Strategy: Option A (Precision Refocus)

Each skill restructured into 4 sections:

### A) Spawn Section
- Exact Task tool call parameters (subagent_type, team_name, name, mode)
- Spawn sequence (which first, which parallel)
- Tier-based branching (TRIVIAL/STANDARD/COMPLEX)
- Pre-spawn pattern (coordinator first, then workers)

### B) Directive Section (Prompt Templates)
- What to **embed** in prompt (PT content, scope, constraints)
- What to **reference** as file path (agent reads independently)
- What to **omit** (already in agent .md body)

### C) Interface Section
- **Input:** What this skill reads (PT state, previous phase L1/L2/L3)
- **Output:** What this skill produces (L1/L2/L3, PT update)
- **Next:** What the next skill needs from this skill's output

### D) Cross-Cutting (1-line references)
- Error Handling → "Per CLAUDE.md §9 and agent-common-protocol.md"
- Compact Recovery → "Per CLAUDE.md §9"
- Sequential Thinking → "All agents use sequential-thinking (per agent .md tools)"
- Understanding Verification → "Per CLAUDE.md §6"
- RTD → "Per CLAUDE.md §6 Observability"

## 4. PT-Centric Interface Model

**Before (current):**
```
bp → GC-v1 → GC-v2 → GC-v3
write-plan reads GC-v3 → GC-v4
validation reads GC-v4 → GC-v4/v5
execution reads GC-v4/v5 → GC-v5
verification reads GC-v5 → GC-v6
delivery reads GC-v6
```

**After (proposed):**
```
Each skill:
  Input:  PT-v{N} + previous phase L1/L2/L3 files
  Output: PT-v{N+1} + current phase L1/L2/L3 files
  GC:     Session-scoped scratch (spawn state, file paths, temp data only)
```

PT evolves: PT-v1 (P1) → PT-v2 (P2) → PT-v3 (P3) → PT-v4 (P4) → PT-v5 (P5) → PT-v6 (P6) → PT-v7 (P7/8) → PT-vFinal (P9)

## 5. Target Skills and Current State

| Skill | Lines | Era | Key Gaps |
|-------|-------|-----|----------|
| brainstorming-pipeline | 613L | v9.0 (P0/P1 only) | P2/P3 need Precision Refocus |
| agent-teams-write-plan | 362L | v5.0 | Full restructure needed |
| plan-validation-pipeline | 434L | v6.0 | Moderate — has NLP, needs Precision Refocus |
| agent-teams-execution-plan | 692L | v5.0 | Full restructure, longest skill |
| verification-pipeline | 574L | v6.0 | Moderate — NLP native, needs Precision Refocus |
| delivery-pipeline | 471L | v7.0 | Lead-only, needs dedup + PT interface |
| rsil-global | 452L | v7.0 | Lead-only, needs dedup |
| rsil-review | 549L | v7.0 | Lead-only, needs dedup |
| permanent-tasks | 279L | v8.0 | Light — PT template update if interface changes |

**Total current:** 4,426L across 9 skills

## 6. Scope Statement (v2 — APPROVED)

**Goal:** 9개 스킬 + 관련 에이전트를 INFRA v9.0에 정밀 정렬, Lead-only 스킬에 context:fork 격리 아키텍처 도입

**In Scope:**
- 9 SKILL.md redesigned (Precision Refocus: Spawn + Directive + Interface + Cross-Cutting)
- 8 coordinator agent .md co-optimized (hooks, skills preload, memory: project)
- 3 new agent .md created (delivery-agent, rsil-agent, pt-manager — fork context)
- 4 Lead-only skills → context:fork (delivery, rsil-global, rsil-review, permanent-tasks)
- CLAUDE.md §10 modification: Lead-delegated fork agent Task API allowed
- GC versioning → PT-centric interface
- CLAUDE.md/reference duplication removal
- CC feature adoption ($0/$1, ${CLAUDE_SESSION_ID}, allowed-tools, Dynamic Context expansion)

**Out of Scope:**
- palantir-dev skill
- 35 worker agent .md files (coordinators only)
- Reference documents (.claude/references/*.md)
- Hooks, settings

**Approach:** Precision Refocus (4-section) + context:fork revolution

**Success Criteria:**
- 9 SKILL.md with unified 4-section structure
- PT-centric interface: all skills read/write PT-v{N}
- 4 Lead-only skills context:fork isolated
- 0 CLAUDE.md duplication (all cross-cutting = 1-line reference)

**Pipeline Tier:** COMPLEX (20+ files, 3+ modules, cross-boundary interface change)

**Status:** Gate 1 APPROVED (2026-02-12)

## 7. Phase 2 Research Needs

- ~~CC research: Agent Teams spawn mechanism~~ (DONE — see §9)
- Pattern analysis: quantify duplication across 9 skills (which sections are identical)
- Interface analysis: map current GC consumption points across all skills
- context:fork prototype: permanent-tasks fork behavior verification
- Agent .md audit: 8 coordinators current state vs optimization targets

## 8. Phase 3 Architecture Needs

- Common skill template (Precision Refocus 4-section)
- PT-centric interface contract (per-skill read/write PT sections)
- Fork agent .md design (tools, permissions, memory)
- CLAUDE.md §10 modification design
- Per-skill delta from common template (unique orchestration logic)

## 9. CC Research Findings (claude-code-guide, 2026-02-12)

### 9.1 Skills System — Complete Feature Inventory

**Frontmatter fields (all supported):**

| Field | Purpose | Current Usage |
|-------|---------|---------------|
| `name` | Display name for `/slash-command` | All 9 skills ✓ |
| `description` | When to use (auto-invocation) | All 9 skills ✓ |
| `argument-hint` | Hint for expected args | Some skills ✓ |
| `disable-model-invocation` | Prevent auto-invoke | Not used |
| `user-invocable` | Hide from `/` menu | Not used |
| `allowed-tools` | Tools without asking | Not used |
| `model` | Model override | Not used |
| `context` | `fork` for subagent isolation | Not used |
| `agent` | Subagent type when `context: fork` | Not used |
| `hooks` | Skill-scoped hooks | Not used |

**Dynamic Context Injection (`!command`):**
- Preprocessed BEFORE Claude sees skill — shell commands replaced with output
- Used in brainstorming-pipeline for project structure, git log, plans list
- Execution on Lead's machine — all agents receive pre-rendered context
- Error in command → skill load failure (use `2>/dev/null || echo "{}"` for safety)

**$ARGUMENTS system:**
- `$ARGUMENTS` = full string, `$0`/`$1` = indexed args, `${CLAUDE_SESSION_ID}` = session ID
- Auto-appended as `ARGUMENTS: <value>` if not present in skill body
- Preprocessed before Claude — not variable references but literal substitutions

**Skill loading behavior:**
- Descriptions: loaded at session start (2% context window budget, ~16K char fallback)
- Full content: on-demand when invoked or auto-matched
- Discovery: .claude/skills/<name>/SKILL.md (project) → ~/.claude/skills/ (user) → plugins
- Subagent skill preloading: `skills:` in agent .md frontmatter injects full content at startup

### 9.2 Task Tool — Complete Parameter List

| Parameter | Type | Current Usage |
|-----------|------|---------------|
| `subagent_type` | string (required) | All spawns ✓ |
| `prompt` | string (required) | All spawns ✓ |
| `description` | string | All spawns ✓ |
| `team_name` | string | Team spawns ✓ |
| `name` | string | Team spawns ✓ |
| `mode` | enum | Always "default" (BUG-001) ✓ |
| `run_in_background` | boolean | Not used in skills |
| `resume` | string (agent ID) | Not used in skills |
| `model` | enum | Not used in skills |
| `max_turns` | integer | Not used in skills |

**Agent .md frontmatter (all fields):**
name, description, tools, disallowedTools, model, permissionMode, maxTurns,
skills (preload into agent), mcpServers, hooks (agent-scoped), memory (user/project/local)

### 9.3 Feasibility Assessment

| Design Element | Verdict | Confidence | Key Risk |
|----------------|---------|------------|----------|
| PT-centric interface (TaskList→TaskGet→TaskUpdate) | FEASIBLE | 85% | Task description size limits context |
| Skill-to-skill handoff via file paths | FEASIBLE | 75% | No formal artifact registry |
| Dynamic Context for session state (`!commands`) | FEASIBLE | 90% | Commands run on Lead's machine only |
| Coordinator pattern (SendMessage, no spawn) | FEASIBLE | 70% | Worker orphaning if coordinator crashes |
| Big Bang 9-skill change | FEASIBLE | 80% | Syntax error in any skill blocks all |

**PT-centric caveats:**
- Keep PT description lean (summary + YAML) — bulk data in phase directory files
- Task operations are atomic per-update but no cross-task transactions
- Recommend: PT holds pointers to L1/L2/L3 paths, not full data

**Coordinator caveats:**
- No ACK mechanism for SendMessage — polling needed
- No coordinator auto-recovery — Lead must detect and restart
- Worker orphaning risk if coordinator crashes without handoff

### 9.4 Enhancement Opportunities

| Enhancement | Verdict | Rationale |
|-------------|---------|-----------|
| Skill-scoped hooks (audit trail) | ADOPT | Coordinator hooks capture all worker tool calls |
| MCP server references in skills | ADOPT | Document MCP tools per coordinator |
| Model selection per spawn | CONSIDER | Haiku for simple tasks, Opus for architecture |
| Agent memory for coordinators | ADOPT | `memory: project` for cross-run learning |
| Global settings for skills | SKIP | Frontmatter is localized and clear enough |

### 9.5 New CC Features (2025-2026) Relevant to Redesign

| Feature | Version | Relevance |
|---------|---------|-----------|
| `${CLAUDE_SESSION_ID}` substitution | 2.1.9 | RTD/observability in skills |
| Shorthand args (`$0`, `$1`) | 2.1.19 | Cleaner skill syntax |
| Skills in `--add-dir` auto-discovered | 2.1.32 | Monorepo support |
| Skill char budget scales with context | 2.1.32 | Prevents description truncation |
| `skills:` in agent frontmatter | — | Preload skills into subagents |
| `context: fork` + `agent:` | — | Run skill in isolated subagent |
| Agent-scoped `hooks:` | — | Per-agent lifecycle automation |
| `memory: project` for agents | — | Persistent cross-session learning |
