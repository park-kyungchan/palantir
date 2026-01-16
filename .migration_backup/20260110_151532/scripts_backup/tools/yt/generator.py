"""
Orion ODA V3 - YouTube Automation - Metadata Generator
=======================================================
Generate YouTube video metadata from transcript.

Maps to IndyDevDan's idt yt generate command.
"""

import asyncio
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class MetadataGenerator:
    """
    Generate YouTube video metadata from transcript.
    
    Maps to IndyDevDan's idt yt generate functionality.
    
    Generates:
        - Title (3 options)
        - Description
        - Tags (15-20)
        - Thumbnail concepts
        - Chapters with timestamps
    
    Usage:
        generator = MetadataGenerator()
        metadata = await generator.generate(transcript)
    """
    
    def __init__(self, llm=None):
        self._llm = llm
    
    @property
    def llm(self):
        """Lazy-load InstructorClient."""
        if self._llm is None:
            try:
                from scripts.llm.instructor_client import InstructorClient
                self._llm = InstructorClient()
            except ImportError:
                logger.warning("InstructorClient not available")
        return self._llm
    
    async def generate(
        self,
        transcript: str,
        style: str = "educational",
        target_audience: str = "developers",
    ) -> Dict[str, Any]:
        """
        Generate all metadata from transcript.
        
        Args:
            transcript: Video transcript text
            style: Content style (educational, entertainment, tutorial)
            target_audience: Target viewer demographic
            
        Returns:
            Dict with all metadata
        """
        logger.info(f"Generating metadata for {len(transcript)} char transcript")
        
        # Generate in parallel
        titles, description, tags, chapters, thumbnails = await asyncio.gather(
            self._generate_titles(transcript, style),
            self._generate_description(transcript, style),
            self._generate_tags(transcript),
            self._generate_chapters(transcript),
            self._generate_thumbnails(transcript),
        )
        
        return {
            "titles": titles,
            "description": description,
            "tags": tags,
            "chapters": chapters,
            "thumbnails": thumbnails,
            "metadata": {
                "style": style,
                "target_audience": target_audience,
                "transcript_length": len(transcript),
            }
        }
    
    async def _generate_titles(self, transcript: str, style: str) -> List[str]:
        """Generate title options."""
        if self.llm is None:
            return ["[LLM not configured] Video Title"]
        
        prompt = f"""Based on this video transcript, generate 3 compelling YouTube titles.

Style: {style}

Transcript (first 1000 chars):
{transcript[:1000]}

Requirements:
- Under 60 characters each
- Include power words
- Create curiosity
- SEO optimized

Return as JSON array: ["title1", "title2", "title3"]"""
        
        try:
            result = await self.llm.generate_json(prompt)
            return result if isinstance(result, list) else [str(result)]
        except Exception as e:
            logger.error(f"Title generation failed: {e}")
            return ["Generated Title"]
    
    async def _generate_description(self, transcript: str, style: str) -> str:
        """Generate video description."""
        if self.llm is None:
            return "[LLM not configured] Video description placeholder."
        
        prompt = f"""Write a YouTube video description based on this transcript.

Style: {style}

Transcript (first 2000 chars):
{transcript[:2000]}

Requirements:
- Strong hook in first 150 characters
- Include key points
- Call to action
- Relevant hashtags
- 1000-1500 characters total"""
        
        try:
            return await self.llm.generate_text(prompt)
        except Exception as e:
            logger.error(f"Description generation failed: {e}")
            return "Video description."
    
    async def _generate_tags(self, transcript: str) -> List[str]:
        """Generate video tags."""
        if self.llm is None:
            return ["video", "content"]
        
        prompt = f"""Generate 15-20 YouTube tags for this video.

Transcript (first 1500 chars):
{transcript[:1500]}

Requirements:
- Mix of broad and specific terms
- Include long-tail keywords
- Relevant to content
- SEO optimized

Return as JSON array: ["tag1", "tag2", ...]"""
        
        try:
            result = await self.llm.generate_json(prompt)
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"Tag generation failed: {e}")
            return []
    
    async def _generate_chapters(self, transcript: str) -> List[Dict[str, str]]:
        """Generate video chapters."""
        if self.llm is None:
            return [{"time": "0:00", "title": "Intro"}]
        
        prompt = f"""Create chapter markers for this video transcript.

Transcript (first 3000 chars):
{transcript[:3000]}

Requirements:
- Start with 0:00 intro
- Logical topic segments
- Clear labels (under 50 chars)
- 5-10 chapters

Return as JSON array: [{{"time": "0:00", "title": "Intro"}}, ...]"""
        
        try:
            result = await self.llm.generate_json(prompt)
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"Chapter generation failed: {e}")
            return []
    
    async def _generate_thumbnails(self, transcript: str) -> List[str]:
        """Generate thumbnail concepts."""
        if self.llm is None:
            return ["Eye-catching thumbnail concept"]
        
        prompt = f"""Suggest 3 YouTube thumbnail concepts for this video.

Transcript (first 1000 chars):
{transcript[:1000]}

Requirements:
- Eye-catching
- Simple, bold elements
- Faces if applicable
- Contrasting colors
- Text overlay suggestions

Return as JSON array: ["concept1", "concept2", "concept3"]"""
        
        try:
            result = await self.llm.generate_json(prompt)
            return result if isinstance(result, list) else []
        except Exception as e:
            logger.error(f"Thumbnail generation failed: {e}")
            return []
