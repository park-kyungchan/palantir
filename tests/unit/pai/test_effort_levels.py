"""
Unit Tests for PAI Algorithm Effort Levels
==========================================

Tests for the EffortLevel enum that controls algorithm behavior.
Validates enum construction, comparison operators, parsing, and properties.
"""

import pytest

try:
    from lib.oda.pai.algorithm.effort_levels import EffortLevel, EffortUnlocks
except ImportError:
    pytest.skip("PAI algorithm module not available", allow_module_level=True)


class TestEffortLevelEnumConstruction:
    """Tests for EffortLevel enum value construction."""

    def test_all_five_values_exist(self):
        """Verify all 5 effort levels are defined."""
        expected_values = {"TRIVIAL", "QUICK", "STANDARD", "THOROUGH", "DETERMINED"}
        actual_values = {e.value for e in EffortLevel}
        assert actual_values == expected_values

    @pytest.mark.parametrize(
        "level,expected_value",
        [
            (EffortLevel.TRIVIAL, "TRIVIAL"),
            (EffortLevel.QUICK, "QUICK"),
            (EffortLevel.STANDARD, "STANDARD"),
            (EffortLevel.THOROUGH, "THOROUGH"),
            (EffortLevel.DETERMINED, "DETERMINED"),
        ],
    )
    def test_enum_string_value(self, level: EffortLevel, expected_value: str):
        """Verify each enum has the correct string value."""
        assert level.value == expected_value

    def test_enum_is_str_subclass(self):
        """Verify EffortLevel inherits from str for JSON serialization."""
        assert isinstance(EffortLevel.STANDARD, str)
        assert EffortLevel.STANDARD == "STANDARD"


class TestEffortLevelRank:
    """Tests for the rank property."""

    @pytest.mark.parametrize(
        "level,expected_rank",
        [
            (EffortLevel.TRIVIAL, 0),
            (EffortLevel.QUICK, 1),
            (EffortLevel.STANDARD, 2),
            (EffortLevel.THOROUGH, 3),
            (EffortLevel.DETERMINED, 4),
        ],
    )
    def test_rank_returns_correct_value(self, level: EffortLevel, expected_rank: int):
        """Verify each effort level returns its correct numeric rank."""
        assert level.rank == expected_rank

    def test_ranks_are_unique(self):
        """Verify all ranks are unique across effort levels."""
        ranks = [e.rank for e in EffortLevel]
        assert len(ranks) == len(set(ranks))

    def test_ranks_are_sequential(self):
        """Verify ranks form a sequence from 0 to 4."""
        ranks = sorted([e.rank for e in EffortLevel])
        assert ranks == [0, 1, 2, 3, 4]


class TestEffortLevelComparison:
    """Tests for comparison operators (<, <=, >, >=)."""

    def test_less_than(self):
        """Test < operator between effort levels."""
        assert EffortLevel.TRIVIAL < EffortLevel.QUICK
        assert EffortLevel.QUICK < EffortLevel.STANDARD
        assert EffortLevel.STANDARD < EffortLevel.THOROUGH
        assert EffortLevel.THOROUGH < EffortLevel.DETERMINED

    def test_less_than_or_equal(self):
        """Test <= operator between effort levels."""
        assert EffortLevel.TRIVIAL <= EffortLevel.TRIVIAL
        assert EffortLevel.TRIVIAL <= EffortLevel.QUICK
        assert EffortLevel.STANDARD <= EffortLevel.STANDARD

    def test_greater_than(self):
        """Test > operator between effort levels."""
        assert EffortLevel.DETERMINED > EffortLevel.THOROUGH
        assert EffortLevel.THOROUGH > EffortLevel.STANDARD
        assert EffortLevel.STANDARD > EffortLevel.QUICK
        assert EffortLevel.QUICK > EffortLevel.TRIVIAL

    def test_greater_than_or_equal(self):
        """Test >= operator between effort levels."""
        assert EffortLevel.DETERMINED >= EffortLevel.DETERMINED
        assert EffortLevel.DETERMINED >= EffortLevel.TRIVIAL
        assert EffortLevel.STANDARD >= EffortLevel.STANDARD

    def test_comparison_with_non_effort_level_returns_not_implemented(self):
        """Test comparison operators return NotImplemented for non-EffortLevel types."""
        assert EffortLevel.STANDARD.__lt__("STANDARD") is NotImplemented
        assert EffortLevel.STANDARD.__le__(2) is NotImplemented
        assert EffortLevel.STANDARD.__gt__(None) is NotImplemented
        assert EffortLevel.STANDARD.__ge__([]) is NotImplemented

    @pytest.mark.parametrize(
        "lower,higher",
        [
            (EffortLevel.TRIVIAL, EffortLevel.QUICK),
            (EffortLevel.QUICK, EffortLevel.STANDARD),
            (EffortLevel.STANDARD, EffortLevel.THOROUGH),
            (EffortLevel.THOROUGH, EffortLevel.DETERMINED),
        ],
    )
    def test_hierarchy_ordering(self, lower: EffortLevel, higher: EffortLevel):
        """Verify effort level hierarchy is correctly ordered."""
        assert lower < higher
        assert higher > lower
        assert not (lower > higher)
        assert not (higher < lower)


class TestEffortLevelFromString:
    """Tests for from_string() class method."""

    @pytest.mark.parametrize(
        "input_str,expected_level",
        [
            ("TRIVIAL", EffortLevel.TRIVIAL),
            ("QUICK", EffortLevel.QUICK),
            ("STANDARD", EffortLevel.STANDARD),
            ("THOROUGH", EffortLevel.THOROUGH),
            ("DETERMINED", EffortLevel.DETERMINED),
        ],
    )
    def test_uppercase_parsing(self, input_str: str, expected_level: EffortLevel):
        """Test parsing uppercase strings."""
        assert EffortLevel.from_string(input_str) == expected_level

    @pytest.mark.parametrize(
        "input_str,expected_level",
        [
            ("trivial", EffortLevel.TRIVIAL),
            ("quick", EffortLevel.QUICK),
            ("standard", EffortLevel.STANDARD),
            ("thorough", EffortLevel.THOROUGH),
            ("determined", EffortLevel.DETERMINED),
        ],
    )
    def test_lowercase_parsing(self, input_str: str, expected_level: EffortLevel):
        """Test case-insensitive parsing with lowercase input."""
        assert EffortLevel.from_string(input_str) == expected_level

    @pytest.mark.parametrize(
        "input_str",
        ["Standard", "QuIcK", "ThoRouGH", "DeTeRmInEd"],
    )
    def test_mixed_case_parsing(self, input_str: str):
        """Test case-insensitive parsing with mixed case input."""
        result = EffortLevel.from_string(input_str)
        assert isinstance(result, EffortLevel)

    def test_invalid_string_raises_value_error(self):
        """Test that invalid strings raise ValueError with helpful message."""
        with pytest.raises(ValueError) as exc_info:
            EffortLevel.from_string("INVALID")

        error_message = str(exc_info.value)
        assert "Invalid effort level" in error_message
        assert "INVALID" in error_message
        assert "TRIVIAL" in error_message  # Valid values should be listed

    @pytest.mark.parametrize(
        "invalid_input",
        ["", "NORMAL", "HIGH", "LOW", "MEDIUM", "123", "trivial "],
    )
    def test_various_invalid_inputs(self, invalid_input: str):
        """Test various invalid inputs raise ValueError."""
        with pytest.raises(ValueError):
            EffortLevel.from_string(invalid_input)


class TestEffortLevelDefault:
    """Tests for default() class method."""

    def test_default_returns_standard(self):
        """Verify default() returns STANDARD effort level."""
        assert EffortLevel.default() == EffortLevel.STANDARD

    def test_default_returns_effort_level_instance(self):
        """Verify default() returns an EffortLevel instance."""
        result = EffortLevel.default()
        assert isinstance(result, EffortLevel)

    def test_default_is_middle_tier(self):
        """Verify default level is in the middle of the hierarchy."""
        default = EffortLevel.default()
        assert EffortLevel.TRIVIAL < default < EffortLevel.DETERMINED


class TestEffortLevelCanUse:
    """Tests for can_use() method - capability checking logic."""

    def test_same_level_can_use(self):
        """Test that a level can use capabilities at its own level."""
        assert EffortLevel.STANDARD.can_use(EffortLevel.STANDARD)
        assert EffortLevel.DETERMINED.can_use(EffortLevel.DETERMINED)
        assert EffortLevel.TRIVIAL.can_use(EffortLevel.TRIVIAL)

    def test_higher_level_can_use_lower_requirements(self):
        """Test that higher levels can use lower-requirement capabilities."""
        assert EffortLevel.DETERMINED.can_use(EffortLevel.TRIVIAL)
        assert EffortLevel.DETERMINED.can_use(EffortLevel.QUICK)
        assert EffortLevel.DETERMINED.can_use(EffortLevel.STANDARD)
        assert EffortLevel.DETERMINED.can_use(EffortLevel.THOROUGH)
        assert EffortLevel.THOROUGH.can_use(EffortLevel.STANDARD)
        assert EffortLevel.STANDARD.can_use(EffortLevel.QUICK)

    def test_lower_level_cannot_use_higher_requirements(self):
        """Test that lower levels cannot use higher-requirement capabilities."""
        assert not EffortLevel.TRIVIAL.can_use(EffortLevel.QUICK)
        assert not EffortLevel.TRIVIAL.can_use(EffortLevel.DETERMINED)
        assert not EffortLevel.QUICK.can_use(EffortLevel.STANDARD)
        assert not EffortLevel.STANDARD.can_use(EffortLevel.THOROUGH)
        assert not EffortLevel.THOROUGH.can_use(EffortLevel.DETERMINED)

    @pytest.mark.parametrize(
        "current_level,required_level,expected",
        [
            (EffortLevel.TRIVIAL, EffortLevel.TRIVIAL, True),
            (EffortLevel.QUICK, EffortLevel.TRIVIAL, True),
            (EffortLevel.STANDARD, EffortLevel.QUICK, True),
            (EffortLevel.THOROUGH, EffortLevel.STANDARD, True),
            (EffortLevel.DETERMINED, EffortLevel.THOROUGH, True),
            (EffortLevel.TRIVIAL, EffortLevel.QUICK, False),
            (EffortLevel.QUICK, EffortLevel.STANDARD, False),
            (EffortLevel.STANDARD, EffortLevel.THOROUGH, False),
            (EffortLevel.THOROUGH, EffortLevel.DETERMINED, False),
        ],
    )
    def test_can_use_parametrized(
        self, current_level: EffortLevel, required_level: EffortLevel, expected: bool
    ):
        """Parametrized test for can_use() with various level combinations."""
        assert current_level.can_use(required_level) == expected


class TestEffortLevelDescription:
    """Tests for description property."""

    @pytest.mark.parametrize(
        "level,expected_description",
        [
            (EffortLevel.TRIVIAL, "Skip algorithm, direct response"),
            (EffortLevel.QUICK, "Single-step, fast execution"),
            (EffortLevel.STANDARD, "Multi-step bounded work"),
            (EffortLevel.THOROUGH, "Complex, multi-file work"),
            (EffortLevel.DETERMINED, "Mission-critical, unlimited iteration"),
        ],
    )
    def test_description_content(self, level: EffortLevel, expected_description: str):
        """Verify each effort level has the correct description."""
        assert level.description == expected_description

    def test_all_descriptions_are_strings(self):
        """Verify all descriptions are non-empty strings."""
        for level in EffortLevel:
            assert isinstance(level.description, str)
            assert len(level.description) > 0

    def test_all_descriptions_are_unique(self):
        """Verify each effort level has a unique description."""
        descriptions = [e.description for e in EffortLevel]
        assert len(descriptions) == len(set(descriptions))


class TestEffortLevelMaxConcurrent:
    """Tests for max_concurrent property."""

    @pytest.mark.parametrize(
        "level,expected_concurrency",
        [
            (EffortLevel.TRIVIAL, 1),
            (EffortLevel.QUICK, 1),
            (EffortLevel.STANDARD, 3),
            (EffortLevel.THOROUGH, 5),
            (EffortLevel.DETERMINED, 10),
        ],
    )
    def test_max_concurrent_values(self, level: EffortLevel, expected_concurrency: int):
        """Verify each effort level has the correct concurrency limit."""
        assert level.max_concurrent == expected_concurrency

    def test_concurrency_increases_with_effort(self):
        """Verify concurrency limits generally increase with effort level."""
        levels = [
            EffortLevel.TRIVIAL,
            EffortLevel.QUICK,
            EffortLevel.STANDARD,
            EffortLevel.THOROUGH,
            EffortLevel.DETERMINED,
        ]
        concurrencies = [level.max_concurrent for level in levels]
        # Verify non-decreasing order
        for i in range(len(concurrencies) - 1):
            assert concurrencies[i] <= concurrencies[i + 1]

    def test_max_concurrent_is_positive_integer(self):
        """Verify all concurrency limits are positive integers."""
        for level in EffortLevel:
            assert isinstance(level.max_concurrent, int)
            assert level.max_concurrent >= 1

    def test_concurrency_within_documented_range(self):
        """Verify all concurrency values are within documented range (1-10)."""
        for level in EffortLevel:
            assert 1 <= level.max_concurrent <= 10


class TestEffortUnlocksTypeAlias:
    """Tests for the EffortUnlocks type alias."""

    def test_type_alias_is_defined(self):
        """Verify EffortUnlocks type alias is importable."""
        assert EffortUnlocks is not None

    def test_type_alias_accepts_valid_structure(self):
        """Verify EffortUnlocks can be used with proper structure."""
        unlocks: EffortUnlocks = {
            EffortLevel.TRIVIAL: ["direct_response"],
            EffortLevel.QUICK: ["haiku", "intern"],
            EffortLevel.STANDARD: ["sonnet", "researchers"],
        }
        assert isinstance(unlocks, dict)
        assert all(isinstance(k, EffortLevel) for k in unlocks.keys())
        assert all(isinstance(v, list) for v in unlocks.values())
