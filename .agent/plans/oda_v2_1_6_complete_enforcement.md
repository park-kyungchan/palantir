# ODA v2.1.6 완전 강제화 및 Agent Chaining 통합

> **Version:** 1.0 | **Status:** COMPLETED | **Date:** 2026-01-13
> **Auto-Compact Safe:** This file persists across context compaction

## Overview

| Item | Value |
|------|-------|
| Complexity | LARGE |
| Total Phases | 4 |
| Files Affected | 15+ |
| Estimated Tasks | 24 |

## Goals

1. Skills Proposal 통합 (7/7 = 100%)
2. Enforcement Mode WARN → BLOCK 변경
3. Agents ODA 명세 추가 (Proposal 의무화)
4. Agent Chaining 지원 (Main Agent = Orchestrator only)

## Key Constraints

- Main Agent는 반드시 Orchestrator 역할만 수행
- 모든 실제 작업은 Agents에게 위임
- V2.1.6 기능 활용: resume 파라미터, TaskDecomposer, run_in_background

---

## Phase 1: Enforcement Mode Change (WARN → BLOCK)

**Priority:** HIGH | **Status:** COMPLETED

### Tasks

| # | Task | Status | File |
|---|------|--------|------|
| 1.1 | Create enforcement_config.yaml | COMPLETED | `.claude/hooks/config/enforcement_config.yaml` |
| 1.2 | Modify pre-tool-use-oda.sh exit logic | COMPLETED | `.claude/hooks/pre-tool-use-oda.sh` |
| 1.3 | Update CLAUDE.md Section 2.6 | COMPLETED | `/home/palantir/.claude/CLAUDE.md` |
| 1.4 | Create allowed_direct_commands list | COMPLETED | `.claude/hooks/config/bypass_list.yaml` |

### Key Changes

```yaml
# enforcement_config.yaml
enforcement_mode: BLOCK  # Changed from WARN
thresholds:
  bash_command_length: 200
  bash_pipe_count: 3
  edit_line_count: 50
allowed_direct_commands:
  - "git status"
  - "pytest"
  - "ruff check"
  - "mypy"
```

---

## Phase 2: Skills Proposal Integration (29% → 100%)

**Priority:** HIGH | **Status:** COMPLETED

### Current State

| Skill | ODA Integration | Proposal Section |
|-------|-----------------|------------------|
| plan.md | Full | Missing |
| audit.md | Full | Missing |
| protocol.md | Full | Missing |
| deep-audit.md | Full | Partial (Block only) |
| pre-check.md | Full | Missing |
| evidence-report.md | Full | Has reference |
| ask.md | Full | N/A (routing) |

### Tasks

| # | Task | Status | File |
|---|------|--------|------|
| 2.1 | Add Proposal section to audit.md | COMPLETED | `.claude/skills/audit.md` |
| 2.2 | Add Proposal section to plan.md | COMPLETED | `.claude/skills/plan.md` |
| 2.3 | Add Proposal section to protocol.md | COMPLETED | `.claude/skills/protocol.md` |
| 2.4 | Enhance Proposal in deep-audit.md | COMPLETED | `.claude/skills/deep-audit.md` |
| 2.5 | Add Proposal section to pre-check.md | COMPLETED | `.claude/skills/pre-check.md` |
| 2.6 | Add Proposal routing to ask.md | COMPLETED | `.claude/skills/ask.md` |

### Standard Template

```markdown
## Proposal Integration

### Mutation Detection
All operations that modify files MUST go through Proposal workflow.

### Proposal Creation Pattern
```python
for change in identified_changes:
    mcp__oda_ontology__create_proposal(
        action_type="file.modify",
        payload={
            "path": change.file,
            "changes": change.diff,
            "reason": change.rationale,
            "evidence": {
                "skill": "{skill_name}",
                "stage": "{stage}",
                "findings": change.findings
            }
        },
        priority=change.severity_to_priority(),
        submit=True
    )
```
```

---

## Phase 3: Agents ODA Mandate

**Priority:** MEDIUM | **Status:** COMPLETED

### Current Agents

| Agent | Location | ODA Mandate |
|-------|----------|-------------|
| governance-gate.md | `.claude/agents/` | Implicit |

### Tasks

| # | Task | Status | File |
|---|------|--------|------|
| 3.1 | Add proposal_mandate: REQUIRED to governance-gate | COMPLETED | `.claude/agents/governance-gate.md` |
| 3.2 | Create agent-specification-template.md | COMPLETED | `.claude/references/agent-specification.md` |
| 3.3 | Document Agent-to-Proposal handoff | COMPLETED | `.claude/references/agent-chaining-protocol.md` |

### Agent Spec Template

```yaml
oda_context:
  role: {role}
  stage_access: [A, B, C]
  evidence_required: true
  governance_mode: strict
  proposal_mandate: REQUIRED  # All mutations via Proposal
```

---

## Phase 4: Agent Chaining (Orchestrator Pattern)

**Priority:** HIGH | **Status:** COMPLETED

### Architecture

```
User Request
     │
     ▼
┌─────────────────────────────────────────────────────────┐
│                    MAIN AGENT (Orchestrator)             │
│                                                         │
│  ALLOWED: Read, Grep, Glob, TodoWrite, AskUserQuestion  │
│  BLOCKED: Edit, Write, Bash (complex), NotebookEdit     │
└─────────────────────┬───────────────────────────────────┘
                      │
     ┌────────────────┼────────────────┐
     │                │                │
     ▼                ▼                ▼
┌──────────┐   ┌──────────┐    ┌──────────────┐
│ Explore  │   │   Plan   │    │ general-     │
│ Subagent │   │ Subagent │    │ purpose      │
└────┬─────┘   └────┬─────┘    └──────┬───────┘
     │              │                 │
     ▼              ▼                 ▼
[Stage A/B     [Plan File]      [Proposal]
 Evidence]                           │
                                     ▼
                              [Human Approval]
                                     │
                                     ▼
                              [Execution]
```

### Tasks

| # | Task | Status | File |
|---|------|--------|------|
| 4.1 | Create agent-chaining-protocol.md | COMPLETED | `.claude/references/agent-chaining-protocol.md` |
| 4.2 | Create agent_registry.yaml | COMPLETED | `.agent/config/agent_registry.yaml` |
| 4.3 | Update CLAUDE.md orchestrator rules | COMPLETED | `/home/palantir/.claude/CLAUDE.md` |
| 4.4 | Add delegation_mandate to all skills | COMPLETED | `.claude/skills/*.md` |
| 4.5 | Strengthen hook enforcement | COMPLETED | `.claude/hooks/pre-tool-use-oda.sh` |

### Delegation Rules

| Operation | Direct Allowed | Must Delegate To |
|-----------|---------------|------------------|
| File read | YES | - |
| Pattern search | YES | - |
| File edit | NO | general-purpose + Proposal |
| File write | NO | general-purpose + Proposal |
| Complex bash | NO | Explore or general-purpose |
| Git operations | NO | general-purpose + Proposal |

---

## Progress Tracking

| Phase | Tasks | Completed | Status |
|-------|-------|-----------|--------|
| Phase 1 | 4 | 4 | COMPLETED |
| Phase 2 | 6 | 6 | COMPLETED |
| Phase 3 | 3 | 3 | COMPLETED |
| Phase 4 | 5 | 5 | COMPLETED |
| **Total** | **18** | **18** | **100%** |

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/oda_v2_1_6_complete_enforcement.md`
2. Check TodoWrite for current task status
3. Continue from first PENDING task in sequence
4. Use subagent delegation pattern from "Execution Strategy" section

---

## Execution Strategy

### Parallel Execution Groups

| Group | Tasks | Can Parallelize |
|-------|-------|-----------------|
| Group A | 1.1, 1.4 | YES (config files) |
| Group B | 2.1-2.6 | YES (independent skills) |
| Group C | 3.1-3.3 | YES (independent agents) |
| Group D | 4.1-4.5 | NO (dependencies) |

### Subagent Delegation

| Task Group | Subagent Type | Context | Budget |
|------------|---------------|---------|--------|
| Phase 1 | general-purpose | fork | 15K tokens |
| Phase 2 | general-purpose | fork | 15K tokens |
| Phase 3 | general-purpose | fork | 15K tokens |
| Phase 4 | Plan + general-purpose | fork | 10K + 15K tokens |

---

## Agent Registry (Auto-Compact Resume)

| Task | Agent ID | Status | Resume Eligible |
|------|----------|--------|-----------------|
| Stage A Scan | aeeadbd | completed | No |
| Plan Analysis | afac2eb | completed | No |
| Phase 1: Enforcement Mode | a3a108f | completed | No |
| Phase 2: Skills Proposal | a8e6f3a | completed | No |
| Phase 3: Agents Mandate | a0667fb | completed | No |
| Phase 4: Agent Chaining | aa820f9 | completed | No |

---

## Critical File Paths

```yaml
enforcement_config:
  - .claude/hooks/config/enforcement_config.yaml (NEW)
  - .claude/hooks/config/bypass_list.yaml (NEW)
  - .claude/hooks/pre-tool-use-oda.sh (MODIFY)

skills_to_update:
  - .claude/skills/audit.md
  - .claude/skills/plan.md
  - .claude/skills/protocol.md
  - .claude/skills/deep-audit.md
  - .claude/skills/pre-check.md
  - .claude/skills/ask.md

agents_to_update:
  - .claude/agents/governance-gate.md

new_references:
  - .claude/references/agent-chaining-protocol.md (NEW)
  - .claude/references/agent-specification.md (NEW)
  - .agent/config/agent_registry.yaml (NEW)

main_config:
  - /home/palantir/.claude/CLAUDE.md (user global)
```

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Breaking existing workflows | Bypass list for common operations |
| Performance impact of BLOCK | Cache governance decisions |
| User friction | Clear error messages with next steps |
| Auto-Compact context loss | This plan file persists |

---

## Verification Checklist

After implementation, verify:

- [x] `pre-tool-use-oda.sh` exits non-zero for mutations without Proposal
- [x] All 7 skills have Proposal integration sections
- [x] All agents have `proposal_mandate: REQUIRED`
- [x] Main Agent cannot directly execute Edit/Write
- [x] Subagent delegation works with `run_in_background=true`
- [x] Resume parameter recovers from Auto-Compact

---

## Evidence from Analysis

### Stage A Scan (Explore Agent aeeadbd)
- Skills: 7/7 ODA-integrated, V2.1.6 features active
- Proposal infrastructure: Fully implemented
- TaskDecomposer: Active in 4 skills
- Hooks: WARN mode (needs BLOCK)

### Plan Analysis (Plan Agent afac2eb)
- 4 phases identified with clear dependencies
- Risk assessment completed
- File-level changes documented
- Agent chaining architecture designed
