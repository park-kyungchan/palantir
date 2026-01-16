import pytest

from lib.oda.cognitive.learner import LearnerManager
from lib.oda.ontology.learning.persistence import LearnerRepository as LegacyLearnerRepository
from lib.oda.ontology.learning.types import LearnerState as LegacyLearnerState
from lib.oda.ontology.objects.learning import Learner
from lib.oda.ontology.storage.database import Database, DatabaseManager
from lib.oda.osdk.query import ObjectQuery


@pytest.mark.asyncio
async def test_learner_manager_update_twice_and_osdk_query_real(tmp_path) -> None:
    db = Database(tmp_path / "e2e_learning_osdk.db")
    await db.initialize()
    token = DatabaseManager.set_context(db)

    try:
        mgr = LearnerManager()

        state1 = await mgr.update_concept_mastery("u1", "concept_a", success=True)
        state2 = await mgr.update_concept_mastery("u1", "concept_a", success=False)

        assert state1.user_id == "u1"
        assert state2.user_id == "u1"

        learners = await (
            ObjectQuery(Learner)
            .where("user_id", "eq", "u1")
            .limit(10)
            .execute()
        )
        assert len(learners) == 1
        assert learners[0].user_id == "u1"

    finally:
        DatabaseManager.reset_context(token)
        await db.dispose()


@pytest.mark.asyncio
async def test_legacy_learning_persistence_adapter_save_twice_real(tmp_path) -> None:
    db = Database(tmp_path / "e2e_learning_persistence.db")
    await db.initialize()
    token = DatabaseManager.set_context(db)

    try:
        repo = LegacyLearnerRepository()
        await repo.initialize()

        state = LegacyLearnerState(user_id="u2", theta=0.1)
        await repo.save_learner(state)

        state.theta = 0.2
        await repo.save_learner(state)

        loaded = await repo.get_learner("u2")
        assert loaded is not None
        assert loaded.user_id == "u2"
        assert loaded.theta == 0.2

    finally:
        DatabaseManager.reset_context(token)
        await db.dispose()
