"""
Orion Phase 5 - Scoping & ZPD Engine
Selects the optimal next lesson based on Learner State and Code Complexity.
"""

from typing import List, Dict, Optional
from .types import LearnerState, TeachingComplexityScore
from .engine import TutoringEngine
from .graph import DependencyGraph

# ZPD Constants
OPTIMAL_STRETCH_MIN = 0.10  # 10% harder
OPTIMAL_STRETCH_MAX = 0.30  # 30% harder
MASTERY_THRESHOLD = 0.70    # Required P(mastery) to consider a dependency "known"

class ScopingEngine:
    def __init__(self, tutoring_engine: TutoringEngine):
        self.engine = tutoring_engine

    @staticmethod
    def _get_mastery_probability(kc: object | None) -> float:
        """
        Returns a normalized mastery probability for a KC object.

        Supports both:
        - scripts.ontology.learning.types.KnowledgeComponentState (p_mastery)
        - scripts.cognitive.types.KnowledgeComponent (mastery_probability)
        """
        if kc is None:
            return 0.0
        p = getattr(kc, "p_mastery", None)
        if p is None:
            p = getattr(kc, "mastery_probability", 0.0)
        try:
            return float(p)
        except Exception:
            return 0.0

    def calculate_zpd_score(self, file_tcs: float, learner_level: float) -> float:
        """
        Returns 0.0 - 1.0 suitability score.
        1.0 means perfect ZPD fit.
        """
        # Prevent divide by zero; floor learner level at 10.0 for math stability
        effective_level = max(learner_level, 10.0)
        
        # Calculate stretch percentage (e.g. 50 TCS vs 40 Level = 0.25 stretch)
        stretch = (file_tcs - effective_level) / effective_level
        
        base_score = 0.0
        
        if stretch < 0.05:
            # Zone of Actual Development (Too Easy)
            base_score = 0.2
        elif 0.05 <= stretch < OPTIMAL_STRETCH_MIN:
            # Warm-up
            base_score = 0.6
        elif OPTIMAL_STRETCH_MIN <= stretch <= OPTIMAL_STRETCH_MAX:
            # OPTIMAL ZPD
            base_score = 1.0
        elif OPTIMAL_STRETCH_MAX < stretch <= 0.50:
            # Challenging
            base_score = 0.5
        else:
            # Zone of Frustration (Too Hard)
            base_score = 0.1
            
        return base_score

    def get_prerequisite_status(self, file_path: str, state: LearnerState) -> float:
        """
        Checks if dependencies are mastered.
        Returns 0.0 (blocked) to 1.0 (all clear).
        """
        deps = self.engine.dependency_graph.adj_list.get(file_path, set())
        if not deps:
            return 1.0 # No dependencies = Executable immediately
            
        total_p = 0.0
        count = 0
        
        for dep_path in deps:
            # Check mastery of the *file* (assuming file path is concept_id)
            # OR check mastery of concepts *in* the file?
            # Phase 5 implies file-based progression.
            kc = state.knowledge_components.get(dep_path)
            p = self._get_mastery_probability(kc)
            
            # Critical blocking: If any dependency is < 0.3, strictly block?
            # Averaging for now.
            total_p += p
            count += 1
            
        avg_mastery = total_p / count
        return avg_mastery

    def recommend_next_files(
        self,
        state: LearnerState,
        limit: int = 3,
        allowlist: set[str] | None = None,
    ) -> List[Dict]:
        """
        Returns ranked list of recommended files.
        """
        # Ensure scores are calculated
        if not self.engine.scores:
            self.engine.scan_codebase()
            self.engine.calculate_scores()
            
        recommendations = []
        
        # Approximate "Learner Level" from Theta or Average Mastery?
        # Phase 5 uses Theta directly or derived TCS capacity.
        # Let's assume Learner TCP (Teaching Complexity Point) ~ Theta * 20 + 20? 
        # Or simpler: Max TCS of mastered files?
        # Let's implement specific logic:
        # Effective Level = Average TCS of files with Mastery > 0.7
        mastered_tcs = []
        for concept_id, kc in state.knowledge_components.items():
            if self._get_mastery_probability(kc) >= MASTERY_THRESHOLD:
                # Is this concept a file?
                if concept_id in self.engine.scores:
                    mastered_tcs.append(self.engine.scores[concept_id].total_score)
        
        if mastered_tcs:
            effective_level = sum(mastered_tcs) / len(mastered_tcs)
        else:
            effective_level = 15.0 # Baseline for beginner
            
        # Analyze all candidates
        for file_path, score in self.engine.scores.items():
            if allowlist is not None and file_path not in allowlist:
                continue
            # Skip if already mastered
            kc = state.knowledge_components.get(file_path)
            if kc and self._get_mastery_probability(kc) > 0.85:
                continue
                
            # 1. Prerequisite Check
            prereq_score = self.get_prerequisite_status(file_path, state)
            if prereq_score < MASTERY_THRESHOLD and self.engine.dependency_graph.adj_list.get(file_path):
                # Dependencies not met
                continue
                
            # 2. ZPD Score
            zpd_score = self.calculate_zpd_score(score.total_score, effective_level)
            
            # 3. Final Ranking Score
            # Weight ZPD heavily, but boost foundational files
            final_rank = zpd_score
            
            recommendations.append({
                "file": file_path,
                "tcs": round(score.total_score, 1),
                "zpd_score": zpd_score,
                "reason": "Optimal Challenge" if zpd_score == 1.0 else "Review/Stretch"
            })
            
        # Sort by suitability descending
        recommendations.sort(key=lambda x: x["zpd_score"], reverse=True)
        return recommendations[:limit]
