# Task Management — Detailed Methodology
> On-demand reference. Contains PT YAML template, task creation templates, dependency patterns, status update table, ASCII visualization format, and failure sub-cases.

## PT Creation — Metadata Template

```json
{
  "type": "permanent",
  "tier": "TRIVIAL|STANDARD|COMPLEX",
  "current_phase": "P0",
  "commit_status": "pending",
  "references": [],
  "user_directives": []
}
```

## PT Phase Checkpoint — Compact Signal Examples

After each phase completion, add to `metadata.phase_signals`:

```json
{
  "phase_signals": {
    "p0": "PASS|reqs:6",
    "p1": "PASS|arch:4waves",
    "p2": "PASS|gaps:0",
    "p3": "PASS|tasks:12|deps:8"
  }
}
```

Format: `metadata.phase_signals.{phase} = "{STATUS}|{key_signal}"`. Enables compaction recovery: `TaskGet(PT)` → reads `phase_signals` → knows entire pipeline history.

## Work Task Batch — Metadata Template

```json
{
  "type": "work",
  "phase": "P7",
  "domain": "execution",
  "skill": "execution-code",
  "agent": "implementer",
  "files": ["src/target.ts"],
  "priority": "high",
  "parent": "{PT-task-id}",
  "problem": "기존 문제 상세 설명",
  "improvement": "이 작업이 문제를 어떻게 개선하는지"
}
```

## Real-Time Update Protocol

| Event | TaskUpdate Fields |
|-------|------------------|
| Start work | `status: "in_progress"`, `activeForm: "현재 작업 설명"` |
| Progress | `metadata: {progress update, partial results}` |
| Complete | `status: "completed"`, `metadata: {result summary}` |
| Failed | `status: "failed"`, `metadata: {error: "reason"}` |

Lead monitors via TaskList. No polling needed — state always current.

## ASCII Visualization Format (Korean Output)

```
╔═ 파이프라인 개요 ═══════════════════════════════╗
║  이름, 티어, 현재 단계, 전체 진행률             ║
╠═ 도메인별 진행률 ═══════════════════════════════╣
║  각 phase 진행 바 + 완료/전체 카운트            ║
╠═ 진행중 작업 ═══════════════════════════════════╣
║  #ID [agent] 진행중  N%                          ║
║      대상: 파일 목록                             ║
║      문제: 이 작업이 해결하려는 기존 문제        ║
║      개선: 어떻게 문제를 개선하는지 상세 설명    ║
║      차단: 의존성 / 후속: 이 작업을 기다리는 것  ║
╠═ 완료된 작업 ═══════════════════════════════════╣
║  #ID [agent] 완료 ✓                              ║
║      문제: → 결과: 구조                          ║
╠═ 대기중 작업 ═══════════════════════════════════╣
║  #ID [agent] 대기  ← 선행 작업 목록              ║
║      문제: → 계획: 구조                          ║
╠═ PT 참조사항 ═══════════════════════════════════╣
║  사용자 지시사항 + 코드베이스 참조               ║
╚═════════════════════════════════════════════════╝
```

Key rendering rules:
- `metadata.problem` → 문제 field (기존 상태의 무엇이 불충분한가)
- `metadata.improvement` → 개선/결과/계획 field (어떻게 개선하는가)
- Status labels: 진행중, 완료, 대기, 실패

## PT Description Density Management

- **Keep in PT description**: Core requirements, acceptance criteria, tier classification, key architecture decisions (up to ~2000 chars). Information that every teammate needs on `TaskGet`.
- **Move to file reference**: Extended design docs, full task breakdowns, detailed analysis reports. Store in workspace files and add file paths to `references[]`. Prevents PT description from becoming unwieldy.

## Work Task Granularity

- **Fine-grained** (1-2 files each): Use when tasks are highly parallelizable and independent. Each task maps to a single implementer assignment. Typical for execution phase.
- **Coarse-grained** (3-4 files each): Use when files are tightly coupled and must be modified atomically. Max 4 files per task to maintain single-responsibility.

## Dependency Chain Patterns

- **Linear chain**: T1 → T2 → T3. Use `addBlockedBy` for strict sequence. Simple but limits parallelism.
- **Diamond pattern**: T2 and T3 both depend on T1; T4 depends on both T2 and T3. Maximizes parallelism while respecting dependencies. Common for code + infra parallel execution converging at review.
- **No dependencies**: Fully independent tasks. No `addBlockedBy` needed. Used for parallel analysis in P0-P1.

## Failure Sub-Cases

### Duplicate PT Detection
- **Cause**: PT creation attempted when one already exists (pipeline-resume created a new PT without checking, or two pipeline starts raced).
- **Action**: `TaskList` to find all `[PERMANENT]` tasks. If multiple exist, compare metadata to determine which is authoritative (most recent, most complete). Complete the duplicate with `metadata.reason: "duplicate"`. Never delete.

### Circular Dependency in Work Tasks
- **Cause**: `addBlockedBy` creates a cycle (T1 blocks T2, T2 blocks T3, T3 blocks T1). Pipeline deadlocks.
- **Action**: Detect cycle by traversing `blockedBy` chains. Break at the weakest dependency. Document the decision in PT metadata.

### PT Metadata Corruption (Partial or Malformed)
- **Cause**: A `TaskUpdate` wrote partial or malformed metadata (JSON parse error, missing required fields like `type` or `current_phase`).
- **Action**: Read current PT state. Reconstruct missing fields from task history and pipeline context. Update with corrected metadata. Log corruption in PT metadata for audit trail.

### Work Task Status Stuck in_progress
- **Cause**: Agent crashed, exhausted turns, or was interrupted without updating status.
- **Action**: Lead detects via `TaskList`. If agent confirmed terminated, update task status to `failed` with `metadata.error: "agent_interrupted"`. Route to execution skill for re-assignment.

### Dead Teammate Blocking TeamDelete
- **Cause**: User killed a teammate process. Agent is dead but `config.json` still lists it as active. `TeamDelete` fails: "Cannot cleanup team with N active member(s)."
- **Action**: Edit `~/.claude/teams/{team-name}/config.json` directly to remove the dead member from `members` array. Then retry TeamDelete. Only CC-native workaround available.
