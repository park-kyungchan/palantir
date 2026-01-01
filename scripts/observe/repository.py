"""
Orion ODA V3 - Observability Repository
========================================
EventsRepository for hook event persistence.

Maps to IndyDevDan's Watchtower db.ts functions.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

from sqlalchemy import select, desc, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from scripts.observe.models import HookEvent

logger = logging.getLogger(__name__)


class EventsRepository:
    """
    Repository for HookEvent persistence and retrieval.
    
    Maps to IndyDevDan's db.ts functions:
        - insertEvent
        - getRecentEvents
        - getFilterOptions
        - updateEventHITLResponse
    
    Usage:
        repo = EventsRepository()
        await repo.save(event)
        events = await repo.get_recent(100)
    """
    
    # Connected WebSocket clients (for broadcasting)
    _ws_clients: Set[Any] = set()
    
    def __init__(self, db=None):
        self._db = db
    
    async def _get_db(self):
        """Lazy-load database."""
        if self._db is None:
            try:
                from scripts.ontology.storage.database import DatabaseManager
                self._db = DatabaseManager.get()
            except ImportError:
                from scripts.ontology.storage import get_database
                self._db = get_database()
        return self._db
    
    async def save(self, event: HookEvent) -> HookEvent:
        """
        Save a new event to the database.
        
        Maps to IndyDevDan's insertEvent().
        """
        db = await self._get_db()
        async with db.transaction() as session:
            session.add(event)
            await session.flush()
            await session.refresh(event)
        
        logger.debug(f"Saved event: {event.id} ({event.hook_event_type})")
        
        # Broadcast to WebSocket clients
        await self._broadcast(event)
        
        return event
    
    async def get_recent(self, limit: int = 300) -> List[HookEvent]:
        """
        Get most recent events.
        
        Maps to IndyDevDan's getRecentEvents().
        """
        db = await self._get_db()
        async with db.transaction() as session:
            stmt = (
                select(HookEvent)
                .order_by(desc(HookEvent.timestamp))
                .limit(limit)
            )
            result = await session.execute(stmt)
            events = result.scalars().all()
        
        # Reverse to chronological order
        return list(reversed(events))
    
    async def get_by_id(self, event_id: int) -> Optional[HookEvent]:
        """Get event by ID."""
        db = await self._get_db()
        async with db.transaction() as session:
            stmt = select(HookEvent).where(HookEvent.id == event_id)
            result = await session.execute(stmt)
            return result.scalar_one_or_none()
    
    async def get_filter_options(self) -> Dict[str, List[str]]:
        """
        Get available filter options (distinct values).
        
        Maps to IndyDevDan's getFilterOptions().
        """
        db = await self._get_db()
        async with db.transaction() as session:
            # Source apps
            stmt = select(distinct(HookEvent.source_app))
            result = await session.execute(stmt)
            source_apps = [r[0] for r in result.fetchall() if r[0]]
            
            # Session IDs (last N)
            stmt = (
                select(distinct(HookEvent.session_id))
                .order_by(desc(HookEvent.id))
                .limit(100)
            )
            result = await session.execute(stmt)
            session_ids = [r[0] for r in result.fetchall() if r[0]]
            
            # Event types
            stmt = select(distinct(HookEvent.hook_event_type))
            result = await session.execute(stmt)
            event_types = [r[0] for r in result.fetchall() if r[0]]
        
        return {
            "source_apps": source_apps,
            "session_ids": session_ids,
            "hook_event_types": event_types,
        }
    
    async def update_hitl_response(
        self,
        event_id: int,
        response: Dict[str, Any],
    ) -> Optional[HookEvent]:
        """
        Update human-in-the-loop response.
        
        Maps to IndyDevDan's updateEventHITLResponse().
        """
        db = await self._get_db()
        async with db.transaction() as session:
            stmt = select(HookEvent).where(HookEvent.id == event_id)
            result = await session.execute(stmt)
            event = result.scalar_one_or_none()
            
            if not event:
                return None
            
            event.hitl_status = "responded"
            event.human_in_the_loop = {
                **(event.human_in_the_loop or {}),
                "response": response,
                "responded_at": int(datetime.utcnow().timestamp() * 1000),
            }
            
            await session.flush()
            await session.refresh(event)
        
        # Broadcast update
        await self._broadcast(event)
        
        logger.info(f"Updated HITL response for event: {event_id}")
        return event
    
    async def search(
        self,
        source_app: str = None,
        session_id: str = None,
        event_type: str = None,
        limit: int = 100,
    ) -> List[HookEvent]:
        """Search events with filters."""
        db = await self._get_db()
        async with db.transaction() as session:
            stmt = select(HookEvent)
            
            if source_app:
                stmt = stmt.where(HookEvent.source_app == source_app)
            if session_id:
                stmt = stmt.where(HookEvent.session_id == session_id)
            if event_type:
                stmt = stmt.where(HookEvent.hook_event_type == event_type)
            
            stmt = stmt.order_by(desc(HookEvent.timestamp)).limit(limit)
            
            result = await session.execute(stmt)
            return list(result.scalars().all())
    
    @classmethod
    def register_client(cls, ws) -> None:
        """Register a WebSocket client for broadcasts."""
        cls._ws_clients.add(ws)
        logger.debug(f"WebSocket client registered. Total: {len(cls._ws_clients)}")
    
    @classmethod
    def unregister_client(cls, ws) -> None:
        """Unregister a WebSocket client."""
        cls._ws_clients.discard(ws)
        logger.debug(f"WebSocket client unregistered. Total: {len(cls._ws_clients)}")
    
    async def _broadcast(self, event: HookEvent) -> None:
        """Broadcast event to all connected WebSocket clients."""
        if not self._ws_clients:
            return
        
        message = json.dumps({
            "type": "event",
            "data": event.to_dict()
        })
        
        disconnected = set()
        for client in self._ws_clients:
            try:
                await client.send_text(message)
            except Exception:
                disconnected.add(client)
        
        # Clean up disconnected clients
        self._ws_clients -= disconnected
