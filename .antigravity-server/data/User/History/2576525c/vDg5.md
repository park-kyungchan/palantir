# Implementation: HWP Automation Events

The HWPX Knowledge Base includes a registry of available Automation Events extracted from official C++ technical guides. These events allow the system to hook into document lifecycle changes.

## 1. Extraction Methodology
Events were extracted from `한글오토메이션EventHandler추가_2504.pdf` using the `TextEventIngestor` (`lib/ingestors/event_ingestor.py`). 
- **Source**: C++ MFC `IHwpObjectEvents` implementation.
- **Pattern**: `STDMETHOD(EventName)(Args)` regex matching.

## 2. Extracted Events Registry

The following 11 events have been verified and integrated into `action_db.json`:

| Event ID | Arguments | Description |
| :--- | :--- | :--- |
| **Quit** | `()` | Triggered when the HWP application is terminated. |
| **CreateXHwpWindow** | `()` | Triggered when a new HWP window is created. |
| **CloseXHwpWindow** | `()` | Triggered when an HWP window is closed. |
| **NewDocument** | `(long newVal)` | Triggered when a new empty document is created. |
| **DocumentBeforeClose** | `(long newVal)` | Triggered before a document is closed. |
| **DocumentBeforeOpen** | `(long newVal)` | Triggered before opening a document file. |
| **DocumentAfterOpen** | `(long newVal)` | Triggered after a document file is successfully opened. |
| **DocumentBeforeSave** | `(long newVal)` | Triggered before a document is saved to disk. |
| **DocumentAfterSave** | `(long newVal)` | Triggered after a document is successfully saved. |
| **DocumentAfterClose** | `(long newVal)` | Triggered after a document is closed. |
| **DocumentChange** | `(long newVal)` | Triggered when content or state changes within the document. |

## 3. Knowledge Base Integration
The events are stored in the `events` dictionary within the `ActionDatabase` schema:

```python
class EventDefinition(BaseModel):
    event_id: str
    description: Optional[str] = None
    arguments: Optional[str] = None
```

This allows the HWP Compiler or a high-level automation agent to proactively register handlers for these specific IDs during document processing sessions.
