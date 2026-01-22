# ODA Workspace Comprehensive Audit Plan

> **Version:** 1.0 | **Status:** IN_PROGRESS | **Date:** 2026-01-18
> **Auto-Compact Safe:** This file persists across context compaction

---

## Overview

| Item | Value |
|------|-------|
| Complexity | **large** (전체 ODA 구성요소 점검) |
| Total Tasks | 6 Phases, 24 Tasks |
| Components | Commands(16), Hooks(17), Agents(7), Configs(4) |

---

## Problem Statement

**발견된 Critical Issues:**

1. **Phantom Hooks (4건)** - settings.json에 등록되었으나 파일 미존재
   - `pre-tool-use-oda.sh` → PreToolUse matcher에서 참조
   - `post-tool-use-audit.sh` → PostToolUse matcher에서 참조
   - `permission-request.sh` → PermissionRequest hooks
   - `notification.sh` → Notification hooks

2. **Permission Issues (2건)** - Python hooks 실행권한 미설정
   - `progressive_disclosure_hook.py` (644 → 755 필요)
   - `output_preservation_hook.py` (644 → 755 필요)

3. **Command Structure Issues (3건)**
   - `teleport.md` - description/tools/arg-hint 누락
   - `consolidate.md` - allowed-tools 누락
   - `memory-sync.md` - allowed-tools 누락

4. **Agent Documentation Gap (1건)**
   - `l2-synthesizer.md` - 1 section only (vs 30+ in others)

---

## Tasks

| # | Phase | Task | Status | Priority |
|---|-------|------|--------|----------|
| 1 | Hook Integrity | Phantom hook 존재 여부 확인 | PENDING | P0 |
| 2 | Hook Integrity | 모든 hook 파일 권한 검증 | PENDING | P0 |
| 3 | Hook Integrity | Bash syntax 검증 (bash -n) | PENDING | P1 |
| 4 | Hook Integrity | Python syntax 검증 (py_compile) | PENDING | P1 |
| 5 | Command Validation | Frontmatter 구조 검증 | PENDING | P1 |
| 6 | Command Validation | 참조 agent/skill 존재 확인 | PENDING | P1 |
| 7 | Agent Audit | Agent frontmatter 완전성 검증 | PENDING | P2 |
| 8 | Agent Audit | l2-synthesizer.md 문서 보강 | PENDING | P2 |
| 9 | Config Sync | Hook config-implementation 일치 확인 | PENDING | P1 |
| 10 | Config Sync | Path 설정 유효성 검증 | PENDING | P1 |
| 11 | Integration Test | /audit 워크플로우 체인 테스트 | PENDING | P1 |
| 12 | Integration Test | /plan 워크플로우 체인 테스트 | PENDING | P1 |
| 13 | Integration Test | /execute 워크플로우 체인 테스트 | PENDING | P1 |
| 14 | E2E Test | Session start/end 훅 실행 확인 | PENDING | P2 |

---

## Progress Tracking

| Phase | Tasks | Completed | Status |
|-------|-------|-----------|--------|
| 1. Hook Integrity | 4 | 0 | PENDING |
| 2. Command Validation | 2 | 0 | PENDING |
| 3. Agent Audit | 2 | 0 | PENDING |
| 4. Config Sync | 2 | 0 | PENDING |
| 5. Integration Test | 3 | 0 | PENDING |
| 6. E2E Test | 1 | 0 | PENDING |

---

## Phase 1: Hook Integrity (P0 - Critical)

### 1.1 Phantom Hook Resolution

**Problem:** settings.json references non-existent hooks

| Hook | Referenced In | Location Should Be | Action |
|------|---------------|-------------------|--------|
| pre-tool-use-oda.sh | PreToolUse:line 78 | ~/.claude/hooks/ | Create or remove reference |
| post-tool-use-audit.sh | PostToolUse:line 112 | ~/.claude/hooks/ | Create or remove reference |
| permission-request.sh | PermissionRequest:line 198 | ~/.claude/hooks/ | Create or remove reference |
| notification.sh | Notification:line 208 | ~/.claude/hooks/ | Create or remove reference |

**Verification Script:**
```bash
#!/bin/bash
# verify_hooks.sh

SETTINGS="/home/palantir/.claude/settings.json"
HOOKS_DIR="/home/palantir/.claude/hooks"

echo "=== Hook Existence Check ==="
for hook in $(jq -r '.. | .command? // empty' "$SETTINGS" 2>/dev/null | grep -v null | sort -u); do
  if [ -f "$hook" ]; then
    echo "[OK] $hook"
  else
    echo "[MISSING] $hook"
  fi
done
```

### 1.2 Permission Fix

**Problem:** Python hooks not executable

```bash
# Fix permissions
chmod +x ~/.claude/hooks/*.py
chmod +x ~/.claude/hooks/*.sh

# Verify
ls -la ~/.claude/hooks/*.py ~/.claude/hooks/*.sh
```

### 1.3 Syntax Validation

```bash
# Bash syntax check
for script in ~/.claude/hooks/*.sh; do
  if bash -n "$script" 2>/dev/null; then
    echo "[OK] $script"
  else
    echo "[ERROR] $script - syntax error"
  fi
done

# Python syntax check
for script in ~/.claude/hooks/*.py; do
  if python3 -m py_compile "$script" 2>/dev/null; then
    echo "[OK] $script"
  else
    echo "[ERROR] $script - syntax error"
  fi
done
```

---

## Phase 2: Command Validation

### 2.1 Frontmatter Requirements

Required fields for all commands:
- `description` (string) - 명령어 설명
- `allowed-tools` (string[]) - 사용 가능한 도구 목록
- `argument-hint` (string, optional) - 인자 힌트

**Commands with Issues:**
| Command | Missing Fields | Priority |
|---------|---------------|----------|
| teleport.md | description, allowed-tools, argument-hint | P1 |
| consolidate.md | allowed-tools | P2 |
| memory-sync.md | allowed-tools | P2 |

### 2.2 Reference Validation

Check each command references existing:
- Agents (in `.claude/agents/`)
- Skills (in `.claude/skills/`)
- Hooks (in `.claude/hooks/`)

---

## Phase 3: Agent Audit

### 3.1 Agent Completeness

| Agent | Sections | Status |
|-------|----------|--------|
| action-executor.md | 42 | OK |
| audit-logger.md | 11 | OK |
| evidence-collector.md | 33 | OK |
| l2-synthesizer.md | 1 | **NEEDS DOCS** |
| onboarding-guide.md | 8 | OK |
| prompt-assistant.md | 39 | OK |
| schema-validator.md | 38 | OK |

### 3.2 l2-synthesizer.md Enhancement

Required sections to add:
1. Description
2. Tools allowed
3. Input/Output schema
4. Usage examples
5. Integration with progressive-disclosure system

---

## Phase 4: Config Synchronization

### 4.1 Config-Implementation Matrix

| Config File | Implementation | Sync Status |
|-------------|---------------|-------------|
| enforcement_config.yaml | orchestrator_enforcement.py | CHECK |
| progressive_disclosure_config.yaml | progressive_disclosure_hook.py | CHECK |
| output_preservation_config.yaml | output_preservation_hook.py | CHECK |
| validate_task_config.yaml | validate_task_result.py | CHECK |

### 4.2 Path Validation

Verify all paths in configs exist:
- `log_path` directories
- `l2_base_path` directories
- `l3_base_path` directories

---

## Phase 5: Integration Testing

### Test Case Matrix

| Test ID | Scenario | Expected Chain | Pass Criteria |
|---------|----------|----------------|---------------|
| INT-001 | /audit lib/oda | PreToolUse → Task → PostToolUse | L2 file created |
| INT-002 | /plan feature | TodoWrite(3+) → Dual-path → Plan file | Plan in .agent/plans/ |
| INT-003 | /execute plan | Orchestrator mode → Delegation | No direct mutations |
| INT-004 | Complex Bash | Orchestrator enforcement | Block/warn issued |

---

## Phase 6: E2E Testing

### Session Lifecycle Test

```bash
# Test session start hooks
claude --verbose 2>&1 | grep -E "(session-start|welcome|setup)"

# Verify hook execution order
tail -f ~/.agent/logs/hook_audit.log &

# Run test commands
/audit .
/plan test feature
/execute

# Check logs for complete chain
```

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/oda_workspace_audit.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING task in sequence

---

## Execution Strategy

### Parallel Execution Groups

| Group | Phases | Mode |
|-------|--------|------|
| 1 | Phase 1 (Hook Integrity) | Sequential - critical |
| 2 | Phase 2, 3 (Commands, Agents) | Parallel - independent |
| 3 | Phase 4 (Config Sync) | Sequential - needs 1-3 |
| 4 | Phase 5, 6 (Testing) | Sequential - needs all |

### Subagent Delegation

| Task Group | Subagent Type | Budget |
|------------|---------------|--------|
| Hook verification | general-purpose | 10K |
| Command audit | Explore | 5K |
| Agent audit | Explore | 5K |
| Integration testing | general-purpose | 15K |

---

## Critical File Paths

```yaml
settings_file:
  - /home/palantir/.claude/settings.json    # Hook registrations

hooks_directory:
  - /home/palantir/.claude/hooks/           # All hooks

commands_directory:
  - /home/palantir/.claude/commands/        # Slash commands

agents_directory:
  - /home/palantir/.claude/agents/          # Agent definitions

config_directory:
  - /home/palantir/.claude/hooks/config/    # Hook configurations

missing_hooks:
  - pre-tool-use-oda.sh
  - post-tool-use-audit.sh
  - permission-request.sh
  - notification.sh
```

---

## Recommended Fix Priority

### P0 - Immediate (Blocks Operation)
1. Create missing hooks OR remove from settings.json
2. Fix Python hook permissions

### P1 - Short-term (Quality Issue)
3. Add missing frontmatter to commands
4. Verify config-implementation sync
5. Run integration tests

### P2 - Medium-term (Documentation)
6. Document l2-synthesizer.md
7. Add validation scripts to CI

---

## Approval Checklist

- [ ] Phase 1 fixes approved (missing hooks decision)
- [ ] Phase 2 command fixes approved
- [ ] Integration test plan approved
- [ ] Ready to proceed with implementation
