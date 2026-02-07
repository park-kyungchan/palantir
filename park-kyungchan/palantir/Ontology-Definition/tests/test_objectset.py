"""
Unit tests for ObjectSet type definitions.

Tests cover:
- Filter operators and conditions
- Combined filters (AND/OR/NOT)
- Set operations (union, intersect, subtract)
- Aggregation types and clauses
- OrderByClause and ObjectSetDefinition
- Serialization (to_foundry_dict / from_foundry_dict roundtrip)
"""

import pytest

from ontology_definition.types import (
    ObjectSetDefinition,
    FilterCondition,
    CombinedFilter,
    FilterOperatorType,
    FilterCombinator,
    SetOperation,
    AggregationType,
    OrderByClause,
    OrderDirection,
    AggregationClause,
)


class TestFilterOperatorType:
    """Tests for FilterOperatorType enum."""

    def test_string_operators(self):
        """String filter operators should be available."""
        assert FilterOperatorType.PHRASE.value == "phrase"
        assert FilterOperatorType.PHRASE_PREFIX.value == "phrasePrefix"
        assert FilterOperatorType.FUZZY_MATCH_ANY_TOKEN.value == "fuzzyMatchAnyToken"

    def test_range_operators(self):
        """Range filter operators should be available."""
        assert FilterOperatorType.RANGE_LT.value == "range.lt"
        assert FilterOperatorType.RANGE_GTE.value == "range.gte"

    def test_geo_operators(self):
        """Geo filter operators should be available."""
        assert FilterOperatorType.WITHIN_DISTANCE_OF.value == "withinDistanceOf"
        assert FilterOperatorType.WITHIN_POLYGON.value == "withinPolygon"


class TestFilterCondition:
    """Tests for FilterCondition - single filter condition."""

    def test_exact_match(self):
        """Exact match filter condition."""
        condition = FilterCondition(
            property_name="employeeId",
            operator=FilterOperatorType.EXACT_MATCH,
            value="E12345"
        )
        assert condition.property_name == "employeeId"
        assert condition.operator == FilterOperatorType.EXACT_MATCH
        assert condition.value == "E12345"

    def test_range_filter(self):
        """Range filter condition."""
        condition = FilterCondition(
            property_name="salary",
            operator=FilterOperatorType.RANGE_GTE,
            value=50000
        )
        assert condition.operator == FilterOperatorType.RANGE_GTE
        assert condition.value == 50000

    def test_fuzzy_match_with_parameters(self):
        """Fuzzy match filter with parameters."""
        condition = FilterCondition(
            property_name="name",
            operator=FilterOperatorType.FUZZY_MATCH_ANY_TOKEN,
            value="John",
            parameters={"maxEdits": 2}
        )
        assert condition.parameters == {"maxEdits": 2}

    def test_has_property_without_value(self):
        """hasProperty operator doesn't require value."""
        condition = FilterCondition(
            property_name="email",
            operator=FilterOperatorType.HAS_PROPERTY
        )
        assert condition.value is None

    def test_to_foundry_dict(self):
        """Export to Foundry dictionary format."""
        condition = FilterCondition(
            property_name="department",
            operator=FilterOperatorType.EXACT_MATCH,
            value="Engineering"
        )
        result = condition.to_foundry_dict()
        assert result == {
            "propertyName": "department",
            "operator": "exactMatch",
            "value": "Engineering"
        }

    def test_from_foundry_dict(self):
        """Create from Foundry dictionary format."""
        data = {
            "propertyName": "salary",
            "operator": "range.gte",
            "value": 100000
        }
        condition = FilterCondition.from_foundry_dict(data)
        assert condition.property_name == "salary"
        assert condition.operator == FilterOperatorType.RANGE_GTE
        assert condition.value == 100000


class TestCombinedFilter:
    """Tests for CombinedFilter - AND/OR/NOT combinations."""

    def test_and_filter(self):
        """AND combined filter."""
        combined = CombinedFilter(
            combinator=FilterCombinator.AND,
            filters=[
                FilterCondition(
                    property_name="department",
                    operator=FilterOperatorType.EXACT_MATCH,
                    value="Engineering"
                ),
                FilterCondition(
                    property_name="salary",
                    operator=FilterOperatorType.RANGE_GTE,
                    value=100000
                )
            ]
        )
        assert combined.combinator == FilterCombinator.AND
        assert len(combined.filters) == 2

    def test_or_filter(self):
        """OR combined filter."""
        combined = CombinedFilter(
            combinator=FilterCombinator.OR,
            filters=[
                FilterCondition(
                    property_name="status",
                    operator=FilterOperatorType.EXACT_MATCH,
                    value="active"
                ),
                FilterCondition(
                    property_name="status",
                    operator=FilterOperatorType.EXACT_MATCH,
                    value="pending"
                )
            ]
        )
        assert combined.combinator == FilterCombinator.OR

    def test_nested_combined_filters(self):
        """Nested combined filters: (A AND B) OR C."""
        inner_and = CombinedFilter(
            combinator=FilterCombinator.AND,
            filters=[
                FilterCondition(
                    property_name="department",
                    operator=FilterOperatorType.EXACT_MATCH,
                    value="Engineering"
                ),
                FilterCondition(
                    property_name="level",
                    operator=FilterOperatorType.RANGE_GTE,
                    value=5
                )
            ]
        )
        outer_or = CombinedFilter(
            combinator=FilterCombinator.OR,
            filters=[
                inner_and,
                FilterCondition(
                    property_name="is_manager",
                    operator=FilterOperatorType.IS_TRUE
                )
            ]
        )
        assert outer_or.combinator == FilterCombinator.OR
        assert len(outer_or.filters) == 2
        assert isinstance(outer_or.filters[0], CombinedFilter)

    def test_to_foundry_dict_roundtrip(self):
        """Roundtrip serialization."""
        original = CombinedFilter(
            combinator=FilterCombinator.AND,
            filters=[
                FilterCondition(
                    property_name="department",
                    operator=FilterOperatorType.EXACT_MATCH,
                    value="Sales"
                )
            ]
        )
        dict_form = original.to_foundry_dict()
        restored = CombinedFilter.from_foundry_dict(dict_form)
        assert restored.combinator == original.combinator
        assert len(restored.filters) == len(original.filters)


class TestOrderByClause:
    """Tests for OrderByClause - ordering specification."""

    def test_ascending_order(self):
        """Ascending order by property."""
        order = OrderByClause(
            property_name="employeeName",
            direction=OrderDirection.ASC
        )
        assert order.direction == OrderDirection.ASC

    def test_descending_order(self):
        """Descending order by property."""
        order = OrderByClause(
            property_name="salary",
            direction=OrderDirection.DESC
        )
        assert order.direction == OrderDirection.DESC

    def test_relevance_order(self):
        """Relevance order (for search results)."""
        order = OrderByClause(direction=OrderDirection.RELEVANCE)
        assert order.direction == OrderDirection.RELEVANCE
        assert order.property_name is None

    def test_to_foundry_dict(self):
        """Export to Foundry dictionary format."""
        order = OrderByClause(
            property_name="createdAt",
            direction=OrderDirection.DESC
        )
        result = order.to_foundry_dict()
        assert result == {"propertyName": "createdAt", "direction": "desc"}


class TestAggregationClause:
    """Tests for AggregationClause - aggregation operations."""

    def test_count_aggregation(self):
        """Count aggregation (no property needed)."""
        agg = AggregationClause(aggregation_type=AggregationType.COUNT)
        assert agg.aggregation_type == AggregationType.COUNT
        assert agg.property_name is None

    def test_average_aggregation(self):
        """Average aggregation on property."""
        agg = AggregationClause(
            aggregation_type=AggregationType.AVERAGE,
            property_name="salary"
        )
        assert agg.aggregation_type == AggregationType.AVERAGE
        assert agg.property_name == "salary"

    def test_sum_aggregation(self):
        """Sum aggregation on property."""
        agg = AggregationClause(
            aggregation_type=AggregationType.SUM,
            property_name="amount"
        )
        assert agg.aggregation_type == AggregationType.SUM

    def test_to_foundry_dict(self):
        """Export to Foundry dictionary format."""
        agg = AggregationClause(
            aggregation_type=AggregationType.MAX,
            property_name="price"
        )
        result = agg.to_foundry_dict()
        assert result == {"aggregationType": "max", "propertyName": "price"}


class TestSetOperation:
    """Tests for SetOperation enum."""

    def test_set_operations(self):
        """Set operations should be available."""
        assert SetOperation.UNION.value == "union"
        assert SetOperation.INTERSECT.value == "intersect"
        assert SetOperation.SUBTRACT.value == "subtract"


class TestObjectSetDefinition:
    """Tests for ObjectSetDefinition - complete object set query."""

    def test_basic_object_set(self):
        """Basic object set with object type only."""
        obj_set = ObjectSetDefinition(object_type="Employee")
        assert obj_set.object_type == "Employee"
        assert obj_set.filters is None

    def test_with_single_filter(self):
        """Object set with single filter condition."""
        obj_set = ObjectSetDefinition(
            object_type="Employee",
            filters=FilterCondition(
                property_name="department",
                operator=FilterOperatorType.EXACT_MATCH,
                value="Engineering"
            )
        )
        assert obj_set.filters is not None
        assert isinstance(obj_set.filters, FilterCondition)

    def test_with_combined_filter(self):
        """Object set with combined filter."""
        obj_set = ObjectSetDefinition(
            object_type="Employee",
            filters=CombinedFilter(
                combinator=FilterCombinator.AND,
                filters=[
                    FilterCondition(
                        property_name="department",
                        operator=FilterOperatorType.EXACT_MATCH,
                        value="Engineering"
                    ),
                    FilterCondition(
                        property_name="salary",
                        operator=FilterOperatorType.RANGE_GTE,
                        value=100000
                    )
                ]
            )
        )
        assert isinstance(obj_set.filters, CombinedFilter)

    def test_with_ordering(self):
        """Object set with ordering."""
        obj_set = ObjectSetDefinition(
            object_type="Employee",
            ordering=[
                OrderByClause(property_name="salary", direction=OrderDirection.DESC),
                OrderByClause(property_name="name", direction=OrderDirection.ASC)
            ]
        )
        assert len(obj_set.ordering) == 2

    def test_with_limit(self):
        """Object set with result limit."""
        obj_set = ObjectSetDefinition(
            object_type="Employee",
            limit=100
        )
        assert obj_set.limit == 100

    def test_limit_max_100000(self):
        """Limit should not exceed 100,000."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError) as exc_info:
            ObjectSetDefinition(
                object_type="Employee",
                limit=200000  # Too high!
            )
        assert "limit" in str(exc_info.value).lower() or "le" in str(exc_info.value).lower()

    def test_with_aggregations(self):
        """Object set with aggregations."""
        obj_set = ObjectSetDefinition(
            object_type="Employee",
            aggregations=[
                AggregationClause(aggregation_type=AggregationType.COUNT),
                AggregationClause(
                    aggregation_type=AggregationType.AVERAGE,
                    property_name="salary"
                )
            ]
        )
        assert len(obj_set.aggregations) == 2

    def test_complete_object_set(self):
        """Complete object set with all components."""
        obj_set = ObjectSetDefinition(
            object_type="Employee",
            filters=CombinedFilter(
                combinator=FilterCombinator.AND,
                filters=[
                    FilterCondition(
                        property_name="department",
                        operator=FilterOperatorType.EXACT_MATCH,
                        value="Engineering"
                    ),
                    FilterCondition(
                        property_name="salary",
                        operator=FilterOperatorType.RANGE_GTE,
                        value=100000
                    )
                ]
            ),
            ordering=[
                OrderByClause(property_name="salary", direction=OrderDirection.DESC)
            ],
            limit=100,
            aggregations=[
                AggregationClause(aggregation_type=AggregationType.COUNT)
            ]
        )
        assert obj_set.object_type == "Employee"
        assert obj_set.filters is not None
        assert obj_set.ordering is not None
        assert obj_set.limit == 100
        assert obj_set.aggregations is not None

    def test_to_foundry_dict_roundtrip(self):
        """to_foundry_dict / from_foundry_dict should roundtrip."""
        original = ObjectSetDefinition(
            object_type="Employee",
            filters=CombinedFilter(
                combinator=FilterCombinator.AND,
                filters=[
                    FilterCondition(
                        property_name="department",
                        operator=FilterOperatorType.EXACT_MATCH,
                        value="Engineering"
                    ),
                    FilterCondition(
                        property_name="salary",
                        operator=FilterOperatorType.RANGE_GTE,
                        value=100000
                    )
                ]
            ),
            ordering=[
                OrderByClause(property_name="salary", direction=OrderDirection.DESC)
            ],
            limit=50,
            aggregations=[
                AggregationClause(aggregation_type=AggregationType.COUNT)
            ]
        )

        dict_form = original.to_foundry_dict()
        restored = ObjectSetDefinition.from_foundry_dict(dict_form)

        assert restored.object_type == original.object_type
        assert restored.limit == original.limit
        assert len(restored.ordering) == len(original.ordering)
        assert len(restored.aggregations) == len(original.aggregations)

