
from typing import Optional
from datetime import datetime
from sqlalchemy import String, JSON, DateTime
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
