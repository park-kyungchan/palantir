# scripts/ontology/fde_learning/actions.py
"""
FDE Learning ActionTypes for Orion ODA Integration.

These ActionTypes wrap the Palantir FDE Learning System's core functionality,
exposing it through Orion's Action Registry for use by the Kernel.

Actions:
- RecordAttemptAction: Record a learning attempt and update BKT mastery
- GetRecommendationAction: Get ZPD-based concept recommendations
- SyncLearnerStateAction: Sync learner state between FDE and Orion

All actions follow Palantir ODA patterns:
- Declarative class-based definitions
- SubmissionCriteria for parameter validation
- EditOperations for audit trail
- SideEffects for async post-processing
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from typing import Any, ClassVar, Dict, List, Optional, Tuple, Type

from pydantic import BaseModel, Field

# Add coding directory to path for FDE Learning imports
_CODING_PATH = "/home/palantir/orion-orchestrator-v2/coding"
if _CODING_PATH not in sys.path:
    sys.path.insert(0, _CODING_PATH)

from scripts.ontology.actions import (
    ActionContext,
    ActionResult,
    ActionType,
    EditOperation,
    EditType,
    RequiredField,
    RangeValidator,
    register_action,
    action_registry,
)
from scripts.ontology.ontology_types import OntologyObject

logger = logging.getLogger(__name__)


# =============================================================================
# LEARNER OBJECT (Ontology Object Type)
# =============================================================================

class LearnerObject(OntologyObject):
    """
    OntologyObject representing a Learner in the FDE Learning System.
    
    This object type syncs with the FDE Learning System's LearnerProfile,
    providing Ontology-level access to mastery data.
    """
    learner_id: str = Field(..., description="External learner identifier")
    overall_mastery: float = Field(0.0, ge=0.0, le=1.0, description="Overall mastery level")
    concepts_mastered: int = Field(0, ge=0, description="Number of mastered concepts")
    total_attempts: int = Field(0, ge=0, description="Total practice attempts")
    last_activity: Optional[datetime] = Field(None, description="Last learning activity")
    recommendations: Optional[List[Dict[str, Any]]] = Field(None, description="Transient recommendations")


# =============================================================================
# RECORD ATTEMPT ACTION
# =============================================================================

@register_action
class RecordAttemptAction(ActionType[LearnerObject]):
    """
    Record a learning attempt and update BKT mastery.
    
    This action integrates with the FDE Learning System's BKT algorithm
    to update mastery estimates based on learner responses.
    
    Parameters:
        learner_id: Unique identifier of the learner
        concept_id: ID of the concept being practiced
        correct: Whether the response was correct
        response_time_ms: Optional response time in milliseconds
    
    Returns:
        Updated LearnerObject with new mastery values
    """
    
    api_name: ClassVar[str] = "fde.record_attempt"
    object_type: ClassVar[Type[LearnerObject]] = LearnerObject
    submission_criteria: ClassVar[List[Any]] = [
        RequiredField("learner_id"),
        RequiredField("concept_id"),
    ]
    requires_proposal: ClassVar[bool] = False  # Non-hazardous
    
    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> Tuple[Optional[LearnerObject], List[EditOperation]]:
        """Apply BKT update based on learner attempt."""
        learner_id = params["learner_id"]
        concept_id = params["concept_id"]
        correct = params.get("correct", True)
        
        edits: List[EditOperation] = []
        
        try:
            # Import FDE Learning components
            from palantir_fde_learning.domain.bkt import (
                BKTModel,
                BKTState,
                get_bkt_model,
            )
            from palantir_fde_learning.domain.types import LearnerProfile, KnowledgeComponentState
            from palantir_fde_learning.adapters.repository.sqlite import SQLiteLearnerRepository
            
            # Initialize repository
            # Use a persistent path in the data directory
            db_path = "/home/palantir/orion-orchestrator-v2/coding/palantir-fde-learning/learner_state.db"
            repo = SQLiteLearnerRepository(db_path=db_path)
            
            # Load existing profile or create new
            profile = await repo.find_by_id(learner_id)
            if not profile:
                profile = LearnerProfile(learner_id=learner_id)
            
            # Get or create BKT model (use interview preset for FDE prep)
            bkt = get_bkt_model("interview")
            
            # Get current KC state
            current_kc = profile.knowledge_states.get(concept_id)
            
            # Map to BKTState
            if current_kc:
                bkt_state = BKTState(
                    mastery=current_kc.mastery_level,
                    attempts=current_kc.practice_count,
                    correct=current_kc.correct_count,
                )
            else:
                bkt_state = BKTState()
            
            # Update mastery based on attempt
            new_bkt_state = bkt.update(bkt_state, correct=correct)
            
            # Calculate streak
            streak_current = 0
            streak_best = 0
            if current_kc:
                streak_best = current_kc.streak_best
                if correct:
                    streak_current = current_kc.streak_current + 1
                    streak_best = max(streak_best, streak_current)
                else:
                    streak_current = 0
            elif correct:
                streak_current = 1
                streak_best = 1

            # Map back to KnowledgeComponentState
            new_kc = KnowledgeComponentState(
                concept_id=concept_id,
                mastery_level=new_bkt_state.mastery,
                last_accessed=datetime.now(timezone.utc),
                practice_count=new_bkt_state.attempts,
                correct_count=new_bkt_state.correct,
                streak_current=streak_current,
                streak_best=streak_best,
            )
            
            # Update profile with new state
            profile.knowledge_states[concept_id] = new_kc
            
            # Persist changes
            await repo.save(profile)
            
            # Create/update LearnerObject for Ontology
            learner = LearnerObject(
                learner_id=learner_id,
                overall_mastery=profile.overall_mastery(),
                concepts_mastered=len(profile.get_mastered_concepts()),
                total_attempts=sum(s.practice_count for s in profile.knowledge_states.values()),
                last_activity=datetime.now(timezone.utc),
            )
            
            edits.append(EditOperation(
                edit_type=EditType.MODIFY,
                object_type="LearnerObject",
                object_id=learner_id,
                changes={
                    "concept_id": concept_id,
                    "correct": correct,
                    "new_mastery": new_bkt_state.mastery,
                    "is_mastered": new_bkt_state.is_mastered,
                },
            ))
            
            logger.info(
                f"RecordAttempt: {learner_id} on {concept_id} "
                f"(correct={correct}, mastery={new_bkt_state.mastery:.2%})"
            )
            
            return learner, edits
            
        except ImportError as e:
            logger.error(f"FDE Learning not installed: {e}")
            raise RuntimeError("FDE Learning System not available") from e


# =============================================================================
# GET RECOMMENDATION ACTION
# =============================================================================

@register_action
class GetRecommendationAction(ActionType[LearnerObject]):
    """
    Get ZPD-based concept recommendations for a learner.
    
    This action uses the FDE Learning System's ScopingEngine to generate
    personalized learning recommendations based on Zone of Proximal Development.
    
    Parameters:
        learner_id: Unique identifier of the learner
        limit: Maximum number of recommendations (default: 5)
        domain: Optional domain filter
    
    Returns:
        ActionResult with recommended concepts in data field
    """
    
    api_name: ClassVar[str] = "fde.get_recommendation"
    object_type: ClassVar[Type[LearnerObject]] = LearnerObject
    submission_criteria: ClassVar[List[Any]] = [
        RequiredField("learner_id"),
        RangeValidator("limit", min_value=1, max_value=20),
    ]
    requires_proposal: ClassVar[bool] = False  # Read-only action
    
    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> Tuple[Optional[LearnerObject], List[EditOperation]]:
        """Generate ZPD-based recommendations."""
        learner_id = params["learner_id"]
        limit = params.get("limit", 5)
        domain_filter = params.get("domain")
        
        try:
            from palantir_fde_learning.domain.types import LearnerProfile
            from palantir_fde_learning.application.scoping import ScopingEngine
            from palantir_fde_learning.adapters.repository.sqlite import SQLiteLearnerRepository
            from palantir_fde_learning.adapters.kb_reader import KBReader
            
            # Initialize repository
            db_path = "/home/palantir/orion-orchestrator-v2/coding/palantir-fde-learning/learner_state.db"
            repo = SQLiteLearnerRepository(db_path=db_path)
            
            # Load existing profile or create new
            profile = await repo.find_by_id(learner_id)
            if not profile:
                profile = LearnerProfile(learner_id=learner_id)
            
            # Load Concept Library
            # KB files are in the data directory
            kb_root = "/home/palantir/orion-orchestrator-v2/coding/palantir-fde-learning/knowledge_bases"
            reader = KBReader(kb_root=kb_root)
            concepts = reader.build_concept_library()
            
            # Get recommendations from ScopingEngine
            engine = ScopingEngine(concepts=concepts, learner_profile=profile)
            recommendations = engine.recommend_next_concept(
                limit=limit,
                domain_filter=domain_filter
            )
            
            # Create result object with recommendations
            learner = LearnerObject(
                learner_id=learner_id,
                overall_mastery=profile.overall_mastery(),
            )
            
            # Add recommendations to metadata (will be in ActionResult.data)
            learner.recommendations = [
                {
                    "concept_id": rec.concept.concept_id,
                    "title": rec.concept.title,
                    "difficulty": rec.concept.difficulty_tier.value,
                    "domain": rec.concept.domain.value,
                    "estimated_minutes": rec.concept.estimated_minutes,
                    "rationale": rec.rationale, # Added rationale
                    "priority": rec.priority,   # Added priority
                }
                for rec in recommendations
            ]
            
            logger.info(
                f"GetRecommendation: {learner_id} received {len(recommendations)} recommendations"
            )
            
            return learner, []  # No edits for read-only action
            
        except ImportError as e:
            logger.error(f"FDE Learning not installed: {e}")
            raise RuntimeError("FDE Learning System not available") from e


# =============================================================================
# SYNC LEARNER STATE ACTION
# =============================================================================

@register_action(requires_proposal=True)  # Hazardous - syncs external data
class SyncLearnerStateAction(ActionType[LearnerObject]):
    """
    Sync learner state between FDE Learning System and Orion.
    
    This action synchronizes the complete learner state from the FDE
    Learning System's persistence layer to Orion's Ontology.
    
    Marked as hazardous (requires_proposal=True) because it:
    - Modifies multiple objects
    - Syncs external data source
    - May overwrite existing Ontology state
    
    Parameters:
        learner_id: Unique identifier of the learner
        sync_direction: "fde_to_orion" or "orion_to_fde"
        force: If True, overwrite even if local is newer
    
    Returns:
        Updated LearnerObject with synced state
    """
    
    api_name: ClassVar[str] = "fde.sync_learner_state"
    object_type: ClassVar[Type[LearnerObject]] = LearnerObject
    submission_criteria: ClassVar[List[Any]] = [
        RequiredField("learner_id"),
    ]
    requires_proposal: ClassVar[bool] = True  # Hazardous action
    
    async def apply_edits(
        self,
        params: Dict[str, Any],
        context: ActionContext
    ) -> Tuple[Optional[LearnerObject], List[EditOperation]]:
        """Sync learner state between systems."""
        learner_id = params["learner_id"]
        sync_direction = params.get("sync_direction", "fde_to_orion")
        force = params.get("force", False)
        
        edits: List[EditOperation] = []
        
        try:
            from palantir_fde_learning.adapters.repository.sqlite import (
                SQLiteLearnerRepository,
            )
            
            # Initialize repository
            repo = SQLiteLearnerRepository()
            
            if sync_direction == "fde_to_orion":
                # Load profile from FDE persistence
                profile = await repo.find_by_id(learner_id)
                
                if profile is None:
                    logger.warning(f"Learner {learner_id} not found in FDE")
                    return None, []
                
                # Convert to LearnerObject
                learner = LearnerObject(
                    learner_id=learner_id,
                    overall_mastery=profile.overall_mastery,
                    concepts_mastered=len([
                        kc for kc in profile.knowledge_components.values()
                        if kc.is_mastered()
                    ]),
                    total_attempts=sum(
                        kc.practice_count 
                        for kc in profile.knowledge_components.values()
                    ),
                    last_activity=profile.last_activity_at,
                )
                
                edits.append(EditOperation(
                    edit_type=EditType.MODIFY,
                    object_type="LearnerObject",
                    object_id=learner_id,
                    changes={
                        "sync_direction": sync_direction,
                        "force": force,
                        "synced_at": datetime.now(timezone.utc).isoformat(),
                    },
                ))
                
                logger.info(f"SyncLearnerState: Synced {learner_id} from FDE to Orion")
                return learner, edits
            
            else:
                # orion_to_fde sync (future implementation)
                logger.warning("orion_to_fde sync not yet implemented")
                return None, []
                
        except ImportError as e:
            logger.error(f"FDE Learning not installed: {e}")
            raise RuntimeError("FDE Learning System not available") from e


# =============================================================================
# REGISTRATION HELPER
# =============================================================================

def register_fde_learning_actions() -> List[str]:
    """
    Register all FDE Learning actions with the Orion Action Registry.
    
    Call this during Orion initialization to enable FDE Learning integration.
    
    Returns:
        List of registered action api_names
    """
    actions = [
        RecordAttemptAction,
        GetRecommendationAction,
        SyncLearnerStateAction,
    ]
    
    registered = []
    for action in actions:
        if action.api_name not in action_registry.list_actions():
            # Already registered via decorator, just verify
            pass
        registered.append(action.api_name)
    
    logger.info(f"FDE Learning actions registered: {registered}")
    return registered


# =============================================================================
# EXPORTS
# =============================================================================

__all__ = [
    "LearnerObject",
    "RecordAttemptAction",
    "GetRecommendationAction",
    "SyncLearnerStateAction",
    "register_fde_learning_actions",
]
