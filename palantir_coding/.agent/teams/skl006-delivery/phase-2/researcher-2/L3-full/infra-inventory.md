# L3: Complete INFRA Inventory

## File-by-File Analysis

### CLAUDE.md (172 lines)

**Structure:** §0 Language Policy → §1 Team Identity → §2 Phase Pipeline → §3 Roles → §4 Communication → §5 File Ownership → §6 How Lead Operates → §7 Tools → §8 Safety → §9 Recovery → §10 Integrity Principles

**Quality:** Excellent. Clean NLP v6.0, no protocol markers, well-organized sections. The §6 "How Lead Operates" subsections (Before Spawning, Assigning Work, Verifying Understanding, Monitoring Progress, Phase Gates, Status Visualization, Coordination Infrastructure) provide comprehensive guidance without excessive ceremony.

**Issues:**
- Line 155: "Archive to MEMORY.md + ARCHIVE.md at work end" — ARCHIVE.md undefined
- §7 mentions "Use sequential-thinking for all non-trivial analysis" — repeated in every skill
- §6 "Before Spawning" gatekeeping (S-1, S-2, S-3) is excellent — derived from BUG-002 learnings

### Agent Files (6 files, 442 lines total)

| Agent | Lines | model | permissionMode | maxTurns | Tools (unique) |
|-------|-------|-------|----------------|----------|---------------|
| researcher | 62 | opus | default | 50 | WebSearch, WebFetch |
| architect | 73 | opus | default | 50 | Write |
| devils-advocate | 72 | opus | default | 30 | (read-only) |
| implementer | 79 | opus | acceptEdits | 100 | Edit, Write, Bash |
| tester | 76 | opus | default | 50 | Write, Bash |
| integrator | 80 | opus | acceptEdits | 100 | Edit, Write, Bash |

**Common tools (all 6):** Read, Glob, Grep, TaskList, TaskGet, sequential-thinking, context7 (2 tools), tavily

**Structural consistency:** All follow: frontmatter → Role → Before Starting Work → Probing Questions → How to Work → Output Format → Constraints

**Note on researcher Write tool:** The system-level agent type definition in the Task tool prompt DOES include Write and Edit for researcher. The .md frontmatter tools list does NOT include Write. The system definition overrides the .md frontmatter. This means researcher CAN write files despite the .md saying "Read-only access." This may be intentional (researchers need Write for L1/L2/L3 output) — the body text "read-only" refers to codebase mutation prevention, not L1/L2 file creation.

### Skill Files (6 files, 2549 lines total)

| Skill | Lines | Phase | Key Sections |
|-------|-------|-------|-------------|
| brainstorming-pipeline | 509 | P1-3 | Discovery Q&A, Research spawn, Architecture spawn |
| agent-teams-write-plan | 316 | P4 | Input Discovery, Architect spawn, Plan Generation |
| plan-validation-pipeline | 381 | P5 | Devils-advocate spawn, Challenge execution |
| agent-teams-execution-plan | 572 | P6 | Adaptive spawn, Task execution + 2-stage review |
| verification-pipeline | 521 | P7-8 | Tester spawn, Integrator (conditional) |
| permanent-tasks | 250 | — | PT CRUD, Read-Merge-Write consolidation |

**Common sections across pipeline skills (5 skills, not permanent-tasks):**

1. **Phase 0 PT Check** (~28 lines each, identical flow diagram)
   - Exact same ASCII decision tree in all 5 skills
   - Same TaskList → found/not found → TaskGet/AskUser branching
   - Same /permanent-tasks invocation path

2. **Clean Termination** (~15 lines each)
   - shutdown teammates → TeamDelete → preserve artifacts → output summary → "Next: Phase N"
   - Only the teammate types and next phase differ

3. **Cross-Cutting Sequential Thinking** (~8 lines each)
   - "All agents use `mcp__sequential-thinking__sequentialthinking` for analysis, judgment, and verification."
   - Agent × When table varies per skill

4. **Error Handling table** (~10 lines each)
   - Spawn failure, understanding verification rejection, gate iteration, context compact, user cancellation
   - 80% identical across skills

5. **Compact Recovery** (~3 lines each)
   - Lead: orchestration-plan → task list → gate records → L1 → re-inject
   - Teammate: TaskGet PT → read own L1/L2/L3 → re-submit

6. **Dynamic Context commands** (partial overlap)
   - Infrastructure Version: `head -3 CLAUDE.md` — all 5 skills
   - Existing Plans: `ls docs/plans/` — 4/5 skills

### Hook Scripts (8 files, 362 lines total)

| Hook | Lines | Event | Purpose | Blocking? |
|------|-------|-------|---------|-----------|
| on-subagent-start | 67 | SubagentStart | PT/GC context injection | No |
| on-subagent-stop | 52 | SubagentStop | L1/L2 existence check + logging | No |
| on-task-update | 35 | PostToolUse(TaskUpdate) | Task state logging | No |
| on-pre-compact | 42 | PreCompact | Task list snapshot | No |
| on-session-compact | 25 | SessionStart(compact) | Recovery notification | No |
| on-teammate-idle | 51 | TeammateIdle | L1/L2 validation gate | Yes (exit 2) |
| on-task-completed | 56 | TaskCompleted | L1/L2 validation gate | Yes (exit 2) |
| on-tool-failure | 34 | PostToolUseFailure | Failure logging | No |

**Effectiveness ranking:**
1. `on-teammate-idle` + `on-task-completed`: Most valuable — enforce L1/L2 output obligation
2. `on-subagent-start`: Valuable — context injection guidance
3. `on-pre-compact`: Valuable — snapshot preservation
4. `on-subagent-stop`: Useful — output validation logging
5. `on-session-compact`: Useful but uses old markers
6. `on-task-update`, `on-tool-failure`: Lightweight logging — low impact

### Settings Files

**settings.json (133L):**
- env: CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1, output token limits (128K/100K/200K)
- permissions.deny: .env, secrets, credentials, SSH keys, rm -rf, sudo rm, chmod 777
- hooks: 8 hook registrations (SubagentStart, SubagentStop, PostToolUse(TaskUpdate), PreCompact, SessionStart(compact), TeammateIdle, TaskCompleted, PostToolUseFailure)
- enabledPlugins: superpowers-developing-for-claude-code, superpowers
- language: Korean
- teammateMode: tmux

**settings.local.json (22L):**
- permissions.allow: Bash(*), MCP tools, WebFetch(github), WebSearch, Skill(orchestrate), TaskUpdate, TaskCreate
- enableAllProjectMcpServers: true
- enabledMcpjsonServers: [oda-ontology, tavily]

**Security concern:** settings.local.json contains `"Bash(*)"` — allows any Bash command. The settings.json deny list provides the safety net, but this is a broad permission.

### References

**agent-common-protocol.md (84L):** Clean, concise NLP. Covers: task assignment, context changes, completion, Task API, team memory, saving work, context loss recovery, agent memory. No issues.

**task-api-guideline.md (536L):** The INFRA's largest file by content density. 14 sections. §1-§10 are useful operational guidelines. §11-§14 are the legacy protocol ceremony:

| Section | Lines | Status |
|---------|-------|--------|
| §1 Pre-Call | ~15 | OK |
| §2 Storage Architecture | ~40 | OK |
| §3 Comprehensive TaskCreate | ~50 | OK — the template is valuable |
| §4 Dependency Chain | ~20 | OK |
| §5 Task Lifecycle | ~20 | OK |
| §6 Semantic Integrity | ~30 | Mixed — some protocol markers |
| §7 Anti-Patterns | ~20 | OK |
| §8 Known Issues | ~40 | OK — ISS-001~005 documented |
| §9 Sub-Orchestrator | ~15 | OK |
| §10 Metadata | ~10 | OK |
| §11 DIA Enforcement | ~220 | LEGACY — 30+ protocol markers, DIAVP tiers, LDAP categories, RC-01~10 |
| §12 TASK_LIST_ID | ~20 | OK |
| §13 Team Memory | ~40 | OK |
| §14 Context Delta | ~40 | Mixed — protocol markers but useful content |

**§11 analysis:** This section defines CIP (Context Injection Protocol), DIAVP (Impact Awareness Verification Protocol), and LDAP (Adversarial Challenge Protocol). These were the pre-NLP v6.0 protocol system. The current NLP v6.0 approach embeds verification naturally in CLAUDE.md §6 and skill files. §11 is now largely redundant — the skills contain the same logic in natural language. However, some content has value:
- IP-001~010 injection point table: useful reference
- ISS-001~005 known issues: valuable operational knowledge
- FC-1~5 fallback conditions: useful decision tree

**Recommended restructure:** Keep §1-§10, §12-§13 operational content. Trim §11 to just the IP table + fallback conditions. Remove DIAVP/LDAP ceremony. Convert §14 to natural language. Target: ~200 lines.

## Pre-Compact Snapshot Accumulation

Found 29+ `pre-compact-tasks-*.json` files in `.agent/teams/` ranging from 4 bytes to 15KB. These accumulate with no cleanup mechanism. Phase 9 should include snapshot cleanup as part of session finalization.

## ARCHIVE.md Design Gap

CLAUDE.md §10 says "Archive to MEMORY.md + ARCHIVE.md at work end" but ARCHIVE.md is never defined. The intended distinction seems to be:
- MEMORY.md: Durable lessons learned, patterns, bug records (cross-session)
- ARCHIVE.md: Complete pipeline execution record (single-session history)

Phase 9 should define ARCHIVE.md template containing: feature name, dates, all gate records, key decisions, metrics, deviations from plan, lessons learned.
