# RSIL Opportunities Analysis — Features Available vs Currently Used

## Methodology
Cross-reference Claude Code CLI features (from official docs) against current .claude/ INFRA files to identify unused capabilities that could improve the infrastructure.

## Current INFRA Inventory
- CLAUDE.md v6.1 (172 lines)
- 6 agent .md files (researcher, architect, implementer, integrator, tester, devils-advocate)
- 6 skills (brainstorming, write-plan, execution, validation, verification, permanent-tasks)
- 8 hooks (SubagentStart, SubagentStop, PostToolUse:TaskUpdate, PreCompact, SessionStart:compact, TeammateIdle, TaskCompleted, PostToolUseFailure)
- settings.json with env, permissions, hooks, plugins, language, teammateMode

---

## HIGH PRIORITY — Direct Infrastructure Improvements

### H-1: Agent `memory` Frontmatter Already Used but Underutilized
**Status:** Partially used — all agents have `memory: user`
**Opportunity:** Agent memory directories exist but MEMORY.md templates are listed as "Deferred Work"
**RSIL Action:** Create standardized MEMORY.md templates per agent type
**Impact:** Agents build knowledge across sessions, reducing repeat context load

### H-2: `skills` Preload in Agent Frontmatter — UNUSED
**Status:** Not used in any agent .md file
**Feature:** `skills` field injects full skill content into subagent context at startup
**Opportunity:** Preload relevant pipeline skills into agents. E.g., implementer could preload code conventions, tester could preload testing patterns
**RSIL Action:** Add `skills:` field to appropriate agent definitions
**Impact:** Agents start with domain knowledge without needing to discover/load skills

### H-3: `hooks` in Agent/Skill Frontmatter — UNUSED
**Status:** All hooks defined in settings.json globally. No agent/skill-level hooks
**Feature:** Hooks scoped to component lifecycle in frontmatter
**Opportunity:** Move role-specific validation from global hooks to agent-level frontmatter. E.g., implementer-specific PreToolUse hooks for file ownership validation, tester PostToolUse hooks for test result checking
**RSIL Action:** Migrate appropriate global hooks to agent frontmatter; add role-specific hooks
**Impact:** Cleaner hook architecture, role-scoped validation, reduced global hook complexity

### H-4: Prompt-Based and Agent-Based Hooks — UNUSED
**Status:** All hooks are `type: "command"` (shell scripts)
**Feature:** `type: "prompt"` for LLM evaluation, `type: "agent"` for multi-turn verification
**Opportunity:**
- Use prompt hooks for TaskCompleted: LLM evaluates whether task outputs meet criteria
- Use agent hooks for TeammateIdle: agent verifies L1/L2 files exist and are well-formed
- Use prompt hooks for Stop: evaluate if all pipeline phases are complete
**RSIL Action:** Convert appropriate shell hooks to prompt/agent hooks
**Impact:** More intelligent validation, less shell scripting maintenance

### H-5: `delegate` Permission Mode — UNUSED in Lead
**Status:** Lead runs as main session, no explicit permission mode restriction
**Feature:** `delegate` mode restricts to coordination-only tools, prevents Lead from implementing
**Opportunity:** In CLAUDE.md §6, recommend Shift+Tab to enter delegate mode after team spawn
**RSIL Action:** Document delegate mode in CLAUDE.md, add to pipeline skills
**Impact:** Enforces the "Lead never modifies code directly" principle at tool level

### H-6: Effort Parameter Integration — UNUSED
**Status:** No effort configuration in any agent or skill
**Feature:** Opus 4.6 effort parameter (low/medium/high/max) affects all token usage
**Opportunity:**
- Use `effort: low` for Explore subagents doing quick lookups
- Use `effort: medium` for routine Phase 6 implementation
- Use `effort: high` (default) for Phase 2 research and Phase 5 validation
- Use `effort: max` for Phase 3 architecture decisions
**RSIL Action:** Document effort strategy in CLAUDE.md, configure per-phase
**Impact:** Significant token savings without quality loss on simple tasks

### H-7: `Task(agent_type)` Restriction — UNUSED
**Status:** All agents can spawn any subagent type
**Feature:** Restrict which subagent types an agent can spawn via `tools: Task(specific_types)`
**Opportunity:**
- researcher: `Task(Explore)` only (read-only research)
- implementer: `Task(Explore)` only (can explore but not spawn researchers)
- Lead: `Task(researcher, architect, implementer, tester, integrator, devils-advocate)`
**RSIL Action:** Add Task(type) restrictions to agent tools lists
**Impact:** Prevents unintended agent spawning, enforces role boundaries

---

## MEDIUM PRIORITY — Quality of Life Improvements

### M-1: `once` Field for Hook Handlers — PARTIALLY USED
**Status:** Used in SessionStart:compact hook (once: true)
**Opportunity:** Could use for one-time setup hooks in other events
**No immediate action needed — already leveraged where appropriate

### M-2: Async Hooks — UNUSED
**Status:** All hooks are synchronous
**Feature:** `async: true` for background non-blocking execution
**Opportunity:** Make PostToolUseFailure hook async (logging doesn't need to block)
**RSIL Action:** Set async: true on non-critical logging hooks
**Impact:** Faster execution, less blocking on non-critical operations

### M-3: `statusLine` Custom Configuration — UNUSED
**Status:** No statusLine in settings.json
**Feature:** Custom status line via shell command
**Opportunity:** Show pipeline phase, active teammate count, task completion progress
**RSIL Action:** Create statusline.sh script, add to settings
**Impact:** Better user visibility into pipeline state

### M-4: `fileSuggestion` Custom Autocomplete — UNUSED
**Status:** No fileSuggestion configuration
**Feature:** Custom @ file autocomplete
**Opportunity:** Prioritize .claude/ INFRA files, docs/plans/, agent output dirs
**RSIL Action:** Create file-suggestion.sh, add to settings
**Impact:** Faster file navigation for user

### M-5: `maxTurns` Optimization — PARTIALLY USED
**Status:** researcher: 50, implementer: 100. Others not checked
**Opportunity:** Tune maxTurns per role: devils-advocate could be lower (30), architect higher (75)
**RSIL Action:** Review and optimize maxTurns for all agents
**Impact:** Prevent runaway agents, optimize token spend

### M-6: `outputStyle` Setting — UNUSED
**Status:** No outputStyle in settings.json
**Feature:** Adjust system prompt style
**Opportunity:** Could set "Concise" for token efficiency
**RSIL Action:** Evaluate benefit vs user preference
**Impact:** Minor token savings

### M-7: PreToolUse `updatedInput` — UNUSED
**Status:** Current hooks only allow/deny, never modify input
**Feature:** Hooks can modify tool input before execution
**Opportunity:** Auto-inject working directory prefix, normalize file paths
**RSIL Action:** Evaluate specific use cases
**Impact:** Reduced errors from incorrect paths

### M-8: PermissionRequest Hooks — UNUSED
**Status:** No PermissionRequest hooks configured
**Feature:** Auto-approve/deny permission requests programmatically
**Opportunity:** Auto-approve known-safe operations per agent role
**RSIL Action:** Add PermissionRequest hooks for common patterns
**Impact:** Fewer permission interruptions during pipeline execution

### M-9: `mcpServers` in Agent Frontmatter — UNUSED
**Status:** MCP tools listed individually in agent tools list
**Feature:** `mcpServers` field for cleaner MCP configuration per agent
**Opportunity:** Move MCP server definitions to agent frontmatter instead of individual tool listing
**RSIL Action:** Evaluate if cleaner than current approach
**Impact:** Cleaner agent configuration

---

## LOW PRIORITY — Future Considerations

### L-1: Sandbox Configuration — UNUSED
**Status:** No sandbox configuration
**Opportunity:** Could sandbox implementer Bash commands for safety
**Consideration:** May conflict with agent teams workflow

### L-2: CLAUDE_AUTOCOMPACT_PCT_OVERRIDE — UNUSED
**Status:** Default ~95% threshold
**Opportunity:** Set lower (e.g., 80%) for agents that frequently hit context limits
**RSIL Action:** Evaluate per-agent benefit
**Impact:** Earlier compaction = less context loss risk

### L-3: Plugin System Enhancement — MINIMAL USE
**Status:** Only superpowers plugins enabled
**Opportunity:** Package custom skills/agents as internal plugin for distribution
**Consideration:** Overkill for single-user setup

### L-4: `UserPromptSubmit` Hooks — UNUSED
**Status:** No prompt-level hooks
**Opportunity:** Auto-inject pipeline state context before user prompts
**Consideration:** May slow down interactive mode

### L-5: CLAUDE_ENV_FILE for Dynamic Env Setup — UNUSED
**Status:** Environment set statically in settings.json env
**Opportunity:** Dynamic environment setup based on session context
**Consideration:** Current static approach is sufficient

### L-6: SessionEnd Hooks — UNUSED
**Status:** No cleanup on session end
**Opportunity:** Auto-archive team files, generate session report
**RSIL Action:** Create session cleanup script
**Impact:** Cleaner workspace, better audit trail

---

## Layer 2 Forward-Compatibility Notes

### For Ontology Framework
- Agent memory (H-1) will accumulate domain knowledge across sessions
- Skill preloading (H-2) can inject Ontology conventions into implementers
- Task(agent_type) restrictions (H-7) prevent Ontology agents from spawning wrong types
- Effort parameter (H-6) crucial for Ontology — research needs max, object creation medium
- Prompt hooks (H-4) can validate Ontology constraint satisfaction
- delegate mode (H-5) ensures Lead stays orchestrator during complex Ontology builds
