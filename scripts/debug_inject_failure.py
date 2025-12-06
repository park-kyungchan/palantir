from scripts.observer import Observer
from scripts.ontology import Event, EventType
from datetime import datetime
import uuid

def inject():
    trace_id = Observer.start_trace("test_failure_mining", tags=["test"])
    
    # Emit normal event
    Observer.emit(Event(
        id=str(uuid.uuid4()),
        trace_id=trace_id,
        event_type=EventType.ACTION_START,
        component="Executor",
        details={"action": "run_command", "cmd": "bad_cmd"},
        timestamp=datetime.now().isoformat()
    ))
    
    # Emit Failure
    Observer.emit(Event(
        id=str(uuid.uuid4()),
        trace_id=trace_id,
        event_type=EventType.ERROR,
        component="Executor",
        details={"error": "FileNotFoundError: /bad/path not found"},
        timestamp=datetime.now().isoformat()
    ))
    
    # End Trace (FAILED)
    from scripts.ontology import StatusEnum
    Observer.end_trace(StatusEnum.FAILED)

if __name__ == "__main__":
    inject()
    # Inject twice to ensure pattern (min_sup=2)
    inject()
