"""
Orion ODA v3.0 - Proposal Cleanup Job
=====================================

Background job to maintain database hygiene by archiving/deleting
stale proposals.

Policy:
- EXECUTED/REJECTED/CANCELLED proposals > 30 days old are hard deleted.
- DELETED proposals > 7 days old are hard deleted.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from scripts.ontology.objects.proposal import ProposalStatus
from scripts.ontology.storage import ProposalRepository, initialize_database
from scripts.ontology.ontology_types import utc_now

logger = logging.getLogger(__name__)

class ProposalCleanupJob:
    """
    Periodically cleans up old proposals.
    """
    
    def __init__(self, repo: ProposalRepository):
        self.repo = repo
        
    async def run(self, retention_days_terminal: int = 30, retention_days_deleted: int = 7):
        """
        Execute the cleanup logic.
        
        Args:
            retention_days_terminal: Days to keep terminal states (Executed, Rejected, Cancelled)
            retention_days_deleted: Days to keep soft-deleted items
        """
        logger.info("Starting Proposal Cleanup Job...")
        
        # 1. Clean up Terminal States
        cutoff_terminal = utc_now() - timedelta(days=retention_days_terminal)
        terminal_statuses = [
            ProposalStatus.EXECUTED,
            ProposalStatus.REJECTED,
            ProposalStatus.CANCELLED
        ]
        
        count_terminal = await self.repo.delete_expired(
            older_than=cutoff_terminal,
            statuses=terminal_statuses
        )
        logger.info(f"Deleted {count_terminal} terminal proposals older than {retention_days_terminal} days.")
        
        # 2. Clean up Soft Deleted
        cutoff_deleted = utc_now() - timedelta(days=retention_days_deleted)
        count_deleted = await self.repo.delete_expired(
            older_than=cutoff_deleted,
            statuses=[ProposalStatus.DELETED]
        )
        logger.info(f"Deleted {count_deleted} soft-deleted proposals older than {retention_days_deleted} days.")
        
        return {
            "terminal_deleted": count_terminal,
            "soft_deleted": count_deleted
        }

async def main():
    logging.basicConfig(level=logging.INFO)
    db = await initialize_database()
    repo = ProposalRepository(db)
    job = ProposalCleanupJob(repo)
    
    await job.run()

if __name__ == "__main__":
    asyncio.run(main())
