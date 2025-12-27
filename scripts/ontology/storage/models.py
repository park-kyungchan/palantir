"""
Orion ODA V3 - ORM Models
==========================
SQLAlchemy 2.0 Declarative Models for all persisted domain objects.

Maps 1:1 with Pydantic domain objects in scripts/ontology/schemas/:
- ProposalModel -> Proposal
- OrionActionLogModel -> OrionActionLog
- JobResultModel -> JobResult
- OrionInsightModel -> OrionInsight
- OrionPatternModel -> OrionPattern
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy import String, JSON, DateTime, Text, Integer, Float, Index
from sqlalchemy.orm import Mapped, mapped_column

from .orm import AsyncOntologyObject, Base

class ProposalModel(AsyncOntologyObject):
    """
    SQLAlchemy Model for Proposals.
    Maps 1:1 with scripts.ontology.objects.proposal.Proposal
    """
    __tablename__ = "proposals"

    # Core Action Data
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)  # Stores job parameters
    priority: Mapped[str] = mapped_column(String, default="medium")
    
    # Review Audit Data
    reviewed_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Execution Audit Data (for traceability)
    executor_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    def __repr__(self):
        return f"<Proposal(id={self.id}, action={self.action_type}, status={self.status}, v={self.version})>"

class ProposalHistoryModel(AsyncOntologyObject):
    """
    Audit Log for Proposal changes.
    """
    __tablename__ = "proposal_history"

    proposal_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False) # created, updated, approved, etc
    actor_id: Mapped[str] = mapped_column(String, nullable=False)
    comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    previous_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    new_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # We use created_at from AsyncOntologyObject as the timestamp

    def __repr__(self):
        return f"<History(proposal={self.proposal_id}, action={self.action})>"


# =============================================================================
# ORION ACTION LOG MODEL
# =============================================================================

class OrionActionLogModel(AsyncOntologyObject):
    """
    SQLAlchemy Model for Action Audit Logs.
    Maps to: scripts/ontology/schemas/governance.py::OrionActionLog

    Stores immutable audit records for all kinetic actions executed.
    """
    __tablename__ = "action_logs"

    # Context
    agent_id: Mapped[str] = mapped_column(String(255), default="Orion-Kernel", nullable=False)
    trace_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Intent
    action_type: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    parameters: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Outcome
    # Note: 'status' is inherited from AsyncOntologyObject, used for SUCCESS/FAILURE/ROLLED_BACK
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Impact
    affected_ids: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Meta
    duration_ms: Mapped[int] = mapped_column(Integer, default=0)

    # Full-Text Search
    fts_content: Mapped[str] = mapped_column(Text, default="")

    __table_args__ = (
        Index('idx_alog_type_status', 'action_type', 'status'),
        Index('idx_alog_agent_created', 'agent_id', 'created_at'),
    )

    def __repr__(self):
        return f"<ActionLog(id={self.id}, type={self.action_type}, status={self.status})>"


# =============================================================================
# JOB RESULT MODEL
# =============================================================================

class JobResultModel(AsyncOntologyObject):
    """
    SQLAlchemy Model for Job Results.
    Maps to: scripts/ontology/schemas/result.py::JobResult

    Stores formal output contracts from external agent execution.
    """
    __tablename__ = "job_results"

    # Core
    job_id: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    # Note: 'status' inherited from base, used for SUCCESS/FAILURE/BLOCKED

    # Outputs (JSON arrays/objects)
    output_artifacts: Mapped[List[Dict[str, Any]]] = mapped_column(JSON, default=list)
    metrics: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Full-Text Search
    fts_content: Mapped[str] = mapped_column(Text, default="")

    def __repr__(self):
        return f"<JobResult(id={self.id}, job_id={self.job_id}, status={self.status})>"


# =============================================================================
# ORION INSIGHT MODEL
# =============================================================================

class OrionInsightModel(AsyncOntologyObject):
    """
    SQLAlchemy Model for Insights (Declarative Knowledge).
    Maps to: scripts/ontology/schemas/memory.py::OrionInsight

    Stores atomic units of learned knowledge with confidence scoring.
    """
    __tablename__ = "insights"

    # Core Content
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    domain: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Confidence & Decay
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0)
    decay_factor: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Provenance
    source_episodic_ids: Mapped[List[str]] = mapped_column(JSON, default=list)
    provenance_method: Mapped[str] = mapped_column(String(100), default="unknown")

    # Relations (flattened)
    supports: Mapped[List[str]] = mapped_column(JSON, default=list)
    contradicts: Mapped[List[str]] = mapped_column(JSON, default=list)
    related_to: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Full-Text Search
    fts_content: Mapped[str] = mapped_column(Text, default="")

    __table_args__ = (
        Index('idx_insight_domain_confidence', 'domain', 'confidence_score'),
    )

    def __repr__(self):
        return f"<Insight(id={self.id}, domain={self.domain}, confidence={self.confidence_score})>"


# =============================================================================
# ORION PATTERN MODEL
# =============================================================================

class OrionPatternModel(AsyncOntologyObject):
    """
    SQLAlchemy Model for Patterns (Procedural Knowledge).
    Maps to: scripts/ontology/schemas/memory.py::OrionPattern

    Stores reusable procedural workflows learned from execution history.
    """
    __tablename__ = "patterns"

    # Structure
    trigger: Mapped[str] = mapped_column(Text, nullable=False)
    steps: Mapped[List[str]] = mapped_column(JSON, default=list)
    anti_patterns: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Usage Metrics
    frequency_count: Mapped[int] = mapped_column(Integer, default=0)
    success_rate: Mapped[float] = mapped_column(Float, default=0.0)
    last_used: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Reference
    code_snippet_ref: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Full-Text Search
    fts_content: Mapped[str] = mapped_column(Text, default="")

    __table_args__ = (
        Index('idx_pattern_frequency', 'frequency_count'),
        Index('idx_pattern_success', 'success_rate'),
    )

    def __repr__(self):
        return f"<Pattern(id={self.id}, freq={self.frequency_count}, success={self.success_rate})>"
