
# 💻 Phase 6 Execution Plan: Feature Expansion (The Interface)

> **Context**: Executing `docs/ROADMAP_PHASE_4_5_6.md` (Phase 6)
> **Mandate**: `dynamic-impact-analysis.txt` (Deep Context Awareness)

---

## 🛑 Dynamic Impact Analysis (Pre-Flight)

Before expanding the feature set, we evaluate the system-wide integration risks:

1.  **Dependency Chain (Frontend Mounting)**:
    - `scripts/api/main.py` (FastAPI) -> `frontend/dist/` (React Build Artifacts).
    - **Impact**: The API is currently a Python-only construct. Mounting a static directory that *doesn't exist yet* will cause startup `RuntimeError`.
    - **Risk**: The "Deployment Complexity" risk identified in Deep Research. We must ensure the `frontend/` directory structure exists even if empty, or handle the mount conditionally during development.
    - **Mitigation**: Use `StaticFiles(..., check_dir=False)` or create a placeholder logic in `main.py` until the build process is active.

2.  **Dependency Chain (Dashboard UI)**:
    - React App -> `scripts/api/dtos.py` (JSON Contract).
    - **Impact**: The React Types definition (`types/proposal.ts`) MUST match `ProposalResponse` exactly.
    - **Risk**: Drift between Pydantic models (Backend) and TypeScript interfaces (Frontend).
    - **Strategy**: We will generate the TypeScript interfaces directly from the OpenAPI schema (`/openapi.json`) in a real pipeline. For this phase, we map them manually but explicitly document the mapping.

3.  **Dependency Chain (Docker)**:
    - `Dockerfile` -> `pyproject.toml` + `package.json`.
    - **Impact**: A monolithic build requires a Multi-Stage Dockerfile.
    - **Risk**: Large image sizes. We must use `python:3.11-slim` and discard the Node.js builder layer in the final image.

---

## 📋 Execution Steps

### Step 1: Frontend Skeleton
**Action**: Initialize `frontend/` directory.
- Create minimal HTML/JS structure to simulate the React Build.
- **Why**: To verify the `FastAPI` mounting logic without needing a full Node.js toolchain installed in this restricted environment.

### Step 2: Monolithic Integration
**Action**: Update `scripts/api/main.py`.
- Implement conditional mounting: Check if `frontend/dist` exists.
- Implement "Catch-All" route (`/{full_path:path}`) to serve `index.html` for client-side routing.

### Step 3: Dockerization Logic
**Action**: Create `Dockerfile`.
- **Stage 1 (Builder)**: `node:18` (Mocked for now, described in file) -> `npm run build`.
- **Stage 2 (Runtime)**: `python:3.11-slim`.
- **Copy**: `COPY --from=builder /app/dist /app/frontend/dist`.
- **Entrypoint**: `uvicorn scripts.api.main:app --host 0.0.0.0`.

### Step 4: Final Validation (E2E)
**Action**: Create `tests/e2e/test_monolith.py`.
- **Scenario**: Request `/` -> Returns 200 (HTML).
- **Scenario**: Request `/dashboard/settings` -> Returns 200 (HTML - via Catch-All).
- **Scenario**: Request `/api/v1/proposals` -> Returns 200 (JSON).
- **Goal**: Verify that API and Static Content coexist without conflict.

---

## 🏃 Immediate Next Actions

1.  **Scaffold**: Create `frontend/dist` and `frontend/dist/static`.
2.  **Mock**: Create a dummy `index.html` to simulate a React App.
