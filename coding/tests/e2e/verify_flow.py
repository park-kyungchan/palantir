import asyncio
import sys
import logging
from datetime import datetime
from pathlib import Path

# Setup paths
PROJECT_ROOT = Path("/home/palantir/orion-orchestrator-v2")
CODING_ROOT = PROJECT_ROOT / "coding"
sys.path.insert(0, str(CODING_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("E2E_TEST")

# Mock ActionContext
class MockActionContext:
    pass

async def run_test():
    logger.info("Starting E2E Simulation: 'The OSDK Journey'")
    
    # Import Actions (This validates imports work)
    try:
        from scripts.ontology.fde_learning.actions import (
            GetRecommendationAction,
            RecordAttemptAction,
            LearnerObject
        )
        # Ensure clean state
        db_path = CODING_ROOT / "palantir-fde-learning/learner_state.db"
        if db_path.exists():
            logger.info("Cleaning up previous test DB...")
            # db_path.unlink() # Optional: Keep persistence to test re-entrancy? 
            # Let's delete to ensure clean test
            try:
                db_path.unlink()
            except PermissionError:
                pass

        learner_id = "learner_e2e_001"
        context = MockActionContext()
        
        # --- STEP 1: Initial Recommendation ---
        logger.info("\n--- STEP 1: Initial Recommendation ---")
        rec_action = GetRecommendationAction()
        result_obj, _ = await rec_action.apply_edits(
            {"learner_id": learner_id, "limit": 1}, context
        )
        
        recs = result_obj.recommendations or []
        if not recs:
            logger.error("FAIL: No recommendations returned!")
            return
        
        first_rec_id = recs[0]["concept_id"]
        logger.info(f"Recommended: {first_rec_id} (Rationale: {recs[0]['rationale']})")
        
        # --- STEP 2: Learning Loop (Simulate Mastery) ---
        logger.info(f"\n--- STEP 2: Mastering {first_rec_id} ---")
        record_action = RecordAttemptAction()
        
        for i in range(5):
            learner, edits = await record_action.apply_edits(
                {"learner_id": learner_id, "concept_id": first_rec_id, "correct": True},
                context
            )
            changes = edits[0].changes
            logger.info(f"Attempt {i+1}: Mastery -> {changes['new_mastery']:.4f} (Mastered: {changes['is_mastered']})")
            
            if changes['is_mastered']:
                logger.info(">>> CONCEPT MASTERED! <<<")
                break
        
        # --- STEP 3: Verify Adaptation ---
        logger.info("\n--- STEP 3: Get New Recommendation ---")
        result_obj_2, _ = await rec_action.apply_edits(
            {"learner_id": learner_id, "limit": 1}, context
        )
        
        new_recs = result_obj_2.recommendations or []
        if not new_recs:
             logger.error("FAIL: No follow-up recommendations!")
             return

        next_rec_id = new_recs[0]["concept_id"]
        logger.info(f"New Recommendation: {next_rec_id}")
        
        if next_rec_id == first_rec_id:
            logger.error("FAIL: System recommended the same mastered concept!")
        else:
            logger.info("SUCCESS: System recommended a NEW concept!")
            logger.info(f"Transition: {first_rec_id} -> {next_rec_id}")

    except Exception as e:
        logger.exception("Test Failed with Exception")
        raise

if __name__ == "__main__":
    asyncio.run(run_test())
