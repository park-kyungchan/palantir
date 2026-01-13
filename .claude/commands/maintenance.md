---
name: maintenance
description: Database rebuild and schema validation (DESTRUCTIVE - requires explicit approval)
allowed-tools: Bash, Read, AskUserQuestion
---

# /maintenance Command

$ARGUMENTS

## CRITICAL WARNING

```
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
!  DESTRUCTIVE OPERATIONS - DATA LOSS POSSIBLE                  !
!  The 'rebuild' command will DELETE ALL existing data.         !
!  Explicit user approval via AskUserQuestion is MANDATORY.     !
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

---

## 사용법

```
/maintenance status       # 현재 DB 상태 확인
/maintenance validate     # 스키마 유효성 검사
/maintenance rebuild      # DB 재구축 (DESTRUCTIVE)
/maintenance migrate      # Alembic 마이그레이션 실행
```

---

## 작업 설명

### status - DB 상태 확인
```bash
cd /home/palantir/park-kyungchan/palantir
source .venv/bin/activate
python -c "
from scripts.ontology.storage.database import Database
import asyncio

async def check():
    db = Database()
    await db.initialize()
    health = await db.health_check()
    print('Database Health:', health)

asyncio.run(check())
"
```

### validate - 스키마 유효성 검사
```bash
cd /home/palantir/park-kyungchan/palantir
source .venv/bin/activate
python -m scripts.ontology.registry
```

### rebuild - DB 재구축 (DESTRUCTIVE)

**MANDATORY: Before executing rebuild, you MUST use AskUserQuestion:**

```
AskUserQuestion(
  questions=[{
    "question": "WARNING: 'rebuild' will DELETE ALL DATA. This is IRREVERSIBLE. Proceed?",
    "header": "DESTRUCTIVE",
    "options": [
      {"label": "Yes, rebuild", "description": "Delete all data and rebuild from scratch"},
      {"label": "No, cancel", "description": "Abort without changes"}
    ],
    "multiSelect": false
  }]
)
```

**ONLY if user selects "Yes"**, execute:

```bash
# Step 1: Backup FIRST
cp /home/palantir/park-kyungchan/palantir/.agent/tmp/ontology.db \
   /home/palantir/park-kyungchan/palantir/.agent/tmp/ontology.db.backup.$(date +%Y%m%d_%H%M%S)

# Step 2: Delete and rebuild
cd /home/palantir/park-kyungchan/palantir
rm -f .agent/tmp/ontology.db
source .venv/bin/activate
python -c "
from scripts.ontology.storage.database import initialize_database
import asyncio
asyncio.run(initialize_database())
print('Database rebuilt successfully')
"
```

**If user selects "No"**: Stop immediately and report cancellation.

### migrate - Alembic 마이그레이션
```bash
cd /home/palantir/park-kyungchan/palantir
source .venv/bin/activate
alembic upgrade head
```

---

## 안전 체크리스트

**rebuild 실행 전:**
- [ ] 현재 DB 백업 완료
- [ ] 진행 중인 작업 없음 확인
- [ ] 명시적 승인 획득

---

## 백업 방법

```bash
# DB 백업
cp /home/palantir/park-kyungchan/palantir/.agent/tmp/ontology.db \
   /home/palantir/park-kyungchan/palantir/.agent/tmp/ontology.db.backup.$(date +%Y%m%d_%H%M%S)
```

---

## Error Handling

| Error | Action |
|-------|--------|
| User denies approval | Cancel immediately, report "Operation cancelled" |
| Backup fails | Do NOT proceed, report error |
| Rebuild fails | Attempt restore from backup |

**REMEMBER: Never execute rebuild without explicit AskUserQuestion approval.**
