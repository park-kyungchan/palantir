# ProposalRepository SQLite Implementation - Master Guide

> **Date**: 2025-12-20
> **Target Agent**: Antigravity IDE (Gemini 3.0 Pro)
> **Prerequisites**: ODA V3.0 Action Layer completed
> **Estimated Time**: 2 hours

---

## 📦 Delivery Contents

| File | Purpose | Apply Order |
|:-----|:--------|:-----------:|
| `01_proposal_repository.md` | Database + Repository implementation | 1 |
| `02_repository_tests.md` | 28 test cases | 2 |
| `03_mcp_server_update.md` | MCP server with persistence | 3 |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         MCP Server (oda-ontology)                    │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  create_proposal │ approve_proposal │ execute_proposal       │    │
│  └─────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        ProposalRepository                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │
│  │    save()   │  │   query()   │  │  approve()  │  │ history() │  │
│  │   insert    │  │   filter    │  │   reject()  │  │  audit    │  │
│  │   update    │  │   paginate  │  │  execute()  │  │  trail    │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           Database                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐  │
│  │    proposals    │  │ proposal_history │  │   edit_operations   │  │
│  │   (main table)  │  │  (audit trail)   │  │   (change log)      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────┘  │
│                                                                      │
│  SQLite with WAL Mode │ Optimistic Locking │ Auto Migrations        │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                    📁 /home/palantir/orion-orchestrator-v2/data/ontology.db
```

---

## ⚡ Quick Start

### Step 1: Create Directory Structure

```bash
mkdir -p scripts/ontology/storage
mkdir -p data
touch scripts/ontology/storage/__init__.py
```

### Step 2: Install Dependency

```bash
pip install aiosqlite --break-system-packages
```

### Step 3: Apply Database Implementation

```bash
# Copy code from 01_proposal_repository.md to:
# scripts/ontology/storage/database.py
# scripts/ontology/storage/proposal_repository.py

# Update __init__.py
cat > scripts/ontology/storage/__init__.py << 'EOF'
"""ODA V3.0 Storage Layer."""
from scripts.ontology.storage.database import (
    Database,
    get_database,
    initialize_database,
)
from scripts.ontology.storage.proposal_repository import (
    ProposalRepository,
    ProposalQuery,
    PaginatedResult,
    ProposalNotFoundError,
    OptimisticLockError,
)

__all__ = [
    "Database",
    "get_database",
    "initialize_database",
    "ProposalRepository",
    "ProposalQuery",
    "PaginatedResult",
    "ProposalNotFoundError",
    "OptimisticLockError",
]
EOF
```

### Step 4: Verify Implementation

```bash
python -c "
import asyncio
from scripts.ontology.storage import initialize_database, ProposalRepository
from scripts.ontology.objects.proposal import Proposal

async def verify():
    # Initialize
    db = await initialize_database()
    repo = ProposalRepository(db)
    
    # Create and save
    p = Proposal(action_type='test_action', created_by='verify-script')
    p.submit()
    await repo.save(p)
    
    # Query
    found = await repo.find_by_id(p.id)
    assert found is not None
    assert found.action_type == 'test_action'
    
    # Stats
    stats = await repo.count_by_status()
    print(f'✅ Database initialized. Stats: {stats}')
    
    # Cleanup
    await repo.delete(p.id, 'verify-script', hard_delete=True)
    print('✅ Verification complete!')

asyncio.run(verify())
"
```

### Step 5: Apply Tests

```bash
# Copy test code from 02_repository_tests.md to:
# tests/e2e/test_proposal_repository.py

# Run tests
pytest tests/e2e/test_proposal_repository.py -v --asyncio-mode=auto
```

### Step 6: Update MCP Server

```bash
# Replace scripts/mcp/ontology_server.py with code from 03_mcp_server_update.md

# Verify MCP server
python -c "
import asyncio
from scripts.mcp.ontology_server import get_repo

async def test():
    repo = await get_repo()
    print('✅ MCP Server ready with persistent storage')

asyncio.run(test())
"
```

---

## 📊 Database Schema

### `proposals` Table

| Column | Type | Description |
|:-------|:-----|:------------|
| `id` | TEXT PK | UUID primary key |
| `action_type` | TEXT | ActionType API name |
| `payload` | TEXT (JSON) | Action parameters |
| `status` | TEXT | draft/pending/approved/rejected/executed |
| `priority` | TEXT | low/medium/high/critical |
| `created_by` | TEXT | Creator ID |
| `created_at` | TEXT | ISO timestamp |
| `updated_at` | TEXT | ISO timestamp |
| `version` | INTEGER | Optimistic lock version |
| `reviewed_by` | TEXT | Reviewer ID |
| `reviewed_at` | TEXT | Review timestamp |
| `review_comment` | TEXT | Review comment |
| `executed_at` | TEXT | Execution timestamp |
| `execution_result` | TEXT (JSON) | Execution result |

### `proposal_history` Table

| Column | Type | Description |
|:-------|:-----|:------------|
| `id` | INTEGER PK | Auto-increment |
| `proposal_id` | TEXT FK | Reference to proposals |
| `action` | TEXT | created/submitted/approved/rejected/executed |
| `actor_id` | TEXT | Actor who performed action |
| `timestamp` | TEXT | ISO timestamp |
| `previous_status` | TEXT | Status before transition |
| `new_status` | TEXT | Status after transition |
| `comment` | TEXT | Action comment |
| `metadata` | TEXT (JSON) | Additional metadata |

### `edit_operations` Table

| Column | Type | Description |
|:-------|:-----|:------------|
| `id` | INTEGER PK | Auto-increment |
| `proposal_id` | TEXT FK | Reference to proposals |
| `edit_type` | TEXT | create/modify/delete/link/unlink |
| `object_type` | TEXT | Target object type |
| `object_id` | TEXT | Target object ID |
| `changes` | TEXT (JSON) | Change details |
| `timestamp` | TEXT | ISO timestamp |
| `actor_id` | TEXT | Actor ID |

---

## 🧪 Test Coverage

| Category | Tests | Description |
|:---------|------:|:------------|
| CRUD | 6 | Save, find, update, delete |
| Optimistic Locking | 2 | Version check, concurrent modify |
| Queries | 7 | Status, type, creator, pagination |
| History | 4 | Create, update, transitions |
| Governance | 6 | Approve, reject, execute, workflow |
| Bulk Operations | 1 | Save many |
| Database | 4 | WAL, migrations, health, rollback |
| Concurrent | 2 | Parallel reads/writes |
| **Total** | **28** | |

---

## 🔧 Key Features

### 1. Optimistic Locking

```python
# Prevents concurrent modification
instance1 = await repo.find_by_id(proposal_id)
instance2 = await repo.find_by_id(proposal_id)

instance1.submit()
await repo.save(instance1)  # Success (version 1 → 2)

instance2.submit()
await repo.save(instance2)  # Raises OptimisticLockError!
```

### 2. Full History Tracking

```python
proposal, history = await repo.get_with_history(proposal_id)

for entry in history:
    print(f"{entry.action}: {entry.previous_status} → {entry.new_status}")
    print(f"  by {entry.actor_id} at {entry.timestamp}")
```

### 3. Flexible Querying

```python
query = ProposalQuery(
    status=ProposalStatus.PENDING,
    created_by="agent-001",
    limit=10,
    offset=0,
    order_by="created_at",
    order_desc=True,
)

result = await repo.query(query)
print(f"Found {result.total} proposals, showing {len(result.items)}")
```

### 4. Governance Helpers

```python
# One-liner operations with auto history
await repo.approve(proposal_id, "admin-001", "Looks good")
await repo.reject(proposal_id, "admin-001", "Not ready")
await repo.execute(proposal_id, result={"success": True})
```

---

## 📋 Verification Checklist

After applying all files:

- [ ] `data/ontology.db` file created
- [ ] WAL mode enabled (`PRAGMA journal_mode` = `wal`)
- [ ] 3 tables created: `proposals`, `proposal_history`, `edit_operations`
- [ ] `_migrations` table tracks applied migrations
- [ ] 28 tests passing
- [ ] MCP server initializes with persistent storage
- [ ] `list_pending_proposals` returns real data

---

## 🚨 Troubleshooting

### "No module named 'aiosqlite'"

```bash
pip install aiosqlite --break-system-packages
```

### "Database is locked"

WAL mode should prevent this, but if it occurs:
```python
# Increase timeout
config = DatabaseConfig(path=path, timeout=60.0)
```

### "OptimisticLockError"

This means another process modified the proposal. Re-fetch and retry:
```python
try:
    await repo.save(proposal)
except OptimisticLockError:
    proposal = await repo.find_by_id(proposal.id)
    # Re-apply changes and retry
```

---

## 🎯 Next Steps After Implementation

1. **Integrate with Kernel** — Update `kernel.py` to use repository
2. **Add Cleanup Job** — Archive old executed/rejected proposals
3. **Add Metrics** — Track proposal processing times
4. **Add Notifications** — Real Slack/email on status changes

---

## 📁 Final Directory Structure

```
scripts/ontology/
├── __init__.py
├── ontology_types.py
├── actions.py
├── client.py
├── side_effects.py
├── objects/
│   ├── __init__.py
│   ├── core_definitions.py
│   ├── proposal.py
│   └── task_actions.py
└── storage/              ← NEW
    ├── __init__.py
    ├── database.py       ← Database manager
    └── proposal_repository.py  ← Repository

data/
└── ontology.db           ← SQLite database

tests/e2e/
├── test_v3_production.py
├── test_oda_v3_scenarios.py
└── test_proposal_repository.py  ← NEW
```

---

**End of Master Guide**
