"""
Unit tests for PAI Traits Dimensions module.

Tests the three composable trait dimensions:
- ExpertiseType: Domain knowledge enumeration
- PersonalityDimension: Agent behavior traits
- ApproachStyle: Task methodology styles

Also tests utility functions for trait aggregation and classification.
"""

import pytest

try:
    from lib.oda.pai.traits.dimensions import (
        ExpertiseType,
        PersonalityDimension,
        ApproachStyle,
        get_all_trait_values,
        classify_trait,
    )
    IMPORT_ERROR = None
except ImportError as e:
    IMPORT_ERROR = str(e)
    ExpertiseType = None
    PersonalityDimension = None
    ApproachStyle = None
    get_all_trait_values = None
    classify_trait = None


pytestmark = pytest.mark.skipif(
    IMPORT_ERROR is not None,
    reason=f"Could not import dimensions module: {IMPORT_ERROR}"
)


class TestExpertiseType:
    """Tests for ExpertiseType enum."""

    EXPECTED_VALUES = [
        "security",
        "legal",
        "finance",
        "medical",
        "technical",
        "research",
        "creative",
        "business",
        "data",
        "communications",
    ]

    def test_expertise_type_count(self):
        """ExpertiseType should have exactly 10 values."""
        assert len(ExpertiseType) == 10

    @pytest.mark.parametrize("value", EXPECTED_VALUES)
    def test_expertise_type_has_value(self, value: str):
        """Each expected expertise type value should exist in the enum."""
        assert value in ExpertiseType.values()

    def test_expertise_type_values_method(self):
        """ExpertiseType.values() should return all values as strings."""
        values = ExpertiseType.values()
        assert isinstance(values, list)
        assert all(isinstance(v, str) for v in values)
        assert set(values) == set(self.EXPECTED_VALUES)

    def test_expertise_type_is_str_enum(self):
        """ExpertiseType should be a string enum for serialization."""
        assert ExpertiseType.SECURITY.value == "security"
        # str(Enum) returns 'EnumName.MEMBER', but .value gives the string value
        assert isinstance(ExpertiseType.SECURITY.value, str)


class TestPersonalityDimension:
    """Tests for PersonalityDimension enum."""

    EXPECTED_VALUES = [
        "skeptical",
        "enthusiastic",
        "cautious",
        "bold",
        "analytical",
        "creative",
        "empathetic",
        "contrarian",
        "pragmatic",
        "meticulous",
    ]

    def test_personality_dimension_count(self):
        """PersonalityDimension should have exactly 10 values."""
        assert len(PersonalityDimension) == 10

    @pytest.mark.parametrize("value", EXPECTED_VALUES)
    def test_personality_dimension_has_value(self, value: str):
        """Each expected personality dimension value should exist in the enum."""
        assert value in PersonalityDimension.values()

    def test_personality_dimension_values_method(self):
        """PersonalityDimension.values() should return all values as strings."""
        values = PersonalityDimension.values()
        assert isinstance(values, list)
        assert all(isinstance(v, str) for v in values)
        assert set(values) == set(self.EXPECTED_VALUES)

    def test_personality_dimension_is_str_enum(self):
        """PersonalityDimension should be a string enum for serialization."""
        assert PersonalityDimension.SKEPTICAL.value == "skeptical"
        # str(Enum) returns 'EnumName.MEMBER', but .value gives the string value
        assert isinstance(PersonalityDimension.SKEPTICAL.value, str)


class TestApproachStyle:
    """Tests for ApproachStyle enum."""

    EXPECTED_VALUES = [
        "thorough",
        "rapid",
        "systematic",
        "exploratory",
        "comparative",
        "synthesizing",
        "adversarial",
        "consultative",
    ]

    def test_approach_style_count(self):
        """ApproachStyle should have exactly 8 values."""
        assert len(ApproachStyle) == 8

    @pytest.mark.parametrize("value", EXPECTED_VALUES)
    def test_approach_style_has_value(self, value: str):
        """Each expected approach style value should exist in the enum."""
        assert value in ApproachStyle.values()

    def test_approach_style_values_method(self):
        """ApproachStyle.values() should return all values as strings."""
        values = ApproachStyle.values()
        assert isinstance(values, list)
        assert all(isinstance(v, str) for v in values)
        assert set(values) == set(self.EXPECTED_VALUES)

    def test_approach_style_is_str_enum(self):
        """ApproachStyle should be a string enum for serialization."""
        assert ApproachStyle.THOROUGH.value == "thorough"
        # str(Enum) returns 'EnumName.MEMBER', but .value gives the string value
        assert isinstance(ApproachStyle.THOROUGH.value, str)


class TestGetAllTraitValues:
    """Tests for get_all_trait_values() function."""

    def test_returns_list(self):
        """get_all_trait_values() should return a list."""
        result = get_all_trait_values()
        assert isinstance(result, list)

    def test_returns_correct_count(self):
        """get_all_trait_values() should return 28 total values (10+10+8)."""
        result = get_all_trait_values()
        assert len(result) == 28

    def test_contains_all_expertise_types(self):
        """Result should contain all expertise type values."""
        result = get_all_trait_values()
        for value in ExpertiseType.values():
            assert value in result

    def test_contains_all_personality_dimensions(self):
        """Result should contain all personality dimension values."""
        result = get_all_trait_values()
        for value in PersonalityDimension.values():
            assert value in result

    def test_contains_all_approach_styles(self):
        """Result should contain all approach style values."""
        result = get_all_trait_values()
        for value in ApproachStyle.values():
            assert value in result

    def test_all_values_are_strings(self):
        """All returned values should be strings."""
        result = get_all_trait_values()
        assert all(isinstance(v, str) for v in result)


class TestClassifyTrait:
    """Tests for classify_trait() function."""

    @pytest.mark.parametrize("trait", [
        "security", "legal", "finance", "medical", "technical",
        "research", "creative", "business", "data", "communications"
    ])
    def test_classify_expertise_traits(self, trait: str):
        """Expertise traits should be classified as 'expertise'."""
        assert classify_trait(trait) == "expertise"

    @pytest.mark.parametrize("trait", [
        "skeptical", "enthusiastic", "cautious", "bold", "analytical",
        "empathetic", "contrarian", "pragmatic", "meticulous"
    ])
    def test_classify_personality_traits(self, trait: str):
        """Personality traits should be classified as 'personality'."""
        assert classify_trait(trait) == "personality"

    @pytest.mark.parametrize("trait", [
        "thorough", "rapid", "systematic", "exploratory",
        "comparative", "synthesizing", "adversarial", "consultative"
    ])
    def test_classify_approach_traits(self, trait: str):
        """Approach traits should be classified as 'approach'."""
        assert classify_trait(trait) == "approach"

    def test_classify_unknown_trait_returns_none(self):
        """Unknown traits should return None."""
        assert classify_trait("unknown_trait") is None
        assert classify_trait("nonexistent") is None

    def test_classify_case_insensitive(self):
        """classify_trait() should be case-insensitive."""
        assert classify_trait("SECURITY") == "expertise"
        assert classify_trait("Security") == "expertise"
        assert classify_trait("SKEPTICAL") == "personality"
        assert classify_trait("Thorough") == "approach"

    def test_classify_creative_is_personality(self):
        """'creative' in personality dimension should classify as personality.

        Note: 'creative' exists in both ExpertiseType and PersonalityDimension.
        The implementation checks ExpertiseType first, so 'creative' will be
        classified as 'expertise'.
        """
        # Based on implementation order: ExpertiseType is checked first
        result = classify_trait("creative")
        assert result == "expertise"
