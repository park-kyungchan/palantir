
import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path("/home/palantir/orion-orchestrator-v2")))
from scripts.ontology.learning.persistence import LearnerRepository

async def verify():
    repo = LearnerRepository()
    await repo.initialize()
    
    user = "verify_bot_01"
    concept = "async_patterns"
    
    print(f"--- Verify Persistence for {user} ---")
    
    # 1. Initial State
    state = await repo.get_learner(user)
    initial_p = state.knowledge_components.get(concept).p_mastery if state.knowledge_components.get(concept) else 0.3
    print(f"Initial P(Mastery): {initial_p}")
    
    # 2. Record CORRECT interaction
    print("Recording CORRECT interaction...")
    new_p = await repo.record_interaction(user, concept, correct=True)
    print(f"New P(Mastery): {new_p:.4f}")
    
    if new_p > initial_p:
        print("✅ BKT Update Successful (Probability Increased)")
    else:
        print("❌ BKT Update Failed")
        
    # 3. Read back to visual confirm persistence
    state_reload = await repo.get_learner(user)
    saved_p = state_reload.knowledge_components[concept].p_mastery
    print(f"Persisted P: {saved_p:.4f}")

if __name__ == "__main__":
    asyncio.run(verify())
