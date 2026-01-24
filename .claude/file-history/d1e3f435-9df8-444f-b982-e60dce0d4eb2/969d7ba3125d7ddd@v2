---
name: permission-mode
description: |
  Shared parameter module for permission mode selection.
  Used by: Agent builder, CLI configuration
context: fork
model: haiku
version: "1.0.0"
allowed-tools:
  - AskUserQuestion
---

# Permission Mode Parameter Module

> **Purpose:** Agent 실행 시 권한 승인 동작 설정
> **Caller:** agent-builder, settings configuration

---

## Parameters Covered

| Parameter | Type | Values | Version | Used By |
|-----------|------|--------|---------|---------|
| `permissionMode` | enum | default, acceptEdits, dontAsk, bypassPermissions, plan | V2.0+ | Agent, CLI |

---

## Round 1: Permission Mode Selection

### Input Context
```yaml
component_type: "{agent|cli-config}"  # Caller provides
use_case: "{general|automation|...}"  # Context for recommendation
current_selection: null               # Or previous value for resume
```

### Q&A Flow

```python
response = AskUserQuestion(
    questions=[{
        "question": "실행 권한 모드를 선택하세요",
        "header": "Permission",
        "options": [
            {
                "label": "default (Recommended)",
                "description": "모든 작업에 사용자 승인 필요. 가장 안전함"
            },
            {
                "label": "acceptEdits",
                "description": "파일 편집/쓰기 자동 승인. Bash는 승인 필요"
            },
            {
                "label": "plan",
                "description": "플래닝 모드로 시작. 읽기 전용 분석 후 계획 수립"
            },
            {
                "label": "dontAsk",
                "description": "대부분 자동 승인. 주의: 위험한 작업 가능"
            }
        ],
        "multiSelect": False
    }],
    metadata={"source": "build-permission-mode"}
)
```

---

## Permission Mode Details

### default
```yaml
behavior:
  - 모든 도구 사용 시 사용자 승인 필요
  - 가장 안전한 모드
  - 인터랙티브 작업에 적합
security_level: "★★★★★"
use_case:
  - 민감한 코드베이스
  - 처음 사용하는 환경
  - 학습 목적
```

### acceptEdits
```yaml
behavior:
  - Read, Write, Edit: 자동 승인
  - Glob, Grep: 자동 승인
  - Bash: 여전히 승인 필요
  - 외부 네트워크: 승인 필요
security_level: "★★★★☆"
use_case:
  - 코드 리팩토링 작업
  - 파일 편집 위주 작업
  - 중간 수준 자동화
```

### plan
```yaml
behavior:
  - 읽기 전용 모드로 시작
  - 분석 완료 후 계획 제시
  - 사용자 승인 후 실행 단계로 전환
security_level: "★★★★★"
use_case:
  - 대규모 리팩토링 계획
  - 코드베이스 분석
  - 신중한 접근 필요 시
```

### dontAsk
```yaml
behavior:
  - 대부분의 작업 자동 승인
  - 일부 위험 작업만 승인 요청
security_level: "★★☆☆☆"
use_case:
  - 신뢰할 수 있는 자동화 스크립트
  - 반복적인 루틴 작업
  - 경험 있는 사용자 전용
warning: "주의: 의도치 않은 파일 수정/삭제 가능"
```

### bypassPermissions
```yaml
behavior:
  - 모든 작업 자동 승인
  - 권한 검사 완전 비활성화
security_level: "★☆☆☆☆"
use_case:
  - CI/CD 환경
  - 완전 자동화 파이프라인
  - 격리된 테스트 환경
warning: "매우 위험: 프로덕션 환경에서 사용 금지"
hidden: true  # 일반 선택지에서 숨김
```

---

## Security Matrix

| Mode | File Read | File Write | Bash | Network | Risk Level |
|------|-----------|------------|------|---------|------------|
| default | ✓ Ask | ✓ Ask | ✓ Ask | ✓ Ask | 최소 |
| acceptEdits | Auto | Auto | ✓ Ask | ✓ Ask | 낮음 |
| plan | Auto | ✗ Blocked | ✗ Blocked | ✓ Ask | 최소 |
| dontAsk | Auto | Auto | Auto* | Auto* | 높음 |
| bypassPermissions | Auto | Auto | Auto | Auto | 매우 높음 |

*`dontAsk`도 일부 위험한 패턴은 차단됨 (예: `rm -rf /`)

---

## CLI Flag Mapping

| Frontmatter | CLI Equivalent |
|-------------|----------------|
| `permissionMode: default` | (기본값, 플래그 없음) |
| `permissionMode: acceptEdits` | `--allowedTools 'Edit(*)'` |
| `permissionMode: plan` | `--permission-mode plan` |
| `permissionMode: dontAsk` | `--dangerously-skip-permissions` |
| `permissionMode: bypassPermissions` | (직접 노출 안 함) |

---

## Output Format

### Return to Caller

```yaml
permission_config:
  permissionMode: "default"
  security_level: "★★★★★"
  selection_reason: "가장 안전한 기본 모드"
```

### YAML Frontmatter Fragment

```yaml
# For Agent output
permissionMode: default
```

---

## Decision Tree

```
권한 모드 선택
    │
    ├── 안전이 최우선? ──Yes──► default 또는 plan
    │   │
    │   └── 분석 먼저? ──Yes──► plan
    │                    No──► default
    │
    ├── 파일 편집 자동화? ──Yes──► acceptEdits
    │
    └── 완전 자동화? ──Yes──► dontAsk (주의!)
                       │
                       └── CI/CD 환경? ──Yes──► bypassPermissions (숨김)
```

---

## Version History

| Version | Change |
|---------|--------|
| V2.0+ | `permissionMode` 파라미터 도입 |
| V2.1+ | `plan` 모드 추가 |
| V2.1.16+ | CLI `--permission-mode` 플래그 지원 |

---

## Related Modules

| Module | Relationship |
|--------|--------------|
| `agent-builder.md` | Agent 생성 시 권한 모드 설정 |
| `tool-config.md` | 특정 도구 허용/차단과 연계 |
