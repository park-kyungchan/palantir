"""
Orion Phase 5 - Learning Persistence & BKT Engine
Manages learner state storage and Bayesian Knowledge Tracing updates.
"""

import aiosqlite
from pathlib import Path
from typing import Optional, Dict, Tuple
from datetime import datetime
import json

from .types import LearnerState, KnowledgeComponentState

# BKT Parameters (Default Population Priors)
P_L0 = 0.3   # Initial Mastery
P_T = 0.2    # Learning Rate
P_G = 0.1    # Guess Probability
P_S = 0.15   # Slip Probability

DB_PATH = Path("/home/palantir/orion-orchestrator-v2/data/learning.db")

class LearnerRepository:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._ensure_db_dir()

    def _ensure_db_dir(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

    async def initialize(self):
        """Create tables if they don't exist."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS learners (
                    user_id TEXT PRIMARY KEY,
                    theta REAL DEFAULT 0.0,
                    updated_at TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS mastery (
                    user_id TEXT,
                    concept_id TEXT,
                    p_mastery REAL,
                    evidence_count INTEGER,
                    last_assessed TIMESTAMP,
                    PRIMARY KEY (user_id, concept_id),
                    FOREIGN KEY(user_id) REFERENCES learners(user_id)
                )
            """)
            await db.commit()

    async def get_learner(self, user_id: str) -> LearnerState:
        """Fetch full learner state including all KC masteries."""
        async with aiosqlite.connect(self.db_path) as db:
            # 1. Get Learner Base
            async with db.execute("SELECT theta FROM learners WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    # New user
                    return LearnerState(user_id=user_id, theta=0.0)
                theta = row[0]

            # 2. Get Mastery Records
            kcs = {}
            async with db.execute("SELECT concept_id, p_mastery, evidence_count, last_assessed FROM mastery WHERE user_id = ?", (user_id,)) as cursor:
                async for m_row in cursor:
                    concept_id, p, count, last = m_row
                    dt_last = datetime.fromisoformat(last) if last else None
                    kcs[concept_id] = KnowledgeComponentState(
                        concept_id=concept_id,
                        p_mastery=p,
                        evidence_count=count,
                        last_assessed=dt_last
                    )

            return LearnerState(user_id=user_id, theta=theta, knowledge_components=kcs)

    async def save_learner(self, state: LearnerState):
        """Persist full learner state (upsert)."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO learners (user_id, theta, updated_at) VALUES (?, ?, ?)",
                (state.user_id, state.theta, datetime.now().isoformat())
            )
            
            for kc in state.knowledge_components.values():
                await db.execute(
                    """
                    INSERT OR REPLACE INTO mastery (user_id, concept_id, p_mastery, evidence_count, last_assessed)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        state.user_id,
                        kc.concept_id,
                        kc.p_mastery,
                        kc.evidence_count,
                        kc.last_assessed.isoformat() if kc.last_assessed else None
                    )
                )
            await db.commit()

    def update_bkt(self, current_p: float, correct: bool) -> float:
        """
        Calculates new P(Mastery) using Bayesian Knowledge Tracing.
        
        Steps:
        1. Posterior P(L|Obs) calculation based on correctness
        2. Transit P(L_t+1) calculation
        """
        # 1. Likelihood Update (Posterior)
        if correct:
            # P(L|Correct) = P(L)*(1-S) / [P(L)*(1-S) + (1-L)*G]
            numerator = current_p * (1 - P_S)
            denominator = numerator + (1 - current_p) * P_G
        else:
            # P(L|Incorrect) = P(L)*S / [P(L)*S + (1-L)*(1-G)]
            numerator = current_p * P_S
            denominator = numerator + (1 - current_p) * (1 - P_G)
            
        p_posterior = numerator / denominator if denominator > 0 else 0.0
        
        # 2. Transition Update
        # P(L_next) = P(Posterior) + (1 - P(Posterior)) * T
        p_next = p_posterior + (1 - p_posterior) * P_T
        
        return min(max(p_next, 0.0), 1.0) # Clamp 0-1

    async def record_interaction(self, user_id: str, concept_id: str, correct: bool):
        """Transactional update of a single concept mastery."""
        state = await self.get_learner(user_id)
        
        # Get current P (default to L0 if new)
        kc = state.knowledge_components.get(concept_id)
        current_p = kc.p_mastery if kc else P_L0
        
        # Calculate new P
        new_p = self.update_bkt(current_p, correct)
        
        # Update State Object
        state.update_mastery(concept_id, new_p)
        
        # Persist
        await self.save_learner(state)
        
        return new_p
