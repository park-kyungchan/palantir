"""
Orion ODA V3 - Observability Server
====================================
FastAPI server with WebSocket for real-time events.

Maps to IndyDevDan's Watchtower server/src/index.ts.

Run with:
    python -m scripts.observe.server
"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from lib.oda.observe.repository import EventsRepository
from lib.oda.observe.models import HookEvent

logger = logging.getLogger(__name__)


# ==============================================================================
# Pydantic Models
# ==============================================================================

class HookEventCreate(BaseModel):
    """Request model for creating a hook event."""
    source_app: str
    session_id: str
    hook_event_type: str
    payload: dict
    chat: Optional[dict] = None
    summary: Optional[str] = None
    timestamp: Optional[int] = None
    human_in_the_loop: Optional[dict] = None
    model_name: Optional[str] = None


class HITLResponse(BaseModel):
    """Request model for HITL response."""
    decision: str  # "approve" | "reject" | "modify"
    comment: Optional[str] = None
    modifications: Optional[dict] = None


class EventResponse(BaseModel):
    """Response model for an event."""
    id: int
    source_app: str
    session_id: str
    hook_event_type: str
    payload: dict
    chat: Optional[dict]
    summary: Optional[str]
    timestamp: int
    human_in_the_loop: Optional[dict]
    hitl_status: Optional[str]
    model_name: Optional[str]
    created_at: Optional[str]


# ==============================================================================
# FastAPI App
# ==============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context for startup/shutdown."""
    logger.info("🚀 Orion Observability Server starting...")
    yield
    logger.info("👋 Orion Observability Server shutting down...")


app = FastAPI(
    title="Orion Observability Server",
    description="Real-time agent activity monitoring (Watchtower)",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Repository instance
repo = EventsRepository()


# ==============================================================================
# HTTP Endpoints
# ==============================================================================

@app.get("/")
async def root():
    """Health check."""
    return {
        "status": "ok",
        "service": "orion-observe",
        "version": "1.0.0",
    }


@app.post("/events")
async def receive_event(event_data: HookEventCreate):
    """
    Receive new hook event.
    
    POST /events - Maps to IndyDevDan's POST /events endpoint.
    """
    event = HookEvent(
        source_app=event_data.source_app,
        session_id=event_data.session_id,
        hook_event_type=event_data.hook_event_type,
        payload=event_data.payload,
        chat=event_data.chat,
        summary=event_data.summary,
        timestamp=event_data.timestamp or int(time.time() * 1000),
        human_in_the_loop=event_data.human_in_the_loop,
        model_name=event_data.model_name,
    )
    
    saved = await repo.save(event)
    return saved.to_dict()


@app.get("/events/recent")
async def get_recent_events(limit: int = 300):
    """
    Get recent events.
    
    GET /events/recent - Maps to IndyDevDan's GET /events/recent endpoint.
    """
    events = await repo.get_recent(limit)
    return [e.to_dict() for e in events]


@app.get("/events/filter-options")
async def get_filter_options():
    """
    Get available filter options.
    
    GET /events/filter-options - Maps to IndyDevDan's GET /events/filter-options.
    """
    return await repo.get_filter_options()


@app.get("/events/{event_id}")
async def get_event(event_id: int):
    """Get a specific event by ID."""
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event.to_dict()


@app.post("/events/{event_id}/respond")
async def respond_to_hitl(event_id: int, response: HITLResponse):
    """
    Respond to a human-in-the-loop request.
    
    POST /events/:id/respond - Maps to IndyDevDan's /events/:id/respond.
    """
    updated = await repo.update_hitl_response(event_id, response.model_dump())
    if not updated:
        raise HTTPException(status_code=404, detail="Event not found")
    return updated.to_dict()


@app.get("/events/search")
async def search_events(
    source_app: Optional[str] = None,
    session_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
):
    """Search events with filters."""
    events = await repo.search(
        source_app=source_app,
        session_id=session_id,
        event_type=event_type,
        limit=limit,
    )
    return [e.to_dict() for e in events]


# ==============================================================================
# WebSocket Endpoint
# ==============================================================================

@app.websocket("/stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket stream for real-time events.
    
    ws://host/stream - Maps to IndyDevDan's /stream WebSocket endpoint.
    """
    await websocket.accept()
    EventsRepository.register_client(websocket)
    
    logger.info("WebSocket client connected")
    
    try:
        # Send initial events
        events = await repo.get_recent(100)
        await websocket.send_json({
            "type": "initial",
            "data": [e.to_dict() for e in events]
        })
        
        # Keep connection alive
        while True:
            try:
                # Wait for client message or timeout
                await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )
            except asyncio.TimeoutError:
                # Send ping to keep alive
                await websocket.send_json({"type": "ping"})
    
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        EventsRepository.unregister_client(websocket)


# ==============================================================================
# Entry Point
# ==============================================================================

def run_server(host: str = "0.0.0.0", port: int = 4000):
    """Run the observability server."""
    import uvicorn
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    run_server()
