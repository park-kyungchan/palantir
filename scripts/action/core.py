
from abc import ABC, abstractmethod
from typing import List, Optional, Any, Dict, Type
from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from scripts.ontology.manager import ObjectManager, OrionObject
from scripts.ontology.schemas.governance import OrionActionLog
from scripts.ontology.db import SessionLocal

class ActionContext(BaseModel):
    """
    Runtime context for an Action Execution.
    Holds the Transactional Session and Parameters.
    """
    job_id: str = Field(..., description="Traceability ID")
    parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Runtime Objects (will be injected by ActionRunner)
    session: Optional[Session] = None
    manager: Optional[ObjectManager] = None

    class Config:
        arbitrary_types_allowed = True

class UnitOfWork:
    """
    Manages the Transaction Lifecycle.
    Supports Session Injection for Simulation via Nested Transactions.
    """
    def __init__(self, manager: ObjectManager, session: Optional[Session] = None):
        self.manager = manager
        self.transaction = None
        if session:
            self.session = session
            self.owns_session = False
            # Safety: Wrap injected session in a nested transaction
            # This ensures 'commit' only merges to the parent Savepoint, 
            # keeping the ScenarioFork Savepoint alive.
            self.transaction = self.session.begin_nested()
        else:
            self.session = SessionLocal()
            self.owns_session = True
        self.committed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                # Exception occurred -> Rollback
                print(f"[UnitOfWork] Exception detected: {exc_val}. Rolling back...")
                try:
                    if self.transaction:
                        self.transaction.rollback()
                    else:
                        self.session.rollback()
                except Exception as e:
                    print(f"[UnitOfWork] Rollback ignored (already closed?): {e}")
                    # CRITICAL: If nested rollback fails, the session is likely inconsistent.
                    # We must force a full rollback to prevent 'own-write' visibility.
                    try:
                        self.session.rollback()
                    except Exception as rollback_err:
                        print(f"[UnitOfWork] Session rollback failed: {rollback_err}. Closing session.")
                        self.session.close()
            else:
                # Success -> Commit
                if not self.committed: 
                    if self.transaction:
                        self.transaction.commit()
                    else:
                        try:
                            self.session.commit()
                        except Exception as e:
                            self.session.rollback()
                            raise e
        finally:
            if self.owns_session:
                self.session.close()

class ActionDefinition(ABC):
    """
    The Base Class for Kinetic Actions.
    """
    
    @classmethod
    @abstractmethod
    def action_id(cls) -> str:
        """Unique Identifier (e.g., 'server.reboot')."""
        pass
        
    @abstractmethod
    def validate(self, ctx: ActionContext) -> bool:
        """
        Pure logic check.
        MUST NOT mutate state.
        Returns check result. Raise error for specific feedback.
        """
        pass

    @abstractmethod
    def apply(self, ctx: ActionContext):
        """
        Mutate state via ctx.manager (passing ctx.session).
        """
        pass

class ActionRunner:
    """
    Executes Actions within a UnitOfWork.
    """
    def __init__(self, manager: ObjectManager, session: Optional[Session] = None):
        self.manager = manager
        self.session_override = session

    
    def execute(self, action: ActionDefinition, ctx: ActionContext):
        # Inject Dependencies
        ctx.manager = self.manager
        ctx.session = self.session_override or self.manager.default_session
        
        print(f"[ActionRunner] Executing {action.action_id()} (Session ID: {id(ctx.session)})")

        # --- Phase 5: Audit Logging ---
        start_time = datetime.now()
        log_entry = OrionActionLog(
            action_type=action.action_id(),
            parameters=ctx.parameters,
            trace_id=ctx.job_id,
            status="PENDING",
            agent_id="Orion-Kernel" # Placeholder
        )

        try:
            # Lifecycle
            with UnitOfWork(self.manager, session=ctx.session):
                # 1. Validate
                if not action.validate(ctx):
                    raise ValueError(f"Validation Failed for {action.action_id()}")
                
                # 2. Apply
                action.apply(ctx)
                
                # 3. Commit handled by Context Manager __exit__
            
            log_entry.status = "SUCCESS"
            
        except Exception as e:
            log_entry.status = "FAILURE"
            log_entry.error = str(e)
            raise e
            
        finally:
            # Finalize Log Metadata
            end_time = datetime.now()
            log_entry.duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Persist Log
            self._persist_log(log_entry, ctx)

    def _persist_log(self, log_entry: OrionActionLog, ctx: ActionContext):
        """
        Persists the Audit Log.
        Handles the 'Dual-Transaction' requirement:
        - If Reality (Default Session): Use a FRESH session to ensure log survives rollback.
        - If Simulation: Log to the Sandbox (Ctx Session).
        """
        is_simulation = (ctx.session != self.manager.default_session) and (ctx.session is not None)
        
        if is_simulation:
            # In Simulation, we just save to the sandbox.
            # It will be captured in the diff and discarded on rollback.
            # This is correct behavior (don't pollute reality with sim logs).
            self.manager.save(log_entry, session=ctx.session)
        else:
            # In Reality, we MUST persist the log, even if the action failed.
            # We open a dedicated Audit Session.
            # In Reality, we MUST persist the log, even if the action failed.
            # We reuse the default session to avoid SQLite Locking contention (single writer).
            # Since we rolled back the business transaction, the session should be clean.
            try:
                # Force commit for the log
                self.manager.save(log_entry, session=self.manager.default_session, commit=True)
            except Exception as e:
                print(f"[ActionRunner] CRITICAL: Failed to write Audit Log! {e}")
