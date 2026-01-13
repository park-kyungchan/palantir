# ODA Migration Scripts

> scripts/ -> lib/oda/ 네임스페이스 마이그레이션 자동화 스크립트

## 스크립트 개요

| 스크립트 | 목적 | 예상 시간 |
|---------|------|----------|
| `migrate_phase1.sh` | 디렉토리 생성 및 파일 복사 | 1-2분 |
| `migrate_phase2.sh` | Import 문 변경 (from scripts. -> from lib.oda.) | 1-2분 |
| `migrate_phase3.sh` | 하드코딩된 경로 수정 | 1분 |
| `migrate_phase4.sh` | MCP 및 환경 설정 업데이트 | 1분 |
| `migrate_phase5_test.sh` | 테스트 실행 및 검증 | 2-5분 |
| `migrate_phase6_symlink.sh` | 호환성 심링크 생성 | 1분 |
| `rollback_all.sh` | 전체 롤백 | 1-2분 |
| `verify_migration.sh` | 종합 검증 | 1분 |

## 사용법

### Dry-Run (변경 없이 미리보기)

모든 스크립트는 `--dry-run` 옵션을 지원합니다:

```bash
./migrate_phase1.sh --dry-run
./migrate_phase2.sh -n  # 단축 옵션
```

### 전체 마이그레이션

```bash
cd /home/palantir/docs/plans/scripts

# Phase 1: 디렉토리 생성 및 파일 복사
./migrate_phase1.sh

# Phase 2: Import 문 변경
./migrate_phase2.sh

# Phase 3: 하드코딩된 경로 수정
./migrate_phase3.sh

# Phase 4: 환경 설정 업데이트
./migrate_phase4.sh

# Phase 5: 테스트 실행
./migrate_phase5_test.sh

# Phase 6: 호환성 심링크 생성
./migrate_phase6_symlink.sh

# 최종 검증
./verify_migration.sh
```

### 롤백

문제 발생 시 원래 상태로 복원:

```bash
./rollback_all.sh --dry-run  # 먼저 미리보기
./rollback_all.sh            # 실제 롤백
```

## 각 Phase 상세

### Phase 1: 디렉토리 생성 및 파일 복사

- `lib/oda/` 디렉토리 구조 생성
- `scripts/`에서 모든 Python 파일 복사
- `__init__.py` 파일 생성
- 백업 생성 (`.migration_backup/`)

### Phase 2: Import 리팩토링

- `from scripts.X` -> `from lib.oda.X` 변경
- `import scripts.X` -> `import lib.oda.X` 변경
- 대상: lib/oda/, tests/, scripts/

### Phase 3: 하드코딩된 경로 수정

- 문자열 경로 수정: `"scripts/"` -> `"lib/oda/"`
- sys.path 수정
- 16개 파일 대상

### Phase 4: 환경 설정 업데이트

- `.mcp.json` 업데이트
- `.env` 파일 생성/수정
- PYTHONPATH 설정
- CLAUDE.md 업데이트

### Phase 5: 테스트 실행

- Import 검증
- 모듈 구조 검증
- MCP 서버 테스트
- Registry 초기화 테스트
- Unit 테스트 실행

### Phase 6: 심링크 생성

- `scripts/` 호환성 레이어 생성
- DeprecationWarning 설정
- `setup_env.sh` 생성

## 로그 및 백업

모든 작업은 다음 위치에 기록됩니다:

```
.migration_backup/
├── YYYYMMDD_HHMMSS/     # 타임스탬프된 백업
│   ├── scripts_backup/   # 원본 scripts/ 백업
│   └── lib_oda_backup/   # 기존 lib/oda/ 백업 (있는 경우)
├── latest               # 최신 백업 경로
├── phase1.log
├── phase2.log
├── phase3.log
├── phase4.log
├── phase5.log
├── phase6.log
├── rollback.log
├── verify.log
├── phase2_report.txt
├── phase5_report.txt
└── verification_report.txt
```

## 요구사항

- Bash 4.0+
- Python 3.8+
- sed, grep, find (GNU coreutils)
- pytest (Phase 5 테스트용, 선택사항)

## 문제 해결

### Import 오류 발생 시

```bash
# PYTHONPATH 확인
echo $PYTHONPATH

# 수동 설정
export PYTHONPATH="/home/palantir/park-kyungchan/palantir:$PYTHONPATH"
```

### 롤백 실패 시

```bash
# 수동 복원
cd /home/palantir/park-kyungchan/palantir
rm -rf lib/oda
cp -r .migration_backup/LATEST_TIMESTAMP/scripts_backup scripts
```

### 테스트 실패 시

```bash
# 상세 로그 확인
cat .migration_backup/phase5.log

# 개별 import 테스트
python -c "from lib.oda.ontology.registry import ActionRegistry"
```

## 주의사항

1. **백업 확인**: 마이그레이션 전 `.migration_backup/` 생성 확인
2. **순차 실행**: Phase 1-6 순서대로 실행
3. **테스트 필수**: Phase 5 통과 후 Phase 6 진행
4. **IDE 재시작**: 마이그레이션 후 IDE/에디터 재시작 권장
