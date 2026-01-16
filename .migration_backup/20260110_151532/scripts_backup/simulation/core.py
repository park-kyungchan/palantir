from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from scripts.infrastructure.event_bus import EventBus, DomainEvent
from scripts.ontology.actions import ActionType, ActionContext, ActionResult
from scripts.ontology.storage.database import Database, get_database
from scripts.ontology.storage.repositories import ActionLogRepository
from scripts.ontology.schemas.governance import OrionActionLog

logger = logging.getLogger(__name__)

# =============================================================================
# ASYNC UNIT OF WORK
# =============================================================================

class UnitOfWork:
    """
    Manages the Async Transaction Lifecycle.
    """
    def __init__(self, db: Database, session: Optional[AsyncSession] = None):
        self.db = db
        self.session = session
        self.transaction = None
        self._owns_session = False

    async def __aenter__(self) -> AsyncSession:
        if self.session:
            # Join existing session (Nested Transaction if needed?)
            # For ODA, we trust the passed session is active.
            # We can create a nested transaction (savepoint) for safety.
            self.transaction = await self.session.begin_nested()
            return self.session
        else:
            # Create new session scope
            self.ctx = self.db.transaction()
            self.session = await self.ctx.__aenter__()
            self._owns_session = True
            return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type:
                # Exception -> Rollback
                if self.transaction:
                    await self.transaction.rollback()
                # If we own the session, transaction() context handles rollback
            else:
                # Success -> Commit
                if self.transaction:
                    await self.transaction.commit()
                # If we own the session, transaction() context handles commit
        finally:
            if self._owns_session:
                await self.ctx.__aexit__(exc_type, exc_val, exc_tb)

# =============================================================================
# ACTION RUNNER (ASYNC)
# =============================================================================

class ActionRunner:
    """
    Executes ODA ActionTypes within an Async UnitOfWork.
    Persists Audit Logs via ActionLogRepository.
    """
    def __init__(self, db: Optional[Database] = None, session: Optional[AsyncSession] = None):
        self.db = db or get_database()
        self.session_override = session
        self.log_repo = ActionLogRepository(self.db)

    async def execute(self, action: ActionType, ctx: ActionContext) -> ActionResult:
        # Inject Dependencies via Metadata
        # We inject the session into metadata so actions can use it (Dependency Injection)
        
        # Phase 5: Audit Logging
        start_time = datetime.now(timezone.utc)
        trace_id = getattr(ctx, "job_id", ctx.correlation_id)
        
        log_entry = OrionActionLog(
            action_type=getattr(action, "api_name", "unknown"),
            parameters=getattr(ctx, "parameters", ctx.metadata.get("params", {})),
            trace_id=trace_id,
            status="PENDING",
            agent_id=ctx.actor_id or "Orion-Kernel",
            created_at=start_time,
            updated_at=start_time
        )
        
        # Persist PENDING state (optional, can skip for perf)
        # await self.log_repo.save(log_entry) 

        try:
            # Lifecycle
            async with UnitOfWork(self.db, session=self.session_override) as session:
                # Publish valid session for Action usage
                ctx.metadata["session"] = session
                
                # 1. Validate
                # Construct params from ctx.parameters (legacy) or metadata
                params = getattr(ctx, "parameters", ctx.metadata.get("params", {}))
                
                errors = action.validate(params, ctx)
                if errors:
                    raise ValueError(f"Validation Failed for {action.api_name}: {errors}")
                
                # 2. Apply
                rv = await action.apply_edits(params, ctx)
                
                if isinstance(rv, ActionResult):
                    final_result = rv
                else:
                    # Legacy Tuple Return (T, List[EditOperation])
                    result_obj, edits = rv
                    final_result = ActionResult(
                        action_type=getattr(action, "api_name", "unknown"),
                        success=True,
                        data=result_obj,
                        edits=edits if edits else []
                    )
            
            # Commit handled by UnitOfWork
            log_entry.status = "SUCCESS"
            return final_result
            
        except Exception as e:
            log_entry.status = "FAILURE"
            log_entry.error = str(e)
            raise e
            
        finally:
            end_time = datetime.now(timezone.utc)
            log_entry.duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Persist Log (Best Effort)
            try:
                # If we are in a simulation (session_override), we log to that session?
                # Or do we log to the main DB?
                # Usually logs go to main DB, but in simulation we might want to capture them in sandbox.
                # If session_override is set, we use it (Sandbox).
                # Note: ActionLogRepository handles session logic.
                
                # We create a NEW transaction for logging if not in sandbox, 
                # to ensure logs are written even if action failed?
                # But if action failed, UoW rolled back.
                # We need an independent transaction for the log.
                
                if self.session_override:
                    await self.log_repo.save(log_entry, actor_id=ctx.actor_id)
                else:
                    # Independent save
                    await self.log_repo.save(log_entry, actor_id=ctx.actor_id)
                    
            except Exception as log_err:
                logger.error(f"Failed to persist ActionLog: {log_err}")

# =============================================================================
# SIMULATION ENGINE
# =============================================================================

class SimulationDiff(BaseModel):
    created: List[Dict[str, Any]] = Field(default_factory=list)
    updated: List[Dict[str, Any]] = Field(default_factory=list)
    deleted: List[str] = Field(default_factory=list)

class ScenarioFork:
    """
    The Phase 3 Sandbox (Async).
    Wraps execution in a strict NESTED TRANSACTION (Savepoint) that is ALWAYS rolled back.
    Captures changes via EventBus.
    """
    def __init__(self, db: Database):
        self.db = db
        self.session = None
        self._diff = SimulationDiff()
        self._unsubscribe = None
        
    async def __aenter__(self) -> AsyncSession:
        # 1. Create independent session
        self.ctx = self.db.transaction() # This commits on exit...
        # Wait, we want to ROLLBACK.
        # So we shouldn't use db.transaction() which acts as UoW.
        # We need raw connection or begin() and explicit rollback.
        
        # Correct approach:
        # self.session = self.db.session_factory()
        # await self.session.begin()
        
        # But we want to reuse Database logic.
        self.session = self.db.session_factory()
        await self.session.begin() # Start transaction
        
        # 2. Hook into EventBus
        self._unsubscribe = EventBus.get_instance().subscribe("*", self._capture_event)
        
        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 3. Cleanup: Unsubscribe
        if self._unsubscribe:
            self._unsubscribe()
        
        # 4. ROLLBACK everything
        await self.session.rollback()
        await self.session.close()
        
    def _capture_event(self, event: DomainEvent):
        """
        Listener for EventBus events.
        """
        if event.entity_type == "OrionActionLog":
            return

        payload = event.payload
        # Extract ID and changes
        # Refactor: Payload is the domain object
        if hasattr(payload, "id"):
            obj_id = payload.id
            obj_type = payload.__class__.__name__
            
            if "saved" in event.event_type or "updated" in event.event_type:
                # Capture snapshot
                changes = payload.model_dump(mode='json') if hasattr(payload, 'model_dump') else str(payload)
                self._diff.updated.append({
                    "id": obj_id,
                    "type": obj_type,
                    "changes": changes,
                    "event": event.event_type
                })
            elif "deleted" in event.event_type:
                self._diff.deleted.append(obj_id)

    def get_diff(self) -> SimulationDiff:
        return self._diff

class SimulationEngine:
    """
    Orchestrates the 'What-If'.
    """
    def __init__(self, db: Database):
        self.db = db
        
    async def run_simulation(self, actions: List[ActionType], contexts: List[ActionContext]) -> SimulationDiff:
        logger.info("[SimulationEngine] Starting Scenario Fork...")
        
        fork = ScenarioFork(self.db)
        
        try:
            async with fork as sandbox_session:
                # Configure Runner with Sandbox Session
                runner = ActionRunner(self.db, session=sandbox_session)
                
                for action, ctx in zip(actions, contexts):
                    try:
                        await runner.execute(action, ctx)
                    except Exception as e:
                        logger.error(f"[SimulationEngine] Action Failed: {e}")
                        break
            
            return fork.get_diff()
            
        except Exception as e:
            logger.error(f"[SimulationEngine] Fork Crashed: {e}")
            return SimulationDiff()
