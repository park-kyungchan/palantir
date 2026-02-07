"""
RestrictedViewPolicy Definition for Ontology Security.

RestrictedViewPolicy provides row-level security for ObjectTypes, controlling
which rows a user can access based on:
    - User attributes (organization, roles, markings)
    - Column values matching user properties
    - Security markings on individual rows

This is GAP-001 P1-CRITICAL: Required for Foundry production deployments
with multi-tenant or sensitive data.

Example:
    policy = RestrictedViewPolicy(
        logical_operator=LogicalOperator.AND,
        terms=[
            PolicyTerm(
                term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                column_name="organizationId",
                user_attribute="organizationId",
                comparison_operator=ComparisonOperator.EQUALS,
            ),
            PolicyTerm(
                term_type=PolicyTermType.MARKING_CHECK,
                column_name="securityMarkings",
            ),
        ],
    )
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


class LogicalOperator(str, Enum):
    """
    Logical operator for combining PolicyTerms.

    When multiple terms are defined:
    - AND: User must satisfy ALL terms to access the row
    - OR: User must satisfy ANY term to access the row
    """

    AND = "AND"
    OR = "OR"


class PolicyTermType(str, Enum):
    """
    Type of policy term for row-level access control.

    USER_ATTRIBUTE_COMPARISON: Compare column value to user attribute
    COLUMN_VALUE_MATCH: Match column against static values
    MARKING_CHECK: Verify user has required markings
    """

    USER_ATTRIBUTE_COMPARISON = "USER_ATTRIBUTE_COMPARISON"
    COLUMN_VALUE_MATCH = "COLUMN_VALUE_MATCH"
    MARKING_CHECK = "MARKING_CHECK"


class ComparisonOperator(str, Enum):
    """
    Comparison operator for policy term evaluation.

    EQUALS: Exact match (column == value)
    CONTAINS: Column array contains value
    IN: Column value is in specified set
    NOT_IN: Column value is not in specified set
    """

    EQUALS = "EQUALS"
    CONTAINS = "CONTAINS"
    IN = "IN"
    NOT_IN = "NOT_IN"


class IdentifierType(str, Enum):
    """Type of user identifier used in attribute mapping."""

    UUID = "UUID"
    EMAIL = "EMAIL"
    USERNAME = "USERNAME"
    PRINCIPAL_NAME = "PRINCIPAL_NAME"


class UserAttributeMapping(BaseModel):
    """
    Maps user identity attributes for policy evaluation.

    Defines how user attributes (markings, organizations) are
    extracted from the authentication context for policy evaluation.

    Example:
        mapping = UserAttributeMapping(
            identifier_type=IdentifierType.UUID,
            markings_attribute="user.markings",
            organizations_attribute="user.organizationIds",
        )
    """

    identifier_type: IdentifierType = Field(
        default=IdentifierType.UUID,
        description="Type of user identifier in the system.",
        alias="identifierType",
    )

    markings_attribute: Optional[str] = Field(
        default=None,
        description="Path to user's security markings in auth context.",
        alias="markingsAttribute",
    )

    organizations_attribute: Optional[str] = Field(
        default=None,
        description="Path to user's organization IDs in auth context.",
        alias="organizationsAttribute",
    )

    groups_attribute: Optional[str] = Field(
        default=None,
        description="Path to user's group memberships in auth context.",
        alias="groupsAttribute",
    )

    roles_attribute: Optional[str] = Field(
        default=None,
        description="Path to user's roles in auth context.",
        alias="rolesAttribute",
    )

    custom_attributes: Optional[dict[str, str]] = Field(
        default=None,
        description="Custom attribute paths for policy evaluation.",
        alias="customAttributes",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "identifierType": self.identifier_type.value,
        }
        if self.markings_attribute:
            result["markingsAttribute"] = self.markings_attribute
        if self.organizations_attribute:
            result["organizationsAttribute"] = self.organizations_attribute
        if self.groups_attribute:
            result["groupsAttribute"] = self.groups_attribute
        if self.roles_attribute:
            result["rolesAttribute"] = self.roles_attribute
        if self.custom_attributes:
            result["customAttributes"] = self.custom_attributes
        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "UserAttributeMapping":
        """Create from Foundry JSON format."""
        return cls(
            identifier_type=IdentifierType(data.get("identifierType", "UUID")),
            markings_attribute=data.get("markingsAttribute"),
            organizations_attribute=data.get("organizationsAttribute"),
            groups_attribute=data.get("groupsAttribute"),
            roles_attribute=data.get("rolesAttribute"),
            custom_attributes=data.get("customAttributes"),
        )


class PolicyTerm(BaseModel):
    """
    Single term in a RestrictedViewPolicy.

    A PolicyTerm defines one access condition that must be satisfied.
    Multiple terms are combined using the policy's logical operator.

    Term Types:
    - USER_ATTRIBUTE_COMPARISON: Compare row column to user attribute
    - COLUMN_VALUE_MATCH: Check column against static values
    - MARKING_CHECK: Verify user has markings on the row

    Example (User Attribute Comparison):
        term = PolicyTerm(
            term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
            column_name="ownerId",
            user_attribute="userId",
            comparison_operator=ComparisonOperator.EQUALS,
        )

    Example (Column Value Match):
        term = PolicyTerm(
            term_type=PolicyTermType.COLUMN_VALUE_MATCH,
            column_name="status",
            comparison_operator=ComparisonOperator.IN,
            static_value=["PUBLISHED", "APPROVED"],
        )

    Example (Marking Check):
        term = PolicyTerm(
            term_type=PolicyTermType.MARKING_CHECK,
            column_name="securityMarkings",
        )
    """

    term_type: PolicyTermType = Field(
        ...,
        description="Type of policy term.",
        alias="termType",
    )

    column_name: str = Field(
        ...,
        description="Property apiName in the ObjectType to evaluate.",
        min_length=1,
        alias="columnName",
    )

    user_attribute: Optional[str] = Field(
        default=None,
        description="User attribute path for comparison (required for USER_ATTRIBUTE_COMPARISON).",
        alias="userAttribute",
    )

    comparison_operator: Optional[ComparisonOperator] = Field(
        default=None,
        description="How to compare values (required for comparison types).",
        alias="comparisonOperator",
    )

    static_value: Optional[Union[str, int, float, bool, list[Any]]] = Field(
        default=None,
        description="Static value(s) for COLUMN_VALUE_MATCH comparison.",
        alias="staticValue",
    )

    negate: bool = Field(
        default=False,
        description="If true, negate the term result (NOT).",
    )

    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of this policy term.",
        max_length=1024,
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def validate_term_requirements(self) -> "PolicyTerm":
        """Validate term has required fields for its type."""
        if self.term_type == PolicyTermType.USER_ATTRIBUTE_COMPARISON:
            if not self.user_attribute:
                raise ValueError(
                    "USER_ATTRIBUTE_COMPARISON term requires user_attribute"
                )
            if not self.comparison_operator:
                raise ValueError(
                    "USER_ATTRIBUTE_COMPARISON term requires comparison_operator"
                )

        elif self.term_type == PolicyTermType.COLUMN_VALUE_MATCH:
            if self.static_value is None:
                raise ValueError(
                    "COLUMN_VALUE_MATCH term requires static_value"
                )
            if not self.comparison_operator:
                raise ValueError(
                    "COLUMN_VALUE_MATCH term requires comparison_operator"
                )

        elif self.term_type == PolicyTermType.MARKING_CHECK:
            # Marking check only needs column_name (already required)
            if self.user_attribute or self.static_value:
                raise ValueError(
                    "MARKING_CHECK term should not have user_attribute or static_value"
                )

        return self

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "termType": self.term_type.value,
            "columnName": self.column_name,
        }

        if self.user_attribute:
            result["userAttribute"] = self.user_attribute
        if self.comparison_operator:
            result["comparisonOperator"] = self.comparison_operator.value
        if self.static_value is not None:
            result["staticValue"] = self.static_value
        if self.negate:
            result["negate"] = True
        if self.description:
            result["description"] = self.description

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "PolicyTerm":
        """Create from Foundry JSON format."""
        comparison_op = None
        if data.get("comparisonOperator"):
            comparison_op = ComparisonOperator(data["comparisonOperator"])

        return cls(
            term_type=PolicyTermType(data["termType"]),
            column_name=data["columnName"],
            user_attribute=data.get("userAttribute"),
            comparison_operator=comparison_op,
            static_value=data.get("staticValue"),
            negate=data.get("negate", False),
            description=data.get("description"),
        )


class RestrictedViewPolicy(BaseModel):
    """
    Row-level security policy for an ObjectType.

    RestrictedViewPolicy controls which rows a user can access based on
    policy terms evaluated against user attributes and row values.

    GAP-001 P1-CRITICAL: This is required for Foundry production deployments
    with multi-tenant data or compliance requirements (HIPAA, GDPR, SOC2).

    Key Features:
    - Multiple PolicyTerms combined with AND/OR logic
    - User attribute comparison (organization, roles, groups)
    - Column value matching against static values
    - Security marking verification
    - Flexible user attribute mapping

    Example (Multi-Tenant Isolation):
        policy = RestrictedViewPolicy(
            logical_operator=LogicalOperator.AND,
            terms=[
                PolicyTerm(
                    term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                    column_name="tenantId",
                    user_attribute="user.tenantId",
                    comparison_operator=ComparisonOperator.EQUALS,
                ),
            ],
            user_attribute_mapping=UserAttributeMapping(
                identifier_type=IdentifierType.UUID,
            ),
        )

    Example (Role-Based with Markings):
        policy = RestrictedViewPolicy(
            logical_operator=LogicalOperator.OR,
            terms=[
                # Admin can see all
                PolicyTerm(
                    term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                    column_name="dummy",  # Evaluated against static
                    user_attribute="user.roles",
                    comparison_operator=ComparisonOperator.CONTAINS,
                    static_value="ADMIN",
                ),
                # Others need matching markings
                PolicyTerm(
                    term_type=PolicyTermType.MARKING_CHECK,
                    column_name="securityMarkings",
                ),
            ],
        )
    """

    logical_operator: LogicalOperator = Field(
        default=LogicalOperator.AND,
        description="How to combine multiple terms (AND requires all, OR requires any).",
        alias="logicalOperator",
    )

    terms: list[PolicyTerm] = Field(
        default_factory=list,
        description="Policy terms that define access conditions.",
        min_length=0,
    )

    user_attribute_mapping: Optional[UserAttributeMapping] = Field(
        default=None,
        description="Configuration for extracting user attributes.",
        alias="userAttributeMapping",
    )

    enabled: bool = Field(
        default=True,
        description="If false, policy is disabled (all rows visible).",
    )

    description: Optional[str] = Field(
        default=None,
        description="Human-readable description of the policy purpose.",
        max_length=2048,
    )

    fallback_behavior: str = Field(
        default="DENY",
        description="Behavior when policy cannot be evaluated: DENY or ALLOW.",
        pattern=r"^(DENY|ALLOW)$",
        alias="fallbackBehavior",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
        json_schema_extra={
            "x-palantir-security": True,
            "x-palantir-row-level-security": True,
        },
    )

    @model_validator(mode="after")
    def validate_terms_exist_when_enabled(self) -> "RestrictedViewPolicy":
        """Validate that enabled policies have at least one term."""
        if self.enabled and len(self.terms) == 0:
            raise ValueError(
                "Enabled RestrictedViewPolicy must have at least one term"
            )
        return self

    @model_validator(mode="after")
    def validate_marking_terms_have_mapping(self) -> "RestrictedViewPolicy":
        """Validate that marking check terms have attribute mapping."""
        has_marking_term = any(
            t.term_type == PolicyTermType.MARKING_CHECK for t in self.terms
        )
        if has_marking_term:
            if not self.user_attribute_mapping:
                raise ValueError(
                    "MARKING_CHECK terms require user_attribute_mapping"
                )
            if not self.user_attribute_mapping.markings_attribute:
                raise ValueError(
                    "MARKING_CHECK terms require markings_attribute in mapping"
                )
        return self

    def get_referenced_columns(self) -> list[str]:
        """Get all column names referenced by policy terms."""
        return list(set(term.column_name for term in self.terms))

    def has_marking_check(self) -> bool:
        """Check if policy includes marking verification."""
        return any(
            t.term_type == PolicyTermType.MARKING_CHECK for t in self.terms
        )

    def has_user_attribute_check(self) -> bool:
        """Check if policy includes user attribute comparison."""
        return any(
            t.term_type == PolicyTermType.USER_ATTRIBUTE_COMPARISON
            for t in self.terms
        )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Palantir Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "$type": "RestrictedViewPolicy",
            "logicalOperator": self.logical_operator.value,
            "enabled": self.enabled,
            "fallbackBehavior": self.fallback_behavior,
        }

        if self.terms:
            result["terms"] = [t.to_foundry_dict() for t in self.terms]

        if self.user_attribute_mapping:
            result["userAttributeMapping"] = self.user_attribute_mapping.to_foundry_dict()

        if self.description:
            result["description"] = self.description

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "RestrictedViewPolicy":
        """Create RestrictedViewPolicy from Palantir Foundry JSON format."""
        terms = []
        if data.get("terms"):
            terms = [PolicyTerm.from_foundry_dict(t) for t in data["terms"]]

        user_mapping = None
        if data.get("userAttributeMapping"):
            user_mapping = UserAttributeMapping.from_foundry_dict(
                data["userAttributeMapping"]
            )

        return cls(
            logical_operator=LogicalOperator(
                data.get("logicalOperator", "AND")
            ),
            terms=terms,
            user_attribute_mapping=user_mapping,
            enabled=data.get("enabled", True),
            description=data.get("description"),
            fallback_behavior=data.get("fallbackBehavior", "DENY"),
        )


# Convenience factory for common patterns
class CommonRestrictedViewPolicies:
    """
    Factory for commonly used RestrictedViewPolicy patterns.

    Usage:
        tenant_policy = CommonRestrictedViewPolicies.tenant_isolation("tenantId")
        marking_policy = CommonRestrictedViewPolicies.marking_based("securityMarkings")
    """

    @staticmethod
    def tenant_isolation(
        tenant_column: str = "tenantId",
        user_tenant_attribute: str = "user.tenantId",
    ) -> RestrictedViewPolicy:
        """Create a multi-tenant isolation policy."""
        return RestrictedViewPolicy(
            logical_operator=LogicalOperator.AND,
            terms=[
                PolicyTerm(
                    term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                    column_name=tenant_column,
                    user_attribute=user_tenant_attribute,
                    comparison_operator=ComparisonOperator.EQUALS,
                ),
            ],
            description=f"Tenant isolation: users can only see rows matching their {tenant_column}",
        )

    @staticmethod
    def marking_based(
        markings_column: str = "securityMarkings",
        markings_attribute: str = "user.markings",
    ) -> RestrictedViewPolicy:
        """Create a security markings-based policy."""
        return RestrictedViewPolicy(
            logical_operator=LogicalOperator.AND,
            terms=[
                PolicyTerm(
                    term_type=PolicyTermType.MARKING_CHECK,
                    column_name=markings_column,
                ),
            ],
            user_attribute_mapping=UserAttributeMapping(
                identifier_type=IdentifierType.UUID,
                markings_attribute=markings_attribute,
            ),
            description=f"Marking-based access: users must have markings that cover {markings_column}",
        )

    @staticmethod
    def owner_or_admin(
        owner_column: str = "ownerId",
        admin_role: str = "ADMIN",
    ) -> RestrictedViewPolicy:
        """Create owner-or-admin access policy."""
        return RestrictedViewPolicy(
            logical_operator=LogicalOperator.OR,
            terms=[
                # Owner can see their own records
                PolicyTerm(
                    term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                    column_name=owner_column,
                    user_attribute="user.id",
                    comparison_operator=ComparisonOperator.EQUALS,
                    description="Owner access",
                ),
                # Admins can see all records
                PolicyTerm(
                    term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                    column_name=owner_column,  # Dummy column for role check
                    user_attribute="user.roles",
                    comparison_operator=ComparisonOperator.CONTAINS,
                    static_value=admin_role,
                    description="Admin access",
                ),
            ],
            description=f"Owner ({owner_column}) or {admin_role} role can access",
        )

    @staticmethod
    def organization_hierarchy(
        org_column: str = "organizationId",
        org_attribute: str = "user.organizationIds",
    ) -> RestrictedViewPolicy:
        """Create organization-based access with hierarchy support."""
        return RestrictedViewPolicy(
            logical_operator=LogicalOperator.AND,
            terms=[
                PolicyTerm(
                    term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                    column_name=org_column,
                    user_attribute=org_attribute,
                    comparison_operator=ComparisonOperator.IN,
                    description="User must belong to the record's organization",
                ),
            ],
            user_attribute_mapping=UserAttributeMapping(
                identifier_type=IdentifierType.UUID,
                organizations_attribute=org_attribute,
            ),
            description=f"Organization-based access: {org_column} must be in user's organizations",
        )
