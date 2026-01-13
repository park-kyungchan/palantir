---
name: consolidate
description: Trigger Memory Consolidation Engine with 3-Stage ExecutionProtocol
---

# /consolidate Command

$ARGUMENTS

> **Protocol:** ExecutionProtocol (WARN enforcement)

메모리 통합 엔진을 실행하여 트레이스를 패턴으로 변환합니다.

---

## 3-Stage Protocol

### Stage A: PRE-CHECK

**Goal:** Validate environment before consolidation.

**Checklist:**
- [ ] `.agent/traces/` 디렉토리에 트레이스 파일 존재
- [ ] 데이터베이스 연결 가능
- [ ] 충돌하는 작업 없음

```bash
# 트레이스 파일 확인
ls -la /home/palantir/park-kyungchan/palantir/.agent/traces/

# DB 연결 확인
cd /home/palantir/park-kyungchan/palantir
source .venv/bin/activate
python -c "
from scripts.ontology.storage.database import Database
import asyncio
asyncio.run(Database().initialize())
print('DB connection OK')
"
```

---

### Stage B: EXECUTE

**Goal:** Run consolidation engine.

```bash
cd /home/palantir/park-kyungchan/palantir
source .venv/bin/activate
python scripts/consolidate.py
```

---

### Stage C: VALIDATE

**Goal:** Verify consolidation results.

**Checklist:**
- [ ] `.agent/memory/semantic/patterns/`에 새 파일 생성됨
- [ ] 출력 요약 확인
- [ ] 로그에 에러 없음

```bash
# 새로 생성된 패턴 확인
ls -la /home/palantir/park-kyungchan/palantir/.agent/memory/semantic/patterns/

# 최근 파일 확인
find /home/palantir/park-kyungchan/palantir/.agent/memory/semantic/patterns/ \
  -type f -mmin -5
```

---

## Protocol Enforcement

```python
from scripts.ontology.protocols.execution_protocol import ExecutionProtocol
from scripts.ontology.protocols import ProtocolContext
import asyncio

async def run_consolidation():
    protocol = ExecutionProtocol()
    context = ProtocolContext(
        target_path="consolidation",
        actor_id="claude_code_agent"
    )

    result = await protocol.execute(context)

    if result.passed:
        print("✅ Pre-checks passed, executing consolidation...")
        # Run actual consolidation
        import subprocess
        subprocess.run([
            "bash", "-c",
            "cd /home/palantir/park-kyungchan/palantir && "
            "source .venv/bin/activate && "
            "python scripts/consolidate.py"
        ])
    else:
        print("❌ Pre-checks failed:")
        for stage in result.stages:
            if not stage.passed:
                print(f"  Stage {stage.stage}: {stage.message}")

asyncio.run(run_consolidation())
```

---

## 출력 예시

```
=== Consolidation Report ===
Traces processed: 15
Patterns generated: 3
Insights extracted: 7
Duration: 2.3s
Status: SUCCESS
```
