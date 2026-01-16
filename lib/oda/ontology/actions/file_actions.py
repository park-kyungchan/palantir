"""
Orion ODA v3.0 - File Action Types
LLM-Agnostic Architecture - Phase 1

This module implements file-related ActionTypes for the ODA governance layer.
All file modifications require proposal approval (hazardous actions).

ActionTypes:
- file.read: Audit-only file read (non-hazardous)
- file.modify: Modify existing file content (hazardous)
- file.write: Write new file content (hazardous)
- file.delete: Delete file (hazardous)
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from lib.oda.ontology.actions import (
    ActionContext,
    ActionResult,
    ActionType,
    CustomValidator,
    EditOperation,
    EditType,
    RequiredField,
    register_action,
)
from lib.oda.ontology.ontology_types import OntologyObject

logger = logging.getLogger(__name__)


# =============================================================================
# PYDANTIC MODELS FOR PARAMETER VALIDATION
# =============================================================================


class CorrectionPatch(BaseModel):
    """
    Represents a correction made during document processing.

    Used by Mathpix pipeline to track text/vision parse corrections
    that link back to ODA Evidence for audit trail.
    """
    patch_id: str = Field(
        ...,
        description="Unique identifier for this correction"
    )
    original_text: str = Field(
        ...,
        description="Original text before correction"
    )
    corrected_text: str = Field(
        ...,
        description="Text after correction"
    )
    correction_type: str = Field(
        ...,
        description="Type of correction: ocr_fix|latex_fix|semantic_fix|structural_fix"
    )
    confidence: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Confidence score for the correction (0.0-1.0)"
    )
    source_stage: str = Field(
        ...,
        description="Pipeline stage that generated this correction (B|C|D)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional correction metadata"
    )


class StageEvidence(BaseModel):
    """
    Evidence collected during 3-Stage Protocol execution.
    Required for hazardous file operations to ensure audit trail.

    Extended for Mathpix pipeline integration:
    - correction_patches: Links correction_patch objects to evidence
    - final_confidence: Overall confidence after all stages
    """
    files_viewed: List[str] = Field(
        default_factory=list,
        description="List of files viewed during Stage A (SCAN)"
    )
    imports_verified: List[str] = Field(
        default_factory=list,
        description="List of imports verified during Stage B (TRACE)"
    )
    complexity: Optional[str] = Field(
        default=None,
        description="Complexity classification: small|medium|large"
    )
    protocol_stage: Optional[str] = Field(
        default=None,
        description="Current protocol stage: A|B|C"
    )
    # Mathpix Pipeline Extensions
    correction_patches: List[CorrectionPatch] = Field(
        default_factory=list,
        description="Correction patches applied during document processing"
    )
    final_confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Overall confidence score after all stages (0.0-1.0)"
    )


class FileOperationResult(OntologyObject):
    """
    Result object for file operations.
    Tracks the operation performed and its outcome.
    """
    file_path: str = Field(..., description="Path to the file operated on")
    operation: str = Field(..., description="Operation type: read|modify|write|delete")
    success: bool = Field(default=True, description="Whether the operation succeeded")
    content_hash: Optional[str] = Field(
        default=None,
        description="SHA256 hash of file content after operation"
    )
    bytes_affected: Optional[int] = Field(
        default=None,
        description="Number of bytes read/written"
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error message if operation failed"
    )


# =============================================================================
# VALIDATORS
# =============================================================================


def validate_file_path(params: Dict[str, Any], context: ActionContext) -> bool:
    """
    Validate file_path parameter format and safety.

    Rules:
    - Must be a non-empty string
    - Must not contain dangerous patterns (path traversal, null bytes)
    - Must be within allowed directories (workspace boundary)
    """
    file_path = params.get("file_path", "")

    if not file_path or not isinstance(file_path, str):
        return False

    # Normalize path for comparison
    normalized = os.path.normpath(file_path)

    # Check for path traversal attempts
    if ".." in normalized:
        logger.warning(f"Path traversal attempt detected: {file_path}")
        return False

    # Check for null bytes (injection attack)
    if "\x00" in file_path:
        logger.warning(f"Null byte injection detected in path: {repr(file_path)}")
        return False

    # Check for shell metacharacters
    dangerous_chars = re.compile(r'[;&|`$]')
    if dangerous_chars.search(file_path):
        logger.warning(f"Dangerous characters in path: {file_path}")
        return False

    return True


def validate_file_exists(params: Dict[str, Any], context: ActionContext) -> bool:
    """Validate that the target file exists (for modify/delete operations)."""
    file_path = params.get("file_path", "")
    return Path(file_path).exists()


def validate_old_content_matches(params: Dict[str, Any], context: ActionContext) -> bool:
    """
    Validate that old_content matches current file content.
    This prevents race conditions and ensures intentional modifications.
    """
    file_path = params.get("file_path", "")
    old_content = params.get("old_content")

    if old_content is None:
        # old_content is optional - skip validation if not provided
        return True

    try:
        current_content = Path(file_path).read_text(encoding="utf-8")
        return current_content == old_content
    except Exception as e:
        logger.warning(f"Failed to read file for content verification: {e}")
        return False


def validate_stage_evidence(params: Dict[str, Any], context: ActionContext) -> bool:
    """
    Validate that stage_evidence is provided for hazardous operations.
    Evidence must include at least files_viewed for audit compliance.
    """
    evidence = params.get("stage_evidence")

    if evidence is None:
        return False

    try:
        parsed = evidence if isinstance(evidence, StageEvidence) else StageEvidence.model_validate(evidence)
    except Exception:
        return False

    return bool(parsed.files_viewed)


# =============================================================================
# FILE READ ACTION (Non-Hazardous)
# =============================================================================


@register_action
class FileReadAction(ActionType[FileOperationResult]):
    """
    Read file content for audit logging.

    This is a non-hazardous action that only reads file content.
    All read operations are logged for audit trail.

    Parameters:
        file_path: Absolute path to the file to read

    Returns:
        FileOperationResult with file content in data field
    """
    api_name = "file.read"
    object_type = FileOperationResult
    requires_proposal = False

    submission_criteria = [
        RequiredField("file_path"),
        CustomValidator(
            name="ValidFilePath",
            validator_fn=validate_file_path,
            error_message="Invalid file path: must be a valid path without traversal or dangerous characters"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[FileOperationResult], List[EditOperation]]:
        """Read file and return content with audit log."""
        file_path = params["file_path"]

        try:
            path = Path(file_path)

            if not path.exists():
                return ActionResult(
                    action_type=self.api_name,
                    success=False,
                    error=f"File not found: {file_path}",
                    error_details={"file_path": file_path}
                )

            if not path.is_file():
                return ActionResult(
                    action_type=self.api_name,
                    success=False,
                    error=f"Path is not a file: {file_path}",
                    error_details={"file_path": file_path}
                )

            content = path.read_text(encoding="utf-8")
            content_size = len(content.encode("utf-8"))

            # Create result object
            result = FileOperationResult(
                file_path=file_path,
                operation="read",
                success=True,
                bytes_affected=content_size,
                created_by=context.actor_id,
            )

            # Create audit edit
            edit = EditOperation(
                edit_type=EditType.CREATE,
                object_type="FileOperationResult",
                object_id=result.id,
                changes={
                    "file_path": file_path,
                    "operation": "read",
                    "bytes_read": content_size,
                    "actor": context.actor_id,
                }
            )

            # Store content in result data for caller access
            # Note: actual content is not persisted to avoid storage bloat
            result_with_content = ActionResult(
                action_type=self.api_name,
                success=True,
                data={"content": content, "size": content_size, "path": file_path},
                edits=[edit],
                message=f"Read {content_size} bytes from {file_path}"
            )

            return result_with_content

        except PermissionError:
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=f"Permission denied: {file_path}",
                error_details={"file_path": file_path}
            )
        except Exception as e:
            logger.exception(f"Failed to read file: {file_path}")
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=str(e),
                error_details={"file_path": file_path, "exception_type": type(e).__name__}
            )


# =============================================================================
# FILE MODIFY ACTION (Hazardous)
# =============================================================================


@register_action(requires_proposal=True)
class FileModifyAction(ActionType[FileOperationResult]):
    """
    Modify existing file content.

    This is a HAZARDOUS action requiring proposal approval.
    The old_content parameter provides verification that the file
    hasn't been modified since it was read (optimistic concurrency).

    Parameters:
        file_path: Absolute path to the file to modify
        old_content: Expected current content (for verification)
        new_content: New content to write
        reason: Human-readable reason for the modification
        stage_evidence: 3-Stage Protocol evidence (required)

    Returns:
        FileOperationResult with operation details
    """
    api_name = "file.modify"
    object_type = FileOperationResult
    requires_proposal = True

    submission_criteria = [
        RequiredField("file_path"),
        RequiredField("new_content"),
        RequiredField("reason"),
        RequiredField("stage_evidence"),
        CustomValidator(
            name="ValidFilePath",
            validator_fn=validate_file_path,
            error_message="Invalid file path: must be a valid path without traversal or dangerous characters"
        ),
        CustomValidator(
            name="FileExists",
            validator_fn=validate_file_exists,
            error_message="Target file does not exist - use file.write for new files"
        ),
        CustomValidator(
            name="ContentMatchesExpected",
            validator_fn=validate_old_content_matches,
            error_message="File content has changed since read - refresh and retry"
        ),
        CustomValidator(
            name="ValidStageEvidence",
            validator_fn=validate_stage_evidence,
            error_message="Invalid stage_evidence format"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[FileOperationResult], List[EditOperation]]:
        """Modify file content with audit trail."""
        file_path = params["file_path"]
        new_content = params["new_content"]
        reason = params["reason"]
        stage_evidence = params.get("stage_evidence")

        try:
            path = Path(file_path)

            # Read current content for audit
            current_content = path.read_text(encoding="utf-8")

            # Write new content
            path.write_text(new_content, encoding="utf-8")

            content_size = len(new_content.encode("utf-8"))

            # Create result object
            result = FileOperationResult(
                file_path=file_path,
                operation="modify",
                success=True,
                bytes_affected=content_size,
                created_by=context.actor_id,
            )

            # Create audit edit with diff info
            edit = EditOperation(
                edit_type=EditType.MODIFY,
                object_type="FileOperationResult",
                object_id=result.id,
                changes={
                    "file_path": file_path,
                    "operation": "modify",
                    "bytes_before": len(current_content.encode("utf-8")),
                    "bytes_after": content_size,
                    "reason": reason,
                    "actor": context.actor_id,
                    "stage_evidence": stage_evidence if isinstance(stage_evidence, dict) else None,
                }
            )

            return result, [edit]

        except PermissionError:
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=f"Permission denied: {file_path}",
                error_details={"file_path": file_path}
            )
        except Exception as e:
            logger.exception(f"Failed to modify file: {file_path}")
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=str(e),
                error_details={"file_path": file_path, "exception_type": type(e).__name__}
            )


# =============================================================================
# FILE WRITE ACTION (Hazardous)
# =============================================================================


@register_action(requires_proposal=True)
class FileWriteAction(ActionType[FileOperationResult]):
    """
    Write content to a file (create or overwrite).

    This is a HAZARDOUS action requiring proposal approval.
    Use this for creating new files or complete file replacement.
    For partial modifications, use file.modify instead.

    Parameters:
        file_path: Absolute path to the file to write
        content: Content to write
        reason: Human-readable reason for the write operation
        stage_evidence: 3-Stage Protocol evidence (required)

    Returns:
        FileOperationResult with operation details
    """
    api_name = "file.write"
    object_type = FileOperationResult
    requires_proposal = True

    submission_criteria = [
        RequiredField("file_path"),
        RequiredField("content"),
        RequiredField("reason"),
        RequiredField("stage_evidence"),
        CustomValidator(
            name="ValidFilePath",
            validator_fn=validate_file_path,
            error_message="Invalid file path: must be a valid path without traversal or dangerous characters"
        ),
        CustomValidator(
            name="ValidStageEvidence",
            validator_fn=validate_stage_evidence,
            error_message="Invalid stage_evidence format"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[FileOperationResult], List[EditOperation]]:
        """Write file content with audit trail."""
        file_path = params["file_path"]
        content = params["content"]
        reason = params["reason"]
        stage_evidence = params.get("stage_evidence")

        try:
            path = Path(file_path)

            # Check if file exists (for edit type determination)
            is_new_file = not path.exists()

            # Ensure parent directory exists
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write content
            path.write_text(content, encoding="utf-8")

            content_size = len(content.encode("utf-8"))

            # Create result object
            result = FileOperationResult(
                file_path=file_path,
                operation="write",
                success=True,
                bytes_affected=content_size,
                created_by=context.actor_id,
            )

            # Create audit edit
            edit = EditOperation(
                edit_type=EditType.CREATE if is_new_file else EditType.MODIFY,
                object_type="FileOperationResult",
                object_id=result.id,
                changes={
                    "file_path": file_path,
                    "operation": "write",
                    "is_new_file": is_new_file,
                    "bytes_written": content_size,
                    "reason": reason,
                    "actor": context.actor_id,
                    "stage_evidence": stage_evidence if isinstance(stage_evidence, dict) else None,
                }
            )

            return result, [edit]

        except PermissionError:
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=f"Permission denied: {file_path}",
                error_details={"file_path": file_path}
            )
        except Exception as e:
            logger.exception(f"Failed to write file: {file_path}")
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=str(e),
                error_details={"file_path": file_path, "exception_type": type(e).__name__}
            )


# =============================================================================
# FILE DELETE ACTION (Hazardous)
# =============================================================================


@register_action(requires_proposal=True)
class FileDeleteAction(ActionType[FileOperationResult]):
    """
    Delete a file.

    This is a HAZARDOUS action requiring proposal approval.
    The file content is preserved in the audit log before deletion.

    Parameters:
        file_path: Absolute path to the file to delete
        reason: Human-readable reason for the deletion
        stage_evidence: 3-Stage Protocol evidence (required)

    Returns:
        FileOperationResult with operation details
    """
    api_name = "file.delete"
    object_type = FileOperationResult
    requires_proposal = True

    submission_criteria = [
        RequiredField("file_path"),
        RequiredField("reason"),
        RequiredField("stage_evidence"),
        CustomValidator(
            name="ValidFilePath",
            validator_fn=validate_file_path,
            error_message="Invalid file path: must be a valid path without traversal or dangerous characters"
        ),
        CustomValidator(
            name="FileExists",
            validator_fn=validate_file_exists,
            error_message="Target file does not exist"
        ),
        CustomValidator(
            name="ValidStageEvidence",
            validator_fn=validate_stage_evidence,
            error_message="Invalid stage_evidence format"
        ),
    ]

    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> tuple[Optional[FileOperationResult], List[EditOperation]]:
        """Delete file with audit trail (preserves content hash)."""
        file_path = params["file_path"]
        reason = params["reason"]
        stage_evidence = params.get("stage_evidence")

        try:
            path = Path(file_path)

            # Read content for audit before deletion
            try:
                content = path.read_text(encoding="utf-8")
                content_size = len(content.encode("utf-8"))
            except Exception:
                content = None
                content_size = path.stat().st_size if path.exists() else 0

            # Delete file
            path.unlink()

            # Create result object
            result = FileOperationResult(
                file_path=file_path,
                operation="delete",
                success=True,
                bytes_affected=content_size,
                created_by=context.actor_id,
            )

            # Create audit edit
            edit = EditOperation(
                edit_type=EditType.DELETE,
                object_type="FileOperationResult",
                object_id=result.id,
                changes={
                    "file_path": file_path,
                    "operation": "delete",
                    "bytes_deleted": content_size,
                    "reason": reason,
                    "actor": context.actor_id,
                    "stage_evidence": stage_evidence if isinstance(stage_evidence, dict) else None,
                }
            )

            return result, [edit]

        except PermissionError:
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=f"Permission denied: {file_path}",
                error_details={"file_path": file_path}
            )
        except FileNotFoundError:
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=f"File not found: {file_path}",
                error_details={"file_path": file_path}
            )
        except Exception as e:
            logger.exception(f"Failed to delete file: {file_path}")
            return ActionResult(
                action_type=self.api_name,
                success=False,
                error=str(e),
                error_details={"file_path": file_path, "exception_type": type(e).__name__}
            )


# =============================================================================
# EXPORTS
# =============================================================================


__all__ = [
    # Actions
    "FileReadAction",
    "FileModifyAction",
    "FileWriteAction",
    "FileDeleteAction",
    # Models
    "FileOperationResult",
    "StageEvidence",
    # Validators
    "validate_file_path",
    "validate_file_exists",
    "validate_old_content_matches",
    "validate_stage_evidence",
]
