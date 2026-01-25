"""
ObjectSet Type Definitions for Ontology.

ObjectSet represents an unordered collection of objects of a single type.
Supports filtering, set operations, aggregations, and traversal operations.

This module provides:
    - FilterOperator: All filter operators by type category
    - SetOperation: Union, intersect, subtract operations
    - AggregationType: count, average, max, min, sum, cardinality
    - FilterCondition: Single filter condition definition
    - ObjectSetDefinition: Complete object set query definition

Reference: docs/Ontology.md Section 7
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


class FilterOperatorType(str, Enum):
    """
    Filter operators supported by ObjectSet.

    Categorized by data type compatibility:
    - all_types: exactMatch, hasProperty
    - string: phrase, phrasePrefix, matchAnyToken, etc.
    - numeric_date: range().lt/lte/gt/gte
    - boolean: isTrue, isFalse
    - geo: withinDistanceOf, withinPolygon, withinBoundingBox
    - array: contains
    - link: isPresent
    """

    # All types
    EXACT_MATCH = "exactMatch"
    HAS_PROPERTY = "hasProperty"

    # String operators
    PHRASE = "phrase"
    PHRASE_PREFIX = "phrasePrefix"
    MATCH_ANY_TOKEN = "matchAnyToken"
    MATCH_ALL_TOKENS = "matchAllTokens"
    FUZZY_MATCH_ANY_TOKEN = "fuzzyMatchAnyToken"
    FUZZY_MATCH_ALL_TOKENS = "fuzzyMatchAllTokens"

    # Numeric/Date range operators
    RANGE_LT = "range.lt"
    RANGE_LTE = "range.lte"
    RANGE_GT = "range.gt"
    RANGE_GTE = "range.gte"

    # Boolean operators
    IS_TRUE = "isTrue"
    IS_FALSE = "isFalse"

    # Geo operators
    WITHIN_DISTANCE_OF = "withinDistanceOf"
    WITHIN_POLYGON = "withinPolygon"
    WITHIN_BOUNDING_BOX = "withinBoundingBox"

    # Array operators
    CONTAINS = "contains"

    # Link operators
    IS_PRESENT = "isPresent"


class SetOperation(str, Enum):
    """
    Set operations for combining ObjectSets.

    - UNION: Objects in any set (SQL UNION)
    - INTERSECT: Objects in all sets (SQL INTERSECT)
    - SUBTRACT: Remove objects from first set (SQL EXCEPT)
    """

    UNION = "union"
    INTERSECT = "intersect"
    SUBTRACT = "subtract"


class AggregationType(str, Enum):
    """
    Aggregation operations on ObjectSet.

    - COUNT: Count of objects
    - AVERAGE: Average value of property
    - MAX: Maximum value of property
    - MIN: Minimum value of property
    - SUM: Sum of property values
    - CARDINALITY: Distinct count of property values
    """

    COUNT = "count"
    AVERAGE = "average"
    MAX = "max"
    MIN = "min"
    SUM = "sum"
    CARDINALITY = "cardinality"


class FilterCombinator(str, Enum):
    """
    Filter combination operators.

    - AND: All filters must pass
    - OR: Any filter passes
    - NOT: Negate filter result
    """

    AND = "and"
    OR = "or"
    NOT = "not"


class OrderDirection(str, Enum):
    """
    Ordering direction for results.

    - ASC: Ascending order
    - DESC: Descending order
    - RELEVANCE: Order by search relevance
    """

    ASC = "asc"
    DESC = "desc"
    RELEVANCE = "relevance"


class FilterCondition(BaseModel):
    """
    Single filter condition for ObjectSet.

    Represents a single filter operation on a property:
    - property_name: Target property apiName
    - operator: Filter operator type
    - value: Filter value (optional for operators like hasProperty)
    - parameters: Additional parameters (e.g., maxEdits for fuzzy match)

    Examples:
        # exactMatch
        FilterCondition(
            property_name="employeeId",
            operator=FilterOperatorType.EXACT_MATCH,
            value="E12345"
        )

        # range filter
        FilterCondition(
            property_name="salary",
            operator=FilterOperatorType.RANGE_GTE,
            value=50000
        )

        # fuzzy match
        FilterCondition(
            property_name="name",
            operator=FilterOperatorType.FUZZY_MATCH_ANY_TOKEN,
            value="John",
            parameters={"maxEdits": 2}
        )
    """

    property_name: str = Field(
        ...,
        description="Property apiName to filter on.",
        alias="propertyName",
    )

    operator: FilterOperatorType = Field(
        ...,
        description="Filter operator to apply.",
    )

    value: Optional[Any] = Field(
        default=None,
        description="Filter value. Optional for operators like hasProperty.",
    )

    parameters: Optional[dict[str, Any]] = Field(
        default=None,
        description="Additional operator parameters (e.g., maxEdits, distance).",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {
            "propertyName": self.property_name,
            "operator": self.operator.value,
        }

        if self.value is not None:
            result["value"] = self.value

        if self.parameters:
            result["parameters"] = self.parameters

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "FilterCondition":
        """Create from Foundry JSON format."""
        return cls(
            property_name=data["propertyName"],
            operator=FilterOperatorType(data["operator"]),
            value=data.get("value"),
            parameters=data.get("parameters"),
        )


class CombinedFilter(BaseModel):
    """
    Combined filter using AND/OR/NOT operators.

    Allows complex filter combinations:
    - combinator: AND/OR/NOT
    - filters: List of FilterCondition or nested CombinedFilter

    Examples:
        # AND filter
        CombinedFilter(
            combinator=FilterCombinator.AND,
            filters=[
                FilterCondition(...),
                FilterCondition(...)
            ]
        )

        # Nested: (A AND B) OR C
        CombinedFilter(
            combinator=FilterCombinator.OR,
            filters=[
                CombinedFilter(combinator=FilterCombinator.AND, filters=[A, B]),
                C
            ]
        )
    """

    combinator: FilterCombinator = Field(
        ...,
        description="Combination operator: AND, OR, or NOT.",
    )

    filters: list[Union[FilterCondition, "CombinedFilter"]] = Field(
        ...,
        description="List of filter conditions or nested combined filters.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        return {
            "combinator": self.combinator.value,
            "filters": [
                f.to_foundry_dict() if hasattr(f, "to_foundry_dict") else f
                for f in self.filters
            ],
        }

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "CombinedFilter":
        """Create from Foundry JSON format."""
        filters = []
        for f_data in data["filters"]:
            if "combinator" in f_data:
                filters.append(cls.from_foundry_dict(f_data))
            else:
                filters.append(FilterCondition.from_foundry_dict(f_data))

        return cls(
            combinator=FilterCombinator(data["combinator"]),
            filters=filters,
        )


class OrderByClause(BaseModel):
    """
    Ordering specification for ObjectSet results.

    - property_name: Property to order by
    - direction: ASC, DESC, or RELEVANCE

    Example:
        OrderByClause(
            property_name="employeeName",
            direction=OrderDirection.ASC
        )
    """

    property_name: Optional[str] = Field(
        default=None,
        description="Property apiName to order by. Not required for RELEVANCE.",
        alias="propertyName",
    )

    direction: OrderDirection = Field(
        default=OrderDirection.ASC,
        description="Ordering direction: ASC, DESC, or RELEVANCE.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {"direction": self.direction.value}

        if self.property_name:
            result["propertyName"] = self.property_name

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "OrderByClause":
        """Create from Foundry JSON format."""
        return cls(
            property_name=data.get("propertyName"),
            direction=OrderDirection(data["direction"]),
        )


class AggregationClause(BaseModel):
    """
    Aggregation operation on ObjectSet.

    - aggregation_type: Type of aggregation (count, average, max, etc.)
    - property_name: Property to aggregate on (not required for count)

    Examples:
        # Count
        AggregationClause(aggregation_type=AggregationType.COUNT)

        # Average
        AggregationClause(
            aggregation_type=AggregationType.AVERAGE,
            property_name="salary"
        )
    """

    aggregation_type: AggregationType = Field(
        ...,
        description="Type of aggregation operation.",
        alias="aggregationType",
    )

    property_name: Optional[str] = Field(
        default=None,
        description="Property to aggregate on. Not required for COUNT.",
        alias="propertyName",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {"aggregationType": self.aggregation_type.value}

        if self.property_name:
            result["propertyName"] = self.property_name

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "AggregationClause":
        """Create from Foundry JSON format."""
        return cls(
            aggregation_type=AggregationType(data["aggregationType"]),
            property_name=data.get("propertyName"),
        )


class ObjectSetDefinition(BaseModel):
    """
    Complete ObjectSet query definition.

    Defines a complete object set query with:
    - object_type: Target ObjectType apiName
    - filters: Filter conditions (single or combined)
    - set_operations: Union/intersect/subtract with other sets
    - ordering: Order by clauses
    - limit: Result limit (max 100,000 for all())
    - aggregations: Aggregation operations

    Example:
        # Find high-salary employees in engineering
        ObjectSetDefinition(
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
                OrderByClause(
                    property_name="salary",
                    direction=OrderDirection.DESC
                )
            ],
            limit=100
        )
    """

    object_type: str = Field(
        ...,
        description="Target ObjectType apiName.",
        alias="objectType",
    )

    filters: Optional[Union[FilterCondition, CombinedFilter]] = Field(
        default=None,
        description="Filter conditions (single or combined).",
    )

    set_operations: Optional[list[dict[str, Any]]] = Field(
        default=None,
        description="Set operations (union, intersect, subtract) with other sets.",
        alias="setOperations",
    )

    ordering: Optional[list[OrderByClause]] = Field(
        default=None,
        description="Ordering specifications.",
    )

    limit: Optional[int] = Field(
        default=None,
        description="Result limit. Max 100,000 for all().",
        ge=1,
        le=100000,
    )

    aggregations: Optional[list[AggregationClause]] = Field(
        default=None,
        description="Aggregation operations.",
    )

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    def to_foundry_dict(self) -> dict[str, Any]:
        """Export to Foundry-compatible dictionary format."""
        result: dict[str, Any] = {"objectType": self.object_type}

        if self.filters:
            result["filters"] = self.filters.to_foundry_dict()

        if self.set_operations:
            result["setOperations"] = self.set_operations

        if self.ordering:
            result["ordering"] = [o.to_foundry_dict() for o in self.ordering]

        if self.limit is not None:
            result["limit"] = self.limit

        if self.aggregations:
            result["aggregations"] = [a.to_foundry_dict() for a in self.aggregations]

        return result

    @classmethod
    def from_foundry_dict(cls, data: dict[str, Any]) -> "ObjectSetDefinition":
        """Create from Foundry JSON format."""
        filters = None
        if data.get("filters"):
            filter_data = data["filters"]
            if "combinator" in filter_data:
                filters = CombinedFilter.from_foundry_dict(filter_data)
            else:
                filters = FilterCondition.from_foundry_dict(filter_data)

        ordering = None
        if data.get("ordering"):
            ordering = [OrderByClause.from_foundry_dict(o) for o in data["ordering"]]

        aggregations = None
        if data.get("aggregations"):
            aggregations = [
                AggregationClause.from_foundry_dict(a) for a in data["aggregations"]
            ]

        return cls(
            object_type=data["objectType"],
            filters=filters,
            set_operations=data.get("setOperations"),
            ordering=ordering,
            limit=data.get("limit"),
            aggregations=aggregations,
        )


# Update forward references
CombinedFilter.model_rebuild()
