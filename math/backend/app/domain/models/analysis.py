from pydantic import BaseModel, Field
from typing import List

class NumberAnalysis(BaseModel):
    number: int = Field(..., ge=1, description="The analyzed number")
    is_prime: bool = Field(..., description="Whether the number is prime")
    factors: List[int] = Field(default_factory=list, description="List of prime factors")
