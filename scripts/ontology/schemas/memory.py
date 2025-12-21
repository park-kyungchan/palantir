
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from scripts.ontology.ontology_types import OrionObject

# --- INSIGHT ---

class InsightContent(BaseModel):
    summary: str
    domain: str
    tags: List[str] = Field(default_factory=list)

class InsightProvenance(BaseModel):
    source_episodic_ids: List[str] = Field(default_factory=list)
    method: str

class OrionInsight(OrionObject):
    """
    An atomic unit of declarative knowledge.
    Replaces legacy JSON schema.
    """
    confidence_score: float = Field(1.0, ge=0.0, le=1.0)
    decay_factor: Optional[float] = None
    
    provenance: InsightProvenance
    content: InsightContent
    
    # Relations flattened from legacy 'relations' object
    supports: List[str] = Field(default_factory=list)
    contradicts: List[str] = Field(default_factory=list)
    related_to: List[str] = Field(default_factory=list)

    def get_searchable_text(self) -> str:
        """Override for better semantic search."""
        return f"{self.content.summary} {self.content.domain} {' '.join(self.content.tags)}"

# --- PATTERN ---

class PatternStructure(BaseModel):
    trigger: str
    steps: List[str]
    anti_patterns: List[str] = Field(default_factory=list)

class OrionPattern(OrionObject):
    """
    A reusable procedural workflow.
    Replaces legacy JSON schema.
    """
    frequency_count: int = 0
    success_rate: float = Field(0.0, ge=0.0, le=1.0)
    last_used: Optional[datetime] = None
    
    structure: PatternStructure
    code_snippet_ref: Optional[str] = None
    
    def get_searchable_text(self) -> str:
        """Override for better semantic search."""
        return f"{self.structure.trigger} {' '.join(self.structure.steps)}"
