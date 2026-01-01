# adapters/repository/learner_repository.py
"""
LearnerRepository Interface (ODA-Aligned)

This module defines the abstract interface for LearnerProfile persistence,
extending the base Repository with learner-specific query operations.

Design Rationale:
- Follows Palantir's domain-specific DAO pattern
- Extends generic Repository with specialized queries
- Enables query by business attributes (mastery, staleness)
- Supports aggregate statistics for analytics

Usage:
    class MyLearnerRepo(LearnerRepository):
        async def find_by_mastery_above(self, threshold: float) -> List[LearnerProfile]:
            # Implementation
            ...
"""

from abc import abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from palantir_fde_learning.domain.types import LearnerProfile, LearningDomain
from palantir_fde_learning.adapters.repository.base import Repository, AuditableRepository


class LearnerRepository(Repository[LearnerProfile]):
    """
    Repository interface for LearnerProfile entities.
    
    Extends base Repository with learner-specific queries that support
    the ZPD-based learning system's operational needs:
    
    1. Find learners by mastery level (for cohort analysis)
    2. Find stale profiles (for re-engagement)
    3. Get statistics (for system monitoring)
    4. Find by domain progress (for domain-specific recommendations)
    
    All implementations must maintain:
    - ACID properties for state updates
    - Consistency between profile and knowledge_states
    - Proper timestamp tracking for staleness detection
    """
    
    @abstractmethod
    async def find_by_mastery_above(
        self, 
        threshold: float,
        limit: int = 100
    ) -> List[LearnerProfile]:
        """
        Find all learners with overall mastery above threshold.
        
        Useful for identifying advanced learners who may need
        more challenging content or mentorship opportunities.
        
        Args:
            threshold: Minimum overall mastery (0.0 to 1.0)
            limit: Maximum results to return
            
        Returns:
            List of profiles meeting the mastery threshold
        """
        ...
    
    @abstractmethod
    async def find_by_mastery_below(
        self, 
        threshold: float,
        limit: int = 100
    ) -> List[LearnerProfile]:
        """
        Find all learners with overall mastery below threshold.
        
        Useful for identifying learners who may need additional
        support or intervention.
        
        Args:
            threshold: Maximum overall mastery (0.0 to 1.0)
            limit: Maximum results to return
            
        Returns:
            List of profiles below the mastery threshold
        """
        ...
    
    @abstractmethod
    async def find_stale_profiles(
        self, 
        days: int = 7,
        limit: int = 100
    ) -> List[LearnerProfile]:
        """
        Find profiles not accessed in specified days.
        
        Identifies learners who may have disengaged and could
        benefit from re-engagement strategies.
        
        Args:
            days: Number of days since last access
            limit: Maximum results to return
            
        Returns:
            List of stale profiles ordered by staleness
        """
        ...
    
    @abstractmethod
    async def find_by_domain_progress(
        self, 
        domain: LearningDomain,
        min_concepts: int = 1
    ) -> List[LearnerProfile]:
        """
        Find learners who have studied concepts in a specific domain.
        
        Useful for domain-specific cohort analysis and targeting
        recommendations based on domain expertise.
        
        Args:
            domain: The learning domain to filter by
            min_concepts: Minimum number of concepts studied in domain
            
        Returns:
            List of profiles with domain progress
        """
        ...
    
    @abstractmethod
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get aggregate statistics across all learners.
        
        Returns metrics useful for system monitoring and analytics:
        - Total learner count
        - Average mastery level
        - Active vs stale counts
        - Distribution by mastery tier
        
        Returns:
            Dictionary containing aggregate statistics
        """
        ...
    
    @abstractmethod
    async def bulk_save(self, profiles: List[LearnerProfile]) -> int:
        """
        Save multiple profiles in a single transaction.
        
        More efficient than individual saves for batch operations.
        All saves occur atomically - either all succeed or none.
        
        Args:
            profiles: List of profiles to save
            
        Returns:
            Number of profiles successfully saved
            
        Raises:
            RepositoryError: If any save fails (transaction rolled back)
        """
        ...


class AuditableLearnerRepository(LearnerRepository, AuditableRepository[LearnerProfile]):
    """
    LearnerRepository with full audit trail support.
    
    Use this when you need to:
    - Track all changes to learner profiles
    - Support point-in-time queries
    - Meet compliance/auditing requirements
    
    This mirrors Orion ODA's ProposalRepository which maintains
    full history of all state transitions for governance.
    """
    
    @abstractmethod
    async def find_mastery_changes(
        self, 
        learner_id: str,
        concept_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get mastery level changes for a specific concept over time.
        
        Useful for analyzing learning velocity and identifying
        concepts that are particularly challenging.
        
        Args:
            learner_id: The learner to query
            concept_id: The concept to track
            start_date: Optional start of date range
            end_date: Optional end of date range
            
        Returns:
            List of mastery change records with timestamps
        """
        ...
