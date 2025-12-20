
# 🕵️ Phase 4 Implementation Report: Async Data & Logic

> **Status**: Code Implementation Complete
> **Verification**: Pending Environment Setup (Missing `pip`/`pytest`)

## 🛠️ Implemented Components

### 1. Async ORM Foundation (`scripts/ontology/storage/`)
- **`orm.py`**: Introduced `AsyncOntologyObject` with:
    - `version_id_col` for **Optimistic Locking**.
    - `AsyncAttrs` for safe relationship loading.
- **`models.py`**: Defined `ProposalModel` mapping 1:1 to Domain Schema.
- **`database.py`**: Upgraded to `SQLAlchemy` Async Engine with **WAL Mode enforcement**.
- **`proposal_repository.py`**: Fully refactored to use `AsyncSession.execute(select(...))` instead of raw strings.

### 2. Deterministic AI Engine (`scripts/llm/`)
- **`instructor_client.py`**: Implemented `InstructorClient`.
    - **Self-Healing**: Wraps calls in `tenacity` retry loops for `ValidationError`.
    - **Structure**: Forces LLM output to conform to `Plan` Pydantic model.

### 3. Kernel Refactoring (`scripts/runtime/kernel.py`)
- **Cognitive Loop**: Removed manual JSON parsing. Now uses `await asyncio.to_thread(self.llm.generate_plan, prompt)`.
- **Persistence**: Switched to `await repo.save()` which now runs DB operations asynchronously.

---

## ⚠️ Action Items for Environment

The following commands typically require `pip` which was unavailable in the current shell. Please run these in your target environment:

```bash
# 1. Install Dependencies
python3 -m pip install pydantic "sqlalchemy[asyncio]" aiosqlite instructor tenacity json_repair uuid6 pytest pytest-asyncio

# 2. Run Verification
python3 -m pytest tests/e2e/test_full_integration.py
```

## 🔄 Dynamic Impact Analysis (Post-Implementation)
- **Risk Mitigation**: The shift to `AsyncSession` explicitly separates "Read" and "Write" phases, reducing the chance of SQLite locks.
- **Observability**: `InstructorClient` logs validation errors, allowing us to see *why* a model failed (e.g. "Missing 'jobs' key") rather than just crashing.
