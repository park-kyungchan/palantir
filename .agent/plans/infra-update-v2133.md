# INFRA-UPDATE V2.1.33 Plan

> **Version:** 1.0.0 | **Date:** 2026-02-06
> **Scope:** V2.1.31→V2.1.33 Gap Resolution + Full Hook Event Coverage
> **Current:** settings.json V2.1.31 (partial), CLAUDE.md V7.7
> **Target:** settings.json V2.1.33 (complete), CLAUDE.md V7.8

---

## Gap Analysis Summary

### V2.1.31 PR #45 - NOT MERGED / NOT APPLIED
5 hook scripts listed as implemented but **NOT found on disk**:
- `subagent-stop.sh` - MISSING
- `session-stop.sh` - MISSING (incorrect name; should be SessionEnd)
- `pre-compact-save.sh` - MISSING
- `tool-failure-handler.sh` - MISSING
- `permission-request-handler.sh` - MISSING

3 diagnostic tools - MISSING:
- `hook-health-check.sh` - MISSING
- `hook-timing-test.sh` - MISSING
- `settings-validator.sh` - MISSING

### settings.json Hook Events Coverage

| Event | Registered | Script Exists | Status |
|-------|-----------|---------------|--------|
| SessionStart | ✅ | ✅ | OK |
| UserPromptSubmit | ❌ | ❌ | **GAP** |
| PreToolUse | ✅ (partial) | ✅ | Needs expansion |
| PermissionRequest | ❌ | ❌ | **GAP** |
| PostToolUse | ✅ (partial) | ✅ | Needs expansion |
| PostToolUseFailure | ❌ | ❌ | **GAP** |
| Notification | ❌ | ❌ | **GAP** |
| SubagentStart | ✅ | ✅ | OK |
| SubagentStop | ❌ | ❌ | **GAP** |
| Stop | ✅ (empty) | ❌ | **GAP** |
| PreCompact | ❌ | ❌ | **GAP** |
| SessionEnd | ✅ | ✅ | OK |

### V2.1.32 Features Not Applied
- `memory` frontmatter field for agents/skills
- Automatic memory recording support
- Skill auto-discovery from additional directories

### V2.1.33 Features Not Applied
- `TeammateIdle` hook event (experimental)
- `TaskCompleted` hook event (experimental)
- `memory` frontmatter with scope (user/project/local)
- `Task(agent_type)` restriction syntax
- `once` field for skill frontmatter hooks
- `async` hook support
- `statusMessage` field for UX
- `$CLAUDE_PROJECT_DIR` / `$CLAUDE_ENV_FILE` env vars
- Prompt-based hooks (`type: "prompt"`)
- Agent-based hooks (`type: "agent"`)

---

## ORCHESTRATION PLAN

```
┌─────────────────────────────────────────────────────────────────────────┐
│  INFRA-UPDATE V2.1.33 ORCHESTRATION PLAN                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Phase 1: CRITICAL ─── Missing Hook Scripts ──────────────────────────  │
│  [Tasks 2-5]     │                                                      │
│                   │  ① SubagentStop hook                                │
│                   │  ② PreCompact context save hook                     │
│                   │  ③ PostToolUseFailure handler hook                  │
│                   │  ④ PermissionRequest audit hook                     │
│                   │                                                      │
│                   ▼                                                      │
│  Phase 2: HIGH ────── New V2.1.33 Hook Scripts ───────────────────────  │
│  [Tasks 6-9]     │                                                      │
│                   │  ⑤ UserPromptSubmit validation hook                 │
│                   │  ⑥ Notification routing hook                        │
│                   │  ⑦ Stop completion-check (prompt hook)              │
│                   │  ⑧ Async test-runner hook template                  │
│                   │                                                      │
│                   ▼                                                      │
│  Phase 3: HIGH ────── settings.json Full Update ──────────────────────  │
│  [Task 10]       │                                                      │
│                   │  Register all 12 hook events                         │
│                   │  Wire scripts to events                              │
│                   │  Add V2.1.33 configuration options                   │
│                   │                                                      │
│                   ▼                                                      │
│  Phase 4: MEDIUM ──── Agent/Skill Frontmatter ────────────────────────  │
│  [Tasks 11-12]   │                                                      │
│                   │  ⑨ Add memory frontmatter to agents                 │
│                   │  ⑩ Add hooks frontmatter to skills                  │
│                   │                                                      │
│                   ▼                                                      │
│  Phase 5: MEDIUM ──── Diagnostic Tools ───────────────────────────────  │
│  [Tasks 13-15]   │                                                      │
│                   │  ⑪ hook-health-check.sh                             │
│                   │  ⑫ hook-timing-test.sh                              │
│                   │  ⑬ settings-validator.sh                            │
│                   │                                                      │
│                   ▼                                                      │
│  Phase 6: LOW ─────── Documentation Update ───────────────────────────  │
│  [Tasks 16-17]   │                                                      │
│                   │  ⑭ CLAUDE.md V7.8                                   │
│                   │  ⑮ task-api-guideline.md update                     │
│                   │                                                      │
│                   ▼                                                      │
│  Phase 7: VERIFY ──── Validation & PR ────────────────────────────────  │
│  [Tasks 18-19]   │                                                      │
│                   │  ⑯ Full validation pass                             │
│                   │  ⑰ Commit & PR                                      │
│                   │                                                      │
│                   ▼                                                      │
│  ✅ COMPLETE                                                            │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Dependency Chain

```
[PERMANENT] Context Check (#1)
        │
        ├──────────────────────────────────────┐
        │                                       │
        ▼                                       │
  Phase 1: Hook Scripts (#2-#5) ← 병렬 가능     │
        │                                       │ in_progress
        ▼                                       │ 유지
  Phase 2: New Scripts (#6-#9) ← blockedBy P1   │
        │                                       │
        ▼                                       │
  Phase 3: settings.json (#10) ← blockedBy P2   │
        │                                       │
        ├──────────────────┐                    │
        ▼                  ▼                    │
  Phase 4 (#11-12)   Phase 5 (#13-15) ← 병렬   │
        │                  │                    │
        └──────┬───────────┘                    │
               ▼                                │
  Phase 6: Docs (#16-17) ← blockedBy P4+P5     │
               │                                │
               ▼                                │
  Phase 7: Verify (#18-19) ← blockedBy P6      │
               │                                │
               ▼                                │
  [PERMANENT] completed ◄──────────────────────┘
```

---

## Detailed Task Descriptions

### Phase 1: Missing V2.1.31 Hook Scripts

#### Task 2: Create SubagentStop hook
- **File:** `.claude/hooks/subagent-stop.sh`
- **Event:** SubagentStop
- **Purpose:** Log subagent completion with agent_type, agent_id, duration
- **Input:** JSON with agent_id, agent_type, agent_transcript_path
- **Output:** Log to `.agent/logs/subagent_lifecycle.log`

#### Task 3: Create PreCompact context save hook
- **File:** `.claude/hooks/pre-compact-save.sh`
- **Event:** PreCompact
- **Purpose:** Save active workload context before compaction
- **Input:** JSON with trigger (manual/auto), custom_instructions
- **Output:** Save snapshot to `.agent/tmp/pre_compact_snapshot.json`

#### Task 4: Create PostToolUseFailure handler hook
- **File:** `.claude/hooks/tool-failure-handler.sh`
- **Event:** PostToolUseFailure
- **Purpose:** Log tool failures with error context for debugging
- **Input:** JSON with tool_name, tool_input, error, is_interrupt
- **Output:** Log to `.agent/logs/tool_failures.log`, additionalContext for Claude

#### Task 5: Create PermissionRequest audit hook
- **File:** `.claude/hooks/permission-request-handler.sh`
- **Event:** PermissionRequest
- **Purpose:** Audit permission requests and auto-approve known safe patterns
- **Input:** JSON with tool_name, tool_input, permission_suggestions
- **Output:** Log to `.agent/logs/permission_audit.log`

### Phase 2: New V2.1.33 Hook Scripts

#### Task 6: Create UserPromptSubmit hook
- **File:** `.claude/hooks/user-prompt-submit.sh`
- **Event:** UserPromptSubmit
- **Purpose:** Inject workload context and validate prompts
- **Input:** JSON with prompt text
- **Output:** additionalContext with active workload info

#### Task 7: Create Notification routing hook
- **File:** `.claude/hooks/notification-router.sh`
- **Event:** Notification
- **Purpose:** Route notifications by type (permission_prompt, idle_prompt)
- **Input:** JSON with message, title, notification_type
- **Output:** Log to `.agent/logs/notifications.log`

#### Task 8: Create Stop completion-check (prompt hook)
- **Type:** prompt (NOT command)
- **Event:** Stop
- **Purpose:** Verify task completion before allowing stop
- **Config:** Direct in settings.json as prompt hook

#### Task 9: Create async test-runner hook template
- **File:** `.claude/hooks/async-test-runner.sh`
- **Event:** PostToolUse (Write|Edit)
- **Purpose:** Template for running tests async after file changes
- **Config:** async: true, timeout: 300

### Phase 3: settings.json Full Update

#### Task 10: Update settings.json for V2.1.33
- Register all 12 hook events
- Wire Phase 1 & 2 scripts
- Add prompt hook for Stop event
- Add async hook template
- Use $CLAUDE_PROJECT_DIR for paths
- Add statusMessage to long-running hooks
- Add once field for one-time hooks

### Phase 4: Agent/Skill Frontmatter Improvements

#### Task 11: Add memory frontmatter to agents
- Files: `.claude/agents/*.md`
- Add `memory: project` to relevant agents
- Add `memory: user` to onboarding-guide

#### Task 12: Add hooks frontmatter to key skills
- Files: `.claude/skills/*/SKILL.md`
- Add PreToolUse/PostToolUse hooks where applicable
- Add once field for initialization hooks

### Phase 5: Diagnostic Tools

#### Task 13: Create hook-health-check.sh
- **File:** `.claude/scripts/diagnostics/hook-health-check.sh`
- Verify all registered hooks have corresponding scripts
- Check script permissions (executable)
- Validate JSON output format

#### Task 14: Create hook-timing-test.sh
- **File:** `.claude/scripts/diagnostics/hook-timing-test.sh`
- Measure execution time for each hook
- Flag hooks exceeding timeout thresholds

#### Task 15: Create settings-validator.sh
- **File:** `.claude/scripts/diagnostics/settings-validator.sh`
- Validate settings.json against $schema
- Check hook event coverage
- Detect missing scripts

### Phase 6: Documentation Update

#### Task 16: Update CLAUDE.md to V7.8
- V2.1.33 Hook Events table (all 12 events)
- New features: memory frontmatter, prompt hooks, async hooks
- Updated directory structure
- Changelog entry

#### Task 17: Update task-api-guideline.md
- V2.1.33 hook integration patterns
- New Notification/PermissionRequest events
- Prompt hook patterns

### Phase 7: Validation & PR

#### Task 18: Full validation pass
- Run hook-health-check.sh
- Run settings-validator.sh
- Verify all files exist and are executable
- Test each hook with sample input

#### Task 19: Commit & PR creation
- Branch: feat/infra-update-v2133
- PR to main

---

## Sources

- [Claude Code CHANGELOG](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md)
- [Claude Code Hooks Reference](https://code.claude.com/docs/en/hooks)
- [Claude Code Releases](https://github.com/anthropics/claude-code/releases)
- [Context7: /anthropics/claude-code](https://context7.com/anthropics/claude-code)
