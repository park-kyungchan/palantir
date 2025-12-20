
# 🕵️‍♀️ ODA Phase 4-6: Deep Research Command Protocol
# Target: Gemini Web / Advanced (Model 3.0)

**ROLE**: You are the **Lead Systems Architect** for the **Orion Orchestrator V3** project.
**CONTEXT**: 
We have successfully refactored the ODA Kernel (Phase 1-3).
- **Current Architecture**: Generic Kernel + Action Registry + Metadata Governance + SQLite (Manual Repo).
- **Verification**: E2E Tests passed for full governance workflow.
- **Goal**: Evolve this verification prototype into a **Production-Grade Enterprise System**.

**MISSION**:
Conduct a "Deep Research Session" on the following 3 parallel tracks and generate a concrete Technical Specification (`docs/ROADMAP_PHASE_4_5_6.md`).

---

## 🔬 RESEARCH TRACKS (Be Specific & Technical)

### 1. Technology Depth (The "Integration" Track)
- **Problem**: We currently use a "Mock LLM" in tests. We need real structured output.
- **Research Target**: Python `instructor` library (latest version).
    - *Query*: "instructor python pydantic wrapper pattern for ollama and openai compatible"
    - *Output needed*: A code snippet showing how to patch `OllamaClient` to return our exact `Plan` Pydantic model strictly.
- **Problem**: Raw SQL is good for control, but hard to maintain.
- **Research Target**: `SQLAlchemy 2.0` (Async/Await).
    - *Query*: "sqlalchemy 2.0 async optimistic locking version column pattern"
    - *Output needed*: A base class design that replicates our `OntologyObject` (UUID, version, audit fields) using SQLAlchemy Declarative 2.0.

### 2. Production Engineering (The "DevOps" Track)
- **Problem**: We execute tests manually.
- **Research Target**: GitHub Actions for Agentic Systems.
    - *Query*: "github actions workflow python poetry pytest docker cache"
    - *Output needed*: A YAML structure that runs `pytest` and `mypy` on every PR.
- **Problem**: Deployment Consistency.
- **Research Target**: Docker Multi-stage Builds.
    - *Query*: "python 3.12 docker multi-stage build best practices minimal image"

### 3. Feature Expansion (The "Scalability" Track)
- **Problem**: Approving proposals via CLI/DB is painful. We need a UI.
- **Research Target**: FastAPI + React integration.
    - *Query*: "fastapi mount react static files production pattern"
    - *Output needed*: Architecture for a "Monolithic Agent" where FastAPI serves both the Action API and the React Dashboard.

---

## 📝 REQUIRED OUTPUT FORMAT

After performing the research, output a single file: `docs/ROADMAP_PHASE_4_5_6.md` containing:

1.  **Tech Stack Final Decision**: A table listing the chosen libraries (e.g., `instructor`, `sqlalchemy[asyncio]`, `fastapi`, `pydantic-settings`).
2.  **Implementation Snippets**:
    - The `instructor` patch code.
    - The `SQLAlchemy` Base Model code.
    - The `Dockerfile` skeleton.
3.  **Phase Execution Plan (2-Week Sprint)**:
    - Phase 4: Integration (LLM + ORM)
    - Phase 5: DevOps (CI/CD + Docker)
    - Phase 6: Interface (Dashboard)

---

**EXECUTE RESEARCH PROTOCOL NOW.**
