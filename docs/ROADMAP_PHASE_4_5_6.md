
# 🗺️ ROADMAP: Phase 4-6 (Enterprise Hardening)

> **Status**: APPROVED
> **Target Architecture**: Orion ODA V3 (Enterprise)
> **Based On**: Deep Research Findings (Dec 2025)

---

## 🏗️ 1. Technical Stack Decisions

| Component | Selected Technology | Rationale (from Dynamic Impact Analysis) |
|-----------|--------------------|------------------------------------------|
| **LLM Integration** | `instructor` + `tenacity` | Enforces Pydantic schema on LLM outputs. `tenacity` provides retry loops for validation failures (Self-Healing). |
| **Parsing Safety** | `json_repair` | **Critical**: Fixes "Double-Escape" issues in local quantized models (Ollama/Llama3) before strict parsing. |
| **ORM (Persistence)** | `SQLAlchemy 2.0` (Async) | explicit `await` for I/O safety. Optimistic locking via `version_id_col` prevents "Lost Updates" in highly concurrent webs. |
| **Database** | `SQLite` (WAL Mode) | Write-Ahead Logging enables non-blocking readers/writers. High concurrency performance for this scale. |
| **Backend API** | `FastAPI` | Type-safe, high-performance async API. Native Pydantic integration for DTOs. |
| **Frontend Serving** | Monolithic (FastAPI Mount) | Simplifies deployment (No Nginx requirements). Eliminates CORS issues by serving logic and UI from same origin. |
| **Security** | Middleware (HSTS, CSP) | Application-level defense mechanism independently of infra configuration. |

---

## 💻 2. Implementation Snippets

### A. The "Self-Healing" LLM Client (`instructor` + `json_repair`)
*Addresses the "Non-Determinism" and "Double-Escape" risks.*

```python
import instructor
from openai import OpenAI
from pydantic import ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential

class SafeInstructorClient:
    def __init__(self, base_url: str):
        self.client = instructor.patch(
            OpenAI(base_url=base_url, api_key="ollama"),
            mode=instructor.Mode.JSON
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_plan(self, prompt: str) -> Plan:
        try:
            return self.client.chat.completions.create(
                model="llama3.2",
                messages=[{"role": "user", "content": prompt}],
                response_model=Plan,
                max_retries=2  # Instructor's internal retry
            )
        except ValidationError as e:
            # Hook for json_repair if needed before re-raising
            # Log specific validation error for the "Re-asking" context
            print(f"Validation Failed: {e}")
            raise
```

### B. The Async ORM Base with Optimistic Locking
*Addresses "Data Integrity" and "Hidden Coupling" risks.*

```python
from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
from datetime import datetime, timezone

class Base(AsyncAttrs, DeclarativeBase):
    pass

class AsyncOntologyObject(Base):
    __abstract__ = True
    
    id: Mapped[str] = mapped_column(String, primary_key=True)
    
    # Optimistic Locking Enforcement
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    __mapper_args__ = {
        "version_id_col": version,
        "version_id_generator": False  # We manage increments or let SQLA handle it
    }

    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
```

### C. The Monolithic SPA Router
*Addresses "Deployment Complexity" and "Route Handling".*

```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# 1. API Routes First
@app.get("/api/v1/health")
def health():
    return {"status": "ok"}

# 2. Mount Static Assets (JS/CSS)
app.mount("/static", StaticFiles(directory="frontend/dist/static"), name="static")

# 3. Catch-All for React Router (Must be last)
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    return FileResponse("frontend/dist/index.html")
```

---

## 📅 3. Execution Plan (8-Week Sprint)

### **Phase 4: Foundation (Weeks 1-2) - "Async Data & Logic"**
- [ ] **Data Layer**: Init SQLAlchemy 2.0 Async Engine with WAL Mode.
- [ ] **Migration**: Port `ProposalRepository` from manual SQL to Async ORM.
- [ ] **Locking**: Implement `version_id` optimistic locking and verify with concurrent tests.
- [ ] **LLM Layer**: Replace `MockLLM` with `instructor` client connected to local Ollama.

### **Phase 5: API & Security (Weeks 3-4) - "The Fortress"**
- [ ] **API Shell**: Initialize FastAPI app structure.
- [ ] **DTOs**: Implement strict `RequestModel` (Input) vs `ResponseModel` (Output) separation.
- [ ] **Security**: Add Middleware for HSTS, CSP, and X-Frame-Options.
- [ ] **Error Handling**: Global exception handlers for `StaleDataError` (409) and `ValidationError` (422).

### **Phase 6: Feature Expansion (Weeks 5-8) - "The Interface"**
- [ ] **Frontend Integration**: Mount React build artifacts into FastAPI.
- [ ] **Dashboard**: Build "Proposal Review" UI in React.
- [ ] **DevOps**: Docker Multi-stage build (Python Builder + Node Builder -> Slim Runtime).
- [ ] **Final E2E**: Run full suite against the dockerized monolithic container.
