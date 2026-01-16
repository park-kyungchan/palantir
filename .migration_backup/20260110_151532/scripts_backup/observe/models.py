"""
Orion ODA V3 - Observability Models
====================================
SQLAlchemy models for hook events.

Maps to IndyDevDan's Watchtower db.ts schema.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.orm import declarative_base

logger = logging.getLogger(__name__)

Base = declarative_base()


class HookEvent(Base):
    """
    Hook event model for observability.
    
    Maps to IndyDevDan's Watchtower events table.
    
    Stores all hook events:
        - PreToolUse
        - PostToolUse
        - SubagentStop
        - Custom events
    """
    
    __tablename__ = "observe_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    source_app = Column(String(100), nullable=False, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    hook_event_type = Column(String(50), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    chat = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    timestamp = Column(Integer, nullable=False, index=True)
    human_in_the_loop = Column(JSON, nullable=True)
    hitl_status = Column(String(20), nullable=True)  # pending, responded
    model_name = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response."""
        return {
            "id": self.id,
            "source_app": self.source_app,
            "session_id": self.session_id,
            "hook_event_type": self.hook_event_type,
            "payload": self.payload,
            "chat": self.chat,
            "summary": self.summary,
            "timestamp": self.timestamp,
            "human_in_the_loop": self.human_in_the_loop,
            "hitl_status": self.hitl_status,
            "model_name": self.model_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HookEvent":
        """Create from dictionary."""
        return cls(
            source_app=data["source_app"],
            session_id=data["session_id"],
            hook_event_type=data["hook_event_type"],
            payload=data["payload"],
            chat=data.get("chat"),
            summary=data.get("summary"),
            timestamp=data.get("timestamp", int(datetime.now(timezone.utc).timestamp() * 1000)),
            human_in_the_loop=data.get("human_in_the_loop"),
            hitl_status=data.get("hitl_status"),
            model_name=data.get("model_name"),
        )
    
    def __repr__(self) -> str:
        return (
            f"<HookEvent(id={self.id}, "
            f"type={self.hook_event_type}, "
            f"source={self.source_app})>"
        )
