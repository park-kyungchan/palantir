# ODA Full Import Refactoring Migration Plan

> **Version:** 1.0
> **Author:** Orion ODA Agent
> **Created:** 2026-01-10
> **Status:** Ready for Execution

---

## Overview

### Goal
Migrate ODA core modules from `park-kyungchan/palantir/scripts/` to `/home/palantir/lib/oda/` for a clean, reusable package structure.

### Key Features
- **AIP-FREE**: Claude Max monthly subscription only (no external API costs)
- **Package Isolation**: Clean `oda.*` namespace instead of `scripts.*`
- **Zero Downtime**: Symlink strategy for backward compatibility

### Estimated Duration
- Phase 1-2: 1 day
- Phase 3-4: 2-3 days
- Phase 5-6: 1 day
- **Total: 2-3 weeks** (with testing buffer)

### Statistics Summary
| Category | Count |
|----------|-------|
| `from scripts.ontology` imports | 258 occurrences in 102 files |
| `from scripts.claude` imports | 16 occurrences in 8 files |
| `from scripts.infrastructure` imports | 6 occurrences in 5 files |
| `from scripts.memory` imports | 2 occurrences in 2 files |
| `import scripts.*` imports | 1 occurrence in 1 file |
| Hardcoded paths | 16 files |
| **Total changes** | ~283 import changes + 16 path fixes |

---

## Phase 1: Directory Creation and File Copy

### 1.1 Pre-flight Check
```bash
# Verify source exists
ls -la /home/palantir/park-kyungchan/palantir/scripts/ontology/
ls -la /home/palantir/park-kyungchan/palantir/scripts/claude/
ls -la /home/palantir/park-kyungchan/palantir/scripts/infrastructure/
ls -la /home/palantir/park-kyungchan/palantir/scripts/memory/
ls -la /home/palantir/park-kyungchan/palantir/scripts/consolidation/
```

**Expected Output:** Directory listings for all 5 directories

### 1.2 Create Target Directory
```bash
mkdir -p /home/palantir/lib/oda
```

### 1.3 Copy ODA Core Modules
```bash
# Copy all core modules (preserving structure)
cp -r /home/palantir/park-kyungchan/palantir/scripts/ontology /home/palantir/lib/oda/
cp -r /home/palantir/park-kyungchan/palantir/scripts/claude /home/palantir/lib/oda/
cp -r /home/palantir/park-kyungchan/palantir/scripts/infrastructure /home/palantir/lib/oda/
cp -r /home/palantir/park-kyungchan/palantir/scripts/memory /home/palantir/lib/oda/
cp -r /home/palantir/park-kyungchan/palantir/scripts/consolidation /home/palantir/lib/oda/
```

### 1.4 Create Package Init
```bash
# Create __init__.py for oda package
cat > /home/palantir/lib/oda/__init__.py << 'EOF'
"""
Orion ODA (Ontology-Driven Architecture) Package
================================================
Version: 4.0
License: MIT
"""
__version__ = "4.0.0"
EOF
```

### 1.5 Verification
```bash
ls -la /home/palantir/lib/oda/

# Expected output:
# drwxr-xr-x ontology/
# drwxr-xr-x claude/
# drwxr-xr-x infrastructure/
# drwxr-xr-x memory/
# drwxr-xr-x consolidation/
# -rw-r--r-- __init__.py
```

### 1.6 Rollback (Phase 1)
```bash
rm -rf /home/palantir/lib/oda
```

---

## Phase 2: Import Statement Refactoring

### 2.1 scripts.ontology Changes (258 occurrences in 102 files)

```bash
# Change "from scripts.ontology" to "from oda.ontology"
find /home/palantir/lib/oda -name "*.py" -exec sed -i 's/from scripts\.ontology/from oda.ontology/g' {} \;

# Change "import scripts.ontology" to "import oda.ontology"
find /home/palantir/lib/oda -name "*.py" -exec sed -i 's/import scripts\.ontology/import oda.ontology/g' {} \;
```

### 2.2 scripts.claude Changes (16 occurrences in 8 files)

```bash
# Change "from scripts.claude" to "from oda.claude"
find /home/palantir/lib/oda -name "*.py" -exec sed -i 's/from scripts\.claude/from oda.claude/g' {} \;

# Change "import scripts.claude" to "import oda.claude"
find /home/palantir/lib/oda -name "*.py" -exec sed -i 's/import scripts\.claude/import oda.claude/g' {} \;
```

### 2.3 scripts.infrastructure Changes (6 occurrences in 5 files)

```bash
# Change "from scripts.infrastructure" to "from oda.infrastructure"
find /home/palantir/lib/oda -name "*.py" -exec sed -i 's/from scripts\.infrastructure/from oda.infrastructure/g' {} \;

# Change "import scripts.infrastructure" to "import oda.infrastructure"
find /home/palantir/lib/oda -name "*.py" -exec sed -i 's/import scripts\.infrastructure/import oda.infrastructure/g' {} \;
```

### 2.4 scripts.memory Changes (2 occurrences in 2 files)

```bash
# Change "from scripts.memory" to "from oda.memory"
find /home/palantir/lib/oda -name "*.py" -exec sed -i 's/from scripts\.memory/from oda.memory/g' {} \;

# Change "import scripts.memory" to "import oda.memory"
find /home/palantir/lib/oda -name "*.py" -exec sed -i 's/import scripts\.memory/import oda.memory/g' {} \;
```

### 2.5 scripts.consolidation Changes

```bash
# Change "from scripts.consolidation" to "from oda.consolidation"
find /home/palantir/lib/oda -name "*.py" -exec sed -i 's/from scripts\.consolidation/from oda.consolidation/g' {} \;

# Change "import scripts.consolidation" to "import oda.consolidation"
find /home/palantir/lib/oda -name "*.py" -exec sed -i 's/import scripts\.consolidation/import oda.consolidation/g' {} \;
```

### 2.6 Verification Script
```bash
# Verify no remaining scripts.* imports in oda package
echo "Checking for remaining 'from scripts.' imports..."
grep -r "from scripts\." /home/palantir/lib/oda --include="*.py" | wc -l
# Expected: 0

echo "Checking for remaining 'import scripts.' imports..."
grep -r "import scripts\." /home/palantir/lib/oda --include="*.py" | wc -l
# Expected: 0

# Full verification
echo "Full import check..."
grep -rn "scripts\." /home/palantir/lib/oda --include="*.py" | grep -v "__pycache__" | head -20
# Expected: Empty or only comments/docstrings
```

### 2.7 Rollback (Phase 2)
```bash
# Re-copy original files
rm -rf /home/palantir/lib/oda/ontology
rm -rf /home/palantir/lib/oda/claude
rm -rf /home/palantir/lib/oda/infrastructure
rm -rf /home/palantir/lib/oda/memory
rm -rf /home/palantir/lib/oda/consolidation

cp -r /home/palantir/park-kyungchan/palantir/scripts/ontology /home/palantir/lib/oda/
cp -r /home/palantir/park-kyungchan/palantir/scripts/claude /home/palantir/lib/oda/
cp -r /home/palantir/park-kyungchan/palantir/scripts/infrastructure /home/palantir/lib/oda/
cp -r /home/palantir/park-kyungchan/palantir/scripts/memory /home/palantir/lib/oda/
cp -r /home/palantir/park-kyungchan/palantir/scripts/consolidation /home/palantir/lib/oda/
```

---

## Phase 3: Hardcoded Path Fixes (16 files)

### 3.1 File: scripts/claude/sandbox_runner.py (Line 71)

**Location:** `/home/palantir/lib/oda/claude/sandbox_runner.py`

**Current Code (Line 71):**
```python
workspace_root: Path = field(default_factory=lambda: Path("/home/palantir/park-kyungchan/palantir"))
```

**Change To:**
```python
workspace_root: Path = field(default_factory=lambda: Path(os.environ.get("ORION_WORKSPACE_ROOT", "/home/palantir/park-kyungchan/palantir")))
```

**Verification:**
```bash
grep -n "ORION_WORKSPACE_ROOT\|park-kyungchan" /home/palantir/lib/oda/claude/sandbox_runner.py
```

---

### 3.2 File: scripts/ontology/validators/schema_validator.py (Lines 220-224)

**Location:** `/home/palantir/lib/oda/ontology/validators/schema_validator.py`

**Current Code (Lines 220-224):**
```python
@staticmethod
def _get_default_schema_path() -> Path:
    """Get default schema path."""
    # Try to find workspace root
    workspace_root = os.environ.get(
        "ORION_WORKSPACE_ROOT",
        "/home/palantir/park-kyungchan/palantir"
    )
    return Path(workspace_root) / ".agent" / "schemas" / "ontology_registry.json"
```

**Status:** Already uses `ORION_WORKSPACE_ROOT` environment variable with fallback. No change needed, but verify the fallback is acceptable.

---

### 3.3 File: scripts/ontology/memory_sync.py (Lines 11-13)

**Location:** `/home/palantir/lib/oda/ontology/memory_sync.py`

**Current Code:**
```python
WORKSPACE_ROOT = Path(os.environ.get("ORION_WORKSPACE_ROOT", "/home/palantir"))
SYSTEM_PROMPT = Path(os.environ.get("ORION_SYSTEM_PROMPT", WORKSPACE_ROOT / ".gemini" / "GEMINI.md"))
ORION_MEMORY = Path("/home/palantir/park-kyungchan/palantir/.agent/memory/system_facts.md")
```

**Change To:**
```python
WORKSPACE_ROOT = Path(os.environ.get("ORION_WORKSPACE_ROOT", "/home/palantir"))
PROJECT_ROOT = Path(os.environ.get("ORION_PROJECT_ROOT", "/home/palantir/park-kyungchan/palantir"))
SYSTEM_PROMPT = Path(os.environ.get("ORION_SYSTEM_PROMPT", WORKSPACE_ROOT / ".gemini" / "GEMINI.md"))
ORION_MEMORY = PROJECT_ROOT / ".agent" / "memory" / "system_facts.md"
```

---

### 3.4 File: scripts/maintenance/rebuild_db.py (Line 23)

**Location:** `/home/palantir/lib/oda/../maintenance/rebuild_db.py` (NOT in oda, but references it)

**Note:** This file is NOT copied to oda. Update in original location if needed.

**Current Code:**
```python
db_path = os.environ.get("ORION_DB_PATH", "/home/palantir/park-kyungchan/palantir/data/ontology.db")
```

**Status:** Already uses environment variable with fallback. Acceptable.

---

### 3.5 File: scripts/ontology/storage/database.py (Line 220)

**Location:** `/home/palantir/lib/oda/ontology/storage/database.py`

**Current Code (Line 220):**
```python
default_path = "/home/palantir/park-kyungchan/palantir/data/ontology.db"
```

**Change To:**
```python
default_path = os.environ.get(
    "ORION_DB_PATH",
    "/home/palantir/park-kyungchan/palantir/data/ontology.db"
)
```

**Full Context Change (around Line 218-221):**
```python
@classmethod
async def initialize(cls, path: Path | str | None = None) -> Database:
    """Initialize the default database instance."""
    default_path = os.environ.get(
        "ORION_DB_PATH",
        "/home/palantir/park-kyungchan/palantir/data/ontology.db"
    )
    p = path or os.getenv("ORION_DB_PATH", default_path)
    # ... rest of method
```

---

### 3.6 File: scripts/workflow_runner.py (Line 11)

**Location:** NOT in oda package (stays in scripts/)

**Current Code:**
```python
WORKFLOWS_DIR = Path("/home/palantir/park-kyungchan/palantir/.agent/workflows")
```

**Change To (in original location):**
```python
WORKFLOWS_DIR = Path(os.environ.get(
    "ORION_PROJECT_ROOT",
    "/home/palantir/park-kyungchan/palantir"
)) / ".agent" / "workflows"
```

---

### 3.7 File: tests/e2e/test_monolith.py (Line 13)

**Location:** NOT in oda package

**Current Code:**
```python
sys.path.append("/home/palantir/park-kyungchan/palantir")
```

**Change To:**
```python
import os
sys.path.insert(0, os.environ.get("ORION_PROJECT_ROOT", "/home/palantir/park-kyungchan/palantir"))
```

---

### 3.8 File: tests/e2e/test_v3_production.py (Line 9)

**Location:** NOT in oda package

**Current Code:**
```python
sys.path.append("/home/palantir/park-kyungchan/palantir")
```

**Change To:**
```python
import os
sys.path.insert(0, os.environ.get("ORION_PROJECT_ROOT", "/home/palantir/park-kyungchan/palantir"))
```

---

### 3.9 File: tests/e2e/test_v3_full_stack.py (Line 7)

**Location:** NOT in oda package

**Current Code:**
```python
sys.path.append("/home/palantir/park-kyungchan/palantir")
```

**Change To:**
```python
import os
sys.path.insert(0, os.environ.get("ORION_PROJECT_ROOT", "/home/palantir/park-kyungchan/palantir"))
```

---

### 3.10 File: scripts/ontology/handoff.py (Lines 8-10)

**Location:** `/home/palantir/lib/oda/ontology/handoff.py`

**Current Code:**
```python
TEMPLATE_DIR = "/home/palantir/park-kyungchan/palantir/.agent/handoffs/templates"
PENDING_DIR = "/home/palantir/park-kyungchan/palantir/.agent/handoffs/pending"
PLANS_DIR = "/home/palantir/.agent/plans"
```

**Change To:**
```python
import os
_PROJECT_ROOT = os.environ.get("ORION_PROJECT_ROOT", "/home/palantir/park-kyungchan/palantir")
TEMPLATE_DIR = os.path.join(_PROJECT_ROOT, ".agent/handoffs/templates")
PENDING_DIR = os.path.join(_PROJECT_ROOT, ".agent/handoffs/pending")
PLANS_DIR = os.path.join(os.environ.get("ORION_WORKSPACE_ROOT", "/home/palantir"), ".agent/plans")
```

---

### 3.11 File: scripts/ontology/learning/verify_full_engine.py (Lines 5, 10)

**Location:** `/home/palantir/lib/oda/ontology/learning/verify_full_engine.py`

**Current Code:**
```python
sys.path.append(str(Path("/home/palantir/park-kyungchan/palantir")))
# ...
root = "/home/palantir/park-kyungchan/palantir/scripts/ontology"
```

**Change To:**
```python
import os
_PROJECT_ROOT = os.environ.get("ORION_PROJECT_ROOT", "/home/palantir/park-kyungchan/palantir")
sys.path.append(_PROJECT_ROOT)
# ...
root = os.path.join(_PROJECT_ROOT, "scripts/ontology")
```

---

### 3.12 File: scripts/ontology/learning/verify_persistence_quick.py (Line 6)

**Location:** `/home/palantir/lib/oda/ontology/learning/verify_persistence_quick.py`

**Current Code:**
```python
sys.path.append(str(Path("/home/palantir/park-kyungchan/palantir")))
```

**Change To:**
```python
import os
sys.path.append(os.environ.get("ORION_PROJECT_ROOT", "/home/palantir/park-kyungchan/palantir"))
```

---

### 3.13 File: scripts/ontology/learning/verify_scoping_quick.py (Lines 5, 12)

**Location:** `/home/palantir/lib/oda/ontology/learning/verify_scoping_quick.py`

**Current Code:**
```python
sys.path.append(str(Path("/home/palantir/park-kyungchan/palantir")))
# ...
root = "/home/palantir/park-kyungchan/palantir/scripts/ontology"
```

**Change To:**
```python
import os
_PROJECT_ROOT = os.environ.get("ORION_PROJECT_ROOT", "/home/palantir/park-kyungchan/palantir")
sys.path.append(_PROJECT_ROOT)
# ...
root = os.path.join(_PROJECT_ROOT, "scripts/ontology")
```

---

### 3.14 File: scripts/ontology/learning/verify_metrics_quick.py (Line 7)

**Location:** `/home/palantir/lib/oda/ontology/learning/verify_metrics_quick.py`

**Current Code:**
```python
sys.path.append(str(Path("/home/palantir/park-kyungchan/palantir")))
```

**Change To:**
```python
import os
sys.path.append(os.environ.get("ORION_PROJECT_ROOT", "/home/palantir/park-kyungchan/palantir"))
```

---

### 3.15 File: scripts/ontology/relays/result_job_job-test-01.py (Lines 14, 21)

**Location:** `/home/palantir/lib/oda/ontology/relays/result_job_job-test-01.py`

**Current Code:**
```python
sys.path.append("/home/palantir/park-kyungchan/palantir")
# ...
checked_path = "/home/palantir"
```

**Change To:**
```python
import os
sys.path.append(os.environ.get("ORION_PROJECT_ROOT", "/home/palantir/park-kyungchan/palantir"))
# ...
checked_path = os.environ.get("ORION_WORKSPACE_ROOT", "/home/palantir")
```

---

### 3.16 File: scripts/runtime/planning_hook.py (Line 26)

**Location:** NOT in oda package (stays in scripts/)

**Current Code:**
```python
PROJECT_LEVEL_AGENT = Path("/home/palantir/park-kyungchan/palantir/.agent")
```

**Change To (in original location):**
```python
PROJECT_LEVEL_AGENT = Path(os.environ.get(
    "ORION_PROJECT_ROOT",
    "/home/palantir/park-kyungchan/palantir"
)) / ".agent"
```

---

### 3.17 Batch Sed Commands for Hardcoded Paths

```bash
# Run these commands in sequence to fix hardcoded paths in oda package

# 3.1 sandbox_runner.py
sed -i 's|Path("/home/palantir/park-kyungchan/palantir")|Path(os.environ.get("ORION_WORKSPACE_ROOT", "/home/palantir/park-kyungchan/palantir"))|g' /home/palantir/lib/oda/claude/sandbox_runner.py

# 3.3 memory_sync.py - Complex, manual edit recommended
# See section 3.3 above

# 3.5 database.py
sed -i 's|default_path = "/home/palantir/park-kyungchan/palantir/data/ontology.db"|default_path = os.environ.get("ORION_DB_PATH", "/home/palantir/park-kyungchan/palantir/data/ontology.db")|g' /home/palantir/lib/oda/ontology/storage/database.py

# 3.10-3.15 learning verification scripts - Complex, manual edit recommended
```

### 3.18 Verification Script
```bash
# Check for remaining hardcoded project paths
echo "Checking for hardcoded paths in oda package..."
grep -rn "park-kyungchan/palantir" /home/palantir/lib/oda --include="*.py" | grep -v "__pycache__"

# Expected: Only in fallback defaults for os.environ.get()
```

---

## Phase 4: MCP and Environment Configuration

### 4.1 Update .mcp.json

**File:** `/home/palantir/.mcp.json`

**Current Content:**
```json
{
  "mcpServers": {
    "oda-ontology": {
      "type": "stdio",
      "command": "/home/palantir/park-kyungchan/palantir/.venv/bin/python",
      "args": [
        "-m",
        "scripts.mcp.ontology_server"
      ],
      "cwd": "/home/palantir/park-kyungchan/palantir",
      "env": {
        "PYTHONPATH": "/home/palantir/park-kyungchan/palantir",
        "ORION_DB_PATH": "/home/palantir/park-kyungchan/palantir/.agent/tmp/ontology.db"
      }
    }
  }
}
```

**Change To:**
```json
{
  "mcpServers": {
    "oda-ontology": {
      "type": "stdio",
      "command": "/home/palantir/park-kyungchan/palantir/.venv/bin/python",
      "args": [
        "-m",
        "scripts.mcp.ontology_server"
      ],
      "cwd": "/home/palantir/park-kyungchan/palantir",
      "env": {
        "PYTHONPATH": "/home/palantir/lib/oda:/home/palantir/park-kyungchan/palantir",
        "ODA_ROOT": "/home/palantir/lib/oda",
        "ORION_WORKSPACE_ROOT": "/home/palantir",
        "ORION_PROJECT_ROOT": "/home/palantir/park-kyungchan/palantir",
        "ORION_DB_PATH": "/home/palantir/park-kyungchan/palantir/.agent/tmp/ontology.db"
      }
    }
  }
}
```

### 4.2 Create Environment Setup Script

```bash
cat > /home/palantir/lib/oda/setup_env.sh << 'EOF'
#!/bin/bash
# ODA Environment Setup
# Source this file to configure ODA paths

export ODA_ROOT="/home/palantir/lib/oda"
export ORION_WORKSPACE_ROOT="/home/palantir"
export ORION_PROJECT_ROOT="/home/palantir/park-kyungchan/palantir"
export ORION_DB_PATH="${ORION_PROJECT_ROOT}/.agent/tmp/ontology.db"
export PYTHONPATH="${ODA_ROOT}:${ORION_PROJECT_ROOT}:${PYTHONPATH}"

echo "ODA Environment Configured:"
echo "  ODA_ROOT: ${ODA_ROOT}"
echo "  ORION_PROJECT_ROOT: ${ORION_PROJECT_ROOT}"
echo "  PYTHONPATH: ${PYTHONPATH}"
EOF

chmod +x /home/palantir/lib/oda/setup_env.sh
```

### 4.3 Add to .bashrc (Optional)
```bash
echo '# ODA Environment' >> ~/.bashrc
echo 'source /home/palantir/lib/oda/setup_env.sh 2>/dev/null || true' >> ~/.bashrc
```

### 4.4 Verification
```bash
# Verify MCP config
cat /home/palantir/.mcp.json | python3 -m json.tool

# Test environment
source /home/palantir/lib/oda/setup_env.sh
echo $PYTHONPATH
python3 -c "import sys; print('\\n'.join(sys.path))"
```

---

## Phase 5: Testing and Verification

### 5.1 Basic Import Test
```bash
cd /home/palantir/park-kyungchan/palantir
source .venv/bin/activate
source /home/palantir/lib/oda/setup_env.sh

# Test oda imports
python3 -c "from oda.ontology.registry import OntologyRegistry; print('OntologyRegistry: OK')"
python3 -c "from oda.ontology.storage.database import Database; print('Database: OK')"
python3 -c "from oda.claude.protocol_adapter import ProtocolAdapter; print('ProtocolAdapter: OK')"
python3 -c "from oda.infrastructure.metrics import MetricsCollector; print('MetricsCollector: OK')" 2>/dev/null || echo "MetricsCollector: Check import path"
```

**Expected Output:**
```
OntologyRegistry: OK
Database: OK
ProtocolAdapter: OK
MetricsCollector: OK
```

### 5.2 Full Test Suite
```bash
cd /home/palantir/park-kyungchan/palantir
source .venv/bin/activate
source /home/palantir/lib/oda/setup_env.sh

# Run pytest
pytest tests/ -v --tb=short 2>&1 | tee /tmp/oda_migration_test.log

# Check results
echo "Test Summary:"
tail -20 /tmp/oda_migration_test.log
```

### 5.3 MCP Server Test
```bash
# Start MCP server in test mode
cd /home/palantir/park-kyungchan/palantir
source .venv/bin/activate
source /home/palantir/lib/oda/setup_env.sh

# Quick health check
python3 -c "
from scripts.mcp.ontology_server import app
print('MCP Server import: OK')
"

# Full server test (interactive)
# python3 -m scripts.mcp.ontology_server
```

### 5.4 Database Connectivity Test
```bash
source /home/palantir/lib/oda/setup_env.sh
cd /home/palantir/park-kyungchan/palantir
source .venv/bin/activate

python3 << 'EOF'
import asyncio
from oda.ontology.storage.database import DatabaseManager

async def test_db():
    try:
        db = await DatabaseManager.initialize()
        health = await db.health_check()
        print(f"Database Health: {'OK' if health else 'FAILED'}")
    except Exception as e:
        print(f"Database Error: {e}")

asyncio.run(test_db())
EOF
```

---

## Phase 6: Symlink Creation (Backward Compatibility)

### 6.1 Backup Original Directories
```bash
BACKUP_DATE=$(date +%Y%m%d)

# Backup originals
cd /home/palantir/park-kyungchan/palantir/scripts

mv ontology ontology.bak.${BACKUP_DATE}
mv claude claude.bak.${BACKUP_DATE}
mv infrastructure infrastructure.bak.${BACKUP_DATE}
mv memory memory.bak.${BACKUP_DATE}
mv consolidation consolidation.bak.${BACKUP_DATE}
```

### 6.2 Create Symlinks
```bash
cd /home/palantir/park-kyungchan/palantir/scripts

ln -s /home/palantir/lib/oda/ontology ontology
ln -s /home/palantir/lib/oda/claude claude
ln -s /home/palantir/lib/oda/infrastructure infrastructure
ln -s /home/palantir/lib/oda/memory memory
ln -s /home/palantir/lib/oda/consolidation consolidation
```

### 6.3 Verify Symlinks
```bash
ls -la /home/palantir/park-kyungchan/palantir/scripts/

# Expected output:
# lrwxrwxrwx ontology -> /home/palantir/lib/oda/ontology
# lrwxrwxrwx claude -> /home/palantir/lib/oda/claude
# lrwxrwxrwx infrastructure -> /home/palantir/lib/oda/infrastructure
# lrwxrwxrwx memory -> /home/palantir/lib/oda/memory
# lrwxrwxrwx consolidation -> /home/palantir/lib/oda/consolidation
# drwxr-xr-x ontology.bak.YYYYMMDD
# drwxr-xr-x claude.bak.YYYYMMDD
# ...
```

### 6.4 Test Symlink Resolution
```bash
cd /home/palantir/park-kyungchan/palantir
source .venv/bin/activate

# Both import paths should work
python3 -c "from scripts.ontology.registry import OntologyRegistry; print('scripts.ontology: OK')"
python3 -c "from oda.ontology.registry import OntologyRegistry; print('oda.ontology: OK')"
```

---

## Rollback Procedures

### Full Rollback (Emergency)
```bash
# 1. Remove symlinks and restore backups
cd /home/palantir/park-kyungchan/palantir/scripts

rm -f ontology claude infrastructure memory consolidation

BACKUP_DATE="YYYYMMDD"  # Replace with actual date
mv ontology.bak.${BACKUP_DATE} ontology
mv claude.bak.${BACKUP_DATE} claude
mv infrastructure.bak.${BACKUP_DATE} infrastructure
mv memory.bak.${BACKUP_DATE} memory
mv consolidation.bak.${BACKUP_DATE} consolidation

# 2. Remove oda package
rm -rf /home/palantir/lib/oda

# 3. Restore original .mcp.json (if backed up)
# cp /home/palantir/.mcp.json.backup /home/palantir/.mcp.json

# 4. Verify
ls -la /home/palantir/park-kyungchan/palantir/scripts/
python3 -c "from scripts.ontology.registry import OntologyRegistry; print('Rollback OK')"
```

### Partial Rollback (Per Phase)

#### Rollback Phase 1-2 Only
```bash
rm -rf /home/palantir/lib/oda
```

#### Rollback Phase 6 Only (Symlinks)
```bash
cd /home/palantir/park-kyungchan/palantir/scripts

rm -f ontology claude infrastructure memory consolidation

BACKUP_DATE="YYYYMMDD"  # Replace with actual date
mv ontology.bak.${BACKUP_DATE} ontology
mv claude.bak.${BACKUP_DATE} claude
mv infrastructure.bak.${BACKUP_DATE} infrastructure
mv memory.bak.${BACKUP_DATE} memory
mv consolidation.bak.${BACKUP_DATE} consolidation
```

---

## Checklist

### Phase 1: Directory Creation
- [ ] Pre-flight check passed (source directories exist)
- [ ] Target directory created: `/home/palantir/lib/oda/`
- [ ] All 5 modules copied (ontology, claude, infrastructure, memory, consolidation)
- [ ] `__init__.py` created

### Phase 2: Import Refactoring
- [ ] `scripts.ontology` -> `oda.ontology` (258 occurrences)
- [ ] `scripts.claude` -> `oda.claude` (16 occurrences)
- [ ] `scripts.infrastructure` -> `oda.infrastructure` (6 occurrences)
- [ ] `scripts.memory` -> `oda.memory` (2 occurrences)
- [ ] `scripts.consolidation` -> `oda.consolidation`
- [ ] Verification: `grep -r "from scripts\." /home/palantir/lib/oda` returns 0 results

### Phase 3: Hardcoded Path Fixes
- [ ] sandbox_runner.py (Line 71)
- [ ] schema_validator.py (already env-aware, verify)
- [ ] memory_sync.py (Lines 11-13)
- [ ] database.py (Line 220)
- [ ] handoff.py (Lines 8-10)
- [ ] verify_full_engine.py (Lines 5, 10)
- [ ] verify_persistence_quick.py (Line 6)
- [ ] verify_scoping_quick.py (Lines 5, 12)
- [ ] verify_metrics_quick.py (Line 7)
- [ ] result_job_job-test-01.py (Lines 14, 21)
- [ ] Verification: All paths use `os.environ.get()` with fallbacks

### Phase 4: Environment Configuration
- [ ] `.mcp.json` updated with new PYTHONPATH
- [ ] `setup_env.sh` created
- [ ] Environment variables set correctly
- [ ] MCP config validated with `python3 -m json.tool`

### Phase 5: Testing
- [ ] Basic import tests pass
- [ ] `pytest tests/` passes (or acceptable failures documented)
- [ ] MCP server starts correctly
- [ ] Database connectivity verified

### Phase 6: Symlink Creation
- [ ] Original directories backed up with date suffix
- [ ] Symlinks created for all 5 modules
- [ ] Both `scripts.*` and `oda.*` imports work
- [ ] Full test suite passes with symlinks

### Final Verification
- [ ] All tests pass
- [ ] MCP tools work (list_actions, execute_action)
- [ ] No regression in existing functionality
- [ ] Backup files can be safely removed (after stabilization period)

---

## Notes

### Environment Variables Summary
| Variable | Purpose | Default |
|----------|---------|---------|
| `ODA_ROOT` | ODA package location | `/home/palantir/lib/oda` |
| `ORION_WORKSPACE_ROOT` | User home/workspace | `/home/palantir` |
| `ORION_PROJECT_ROOT` | Project root | `/home/palantir/park-kyungchan/palantir` |
| `ORION_DB_PATH` | Database file path | `{PROJECT_ROOT}/.agent/tmp/ontology.db` |
| `PYTHONPATH` | Python import paths | `{ODA_ROOT}:{PROJECT_ROOT}` |

### Known Limitations
1. Some test files have hardcoded paths that are NOT in the oda package
2. External references to `scripts.*` in non-Python files may need manual updates
3. The MCP server still runs via `scripts.mcp.ontology_server` (not migrated)

### Future Improvements
1. Create proper `setup.py` or `pyproject.toml` for pip installation
2. Publish to internal PyPI for multi-project reuse
3. Add version pinning and dependency management
