from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from scripts.ontology.ontology_types import OrionObject

class Artifact(BaseModel):
    """
    Represents a tangible output produced by a Job.
    """
    path: str = Field(..., description="Absolute path to the artifact")
    description: str = Field(..., description="Description of what this artifact is")
    mime_type: Optional[str] = Field(None, description="MIME type if known")
    checksum: Optional[str] = Field(None, description="Optional SHA256 checksum for integrity")

class JobResult(OrionObject):
    """
    Formal contract for returning work from an external agent back to the Ontology.
    Captured via 'result_job_{id}.py'.
    """
    job_id: str = Field(..., description="The ID of the Job this result belongs to")
    status: Literal["SUCCESS", "FAILURE", "BLOCKED"] = Field(..., description="Execution Status")
    output_artifacts: List[Artifact] = Field(default_factory=list, description="List of files produced")
    metrics: Dict[str, Any] = Field(default_factory=dict, description="Quantitative results (e.g. coverage, latency)")
    # 'evidence' or 'reasoning' could also be added, but relying on base fields for now.
    
    # We can add methods helper methods here if needed, but keeping it data-centric.
