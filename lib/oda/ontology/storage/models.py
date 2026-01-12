"""
Orion ODA V3 - ORM Models
==========================
SQLAlchemy 2.0 Declarative Models for all persisted domain objects.

Maps 1:1 with Pydantic domain objects in lib/oda/ontology/schemas/:
- ProposalModel -> Proposal
- OrionActionLogModel -> OrionActionLog
- JobResultModel -> JobResult
- OrionInsightModel -> OrionInsight
- OrionPatternModel -> OrionPattern
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy import String, JSON, DateTime, Text, Integer, Float, Index, Boolean
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
    @property
    def timestamp(self) -> datetime:
        """Alias for created_at (MCP compatibility)."""
        return self.created_at

    def __repr__(self):
        return f"<History(proposal={self.proposal_id}, action={self.action})>"


# =============================================================================
# ORION ACTION LOG MODEL
# =============================================================================

class OrionActionLogModel(AsyncOntologyObject):
    """
    SQLAlchemy Model for Action Audit Logs.
    Maps to: lib/oda/ontology/schemas/governance.py::OrionActionLog

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
    Maps to: lib/oda/ontology/schemas/result.py::JobResult

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
    Maps to: lib/oda/ontology/schemas/memory.py::OrionInsight

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
    Maps to: lib/oda/ontology/schemas/memory.py::OrionPattern

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


# =============================================================================
# LEARNING MODELS (PHASE 5)
# =============================================================================

class LearnerModel(AsyncOntologyObject):
    """
    SQLAlchemy Model for Learners.
    Maps to: lib/oda/ontology/objects/learning.py::Learner
    """
    __tablename__ = "learners"

    user_id: Mapped[str] = mapped_column(String, index=True, nullable=False, unique=True)
    theta: Mapped[float] = mapped_column(Float, default=0.0)
    knowledge_state: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)
    last_active: Mapped[str] = mapped_column(String, default="")
    
    def __repr__(self):
        return f"<Learner(id={self.id}, user_id={self.user_id}, theta={self.theta})>"


# =============================================================================
# DOMAIN MODELS (Task & Agent)
# =============================================================================

class AgentModel(AsyncOntologyObject):
    """
    SQLAlchemy Model for Agents.
    Maps to: lib/oda/ontology/objects/task_types.py::Agent
    """
    __tablename__ = "agents"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="agent")
    agent_active: Mapped[bool] = mapped_column(Boolean, default=True)
    capabilities: Mapped[List[str]] = mapped_column(JSON, default=list)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    def __repr__(self):
        return f"<Agent(id={self.id}, name={self.name})>"


class TaskModel(AsyncOntologyObject):
    """
    SQLAlchemy Model for Tasks.
    Maps to: lib/oda/ontology/objects/task_types.py::Task
    """
    __tablename__ = "tasks"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[str] = mapped_column(String(20), default="medium")
    task_status: Mapped[str] = mapped_column(String(20), default="pending")
    
    # FKs
    assigned_to_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    parent_task_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Metadata
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    due_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return f"<Task(id={self.id}, title={self.title}, status={self.task_status})>"


class TaskDependencyLinkModel(AsyncOntologyObject):
    """
    Backing datasource for MANY_TO_MANY "task_depends_on_task" relationship.
    Palantir Pattern: N:N links require explicit backing table.
    """
    __tablename__ = "task_dependencies"

    source_task_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    target_task_id: Mapped[str] = mapped_column(String, index=True, nullable=False)
    link_type: Mapped[str] = mapped_column(String, default="task_depends_on_task")

    __table_args__ = (
        Index('idx_task_deps_source', 'source_task_id'),
        Index('idx_task_deps_target', 'target_task_id'),
        Index('idx_task_deps_composite', 'source_task_id', 'target_task_id', unique=True),
    )

    def __repr__(self):
        return f"<TaskDependency({self.source_task_id} -> {self.target_task_id})>"


# =============================================================================
# RELAY MODELS (PHASE 3)
# =============================================================================

class RelayTaskModel(AsyncOntologyObject):
    """
    SQLAlchemy Model for Relay Queue Tasks.
    Replaces legacy relay.db SQLite table.
    """
    __tablename__ = "relay_tasks"

    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # We use the inherited 'status' field for: pending, processing, completed

    __table_args__ = (
        Index('idx_relay_status', 'status'),
    )

    def __repr__(self):
        return f"<RelayTask(id={self.id}, status={self.status})>"


# =============================================================================
# LINK MODELS (Phase 1.3 - Storage Integration)
# =============================================================================


class LinkModel(AsyncOntologyObject):
    """
    Generic SQLAlchemy Model for storing Link instances.

    This model stores individual link records for 1:1, 1:N, and N:1 relationships.
    For N:N relationships, use the specialized JoinTableModel or dynamically
    generated join tables.

    Palantir Pattern:
    - Links are first-class persisted entities
    - Each link has a link_type_id reference
    - Supports soft-delete for audit trail

    Attributes:
        link_type_id: Reference to LinkTypeMetadata.link_type_id
        source_type: ObjectType name of the source object
        source_id: Primary key of the source object
        target_type: ObjectType name of the target object
        target_id: Primary key of the target object
        metadata: Optional JSON metadata for the link
    """
    __tablename__ = "links"

    # Link Type Reference
    link_type_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Reference to LinkTypeMetadata.link_type_id"
    )

    # Source Object Reference
    source_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="ObjectType name of the source object"
    )
    source_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
        comment="Primary key of the source object"
    )

    # Target Object Reference
    target_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="ObjectType name of the target object"
    )
    target_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
        index=True,
        comment="Primary key of the target object"
    )

    # Optional Metadata (for link attributes)
    # Note: "metadata" is reserved in SQLAlchemy, so we use "link_metadata"
    link_metadata: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        default=dict,
        comment="Optional JSON metadata for the link"
    )

    # Audit timestamp for link creation
    linked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(),
        nullable=False,
        comment="When the link was established"
    )

    # Who created the link
    linked_by: Mapped[Optional[str]] = mapped_column(
        String,
        nullable=True,
        comment="ID of actor who created the link"
    )

    __table_args__ = (
        # Composite index for source lookup
        Index('idx_link_source', 'link_type_id', 'source_id'),
        # Composite index for target lookup (reverse navigation)
        Index('idx_link_target', 'link_type_id', 'target_id'),
        # Unique constraint to prevent duplicate links
        Index(
            'idx_link_unique',
            'link_type_id', 'source_id', 'target_id',
            unique=True
        ),
        # Index for type-based queries
        Index('idx_link_types', 'source_type', 'target_type'),
    )

    def __repr__(self) -> str:
        return (
            f"<Link({self.link_type_id}: "
            f"{self.source_type}:{self.source_id} -> "
            f"{self.target_type}:{self.target_id})>"
        )


class LinkTypeRegistryModel(AsyncOntologyObject):
    """
    SQLAlchemy Model for persisting LinkType definitions.

    Stores LinkTypeMetadata in the database for:
    - Schema introspection
    - Runtime link type resolution
    - Schema versioning and migration

    Palantir Pattern:
    - LinkTypes are registered in a central registry
    - Schema changes are versioned
    """
    __tablename__ = "link_type_registry"

    # Identity
    link_type_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique link type identifier"
    )

    # ObjectType References
    source_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationship Properties
    cardinality: Mapped[str] = mapped_column(
        String(10),
        default="1:N",
        nullable=False
    )
    direction: Mapped[str] = mapped_column(
        String(20),
        default="directed",
        nullable=False
    )
    reverse_link_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Storage Configuration
    backing_table_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_materialized: Mapped[bool] = mapped_column(Boolean, default=True)

    # Cascade Policies
    on_source_delete: Mapped[str] = mapped_column(String(20), default="cascade")
    on_target_delete: Mapped[str] = mapped_column(String(20), default="set_null")
    on_source_update: Mapped[str] = mapped_column(String(20), default="cascade")
    on_target_update: Mapped[str] = mapped_column(String(20), default="cascade")

    # Constraints (JSON for flexibility)
    constraints: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict)

    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tags: Mapped[List[str]] = mapped_column(JSON, default=list)

    # Schema Version
    schema_version: Mapped[str] = mapped_column(String(20), default="1.0.0")

    __table_args__ = (
        Index('idx_ltr_source', 'source_type'),
        Index('idx_ltr_target', 'target_type'),
        Index('idx_ltr_cardinality', 'cardinality'),
    )

    def __repr__(self) -> str:
        return (
            f"<LinkTypeRegistry({self.link_type_id}: "
            f"{self.source_type} --[{self.cardinality}]--> {self.target_type})>"
        )
