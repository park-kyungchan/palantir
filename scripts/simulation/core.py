
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from scripts.ontology.ontology_types import OrionObject
from scripts.ontology.manager import ObjectManager
from scripts.action.core import ActionDefinition, ActionContext, ActionRunner

class SimulationDiff(BaseModel):
    created: List[Dict[str, Any]] = Field(default_factory=list)
    updated: List[Dict[str, Any]] = Field(default_factory=list)
    deleted: List[str] = Field(default_factory=list)

class ScenarioFork:
    """
    The Phase 3 Sandbox.
    Wraps execution in a strict NESTED TRANSACTION (Savepoint) that is ALWAYS rolled back.
    """
    def __init__(self, manager: ObjectManager, parent_session: Optional[Session] = None):
        self.manager = manager
        self.session = parent_session or manager.create_session()
        self._owns_session = parent_session is None
        self.nested_tx = None
        self._diff = SimulationDiff()
        
    def __enter__(self):
        # 1. Begin Savepoint
        self.nested_tx = self.session.begin_nested()
            
        # 2. Hook into ObjectManager to capture Event Stream (Observer Pattern)
        # We need to capture what *would* happen.
        # SQLAlchemy's 'session.new', 'session.dirty' works, but only before flush/commit.
        # Since UnitOfWork COMMITS (releases savepoint), the session appears clean after execution!
        # Solution: We need to listen to ObjectManager events *during* execution.
        self.manager.subscribe(self._capture_event)
        
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        # 3. Cleanup: Unsubscribe
        self.manager.unsubscribe(self._capture_event)
        
        # 4. ROLLBACK everything
        if self.nested_tx:
            print("[ScenarioFork] Sandbox Rolled Back (Clean State).")
            self.nested_tx.rollback()
        self.session.rollback()
        if self._owns_session:
            self.session.close()
        
    def _capture_event(self, event_type: str, result: Any):
        """
        Listener for ObjectManager events.
        """
        # print(f"[Debug] Captured Event: {event_type} - {result}")
        if event_type == "save":
            obj: OrionObject = result
            if obj.__class__.__name__ == "OrionActionLog":
                return
            # Naive Diff Logic
            # Note: We duplicate data here because the object might be rolled back.
            change_payload = {
                "id": obj.id,
                "type": obj.__class__.__name__,
                "changes": obj.get_changes()
            }
            # Avoid duplicates?
            self._diff.updated.append(change_payload)
            
        elif event_type == "delete":
            self._diff.deleted.append(str(result))
            
    def get_diff(self) -> SimulationDiff:
        return self._diff

class SimulationEngine:
    """
    Orchestrates the 'What-If'.
    """
    def __init__(self, manager: ObjectManager):
        self.manager = manager
        
    def run_simulation(self, actions: List[ActionDefinition], contexts: List[ActionContext]) -> SimulationDiff:
        print("[SimulationEngine] Starting Scenario Fork...")
        
        fork = ScenarioFork(self.manager)
        
        try:
            with fork as sandbox_session:
                # Configure Runner with Sandbox Session
                runner = ActionRunner(self.manager, session=sandbox_session)
                
                for action, ctx in zip(actions, contexts):
                    # Execute
                    # Note: ctx.session will be set by runner
                    try:
                        runner.execute(action, ctx)
                    except Exception as e:
                        print(f"[SimulationEngine] Action Failed: {e}")
                        # We continue? Or abort simulation?
                        # Usually abort.
                        break
            
            return fork.get_diff()
            
        except Exception as e:
            print(f"[SimulationEngine] Fork Crashed: {e}")
            return SimulationDiff()
