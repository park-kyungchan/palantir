
# 🚀 Phase 4 Execution Plan: Foundation (Async Data & Logic)

> **Context**: Executing `docs/ROADMAP_PHASE_4_5_6.md`
> **Mandate**: `dynamic-impact-analysis.txt` (Deep Context Awareness)

---

## 🛑 Dynamic Impact Analysis (Pre-Flight)

Before touching a single line of code, we analyze the semantic coupling:

1.  **Dependency Chain (Persistence)**:
    - `scripts/ontology/ontology_types.py` (Current Base) -> `scripts/ontology/objects/item.py` (Domain) -> `scripts/ontology/storage/proposal_repository.py` (Raw SQL)
    - **Impact**: introducing SQLAlchemy `DeclarativeBase` will replace `ontology_types.py`'s manual `BaseModel`. This is a **System-Wide Refactor**.
    - **Risk**: `ProposalRepository` currently writes raw SQL (`INSERT INTO...`). This code will be completely deleted and replaced with `session.add()`. The logic for `optimistic_locking` (version check) moves from SQL `WHERE` clauses to the ORM logic or explicit `update()` calls.

2.  **Dependency Chain (LLM)**:
    - `scripts/llm/ollama_client.py` (Current) -> `scripts/runtime/kernel.py` (String manipulation logic).
    - **Impact**: The Kernel's manual JSON string cleanup (lines 114-118) is a "Semantic Drift" artifact. It must be removed.
    - **Risk**: `instructor` might raise `ValidationError` differently than our current logic expects. We must wrap this in the `SafeInstructorClient` to prevent crashing the Kernel loop.

---

## 📋 Execution Steps

### Step 1: Dependencies & Environment
**Action**: Update `pyproject.toml` and install core libraries.
- Add: `sqlalchemy[asyncio]`, `aiosqlite`, `instructor`, `tenacity`.
- **Verify**: `poetry lock` or `pip install` validity.

### Step 2: ORM Foundation (The Schema Shift)
**Action**: Create `scripts/ontology/storage/orm.py`.
- Define `AsyncOntologyObject` (Declarative Base).
- Implement `version_id_col` (Optimistic Locking).
- **Crucial**: Ensure it maps 1:1 with existing Pydantic models so `Proposal` can inherit from it (or map to it). *Decision: We will likely use SQLAlchemy Config to map existing Pydantic models or creating "Table" definitions if using 2.0 style strictly.*

### Step 3: Repository Migration (The Logic Shift)
**Action**: Refactor `scripts/ontology/storage/proposal_repository.py`.
- Replace `Database.execute(raw_sql)` with `AsyncSession.execute(select())`.
- Refactor `save()`: Use `session.merge()` or `add()`.
- Refactor `approve()`: Use `update().where(version == v)`.
- **Validation**: Ensure `StaleDataError` is caught and translated or bubbled up correctly.

### Step 4: Instructor Integration (The Determinisim Shift)
**Action**: Create `scripts/llm/instructor_client.py`.
- Implement `SafeInstructorClient` with `tenacity` retries.
- **Hook**: Implement `json_repair` fallback logic.
**Action**: Update `scripts/runtime/kernel.py`.
- Remove manual parsing logic.
- Inject `InstructorClient` instead of `OllamaClient`.

### Step 5: Verification (The Safety Net)
**Action**: Run `pytest tests/e2e/test_full_integration.py`.
- **Expectation**: Tests *should* pass if interfaces are preserved.
- **Correction**: If tests fail (likely due to MockLLM differences), update the Mocking strategy to emulate Instructor's `response_model` behavior.

---

## 🏃 Immediate Next Actions

1.  **Install Libraries**: `sqlalchemy`, `aiosqlite`, `instructor`, `tenacity`.
2.  **Verify**: Check environment health.
