---
name: freewheelin
description: >-
  math-question-bank dev environment: Docker PostgreSQL (5432) + Next.js (3000).
  Modes: start | status | stop. Checks prerequisites, DB migration, port state.
user-invocable: true
argument-hint: "[start|status|stop]"
disable-model-invocation: false
---

## FreeWheelin 개발환경 관리

`$ARGUMENTS`가 없으면 `start` 모드로 실행합니다.

---

### Mode: `status` — 현재 상태만 확인

```bash
docker ps --filter name=math --format "{{.Names}}: {{.Status}}"
lsof -ti:5432 && echo "port 5432: occupied" || echo "port 5432: free"
lsof -ti:3000 && echo "port 3000: occupied" || echo "port 3000: free"
```

결과를 Status Output 형식으로 출력하고 종료합니다.

---

### Mode: `stop` — 서비스 종료

```bash
# dev server 종료
kill $(lsof -ti:3000) 2>/dev/null || echo "dev server not running"

# Docker 종료
docker compose -f /home/palantir/math-question-bank/docker/docker-compose.yml down
```

---

### Mode: `start` — 전체 시작 시퀀스

**Step 1 — Prerequisites 확인**

```bash
docker info > /dev/null 2>&1
```

- 실패(exit code != 0) → 오류 출력 후 **즉시 중단**: `오류: Docker daemon이 실행 중이지 않습니다. Docker Desktop을 시작한 후 다시 시도하세요.`
- 성공 → Step 2 진행

**Step 2 — PostgreSQL 컨테이너 시작**

```bash
docker compose -f /home/palantir/math-question-bank/docker/docker-compose.yml up -d
```

- 성공 → Step 3 진행
- 실패 → 오류 출력 후 중단: `오류: PostgreSQL 컨테이너 시작 실패. docker compose logs로 확인하세요.`

**Step 3 — DB 마이그레이션 확인**

```bash
cd /home/palantir/math-question-bank && pnpm db:push
```

- 테이블이 이미 최신 → "No changes" 출력, 정상 진행
- 첫 실행(신규 테이블 생성) → 이후 seed도 실행: `pnpm db:seed`
- 실패 → 오류 출력: `오류: DB 마이그레이션 실패. PostgreSQL 연결 상태를 확인하세요.`

**Step 4 — Dev Server 시작**

```bash
lsof -ti:3000
```

- 결과 있음(포트 사용 중) → 이미 실행 중, 스킵
- 결과 없음 → `run_in_background: true`로 실행:

```bash
cd /home/palantir/math-question-bank && pnpm dev
```

5초 대기 후 로그에서 `Ready` 또는 `Local:` 확인. 미확인 시: `경고: dev 서버 시작 확인 실패. http://localhost:3000 수동 확인 필요.`

**Step 5 — Status Output**

```
✓ Docker       → running
✓ PostgreSQL   → localhost:5432 (healthy)
✓ DB Schema    → up to date
✓ Dev Server   → http://localhost:3000
```

---

## Troubleshooting

| 증상 | 원인 | 해결 |
|------|------|------|
| `docker info` 실패 | Docker daemon 미실행 | Docker Desktop 시작 후 재시도 |
| 포트 5432 충돌 | 로컬 Postgres 실행 중 | `sudo service postgresql stop` |
| 포트 3000 충돌 | 다른 프로세스 점유 | `kill $(lsof -ti:3000)` 후 재시도 |
| `pnpm db:push` 실패 | DB 미연결 | Step 2 완료 여부 재확인, 컨테이너 healthy 대기 |
| `pnpm` 미설치 | pnpm 없음 | `npm install -g pnpm` 후 재시도 |
