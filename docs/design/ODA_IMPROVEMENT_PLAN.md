# Orion ODA 아키텍처 개선 계획서

> **문서 버전**: v1.0
> **작성일**: 2025-12-14
> **대상**: Orion Orchestrator v2.0 → v3.0 마이그레이션
> **기반 청사진**: API-less LLM Orchestration Architecture

---

## Executive Summary

현재 Orion ODA는 파일 기반 수동 릴레이에 의존하는 4단계 라이프사이클 시스템입니다. 본 계획은 **하이브리드 아키텍처**로의 전환을 제안합니다:

1. **로컬 LLM (Ollama)** - 60-70% 작업 자동 처리
2. **최적화된 릴레이 프로토콜** - 클립보드 자동화 + 데스크톱 알림
3. **Palantir 스타일 액션 큐** - 제안 기반 워크플로우 + 멱등성 보장
4. **컨텍스트 압축** - LLMLingua 통합으로 릴레이 부담 최소화

---

## 1. 현재 상태 분석 (AS-IS)

### 1.1 기존 아키텍처 강점

| 컴포넌트 | 구현 상태 | 비고 |
|----------|----------|------|
| OrionObject 모델 | ✅ 완료 | UUIDv7, 버전 관리, dirty-checking |
| SQLAlchemy 영속성 | ✅ 완료 | WAL 모드, 단일 테이블 패턴 |
| Action Framework | ✅ 완료 | UnitOfWork, ActionRunner |
| Simulation Engine | ✅ 완료 | SAVEPOINT 기반 샌드박스 |
| Governance Layer | ✅ 완료 | 감사 로그, ActionDispatcher |
| Memory System | ⚠️ 부분 | FTS5 완료, 벡터 검색 미완성 |
| Handoff Protocol | ✅ 완료 | 마크다운 템플릿 주입 |

### 1.2 핵심 격차 (Gap Analysis)

| 영역 | 현재 상태 | 목표 상태 | 우선순위 |
|------|----------|----------|----------|
| **LLM 통합** | 없음 (수동 릴레이) | Ollama + 하이브리드 라우팅 | P0 |
| **작업 큐** | 없음 (순차 실행) | Redis Queue + 재시도 정책 | P0 |
| **릴레이 UX** | 파일 복사-붙여넣기 | 클립보드 자동화 + 토스트 알림 | P1 |
| **컨텍스트 압축** | 없음 | LLMLingua-2 통합 | P1 |
| **실시간 상태** | 없음 | Observer 영속화 + 스트리밍 | P2 |

---

## 2. 목표 아키텍처 (TO-BE)

### 2.1 하이브리드 라우팅 아키텍처

```
┌─────────────────────────────────────────────────────────────────┐
│                    Orion ODA v3.0 Architecture                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────────────────────────────┐    │
│  │   Intent    │───▶│         Hybrid Router               │    │
│  │   Input     │    │  ┌─────────────┬─────────────────┐  │    │
│  └─────────────┘    │  │ Task Type   │ Route Decision  │  │    │
│                     │  ├─────────────┼─────────────────┤  │    │
│                     │  │ JSON Valid  │ → Ollama (Local)│  │    │
│                     │  │ Schema Check│ → Ollama (Local)│  │    │
│                     │  │ Text Parse  │ → Ollama (Local)│  │    │
│                     │  │ Classify    │ → Ollama (Local)│  │    │
│                     │  │ Complex     │ → Human Relay   │  │    │
│                     │  │ Reasoning   │ → Human Relay   │  │    │
│                     │  └─────────────┴─────────────────┘  │    │
│                     └─────────────────────────────────────┘    │
│                            │                │                   │
│                     ┌──────▼──────┐  ┌──────▼──────┐           │
│                     │   Ollama    │  │   Relay     │           │
│                     │   Service   │  │   Queue     │           │
│                     │  (60-70%)   │  │  (30-40%)   │           │
│                     │             │  │             │           │
│                     │ Qwen2.5 7B  │  │ Clipboard   │           │
│                     │ Phi-3 Mini  │  │ + Toast     │           │
│                     │ Llama 3.1   │  │ + waitPaste │           │
│                     └──────┬──────┘  └──────┬──────┘           │
│                            │                │                   │
│                            └───────┬────────┘                   │
│                                    ▼                            │
│                     ┌─────────────────────────────┐             │
│                     │      Action Queue           │             │
│                     │  (Palantir Hub-Spoke)       │             │
│                     │                             │             │
│                     │  • Idempotency Keys         │             │
│                     │  • Retry with Backoff       │             │
│                     │  • Priority Levels          │             │
│                     │  • Cryptographic Signing    │             │
│                     └──────────────┬──────────────┘             │
│                                    ▼                            │
│                     ┌─────────────────────────────┐             │
│                     │    Governance Layer         │             │
│                     │  (Existing ActionDispatcher)│             │
│                     └──────────────┬──────────────┘             │
│                                    ▼                            │
│                     ┌─────────────────────────────┐             │
│                     │    Persistence Layer        │             │
│                     │  (SQLite + ObjectManager)   │             │
│                     └─────────────────────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 릴레이 상태 머신

```
              User Copies Prompt
                     │
    ┌────────────────▼────────────────┐
    │           PENDING               │
    │   (Queue에 작업 추가됨)          │
    └────────────────┬────────────────┘
                     │ dequeue()
    ┌────────────────▼────────────────┐
    │       READY_FOR_RELAY           │
    │   • Clipboard에 프롬프트 복사    │
    │   • Toast 알림 전송             │
    └────────────────┬────────────────┘
                     │ waitForNewPaste()
    ┌────────────────▼────────────────┐
    │      AWAITING_RESPONSE          │
    │   • 클립보드 변경 감지 대기      │
    │   • Timeout: 600초              │
    └────────────────┬────────────────┘
                     │
         ┌──────────┴──────────┐
         │                     │
    ┌────▼─────┐          ┌────▼─────┐
    │ COMPLETED│          │  FAILED  │
    │ (응답 수신)│          │(타임아웃) │
    └──────────┘          └──────────┘
```

---

## 3. 구현 Phase 상세

### Phase 1: 로컬 LLM 기반 구축 (Week 1-2)

#### 3.1.1 신규 모듈: `scripts/llm/`

```
scripts/llm/
├── __init__.py
├── ollama_client.py    # Ollama HTTP 클라이언트
├── router.py           # 하이브리드 라우팅 로직
├── models.py           # Pydantic 출력 스키마
└── prompts/
    ├── json_validation.txt
    ├── schema_check.txt
    └── text_extraction.txt
```

#### 3.1.2 `ollama_client.py` 핵심 설계

```python
# scripts/llm/ollama_client.py
from pydantic import BaseModel
from typing import TypeVar, Type
import httpx

T = TypeVar('T', bound=BaseModel)

class OllamaClient:
    """Ollama API 클라이언트 (Pydantic 네이티브 통합)"""

    def __init__(self, host: str = "http://127.0.0.1:11434"):
        self.host = host
        self.client = httpx.Client(timeout=60.0)

    def generate_structured(
        self,
        prompt: str,
        response_model: Type[T],
        model: str = "qwen2.5:7b-instruct-q4_K_M",
        temperature: float = 0.0
    ) -> T:
        """Pydantic 스키마 기반 구조화된 출력 생성"""
        response = self.client.post(
            f"{self.host}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "format": response_model.model_json_schema(),
                "stream": False,
                "options": {"temperature": temperature}
            }
        )
        return response_model.model_validate_json(response.json()["response"])
```

#### 3.1.3 `router.py` 하이브리드 라우팅

```python
# scripts/llm/router.py
from enum import Enum
from typing import Callable

class RouteTarget(Enum):
    OLLAMA = "ollama"
    HUMAN_RELAY = "human_relay"

class HybridRouter:
    """작업 유형에 따른 LLM 라우팅 결정"""

    LOCAL_TASKS = frozenset([
        'json_validation',
        'schema_check',
        'text_parsing',
        'simple_classification',
        'data_extraction',
        'format_conversion'
    ])

    def route(self, task_type: str, prompt: str, confidence_threshold: float = 0.8) -> RouteTarget:
        """
        라우팅 결정 로직:
        1. 작업 유형이 LOCAL_TASKS에 포함되면 → Ollama
        2. 프롬프트 복잡도가 threshold 미만이면 → Ollama
        3. 그 외 복잡한 추론 → Human Relay
        """
        if task_type in self.LOCAL_TASKS:
            return RouteTarget.OLLAMA

        complexity = self._estimate_complexity(prompt)
        if complexity < confidence_threshold:
            return RouteTarget.OLLAMA

        return RouteTarget.HUMAN_RELAY

    def _estimate_complexity(self, prompt: str) -> float:
        """프롬프트 복잡도 휴리스틱 (0.0~1.0)"""
        # 단어 수, 중첩 구조, 추론 키워드 기반 점수화
        word_count = len(prompt.split())
        reasoning_keywords = ['analyze', 'compare', 'design', 'architect', 'explain why']
        keyword_score = sum(1 for kw in reasoning_keywords if kw in prompt.lower()) / len(reasoning_keywords)

        length_score = min(word_count / 500, 1.0)
        return (length_score + keyword_score) / 2
```

#### 3.1.4 의존성 추가 (`pyproject.toml`)

```toml
[project]
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "uuid6",
    # Phase 1: Local LLM
    "httpx>=0.27.0",           # Ollama HTTP 클라이언트
]

[project.optional-dependencies]
llm = [
    "ollama>=0.4.0",           # 공식 Ollama 파이썬 SDK
    "sentence-transformers>=2.2", # 시맨틱 라우팅용
]
```

#### 3.1.5 환경 설정

```bash
# .env.example
OLLAMA_HOST=127.0.0.1:11434
OLLAMA_NUM_PARALLEL=4
OLLAMA_MAX_LOADED_MODELS=2
ORION_DEFAULT_MODEL=qwen2.5:7b-instruct-q4_K_M
```

---

### Phase 2: 릴레이 프로토콜 코어 (Week 3-4)

#### 3.2.1 신규 모듈: `scripts/relay/`

```
scripts/relay/
├── __init__.py
├── clipboard.py        # pyperclip 래퍼
├── notification.py     # Windows Toast 알림
├── queue.py           # SQLite 기반 작업 큐
├── executor.py        # 릴레이 실행 오케스트레이터
└── compression.py     # LLMLingua 컨텍스트 압축
```

#### 3.2.2 `clipboard.py` 클립보드 자동화

```python
# scripts/relay/clipboard.py
import pyperclip
from typing import Optional
import time

class ClipboardManager:
    """클립보드 기반 릴레이 인터페이스"""

    def copy_prompt(self, prompt: str) -> None:
        """프롬프트를 클립보드에 복사"""
        pyperclip.copy(prompt)

    def wait_for_response(self, timeout: int = 600) -> Optional[str]:
        """
        클립보드 변경 감지 대기

        pyperclip.waitForNewPaste() 사용:
        - 블로킹 방식으로 클립보드 변경 감지
        - 사용자가 LLM 응답을 복사하면 자동 반환
        """
        try:
            return pyperclip.waitForNewPaste(timeout=timeout)
        except pyperclip.PyperclipTimeoutException:
            return None

    def get_current(self) -> str:
        """현재 클립보드 내용 반환"""
        return pyperclip.paste()
```

#### 3.2.3 `notification.py` 데스크톱 알림

```python
# scripts/relay/notification.py
import webbrowser
from typing import Callable, Optional

# Windows 전용 - Linux/WSL2에서는 대체 구현 필요
try:
    from win10toast_click import ToastNotifier
    TOAST_AVAILABLE = True
except ImportError:
    TOAST_AVAILABLE = False

class NotificationManager:
    """데스크톱 알림 관리"""

    def __init__(self):
        self.toaster = ToastNotifier() if TOAST_AVAILABLE else None

    def notify_relay_ready(
        self,
        prompt_length: int,
        target_url: str = "https://claude.ai",
        callback: Optional[Callable] = None
    ) -> None:
        """릴레이 준비 알림 전송"""
        if not self.toaster:
            print(f"[RELAY] Prompt ready ({prompt_length} chars). Open {target_url}")
            return

        self.toaster.show_toast(
            title="Orion Relay Task Ready",
            msg=f"Prompt copied ({prompt_length} chars). Click to open Claude.",
            duration=10,
            threaded=True,
            callback_on_click=callback or (lambda: webbrowser.open(target_url))
        )

    def notify_response_received(self, response_length: int) -> None:
        """응답 수신 알림"""
        if self.toaster:
            self.toaster.show_toast(
                title="Orion Response Received",
                msg=f"Response captured ({response_length} chars).",
                duration=5
            )
```

#### 3.2.4 `queue.py` SQLite 기반 작업 큐

```python
# scripts/relay/queue.py
from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import declarative_base, sessionmaker
import hashlib
import uuid

Base = declarative_base()

class RelayStatus(str, Enum):
    PENDING = "pending"
    READY_FOR_RELAY = "ready_for_relay"
    AWAITING_RESPONSE = "awaiting_response"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class RelayTask(Base):
    """릴레이 작업 영속성 모델"""
    __tablename__ = "relay_tasks"

    id = Column(String, primary_key=True)
    idempotency_key = Column(String, unique=True, index=True)
    prompt = Column(Text, nullable=False)
    compressed_prompt = Column(Text)
    response = Column(Text)
    status = Column(SQLEnum(RelayStatus), default=RelayStatus.PENDING)
    priority = Column(Integer, default=0)  # 높을수록 우선
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    timeout_seconds = Column(Integer, default=600)
    job_id = Column(String, index=True)  # 연관 Job 참조

class RelayQueue:
    """Palantir 스타일 액션 큐"""

    def __init__(self, db_path: str = ".agent/relay_queue.db"):
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def enqueue(
        self,
        prompt: str,
        job_id: Optional[str] = None,
        priority: int = 0,
        idempotency_key: Optional[str] = None
    ) -> RelayTask:
        """
        작업 큐에 추가 (멱등성 보장)

        idempotency_key가 이미 존재하면 기존 작업 반환
        """
        if idempotency_key is None:
            idempotency_key = hashlib.sha256(prompt.encode()).hexdigest()[:16]

        session = self.Session()
        try:
            # 멱등성 체크
            existing = session.query(RelayTask).filter_by(
                idempotency_key=idempotency_key
            ).first()

            if existing:
                return existing

            task = RelayTask(
                id=str(uuid.uuid4()),
                idempotency_key=idempotency_key,
                prompt=prompt,
                job_id=job_id,
                priority=priority,
                status=RelayStatus.PENDING
            )
            session.add(task)
            session.commit()
            session.refresh(task)
            return task
        finally:
            session.close()

    def dequeue(self) -> Optional[RelayTask]:
        """
        다음 작업 가져오기 (우선순위 + FIFO)

        상태를 READY_FOR_RELAY로 전환
        """
        session = self.Session()
        try:
            task = session.query(RelayTask).filter_by(
                status=RelayStatus.PENDING
            ).order_by(
                RelayTask.priority.desc(),
                RelayTask.created_at.asc()
            ).first()

            if task:
                task.status = RelayStatus.READY_FOR_RELAY
                session.commit()
                session.refresh(task)

            return task
        finally:
            session.close()

    def mark_awaiting(self, task_id: str) -> None:
        """응답 대기 상태로 전환"""
        self._update_status(task_id, RelayStatus.AWAITING_RESPONSE)

    def complete(self, task_id: str, response: str) -> None:
        """작업 완료 처리"""
        session = self.Session()
        try:
            task = session.query(RelayTask).filter_by(id=task_id).first()
            if task:
                task.status = RelayStatus.COMPLETED
                task.response = response
                session.commit()
        finally:
            session.close()

    def fail(self, task_id: str) -> bool:
        """
        작업 실패 처리 (재시도 가능 여부 반환)

        max_retries 미만이면 PENDING으로 재설정
        """
        session = self.Session()
        try:
            task = session.query(RelayTask).filter_by(id=task_id).first()
            if task:
                task.retry_count += 1
                if task.retry_count < task.max_retries:
                    task.status = RelayStatus.PENDING
                    session.commit()
                    return True  # 재시도 예정
                else:
                    task.status = RelayStatus.FAILED
                    session.commit()
                    return False  # 최종 실패
            return False
        finally:
            session.close()

    def get_pending_count(self) -> int:
        """대기 중인 작업 수"""
        session = self.Session()
        try:
            return session.query(RelayTask).filter_by(
                status=RelayStatus.PENDING
            ).count()
        finally:
            session.close()

    def _update_status(self, task_id: str, status: RelayStatus) -> None:
        session = self.Session()
        try:
            task = session.query(RelayTask).filter_by(id=task_id).first()
            if task:
                task.status = status
                session.commit()
        finally:
            session.close()
```

#### 3.2.5 `executor.py` 릴레이 실행기

```python
# scripts/relay/executor.py
from typing import Optional
from .clipboard import ClipboardManager
from .notification import NotificationManager
from .queue import RelayQueue, RelayTask, RelayStatus

class RelayExecutor:
    """릴레이 워크플로우 오케스트레이터"""

    def __init__(self):
        self.clipboard = ClipboardManager()
        self.notification = NotificationManager()
        self.queue = RelayQueue()

    def execute_relay(
        self,
        prompt: str,
        job_id: Optional[str] = None,
        target_url: str = "https://claude.ai",
        timeout: int = 600
    ) -> Optional[str]:
        """
        완전한 릴레이 사이클 실행

        1. 큐에 작업 추가 (멱등성 보장)
        2. 프롬프트를 클립보드에 복사
        3. 데스크톱 알림 전송
        4. 클립보드 변경 대기
        5. 응답 반환 또는 타임아웃 처리
        """
        # 1. 큐에 추가
        task = self.queue.enqueue(prompt, job_id=job_id)

        # 이미 완료된 작업이면 캐시된 응답 반환
        if task.status == RelayStatus.COMPLETED and task.response:
            return task.response

        # 2. 클립보드에 복사
        effective_prompt = task.compressed_prompt or task.prompt
        self.clipboard.copy_prompt(effective_prompt)

        # 3. 알림 전송
        self.notification.notify_relay_ready(
            prompt_length=len(effective_prompt),
            target_url=target_url
        )

        # 4. 상태 전환 및 대기
        self.queue.mark_awaiting(task.id)
        response = self.clipboard.wait_for_response(timeout=timeout)

        # 5. 결과 처리
        if response:
            self.queue.complete(task.id, response)
            self.notification.notify_response_received(len(response))
            return response
        else:
            can_retry = self.queue.fail(task.id)
            if can_retry:
                return self.execute_relay(prompt, job_id, target_url, timeout)
            return None

    def process_queue(self, max_tasks: int = 10) -> int:
        """
        큐의 대기 작업 일괄 처리

        Returns: 처리된 작업 수
        """
        processed = 0
        for _ in range(max_tasks):
            task = self.queue.dequeue()
            if not task:
                break

            response = self.execute_relay(
                task.prompt,
                job_id=task.job_id,
                timeout=task.timeout_seconds
            )

            if response:
                processed += 1

        return processed
```

#### 3.2.6 의존성 추가

```toml
[project.optional-dependencies]
relay = [
    "pyperclip>=1.8.2",        # 클립보드 자동화
    "win10toast-click>=0.1.2", # Windows 알림 (선택)
]
```

---

### Phase 3: Palantir 스타일 아키텍처 (Week 5-6)

#### 3.3.1 신규 모듈: `scripts/proposal/`

```
scripts/proposal/
├── __init__.py
├── models.py          # Proposal 스키마
├── generator.py       # Proposal 생성기
├── reviewer.py        # Human-in-the-loop 검토
└── executor.py        # 승인된 Proposal 실행
```

#### 3.3.2 `models.py` 제안 스키마

```python
# scripts/proposal/models.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from enum import Enum

class ProposalStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    FAILED = "failed"

class ProposalAction(BaseModel):
    """제안된 단일 액션"""
    action_type: str
    target: str  # 파일 경로, 객체 ID 등
    parameters: Dict[str, Any]
    rationale: str  # AI가 이 액션을 제안한 이유
    risk_level: Literal["low", "medium", "high"]
    reversible: bool = True

class Proposal(BaseModel):
    """
    Palantir 스타일 제안 객체

    AI가 직접 변경을 수행하는 대신, 구조화된 제안을 생성하고
    인간 운영자가 검토/승인/거부 결정을 내림
    """
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # 컨텍스트
    job_id: str
    objective: str
    context_summary: str

    # 제안된 액션들
    actions: List[ProposalAction]

    # 상태
    status: ProposalStatus = ProposalStatus.DRAFT

    # 메타데이터
    confidence_score: float = Field(ge=0.0, le=1.0)
    estimated_impact: str
    dependencies: List[str] = []

    # 검토 정보
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None

    # 암호화 서명 (감사용)
    signature: Optional[str] = None

class ProposalBundle(BaseModel):
    """다중 Proposal 번들 (배치 검토용)"""
    proposals: List[Proposal]
    bundle_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

#### 3.3.3 `generator.py` 제안 생성

```python
# scripts/proposal/generator.py
from typing import List
from scripts.llm.router import HybridRouter, RouteTarget
from scripts.llm.ollama_client import OllamaClient
from scripts.relay.executor import RelayExecutor
from .models import Proposal, ProposalAction, ProposalStatus
import hashlib
import hmac

class ProposalGenerator:
    """
    AI 기반 Proposal 생성기

    Job을 분석하여 구조화된 Proposal로 변환
    """

    def __init__(self, secret_key: str = "orion-signing-key"):
        self.router = HybridRouter()
        self.ollama = OllamaClient()
        self.relay = RelayExecutor()
        self.secret_key = secret_key.encode()

    def generate(self, job) -> Proposal:
        """
        Job에서 Proposal 생성

        1. 작업 유형에 따라 라우팅 결정
        2. 로컬 또는 릴레이를 통해 제안 생성
        3. 암호화 서명 추가
        """
        route = self.router.route(
            task_type=job.action_name,
            prompt=self._build_prompt(job)
        )

        if route == RouteTarget.OLLAMA:
            proposal = self._generate_local(job)
        else:
            proposal = self._generate_via_relay(job)

        # 서명 추가 (감사 추적용)
        proposal.signature = self._sign_proposal(proposal)
        proposal.status = ProposalStatus.PENDING_REVIEW

        return proposal

    def _generate_local(self, job) -> Proposal:
        """Ollama를 통한 로컬 생성"""
        from scripts.llm.models import ProposalSchema

        prompt = self._build_prompt(job)
        result = self.ollama.generate_structured(
            prompt=prompt,
            response_model=ProposalSchema,
            model="qwen2.5:7b-instruct-q4_K_M"
        )

        return Proposal(
            job_id=job.id,
            objective=job.objective,
            context_summary=result.context_summary,
            actions=[
                ProposalAction(**action) for action in result.actions
            ],
            confidence_score=result.confidence,
            estimated_impact=result.impact
        )

    def _generate_via_relay(self, job) -> Proposal:
        """Human Relay를 통한 생성"""
        prompt = self._build_relay_prompt(job)
        response = self.relay.execute_relay(
            prompt=prompt,
            job_id=job.id
        )

        # 응답 파싱 및 Proposal 구성
        return self._parse_relay_response(response, job)

    def _sign_proposal(self, proposal: Proposal) -> str:
        """HMAC-SHA256 서명 생성"""
        content = f"{proposal.id}:{proposal.job_id}:{len(proposal.actions)}"
        return hmac.new(
            self.secret_key,
            content.encode(),
            hashlib.sha256
        ).hexdigest()

    def verify_signature(self, proposal: Proposal) -> bool:
        """서명 검증"""
        expected = self._sign_proposal(proposal)
        return hmac.compare_digest(proposal.signature or "", expected)

    def _build_prompt(self, job) -> str:
        """Proposal 생성용 프롬프트 구성"""
        return f"""
You are a proposal generator for the Orion ODA system.

Job Objective: {job.objective}
Action: {job.action_name}
Parameters: {job.action_args}
Context Files: {job.input_context}

Generate a structured proposal with:
1. List of specific actions to take
2. Risk assessment for each action
3. Rationale for the approach
4. Confidence score (0-1)

Output as JSON matching the ProposalSchema.
"""
```

#### 3.3.4 기존 `governance.py` 통합

```python
# scripts/governance.py 수정 사항

from scripts.proposal.models import Proposal, ProposalStatus

class ActionDispatcher:
    """기존 ActionDispatcher에 Proposal 통합"""

    def dispatch_from_proposal(self, proposal: Proposal) -> None:
        """
        승인된 Proposal의 액션들을 순차 실행

        각 액션은 기존 Governance 규칙을 따름
        """
        if proposal.status != ProposalStatus.APPROVED:
            raise ValueError(f"Proposal {proposal.id} is not approved")

        for action in proposal.actions:
            self.dispatch(
                action_type=action.action_type,
                target=action.target,
                parameters=action.parameters,
                proposal_id=proposal.id  # 감사 연결
            )

        proposal.status = ProposalStatus.EXECUTED
```

---

### Phase 4: 최적화 (Week 7-8)

#### 3.4.1 `compression.py` 컨텍스트 압축

```python
# scripts/relay/compression.py
from typing import Optional

class ContextCompressor:
    """
    LLMLingua-2 기반 컨텍스트 압축

    긴 프롬프트를 3-6x 압축하여 릴레이 부담 감소
    """

    def __init__(self):
        self._compressor = None

    @property
    def compressor(self):
        """지연 로딩 (초기화 비용 절감)"""
        if self._compressor is None:
            try:
                from llmlingua import PromptCompressor
                self._compressor = PromptCompressor(
                    model_name="microsoft/llmlingua-2-bert-base-multilingual-cased-meetingbank",
                    use_llmlingua2=True
                )
            except ImportError:
                return None
        return self._compressor

    def compress(
        self,
        prompt: str,
        target_ratio: float = 0.3,  # 30% 유지 (3.3x 압축)
        force_context_ids: Optional[list] = None
    ) -> str:
        """
        프롬프트 압축

        Args:
            prompt: 원본 프롬프트
            target_ratio: 유지할 토큰 비율 (0.2-0.5 권장)
            force_context_ids: 반드시 유지할 문장 인덱스

        Returns:
            압축된 프롬프트
        """
        if not self.compressor:
            return prompt  # 압축기 없으면 원본 반환

        if len(prompt) < 2000:
            return prompt  # 짧은 프롬프트는 압축 불필요

        result = self.compressor.compress_prompt(
            prompt,
            rate=target_ratio,
            force_context_ids=force_context_ids,
            force_reserve_digit=True  # 숫자 보존
        )

        return result["compressed_prompt"]

    def get_compression_stats(self, original: str, compressed: str) -> dict:
        """압축 통계"""
        original_len = len(original)
        compressed_len = len(compressed)

        return {
            "original_length": original_len,
            "compressed_length": compressed_len,
            "compression_ratio": original_len / compressed_len if compressed_len > 0 else 0,
            "saved_chars": original_len - compressed_len
        }
```

#### 3.4.2 응답 캐싱

```python
# scripts/relay/cache.py
from typing import Optional
from datetime import datetime, timedelta
import hashlib
import json
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class CachedResponse(Base):
    """릴레이 응답 캐시"""
    __tablename__ = "response_cache"

    prompt_hash = Column(String, primary_key=True)
    response = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    hit_count = Column(Integer, default=0)

class ResponseCache:
    """
    프롬프트-응답 캐시

    동일한 프롬프트에 대한 중복 릴레이 방지
    """

    def __init__(
        self,
        db_path: str = ".agent/response_cache.db",
        default_ttl: timedelta = timedelta(hours=24)
    ):
        self.engine = create_engine(f"sqlite:///{db_path}")
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
        self.default_ttl = default_ttl

    def _hash_prompt(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode()).hexdigest()

    def get(self, prompt: str) -> Optional[str]:
        """캐시된 응답 조회"""
        session = self.Session()
        try:
            prompt_hash = self._hash_prompt(prompt)
            cached = session.query(CachedResponse).filter_by(
                prompt_hash=prompt_hash
            ).first()

            if cached:
                if cached.expires_at and cached.expires_at < datetime.utcnow():
                    session.delete(cached)
                    session.commit()
                    return None

                cached.hit_count += 1
                session.commit()
                return cached.response

            return None
        finally:
            session.close()

    def set(
        self,
        prompt: str,
        response: str,
        ttl: Optional[timedelta] = None
    ) -> None:
        """응답 캐시"""
        session = self.Session()
        try:
            prompt_hash = self._hash_prompt(prompt)
            expires_at = datetime.utcnow() + (ttl or self.default_ttl)

            cached = CachedResponse(
                prompt_hash=prompt_hash,
                response=response,
                expires_at=expires_at
            )
            session.merge(cached)
            session.commit()
        finally:
            session.close()
```

---

## 4. 파일 수정 목록

### 4.1 신규 생성 파일

| 파일 경로 | 목적 | Phase |
|-----------|------|-------|
| `scripts/llm/__init__.py` | LLM 모듈 패키지 | 1 |
| `scripts/llm/ollama_client.py` | Ollama HTTP 클라이언트 | 1 |
| `scripts/llm/router.py` | 하이브리드 라우팅 | 1 |
| `scripts/llm/models.py` | Pydantic 출력 스키마 | 1 |
| `scripts/relay/__init__.py` | 릴레이 모듈 패키지 | 2 |
| `scripts/relay/clipboard.py` | 클립보드 자동화 | 2 |
| `scripts/relay/notification.py` | 데스크톱 알림 | 2 |
| `scripts/relay/queue.py` | SQLite 작업 큐 | 2 |
| `scripts/relay/executor.py` | 릴레이 실행기 | 2 |
| `scripts/relay/compression.py` | 컨텍스트 압축 | 4 |
| `scripts/relay/cache.py` | 응답 캐싱 | 4 |
| `scripts/proposal/__init__.py` | Proposal 모듈 | 3 |
| `scripts/proposal/models.py` | Proposal 스키마 | 3 |
| `scripts/proposal/generator.py` | Proposal 생성기 | 3 |
| `scripts/proposal/reviewer.py` | Human-in-the-loop 검토 | 3 |

### 4.2 수정 대상 파일

| 파일 경로 | 변경 내용 | Phase |
|-----------|----------|-------|
| `pyproject.toml` | 의존성 추가 | 1-4 |
| `scripts/governance.py` | Proposal 통합 | 3 |
| `scripts/loop.py` | 하이브리드 라우팅 통합 | 1 |
| `scripts/engine.py` | CLI 명령어 추가 | 2 |
| `scripts/ontology/handoff.py` | 릴레이 큐 통합 | 2 |
| `scripts/memory/manager.py` | 벡터 검색 완성 | 4 |

---

## 5. 의존성 최종 목록

```toml
# pyproject.toml (최종)
[project]
name = "orion-orchestrator"
version = "3.0.0"
description = "Antigravity ODA Runtime with Hybrid LLM Orchestration"
requires-python = ">=3.10"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "uuid6",
    "httpx>=0.27.0",
]

[project.optional-dependencies]
llm = [
    "ollama>=0.4.0",
    "sentence-transformers>=2.2",
]
relay = [
    "pyperclip>=1.8.2",
    "win10toast-click>=0.1.2; platform_system=='Windows'",
    "rq>=1.15",
]
compression = [
    "llmlingua>=0.2",
]
memory = [
    "sqlite-vec>=0.1",
    "fastembed>=0.2",
]
all = [
    "orion-orchestrator[llm,relay,compression,memory]",
]
```

---

## 6. 리스크 분석 및 완화 전략

| 리스크 | 영향도 | 확률 | 완화 전략 |
|--------|--------|------|-----------|
| Ollama 모델 정확도 미달 | 높음 | 중간 | A/B 테스트, 프롬프트 튜닝, fallback to relay |
| 클립보드 감지 불안정 | 중간 | 낮음 | 수동 "응답 준비" 버튼 fallback |
| LLMLingua 압축 품질 저하 | 중간 | 낮음 | 압축 vs 원본 테스트셋 검증 |
| Windows Toast 호환성 | 낮음 | 중간 | Linux용 대체 알림 (notify-send) |
| 큐 복잡도로 인한 버그 | 중간 | 중간 | 단순 FIFO로 시작, 점진적 기능 추가 |

---

## 7. 성공 지표 (KPIs)

| 지표 | 현재 | 목표 | 측정 방법 |
|------|------|------|-----------|
| 로컬 처리 비율 | 0% | 60-70% | `RouteTarget.OLLAMA` 카운트 |
| 릴레이 대기 시간 | N/A | < 30초 (알림→복사) | 타임스탬프 차이 |
| 중복 릴레이 비율 | 알 수 없음 | < 5% | 캐시 히트율 |
| Proposal 승인률 | N/A | > 90% | 승인/거부 비율 |
| 컨텍스트 압축률 | 1x | 3-4x | 압축 전후 길이 비교 |

---

## 8. 결론

본 계획은 Orion ODA를 **완전 수동 릴레이 시스템**에서 **하이브리드 자동화 시스템**으로 전환합니다:

1. **로컬 LLM (Ollama)** 통합으로 60-70% 작업 자동화
2. **클립보드 자동화 + 알림**으로 릴레이 UX 대폭 개선
3. **Palantir 스타일 Proposal 워크플로우**로 인간 검토 구조화
4. **컨텍스트 압축 + 캐싱**으로 효율성 극대화

Web Automation은 법적/기술적 리스크로 인해 **의도적으로 제외**했습니다. 이 아키텍처는 API-less 제약을 **장점**으로 전환하여, 중요 결정에 대한 명시적 인간 검증이 내재된 시스템을 구축합니다.
