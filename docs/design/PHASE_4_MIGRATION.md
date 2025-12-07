
# Phase 4 Detailed Design: The Great Migration (V2 -> Orion)

> **Objective**: Migrate "Protoplasmic" Data (JSON files) into the "Living Object" Kernel (SQLite + FTS).
> **Scope**: Semantic Memory (Insights/Patterns) & Legacy Plans.

---

## 1. The Challenge (Passive vs. Living)
Currently, `Semantic Memory` resides in `.agent/memory/semantic/` as thousands of JSON files.
*   **Pros**: Simple, grep-able.
*   **Cons**: No relationships, no ACID, slow searches, weak schema enforcement (JSONSchema).

**Goal**: Transform these into `OrionObject` rows in the `objects` table, enabling:
1.  **Full-Text Search (FTS)**: "Find insights about 'python' sorted by confidence."
2.  **Relational Linking**: "Link Pattern X to Insight Y."
3.  **Unified Governance**: Manage them via `ObjectManager`.

---

## 2. Schema Translation (Pydantic V2)

### 2.1 Insights
**Legacy**:
```json
{"id": "...", "content": {"summary": "..."}, "meta": {"confidence_score": 0.9}}
```
**Orion (Pydantic)**:
```python
class OrionInsight(OrionObject):
    confidence_score: float = Field(default=1.0)
    provenance: Dict[str, Any]
    content: Dict[str, Any]
    
    def get_searchable_text(self):
        return f"{self.content['summary']} {self.content.get('tags', '')}"
```

### 2.2 Patterns
**Legacy**:
```json
{"id": "...", "structure": {"trigger": "...", "steps": [...]}}
```
**Orion (Pydantic)**:
```python
class OrionPattern(OrionObject):
    trigger: str
    steps: List[str]
    success_rate: float
    frequency: int
    
    def get_searchable_text(self):
        return f"{self.trigger} {' '.join(self.steps)}"
```

---

## 3. Migration Strategy: "The Ark"

### Step 3.1: Preparation (Core Update)
- Add `fts_content` column to the `objects` table (if not exists).
- Update `ObjectManager.save()` to auto-populate `fts_content` by calling `obj.get_searchable_text()`.

### Step 3.2: The Migration Script (`scripts/migration/migrate_memory.py`)
1.  **Scan**: Walk `.agent/memory/` directory.
2.  **Read**: Parse JSON.
3.  **Transform**: Instantiate `OrionInsight` / `OrionPattern`.
    *   Maintain original UUID if possible (or map `old_id` -> `new_uuid`).
    *   Preserve `created_at` timestamps.
4.  **Save**: `manager.save(obj)`.
5.  **Archive**: Move original JSON to `.agent/memory/archived/`.

### Step 3.3: Verification (`scripts/migration/tests/test_migration.py`)
1.  Mock a folder with 3 Legacy JSONs.
2.  Run Migration.
3.  Query `ObjectManager` for ID.
4.  Query SQLite for FTS matches.
5.  Assert `archived` folder contains the JSONs.

---

## 4. Plan Migration (Optional but Recommended)
Move `scripts/ontology/plan.py` classes (`Plan`, `Job`) into the Ontology Kernel.
- **Why?** Allows us to query "Past Plans" via FTS.
- **How?**: `OrionPlan(OrionObject)` wrapping the old structure.

---

## 5. Execution Plan
1.  **Define new Schemas**: `scripts/ontology/schemas/memory.py`
2.  **Update Core**: `ObjectManager` FTS logic.
3.  **Write Script**: `migrate_memory.py`.
4.  **Run & Verify**.
