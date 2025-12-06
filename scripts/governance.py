
import logging
import uuid
import json
import os
import sqlite3
from datetime import datetime
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Any, Dict
from pydantic import BaseModel
from scripts.observer import Observer
from scripts.ontology import Event, EventType

# Mimic Palantir's UserFacingError
class UserFacingError(Exception):
    def __init__(self, message: str, error_name: str = "InvalidAction"):
        self.message = message
        self.error_name = error_name
        super().__init__(f"[{error_name}] {message}")

class OntologyContext:
    """Read-Only view of the Ontology for validation."""
    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root

TParams = TypeVar("TParams", bound=BaseModel)

class OrionAction(ABC, Generic[TParams]):
    """
    Tier 1 Action: Class-based, Schematized, Deterministic.
    Use this for Core Ontology Mutations (Plans, Jobs, Objects).
    """
    def __init__(self, parameters: TParams):
        self.params = parameters
        self.action_id = str(uuid.uuid4())
        self.timestamp = datetime.now()

    @property
    @abstractmethod
    def action_type(self) -> str:
        """Unique API Identifier for the Action."""
        pass

    @abstractmethod
    def validate(self, ctx: OntologyContext) -> None:
        """Pure logic validation. Raises UserFacingError."""
        pass

    @abstractmethod
    def _apply_side_effects(self, ctx: OntologyContext) -> dict:
        """The actual mutation logic (Privacy: Protected)."""
        pass

class ActionDispatcher:
    """
    The Governance Funnel.
    Enforces Rule 1.1 (Action Mandate) and Rule 4.1 (Audit).
    """
    def __init__(self, workspace_root: str):
        self.ctx = OntologyContext(workspace_root)
        self.logger = logging.getLogger("OrionGovernance")
        self._db_path = os.path.join(workspace_root, ".agent", "logs", "ontology.db")
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize the SQLite Audit Ledger (Immutable Log)."""
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT NOT NULL,
                        event_type TEXT NOT NULL,
                        action_type TEXT NOT NULL,
                        action_id TEXT NOT NULL,
                        parameters TEXT NOT NULL, -- JSON String
                        user TEXT NOT NULL,
                        result TEXT, -- JSON String (Updated on commit)
                        status TEXT DEFAULT 'PENDING'
                    )
                """)
                conn.commit()
        except Exception as e:
            self.logger.critical(f"Failed to initialize Ledger DB: {e}")
            raise

    def dispatch(self, action: OrionAction) -> Dict[str, Any]:
        try:
            # 1. Logic / Validation (Rule 1.2)
            action.validate(self.ctx)

            # 2. Intent Capture (Audit Log - Transaction Start)
            self._log_intent(action)

            # 3. Notification (Observer)
            Observer.emit(Event(
                trace_id=f"TRACE-{action.action_id}", # Link trace to action
                event_type=EventType.ACTION_START,
                component="ActionDispatcher",
                details={"action_id": action.action_id, "type": action.action_type},
                timestamp=datetime.now().isoformat()
            ))

            # 4. Side Effect (Mutation)
            result = action._apply_side_effects(self.ctx)

            # 5. Success (Update Ledger)
            self._update_ledger_success(action.action_id, result)

            Observer.emit(Event(
                trace_id=f"TRACE-{action.action_id}",
                event_type=EventType.ACTION_END,
                component="ActionDispatcher",
                details={"action_id": action.action_id, "result": result},
                timestamp=datetime.now().isoformat()
            ))
            
            return {"status": "success", "action_id": action.action_id, "result": result}

        except UserFacingError as e:
            self.logger.warning(f"Action Rejected: {e}")
            self._update_ledger_fail(action.action_id, str(e))
            raise
        except Exception as e:
            self.logger.error(f"System Failure in Action {action.action_id}: {e}")
            self._update_ledger_fail(action.action_id, str(e))
            raise RuntimeError("Internal Ontology Error") from e

    def _log_intent(self, action: OrionAction):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "INSERT INTO audit_log (id, timestamp, event_type, action_type, action_id, parameters, user) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    str(uuid.uuid4()),
                    action.timestamp.isoformat(),
                    "ontology_action_submission",
                    action.action_type,
                    action.action_id,
                    action.params.model_dump_json(),
                    "local_agent"
                )
            )
            conn.commit()

    def _update_ledger_success(self, action_id: str, result: Dict):
        with sqlite3.connect(self._db_path) as conn:
            conn.execute(
                "UPDATE audit_log SET status = ?, result = ? WHERE action_id = ?",
                ("COMMITTED", json.dumps(result), action_id)
            )
            conn.commit()

    def _update_ledger_fail(self, action_id: str, error: str):
        try:
            with sqlite3.connect(self._db_path) as conn:
                conn.execute(
                    "UPDATE audit_log SET status = ?, result = ? WHERE action_id = ?",
                    ("FAILED", json.dumps({"error": error}), action_id)
                )
                conn.commit()
        except:
            pass # Fail silently if DB is broken

