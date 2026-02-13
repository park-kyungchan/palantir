# L2 Summary: Opus 4.6 + Claude Code CLI v2.1.37 Research

**Researcher:** researcher-1
**Date:** 2026-02-08
**Downstream Consumer:** Architect (Phase 3) — SKL-006 design + RSIL catalog

---

## Executive Summary

Opus 4.6 introduces three transformative capabilities for our infrastructure: **adaptive thinking with effort controls**, **server-side compaction**, and **128K output tokens**. Claude Code v2.1.x adds **prompt/agent-based hooks**, **agent memory with persistence**, **skill preloading into agents**, and **Task(agent_type) restrictions**. Cross-referencing these against our current .claude/ INFRA reveals **7 high-priority** and **4 medium-priority** improvement opportunities that the architect should incorporate into both SKL-006 design and the RSIL catalog.

---

## Area 1: Opus 4.6 Model Capabilities

### Context & Output
- **200K standard context** (1M in beta with premium pricing)
- **128K max output** (doubled from 64K) — enables longer thinking and comprehensive responses
- **76% on MRCR v2** (8 needles in 1M tokens) — dramatically reduces context rot

### Adaptive Thinking (Replaces budget_tokens)
The `thinking: {type: "adaptive"}` mode is the new default. Claude dynamically decides when and how much to think based on problem difficulty. This replaces the manual `budget_tokens` parameter (now deprecated). Combined with the **effort parameter**, this gives us precise control over token-quality tradeoffs.

### Effort Parameter (GA — the key optimization lever)
Four levels: `low`, `medium`, `high` (default), `max` (Opus 4.6 only). Affects ALL tokens — text, tool calls, AND thinking. This is the single most impactful optimization for our multi-agent system:

| Level | Use Case in Our Pipeline | Token Impact |
|-------|--------------------------|--------------|
| low | Simple subagent lookups, Explore tasks | Significant savings |
| medium | Routine implementation, standard research | Moderate savings |
| high | Default — complex reasoning, agentic tasks | Baseline |
| max | Phase 3 architecture, Phase 5 devil's advocate | Maximum quality |

**Critical insight:** Lower effort doesn't just reduce response length — it makes Claude use **fewer tool calls** and skip preambles. This multiplicative effect makes it far more impactful than simple prompt compression.

### Compaction API
Server-side context summarization. Triggers at configurable threshold (default 150K, min 50K). Key features:
- Custom summarization instructions (completely replace default prompt)
- `pause_after_compaction` for injecting preserved messages
- Token counting endpoint for monitoring
- Works with streaming and prompt caching

### Fast Mode
2.5x faster output at premium pricing ($30/$150 per MTok). Same model intelligence. Only relevant if latency becomes a bottleneck — currently not a priority for our pipeline.

### Breaking Changes
- **Prefill removal:** Cannot prefill assistant messages (400 error). Not an issue for our setup.
- **budget_tokens deprecated:** Must migrate to adaptive thinking. Not directly relevant since Claude Code handles this internally.

---

## Area 2: Claude Code CLI v2.1.37 Features

### Skill System — Complete Feature Map
9 frontmatter fields available. Our skills use: `name`, `description`, `argument-hint`. **Unused but valuable:**
- `hooks`: Skill-scoped lifecycle hooks (clean up when skill finishes)
- `allowed-tools`: Restrict tool access per skill
- `agent`: Specify subagent type for `context: fork` skills

Key patterns: Dynamic context injection (`!`command``), `$ARGUMENTS` substitution, `context: fork` for isolation, `ultrathink` for extended thinking.

### Hook System — 14 Events, 3 Handler Types
We use 8 of 14 events, all with `type: "command"`. **Unused events:**
- `UserPromptSubmit` — could inject pipeline state context
- `PermissionRequest` — could auto-approve known-safe patterns
- `SessionEnd` — could auto-archive team files
- `Notification` — could customize alerts

**Game-changing unused handler types:**
- `type: "prompt"` — LLM evaluates a condition (yes/no decision). Cheaper than agent, faster than shell script for nuanced evaluation.
- `type: "agent"` — Multi-turn subagent with tools (Read, Grep, Glob). Up to 50 turns. Perfect for verifying L1/L2 file quality, checking test results.

### Agent System — Key Unused Features
1. **`skills` preload:** Inject skill content at startup. Our agents don't use this. Could preload coding conventions, testing patterns.
2. **`hooks` in frontmatter:** Role-scoped hooks. Currently all hooks are global. Moving validation to agent level would be cleaner.
3. **`Task(agent_type)` restrictions:** Control which subagents an agent can spawn. None of our agents use this. Should add for boundary enforcement.
4. **`delegate` mode:** Lead coordination-only mode. We document "Lead never modifies code" as a principle, but don't enforce it at tool level.

### Agent Memory — Partially Implemented
All agents have `memory: user` set but the MEMORY.md templates are listed as "Deferred Work." Memory is functional — I'm using it right now — but standardized templates would improve cross-session knowledge building.

### Settings — Unused Capabilities
- `statusLine`: Could show pipeline phase, teammate count, task progress
- `fileSuggestion`: Custom @ autocomplete for .claude/ files
- `outputStyle`: Could tune for token efficiency
- `sandbox`: Could isolate implementer Bash commands
- `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE`: Could tune compaction timing

---

## RSIL Opportunities — Cross-Impact Matrix

| Opportunity | CLAUDE.md | Agents | Skills | Hooks | Settings | Layer 2 |
|-------------|-----------|--------|--------|-------|----------|---------|
| H-1 Agent memory templates | — | ALL 6 | — | — | — | HIGH |
| H-2 Skills preload | — | implementer, tester | reference | — | — | HIGH |
| H-3 Hooks in frontmatter | — | ALL 6 | ALL 6 | migrate | — | MED |
| H-4 Prompt/agent hooks | — | — | — | 3-4 hooks | — | HIGH |
| H-5 delegate mode | §6 | — | pipeline | — | — | MED |
| H-6 Effort strategy | §7 NEW | ALL 6 | — | — | — | HIGH |
| H-7 Task(agent_type) | §3 | ALL 6 | — | — | — | HIGH |
| M-2 Async hooks | — | — | — | 2 hooks | — | LOW |
| M-3 statusLine | — | — | — | — | settings | MED |
| M-5 maxTurns tune | — | ALL 6 | — | — | — | LOW |
| M-8 PermissionRequest | — | — | — | NEW | settings | MED |

---

## Prioritized Recommendations for Architect

### Must-Have for SKL-006 + RSIL
1. **H-6 Effort strategy:** Document per-phase effort levels in CLAUDE.md. This is the single highest-ROI improvement. Concrete token savings with zero quality loss on simple tasks.
2. **H-7 Task(agent_type):** Add to all agent .md files. Prevents role boundary violations at tool level.
3. **H-4 Prompt/agent hooks:** Convert TaskCompleted and TeammateIdle to prompt-based hooks for intelligent evaluation instead of shell script file-existence checks.
4. **H-3 Hooks in frontmatter:** Move role-specific validation from global settings.json to agent frontmatter. Cleaner architecture, self-contained agents.
5. **H-2 Skills preload:** Add coding convention skills to implementer, testing pattern skills to tester.

### Should-Have
6. **H-5 delegate mode:** Document in CLAUDE.md §6, integrate into pipeline skills as recommended practice.
7. **H-1 Agent memory templates:** Create standardized MEMORY.md for each agent type.
8. **M-3 statusLine:** Create pipeline status display for user visibility.
9. **M-8 PermissionRequest hooks:** Auto-approve common operations to reduce friction.

### Nice-to-Have
10. **M-2 Async hooks:** Make logging hooks non-blocking.
11. **M-5 maxTurns:** Tune per role.
12. **L-6 SessionEnd:** Auto-archive cleanup.

---

## SKL-006 Design Implications

The delivery pipeline (Phase 9) should:
1. Leverage effort parameter: Use `effort: low` for automated checks, `effort: high` for commit message generation
2. Use prompt hooks for pre-delivery quality gates (LLM evaluates completeness)
3. Support Layer 2 by including Ontology-aware delivery checklists
4. Use dynamic context injection for git state, test results, artifact inventory
5. Integrate with the PERMANENT Task for final status update

---

## Unresolved Items

| Item | Severity | Recommendation |
|------|----------|----------------|
| Exact v2.1.37 changelog unavailable | LOW | v2.1.33 is documented, minor patches since then |
| Effort parameter in Claude Code CLI | MEDIUM | Verify how CC exposes effort (may be internal/automatic) |
| Fast mode in Claude Code | LOW | API-only feature, not relevant for CLI usage |
| Compaction in Claude Code vs API | MEDIUM | CC has its own compaction; API compaction is separate |

---

## MCP Tools Usage Report

| Tool | Used? | Notes |
|------|-------|-------|
| sequential-thinking | No | Not available in this session |
| tavily | No | Used WebSearch as fallback |
| context7 | No | Used WebFetch as fallback |
| WebSearch | Yes | 4 searches for Opus 4.6 docs |
| WebFetch | Yes | 6 page fetches (Anthropic docs, Claude Code docs) |
| claude-code-guide | Yes | 2 background agents spawned for parallel research |

---

## Sources

- [Anthropic: Introducing Claude Opus 4.6](https://www.anthropic.com/news/claude-opus-4-6)
- [Claude API Docs: What's New in 4.6](https://platform.claude.com/docs/en/about-claude/models/whats-new-claude-4-6)
- [Claude API Docs: Effort Parameter](https://platform.claude.com/docs/en/build-with-claude/effort)
- [Claude API Docs: Compaction](https://platform.claude.com/docs/en/build-with-claude/compaction)
- [Claude Code Docs: Skills](https://code.claude.com/docs/en/skills)
- [Claude Code Docs: Hooks Reference](https://code.claude.com/docs/en/hooks)
- [Claude Code Docs: Subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code Docs: Agent Teams](https://code.claude.com/docs/en/agent-teams)
- [Claude Code Docs: Settings](https://code.claude.com/docs/en/settings)
- [Claude Code v2.1.33 Release Notes](https://github.com/anthropics/claude-code/releases/tag/v2.1.33)
