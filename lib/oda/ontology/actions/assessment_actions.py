"""
Orion ODA v4.0 - Assessment Action Types
========================================

ActionTypes for Assessment object management.
Provides test/quiz lifecycle management and grading.

Phase 3.4.3 Implementation:
- assessment.create: Create new assessment
- assessment.start: Start assessment attempt
- assessment.submit_response: Submit answer for an item
- assessment.submit: Submit assessment for grading
- assessment.grade: Grade the assessment
- assessment.add_feedback: Add feedback to assessment
- assessment.retry: Start a new attempt

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from lib.oda.ontology.actions import (
    ActionContext,
    ActionResult,
    ActionType,
    AllowedValues,
    CustomValidator,
    EditOperation,
    EditType,
    RangeValidator,
    RequiredField,
    register_action,
)
from lib.oda.ontology.objects.assessment import (
    Assessment,
    AssessmentStatus,
    AssessmentType,
    GradingMethod,
    ItemType,
)
from lib.oda.ontology.ontology_types import OntologyObject

logger = logging.getLogger(__name__)


# =============================================================================
# VALIDATORS
# =============================================================================


def validate_assessment_exists(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate that assessment_id refers to an existing assessment."""
    assessment_id = params.get("assessment_id", "")
    return bool(assessment_id)


def validate_assessment_not_started(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate that assessment has not been started."""
    # Would check assessment status in database
    return True


def validate_assessment_in_progress(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate that assessment is in progress."""
    # Would check assessment status
    return True


def validate_assessment_submitted(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate that assessment has been submitted."""
    # Would check assessment status
    return True


def validate_has_attempts_remaining(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate that learner has attempts remaining."""
    # Would check attempts_used < max_attempts
    return True


def validate_item_exists(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate that the item_id exists in the assessment."""
    item_id = params.get("item_id", "")
    return bool(item_id)


def validate_items_list(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate items list structure."""
    items = params.get("items", [])
    if not isinstance(items, list):
        return False
    for item in items:
        if not isinstance(item, dict):
            return False
        if "id" not in item or "type" not in item or "content" not in item:
            return False
    return True


# =============================================================================
# ASSESSMENT CREATE ACTION
# =============================================================================


@register_action
class AssessmentCreateAction(ActionType[Assessment]):
    """
    Create a new assessment.

    Parameters:
        title: Assessment title (required)
        assessment_type: Type (quiz, test, exam, etc.)
        grading_method: Grading method (automatic, manual, hybrid)
        course_id: Optional associated course
        items: List of assessment items
        time_limit_minutes: Optional time limit
        max_attempts: Maximum attempts allowed (default: 1)
        passing_score: Minimum passing percentage (default: 70)
        shuffle_items: Whether to shuffle item order
        shuffle_options: Whether to shuffle answer options

    Returns:
        Assessment: The created assessment
    """
    api_name = "assessment.create"
    object_type = Assessment
    requires_proposal = False

    submission_criteria = [
        RequiredField("title"),
        AllowedValues(
            "assessment_type",
            [at.value for at in AssessmentType]
        ),
        AllowedValues(
            "grading_method",
            [gm.value for gm in GradingMethod]
        ),
        RangeValidator("passing_score", min_value=0, max_value=100),
        RangeValidator("max_attempts", min_value=1),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Assessment], List[EditOperation]]:
        """Create a new assessment."""
        items = params.get("items", [])
        total_points = sum(item.get("points", 1) for item in items)

        assessment = Assessment(
            title=params["title"],
            assessment_type=AssessmentType(params.get("assessment_type", "quiz")),
            assessment_status=AssessmentStatus.DRAFT,
            grading_method=GradingMethod(params.get("grading_method", "automatic")),
            course_id=params.get("course_id"),
            learner_id=params.get("learner_id"),
            session_id=params.get("session_id"),
            description=params.get("description", ""),
            instructions=params.get("instructions", ""),
            items=items,
            item_count=len(items),
            knowledge_components=params.get("knowledge_components", []),
            total_points=total_points,
            passing_score=params.get("passing_score", 70.0),
            time_limit_minutes=params.get("time_limit_minutes"),
            max_attempts=params.get("max_attempts", 1),
            shuffle_items=params.get("shuffle_items", False),
            shuffle_options=params.get("shuffle_options", False),
            show_correct_answers=params.get("show_correct_answers", False),
            show_feedback_immediately=params.get("show_feedback_immediately", False),
            is_adaptive=params.get("is_adaptive", False),
            tags=params.get("tags", []),
            settings=params.get("settings", {}),
            created_by=context.actor_id,
        )

        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="Assessment",
            object_id=assessment.id,
            changes={
                "title": assessment.title,
                "assessment_type": assessment.assessment_type.value,
                "item_count": assessment.item_count,
                "total_points": assessment.total_points,
                "actor": context.actor_id,
            }
        )

        return assessment, [edit]


# =============================================================================
# ASSESSMENT LIFECYCLE ACTIONS
# =============================================================================


@register_action
class AssessmentStartAction(ActionType[Assessment]):
    """
    Start an assessment attempt.

    Parameters:
        assessment_id: ID of assessment to start (required)

    Returns:
        Assessment: The started assessment
    """
    api_name = "assessment.start"
    object_type = Assessment
    requires_proposal = False

    submission_criteria = [
        RequiredField("assessment_id"),
        CustomValidator(
            name="AssessmentExists",
            validator_fn=validate_assessment_exists,
            error_message="Assessment not found"
        ),
        CustomValidator(
            name="HasAttemptsRemaining",
            validator_fn=validate_has_attempts_remaining,
            error_message="No attempts remaining"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Assessment], List[EditOperation]]:
        """Start the assessment."""
        assessment_id = params["assessment_id"]

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Assessment",
            object_id=assessment_id,
            changes={
                "assessment_status": AssessmentStatus.IN_PROGRESS.value,
                "started_at": datetime.now(timezone.utc).isoformat(),
                "attempts_used": "+1",
                "responses": {},  # Clear previous responses
                "item_scores": {},  # Clear previous scores
                "actor": context.actor_id,
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Assessment {assessment_id} started",
            edits=[edit],
            modified_ids=[assessment_id],
        )


@register_action
class AssessmentSubmitResponseAction(ActionType[Assessment]):
    """
    Submit a response for an assessment item.

    Parameters:
        assessment_id: ID of assessment (required)
        item_id: ID of the item being answered (required)
        response: The learner's response (required)

    Returns:
        Assessment: The updated assessment
    """
    api_name = "assessment.submit_response"
    object_type = Assessment
    requires_proposal = False

    submission_criteria = [
        RequiredField("assessment_id"),
        RequiredField("item_id"),
        RequiredField("response"),
        CustomValidator(
            name="AssessmentExists",
            validator_fn=validate_assessment_exists,
            error_message="Assessment not found"
        ),
        CustomValidator(
            name="AssessmentInProgress",
            validator_fn=validate_assessment_in_progress,
            error_message="Assessment not in progress"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Assessment], List[EditOperation]]:
        """Submit response for an item."""
        assessment_id = params["assessment_id"]
        item_id = params["item_id"]
        response = params["response"]

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Assessment",
            object_id=assessment_id,
            changes={
                "response_submitted": {
                    "item_id": item_id,
                    "response": response,
                    "submitted_at": datetime.now(timezone.utc).isoformat(),
                },
                "actor": context.actor_id,
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Response submitted for item {item_id}",
            edits=[edit],
            modified_ids=[assessment_id],
        )


@register_action
class AssessmentSubmitAction(ActionType[Assessment]):
    """
    Submit assessment for grading.

    Parameters:
        assessment_id: ID of assessment to submit (required)

    Returns:
        Assessment: The submitted assessment
    """
    api_name = "assessment.submit"
    object_type = Assessment
    requires_proposal = False

    submission_criteria = [
        RequiredField("assessment_id"),
        CustomValidator(
            name="AssessmentExists",
            validator_fn=validate_assessment_exists,
            error_message="Assessment not found"
        ),
        CustomValidator(
            name="AssessmentInProgress",
            validator_fn=validate_assessment_in_progress,
            error_message="Assessment not in progress"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Assessment], List[EditOperation]]:
        """Submit the assessment for grading."""
        assessment_id = params["assessment_id"]

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Assessment",
            object_id=assessment_id,
            changes={
                "assessment_status": AssessmentStatus.SUBMITTED.value,
                "submitted_at": datetime.now(timezone.utc).isoformat(),
                "actor": context.actor_id,
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Assessment {assessment_id} submitted for grading",
            edits=[edit],
            modified_ids=[assessment_id],
        )


# =============================================================================
# ASSESSMENT GRADING ACTIONS
# =============================================================================


@register_action
class AssessmentGradeAction(ActionType[Assessment]):
    """
    Grade an assessment.

    Parameters:
        assessment_id: ID of assessment to grade (required)
        item_scores: Dictionary of scores per item (required)
        feedback: Optional dictionary of feedback per item

    Returns:
        Assessment: The graded assessment
    """
    api_name = "assessment.grade"
    object_type = Assessment
    requires_proposal = False

    submission_criteria = [
        RequiredField("assessment_id"),
        RequiredField("item_scores"),
        CustomValidator(
            name="AssessmentExists",
            validator_fn=validate_assessment_exists,
            error_message="Assessment not found"
        ),
        CustomValidator(
            name="AssessmentSubmitted",
            validator_fn=validate_assessment_submitted,
            error_message="Assessment not submitted"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Assessment], List[EditOperation]]:
        """Grade the assessment."""
        assessment_id = params["assessment_id"]
        item_scores = params["item_scores"]
        feedback = params.get("feedback", {})

        # Calculate total score
        score = sum(item_scores.values())
        # Note: In real implementation, we'd calculate percentage from total_points

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Assessment",
            object_id=assessment_id,
            changes={
                "assessment_status": AssessmentStatus.GRADED.value,
                "item_scores": item_scores,
                "feedback": feedback,
                "score": score,
                "graded_at": datetime.now(timezone.utc).isoformat(),
                "graded_by": context.actor_id,
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Assessment {assessment_id} graded with score {score}",
            edits=[edit],
            modified_ids=[assessment_id],
        )


@register_action
class AssessmentAutoGradeAction(ActionType[Assessment]):
    """
    Auto-grade an assessment based on correct answers.

    Parameters:
        assessment_id: ID of assessment to grade (required)

    Returns:
        Assessment: The graded assessment with calculated scores
    """
    api_name = "assessment.auto_grade"
    object_type = Assessment
    requires_proposal = False

    submission_criteria = [
        RequiredField("assessment_id"),
        CustomValidator(
            name="AssessmentExists",
            validator_fn=validate_assessment_exists,
            error_message="Assessment not found"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Assessment], List[EditOperation]]:
        """Auto-grade the assessment."""
        assessment_id = params["assessment_id"]

        # In real implementation, this would:
        # 1. Load assessment with items and responses
        # 2. Compare responses to correct answers
        # 3. Calculate scores for each item
        # 4. Calculate total score and percentage

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Assessment",
            object_id=assessment_id,
            changes={
                "assessment_status": AssessmentStatus.GRADING.value,
                "grading_started_at": datetime.now(timezone.utc).isoformat(),
                "grading_method_used": "automatic",
                "actor": context.actor_id,
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Auto-grading initiated for assessment {assessment_id}",
            edits=[edit],
            modified_ids=[assessment_id],
        )


@register_action
class AssessmentAddFeedbackAction(ActionType[Assessment]):
    """
    Add overall feedback to a graded assessment.

    Parameters:
        assessment_id: ID of assessment (required)
        overall_feedback: Overall feedback text (required)
        item_feedback: Optional additional item-level feedback

    Returns:
        Assessment: The updated assessment
    """
    api_name = "assessment.add_feedback"
    object_type = Assessment
    requires_proposal = False

    submission_criteria = [
        RequiredField("assessment_id"),
        RequiredField("overall_feedback"),
        CustomValidator(
            name="AssessmentExists",
            validator_fn=validate_assessment_exists,
            error_message="Assessment not found"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Assessment], List[EditOperation]]:
        """Add feedback to assessment."""
        assessment_id = params["assessment_id"]
        overall_feedback = params["overall_feedback"]
        item_feedback = params.get("item_feedback", {})

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Assessment",
            object_id=assessment_id,
            changes={
                "assessment_status": AssessmentStatus.REVIEWED.value,
                "overall_feedback": overall_feedback,
                "item_feedback_additions": item_feedback,
                "reviewed_at": datetime.now(timezone.utc).isoformat(),
                "reviewed_by": context.actor_id,
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Feedback added to assessment {assessment_id}",
            edits=[edit],
            modified_ids=[assessment_id],
        )


# =============================================================================
# ASSESSMENT RETRY ACTION
# =============================================================================


@register_action
class AssessmentRetryAction(ActionType[Assessment]):
    """
    Create a retry attempt for an assessment.

    Parameters:
        assessment_id: ID of original assessment (required)

    Returns:
        Assessment: New assessment attempt
    """
    api_name = "assessment.retry"
    object_type = Assessment
    requires_proposal = False

    submission_criteria = [
        RequiredField("assessment_id"),
        CustomValidator(
            name="AssessmentExists",
            validator_fn=validate_assessment_exists,
            error_message="Assessment not found"
        ),
        CustomValidator(
            name="HasAttemptsRemaining",
            validator_fn=validate_has_attempts_remaining,
            error_message="No attempts remaining"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Assessment], List[EditOperation]]:
        """Create retry attempt."""
        assessment_id = params["assessment_id"]

        # In real implementation:
        # 1. Load original assessment
        # 2. Create new Assessment with incremented attempt_number
        # 3. Reset responses, scores, status

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Assessment",
            object_id=assessment_id,
            changes={
                "assessment_status": AssessmentStatus.READY.value,
                "attempt_number": "+1",
                "responses": {},
                "item_scores": {},
                "score": None,
                "score_percentage": None,
                "passed": None,
                "started_at": None,
                "submitted_at": None,
                "actor": context.actor_id,
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Retry prepared for assessment {assessment_id}",
            edits=[edit],
            modified_ids=[assessment_id],
        )


# =============================================================================
# ASSESSMENT ITEM MANAGEMENT ACTIONS
# =============================================================================


@register_action
class AssessmentAddItemAction(ActionType[Assessment]):
    """
    Add an item (question) to an assessment.

    Parameters:
        assessment_id: ID of assessment (required)
        item: Item definition dict (required)
            - id: Unique item ID
            - type: Item type (multiple_choice, short_answer, etc.)
            - content: Question content
            - options: Answer options (for choice types)
            - correct_answer: Correct answer(s)
            - points: Point value
            - difficulty: Difficulty level (0-1)

    Returns:
        Assessment: The updated assessment
    """
    api_name = "assessment.add_item"
    object_type = Assessment
    requires_proposal = False

    submission_criteria = [
        RequiredField("assessment_id"),
        RequiredField("item"),
        CustomValidator(
            name="AssessmentExists",
            validator_fn=validate_assessment_exists,
            error_message="Assessment not found"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Assessment], List[EditOperation]]:
        """Add item to assessment."""
        assessment_id = params["assessment_id"]
        item = params["item"]

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Assessment",
            object_id=assessment_id,
            changes={
                "item_added": item,
                "item_count": "+1",
                "total_points": f"+{item.get('points', 1)}",
                "actor": context.actor_id,
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Item added to assessment {assessment_id}",
            edits=[edit],
            modified_ids=[assessment_id],
        )


@register_action
class AssessmentRemoveItemAction(ActionType[Assessment]):
    """
    Remove an item from an assessment.

    Parameters:
        assessment_id: ID of assessment (required)
        item_id: ID of item to remove (required)

    Returns:
        Assessment: The updated assessment
    """
    api_name = "assessment.remove_item"
    object_type = Assessment
    requires_proposal = False

    submission_criteria = [
        RequiredField("assessment_id"),
        RequiredField("item_id"),
        CustomValidator(
            name="AssessmentExists",
            validator_fn=validate_assessment_exists,
            error_message="Assessment not found"
        ),
        CustomValidator(
            name="ItemExists",
            validator_fn=validate_item_exists,
            error_message="Item not found in assessment"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[Assessment], List[EditOperation]]:
        """Remove item from assessment."""
        assessment_id = params["assessment_id"]
        item_id = params["item_id"]

        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Assessment",
            object_id=assessment_id,
            changes={
                "item_removed": item_id,
                "item_count": "-1",
                "actor": context.actor_id,
            }
        )

        return ActionResult(
            action_type=self.api_name,
            success=True,
            message=f"Item {item_id} removed from assessment {assessment_id}",
            edits=[edit],
            modified_ids=[assessment_id],
        )


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Create
    "AssessmentCreateAction",
    # Lifecycle
    "AssessmentStartAction",
    "AssessmentSubmitResponseAction",
    "AssessmentSubmitAction",
    # Grading
    "AssessmentGradeAction",
    "AssessmentAutoGradeAction",
    "AssessmentAddFeedbackAction",
    # Retry
    "AssessmentRetryAction",
    # Item management
    "AssessmentAddItemAction",
    "AssessmentRemoveItemAction",
]
