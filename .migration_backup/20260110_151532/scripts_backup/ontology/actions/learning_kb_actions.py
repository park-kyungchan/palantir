"""
ODA Learning KB Actions
======================

Knowledge Base 콘텐츠 관리를 위한 ODA 액션 타입 정의.
Antigravity IDE의 Claude Opus가 `/coding` 디렉토리 개선 시 사용.

Usage:
    from scripts.ontology.actions.learning_kb_actions import (
        UpdateLearningKBAction,
        ValidateKBStructureAction,
        VerifyTutorEngineAction
    )
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, ClassVar, Optional

from scripts.ontology.actions import (
    ActionContext,
    ActionResult,
    ActionType,
    EditOperation,
    EditType,
    RequiredField,
    MaxLength,
    register_action,
)
from scripts.ontology.objects.core_definitions import Artifact


# =============================================================================
# KB Update Action (Proposal Required)
# =============================================================================

@register_action(requires_proposal=True)
class UpdateLearningKBAction(ActionType[Artifact]):
    """
    Knowledge Base 콘텐츠 업데이트 액션.

    Proposal 승인 후 실행됩니다.
    모든 KB 수정은 이 액션을 통해 수행되어야 합니다.

    Parameters:
        kb_id: KB 파일 식별자 (예: "01", "02", ...)
        section: 수정할 섹션 이름 (예: "Practice Exercise")
        content: 새로운 콘텐츠

    Example:
        >>> action = UpdateLearningKBAction()
        >>> result = await action.execute({
        ...     "kb_id": "01",
        ...     "section": "Practice Exercise",
        ...     "content": "## Practice Exercise\\n\\n..."
        ... }, context)
    """

    api_name: ClassVar[str] = "learning.update_kb"
    object_type: ClassVar[type] = Artifact

    submission_criteria: ClassVar[list] = [
        RequiredField("kb_id"),
        RequiredField("section"),
        RequiredField("content"),
        MaxLength("content", 50000),  # 50KB 제한
    ]

    # 유효한 섹션 목록
    VALID_SECTIONS: ClassVar[list[str]] = [
        "Universal Concept",
        "Technical Explanation",
        "Cross-Stack Comparison",
        "Palantir Context",
        "Design Philosophy",
        "Practice Exercise",
        "Adaptive Next Steps",
    ]

    async def apply_edits(
        self,
        params: dict[str, Any],
        context: ActionContext,
    ) -> tuple[Optional[Artifact], list[EditOperation]]:
        """KB 파일 업데이트 적용."""

        kb_id = params["kb_id"]
        section = params["section"]
        content = params["content"]

        # 섹션 유효성 검증
        if section not in self.VALID_SECTIONS:
            raise ValueError(
                f"Invalid section '{section}'. Must be one of: {self.VALID_SECTIONS}"
            )

        # KB 파일 경로 결정
        kb_base = Path("coding/knowledge_bases")
        kb_files = list(kb_base.glob(f"{kb_id}_*.md"))

        if not kb_files:
            raise FileNotFoundError(f"KB file not found for id: {kb_id}")

        kb_path = kb_files[0]

        # Artifact 생성
        artifact = Artifact(
            path=str(kb_path),
            type="markdown",
            produced_by_task_id=f"kb_update_{kb_id}_{section.replace(' ', '_').lower()}",
            created_by=context.actor_id,
        )

        # Edit 기록
        edit = EditOperation(
            edit_type=EditType.MODIFY,
            object_type="Artifact",
            object_id=artifact.id,
            changes={
                "kb_id": kb_id,
                "kb_path": str(kb_path),
                "section": section,
                "content_length": len(content),
                "content_preview": content[:200] + "..." if len(content) > 200 else content,
            },
            timestamp=context.timestamp,
        )

        return artifact, [edit]


# =============================================================================
# KB Validation Action (Immediate)
# =============================================================================

@register_action(requires_proposal=False)
class ValidateKBStructureAction(ActionType[None]):
    """
    KB 7-컴포넌트 구조 검증 액션.

    읽기 전용 액션으로, Proposal 없이 즉시 실행 가능합니다.

    Parameters:
        kb_path: 검증할 KB 파일 경로 (또는 glob 패턴)

    Returns:
        ActionResult with validation details in edits[0].changes

    Example:
        >>> result = await ValidateKBStructureAction().execute({
        ...     "kb_path": "coding/knowledge_bases/01_*.md"
        ... }, context)
        >>> print(result.edits[0].changes["missing_sections"])
    """

    api_name: ClassVar[str] = "learning.validate_kb"
    object_type: ClassVar[type] = type(None)

    REQUIRED_SECTIONS: ClassVar[list[str]] = [
        "Universal Concept",
        "Technical Explanation",
        "Cross-Stack Comparison",
        "Palantir Context",
        "Design Philosophy",
        "Practice Exercise",
        "Adaptive Next Steps",
    ]

    async def apply_edits(
        self,
        params: dict[str, Any],
        context: ActionContext,
    ) -> tuple[None, list[EditOperation]]:
        """KB 구조 검증 (읽기 전용)."""

        kb_path_pattern = params.get("kb_path", "")

        # Glob 패턴 처리
        if "*" in kb_path_pattern:
            kb_files = list(Path(".").glob(kb_path_pattern))
        else:
            kb_files = [Path(kb_path_pattern)]

        results = []

        for kb_file in kb_files:
            if not kb_file.exists():
                results.append({
                    "path": str(kb_file),
                    "error": "File not found",
                    "is_valid": False,
                })
                continue

            content = kb_file.read_text(encoding="utf-8")

            # 섹션 검증
            missing = []
            found = []
            for section in self.REQUIRED_SECTIONS:
                # ## 또는 # 헤더 검색
                if f"## {section}" in content or f"# {section}" in content:
                    found.append(section)
                else:
                    missing.append(section)

            results.append({
                "path": str(kb_file),
                "found_sections": found,
                "missing_sections": missing,
                "is_valid": len(missing) == 0,
                "completion_rate": f"{len(found)}/{len(self.REQUIRED_SECTIONS)}",
            })

        # 검증 결과 기록
        edit = EditOperation(
            edit_type=EditType.CREATE,  # 검증 결과 생성
            object_type="KBValidation",
            object_id=f"validate_{context.timestamp.isoformat()}",
            changes={
                "pattern": kb_path_pattern,
                "files_checked": len(results),
                "results": results,
                "all_valid": all(r["is_valid"] for r in results),
            },
            timestamp=context.timestamp,
        )

        return None, [edit]


# =============================================================================
# Tutor Engine Verification Action (Immediate)
# =============================================================================

@register_action(requires_proposal=False)
class VerifyTutorEngineAction(ActionType[None]):
    """
    ZPD ScopingEngine 기능 검증 액션.

    튜터 엔진이 올바르게 작동하는지 테스트합니다.

    Parameters:
        kb_path: Knowledge Base 디렉토리 경로
        user_id: 테스트 사용자 ID (기본값: "test_user")
        limit: 추천 개수 (기본값: 3)

    Example:
        >>> result = await VerifyTutorEngineAction().execute({
        ...     "kb_path": "coding/knowledge_bases"
        ... }, context)
        >>> print(result.edits[0].changes["status"])  # "PASS" or "FAIL"
    """

    api_name: ClassVar[str] = "learning.verify_tutor"
    object_type: ClassVar[type] = type(None)

    async def apply_edits(
        self,
        params: dict[str, Any],
        context: ActionContext,
    ) -> tuple[None, list[EditOperation]]:
        """튜터 엔진 기능 테스트."""

        kb_path = params.get("kb_path", "coding/knowledge_bases")
        user_id = params.get("user_id", "test_user")
        limit = params.get("limit", 3)

        verification_result = {
            "kb_path": kb_path,
            "user_id": user_id,
            "limit": limit,
            "timestamp": context.timestamp.isoformat(),
        }

        try:
            # 동적 임포트 (coding 디렉토리의 모듈)
            import sys
            sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "coding"))

            from palantir_fde_learning import ScopingEngine, LearnerProfile
            from palantir_fde_learning.adapters import KBReader

            # KB 읽기
            reader = KBReader(kb_path)
            concepts = reader.build_concept_library()
            verification_result["concepts_loaded"] = len(concepts)

            # 프로필 생성
            profile = LearnerProfile(user_id=user_id)

            # 엔진 생성 및 추천
            engine = ScopingEngine(concepts, profile)
            recommendations = engine.recommend_next_concept(limit=limit)

            # 결과 기록
            verification_result["recommendations_count"] = len(recommendations)
            verification_result["recommendations"] = [
                {
                    "name": rec.concept.name,
                    "domain": rec.concept.domain.value if hasattr(rec.concept, "domain") else "unknown",
                    "stretch_factor": round(rec.stretch_factor, 3),
                    "in_zpd": 0.1 <= rec.stretch_factor <= 0.3,
                }
                for rec in recommendations
            ]

            # 성공 판정
            verification_result["status"] = "PASS" if len(recommendations) > 0 else "WARN_NO_RECOMMENDATIONS"
            verification_result["error"] = None

        except ImportError as e:
            verification_result["status"] = "FAIL_IMPORT"
            verification_result["error"] = f"Import error: {e}"
        except Exception as e:
            verification_result["status"] = "FAIL_RUNTIME"
            verification_result["error"] = f"Runtime error: {e}"

        # Edit 기록
        edit = EditOperation(
            edit_type=EditType.CREATE,
            object_type="TutorVerification",
            object_id=f"verify_tutor_{context.timestamp.isoformat()}",
            changes=verification_result,
            timestamp=context.timestamp,
        )

        return None, [edit]


# =============================================================================
# Batch Validation Helper
# =============================================================================

async def validate_all_kbs(context: ActionContext) -> dict[str, Any]:
    """
    모든 KB 파일의 7-컴포넌트 구조를 일괄 검증합니다.

    Returns:
        검증 결과 요약 딕셔너리
    """
    action = ValidateKBStructureAction()
    result = await action.execute(
        {"kb_path": "coding/knowledge_bases/*.md"},
        context,
    )

    if result.success:
        changes = result.edits[0].changes
        summary = {
            "total_files": changes["files_checked"],
            "all_valid": changes["all_valid"],
            "invalid_kbs": [
                r["path"] for r in changes["results"] if not r["is_valid"]
            ],
            "missing_sections_by_kb": {
                r["path"]: r["missing_sections"]
                for r in changes["results"]
                if r["missing_sections"]
            },
        }
        return summary
    else:
        return {"error": result.error}


# =============================================================================
# Action Registration Check
# =============================================================================

def get_registered_learning_actions() -> list[str]:
    """등록된 학습 관련 액션 목록 반환."""
    return [
        "learning.update_kb",
        "learning.validate_kb",
        "learning.verify_tutor",
    ]
