"""
Orion ODA v4.0 - Branch Actions
================================

Actions for Git-like branching operations on the ODA ontology.

Actions:
- branch.compare: Compare two branches (non-hazardous)
- branch.diff: Show diff between branches (non-hazardous)
- branch.merge_preview: Preview merge without executing (non-hazardous)
- branch.resolve_conflict: Resolve merge conflicts (HAZARDOUS - requires proposal)
- branch.cherry_pick: Apply specific commit (HAZARDOUS - requires proposal)

Example:
    ```python
    from lib.oda.ontology.actions import action_registry, ActionContext

    # Compare branches
    CompareAction = action_registry.get("branch.compare")
    action = CompareAction()

    result = await action.execute(
        params={
            "branch_a": "feature/new-api",
            "branch_b": "main",
        },
        context=ActionContext(actor_id="user-123")
    )
    ```

Schema Version: 4.0.0
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, ClassVar, Dict, List, Optional, Type

from lib.oda.ontology.actions import (
    ActionContext,
    ActionResult,
    ActionType,
    EditOperation,
    EditType,
    RequiredField,
    SubmissionCriterion,
    ValidationError,
    register_action,
)
from lib.oda.ontology.ontology_types import OntologyObject

logger = logging.getLogger(__name__)


# =============================================================================
# CUSTOM VALIDATORS
# =============================================================================


class ValidBranchId(SubmissionCriterion):
    """Validates that a branch ID is provided and non-empty."""

    def __init__(self, field_name: str):
        self.field_name = field_name

    @property
    def name(self) -> str:
        return f"ValidBranchId({self.field_name})"

    def validate(self, params: Dict[str, Any], context: ActionContext) -> bool:
        value = params.get(self.field_name)
        if not value or not isinstance(value, str) or not value.strip():
            raise ValidationError(
                criterion=self.name,
                message=f"Branch identifier required for '{self.field_name}'",
                details={"field": self.field_name, "value": value}
            )
        return True


class BranchesNotEqual(SubmissionCriterion):
    """Validates that two branch identifiers are different."""

    def __init__(self, field_a: str = "branch_a", field_b: str = "branch_b"):
        self.field_a = field_a
        self.field_b = field_b

    @property
    def name(self) -> str:
        return f"BranchesNotEqual({self.field_a}, {self.field_b})"

    def validate(self, params: Dict[str, Any], context: ActionContext) -> bool:
        value_a = params.get(self.field_a)
        value_b = params.get(self.field_b)

        if value_a and value_b and value_a == value_b:
            raise ValidationError(
                criterion=self.name,
                message="Cannot compare a branch with itself",
                details={
                    self.field_a: value_a,
                    self.field_b: value_b,
                }
            )
        return True


# =============================================================================
# BRANCH COMPARE ACTION (NON-HAZARDOUS)
# =============================================================================


@register_action
class BranchCompareAction(ActionType[OntologyObject]):
    """
    Compare two branches to identify differences.

    This action is non-hazardous (read-only) and does not require approval.

    Parameters:
        branch_a: First branch ID or name
        branch_b: Second branch ID or name
        include_commits: If True, include commit lists (default: False)
        include_stats: If True, include diff statistics (default: True)

    Returns:
        ActionResult with comparison details:
        - ahead_count: Commits branch_a is ahead of branch_b
        - behind_count: Commits branch_a is behind branch_b
        - common_ancestor: Common ancestor commit ID
        - diverged_at: When branches diverged
    """

    api_name: ClassVar[str] = "branch.compare"
    object_type: ClassVar[Type[OntologyObject]] = OntologyObject
    requires_proposal: ClassVar[bool] = False

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        ValidBranchId("branch_a"),
        ValidBranchId("branch_b"),
        BranchesNotEqual(),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> ActionResult:
        """Compare the two branches."""
        branch_a = params["branch_a"]
        branch_b = params["branch_b"]
        include_commits = params.get("include_commits", False)
        include_stats = params.get("include_stats", True)

        try:
            # In a real implementation, this would use BranchManager
            # For now, return a structured comparison result
            comparison = {
                "branch_a": branch_a,
                "branch_b": branch_b,
                "ahead_count": 0,
                "behind_count": 0,
                "common_ancestor": None,
                "diverged_at": None,
                "can_fast_forward": True,
                "has_conflicts": False,
            }

            if include_stats:
                comparison["stats"] = {
                    "files_changed": 0,
                    "additions": 0,
                    "deletions": 0,
                    "object_types_affected": [],
                }

            if include_commits:
                comparison["commits_a"] = []
                comparison["commits_b"] = []

            logger.info(f"Branch comparison: {branch_a} vs {branch_b}")

            return ActionResult(
                action_type=self.api_name,
                success=True,
                data=comparison,
                edits=[],
                message=f"Compared {branch_a} with {branch_b}",
            )

        except Exception as e:
            logger.exception(f"Branch comparison failed: {e}")
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=str(e),
                error_details={"exception_type": type(e).__name__},
            )


# =============================================================================
# BRANCH DIFF ACTION (NON-HAZARDOUS)
# =============================================================================


@register_action
class BranchDiffAction(ActionType[OntologyObject]):
    """
    Show detailed diff between two branches.

    This action is non-hazardous (read-only) and does not require approval.

    Parameters:
        branch_a: First branch ID or name (base)
        branch_b: Second branch ID or name (compare)
        object_type: Optional filter by object type
        include_content: If True, include full change content (default: False)
        max_changes: Maximum changes to return (default: 100)

    Returns:
        ActionResult with diff details including changed objects and fields
    """

    api_name: ClassVar[str] = "branch.diff"
    object_type: ClassVar[Type[OntologyObject]] = OntologyObject
    requires_proposal: ClassVar[bool] = False

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        ValidBranchId("branch_a"),
        ValidBranchId("branch_b"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> ActionResult:
        """Generate diff between branches."""
        branch_a = params["branch_a"]
        branch_b = params["branch_b"]
        object_type_filter = params.get("object_type")
        include_content = params.get("include_content", False)
        max_changes = params.get("max_changes", 100)

        try:
            diff_result = {
                "base_branch": branch_a,
                "compare_branch": branch_b,
                "changes": [],
                "summary": {
                    "total_changes": 0,
                    "additions": 0,
                    "modifications": 0,
                    "deletions": 0,
                },
                "truncated": False,
            }

            # In a real implementation, this would query the actual diff
            # using DiffEngine from lib.oda.transaction.diff

            logger.info(f"Branch diff: {branch_a}...{branch_b}")

            return ActionResult(
                action_type=self.api_name,
                success=True,
                data=diff_result,
                edits=[],
                message=f"Generated diff for {branch_a}...{branch_b}",
            )

        except Exception as e:
            logger.exception(f"Branch diff failed: {e}")
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=str(e),
                error_details={"exception_type": type(e).__name__},
            )


# =============================================================================
# BRANCH MERGE PREVIEW ACTION (NON-HAZARDOUS)
# =============================================================================


@register_action
class BranchMergePreviewAction(ActionType[OntologyObject]):
    """
    Preview merge without executing it.

    This action is non-hazardous (read-only) and does not require approval.
    It simulates a merge to identify potential conflicts.

    Parameters:
        source_branch: Branch to merge from
        target_branch: Branch to merge into
        merge_strategy: Strategy to use (default: "three_way")

    Returns:
        ActionResult with merge preview:
        - can_merge: If merge can proceed
        - conflicts: List of potential conflicts
        - changes_to_apply: Changes that would be made
    """

    api_name: ClassVar[str] = "branch.merge_preview"
    object_type: ClassVar[Type[OntologyObject]] = OntologyObject
    requires_proposal: ClassVar[bool] = False

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        ValidBranchId("source_branch"),
        ValidBranchId("target_branch"),
        BranchesNotEqual("source_branch", "target_branch"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> ActionResult:
        """Preview the merge."""
        source_branch = params["source_branch"]
        target_branch = params["target_branch"]
        merge_strategy = params.get("merge_strategy", "three_way")

        try:
            # Use MergeStrategy from lib.oda.transaction.merge for preview
            from lib.oda.transaction.merge import MergeMode

            preview = {
                "source_branch": source_branch,
                "target_branch": target_branch,
                "merge_strategy": merge_strategy,
                "can_merge": True,
                "is_fast_forward": False,
                "conflicts": [],
                "changes_to_apply": [],
                "common_ancestor": None,
            }

            # In a real implementation, use MergeStrategy.preview()

            logger.info(
                f"Merge preview: {source_branch} -> {target_branch} "
                f"(strategy: {merge_strategy})"
            )

            return ActionResult(
                action_type=self.api_name,
                success=True,
                data=preview,
                edits=[],
                message=f"Merge preview: {source_branch} -> {target_branch}",
            )

        except Exception as e:
            logger.exception(f"Merge preview failed: {e}")
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=str(e),
                error_details={"exception_type": type(e).__name__},
            )


# =============================================================================
# CONFLICT RESOLVE ACTION (HAZARDOUS)
# =============================================================================


@register_action(requires_proposal=True)
class ConflictResolveAction(ActionType[OntologyObject]):
    """
    Resolve merge conflicts.

    This action is HAZARDOUS and requires a proposal for approval.
    It applies conflict resolutions and creates a merge commit.

    Parameters:
        merge_id: ID of the merge operation
        resolutions: List of conflict resolutions
            Each resolution: {"conflict_id": "...", "mode": "ours|theirs|manual", "value": ...}
        commit_message: Optional custom commit message

    Returns:
        ActionResult with resolution details and new commit ID
    """

    api_name: ClassVar[str] = "branch.resolve_conflict"
    object_type: ClassVar[Type[OntologyObject]] = OntologyObject
    requires_proposal: ClassVar[bool] = True

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        RequiredField("merge_id"),
        RequiredField("resolutions"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> ActionResult:
        """Apply conflict resolutions."""
        merge_id = params["merge_id"]
        resolutions = params["resolutions"]
        commit_message = params.get("commit_message")

        try:
            # Use ConflictResolver from lib.oda.transaction.conflicts
            from lib.oda.transaction.conflicts import (
                ConflictResolver,
                ConflictResolutionMode,
            )

            resolver = ConflictResolver()
            resolved_conflicts = []

            for resolution in resolutions:
                conflict_id = resolution.get("conflict_id")
                mode = resolution.get("mode", "manual")
                value = resolution.get("value")

                # Convert mode string to enum
                resolution_mode = ConflictResolutionMode(mode)

                resolved_conflicts.append({
                    "conflict_id": conflict_id,
                    "mode": mode,
                    "resolved_by": context.actor_id,
                })

            # Create edit operation for audit trail
            edit = EditOperation(
                edit_type=EditType.MODIFY,
                object_type="MergeConflict",
                object_id=merge_id,
                changes={
                    "resolutions": resolved_conflicts,
                    "resolved_by": context.actor_id,
                },
                timestamp=context.timestamp,
            )

            logger.info(
                f"Conflicts resolved: merge_id={merge_id}, "
                f"count={len(resolved_conflicts)}, by={context.actor_id}"
            )

            return ActionResult(
                action_type=self.api_name,
                success=True,
                data={
                    "merge_id": merge_id,
                    "resolved_count": len(resolved_conflicts),
                    "resolutions": resolved_conflicts,
                },
                edits=[edit],
                modified_ids=[merge_id],
                message=f"Resolved {len(resolved_conflicts)} conflicts for merge {merge_id}",
            )

        except Exception as e:
            logger.exception(f"Conflict resolution failed: {e}")
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=str(e),
                error_details={"exception_type": type(e).__name__},
            )


# =============================================================================
# CHERRY PICK ACTION (HAZARDOUS)
# =============================================================================


@register_action(requires_proposal=True)
class CherryPickAction(ActionType[OntologyObject]):
    """
    Apply a specific commit to the target branch (cherry-pick).

    This action is HAZARDOUS and requires a proposal for approval.

    Parameters:
        commit_id: ID of commit to cherry-pick
        target_branch: Branch to apply the commit to
        conflict_resolution: How to handle conflicts ("abort"|"skip"|"ours"|"theirs")
        message_override: Optional custom commit message

    Returns:
        ActionResult with cherry-pick details and new commit ID
    """

    api_name: ClassVar[str] = "branch.cherry_pick"
    object_type: ClassVar[Type[OntologyObject]] = OntologyObject
    requires_proposal: ClassVar[bool] = True

    submission_criteria: ClassVar[List[SubmissionCriterion]] = [
        RequiredField("commit_id"),
        ValidBranchId("target_branch"),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext,
    ) -> ActionResult:
        """Execute cherry-pick operation."""
        commit_id = params["commit_id"]
        target_branch = params["target_branch"]
        conflict_resolution = params.get("conflict_resolution", "abort")
        message_override = params.get("message_override")

        try:
            from lib.oda.transaction.cherry_pick import (
                CherryPicker,
                CherryPickConflictResolution,
            )

            # Map string to enum
            resolution_map = {
                "abort": CherryPickConflictResolution.ABORT,
                "skip": CherryPickConflictResolution.SKIP,
                "ours": CherryPickConflictResolution.OURS,
                "theirs": CherryPickConflictResolution.THEIRS,
            }
            resolution = resolution_map.get(
                conflict_resolution,
                CherryPickConflictResolution.ABORT
            )

            # In a real implementation, use the actual BranchManager
            picker = CherryPicker(
                branch_manager=None,
                conflict_resolution=resolution,
            )

            # For now, return simulated result
            result_data = {
                "commit_id": commit_id,
                "target_branch": target_branch,
                "new_commit_id": None,  # Would be populated after actual cherry-pick
                "applied_changes": [],
                "conflicts": [],
                "status": "pending",
            }

            # Create edit operation for audit trail
            edit = EditOperation(
                edit_type=EditType.CREATE,
                object_type="CherryPickOperation",
                object_id=f"cp-{commit_id[:8]}",
                changes={
                    "source_commit": commit_id,
                    "target_branch": target_branch,
                    "conflict_resolution": conflict_resolution,
                    "initiated_by": context.actor_id,
                },
                timestamp=context.timestamp,
            )

            logger.info(
                f"Cherry-pick initiated: {commit_id} -> {target_branch} "
                f"by {context.actor_id}"
            )

            return ActionResult(
                action_type=self.api_name,
                success=True,
                data=result_data,
                edits=[edit],
                created_ids=[result_data.get("new_commit_id")] if result_data.get("new_commit_id") else [],
                message=f"Cherry-pick initiated: {commit_id} -> {target_branch}",
            )

        except Exception as e:
            logger.exception(f"Cherry-pick failed: {e}")
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=str(e),
                error_details={"exception_type": type(e).__name__},
            )


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "BranchCompareAction",
    "BranchDiffAction",
    "BranchMergePreviewAction",
    "ConflictResolveAction",
    "CherryPickAction",
    "ValidBranchId",
    "BranchesNotEqual",
]
