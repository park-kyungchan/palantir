
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type
from pydantic import BaseModel
from sqlalchemy.orm import Session
from scripts.ontology.manager import ObjectManager, OrionObject

# --- Phase 2: Action Definition ---

class ActionContext(BaseModel):
    """Context for a single action execution."""
    job_id: str
    parameters: Dict[str, Any]
    # Transient runtime state
    manager: Optional[Any] = None # Injected at runtime (ObjectManager)
    session: Optional[Any] = None # Injected at runtime (SQLAlchemy Session)
    
    class Config:
        arbitrary_types_allowed = True

class ActionDefinition(ABC):
    """
    Abstract Base Class for all Kinetic Actions.
    Enforces the Validate -> Apply lifecycle.
    """
    
    @classmethod
    @abstractmethod
    def action_id(cls) -> str:
        """Unique Identifier (e.g., 'server.restart')."""
        pass
    
    @abstractmethod
    def validate(self, ctx: ActionContext) -> bool:
        """
        Pure Logic Check.
        Returns True if action CAN proceed.
        Raises ValueError or returns False if not.
        """
        pass

    @abstractmethod
    def apply(self, ctx: ActionContext):
        """
        State Mutation.
        Modifies OrionObjects in memory/session.
        Does NOT commit directly.
        """
        pass

    def describe_side_effects(self, ctx: ActionContext) -> List[str]:
        """Optional description of external effects."""
        return []

# --- Phase 2: Transaction Management ---

class UnitOfWork:
    """
    Atomic Wrapper for Action Execution.
    Manages the Transaction Lifecycle:
    Evaluate -> Flush -> Commit (success) or Rollback (failure).
    """
    def __init__(self, manager: ObjectManager, session: Optional[Session] = None):
        self.manager = manager
        # If session is injected (e.g. from Simulation), use it.
        # Otherwise, create a new one.
        if session:
            self.session = session
            self.owns_session = False
        else:
            self.session = manager.default_session # Or manager.create_session() if we wanted new connections per action
            # Actually, manager.default_session is shared. We might want a dedicated session for true isolation?
            # For now, let's use default_session but begin_nested() if we wanted internal savepoints.
            # But standard UoW usually implies a full transaction.
            # Let's assume we use the manager's active session mechanism.
            self.owns_session = False # We don't close manager's session usually.

    def __enter__(self):
        # We might want to start a SAVEPOINT if we are already in a transaction?
        # Use begin_nested() just in case to allow recursive actions or simulation wrapping.
        # This is CRITICAL for Phase 3 Simulation.
        if self.session.in_transaction():
             self.transaction = self.session.begin_nested()
        else:
             self.transaction = self.session.begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            # Failure
            print(f"[UnitOfWork] Exception detected: {exc_val}. Rolling back...")
            self.transaction.rollback()
            # Propagate exception
            return False
            
        # Success path
        try:
            self.transaction.commit()
            # Note: Commit releases the savepoint or the transaction.
        except Exception as e:
            print(f"[UnitOfWork] Commit failed: {e}")
            self.transaction.rollback()
            raise e
        finally:
            if self.owns_session:
                self.session.close()

class ActionRunner:
    """
    The Engine that runs Actions.
    """
    def __init__(self, manager: ObjectManager, session: Optional[Session] = None):
        self.manager = manager
        self.session = session # Injected session for Simulation

    def execute(self, action: ActionDefinition, ctx: ActionContext):
        # Inject Dependencies
        ctx.manager = self.manager
        ctx.session = self.session or self.manager.default_session
        
        print(f"[ActionRunner] Executing {action.action_id()} (Session ID: {id(ctx.session)})")

        # Lifecycle
        with UnitOfWork(self.manager, session=ctx.session):
            # 1. Validate
            if not action.validate(ctx):
                raise ValueError(f"Validation Failed for {action.action_id()}")
            
            # 2. Apply
            action.apply(ctx)
            
            # 3. Commit handled by Context Manager __exit__
