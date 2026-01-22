# Resume-Enhanced Progressive-Disclosure Orchestration System

> **Version:** 1.0 | **Status:** IN_PROGRESS | **Date:** 2026-01-17
> **Auto-Compact Safe:** This file persists across context compaction

---

## Overview

| Item | Value |
|------|-------|
| Complexity | Large |
| Total Phases | 10 |
| Target | All Subagents (Native + Custom) |
| Key Integration | ContextBudgetManager V2.1.7 |

---

## Requirements

### Core Requirements
1. **Resume Pattern Support**: All subagents must support Task(resume=agent_id)
2. **Auto-Compact Detection**: ContextBudgetManager usage > 80% triggers warning
3. **3-Layer Progressive-Disclosure**:
   - L1: Headline (Main Context)
   - L2: Structured Report (.agent/outputs/)
   - L3: Raw Output (/tmp/claude/.../tasks/)
4. **Agent Registry**: Track agent IDs for resume across Auto-Compact
5. **Layer Access Decision**: Based on task type (설계/계획/실행계획)

### Confirmed Specifications
- Detection: Context % 기반 (usage > 80%)
- Scope: All Native + Custom + Skill agents
- Storage: Hybrid (.agent/outputs/ + /tmp/claude/)
- Layer Structure: 3-Layer (L1 Headline / L2 Structured / L3 Raw)
- Access Pattern: 작업 유형 기반 자동 결정

---

## Tasks

| # | Phase | Task | Status | Agent ID |
|---|-------|------|--------|----------|
| 1 | SCAN | Analyze all existing agents for Resume pattern support | ✅ completed | afb39ab |
| 2 | DESIGN | Design ContextBudgetManager integration with Auto-Compact detection | ✅ completed | a46b6cd |
| 3 | IMPLEMENT | Implement 3-Layer Progressive-Disclosure output structure | ✅ completed | - |
| 4 | IMPLEMENT | Create Agent Registry system for Resume ID tracking | ✅ completed | - |
| 5 | UPDATE | Update all ODA agents with Resume-enabled templates | ✅ completed | - |
| 6 | UPDATE | Update all Native subagent delegation patterns | ✅ completed | - |
| 7 | IMPLEMENT | Implement L2 Structured Output format generator | ✅ completed | - |
| 8 | IMPLEMENT | Create hybrid storage strategy | ✅ completed | - |
| 9 | INTEGRATE | Integrate with CLAUDE.md orchestration protocol | ✅ completed | - |
| 10 | VERIFY | Verify and test complete system | ✅ completed | - |

---

## Progress Tracking

| Phase | Tasks | Completed | Status |
|-------|-------|-----------|--------|
| SCAN | 1 | 1 | ✅ Complete |
| DESIGN | 1 | 1 | ✅ Complete |
| IMPLEMENT | 4 | 4 | ✅ Complete |
| UPDATE | 2 | 2 | ✅ Complete |
| INTEGRATE | 1 | 1 | ✅ Complete |
| VERIFY | 1 | 1 | ✅ Complete |

---

## Agent Registry (Auto-Compact Resume)

| Task | Agent ID | Type | Status | Resume Eligible |
|------|----------|------|--------|-----------------|
| Phase 1: Agent Scan | afb39ab | Explore | completed | No |
| Phase 2: Architecture Design | a46b6cd | Plan | completed | No |

---

## Quick Resume After Auto-Compact

If context is compacted, resume by:

1. Read this file: `.agent/plans/resume_enhanced_progressive_disclosure.md`
2. Check TodoWrite for current task status
3. Check Agent Registry for in_progress agents
4. Resume agents with: `Task(resume="agent_id", prompt="Continue...")`
5. Continue from first PENDING task in sequence

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    RESUME-ENHANCED ORCHESTRATION SYSTEM                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         MAIN AGENT (Orchestrator)                      │  │
│  │                                                                        │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  ContextBudgetManager (V2.1.7)                                  │  │  │
│  │  │  ├─ Effective Window: full_window - max_output_tokens           │  │  │
│  │  │  ├─ Usage Tracking: current_usage / effective_window            │  │  │
│  │  │  ├─ Auto-Compact Detection: usage > 80% → Warning               │  │  │
│  │  │  └─ Delegation Decision: PROCEED | REDUCE_SCOPE | DEFER | ABORT │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                              │                                         │  │
│  │                              ▼                                         │  │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │  │
│  │  │  Agent Registry (Persistent)                                    │  │  │
│  │  │  ├─ .agent/plans/{slug}.md → Agent Registry Section             │  │  │
│  │  │  ├─ Track: {task_name, agent_id, type, status, output_path}     │  │  │
│  │  │  └─ Resume Eligibility: in_progress + <1hr + matching type      │  │  │
│  │  └─────────────────────────────────────────────────────────────────┘  │  │
│  │                              │                                         │  │
│  └──────────────────────────────┼────────────────────────────────────────┘  │
│                                 │                                            │
│                    ┌────────────┴────────────┐                              │
│                    │                         │                              │
│            ┌───────▼───────┐         ┌───────▼───────┐                      │
│            │ Task() Normal │         │ Task(resume=) │                      │
│            │ Delegation    │         │ Continuation  │                      │
│            └───────┬───────┘         └───────┬───────┘                      │
│                    │                         │                              │
│                    ▼                         ▼                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        SUBAGENT LAYER                                │   │
│  │                                                                      │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐   │   │
│  │  │   Native     │  │   Custom     │  │   Skill-Based            │   │   │
│  │  │   Subagents  │  │   Agents     │  │   Agents                 │   │   │
│  │  ├──────────────┤  ├──────────────┤  ├──────────────────────────┤   │   │
│  │  │ • Explore    │  │ • evidence-  │  │ • /audit → Explore       │   │   │
│  │  │ • Plan       │  │   collector  │  │ • /deep-audit → Explore  │   │   │
│  │  │ • general-   │  │ • schema-    │  │ • /plan → Plan           │   │   │
│  │  │   purpose    │  │   validator  │  │ • /ask → prompt-         │   │   │
│  │  │ • claude-    │  │ • action-    │  │         assistant        │   │   │
│  │  │   code-guide │  │   executor   │  │                          │   │   │
│  │  │              │  │ • audit-     │  │                          │   │   │
│  │  │              │  │   logger     │  │                          │   │   │
│  │  │              │  │ • prompt-    │  │                          │   │   │
│  │  │              │  │   assistant  │  │                          │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘   │   │
│  │                                                                      │   │
│  │  ALL return agent_id for potential resume                            │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                 │                                            │
│                                 ▼                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │              3-LAYER PROGRESSIVE-DISCLOSURE OUTPUT                    │   │
│  │                                                                       │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │ L1: HEADLINE (In Main Context)                                 │  │   │
│  │  │     Format: "{emoji} {Agent}[{id}]: {1-line summary}"          │  │   │
│  │  │     Example: "✅ Explore[afb39ab]: 8 files, 3 issues found"    │  │   │
│  │  │     Token Cost: ~50 tokens per agent result                    │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                        │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │ L2: STRUCTURED (On-Demand File Read)                           │  │   │
│  │  │     Location: .agent/outputs/{agent_id}_structured.md          │  │   │
│  │  │     Content: Metadata, Critical Findings, Recommendations      │  │   │
│  │  │     Access: Main Agent reads when L1 insufficient              │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                        │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │ L3: RAW OUTPUT (Resume Access)                                 │  │   │
│  │  │     Location: /tmp/claude/.../tasks/{agent_id}.output          │  │   │
│  │  │     Content: Full agent transcript (unmodified)                │  │   │
│  │  │     Access: Task(resume=agent_id) for full context recovery    │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  │                                                                       │   │
│  └───────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Component Interaction Flow

```
[User Request]
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│ Main Agent: Pre-Delegation Check                                │
│                                                                 │
│ 1. ContextBudgetManager.check_before_delegation()               │
│    └─ If ABORT: Suggest /compact first                          │
│    └─ If REDUCE_SCOPE: Use TaskDecomposer to split              │
│                                                                 │
│ 2. Read Plan File (if exists)                                   │
│    └─ Check Agent Registry for in_progress tasks                │
│    └─ If resumable: Use Task(resume=agent_id)                   │
│                                                                 │
│ 3. Deploy Subagent(s)                                           │
│    └─ run_in_background=true for parallel                       │
│    └─ Store agent_id in Agent Registry                          │
└─────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│ Subagent Execution                                              │
│                                                                 │
│ 1. Execute task with output budget constraint                   │
│ 2. Generate L2 Structured Output → .agent/outputs/              │
│ 3. Return L1 Headline to Main Agent                             │
│ 4. Full transcript saved to L3 → /tmp/claude/.../tasks/         │
└─────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│ Main Agent: Post-Execution Decision                             │
│                                                                 │
│ 1. Receive L1 Headline                                          │
│                                                                 │
│ 2. Layer Access Decision (based on task type):                  │
│    ├─ 설계/계획: L1 → L2 → L3 (full access)                     │
│    ├─ 실행 검증: L1 → L3 (skip L2, need details)                │
│    └─ 요약 보고: L1 only (sufficient)                           │
│                                                                 │
│ 3. If L1 insufficient AND need full context:                    │
│    └─ Task(resume=agent_id, prompt="Report full findings")      │
│    └─ Subagent returns with full context intact                 │
│                                                                 │
│ 4. Update Agent Registry status: completed                      │
│ 5. Update Plan File progress                                    │
└─────────────────────────────────────────────────────────────────┘
      │
      ▼
[Continue Orchestration or Report to User]
```

---

## Critical File Paths

```yaml
# Configuration
context_budget_manager: lib/oda/planning/context_budget_manager.py
task_decomposer: lib/oda/planning/task_decomposer.py
claude_md: .claude/CLAUDE.md

# Agents (Custom)
agents_directory: .claude/agents/
  - evidence-collector.md
  - schema-validator.md
  - action-executor.md
  - audit-logger.md
  - prompt-assistant.md
  - onboarding-guide.md

# Skills with Subagents
commands_directory: .claude/commands/
  - audit.md
  - deep-audit.md
  - plan.md
  - ask.md

# Output Locations
l2_outputs: .agent/outputs/
l3_outputs: /tmp/claude/.../tasks/
plan_files: .agent/plans/
```

---

## Execution Strategy

### Parallel Execution Groups

| Group | Tasks | Dependencies |
|-------|-------|--------------|
| Group A | Phase 1, 2 | None (can run parallel) |
| Group B | Phase 3, 4 | Group A complete |
| Group C | Phase 5, 6, 7, 8 | Group B complete |
| Group D | Phase 9 | Group C complete |
| Group E | Phase 10 | Group D complete |

### Subagent Delegation

| Task Group | Subagent Type | Context | Budget |
|------------|---------------|---------|--------|
| SCAN | Explore | fork | 5K |
| DESIGN | Plan | fork | 10K |
| IMPLEMENT | general-purpose | fork | 15K |
| UPDATE | general-purpose | fork | 15K |
| INTEGRATE | general-purpose | fork | 15K |
| VERIFY | Explore | fork | 5K |

---

## 3-Layer Progressive-Disclosure Design

### L1: Headline (Main Context에 포함)

```
Format: "{status_emoji} {Agent}[{id}]: {1-line summary}"
Example: "✅ Explore[afb39ab]: 8개 agents 분석, 5개 Resume 미지원"
```

### L2: Structured Report (.agent/outputs/{agent_id}_structured.md)

```markdown
# Agent Output: {agent_id}

## Metadata
- Agent Type: {type}
- Execution Time: {timestamp}
- Context Budget Used: {tokens}

## Critical Findings
1. [CRITICAL] {finding}
2. [HIGH] {finding}

## Recommendations
- {recommendation}

## File References (L3 Access)
- Full transcript: /tmp/claude/.../tasks/{agent_id}.output
```

### L3: Raw Output (/tmp/claude/.../tasks/{agent_id}.output)

```
[Full agent transcript - unmodified]
```

---

## Layer Access Decision Matrix

| 작업 단계 | L1 | L2 | L3 | Rationale |
|-----------|----|----|----| --------- |
| 설계 초기 | ✅ | ✅ | 선택 | 구조 파악이 중요 |
| 계획 수립 | ✅ | ✅ | ✅ | 전체 내용 필요 |
| 실행 검증 | ✅ | 선택 | ✅ | 상세 결과 필요 |
| 요약 보고 | ✅ | 선택 | 선택 | 핵심만 필요 |

---

## Notes

- Plan created: 2026-01-17T09:30:00
- Last updated: 2026-01-17T09:30:00
- Created by: /plan command
