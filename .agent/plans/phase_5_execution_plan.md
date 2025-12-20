
# 🔐 Phase 5 Execution Plan: API & Security (The Fortress)

> **Context**: Executing `docs/ROADMAP_PHASE_4_5_6.md` (Phase 5)
> **Mandate**: `dynamic-impact-analysis.txt` (Deep Context Awareness)

---

## 🛑 Dynamic Impact Analysis (Pre-Flight)

Before implementation, we analyze the causal chains:

1.  **Dependency Chain (DTOs)**:
    - `scripts/ontology/objects/proposal.py` (Domain Entity) <-> `scripts/api/dtos.py` (Interface).
    - **Impact**: We are introducing a **Strict Separation Layer**. The API will NEVER return `Proposal` or `ProposalModel` directly.
    - **Risk**: "Over-fetching". If we use `ProposalModel` (SQLAlchemy) to populate `ProposalResponse` (Pydantic), we must ensure we don't trigger N+1 queries.
    - **Mitigation**: We already implemented `selectinload` strategy in the Persistence layer (Phase 4), so accessing relationships for DTO mapping will be safe.

2.  **Dependency Chain (Error Handling)**:
    - `scripts/runtime/kernel.py` (Exception Source) -> `scripts/api/main.py` (Exception Handler).
    - **Impact**: `ConcurrencyError` (implemented in Phase 4) must be mapped to HTTP 409. `ValidationError` to HTTP 422.
    - **Risk**: If we miss a mapping, the API will return generic 500 errors, masking the root cause (e.g. "Stale Data").

---

## 📋 Execution Steps

### Step 1: Environment & Structure
**Action**: Update `pyproject.toml` (already done, but verify `fastapi` and `uvicorn`).
**Action**: Create directory structure:
```text
scripts/api/
├── __init__.py
├── main.py          # App Entrypoint (Middleware)
├── routes.py        # Endpoints
├── dtos.py          # Request/Response Models
└── dependencies.py  # DI (Database Session)
```

### Step 2: Data Transfer Objects (DTOs)
**Action**: Implement `scripts/api/dtos.py`.
- **Constraint**: `ResponseModel` must NOT contain `version` (internal locking detail) unless specifically needed for "Edit" forms.
- **Constraint**: `RequestModel` for `create_proposal` must enforce `action_type` validity.

### Step 3: API Foundation & Middleware
**Action**: Implement `scripts/api/main.py`.
- **Security**: Add `CORSMiddleware`, `TrustedHostMiddleware`.
- **Headers**: Implement Custom Middleware for `Strict-Transport-Security`, `X-Content-Type-Options`, `Content-Security-Policy`.
- **Exception Handlers**: Map `ConcurrencyError` -> 409, `ValueError` -> 400.

### Step 4: Routes & Dependency Injection
**Action**: Implement `scripts/api/routes.py`.
- **Dependency**: Create `get_db` generator yielding `AsyncSession`.
- **Endpoint**: `POST /proposals` (Submit).
- **Endpoint**: `GET /proposals` (List Pending).
- **Endpoint**: `POST /proposals/{id}/approve` (Review).
- **Logic**: Routes will call `ProposalRepository` methods directly (Repository Pattern).

### Step 5: Verification
**Action**: Create `tests/e2e/test_api_security.py`.
- **Scenario**: Verify HSTS headers are present.
- **Scenario**: Verify 409 Conflict on concurrent edits (simulated).
- **Scenario**: Verify DTOs strip internal fields.

---

## 🏃 Immediate Next Actions

1.  **Install**: `fastapi`, `uvicorn`, `httpx` (for testing).
2.  **Scaffold**: Create the `scripts/api` folder structure.
