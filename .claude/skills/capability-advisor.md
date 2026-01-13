---
name: capability-advisor
description: |
  Claude Code Native Capabilities 추천 엔진. 사용자 요청 분석 시 자동으로 호출됩니다.
  Use proactively when: user asks "how do I...", user is confused, user mentions complex task.
  Recommends: Plan Mode, Explore Agent, MCP servers, Hooks, Extended Thinking, etc.
allowed-tools: Read, Grep, Glob
# ╔═════════════════════════════════════════════════════════════════════════╗
# ║ NATIVE CAPABILITY ENHANCEMENT: Forked Context with Explore Agent       ║
# ╠═════════════════════════════════════════════════════════════════════════╣
# ║ context: fork                                                           ║
# ║   - Creates an ISOLATED execution environment for this skill            ║
# ║   - Prevents contamination of main conversation context                 ║
# ║   - Allows deep codebase exploration without cluttering user session    ║
# ║   - Memory-efficient: forked context is discarded after skill completes ║
# ║                                                                         ║
# ║ agent: Explore                                                          ║
# ║   - Specialized for FAST, BROAD codebase analysis                       ║
# ║   - Optimized for pattern recognition and structure understanding       ║
# ║   - Lighter weight than general-purpose agent                           ║
# ║   - Perfect for capability discovery and recommendation tasks           ║
# ║                                                                         ║
# ║ WHY THIS COMBINATION?                                                   ║
# ║   1. User asks "how do I X?" → needs codebase context                   ║
# ║   2. Explore agent quickly scans relevant files                         ║
# ║   3. Forked context keeps exploration separate from main chat           ║
# ║   4. Returns only distilled recommendations to user                     ║
# ╚═════════════════════════════════════════════════════════════════════════╝
context: fork
agent: Explore
---

# Capability Advisor

사용자 요청에 따라 최적의 Claude Code 기능을 추천합니다.

## Native Capability Integration

이 스킬은 **Forked Context**와 **Explore Agent**를 활용하여 동작합니다:

### Forked Context 사용 이유
1. **격리된 실행 환경** - 사용자 대화 흐름을 방해하지 않음
2. **메모리 효율** - 탐색 후 컨텍스트 자동 해제
3. **깊은 분석 가능** - 많은 파일을 읽어도 메인 세션에 부담 없음

### Explore Agent 선택 이유
1. **빠른 코드베이스 스캔** - 구조 파악에 최적화
2. **패턴 인식** - 유사한 코드 패턴 빠르게 발견
3. **경량 실행** - 일반 에이전트보다 빠른 응답

---

## 상황별 추천

### 코드 분석이 필요할 때

**키워드:** 분석, 이해, 설명, 구조, 어떻게 동작

**추천:**
1. **Explore Agent** - 빠른 코드베이스 탐색
   ```
   "프로젝트 구조 분석해줘"
   ```

2. **/audit 명령어** - 코드 품질 검사
   ```
   /audit [경로]
   ```

3. **Read Tool** - 특정 파일 상세 분석
   ```
   "src/main.py 파일 분석해줘"
   ```

---

### 여러 파일을 수정해야 할 때

**키워드:** 리팩토링, 전체, 모든 파일, 대규모

**추천:**
1. **Plan Mode** - 안전한 계획 수립
   - `Shift+Tab` 두 번으로 활성화
   - 계획 검토 후 승인

2. **TodoWrite** - 작업 추적
   - 복잡한 작업 자동 분해
   - 진행 상황 실시간 표시

3. **Git Worktree** - 병렬 작업
   - 독립적인 작업 공간 생성

---

### 자동화가 필요할 때

**키워드:** 자동, 매번, 항상, 반복

**추천:**
1. **Hooks** - 이벤트 기반 자동화
   - SessionStart: 세션 시작 시
   - PreToolUse: 도구 사용 전
   - PostToolUse: 도구 사용 후

2. **Background Tasks** - 비동기 실행
   - `Ctrl+B`로 백그라운드 전환
   - 긴 작업 병렬 처리

3. **Skills** - 재사용 가능한 지식
   - 프로젝트별 커스텀 스킬

---

### 외부 서비스 연동이 필요할 때

**키워드:** GitHub, 데이터베이스, API, 연동

**추천:**
1. **MCP 서버**
   - `/mcp`로 상태 확인
   - 이미 연결된 서버:
     - github-mcp-server: GitHub API
     - tavily: 웹 검색
     - context7: 컨텍스트 관리
     - sequential-thinking: 추론
     - oda-ontology: 온톨로지 조회

---

### 복잡한 문제 해결이 필요할 때

**키워드:** 복잡한, 어려운, 깊이, 자세히

**추천:**
1. **Extended Thinking**
   - `Alt+T` 또는 "ultrathink"
   - 더 깊은 추론 활성화

2. **3-Stage Protocol**
   - Stage A: 분석 (SCAN)
   - Stage B: 추적 (TRACE)
   - Stage C: 검증 (VERIFY)

---

### 안전하게 작업하고 싶을 때

**키워드:** 안전, 실수, 걱정, 되돌리기

**추천:**
1. **Plan Mode**
   - 실행 전 계획 검토
   - `Shift+Tab` 두 번

2. **Checkpoints**
   - 자동 저장
   - `Esc Esc`로 되돌리기

3. **Governance Hooks**
   - 위험한 명령 자동 차단
   - rm -rf, sudo rm 등

---

## 기능 조합 패턴

### 대규모 리팩토링
```
1. Plan Mode 활성화
2. /audit으로 현재 상태 분석
3. TodoWrite로 작업 분해
4. 단계별 실행 및 검증
5. 완료 후 /audit으로 확인
```

### 새 기능 개발
```
1. Explore Agent로 관련 코드 탐색
2. Plan Mode로 설계
3. 구현
4. 테스트 작성
5. /audit으로 품질 확인
```

### 버그 수정
```
1. 에러 로그 분석
2. Grep으로 관련 코드 검색
3. Extended Thinking으로 원인 분석
4. Plan Mode로 수정 계획
5. 수정 및 테스트
```

---

## 빠른 참조

| 상황 | 추천 기능 | 활성화 방법 |
|------|----------|-------------|
| 분석 | Explore Agent | 자동 |
| 수정 | Plan Mode | Shift+Tab ×2 |
| 자동화 | Hooks | settings.json |
| 외부 연동 | MCP | /mcp |
| 깊은 사고 | Extended Thinking | Alt+T |
| 되돌리기 | Checkpoints | Esc ×2 |
| 추적 | TodoWrite | 자동 |
