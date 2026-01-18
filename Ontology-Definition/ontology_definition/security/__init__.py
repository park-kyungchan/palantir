"""
Security module - Row-level security and access control definitions.

Exports:
    - RestrictedViewPolicy: Row-level security policy (GAP-001 P1-CRITICAL)
    - PolicyTerm: Individual access condition
    - LogicalOperator: AND/OR for combining terms
    - ComparisonOperator: EQUALS, CONTAINS, IN, NOT_IN
    - UserAttributeMapping: User attribute extraction config
    - CommonRestrictedViewPolicies: Factory for common patterns
    - AccessLevel: Property access levels (FULL, READ_ONLY, MASKED, HIDDEN)
    - SecurityConfig: Combined security configuration
    - ObjectSecurityPolicy: Row-level security policy wrapper
    - PropertySecurityPolicy: Column-level security policy
"""

from ontology_definition.core.enums import AccessLevel
from ontology_definition.security.restricted_view import (
    CommonRestrictedViewPolicies,
    ComparisonOperator,
    IdentifierType,
    LogicalOperator,
    PolicyTerm,
    PolicyTermType,
    RestrictedViewPolicy,
    UserAttributeMapping,
)
from ontology_definition.types.object_type import (
    ObjectSecurityPolicy,
    PropertySecurityPolicy,
    SecurityConfig,
)

__all__ = [
    # RestrictedViewPolicy (GAP-001)
    "RestrictedViewPolicy",
    "PolicyTerm",
    "PolicyTermType",
    "LogicalOperator",
    "ComparisonOperator",
    "IdentifierType",
    "UserAttributeMapping",
    "CommonRestrictedViewPolicies",
    # Access Control
    "AccessLevel",
    "SecurityConfig",
    "ObjectSecurityPolicy",
    "PropertySecurityPolicy",
]
