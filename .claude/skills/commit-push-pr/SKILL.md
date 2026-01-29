---
name: commit-push-pr
description: |
  Boris Cherny Pattern 6: Commit changes, push to remote, create/update PR.
  All-in-one git workflow command used dozens of times daily.
  Automates: git add → git commit → git push → gh pr create.
  Use when ready to commit and share changes with the team.

  Core Capabilities:
  - Change Analysis: Analyze staged/unstaged changes
  - Commit Generation: Auto-generate or use provided commit message
  - Push Automation: Push with upstream tracking
  - PR Management: Create/update pull requests via gh CLI

  Output Format:
  - L1: Commit summary (commit hash, branch, files changed)
  - L2: Detailed change analysis and PR info
  - L3: Full git diff output

  Pipeline Position:
  - Terminal Skill (pipeline endpoint)
  - Upstream: /synthesis (COMPLETE status)
user-invocable: true
disable-model-invocation: false
context: fork
model: opus
allowed-tools:
  - Bash
  - Read
  - Write
  - Task
  - mcp__sequential-thinking__sequentialthinking
argument-hint: "[commit message] | --workload <slug>"
version: "3.0.0"
hooks:
  Setup:
    - type: command
      command: "source /home/palantir/.claude/skills/shared/workload-files.sh"
      timeout: 5000
  PreToolUse:
    - type: command
      command: "/home/palantir/.claude/hooks/git-safety-check.sh"
      timeout: 10000
      matcher: "Bash"

# =============================================================================
# P1: Skill as Sub-Orchestrator (Minimal - Terminal Skill)
# =============================================================================
agent_delegation:
  enabled: false
  reason: "Terminal skill - executes directly without delegation"
  output_paths:
    l1: ".agent/prompts/{slug}/commit-push-pr/l1_summary.yaml"
    l2: ".agent/prompts/{slug}/commit-push-pr/l2_index.md"
    l3: ".agent/prompts/{slug}/commit-push-pr/l3_details/"
  return_format:
    l1: "Commit summary with hash, branch, files changed (≤500 tokens)"
    l2_path: ".agent/prompts/{slug}/commit-push-pr/l2_index.md"
    l3_path: ".agent/prompts/{slug}/commit-push-pr/l3_details/"
    requires_l2_read: false
    next_action_hint: "PR URL returned"

# =============================================================================
# P2: Parallel Agent Configuration (Disabled - Sequential Git Operations)
# =============================================================================
parallel_agent_config:
  enabled: false
  reason: "Git operations must be sequential"

# =============================================================================
# P6: Internal Validation (Git Safety)
# =============================================================================
internal_validation:
  enabled: true
  checks:
    - "Branch is not main/master"
    - "No sensitive files (.env, credentials) staged"
    - "Commit message follows convention"
  max_retries: 2
---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


# /commit-push-pr Command (Boris Cherny Pattern 6)

Automates the complete git workflow: commit → push → PR in one command.

## Arguments
$ARGUMENTS - Optional commit message (auto-generated if not provided)

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## Pre-flight Checks

Before executing, verify:
```bash
# Check git status
git status --porcelain

# Check current branch (avoid direct main/master commits)
git branch --show-current
```

**Safety Rules:**
- NEVER commit directly to `main` or `master` without explicit approval
- ALWAYS run `/governance` or `/quality-check` before commit for critical changes
- WARN if committing sensitive files (.env, credentials, secrets)

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## Execution Strategy

### Phase 1: Analyze Changes

```bash
# View untracked and modified files
git status

# View staged changes
git diff --cached

# View unstaged changes
git diff

# Recent commit history for style reference
git log --oneline -5
```

### Phase 2: Stage and Commit

If `$ARGUMENTS` provided, use as commit message.
Otherwise, generate descriptive message based on:
- Nature of changes (feature, fix, refactor, docs, test)
- Affected files and modules
- "Why" over "what"

**Commit Message Format:**
```
<type>: <concise description>

<optional body explaining why>

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

**Types:** feat, fix, refactor, docs, test, chore, style

### Phase 3: Push to Remote

```bash
# Push with upstream tracking
git push -u origin $(git branch --show-current)
```

### Phase 4: Create/Update PR (Optional)

If `gh` CLI available:
```bash
# Check if PR exists for current branch
gh pr view --json state 2>/dev/null

# Create PR if none exists
gh pr create --title "<title>" --body "$(cat <<'EOF'
## Summary
<bullet points>

## Test plan
- [ ] Unit tests pass
- [ ] Manual verification

Generated with Claude Code
EOF
)"
```

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## Safety Validations

### Blocked Operations

| Condition | Action |
|-----------|--------|
| Branch is `main` or `master` | WARN and ask for confirmation |
| Committing `.env*` files | BLOCK unless explicit approval |
| Committing `*credentials*` | BLOCK - security risk |
| Empty commit | SKIP - nothing to commit |

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## Output Format

```markdown
## Commit Summary

**Branch:** feature/xyz
**Commit:** abc1234
**Message:** feat: Add new authentication flow

### Files Changed
- src/auth/login.py (+42, -10)
- tests/test_auth.py (+25, -0)

### Push Status
Pushed to origin/feature/xyz

### PR Status
PR #123 created: https://github.com/owner/repo/pull/123
```

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## Example Usage

```bash
# Auto-generate commit message
/commit-push-pr

# Provide commit message
/commit-push-pr "feat: Add user authentication flow"

# Fix commit
/commit-push-pr "fix: Resolve null pointer in login handler"
```

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## Parameter Module Compatibility (V2.1.0)

> `/build/parameters/` 모듈과의 호환성 체크리스트

| Module | Status | Notes |
|--------|--------|-------|
| `model-selection.md` | ✅ | `model: opus` 설정 |
| `context-mode.md` | ✅ | `context: standard` 사용 |
| `tool-config.md` | ✅ | V2.1.0: 허용 도구 명시 |
| `hook-config.md` | N/A | Skill 내 Hook 없음 |
| `permission-mode.md` | N/A | Skill에는 해당 없음 |
| `task-params.md` | N/A | 내부 Task 위임 없음 |

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## 7. Standalone Execution (V2.2.0)

> /commit-push-pr는 독립 실행 및 파이프라인 종료점으로 사용 가능

### 7.1 독립 실행 모드

```bash
# 독립 실행 (메시지 자동 생성)
/commit-push-pr

# 커밋 메시지 지정
/commit-push-pr "feat: Add authentication module"

# 파이프라인 종료 (synthesis 후)
/commit-push-pr --workload user-auth-20260128-143022
```

### 7.2 Workload Context Resolution

```javascript
// Workload 감지 우선순위:
// 1. --workload 인자
// 2. Active workload (_active_workload.yaml)
// 3. 독립 실행 (workload 없이)

source /home/palantir/.claude/skills/shared/skill-standalone.sh
const context = init_skill_context("commit-push-pr", ARGUMENTS)
```

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## 8. Handoff Contract (V2.2.0)

> /commit-push-pr는 파이프라인 종료점 (Terminal Skill)

### 8.1 Handoff 매핑

| Status | Next Skill | Arguments |
|--------|------------|-----------|
| `completed` | (none) | Pipeline terminates |

### 8.2 Upstream

```
/synthesis (COMPLETE) ──▶ /commit-push-pr
                              │
                              └── Pipeline 종료
```

### 8.3 Handoff YAML 출력

```yaml
handoff:
  skill: "commit-push-pr"
  workload_slug: "{slug}"
  status: "completed"
  timestamp: "2026-01-28T14:35:00Z"
  next_action:
    skill: null
    arguments: null
    required: false
    reason: "Pipeline completed - changes committed and PR created"
```

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


### Version History

| Version | Change |
|---------|--------|
| 1.1.1 | Git workflow automation |
| 2.1.0 | V2.1.19 Spec 호환, allowed-tools 배열 형식 수정 |
| 2.2.0 | Standalone Execution + Handoff Contract |
| 3.0.0 | EFL Pattern Integration, context: fork, git-safety-check hook |

---

### Auto-Delegation Trigger (CRITICAL)

> **Reference:** `.claude/skills/shared/auto-delegation.md`
> **Behavior:** When `agent_delegation.enabled: true` AND `default_mode: true`, skill automatically operates as Sub-Orchestrator.

```javascript
// AUTO-DELEGATION CHECK - Execute at skill invocation
// If complex task detected, triggers: analyze → delegate → collect
const delegationDecision = checkAutoDelegation(SKILL_CONFIG, userRequest)
if (delegationDecision.shouldDelegate) {
  const complexity = analyzeTaskComplexity(taskDescription, SKILL_CONFIG)
  return executeDelegation(taskDescription, complexity, SKILL_CONFIG)
}
// Simple tasks execute directly without delegation overhead
```


## EFL Pattern Implementation (V3.0.0)

### Terminal Skill Design

As a Terminal Skill (pipeline endpoint), this skill:
- Does NOT delegate to sub-agents (P1 disabled)
- Executes sequentially (P2 disabled)
- Uses internal validation for git safety (P6 adaptation)

### P6: Git Safety Validation

```javascript
// Pre-commit validation (adapted P6)
const gitSafetyChecks = {
  maxRetries: 2,
  checks: [
    "branch !== 'main' && branch !== 'master'",
    "!stagedFiles.some(f => f.includes('.env'))",
    "!stagedFiles.some(f => f.includes('credential'))",
    "commitMessage.match(/^(feat|fix|refactor|docs|test|chore|style):/)"
  ],
  onFailure: "BLOCK and prompt user for correction"
}
```

### Post-Compact Recovery

```javascript
if (isPostCompactSession()) {
  const slug = await getActiveWorkload()
  if (slug) {
    // Resume from workload context
    const lastCommit = await Bash("git log -1 --oneline")
    console.log(`Last commit: ${lastCommit}`)
  }
  // Continue with current git state
}
```
