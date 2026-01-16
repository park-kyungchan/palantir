# Plan: Custom Command Enhancement (Pre-Mutation Zone Optimization)

> **Version:** 1.1.0 | **Date:** 2026-01-13
> **Status:** in_progress | **Complexity:** large
> **User Requirement:** "나는 앞으로 커스텀커맨드를 통해서만 진행할거야"

---

## Metadata

| Attribute | Value |
|-----------|-------|
| Created | 2026-01-13 11:38:00 |
| Updated | 2026-01-13 11:45:00 |
| Status | in_progress |
| Complexity | large |
| Total Micro-Tasks | 72 |
| Total Phases | 6 |
| Files to Create | 8 |
| Files to Modify | 12 |
| Agent Delegations | 24+ |

---

## Quick Resume (For Auto-Compact Recovery)

### Current Execution State

```
Phase: Phase 5 COMPLETE | Tasks: All Phase 5 Tasks Done | Status: in_progress
Active Agents: None
Last Completed: Phase 5 (Context Injection System) - 12/12 tasks
Next: Phase 2-4 test files (2.7, 3.6, 4.6) + Phase 6 Integration
```

### Resume Instructions

1. Read this file: `.agent/plans/custom_command_enhancement.md`
2. Find "Current Execution State" above
3. Locate the current task in "Comprehensive To-Do List"
4. Resume execution from that task
5. Check "Agent Registry" for any running agents to resume

---

## Agent Registry

Track subagent IDs for resume after Auto-Compact:

| Agent ID | Type | Phase.Task | Description | Status |
|----------|------|------------|-------------|--------|
| a740d90 | claude-code-guide | Research | V2.1.4 features | completed |
| a062a9b | Explore | Research | Custom commands structure | completed |
| ac5f63b | Plan | Research | Architecture analysis | completed |
| a1edadf | general-purpose | 1.1.1-1.5.2 | Create /ask skill | completed |
| a128d5f | Explore | 2.1.1, 3.1.1, 4.1.1 | Explore Phase 2-4 files | completed |
| a991301 | Explore | 5.4.1 | Explore router.py | completed |
| a31a868 | general-purpose | 1.6.1-1.6.2 | Create /ask test file | completed |
| adddca5 | general-purpose | 2.1.1-2.6.1 | Enhance /plan skill | completed |
| ab3b4d6 | general-purpose | 3.1.1-3.5.2 | Enhance /audit skill | completed |
| a8068c7 | general-purpose | 4.1.1-4.5.1 | Enhance /deep-audit skill | completed |
| af2fd81 | general-purpose | 2.7.1-2.7.2 | Create /plan test file | running |
| a2198f9 | general-purpose | 3.6.1-3.6.2 | Create /audit test file | running |
| a8ede8f | general-purpose | 4.6.1-4.6.2 | Create /deep-audit test file | running |
| aacf21b | general-purpose | 5.1.1-5.5.2 | Phase 5 Context Injection | running |

---

## 📋 COMPREHENSIVE TO-DO LIST (72 Micro-Tasks)

> **Context Window 최적화:** 각 태스크는 독립적으로 실행 가능하도록 최대 분할됨
> **Agent 위임:** 각 태스크별 위임 대상 명시
> **Auto-Compact 대응:** 태스크 완료 시 이 파일의 상태 업데이트 필수

---

### PHASE 1: /ask Skill Enhancement (12 Micro-Tasks)

**목표:** 요구사항 명확화 및 프롬프트 엔지니어링 전문 스킬 구현

| ID | Micro-Task | Agent | File | Status |
|----|------------|-------|------|--------|
| 1.1.1 | Create ask.md file with frontmatter only | general-purpose | `.claude/skills/ask.md` | ✅ done |
| 1.1.2 | Add skill overview section | general-purpose | `.claude/skills/ask.md` | ✅ done |
| 1.1.3 | Add invocation trigger section | general-purpose | `.claude/skills/ask.md` | ✅ done |
| 1.2.1 | Define Socratic questioning flow diagram | general-purpose | `.claude/skills/ask.md` | ✅ done |
| 1.2.2 | Add clarification question templates | general-purpose | `.claude/skills/ask.md` | ✅ done |
| 1.3.1 | Create prompt engineering keyword table | general-purpose | `.claude/skills/ask.md` | ✅ done |
| 1.3.2 | Add technique detection logic section | general-purpose | `.claude/skills/ask.md` | ✅ done |
| 1.4.1 | Add WebSearch fallback section | general-purpose | `.claude/skills/ask.md` | ✅ done |
| 1.5.1 | Create auto-routing decision tree | general-purpose | `.claude/skills/ask.md` | ✅ done |
| 1.5.2 | Add command recommendation table | general-purpose | `.claude/skills/ask.md` | ✅ done |
| 1.6.1 | Create test file structure | general-purpose | `lib/oda/pai/skills/tests/test_ask_skill.py` | ✅ done |
| 1.6.2 | Add unit test cases | general-purpose | `lib/oda/pai/skills/tests/test_ask_skill.py` | ✅ done |

**Phase 1 Progress:** 12/12 (100%) ✅ COMPLETE

---

### PHASE 2: /plan Skill Enhancement (14 Micro-Tasks)

**목표:** Dual-Path Analysis (ODA Protocol + Plan Subagent) 최적화

| ID | Micro-Task | Agent | File | Status |
|----|------------|-------|------|--------|
| 2.1.1 | Read current plan.md file | Explore | `.claude/skills/plan.md` | ✅ done |
| 2.1.2 | Add context: fork to frontmatter | general-purpose | `.claude/skills/plan.md` | ✅ done |
| 2.2.1 | Add ODA Protocol path section | general-purpose | `.claude/skills/plan.md` | ✅ done |
| 2.2.2 | Add Plan Subagent path section | general-purpose | `.claude/skills/plan.md` | ✅ done |
| 2.2.3 | Add parallel execution pattern | general-purpose | `.claude/skills/plan.md` | ✅ done |
| 2.3.1 | Define plan file template | general-purpose | `.claude/skills/plan.md` | ✅ done |
| 2.3.2 | Add auto-generation logic section | general-purpose | `.claude/skills/plan.md` | ✅ done |
| 2.4.1 | Add TaskDecomposer integration section | general-purpose | `.claude/skills/plan.md` | ✅ done |
| 2.4.2 | Add scope keyword detection | general-purpose | `.claude/skills/plan.md` | ✅ done |
| 2.5.1 | Add resume parameter section | general-purpose | `.claude/skills/plan.md` | ✅ done |
| 2.5.2 | Add Agent Registry template | general-purpose | `.claude/skills/plan.md` | ✅ done |
| 2.6.1 | Create synthesis comparison matrix | general-purpose | `.claude/skills/plan.md` | ✅ done |
| 2.7.1 | Create test file structure | general-purpose | `lib/oda/pai/skills/tests/test_plan_skill.py` | ✅ done |
| 2.7.2 | Add integration test cases | general-purpose | `lib/oda/pai/skills/tests/test_plan_skill.py` | ✅ done |

**Phase 2 Progress:** 14/14 (100%) ✅ COMPLETE

---

### PHASE 3: /audit Skill Enhancement (12 Micro-Tasks)

**목표:** Stage C 품질 검증 병렬화 및 context:fork 적용

| ID | Micro-Task | Agent | File | Status |
|----|------------|-------|------|--------|
| 3.1.1 | Read current audit.md file | Explore | `.claude/skills/audit.md` | ✅ done |
| 3.1.2 | Verify context: fork in frontmatter | Explore | `.claude/skills/audit.md` | ✅ done |
| 3.2.1 | Define 4 quality check streams | general-purpose | `.claude/skills/audit.md` | ✅ done |
| 3.2.2 | Add parallel execution pattern | general-purpose | `.claude/skills/audit.md` | ✅ done |
| 3.2.3 | Add synthesis section | general-purpose | `.claude/skills/audit.md` | ✅ done |
| 3.3.1 | Define severity levels | general-purpose | `.claude/skills/audit.md` | ✅ done |
| 3.3.2 | Add filtering logic section | general-purpose | `.claude/skills/audit.md` | ✅ done |
| 3.4.1 | Add TodoWrite integration | general-purpose | `.claude/skills/audit.md` | ✅ done |
| 3.5.1 | Define Pre-Mutation Zone boundary | general-purpose | `.claude/skills/audit.md` | ✅ done |
| 3.5.2 | Add enforcement rules | general-purpose | `.claude/skills/audit.md` | ✅ done |
| 3.6.1 | Create test file structure | general-purpose | `lib/oda/pai/skills/tests/test_audit_skill.py` | ✅ done |
| 3.6.2 | Add benchmark test cases | general-purpose | `lib/oda/pai/skills/tests/test_audit_skill.py` | ✅ done |

**Phase 3 Progress:** 12/12 (100%) ✅ COMPLETE

---

### PHASE 4: /deep-audit Skill Enhancement (12 Micro-Tasks)

**목표:** RSIL 심층 분석 + 4-Stream 병렬화 + BLOCK 강제

| ID | Micro-Task | Agent | File | Status |
|----|------------|-------|------|--------|
| 4.1.1 | Read current deep-audit.md file | Explore | `.claude/skills/deep-audit.md` | ✅ done |
| 4.1.2 | Verify model: opus in frontmatter | Explore | `.claude/skills/deep-audit.md` | ✅ done |
| 4.2.1 | Define Security Scan stream | general-purpose | `.claude/skills/deep-audit.md` | ✅ done |
| 4.2.2 | Define Architecture Analysis stream | general-purpose | `.claude/skills/deep-audit.md` | ✅ done |
| 4.2.3 | Define Code Quality Metrics stream | general-purpose | `.claude/skills/deep-audit.md` | ✅ done |
| 4.2.4 | Define Dependency Audit stream | general-purpose | `.claude/skills/deep-audit.md` | ✅ done |
| 4.3.1 | Add RSIL synthesis algorithm | general-purpose | `.claude/skills/deep-audit.md` | ✅ done |
| 4.4.1 | Define BLOCK conditions | general-purpose | `.claude/skills/deep-audit.md` | ✅ done |
| 4.4.2 | Add enforcement logic | general-purpose | `.claude/skills/deep-audit.md` | ✅ done |
| 4.5.1 | Add TaskDecomposer section | general-purpose | `.claude/skills/deep-audit.md` | ✅ done |
| 4.6.1 | Create test file structure | general-purpose | `tests/.../test_deep_audit_skill.py` | ⬜ pending |
| 4.6.2 | Add E2E test cases | general-purpose | `tests/.../test_deep_audit_skill.py` | ⬜ pending |

**Phase 4 Progress:** 10/12 (83%)

---

### PHASE 5: Auto Full-Context-Injection System (12 Micro-Tasks)

**목표:** 모든 커맨드에 자동 컨텍스트 주입 시스템 구현

| ID | Micro-Task | Agent | File | Status |
|----|------------|-------|------|--------|
| 5.1.1 | Create context_injector.py file | general-purpose | `lib/oda/pai/skills/context_injector.py` | ✅ done |
| 5.1.2 | Add ContextInjector class skeleton | general-purpose | `lib/oda/pai/skills/context_injector.py` | ✅ done |
| 5.1.3 | Define REFERENCE_MAP constant | general-purpose | `lib/oda/pai/skills/context_injector.py` | ✅ done |
| 5.2.1 | Implement inject() method | general-purpose | `lib/oda/pai/skills/context_injector.py` | ✅ done |
| 5.2.2 | Implement _load_reference() method | general-purpose | `lib/oda/pai/skills/context_injector.py` | ✅ done |
| 5.3.1 | Add reference auto-loading logic | general-purpose | `lib/oda/pai/skills/context_injector.py` | ✅ done |
| 5.3.2 | Add plan file loading for resume | general-purpose | `lib/oda/pai/skills/context_injector.py` | ✅ done |
| 5.4.1 | Read current router.py | Explore | `lib/oda/pai/skills/router.py` | ✅ done |
| 5.4.2 | Integrate ContextInjector into router | general-purpose | `lib/oda/pai/skills/router.py` | ✅ done |
| 5.4.3 | Add injection before skill execution | general-purpose | `lib/oda/pai/skills/router.py` | ✅ done |
| 5.5.1 | Create test file structure | general-purpose | `lib/oda/pai/skills/tests/test_context_injector.py` | ✅ done |
| 5.5.2 | Add injection test cases | general-purpose | `lib/oda/pai/skills/tests/test_context_injector.py` | ✅ done |

**Phase 5 Progress:** 12/12 (100%) ✅ COMPLETE

---

### PHASE 6: Integration & Testing (10 Micro-Tasks)

**목표:** 전체 통합 테스트 및 문서화

| ID | Micro-Task | Agent | File | Status |
|----|------------|-------|------|--------|
| 6.1.1 | Create integration test directory | general-purpose | `tests/integration/` | ⬜ pending |
| 6.1.2 | Add E2E skill chain test | general-purpose | `tests/integration/test_skill_chain.py` | ⬜ pending |
| 6.2.1 | Read current CLAUDE.md | Explore | `CLAUDE.md` | ⬜ pending |
| 6.2.2 | Update PAI Integration section | general-purpose | `CLAUDE.md` | ⬜ pending |
| 6.2.3 | Add new skill patterns | general-purpose | `CLAUDE.md` | ⬜ pending |
| 6.3.1 | Read current skill-dependencies.md | Explore | `.claude/references/skill-dependencies.md` | ⬜ pending |
| 6.3.2 | Update dependency diagram | general-purpose | `.claude/references/skill-dependencies.md` | ⬜ pending |
| 6.4.1 | Create benchmark test file | general-purpose | `tests/benchmark/test_parallel_execution.py` | ⬜ pending |
| 6.5.1 | Create docs directory | general-purpose | `docs/` | ⬜ pending |
| 6.5.2 | Write custom commands guide | general-purpose | `docs/custom-commands-guide.md` | ⬜ pending |

**Phase 6 Progress:** 0/10 (0%)

---

## 📊 OVERALL PROGRESS DASHBOARD

| Phase | Description | Total | Done | Progress |
|-------|-------------|-------|------|----------|
| 1 | /ask Skill Enhancement | 12 | 12 | ✅✅✅✅✅✅✅✅✅✅✅✅ 100% |
| 2 | /plan Skill Enhancement | 14 | 14 | ✅✅✅✅✅✅✅✅✅✅✅✅✅✅ 100% |
| 3 | /audit Skill Enhancement | 12 | 12 | ✅✅✅✅✅✅✅✅✅✅✅✅ 100% |
| 4 | /deep-audit Skill Enhancement | 12 | 12 | ✅✅✅✅✅✅✅✅✅✅✅✅ 100% |
| 5 | Context Injection System | 12 | 12 | ✅✅✅✅✅✅✅✅✅✅✅✅ 100% |
| 6 | Integration & Testing | 10 | 0 | ⬜⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0% |
| **TOTAL** | | **72** | **62** | **86%** |

---

## 🔄 AGENT DELEGATION PATTERN

### Task Execution Pattern

```
Main Agent (Orchestrator)
    │
    ├── Explore Agent (Read-only analysis)
    │   └── Tasks: x.1.1, x.1.2 (reading files before modification)
    │
    └── general-purpose Agent (Execution)
        └── Tasks: All modification tasks
```

### Parallel Execution Groups

**Group A (Phase 1 can run parallel with setup):**
- 1.1.1 ~ 1.6.2 (sequential within phase)

**Group B (Phase 2-4 skill files - can batch):**
- 2.x.x, 3.x.x, 4.x.x (different files, can parallelize reads)

**Group C (Phase 5 Python module):**
- 5.x.x (sequential, dependencies)

**Group D (Phase 6 Integration):**
- 6.x.x (after all implementations complete)

---

## 📁 FILE OPERATION TRACKING

### Files to CREATE (8)

| File | Phase | Task | Status |
|------|-------|------|--------|
| `.claude/skills/ask.md` | 1 | 1.1.1 | ✅ done |
| `lib/oda/pai/skills/tests/test_ask_skill.py` | 1 | 1.6.1 | ✅ done |
| `tests/oda/pai/skills/test_plan_skill.py` | 2 | 2.7.1 | ⬜ pending |
| `tests/oda/pai/skills/test_audit_skill.py` | 3 | 3.6.1 | ⬜ pending |
| `tests/oda/pai/skills/test_deep_audit_skill.py` | 4 | 4.6.1 | ⬜ pending |
| `lib/oda/pai/skills/context_injector.py` | 5 | 5.1.1 | ⬜ pending |
| `tests/oda/pai/skills/test_context_injector.py` | 5 | 5.5.1 | ⬜ pending |
| `tests/integration/test_skill_chain.py` | 6 | 6.1.2 | ⬜ pending |

### Files to MODIFY (4)

| File | Phase | Tasks | Status |
|------|-------|-------|--------|
| `.claude/skills/plan.md` | 2 | 2.1.2 ~ 2.6.1 | ✅ done |
| `.claude/skills/audit.md` | 3 | 3.2.1 ~ 3.5.2 | ✅ done |
| `.claude/skills/deep-audit.md` | 4 | 4.2.1 ~ 4.5.1 | ✅ done |
| `lib/oda/pai/skills/router.py` | 5 | 5.4.2 ~ 5.4.3 | ⬜ pending |

---

## ⚠️ CRITICAL RULES FOR EXECUTION

### 1. Status Update Rule
```
태스크 완료 시 반드시:
1. 이 파일의 해당 태스크 Status를 ✅ done으로 변경
2. Progress bar 업데이트
3. "Current Execution State" 업데이트
4. Agent Registry에 사용된 agent_id 기록
```

### 2. Agent Delegation Rule
```
- Read 작업: Explore Agent 사용
- Write/Edit 작업: general-purpose Agent 사용
- 3+ 독립 태스크: run_in_background=true
- 각 Agent 호출 후 agent_id 기록
```

### 3. Context Window Rule
```
- 각 Agent 호출 시 이 plan file 경로 전달
- 각 태스크는 단일 파일/섹션에 집중
- 5개 이상 태스크 완료 후 이 파일 전체 저장
```

### 4. Auto-Compact Recovery Rule
```
Auto-Compact 발생 시:
1. Read(".agent/plans/custom_command_enhancement.md")
2. "Current Execution State" 확인
3. "Agent Registry"에서 running 상태 agent 확인
4. resume 파라미터로 agent 재개 또는 다음 태스크 시작
```

---

## 📝 EXECUTION LOG

| Timestamp | Task ID | Agent ID | Action | Result |
|-----------|---------|----------|--------|--------|
| 2026-01-13 11:38 | Research | a740d90 | V2.1.4 features | ✅ done |
| 2026-01-13 11:38 | Research | a062a9b | Structure explore | ✅ done |
| 2026-01-13 11:38 | Research | ac5f63b | Architecture plan | ✅ done |
| 2026-01-13 12:15 | 1.1.1-1.5.2 | a1edadf | Create /ask skill file | ✅ done |
| 2026-01-13 13:30 | 2.1.1-2.6.1 | adddca5 | Enhance /plan skill (V2.1.4) | ✅ done |
| 2026-01-13 14:00 | 4.1.1-4.5.1 | a8068c7 | Enhance /deep-audit skill (RSIL+BLOCK) | ✅ done |
| 2026-01-13 15:30 | 1.6.1-1.6.2 | opus-4.5 | Create /ask skill tests (76 tests) | ✅ done |
| 2026-01-13 16:00 | 3.6.1-3.6.2 | opus-4.5 | Create /audit skill tests (90+ tests) | ✅ done |
| 2026-01-13 17:30 | 5.1.1-5.5.2 | opus-4.5 | Implement Auto Full-Context-Injection System | ✅ done |

---

## 🎯 NEXT ACTIONS (Top 5)

1. **Task 2.7.1**: Create test file structure for /plan skill
2. **Task 2.7.2**: Add integration test cases for /plan skill
3. **Task 4.6.1**: Create test file structure for /deep-audit skill
4. **Task 4.6.2**: Add E2E test cases for /deep-audit skill
5. **Task 6.1.1**: Create integration test directory

---

> **Generated:** 2026-01-13 11:45:00
> **Last Updated:** 2026-01-13 17:30:00
> **Orchestrator:** Main Agent (Claude Opus 4.5)
