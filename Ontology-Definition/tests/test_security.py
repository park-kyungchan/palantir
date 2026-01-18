"""
Unit tests for security module: RestrictedViewPolicy, PolicyTerm, and related types.

Tests cover:
- GAP-001 P1-CRITICAL: RestrictedViewPolicy for row-level security
- PolicyTerm validation for different term types
- Logical operators (AND/OR) for combining terms
- Comparison operators (EQUALS, CONTAINS, IN, NOT_IN)
- UserAttributeMapping for user identity context
- Validation error cases
- Serialization (to_foundry_dict / from_foundry_dict roundtrip)
"""

import pytest
from pydantic import ValidationError

from ontology_definition import (
    ComparisonOperator,
    LogicalOperator,
    PolicyTerm,
    PolicyTermType,
    RestrictedViewPolicy,
)
from ontology_definition.security.restricted_view import (
    CommonRestrictedViewPolicies,
    IdentifierType,
    UserAttributeMapping,
)


class TestPolicyTermType:
    """Tests for PolicyTermType enumeration."""

    def test_all_term_types_exist(self):
        """Verify all expected term types are available."""
        assert PolicyTermType.USER_ATTRIBUTE_COMPARISON.value == "USER_ATTRIBUTE_COMPARISON"
        assert PolicyTermType.COLUMN_VALUE_MATCH.value == "COLUMN_VALUE_MATCH"
        assert PolicyTermType.MARKING_CHECK.value == "MARKING_CHECK"

    def test_term_type_from_string(self):
        """Test creating PolicyTermType from string."""
        assert PolicyTermType("USER_ATTRIBUTE_COMPARISON") == PolicyTermType.USER_ATTRIBUTE_COMPARISON
        assert PolicyTermType("COLUMN_VALUE_MATCH") == PolicyTermType.COLUMN_VALUE_MATCH
        assert PolicyTermType("MARKING_CHECK") == PolicyTermType.MARKING_CHECK


class TestLogicalOperator:
    """Tests for LogicalOperator enumeration."""

    def test_all_operators_exist(self):
        """Verify AND and OR operators are available."""
        assert LogicalOperator.AND.value == "AND"
        assert LogicalOperator.OR.value == "OR"


class TestComparisonOperator:
    """Tests for ComparisonOperator enumeration."""

    def test_all_comparison_operators_exist(self):
        """Verify all expected comparison operators are available."""
        assert ComparisonOperator.EQUALS.value == "EQUALS"
        assert ComparisonOperator.CONTAINS.value == "CONTAINS"
        assert ComparisonOperator.IN.value == "IN"
        assert ComparisonOperator.NOT_IN.value == "NOT_IN"


class TestIdentifierType:
    """Tests for IdentifierType enumeration."""

    def test_all_identifier_types_exist(self):
        """Verify all expected identifier types are available."""
        assert IdentifierType.UUID.value == "UUID"
        assert IdentifierType.EMAIL.value == "EMAIL"
        assert IdentifierType.USERNAME.value == "USERNAME"
        assert IdentifierType.PRINCIPAL_NAME.value == "PRINCIPAL_NAME"


class TestUserAttributeMapping:
    """Tests for UserAttributeMapping - user identity context for policies."""

    def test_basic_mapping(self):
        """Basic UserAttributeMapping creation."""
        mapping = UserAttributeMapping(
            identifier_type=IdentifierType.UUID,
            markings_attribute="user.markings",
        )
        assert mapping.identifier_type == IdentifierType.UUID
        assert mapping.markings_attribute == "user.markings"

    def test_full_mapping(self):
        """UserAttributeMapping with all attributes."""
        mapping = UserAttributeMapping(
            identifier_type=IdentifierType.EMAIL,
            markings_attribute="user.markings",
            organizations_attribute="user.organizationIds",
            groups_attribute="user.groups",
            roles_attribute="user.roles",
            custom_attributes={"tenantId": "user.tenantId"},
        )
        assert mapping.identifier_type == IdentifierType.EMAIL
        assert mapping.markings_attribute == "user.markings"
        assert mapping.organizations_attribute == "user.organizationIds"
        assert mapping.groups_attribute == "user.groups"
        assert mapping.roles_attribute == "user.roles"
        assert mapping.custom_attributes == {"tenantId": "user.tenantId"}

    def test_default_identifier_type(self):
        """Default identifier type should be UUID."""
        mapping = UserAttributeMapping()
        assert mapping.identifier_type == IdentifierType.UUID

    def test_to_foundry_dict(self):
        """Export to Foundry dict format."""
        mapping = UserAttributeMapping(
            identifier_type=IdentifierType.UUID,
            markings_attribute="user.markings",
        )
        result = mapping.to_foundry_dict()
        assert result["identifierType"] == "UUID"
        assert result["markingsAttribute"] == "user.markings"

    def test_from_foundry_dict_roundtrip(self):
        """from_foundry_dict should be inverse of to_foundry_dict."""
        original = UserAttributeMapping(
            identifier_type=IdentifierType.EMAIL,
            markings_attribute="user.markings",
            organizations_attribute="user.orgs",
        )
        dict_form = original.to_foundry_dict()
        restored = UserAttributeMapping.from_foundry_dict(dict_form)
        assert restored.identifier_type == original.identifier_type
        assert restored.markings_attribute == original.markings_attribute
        assert restored.organizations_attribute == original.organizations_attribute


class TestPolicyTerm:
    """Tests for PolicyTerm - single access condition in a policy."""

    def test_user_attribute_comparison_valid(self):
        """Valid USER_ATTRIBUTE_COMPARISON term."""
        term = PolicyTerm(
            term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
            column_name="tenantId",
            user_attribute="user.tenantId",
            comparison_operator=ComparisonOperator.EQUALS,
        )
        assert term.term_type == PolicyTermType.USER_ATTRIBUTE_COMPARISON
        assert term.column_name == "tenantId"
        assert term.user_attribute == "user.tenantId"
        assert term.comparison_operator == ComparisonOperator.EQUALS

    def test_user_attribute_comparison_requires_user_attribute(self):
        """USER_ATTRIBUTE_COMPARISON must have user_attribute."""
        with pytest.raises(ValidationError) as exc_info:
            PolicyTerm(
                term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                column_name="tenantId",
                comparison_operator=ComparisonOperator.EQUALS,
                # Missing: user_attribute
            )
        assert "USER_ATTRIBUTE_COMPARISON term requires user_attribute" in str(exc_info.value)

    def test_user_attribute_comparison_requires_comparison_operator(self):
        """USER_ATTRIBUTE_COMPARISON must have comparison_operator."""
        with pytest.raises(ValidationError) as exc_info:
            PolicyTerm(
                term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                column_name="tenantId",
                user_attribute="user.tenantId",
                # Missing: comparison_operator
            )
        assert "USER_ATTRIBUTE_COMPARISON term requires comparison_operator" in str(exc_info.value)

    def test_column_value_match_valid(self):
        """Valid COLUMN_VALUE_MATCH term."""
        term = PolicyTerm(
            term_type=PolicyTermType.COLUMN_VALUE_MATCH,
            column_name="status",
            comparison_operator=ComparisonOperator.IN,
            static_value=["PUBLISHED", "APPROVED"],
        )
        assert term.term_type == PolicyTermType.COLUMN_VALUE_MATCH
        assert term.column_name == "status"
        assert term.static_value == ["PUBLISHED", "APPROVED"]

    def test_column_value_match_requires_static_value(self):
        """COLUMN_VALUE_MATCH must have static_value."""
        with pytest.raises(ValidationError) as exc_info:
            PolicyTerm(
                term_type=PolicyTermType.COLUMN_VALUE_MATCH,
                column_name="status",
                comparison_operator=ComparisonOperator.IN,
                # Missing: static_value
            )
        assert "COLUMN_VALUE_MATCH term requires static_value" in str(exc_info.value)

    def test_column_value_match_requires_comparison_operator(self):
        """COLUMN_VALUE_MATCH must have comparison_operator."""
        with pytest.raises(ValidationError) as exc_info:
            PolicyTerm(
                term_type=PolicyTermType.COLUMN_VALUE_MATCH,
                column_name="status",
                static_value=["PUBLISHED"],
                # Missing: comparison_operator
            )
        assert "COLUMN_VALUE_MATCH term requires comparison_operator" in str(exc_info.value)

    def test_marking_check_valid(self):
        """Valid MARKING_CHECK term."""
        term = PolicyTerm(
            term_type=PolicyTermType.MARKING_CHECK,
            column_name="securityMarkings",
        )
        assert term.term_type == PolicyTermType.MARKING_CHECK
        assert term.column_name == "securityMarkings"

    def test_marking_check_cannot_have_user_attribute(self):
        """MARKING_CHECK should not have user_attribute or static_value."""
        with pytest.raises(ValidationError) as exc_info:
            PolicyTerm(
                term_type=PolicyTermType.MARKING_CHECK,
                column_name="securityMarkings",
                user_attribute="user.markings",  # Invalid for MARKING_CHECK
            )
        assert "MARKING_CHECK term should not have user_attribute or static_value" in str(exc_info.value)

    def test_marking_check_cannot_have_static_value(self):
        """MARKING_CHECK should not have static_value."""
        with pytest.raises(ValidationError) as exc_info:
            PolicyTerm(
                term_type=PolicyTermType.MARKING_CHECK,
                column_name="securityMarkings",
                static_value="some_value",  # Invalid for MARKING_CHECK
            )
        assert "MARKING_CHECK term should not have user_attribute or static_value" in str(exc_info.value)

    def test_term_with_negate(self):
        """Term with negate flag."""
        term = PolicyTerm(
            term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
            column_name="excludedRegion",
            user_attribute="user.region",
            comparison_operator=ComparisonOperator.EQUALS,
            negate=True,
        )
        assert term.negate is True

    def test_term_with_description(self):
        """Term with description."""
        term = PolicyTerm(
            term_type=PolicyTermType.MARKING_CHECK,
            column_name="securityMarkings",
            description="Verify user has required security markings",
        )
        assert term.description == "Verify user has required security markings"

    def test_to_foundry_dict(self):
        """Export term to Foundry dict."""
        term = PolicyTerm(
            term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
            column_name="tenantId",
            user_attribute="user.tenantId",
            comparison_operator=ComparisonOperator.EQUALS,
            description="Tenant isolation",
        )
        result = term.to_foundry_dict()
        assert result["termType"] == "USER_ATTRIBUTE_COMPARISON"
        assert result["columnName"] == "tenantId"
        assert result["userAttribute"] == "user.tenantId"
        assert result["comparisonOperator"] == "EQUALS"
        assert result["description"] == "Tenant isolation"

    def test_from_foundry_dict_roundtrip(self):
        """from_foundry_dict should be inverse of to_foundry_dict."""
        original = PolicyTerm(
            term_type=PolicyTermType.COLUMN_VALUE_MATCH,
            column_name="status",
            comparison_operator=ComparisonOperator.IN,
            static_value=["ACTIVE", "PENDING"],
            negate=True,
        )
        dict_form = original.to_foundry_dict()
        restored = PolicyTerm.from_foundry_dict(dict_form)
        assert restored.term_type == original.term_type
        assert restored.column_name == original.column_name
        assert restored.comparison_operator == original.comparison_operator
        assert restored.static_value == original.static_value
        assert restored.negate == original.negate


class TestRestrictedViewPolicy:
    """Tests for RestrictedViewPolicy - row-level security policy."""

    def test_basic_policy(self, sample_restricted_view):
        """Basic policy creation using fixture."""
        assert sample_restricted_view.enabled is True
        assert sample_restricted_view.logical_operator == LogicalOperator.AND
        assert len(sample_restricted_view.terms) == 1

    def test_enabled_policy_requires_terms(self):
        """Enabled policy must have at least one term."""
        with pytest.raises(ValidationError) as exc_info:
            RestrictedViewPolicy(
                logical_operator=LogicalOperator.AND,
                terms=[],  # Empty
                enabled=True,
            )
        assert "Enabled RestrictedViewPolicy must have at least one term" in str(exc_info.value)

    def test_disabled_policy_can_be_empty(self):
        """Disabled policy can have no terms."""
        policy = RestrictedViewPolicy(
            logical_operator=LogicalOperator.AND,
            terms=[],
            enabled=False,
        )
        assert policy.enabled is False
        assert len(policy.terms) == 0

    def test_marking_check_requires_user_attribute_mapping(self):
        """MARKING_CHECK terms require user_attribute_mapping."""
        with pytest.raises(ValidationError) as exc_info:
            RestrictedViewPolicy(
                logical_operator=LogicalOperator.AND,
                terms=[
                    PolicyTerm(
                        term_type=PolicyTermType.MARKING_CHECK,
                        column_name="securityMarkings",
                    ),
                ],
                enabled=True,
                # Missing: user_attribute_mapping
            )
        assert "MARKING_CHECK terms require user_attribute_mapping" in str(exc_info.value)

    def test_marking_check_requires_markings_attribute(self):
        """MARKING_CHECK terms require markings_attribute in mapping."""
        with pytest.raises(ValidationError) as exc_info:
            RestrictedViewPolicy(
                logical_operator=LogicalOperator.AND,
                terms=[
                    PolicyTerm(
                        term_type=PolicyTermType.MARKING_CHECK,
                        column_name="securityMarkings",
                    ),
                ],
                enabled=True,
                user_attribute_mapping=UserAttributeMapping(
                    identifier_type=IdentifierType.UUID,
                    # Missing: markings_attribute
                ),
            )
        assert "MARKING_CHECK terms require markings_attribute in mapping" in str(exc_info.value)

    def test_marking_based_policy_valid(self, marking_based_restricted_view):
        """Valid marking-based policy using fixture."""
        assert marking_based_restricted_view.has_marking_check() is True
        assert marking_based_restricted_view.user_attribute_mapping is not None
        assert marking_based_restricted_view.user_attribute_mapping.markings_attribute == "user.markings"

    def test_multi_term_policy_with_or_logic(self, multi_term_restricted_view):
        """Policy with multiple terms using OR logic."""
        assert multi_term_restricted_view.logical_operator == LogicalOperator.OR
        assert len(multi_term_restricted_view.terms) == 2
        assert multi_term_restricted_view.has_user_attribute_check() is True

    def test_default_fallback_behavior(self):
        """Default fallback behavior should be DENY."""
        policy = RestrictedViewPolicy(
            terms=[
                PolicyTerm(
                    term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                    column_name="ownerId",
                    user_attribute="user.id",
                    comparison_operator=ComparisonOperator.EQUALS,
                ),
            ],
            enabled=True,
        )
        assert policy.fallback_behavior == "DENY"

    def test_allow_fallback_behavior(self):
        """Policy with ALLOW fallback behavior."""
        policy = RestrictedViewPolicy(
            terms=[
                PolicyTerm(
                    term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                    column_name="ownerId",
                    user_attribute="user.id",
                    comparison_operator=ComparisonOperator.EQUALS,
                ),
            ],
            enabled=True,
            fallback_behavior="ALLOW",
        )
        assert policy.fallback_behavior == "ALLOW"

    def test_invalid_fallback_behavior(self):
        """Invalid fallback behavior should fail."""
        with pytest.raises(ValidationError):
            RestrictedViewPolicy(
                terms=[
                    PolicyTerm(
                        term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                        column_name="ownerId",
                        user_attribute="user.id",
                        comparison_operator=ComparisonOperator.EQUALS,
                    ),
                ],
                enabled=True,
                fallback_behavior="INVALID",  # Invalid
            )

    def test_get_referenced_columns(self, multi_term_restricted_view):
        """get_referenced_columns should return all unique columns."""
        columns = multi_term_restricted_view.get_referenced_columns()
        assert "ownerId" in columns
        assert "departmentId" in columns
        assert len(columns) == 2

    def test_has_marking_check_true(self, marking_based_restricted_view):
        """has_marking_check should return True when marking term present."""
        assert marking_based_restricted_view.has_marking_check() is True

    def test_has_marking_check_false(self, sample_restricted_view):
        """has_marking_check should return False when no marking term."""
        assert sample_restricted_view.has_marking_check() is False

    def test_has_user_attribute_check_true(self, sample_restricted_view):
        """has_user_attribute_check should return True when user attr term present."""
        assert sample_restricted_view.has_user_attribute_check() is True

    def test_has_user_attribute_check_false(self, marking_based_restricted_view):
        """has_user_attribute_check should return False when no user attr term."""
        assert marking_based_restricted_view.has_user_attribute_check() is False

    def test_to_foundry_dict(self, sample_restricted_view):
        """Export policy to Foundry dict format."""
        result = sample_restricted_view.to_foundry_dict()
        assert result["$type"] == "RestrictedViewPolicy"
        assert result["logicalOperator"] == "AND"
        assert result["enabled"] is True
        assert result["fallbackBehavior"] == "DENY"
        assert len(result["terms"]) == 1

    def test_from_foundry_dict_roundtrip(self, sample_restricted_view):
        """from_foundry_dict should be inverse of to_foundry_dict."""
        dict_form = sample_restricted_view.to_foundry_dict()
        restored = RestrictedViewPolicy.from_foundry_dict(dict_form)
        assert restored.logical_operator == sample_restricted_view.logical_operator
        assert restored.enabled == sample_restricted_view.enabled
        assert len(restored.terms) == len(sample_restricted_view.terms)
        assert restored.terms[0].term_type == sample_restricted_view.terms[0].term_type


class TestCommonRestrictedViewPolicies:
    """Tests for CommonRestrictedViewPolicies factory patterns."""

    def test_tenant_isolation_policy(self):
        """Create tenant isolation policy."""
        policy = CommonRestrictedViewPolicies.tenant_isolation("tenantId", "user.tenantId")
        assert policy.enabled is True
        assert policy.logical_operator == LogicalOperator.AND
        assert len(policy.terms) == 1
        assert policy.terms[0].term_type == PolicyTermType.USER_ATTRIBUTE_COMPARISON
        assert policy.terms[0].column_name == "tenantId"
        assert policy.terms[0].user_attribute == "user.tenantId"
        assert policy.terms[0].comparison_operator == ComparisonOperator.EQUALS

    def test_marking_based_policy(self):
        """Create marking-based policy."""
        policy = CommonRestrictedViewPolicies.marking_based("securityMarkings", "user.markings")
        assert policy.enabled is True
        assert policy.has_marking_check() is True
        assert policy.user_attribute_mapping is not None
        assert policy.user_attribute_mapping.markings_attribute == "user.markings"

    def test_owner_or_admin_policy(self):
        """Create owner-or-admin policy."""
        policy = CommonRestrictedViewPolicies.owner_or_admin("ownerId", "ADMIN")
        assert policy.enabled is True
        assert policy.logical_operator == LogicalOperator.OR
        assert len(policy.terms) == 2
        # First term: owner access
        assert policy.terms[0].term_type == PolicyTermType.USER_ATTRIBUTE_COMPARISON
        assert policy.terms[0].comparison_operator == ComparisonOperator.EQUALS
        # Second term: admin role access
        assert policy.terms[1].term_type == PolicyTermType.USER_ATTRIBUTE_COMPARISON
        assert policy.terms[1].comparison_operator == ComparisonOperator.CONTAINS

    def test_organization_hierarchy_policy(self):
        """Create organization-based policy."""
        policy = CommonRestrictedViewPolicies.organization_hierarchy("orgId", "user.orgs")
        assert policy.enabled is True
        assert policy.terms[0].comparison_operator == ComparisonOperator.IN
        assert policy.user_attribute_mapping is not None
        assert policy.user_attribute_mapping.organizations_attribute == "user.orgs"


class TestComparisonOperatorUsage:
    """Tests for all ComparisonOperator values in context."""

    def test_equals_operator(self):
        """Test EQUALS comparison operator."""
        term = PolicyTerm(
            term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
            column_name="ownerId",
            user_attribute="user.id",
            comparison_operator=ComparisonOperator.EQUALS,
        )
        assert term.comparison_operator == ComparisonOperator.EQUALS

    def test_not_equals_via_negate(self):
        """Test NOT_EQUALS pattern using negate."""
        term = PolicyTerm(
            term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
            column_name="excludedRegion",
            user_attribute="user.region",
            comparison_operator=ComparisonOperator.EQUALS,
            negate=True,  # NOT EQUALS
        )
        assert term.comparison_operator == ComparisonOperator.EQUALS
        assert term.negate is True

    def test_in_operator(self):
        """Test IN comparison operator."""
        term = PolicyTerm(
            term_type=PolicyTermType.COLUMN_VALUE_MATCH,
            column_name="status",
            comparison_operator=ComparisonOperator.IN,
            static_value=["ACTIVE", "PENDING", "APPROVED"],
        )
        assert term.comparison_operator == ComparisonOperator.IN
        assert term.static_value == ["ACTIVE", "PENDING", "APPROVED"]

    def test_not_in_operator(self):
        """Test NOT_IN comparison operator."""
        term = PolicyTerm(
            term_type=PolicyTermType.COLUMN_VALUE_MATCH,
            column_name="status",
            comparison_operator=ComparisonOperator.NOT_IN,
            static_value=["DELETED", "ARCHIVED"],
        )
        assert term.comparison_operator == ComparisonOperator.NOT_IN

    def test_contains_operator(self):
        """Test CONTAINS comparison operator."""
        term = PolicyTerm(
            term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
            column_name="roles",
            user_attribute="user.roles",
            comparison_operator=ComparisonOperator.CONTAINS,
        )
        assert term.comparison_operator == ComparisonOperator.CONTAINS


class TestLogicalOperatorCombinations:
    """Tests for combining terms with AND/OR logic."""

    def test_and_combination_all_must_pass(self):
        """AND logic: all terms must be satisfied."""
        policy = RestrictedViewPolicy(
            logical_operator=LogicalOperator.AND,
            terms=[
                PolicyTerm(
                    term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                    column_name="tenantId",
                    user_attribute="user.tenantId",
                    comparison_operator=ComparisonOperator.EQUALS,
                ),
                PolicyTerm(
                    term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                    column_name="departmentId",
                    user_attribute="user.departmentId",
                    comparison_operator=ComparisonOperator.EQUALS,
                ),
            ],
            enabled=True,
        )
        assert policy.logical_operator == LogicalOperator.AND
        assert len(policy.terms) == 2

    def test_or_combination_any_can_pass(self):
        """OR logic: any term can be satisfied."""
        policy = RestrictedViewPolicy(
            logical_operator=LogicalOperator.OR,
            terms=[
                PolicyTerm(
                    term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                    column_name="ownerId",
                    user_attribute="user.id",
                    comparison_operator=ComparisonOperator.EQUALS,
                    description="Owner access",
                ),
                PolicyTerm(
                    term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                    column_name="publicAccess",
                    user_attribute="public.flag",
                    comparison_operator=ComparisonOperator.EQUALS,
                    description="Public access",
                ),
            ],
            enabled=True,
        )
        assert policy.logical_operator == LogicalOperator.OR
        assert len(policy.terms) == 2

    def test_mixed_term_types_and_logic(self):
        """Mix of different term types with AND logic."""
        policy = RestrictedViewPolicy(
            logical_operator=LogicalOperator.AND,
            terms=[
                PolicyTerm(
                    term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                    column_name="tenantId",
                    user_attribute="user.tenantId",
                    comparison_operator=ComparisonOperator.EQUALS,
                ),
                PolicyTerm(
                    term_type=PolicyTermType.COLUMN_VALUE_MATCH,
                    column_name="status",
                    comparison_operator=ComparisonOperator.IN,
                    static_value=["ACTIVE"],
                ),
            ],
            enabled=True,
        )
        assert len(policy.terms) == 2
        assert policy.terms[0].term_type == PolicyTermType.USER_ATTRIBUTE_COMPARISON
        assert policy.terms[1].term_type == PolicyTermType.COLUMN_VALUE_MATCH

    def test_mixed_term_types_or_logic_with_marking(self):
        """Mix of term types including marking check with OR logic."""
        policy = RestrictedViewPolicy(
            logical_operator=LogicalOperator.OR,
            terms=[
                PolicyTerm(
                    term_type=PolicyTermType.USER_ATTRIBUTE_COMPARISON,
                    column_name="isAdmin",
                    user_attribute="user.isAdmin",
                    comparison_operator=ComparisonOperator.EQUALS,
                ),
                PolicyTerm(
                    term_type=PolicyTermType.MARKING_CHECK,
                    column_name="securityMarkings",
                ),
            ],
            enabled=True,
            user_attribute_mapping=UserAttributeMapping(
                identifier_type=IdentifierType.UUID,
                markings_attribute="user.markings",
            ),
        )
        assert len(policy.terms) == 2
        assert policy.has_marking_check() is True
        assert policy.has_user_attribute_check() is True
