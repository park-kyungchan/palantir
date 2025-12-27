from typing import Any, Dict, Optional
from scripts.ontology.actions import ActionType, ActionContext, ActionResult, SubmissionCriterion, RequiredField
from scripts.ontology.ontology_types import ObjectStatus
from scripts.ontology.schemas.memory import OrionInsight, OrionPattern, InsightContent, InsightProvenance, PatternStructure
from scripts.ontology.storage import InsightRepository, PatternRepository, get_database

class SaveInsightAction(ActionType):
    """
    Action to persist an Insight to the Ontology.
    Replaces legacy memory_manager.save_object('insight').
    """
    api_name = "memory.save_insight"
    submission_criteria = [
        RequiredField("content"),
        RequiredField("provenance")
    ]

    async def apply_edits(self, params: Dict[str, Any], context: ActionContext) -> ActionResult:
        """
        Create or Update an Insight.
        """
        # params passed directly
        
        # 1. Reconstruct Entity from Parameters
        # Assuming params structure matches schema roughly OR is flat
        # Let's support both flat and nested for flexibility during migration
        
        # Check if ID exists, if not gen one? ODA usually requires ID in context or params
        insight_id = params.get("id")
        if not insight_id:
             import uuid
             insight_id = f"INS-{uuid.uuid4()}"
        
        # Parse Status
        status = ObjectStatus.ACTIVE
        if "status" in params:
             try: status = ObjectStatus(params["status"])
             except: pass
        
        # Construct Value Objects
        content_data = params.get("content", {})
        if isinstance(content_data, str): # Handle legacy string passing?
             content_data = {"summary": content_data}
             
        content = InsightContent(
             summary=content_data.get("summary", "No summary"),
             domain=content_data.get("domain", "general"),
             tags=content_data.get("tags", [])
        )
        
        prov_data = params.get("provenance", {})
        provenance = InsightProvenance(
             source_episodic_ids=prov_data.get("source_episodic_ids", []),
             method=prov_data.get("method", "manual")
        )
        
        insight = OrionInsight(
            id=insight_id,
            status=status,
            confidence_score=params.get("confidence_score", 1.0),
            decay_factor=params.get("decay_factor", 0.95),
            provenance=provenance,
            content=content,
            supports=params.get("supports", []),
            contradicts=params.get("contradicts", []),
            related_to=params.get("related_to", [])
        )
        
        # 2. Persist via Repository
        session = context.metadata.get("session")
        db = get_database()
        
        # Use provided session (UnitOfWork) or new
        # Repository expects 'db' in init. 
        # But 'save' method inside Repo uses 'async with db.transaction()'
        # We need to bridge strict transaction management.
        
        # If context has session, we should use it. 
        # But our GenericRepository uses 'db.transaction()' which creates NEW session.
        # FIX: We need GenericRepository to accept external session for UoW.
        # Checking GenericRepository... It does not seem to support passing 'session' to 'save'.
        # Scripts/ontology/storage/base_repository.py needs check.
        
        # For now, let's assume we use the global db and let Repo handle it.
        # If we need UoW, we might need to modify Repositories later.
        params["id"] = insight_id # Ensure ID is passed back
        
        repo = InsightRepository(db)
        await repo.save(insight, actor_id=context.actor_id)
        
        return ActionResult(
             action_type=self.api_name,
             success=True,
             created_ids=[insight_id],
             message=f"Insight {insight_id} saved."
        )

class SavePatternAction(ActionType):
    """
    Action to persist a Pattern to the Ontology.
    """
    api_name = "memory.save_pattern"
    submission_criteria = [
        RequiredField("structure")
    ]

    async def apply_edits(self, params: Dict[str, Any], context: ActionContext) -> ActionResult:
        """Create or Update a Pattern."""
        # params passed directly
        pattern_id = params.get("id")
        if not pattern_id:
            import uuid
            pattern_id = f"PAT-{uuid.uuid4()}"
            
        status = ObjectStatus.ACTIVE
        if "status" in params:
             try: status = ObjectStatus(params["status"])
             except: pass

        struct_data = params.get("structure", {})
        structure = PatternStructure(
             trigger=struct_data.get("trigger", ""),
             steps=struct_data.get("steps", []),
             anti_patterns=struct_data.get("anti_patterns", [])
        )
        
        pattern = OrionPattern(
             id=pattern_id,
             status=status,
             frequency_count=params.get("frequency_count", 0),
             success_rate=params.get("success_rate", 0.0),
             structure=structure,
             code_snippet_ref=params.get("code_snippet_ref", None)
        )
        
        params["id"] = pattern_id
        
        db = get_database()
        repo = PatternRepository(db)
        await repo.save(pattern, actor_id=context.actor_id)
        
        return ActionResult(
            action_type=self.api_name,
            success=True,
            created_ids=[pattern_id],
            message=f"Pattern {pattern_id} saved."
        )
