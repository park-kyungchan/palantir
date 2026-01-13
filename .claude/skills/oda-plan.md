---
name: oda-plan
description: |
  Internal ODA planning protocol. Transforms requirements into schema-first implementation plans.
  DO NOT invoke directly - use /plan command which orchestrates this with Plan subagent.
allowed-tools: Read, Grep, Glob, Bash, TodoWrite
user-invocable: false
# ╔═════════════════════════════════════════════════════════════════════════╗
# ║ NATIVE CAPABILITY ENHANCEMENT: Forked Context with Plan Agent          ║
# ╠═════════════════════════════════════════════════════════════════════════╣
# ║ context: fork                                                           ║
# ║   - Creates an ISOLATED execution environment for planning              ║
# ║   - Prevents plan exploration from polluting main conversation          ║
# ║   - Enables deep requirement analysis without context overflow          ║
# ║   - Memory-efficient: planning context discarded after skill completes  ║
# ║                                                                         ║
# ║ agent: Plan                                                             ║
# ║   - Specialized for STRUCTURED implementation planning                  ║
# ║   - Optimized for multi-phase breakdown and dependency analysis         ║
# ║   - Focused on schema alignment and ODA pattern compliance              ║
# ║   - Perfect for 3-Stage Protocol orchestration                          ║
# ║                                                                         ║
# ║ WHY THIS COMBINATION?                                                   ║
# ║   1. /plan command requires deep requirement analysis                   ║
# ║   2. Plan agent specializes in structured breakdown                     ║
# ║   3. Forked context allows extensive file reading without bloat         ║
# ║   4. Returns only validated plan to main conversation                   ║
# ║                                                                         ║
# ║ INTEGRATION WITH /plan COMMAND:                                         ║
# ║   - /plan skill invokes this with context:fork automatically            ║
# ║   - Plan agent handles Stage A, B, C protocol execution                 ║
# ║   - Evidence collection happens in isolated context                     ║
# ║   - Final plan returned to user for approval                            ║
# ╚═════════════════════════════════════════════════════════════════════════╝
context: fork
agent: Plan
---

# ODA Planning Skill (3-Stage Protocol)

## Purpose
Convert user requirements into a governed, schema-first implementation plan.
Ensures all changes align with Ontology-Driven Architecture principles.

## Native Capability Integration

이 스킬은 **Forked Context**와 **Plan Agent**를 활용합니다:

### Forked Context 사용 이유
1. **격리된 계획 환경** - 복잡한 분석이 메인 대화를 방해하지 않음
2. **깊은 요구사항 분석** - 많은 파일을 읽어도 컨텍스트 오버플로우 없음
3. **증거 수집 최적화** - Stage A/B/C 증거가 별도 공간에서 관리됨

### Plan Agent 선택 이유
1. **구조화된 계획 수립** - 다단계 분해에 최적화
2. **의존성 분석** - 파일/모듈 간 관계 파악
3. **스키마 정합성** - ODA 패턴 준수 검증
4. **3-Stage Protocol** - Stage A, B, C 자동 실행

### /plan 명령어와의 통합
```
/plan <요구사항>
    │
    ▼
[Forked Context 생성]
    │
    ▼
[Plan Agent 활성화]
    │
    ├── Stage A: BLUEPRINT (요구사항 분석)
    ├── Stage B: INTEGRATION (솔루션 설계)
    └── Stage C: QUALITY GATE (계획 검증)
    │
    ▼
[검증된 계획 반환]
    │
    ▼
[사용자 승인 대기]
```

## Invocation
```
/oda-plan <요구사항>
```

## Protocol Flow

### Stage A: BLUEPRINT (Requirements Analysis)

**Goal:** Understand what needs to be built

**Actions:**
1. **Requirement Parsing**
   - Extract functional requirements
   - Identify non-functional constraints
   - Map to existing ObjectTypes

2. **Codebase Context**
   - Read relevant existing files
   - Identify integration points
   - Check for similar implementations

3. **Scope Definition**
   - Define boundaries (in-scope / out-of-scope)
   - Estimate complexity
   - Identify risks

**TodoWrite Integration:**
```
[x] Stage A: Parse requirements
[x] Stage A: Scan codebase
[x] Stage A: Define scope
[ ] Stage B: Design solution
[ ] Stage C: Validate plan
```

**Evidence Required:**
```yaml
files_viewed:
  - path/to/related/file1.py
  - path/to/related/file2.py
requirements:
  - "FR1: User can create tasks"
  - "FR2: Tasks have priorities"
  - "NFR1: Response time < 200ms"
complexity: medium
```

### Stage B: INTEGRATION TRACE (Solution Design)

**Goal:** Design the implementation approach

**Actions:**
1. **Schema Alignment**
   - Map requirements to ObjectTypes
   - Verify property types match
   - Check link cardinalities

2. **Action Design**
   - Define required Actions
   - Specify submission criteria
   - Plan side effects

3. **Phase Breakdown**
   ```markdown
   ### Phase 1: [Foundation]
   - Goal: Set up base structure
   - Files: [list]
   - Tests: [list]
   - Quality Gate: Build passes

   ### Phase 2: [Core Logic]
   - Goal: Implement main functionality
   - Files: [list]
   - Tests: [list]
   - Quality Gate: Tests pass

   ### Phase 3: [Integration]
   - Goal: Connect components
   - Files: [list]
   - Tests: [list]
   - Quality Gate: E2E passes
   ```

**Evidence Required:**
```yaml
imports_verified:
  - "from scripts.ontology.objects.task_types import Task"
  - "from scripts.ontology.actions import EditOperation"
signatures_matched:
  - "async def create_task(title: str, priority: TaskPriority) -> Task"
test_strategy: "Unit tests for each Action, integration test for workflow"
```

### Stage C: QUALITY GATE (Plan Validation)

**Goal:** Ensure plan is ready for execution

**Validation Checklist:**
- [ ] All ObjectTypes referenced exist in registry
- [ ] All Actions follow ODA patterns
- [ ] No blocked patterns in plan
- [ ] Evidence collected for all stages
- [ ] Risk mitigation defined

**Risk Assessment:**
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Schema mismatch | Low | High | Verify against registry |
| Integration failure | Medium | Medium | Incremental phases |
| Performance issue | Low | Medium | Load test in Stage C |

## Output Format

```markdown
# ODA Implementation Plan

## 1. Requirements Summary
| ID | Type | Description | Priority |
|----|------|-------------|----------|
| FR1 | Functional | ... | HIGH |

## 2. Schema Mapping
| Requirement | ObjectType | Property/Link |
|-------------|------------|---------------|
| FR1 | Task | title, priority |

## 3. Action Definitions
```python
@register_action("task.create")
class CreateTaskAction(OntologyAction):
    async def apply_edits(self, params: CreateTaskParams) -> Task:
        ...
```

## 4. Implementation Phases

### Phase 1: [Name] (Complexity: X)
- **Goal:** ...
- **Files to Create/Modify:**
  - `path/to/file.py` - Description
- **Tests:**
  - `test_file.py::test_case`
- **Quality Gate:** Build + Unit tests

### Phase 2: [Name] (Complexity: X)
...

## 5. Risk Register
[Risk table]

## 6. Evidence
- files_viewed: [...]
- requirements_traced: [...]
- schema_validated: true

## 7. Approval Gate
- [ ] Stage A evidence complete
- [ ] Stage B design approved
- [ ] Stage C validation passed
- [ ] User approval received
```

## Integration with TodoWrite

This skill automatically creates and updates todos:

```python
# Auto-generated todos for plan execution
todos = [
    {"content": "Phase 1: [Name]", "status": "pending"},
    {"content": "Phase 2: [Name]", "status": "pending"},
    {"content": "Phase 3: [Name]", "status": "pending"},
    {"content": "Run tests", "status": "pending"},
    {"content": "Documentation", "status": "pending"},
]
```

## Anti-Hallucination Rule

**CRITICAL:** Plans without file evidence are INVALID.

Before completing any stage:
1. Read at least one relevant file
2. Document the file in `files_viewed`
3. Reference specific line numbers for claims

```python
if not stage_result.evidence.get("files_viewed"):
    raise AntiHallucinationError(
        f"Stage {stage.name} completed without reading any files"
    )
```

## Example Usage

```
User: /oda-plan 사용자가 Task에 태그를 추가할 수 있는 기능 구현

Claude: 3-Stage Planning Protocol을 시작합니다.

## Stage A: BLUEPRINT

### 요구사항 분석
- FR1: 사용자가 Task에 여러 태그를 추가할 수 있음
- FR2: 태그는 문자열 배열로 저장됨
- NFR1: 기존 Task API와 호환 유지

### 파일 스캔
[Read scripts/ontology/objects/task_types.py]

### Evidence
files_viewed:
  - scripts/ontology/objects/task_types.py (lines 57-124)
complexity: small (2 phases)

...
```

## Protocol Integration

This skill executes through the ODA Protocol Adapter:

### Python Invocation
```python
from scripts.claude.protocol_adapter import ODAProtocolAdapter, PROTOCOL_REGISTRY

protocol_cls = PROTOCOL_REGISTRY.get("planning")
if protocol_cls:
    adapter = ODAProtocolAdapter(
        protocol=protocol_cls(),
        target_path="/home/palantir/park-kyungchan/palantir",
        session_id="<SESSION_ID>",
    )

    # Pass requirements through context
    adapter.oda_context.metadata["requirements"] = "$ARGUMENTS"

    result_a = await adapter.execute_stage_a()
    result_b = await adapter.execute_stage_b()
    result_c = await adapter.execute_stage_c()
```

### CLI Invocation
```bash
python -m scripts.claude.protocol_runner planning <target_path> --requirements "요구사항"
```
