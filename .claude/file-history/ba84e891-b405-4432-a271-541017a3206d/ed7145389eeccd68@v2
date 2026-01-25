"""
Unit tests for Rules Engine type definitions.

Tests cover:
- InputSourceType (DATASET, OBJECT)
- LogicBoardType (FILTER_BOARD, AGGREGATION_BOARD, etc.)
- JoinType (INNER, LEFT, RIGHT, FULL)
- ActionRuleType (10 types of object/link operations)
- Logic Board models (FilterBoard, AggregationBoard, JoinBoard, etc.)
- RuleInputSource and RuleOutput
- FoundryRule (main rule definition)
- Serialization (to_foundry_dict / from_foundry_dict roundtrip)
"""

import pytest

from ontology_definition.types import (
    FoundryRule,
    RuleInputSource,
    RuleOutput,
    LogicBoardType,
    InputSourceType,
    JoinType,
    ActionRuleType,
    FilterBoard,
    AggregationBoard,
    JoinBoard,
    ExpressionBoard,
    WindowBoard,
    SelectColumnsBoard,
    UnionBoard,
)


class TestInputSourceType:
    """Tests for InputSourceType enum."""

    def test_dataset_source(self):
        """DATASET source type."""
        assert InputSourceType.DATASET.value == "DATASET"

    def test_object_source(self):
        """OBJECT source type."""
        assert InputSourceType.OBJECT.value == "OBJECT"


class TestLogicBoardType:
    """Tests for LogicBoardType enum."""

    def test_all_board_types(self):
        """All logic board types should be available."""
        assert LogicBoardType.FILTER_BOARD.value == "FILTER_BOARD"
        assert LogicBoardType.AGGREGATION_BOARD.value == "AGGREGATION_BOARD"
        assert LogicBoardType.JOIN_BOARD.value == "JOIN_BOARD"
        assert LogicBoardType.EXPRESSION_BOARD.value == "EXPRESSION_BOARD"
        assert LogicBoardType.WINDOW_BOARD.value == "WINDOW_BOARD"
        assert LogicBoardType.SELECT_COLUMNS_BOARD.value == "SELECT_COLUMNS_BOARD"
        assert LogicBoardType.UNION_BOARD.value == "UNION_BOARD"


class TestJoinType:
    """Tests for JoinType enum."""

    def test_all_join_types(self):
        """All SQL join types should be available."""
        assert JoinType.INNER.value == "INNER"
        assert JoinType.LEFT.value == "LEFT"
        assert JoinType.RIGHT.value == "RIGHT"
        assert JoinType.FULL.value == "FULL"


class TestActionRuleType:
    """Tests for ActionRuleType enum."""

    def test_object_operations(self):
        """Object operation action rule types."""
        assert ActionRuleType.CREATE_OBJECT.value == "createObject"
        assert ActionRuleType.MODIFY_OBJECT.value == "modifyObject"
        assert ActionRuleType.CREATE_OR_MODIFY_OBJECT.value == "createOrModifyObject"
        assert ActionRuleType.DELETE_OBJECT.value == "deleteObject"

    def test_link_operations(self):
        """Link operation action rule types."""
        assert ActionRuleType.CREATE_LINK.value == "createLink"
        assert ActionRuleType.DELETE_LINK.value == "deleteLink"

    def test_function_rule(self):
        """Function rule type."""
        assert ActionRuleType.FUNCTION_RULE.value == "functionRule"

    def test_interface_operations(self):
        """Interface operation action rule types."""
        assert ActionRuleType.CREATE_OBJECT_OF_INTERFACE.value == "createObjectOfInterface"
        assert ActionRuleType.MODIFY_OBJECT_OF_INTERFACE.value == "modifyObjectOfInterface"
        assert ActionRuleType.DELETE_OBJECT_OF_INTERFACE.value == "deleteObjectOfInterface"

    def test_is_exclusive_property(self):
        """FUNCTION_RULE should be exclusive."""
        assert ActionRuleType.FUNCTION_RULE.is_exclusive is True
        assert ActionRuleType.CREATE_OBJECT.is_exclusive is False

    def test_affects_objects_property(self):
        """Object operations should affect objects."""
        assert ActionRuleType.CREATE_OBJECT.affects_objects is True
        assert ActionRuleType.MODIFY_OBJECT.affects_objects is True
        assert ActionRuleType.CREATE_LINK.affects_objects is False

    def test_affects_links_property(self):
        """Link operations should affect links."""
        assert ActionRuleType.CREATE_LINK.affects_links is True
        assert ActionRuleType.DELETE_LINK.affects_links is True
        assert ActionRuleType.CREATE_OBJECT.affects_links is False


class TestRuleInputSource:
    """Tests for RuleInputSource - input source definition."""

    def test_dataset_input(self):
        """Dataset input source."""
        source = RuleInputSource(
            source_type=InputSourceType.DATASET,
            source="ri.foundry.main.dataset.abc123"
        )
        assert source.source_type == InputSourceType.DATASET
        assert source.source.startswith("ri.foundry")

    def test_object_input(self):
        """Object input source."""
        source = RuleInputSource(
            source_type=InputSourceType.OBJECT,
            source="Employee"
        )
        assert source.source_type == InputSourceType.OBJECT
        assert source.source == "Employee"

    def test_with_alias(self):
        """Input source with alias."""
        source = RuleInputSource(
            source_type=InputSourceType.OBJECT,
            source="Employee",
            alias="emp"
        )
        assert source.alias == "emp"

    def test_to_foundry_dict(self):
        """Export to Foundry dictionary format."""
        source = RuleInputSource(
            source_type=InputSourceType.OBJECT,
            source="Employee",
            alias="emp"
        )
        result = source.to_foundry_dict()
        assert result == {
            "type": "OBJECT",
            "source": "Employee",
            "alias": "emp"
        }

    def test_from_foundry_dict(self):
        """Create from Foundry dictionary format."""
        data = {
            "type": "DATASET",
            "source": "ri.foundry.main.dataset.xyz789"
        }
        source = RuleInputSource.from_foundry_dict(data)
        assert source.source_type == InputSourceType.DATASET


class TestFilterBoard:
    """Tests for FilterBoard - row-level filtering."""

    def test_basic_filter_board(self):
        """Basic filter board with conditions."""
        board = FilterBoard(
            conditions=[
                {"field": "salary", "op": "gt", "value": 100000}
            ]
        )
        assert len(board.conditions) == 1

    def test_to_foundry_dict(self):
        """Export to Foundry dictionary format."""
        board = FilterBoard(conditions=[{"field": "status", "op": "eq", "value": "active"}])
        result = board.to_foundry_dict()
        assert "conditions" in result


class TestAggregationBoard:
    """Tests for AggregationBoard - grouping and aggregation."""

    def test_basic_aggregation(self):
        """Basic aggregation board."""
        board = AggregationBoard(
            group_by=["department"],
            aggregations={
                "total_employees": "COUNT(*)",
                "avg_salary": "AVG(salary)"
            }
        )
        assert board.group_by == ["department"]
        assert "total_employees" in board.aggregations

    def test_to_foundry_dict(self):
        """Export to Foundry dictionary format."""
        board = AggregationBoard(
            group_by=["region"],
            aggregations={"count": "COUNT(*)"}
        )
        result = board.to_foundry_dict()
        assert result["groupBy"] == ["region"]

    def test_from_foundry_dict(self):
        """Create from Foundry dictionary format."""
        data = {
            "groupBy": ["department", "year"],
            "aggregations": {"total": "SUM(amount)"}
        }
        board = AggregationBoard.from_foundry_dict(data)
        assert board.group_by == ["department", "year"]


class TestJoinBoard:
    """Tests for JoinBoard - join operations."""

    def test_inner_join(self):
        """Inner join board."""
        board = JoinBoard(
            join_type=JoinType.INNER,
            join_dataset="ri.foundry.main.dataset.xyz789",
            join_conditions=["left.employeeId = right.managerId"]
        )
        assert board.join_type == JoinType.INNER
        assert len(board.join_conditions) == 1

    def test_left_join(self):
        """Left join board."""
        board = JoinBoard(
            join_type=JoinType.LEFT,
            join_dataset="ri.foundry.main.dataset.abc123",
            join_conditions=["left.id = right.foreign_id"]
        )
        assert board.join_type == JoinType.LEFT

    def test_to_foundry_dict(self):
        """Export to Foundry dictionary format."""
        board = JoinBoard(
            join_type=JoinType.FULL,
            join_dataset="ri.foundry.main.dataset.test",
            join_conditions=["a = b"]
        )
        result = board.to_foundry_dict()
        assert result["joinType"] == "FULL"


class TestExpressionBoard:
    """Tests for ExpressionBoard - computed columns."""

    def test_basic_expressions(self):
        """Basic expression board."""
        board = ExpressionBoard(
            expressions={
                "full_name": "firstName || ' ' || lastName",
                "annual_salary": "salary * 12"
            }
        )
        assert "full_name" in board.expressions
        assert "annual_salary" in board.expressions

    def test_to_foundry_dict(self):
        """Export to Foundry dictionary format."""
        board = ExpressionBoard(expressions={"total": "a + b"})
        result = board.to_foundry_dict()
        assert result["expressions"]["total"] == "a + b"


class TestWindowBoard:
    """Tests for WindowBoard - window functions."""

    def test_basic_window(self):
        """Basic window board."""
        board = WindowBoard(
            partition_by=["department"],
            order_by=["salary DESC"],
            window_function="ROW_NUMBER()"
        )
        assert board.partition_by == ["department"]
        assert board.window_function == "ROW_NUMBER()"

    def test_to_foundry_dict(self):
        """Export to Foundry dictionary format."""
        board = WindowBoard(
            partition_by=["region"],
            order_by=["date ASC"],
            window_function="RANK()"
        )
        result = board.to_foundry_dict()
        assert result["partitionBy"] == ["region"]
        assert result["windowFunction"] == "RANK()"


class TestSelectColumnsBoard:
    """Tests for SelectColumnsBoard - column projection."""

    def test_select_columns(self):
        """Basic column selection."""
        board = SelectColumnsBoard(
            columns=["employeeId", "employeeName", "department"]
        )
        assert len(board.columns) == 3

    def test_to_foundry_dict(self):
        """Export to Foundry dictionary format."""
        board = SelectColumnsBoard(columns=["id", "name"])
        result = board.to_foundry_dict()
        assert result["columns"] == ["id", "name"]


class TestUnionBoard:
    """Tests for UnionBoard - combining datasets."""

    def test_basic_union(self):
        """Basic union board."""
        board = UnionBoard(
            datasets=[
                "ri.foundry.main.dataset.abc123",
                "ri.foundry.main.dataset.def456"
            ]
        )
        assert len(board.datasets) == 2

    def test_to_foundry_dict(self):
        """Export to Foundry dictionary format."""
        board = UnionBoard(datasets=["ds1", "ds2", "ds3"])
        result = board.to_foundry_dict()
        assert len(result["datasets"]) == 3


class TestRuleOutput:
    """Tests for RuleOutput - output configuration."""

    def test_basic_output(self):
        """Basic rule output."""
        output = RuleOutput(
            dataset="ri.foundry.main.dataset.output123",
            output_schema=[
                {"name": "employeeId", "type": "STRING"},
                {"name": "alertMessage", "type": "STRING"}
            ]
        )
        assert output.dataset.startswith("ri.foundry")
        assert len(output.output_schema) == 2

    def test_to_foundry_dict(self):
        """Export to Foundry dictionary format."""
        output = RuleOutput(
            dataset="ri.foundry.main.dataset.test",
            output_schema=[{"name": "id", "type": "INTEGER"}]
        )
        result = output.to_foundry_dict()
        assert result["dataset"] == "ri.foundry.main.dataset.test"
        assert result["schema"] == [{"name": "id", "type": "INTEGER"}]


class TestFoundryRule:
    """Tests for FoundryRule - complete rule definition."""

    def test_basic_rule(self):
        """Basic Foundry rule."""
        rule = FoundryRule(
            inputs=[
                RuleInputSource(
                    source_type=InputSourceType.OBJECT,
                    source="Employee"
                )
            ],
            logic_blocks=[
                {
                    "type": "FILTER_BOARD",
                    "conditions": [{"field": "status", "op": "eq", "value": "active"}]
                }
            ],
            output=RuleOutput(
                dataset="ri.foundry.main.dataset.filtered_employees",
                output_schema=[
                    {"name": "employeeId", "type": "STRING"},
                    {"name": "employeeName", "type": "STRING"}
                ]
            )
        )
        assert len(rule.inputs) == 1
        assert len(rule.logic_blocks) == 1

    def test_rule_with_action_rules(self):
        """Rule with action rules."""
        rule = FoundryRule(
            inputs=[
                RuleInputSource(
                    source_type=InputSourceType.DATASET,
                    source="ri.foundry.main.dataset.source"
                )
            ],
            logic_blocks=[],
            output=RuleOutput(
                dataset="ri.foundry.main.dataset.output",
                output_schema=[]
            ),
            action_rules=[
                ActionRuleType.CREATE_OBJECT,
                ActionRuleType.MODIFY_OBJECT
            ]
        )
        assert len(rule.action_rules) == 2

    def test_rule_with_multiple_inputs(self):
        """Rule with multiple input sources."""
        rule = FoundryRule(
            inputs=[
                RuleInputSource(
                    source_type=InputSourceType.OBJECT,
                    source="Employee",
                    alias="emp"
                ),
                RuleInputSource(
                    source_type=InputSourceType.OBJECT,
                    source="Department",
                    alias="dept"
                )
            ],
            logic_blocks=[
                {
                    "type": "JOIN_BOARD",
                    "joinType": "INNER",
                    "joinConditions": ["emp.departmentId = dept.id"]
                }
            ],
            output=RuleOutput(
                dataset="ri.foundry.main.dataset.joined",
                output_schema=[]
            )
        )
        assert len(rule.inputs) == 2

    def test_to_foundry_dict_roundtrip(self):
        """to_foundry_dict / from_foundry_dict should roundtrip."""
        original = FoundryRule(
            inputs=[
                RuleInputSource(
                    source_type=InputSourceType.OBJECT,
                    source="Employee"
                )
            ],
            logic_blocks=[
                {
                    "type": "FILTER_BOARD",
                    "conditions": [{"field": "salary", "op": "gt", "value": 50000}]
                },
                {
                    "type": "AGGREGATION_BOARD",
                    "groupBy": ["department"],
                    "aggregations": {"count": "COUNT(*)"}
                }
            ],
            output=RuleOutput(
                dataset="ri.foundry.main.dataset.high_earners",
                output_schema=[
                    {"name": "department", "type": "STRING"},
                    {"name": "count", "type": "INTEGER"}
                ]
            ),
            action_rules=[ActionRuleType.CREATE_OBJECT]
        )

        dict_form = original.to_foundry_dict()
        restored = FoundryRule.from_foundry_dict(dict_form)

        assert len(restored.inputs) == len(original.inputs)
        assert len(restored.logic_blocks) == len(original.logic_blocks)
        assert restored.output.dataset == original.output.dataset
        assert len(restored.action_rules) == len(original.action_rules)

