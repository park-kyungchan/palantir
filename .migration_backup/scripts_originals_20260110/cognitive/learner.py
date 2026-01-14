from typing import Optional
from datetime import datetime

from lib.oda.cognitive.types import LearnerState, KnowledgeComponent
from lib.oda.ontology.objects.learning import Learner
from lib.oda.ontology.storage.learner_repository import LearnerRepository
from lib.oda.ontology.actions.learning_actions import SaveLearnerStateAction
from lib.oda.simulation.core import ActionRunner, ActionContext
from lib.oda.ontology.storage.database import get_database

class LearnerManager:
    """
    Manages learner state and applies Bayesian Knowledge Tracing (BKT).
    """
    
    def __init__(self):
        self.repo = LearnerRepository()
        self.runner = ActionRunner(get_database())

    async def get_state(self, user_id: str) -> LearnerState:
        """Retrieve current learner state or initialize new one."""
        domain_obj = await self.repo.get_by_user_id(user_id)
        
        if domain_obj:
            # Map Domain Object (Dict) to Pydantic Models
            kcs = {}
            if domain_obj.knowledge_state:
                for k, v in domain_obj.knowledge_state.items():
                    # Ensure we handle partial data or deserialization
                    if isinstance(v, dict):
                        kcs[k] = KnowledgeComponent(**v)
                    else:
                        # Fallback or error
                        pass
            
            return LearnerState(
                user_id=domain_obj.user_id,
                theta=domain_obj.theta,
                knowledge_components=kcs,
                last_active=datetime.fromisoformat(domain_obj.last_active) if domain_obj.last_active else datetime.now()
            )
        else:
            # New Learner
            return LearnerState(
                user_id=user_id,
                theta=0.0, # Neutral starting proficiency
                knowledge_components={}
            )

    async def update_concept_mastery(self, user_id: str, concept_id: str, success: bool) -> LearnerState:
        """
        Apply BKT to update mastery probability for a specific concept.
        """
        state = await self.get_state(user_id)
        
        # Get or Initialize Concept
        if concept_id not in state.knowledge_components:
            kc = KnowledgeComponent(id=concept_id, name=concept_id, mastery_probability=0.1)
            state.knowledge_components[concept_id] = kc
        else:
            kc = state.knowledge_components[concept_id]
            
        # --- BKT Logic ---
        p_known = kc.mastery_probability
        p_slip = kc.slip_probability
        p_guess = kc.guess_probability
        p_learn = kc.learning_rate
        
        if success:
            # P(L|Correct)
            numerator = p_known * (1 - p_slip)
            denominator = numerator + (1 - p_known) * p_guess
            p_posterior = numerator / denominator if denominator > 0 else 0
        else:
            # P(L|Incorrect)
            numerator = p_known * p_slip
            denominator = numerator + (1 - p_known) * (1 - p_guess)
            p_posterior = numerator / denominator if denominator > 0 else 0
            
        # Update with learning rate
        p_new = p_posterior + (1 - p_posterior) * p_learn
        
        # Clip to [0, 1]
        p_new = max(0.0, min(1.0, p_new))
        
        # Update State in memory
        kc.mastery_probability = p_new
        state.knowledge_components[concept_id] = kc
        state.last_active = datetime.now()
        
        # Update Theta (Simple heuristic for now)
        # If success on hard concept -> increase theta
        # For now, just drift slightly
        if success:
            state.theta += 0.05
        else:
            state.theta -= 0.02
        state.theta = max(-3.0, min(3.0, state.theta))
        
        # Persist
        await self._save_state(state)
        
        return state

    async def _save_state(self, state: LearnerState):
        """Map Logic State back to Domain Object and Save via Action."""
        
        params = {
            "user_id": state.user_id,
            "theta": state.theta,
            "knowledge_state": {k: v.model_dump() for k, v in state.knowledge_components.items()},
            "last_active": state.last_active.isoformat()
        }
        
        ctx = ActionContext(actor_id=state.user_id)
        ctx.parameters = params
        
        action = SaveLearnerStateAction()
        await self.runner.execute(action, ctx)
