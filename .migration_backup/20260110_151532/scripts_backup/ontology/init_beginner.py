import asyncio
from scripts.ontology.storage.database import initialize_database
from scripts.ontology.storage.learner_repository import LearnerRepository
from scripts.ontology.objects.learning import Learner
from scripts.ontology.run_tutor import run_session_generation

async def main():
    print("🎓 Initializing Beginner Learning Path (Theta = -2.0)...")
    await initialize_database()
    
    repo = LearnerRepository()
    user_id = "palantir_beginner"
    
    # Create/Reset Beginner User
    learner = Learner(
        user_id=user_id,
        theta=-2.0, # Novice Level
        knowledge_state={},
        last_active=""
    )
    await repo.save(learner)
    print(f"✅ User '{user_id}' set to Novice level.")
    
    # Generate Curriculum from ODA Core
    print(f"📘 Scanning ODA Core (scripts/ontology)...")
    await run_session_generation(
        target_path="scripts/ontology",
        user_id=user_id,
        db_mode="oda",
        limit=3,
        theta=-2.0,
        role="auto",
        entrypoint=None,
        prompt=None,
        prompt_limit=12,
        brief=False,
        brief_path=None,
    )

if __name__ == "__main__":
    asyncio.run(main())
