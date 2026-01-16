"""
Orion ODA v3.0 - Trigger Detection Engine
PAI Prompting Skill Migration - Phase 4

This module implements the keyword-based routing logic for skill activation.
It provides the TriggerDetector class that matches user input against
registered triggers using a priority-based algorithm.

Trigger Detection Algorithm (Priority Order):
1. Exact keyword match
2. Pattern regex match
3. Context similarity (if context_match defined)
4. Default skill or None

All detection operations are logged for audit compliance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from lib.oda.pai.skills.skill_definition import (
    SkillDefinition,
    SkillTrigger,
    TriggerPriority,
)


# =============================================================================
# ENUMS AND TYPES
# =============================================================================

class MatchType(str, Enum):
    """Type of trigger match that occurred."""
    EXACT_KEYWORD = "exact_keyword"
    PATTERN_MATCH = "pattern_match"
    CONTEXT_SIMILARITY = "context_similarity"
    DEFAULT_SKILL = "default_skill"
    NO_MATCH = "no_match"


@dataclass
class TriggerMatch:
    """
    Result of a trigger detection operation.

    Attributes:
        matched: Whether a match was found
        match_type: Type of match that occurred
        trigger: The matched trigger (if any)
        skill_definition_id: ID of the matched skill
        skill_name: Name of the matched skill
        confidence: Match confidence score (0.0 - 1.0)
        matched_value: The specific keyword/pattern that matched
        all_matches: All potential matches found (for debugging)
    """
    matched: bool = False
    match_type: MatchType = MatchType.NO_MATCH
    trigger: Optional[SkillTrigger] = None
    skill_definition_id: Optional[str] = None
    skill_name: Optional[str] = None
    confidence: float = 0.0
    matched_value: Optional[str] = None
    all_matches: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "matched": self.matched,
            "match_type": self.match_type.value,
            "trigger_id": self.trigger.id if self.trigger else None,
            "skill_definition_id": self.skill_definition_id,
            "skill_name": self.skill_name,
            "confidence": self.confidence,
            "matched_value": self.matched_value,
            "all_matches_count": len(self.all_matches),
        }


@dataclass
class DetectorConfig:
    """
    Configuration for the TriggerDetector.

    Attributes:
        enable_context_matching: Whether to use context similarity matching
        context_similarity_threshold: Minimum similarity score for context match
        max_matches_to_return: Maximum number of matches to track
        case_sensitive_default: Default case sensitivity for matching
        enable_fuzzy_matching: Enable fuzzy keyword matching
        fuzzy_threshold: Minimum similarity for fuzzy matches (0.0 - 1.0)
    """
    enable_context_matching: bool = True
    context_similarity_threshold: float = 0.7
    max_matches_to_return: int = 5
    case_sensitive_default: bool = False
    enable_fuzzy_matching: bool = False
    fuzzy_threshold: float = 0.8


# =============================================================================
# PRIORITY ORDERING
# =============================================================================

PRIORITY_ORDER: Dict[TriggerPriority, int] = {
    TriggerPriority.CRITICAL: 4,
    TriggerPriority.HIGH: 3,
    TriggerPriority.NORMAL: 2,
    TriggerPriority.LOW: 1,
}


def priority_sort_key(trigger: SkillTrigger) -> int:
    """Get sort key for trigger priority (higher = first)."""
    return PRIORITY_ORDER.get(trigger.priority, 0)


# =============================================================================
# TRIGGER DETECTOR
# =============================================================================

class TriggerDetector:
    """
    Detects skill triggers from user input.

    The TriggerDetector implements a priority-based matching algorithm:
    1. Exact keyword match (highest priority)
    2. Pattern regex match
    3. Context similarity match
    4. Default skill fallback

    Within each category, triggers are ordered by their priority field.

    Usage:
        ```python
        detector = TriggerDetector()
        detector.register_skill(skill, triggers)

        result = detector.detect("run /commit")
        if result.matched:
            print(f"Matched skill: {result.skill_name}")
        ```
    """

    def __init__(self, config: Optional[DetectorConfig] = None):
        """
        Initialize the TriggerDetector.

        Args:
            config: Optional configuration overrides
        """
        self.config = config or DetectorConfig()

        # Registered triggers indexed by skill
        self._triggers: Dict[str, List[SkillTrigger]] = {}

        # Skill definitions by ID
        self._skills: Dict[str, SkillDefinition] = {}

        # Skill name to ID mapping
        self._skill_name_to_id: Dict[str, str] = {}

        # Default skill (fallback)
        self._default_skill_id: Optional[str] = None

        # Compiled regex patterns cache
        self._compiled_patterns: Dict[str, re.Pattern] = {}

        # Keyword index for O(1) lookup: keyword -> [(skill_id, trigger_id)]
        self._keyword_index: Dict[str, List[Tuple[str, str]]] = {}

    # =========================================================================
    # REGISTRATION
    # =========================================================================

    def register_skill(
        self,
        skill: SkillDefinition,
        triggers: List[SkillTrigger]
    ) -> None:
        """
        Register a skill with its triggers.

        Args:
            skill: The skill definition to register
            triggers: List of triggers that activate this skill
        """
        self._skills[skill.id] = skill
        self._skill_name_to_id[skill.name] = skill.id
        self._triggers[skill.id] = []

        for trigger in triggers:
            # Link trigger to skill
            trigger.skill_definition_id = skill.id

            # Pre-compile regex patterns
            for pattern in trigger.patterns:
                cache_key = f"{pattern}:{trigger.case_sensitive}"
                if cache_key not in self._compiled_patterns:
                    flags = 0 if trigger.case_sensitive else re.IGNORECASE
                    self._compiled_patterns[cache_key] = re.compile(pattern, flags)

            self._triggers[skill.id].append(trigger)

            # Index keywords for fast lookup
            for keyword in trigger.keywords:
                key = keyword.lower() if not trigger.case_sensitive else keyword
                if key not in self._keyword_index:
                    self._keyword_index[key] = []
                self._keyword_index[key].append((skill.id, trigger.id))

    def unregister_skill(self, skill_id: str) -> bool:
        """
        Unregister a skill and its triggers.

        Args:
            skill_id: ID of the skill to unregister

        Returns:
            True if skill was found and removed
        """
        if skill_id not in self._skills:
            return False

        skill = self._skills.pop(skill_id)
        self._skill_name_to_id.pop(skill.name, None)
        self._triggers.pop(skill_id, None)

        if self._default_skill_id == skill_id:
            self._default_skill_id = None

        return True

    def set_default_skill(self, skill_id: str) -> None:
        """
        Set the default skill for fallback matching.

        Args:
            skill_id: ID of the skill to use as default
        """
        if skill_id not in self._skills:
            raise ValueError(f"Skill not registered: {skill_id}")
        self._default_skill_id = skill_id

    # =========================================================================
    # DETECTION
    # =========================================================================

    def detect(self, input_text: str) -> TriggerMatch:
        """
        Detect the best matching trigger for input text.

        Implements the priority algorithm:
        1. Exact keyword match
        2. Pattern regex match
        3. Context similarity (if enabled)
        4. Default skill fallback

        Args:
            input_text: User input to match against triggers

        Returns:
            TriggerMatch with detection results
        """
        if not input_text or not input_text.strip():
            return TriggerMatch(matched=False, match_type=MatchType.NO_MATCH)

        normalized_input = input_text.strip()
        all_matches: List[Dict[str, Any]] = []

        # Collect all triggers and sort by priority
        all_triggers: List[Tuple[str, SkillTrigger]] = []
        for skill_id, triggers in self._triggers.items():
            for trigger in triggers:
                if trigger.enabled:
                    all_triggers.append((skill_id, trigger))

        # Sort by priority (highest first)
        all_triggers.sort(key=lambda x: priority_sort_key(x[1]), reverse=True)

        # Phase 1: Exact keyword match
        for skill_id, trigger in all_triggers:
            match_result = self._match_keywords(normalized_input, trigger)
            if match_result:
                all_matches.append({
                    "type": MatchType.EXACT_KEYWORD.value,
                    "skill_id": skill_id,
                    "trigger_id": trigger.id,
                    "matched_value": match_result,
                    "confidence": 1.0,
                })

        if all_matches:
            best = all_matches[0]
            trigger = self._get_trigger_by_id(best["trigger_id"])
            skill = self._skills.get(best["skill_id"])
            return TriggerMatch(
                matched=True,
                match_type=MatchType.EXACT_KEYWORD,
                trigger=trigger,
                skill_definition_id=best["skill_id"],
                skill_name=skill.name if skill else None,
                confidence=1.0,
                matched_value=best["matched_value"],
                all_matches=all_matches[:self.config.max_matches_to_return],
            )

        # Phase 2: Pattern regex match
        pattern_matches: List[Dict[str, Any]] = []
        for skill_id, trigger in all_triggers:
            match_result = self._match_patterns(normalized_input, trigger)
            if match_result:
                pattern_matches.append({
                    "type": MatchType.PATTERN_MATCH.value,
                    "skill_id": skill_id,
                    "trigger_id": trigger.id,
                    "matched_value": match_result,
                    "confidence": 0.9,
                })

        if pattern_matches:
            best = pattern_matches[0]
            trigger = self._get_trigger_by_id(best["trigger_id"])
            skill = self._skills.get(best["skill_id"])
            return TriggerMatch(
                matched=True,
                match_type=MatchType.PATTERN_MATCH,
                trigger=trigger,
                skill_definition_id=best["skill_id"],
                skill_name=skill.name if skill else None,
                confidence=0.9,
                matched_value=best["matched_value"],
                all_matches=pattern_matches[:self.config.max_matches_to_return],
            )

        # Phase 3: Context similarity match
        if self.config.enable_context_matching:
            context_matches: List[Dict[str, Any]] = []
            for skill_id, trigger in all_triggers:
                if trigger.has_context_match:
                    similarity, matched_keyword = self._match_context(
                        normalized_input, trigger
                    )
                    if similarity >= self.config.context_similarity_threshold:
                        context_matches.append({
                            "type": MatchType.CONTEXT_SIMILARITY.value,
                            "skill_id": skill_id,
                            "trigger_id": trigger.id,
                            "matched_value": matched_keyword,
                            "confidence": similarity,
                        })

            # Sort by confidence
            context_matches.sort(key=lambda x: x["confidence"], reverse=True)

            if context_matches:
                best = context_matches[0]
                trigger = self._get_trigger_by_id(best["trigger_id"])
                skill = self._skills.get(best["skill_id"])
                return TriggerMatch(
                    matched=True,
                    match_type=MatchType.CONTEXT_SIMILARITY,
                    trigger=trigger,
                    skill_definition_id=best["skill_id"],
                    skill_name=skill.name if skill else None,
                    confidence=best["confidence"],
                    matched_value=best["matched_value"],
                    all_matches=context_matches[:self.config.max_matches_to_return],
                )

        # Phase 4: Default skill fallback
        if self._default_skill_id:
            skill = self._skills.get(self._default_skill_id)
            if skill:
                return TriggerMatch(
                    matched=True,
                    match_type=MatchType.DEFAULT_SKILL,
                    trigger=None,
                    skill_definition_id=self._default_skill_id,
                    skill_name=skill.name,
                    confidence=0.5,
                    matched_value=None,
                    all_matches=[],
                )

        # No match found
        return TriggerMatch(matched=False, match_type=MatchType.NO_MATCH)

    def detect_all(self, input_text: str) -> List[TriggerMatch]:
        """
        Detect all matching triggers for input text.

        Unlike detect(), this returns all potential matches, not just the best one.

        Args:
            input_text: User input to match against triggers

        Returns:
            List of all TriggerMatch results, ordered by confidence
        """
        if not input_text or not input_text.strip():
            return []

        normalized_input = input_text.strip()
        matches: List[TriggerMatch] = []

        for skill_id, triggers in self._triggers.items():
            skill = self._skills.get(skill_id)
            for trigger in triggers:
                if not trigger.enabled:
                    continue

                # Check keywords
                keyword_match = self._match_keywords(normalized_input, trigger)
                if keyword_match:
                    matches.append(TriggerMatch(
                        matched=True,
                        match_type=MatchType.EXACT_KEYWORD,
                        trigger=trigger,
                        skill_definition_id=skill_id,
                        skill_name=skill.name if skill else None,
                        confidence=1.0,
                        matched_value=keyword_match,
                    ))
                    continue

                # Check patterns
                pattern_match = self._match_patterns(normalized_input, trigger)
                if pattern_match:
                    matches.append(TriggerMatch(
                        matched=True,
                        match_type=MatchType.PATTERN_MATCH,
                        trigger=trigger,
                        skill_definition_id=skill_id,
                        skill_name=skill.name if skill else None,
                        confidence=0.9,
                        matched_value=pattern_match,
                    ))
                    continue

                # Check context
                if trigger.has_context_match:
                    similarity, matched_keyword = self._match_context(
                        normalized_input, trigger
                    )
                    if similarity >= self.config.context_similarity_threshold:
                        matches.append(TriggerMatch(
                            matched=True,
                            match_type=MatchType.CONTEXT_SIMILARITY,
                            trigger=trigger,
                            skill_definition_id=skill_id,
                            skill_name=skill.name if skill else None,
                            confidence=similarity,
                            matched_value=matched_keyword,
                        ))

        # Sort by confidence (highest first)
        matches.sort(key=lambda x: x.confidence, reverse=True)
        return matches

    # =========================================================================
    # MATCHING HELPERS
    # =========================================================================

    def _match_keywords(
        self, input_text: str, trigger: SkillTrigger
    ) -> Optional[str]:
        """
        Check for exact keyword match.

        Args:
            input_text: Normalized user input
            trigger: Trigger to check against

        Returns:
            Matched keyword or None
        """
        if not trigger.has_keywords:
            return None

        compare_input = input_text if trigger.case_sensitive else input_text.lower()

        for keyword in trigger.keywords:
            compare_keyword = keyword if trigger.case_sensitive else keyword.lower()

            # Exact match
            if compare_input == compare_keyword:
                return keyword

            # Word boundary match (keyword is a word in input)
            if trigger.case_sensitive:
                pattern = rf"\b{re.escape(keyword)}\b"
            else:
                pattern = rf"\b{re.escape(keyword.lower())}\b"

            if re.search(pattern, compare_input, re.IGNORECASE if not trigger.case_sensitive else 0):
                return keyword

        return None

    def _match_patterns(
        self, input_text: str, trigger: SkillTrigger
    ) -> Optional[str]:
        """
        Check for regex pattern match.

        Args:
            input_text: Normalized user input
            trigger: Trigger to check against

        Returns:
            Matched pattern or None
        """
        if not trigger.has_patterns:
            return None

        for pattern in trigger.patterns:
            cache_key = f"{pattern}:{trigger.case_sensitive}"
            compiled = self._compiled_patterns.get(cache_key)

            if compiled is None:
                flags = 0 if trigger.case_sensitive else re.IGNORECASE
                compiled = re.compile(pattern, flags)
                self._compiled_patterns[cache_key] = compiled

            if compiled.search(input_text):
                return pattern

        return None

    def _match_context(
        self, input_text: str, trigger: SkillTrigger
    ) -> Tuple[float, Optional[str]]:
        """
        Check for context similarity match.

        Uses simple word overlap for similarity scoring.
        For production, consider using embeddings or more sophisticated NLP.

        Args:
            input_text: Normalized user input
            trigger: Trigger to check against

        Returns:
            Tuple of (similarity_score, matched_keyword)
        """
        if not trigger.context_match:
            return 0.0, None

        input_words = set(input_text.lower().split())
        context_words = set(w.lower() for w in trigger.context_match)

        # Calculate Jaccard similarity
        intersection = input_words & context_words
        union = input_words | context_words

        if not union:
            return 0.0, None

        similarity = len(intersection) / len(union)

        # Return the first matched word
        matched_word = list(intersection)[0] if intersection else None

        return similarity, matched_word

    def _get_trigger_by_id(self, trigger_id: str) -> Optional[SkillTrigger]:
        """Get a trigger by its ID."""
        for triggers in self._triggers.values():
            for trigger in triggers:
                if trigger.id == trigger_id:
                    return trigger
        return None

    def _match_keywords_indexed(self, input_text: str) -> Optional[Dict[str, Any]]:
        """Fast O(1) keyword lookup using index."""
        normalized = input_text.lower()

        # Check exact match first
        if normalized in self._keyword_index:
            matches = self._keyword_index[normalized]
            if matches:
                skill_id, trigger_id = matches[0]
                return {
                    "skill_id": skill_id,
                    "trigger_id": trigger_id,
                    "matched_value": normalized,
                    "confidence": 1.0
                }

        # Check word boundary matches
        words = set(normalized.split())
        for word in words:
            if word in self._keyword_index:
                matches = self._keyword_index[word]
                if matches:
                    skill_id, trigger_id = matches[0]
                    return {
                        "skill_id": skill_id,
                        "trigger_id": trigger_id,
                        "matched_value": word,
                        "confidence": 1.0
                    }

        return None

    async def detect_parallel(self, input_text: str) -> TriggerMatch:
        """
        Async parallel detection using keyword index.

        Optimized version that:
        1. Uses indexed keyword lookup first (O(1))
        2. Falls back to sequential phases if no index match
        """
        import asyncio

        if not input_text or not input_text.strip():
            return TriggerMatch(matched=False, match_type=MatchType.NO_MATCH)

        normalized_input = input_text.strip()

        # Phase 1: Try indexed keyword match first (O(1))
        indexed_match = self._match_keywords_indexed(normalized_input)
        if indexed_match:
            trigger = self._get_trigger_by_id(indexed_match["trigger_id"])
            skill = self._skills.get(indexed_match["skill_id"])
            return TriggerMatch(
                matched=True,
                match_type=MatchType.EXACT_KEYWORD,
                trigger=trigger,
                skill_definition_id=indexed_match["skill_id"],
                skill_name=skill.name if skill else None,
                confidence=indexed_match["confidence"],
                matched_value=indexed_match["matched_value"],
            )

        # Fallback to synchronous detect for pattern/context matching
        return self.detect(normalized_input)

    # =========================================================================
    # INTROSPECTION
    # =========================================================================

    def list_skills(self) -> List[SkillDefinition]:
        """List all registered skills."""
        return list(self._skills.values())

    def list_triggers(self, skill_id: Optional[str] = None) -> List[SkillTrigger]:
        """List triggers, optionally filtered by skill."""
        if skill_id:
            return self._triggers.get(skill_id, [])

        all_triggers = []
        for triggers in self._triggers.values():
            all_triggers.extend(triggers)
        return all_triggers

    def get_skill(self, skill_id: str) -> Optional[SkillDefinition]:
        """Get a skill by ID."""
        return self._skills.get(skill_id)

    def get_skill_by_name(self, name: str) -> Optional[SkillDefinition]:
        """Get a skill by name."""
        skill_id = self._skill_name_to_id.get(name)
        return self._skills.get(skill_id) if skill_id else None

    def get_statistics(self) -> Dict[str, Any]:
        """Get detector statistics."""
        total_triggers = sum(len(t) for t in self._triggers.values())
        total_keywords = sum(
            len(t.keywords)
            for triggers in self._triggers.values()
            for t in triggers
        )
        total_patterns = sum(
            len(t.patterns)
            for triggers in self._triggers.values()
            for t in triggers
        )

        return {
            "total_skills": len(self._skills),
            "total_triggers": total_triggers,
            "total_keywords": total_keywords,
            "total_patterns": total_patterns,
            "cached_patterns": len(self._compiled_patterns),
            "has_default_skill": self._default_skill_id is not None,
        }


# =============================================================================
# ACTION TYPES
# =============================================================================


class DetectSkillTriggerAction:
    """
    Action to detect skill triggers from user input.

    Non-hazardous action that performs trigger detection.
    """

    api_name: str = "detect_skill_trigger"
    display_name: str = "Detect Skill Trigger"
    description: str = "Detect matching skill trigger from user input"
    is_hazardous: bool = False

    def __init__(
        self,
        user_input: str,
        detector: Optional[TriggerDetector] = None,
    ):
        """
        Initialize detection action.

        Args:
            user_input: User input to detect triggers from
            detector: Optional TriggerDetector (uses new instance if not provided)
        """
        self.user_input = user_input
        self.detector = detector or TriggerDetector()

    def execute(self) -> TriggerMatch:
        """Execute trigger detection."""
        return self.detector.detect(self.user_input)
