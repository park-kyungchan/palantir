
import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from scripts.ontology import Trace, Event, Metric, StatusEnum

TRACE_DIR = os.path.abspath(".agent/traces")
os.makedirs(TRACE_DIR, exist_ok=True)

class Observer:
    """
    Central Observability Bus (V3.0 Standard).
    Unified interface for Logging, Tracing, and Metrics.
    """
    _instance = None
    _current_trace: Optional[Trace] = None
    _events: List[Event] = []
    _metrics: List[Metric] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Observer, cls).__new__(cls)
        return cls._instance

    @classmethod
    def start_trace(cls, task_id: str, tags: List[str] = []) -> str:
        """Starts a new execution trace."""
        trace_id = str(uuid.uuid4())
        cls._current_trace = Trace(
            id=trace_id,
            type="Trace",
            created_at=datetime.now().isoformat(),
            meta_version=1,
            task_id=task_id,
            start_time=datetime.now().isoformat(),
            status=StatusEnum.RUNNING,
            tags=tags
        )
        cls._events = []
        cls._metrics = []
        print(f"👁️ [Observer] Trace Started: {trace_id} (Task: {task_id})")
        return trace_id

    @classmethod
    def emit(cls, event: Event):
        """
        Standard V3.0 Interface: Emits a full Event object.
        Used by Governance Layer.
        """
        if not cls._current_trace:
            # Fallback if no trace is active (e.g. system boot)
            print(f"⚠️ [Observer] Creating ad-hoc trace for event: {event.event_type}")
            cls.start_trace(task_id="system_adhoc")
        
        # Link event to trace if not already linked
        if hasattr(event, "trace_id") and not event.trace_id:
            event.trace_id = cls._current_trace.id
            
        cls._events.append(event)
        
        # Real-time console feedback
        icon = "ℹ️"
        # Convert Enum to string for safety if needed, or comparsion
        et = event.event_type
        # Assuming et is an Enum member
        
        from scripts.ontology import EventType
        if et == EventType.ERROR: icon = "❌"
        elif et == EventType.ACTION_START: icon = "▶️"
        elif et == EventType.ACTION_END: icon = "✅"
        
        # Parse content for nice log
        details = str(event.details)
        print(f"   {icon} [{event.component}] {et}: {details[:100]}")

    @classmethod
    def log_event(cls, event_type: Any, component: str, details: Dict[str, Any]):
        """Legacy helper for simple logging."""
        # Ensure event_type is Enum if possible, otherwise cast?
        # For now assume legacy strings might come in, but strictly we need Enum
        from scripts.ontology import EventType
        
        # Simple mapping for legacy calls (if any)
        et = EventType.STATE_CHANGE 
        
        event = Event(
            trace_id=cls._current_trace.id if cls._current_trace else "TRACE-LEGACY",
            timestamp=datetime.now().isoformat(),
            event_type=et,
            component=component,
            details=details
        )
        cls.emit(event)

    @classmethod
    def end_trace(cls, status=StatusEnum.COMPLETED):
        """Ends the current trace and persists data."""
        if not cls._current_trace:
            return

        cls._current_trace.end_time = datetime.now().isoformat()
        cls._current_trace.status = status
        
        # Persist to JSON
        trace_data = {
            "trace": cls._current_trace.model_dump(mode='json'),
            "events": [e.model_dump(mode='json') for e in cls._events],
            # "metrics": [m.model_dump(mode='json') for m in cls._metrics] # Metrics integration pending
        }
        
        filename = os.path.join(TRACE_DIR, f"{cls._current_trace.id}.json")
        with open(filename, 'w') as f:
            json.dump(trace_data, f, indent=2)
            
        print(f"👁️ [Observer] Trace Saved: {filename}")
        cls._current_trace = None

# Alias for backward compatibility if needed, but we prefer Observer
EventBus = Observer
