"""
ODA Storage - SQLAlchemy ORM Models
==================================

This module defines the minimal SQLite persistence schema needed by the ODA
runtime and test suite. It intentionally keeps JSON-ish fields as TEXT to avoid
SQLite JSON1 coupling; repositories handle json (de)serialization.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Float, text
from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class MigrationModel(Base):
    __tablename__ = "_migrations"

    name: Mapped[str] = mapped_column(String(255), primary_key=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ProposalModel(Base):
    __tablename__ = "proposals"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)

    action_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    payload: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'{}'"))

    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_result: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    tags: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'[]'"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))


class ProposalHistoryModel(Base):
    __tablename__ = "proposal_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    proposal_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    previous_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    new_status: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class OrionInsightModel(Base):
    __tablename__ = "insights"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("1.0"))
    decay_factor: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    provenance: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'{}'"))
    content: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'{}'"))
    supports: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'[]'"))
    contradicts: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'[]'"))
    related_to: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'[]'"))

    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))


class OrionPatternModel(Base):
    __tablename__ = "patterns"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    frequency_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    success_rate: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("0.0"))
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    structure: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'{}'"))
    code_snippet_ref: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))


class OrionActionLogModel(Base):
    __tablename__ = "action_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    trace_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    action_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    parameters: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'{}'"))

    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    affected_ids: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'[]'"))
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class JobResultModel(Base):
    __tablename__ = "job_results"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    job_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)

    output_artifacts: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'[]'"))
    metrics: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'{}'"))

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LearnerModel(Base):
    __tablename__ = "learners"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    theta: Mapped[float] = mapped_column(Float, nullable=False, server_default=text("0.0"))
    knowledge_state: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'{}'"))
    last_active: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))

    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'active'"))
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))


class TaskModel(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)

    title: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"), index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))

    priority: Mapped[str] = mapped_column(String(32), nullable=False, server_default=text("'medium'"))
    task_status: Mapped[str] = mapped_column(String(32), nullable=False, index=True, server_default=text("'pending'"))

    assigned_to_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    parent_task_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    tags: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("'[]'"))
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True, server_default=text("'active'"))
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))


class AgentModel(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)

    name: Mapped[str] = mapped_column(String(255), nullable=False, server_default=text("''"))
    agent_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True, server_default=text("'active'"))
    created_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    updated_by: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("1"))


__all__ = [
    "Base",
    "MigrationModel",
    "ProposalModel",
    "ProposalHistoryModel",
    "OrionInsightModel",
    "OrionPatternModel",
    "OrionActionLogModel",
    "JobResultModel",
    "LearnerModel",
    "TaskModel",
    "AgentModel",
]
