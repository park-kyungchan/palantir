"""
Application Layer - Business Logic and Use Cases

This layer contains the application-specific business rules.
It orchestrates the flow of data to and from the domain entities,
and implements use cases like the Zone of Proximal Development (ZPD)
scoping engine.

Clean Architecture Principle: The application layer depends only
on the domain layer. It implements use cases that coordinate
domain entities to fulfill business requirements.
"""

from palantir_fde_learning.application.scoping import (
    MASTERY_THRESHOLD,
    OPTIMAL_STRETCH_MAX,
    OPTIMAL_STRETCH_MIN,
    ScopingEngine,
    ZPDRecommendation,
)

__all__ = [
    "OPTIMAL_STRETCH_MIN",
    "OPTIMAL_STRETCH_MAX",
    "MASTERY_THRESHOLD",
    "ScopingEngine",
    "ZPDRecommendation",
]
