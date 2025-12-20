
from sqlalchemy import String, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from .orm import AsyncOntologyObject

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
