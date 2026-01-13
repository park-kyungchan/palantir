# [Plan] HWPX Event Handler Knowledge Extraction

## 1. Goal Description
The objective is to extract **HWP Automation Events** from the technical guide `한글오토메이션EventHandler추가_2504.pdf`. Use this to populate the `ActionDatabase` with a list of valid events (e.g., `onDocumentBeforeSave`), enabling the system to understand and generate event-driven automation code.

## 2. Analysis & Surface Scan (Stage A)
*   **Source**: `한글오토메이션EventHandler추가_2504.pdf` (Technical Manual, C++/ATL code)
*   **Content**: Contains C++ COM interface definitions (`STDMETHOD(EventName)(...)`).
*   **Pattern**: `STDMETHOD(EventName)(args)` inside `IHwpObjectEvents` implementation.
*   **Target Data**: List of Event Names (e.g., `Quit`, `DocumentChange`) and potential arguments.

## 3. Implementation Strategy (Stage B)

### 3.1 Schema Enhancement
Update `lib/knowledge/schema.py` to include `EventDefinition`.
```python
class EventDefinition(BaseModel):
    event_id: str  # e.g., "DocumentBeforeSave"
    description: Optional[str] = None
    arguments: Optional[str] = None # e.g., "long newVal"

class ActionDatabase(BaseModel):
    ...
    events: Dict[str, EventDefinition] = Field(default_factory=dict)
```

### 3.2 Ingestor Implementation (`TextEventIngestor`)
Create `lib/ingestors/event_ingestor.py`.
*   Use `pdftotext` to get full text.
*   Regex match: `STDMETHOD\s*\(\s*(\w+)\s*\)\s*\((.*?)\)`
*   Extract `EventName` and `Args`.
*   Deduplicate entries.

### 3.3 Integration
Update `scripts/build_knowledge_base.py` to:
1.  Run `TextEventIngestor`.
2.  Populate `db.events`.
3.  Save to `action_db.json`.

## 4. Verification Plan (Stage C)
### Automated Tests
1.  Run `build_knowledge_base.py`.
2.  Verify `action_db.json` contains `events` key.
3.  Check for known events: `DocumentBeforeSave`, `Quit`.

### Manual Verification
1.  Inspect the generated JSON to ensure C++ syntax (`STDMETHOD`) is stripped and only clean Event IDs remain.
