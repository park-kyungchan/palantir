"""
Semantic Tagger for Layout Regions.

Applies heuristic rules to tag generic layout regions (Text, Title) 
with semantic labels (ProblemBox, AnswerBox) based on content and spatial properties.
"""

from typing import List
import re
from lib.layout.region import LayoutRegion, LayoutLabel

class SemanticTagger:
    """
    Refines layout labels using text patterns and spatial context.
    """
    
    # Patterns for Problem starts (e.g., "1.", "2)", "01.")
    PROBLEM_PATTERN = re.compile(r'^\s*(\d+[\.)]|\(\d+\)|\[\d+\])\s+')
    
    # Patterns for Answer headers (e.g., "풀이", "정답")
    ANSWER_PATTERN = re.compile(r'^\s*(풀\s*이|정\s*답|해\s*설)\s*')

    def tag(self, regions: List[LayoutRegion]) -> List[LayoutRegion]:
        """
        Apply tagging rules to regions.
        
        Args:
            regions: List of LayoutRegions
            
        Returns:
            List of refined LayoutRegions
        """
        tagged_regions = []
        
        for region in regions:
            new_region = region
            
            # 1. Check for ProblemBox
            # If region is TEXT or SECTION_HEADER and starts with a number pattern
            if region.label in {LayoutLabel.TEXT, LayoutLabel.SECTION_HEADER, LayoutLabel.TITLE}:
                text = region.text or ""
                if self.PROBLEM_PATTERN.match(text):
                    # It's a Problem!
                    new_region = region.with_label(LayoutLabel.PROBLEM_BOX)
                    # print(f"DEBUG: Tagged {text[:10]}... as PROBLEM_BOX")
            
            # 2. Check for AnswerBox (Explicit Keywords)
            if region.label in {LayoutLabel.TEXT}:
                text = region.text or ""
                if self.ANSWER_PATTERN.match(text):
                    new_region = region.with_label(LayoutLabel.ANSWER_BOX)
                    # print(f"DEBUG: Tagged {text[:10]}... as ANSWER_BOX")
            
            # 3. Spatial Heuristics for AnswerBox (Future)
            # e.g., if it's a large empty box or below a "ProblemBox" in a 2-column layout
            # For now, we rely on text patterns as sample.pdf seems to have mixed content.
            
            tagged_regions.append(new_region)
            
        return tagged_regions
