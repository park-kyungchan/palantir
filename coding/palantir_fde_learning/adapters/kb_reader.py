"""
Knowledge Base File Reading Adapter

This module provides functionality to read and parse Knowledge Base (KB)
markdown files. KB files follow a 7-component structure for comprehensive
learning content:

1. OVERVIEW - High-level concept introduction
2. PREREQUISITES - Required prior knowledge
3. CORE_CONTENT - Main learning material
4. EXAMPLES - Practical code examples
5. COMMON_PITFALLS - Mistakes to avoid
6. BEST_PRACTICES - Recommended approaches
7. REFERENCES - Links to official documentation

The adapter extracts these sections and maps them to domain entities.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from palantir_fde_learning.domain.types import (
    DifficultyTier,
    LearningConcept,
    LearningDomain,
)


# Standard KB section names (7-component structure)
KB_SECTIONS = [
    "OVERVIEW",
    "PREREQUISITES",
    "CORE_CONTENT",
    "EXAMPLES",
    "COMMON_PITFALLS",
    "BEST_PRACTICES",
    "REFERENCES",
]


class KBSection(BaseModel):
    """
    Represents a single section from a KB markdown file.

    Attributes:
        name: Section name (one of the 7 standard sections)
        content: Raw markdown content of the section
        line_start: Starting line number in the source file
        line_end: Ending line number in the source file
    """

    name: str = Field(
        ...,
        description="Section name (e.g., OVERVIEW, PREREQUISITES)",
    )
    content: str = Field(
        ...,
        description="Raw markdown content of the section",
    )
    line_start: int = Field(
        default=0,
        ge=0,
        description="Starting line number in source file",
    )
    line_end: int = Field(
        default=0,
        ge=0,
        description="Ending line number in source file",
    )

    def is_empty(self) -> bool:
        """Check if the section has meaningful content."""
        return len(self.content.strip()) == 0

    def word_count(self) -> int:
        """Count words in the section content."""
        return len(self.content.split())

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }


class ParsedKBDocument(BaseModel):
    """
    Represents a fully parsed KB markdown document.

    Attributes:
        file_path: Absolute path to the source file
        title: Document title (from H1 header)
        concept_id: Derived concept ID
        domain: Detected learning domain
        difficulty: Detected difficulty tier
        sections: Mapping of section names to KBSection objects
        metadata: Additional metadata extracted from frontmatter
        parsed_at: Timestamp of parsing
    """

    file_path: str = Field(
        ...,
        description="Absolute path to the source file",
    )
    title: str = Field(
        ...,
        description="Document title from H1 header",
    )
    concept_id: str = Field(
        ...,
        description="Derived concept ID",
    )
    domain: Optional[LearningDomain] = Field(
        default=None,
        description="Detected learning domain",
    )
    difficulty: Optional[DifficultyTier] = Field(
        default=None,
        description="Detected difficulty tier",
    )
    sections: dict[str, KBSection] = Field(
        default_factory=dict,
        description="Mapping of section names to content",
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Additional metadata from frontmatter",
    )
    parsed_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp of parsing",
    )

    def has_section(self, section_name: str) -> bool:
        """Check if a specific section exists."""
        return section_name in self.sections

    def get_section_content(self, section_name: str) -> Optional[str]:
        """Get content of a specific section."""
        if section_name in self.sections:
            return self.sections[section_name].content
        return None

    def completeness_score(self) -> float:
        """
        Calculate how complete the KB document is.

        Returns a score from 0.0 to 1.0 based on how many
        of the 7 standard sections are present and non-empty.
        """
        present_count = sum(
            1 for section in KB_SECTIONS
            if section in self.sections and not self.sections[section].is_empty()
        )
        return present_count / len(KB_SECTIONS)

    def to_learning_concept(self) -> LearningConcept:
        """
        Convert the parsed document to a LearningConcept.

        Prerequisites are extracted from the PREREQUISITES section.
        """
        prerequisites = []
        if "PREREQUISITES" in self.sections:
            prereq_content = self.sections["PREREQUISITES"].content
            # Extract concept IDs from prerequisite section
            # Format: - [[concept_id]] or - `concept_id`
            prereq_pattern = re.compile(r'(?:\[\[|`)([a-z][a-z0-9_.]+)(?:\]\]|`)')
            prerequisites = prereq_pattern.findall(prereq_content)

        # Estimate learning time based on content length
        total_words = sum(s.word_count() for s in self.sections.values())
        # Average reading speed: 200 words/minute, plus time for exercises
        estimated_minutes = max(15, min(120, total_words // 150))

        return LearningConcept(
            concept_id=self.concept_id,
            domain=self.domain or LearningDomain.FOUNDRY,
            difficulty_tier=self.difficulty or DifficultyTier.BEGINNER,
            prerequisites=prerequisites,
            title=self.title,
            description=self.get_section_content("OVERVIEW"),
            estimated_minutes=estimated_minutes,
            tags=list(self.metadata.get("tags", "").split(",")) if self.metadata.get("tags") else [],
        )

    model_config = {
        "frozen": False,
        "extra": "forbid",
    }


class KBReader:
    """
    Knowledge Base file reading adapter.

    Reads and parses KB markdown files following the 7-component structure.
    Supports YAML frontmatter for metadata extraction.

    Example usage:
        reader = KBReader("/path/to/kb/directory")
        doc = reader.parse_file("osdk/getting-started.md")
        sections = reader.extract_sections(doc)
        concept = doc.to_learning_concept()
    """

    def __init__(self, kb_root: str):
        """
        Initialize the KB reader.

        Args:
            kb_root: Root directory containing KB markdown files
        """
        self.kb_root = Path(kb_root)
        self._section_pattern = re.compile(
            r'^##\s+(\d+\.\s+)?(' + '|'.join(KB_SECTIONS) + r')\s*$',
            re.IGNORECASE | re.MULTILINE
        )
        self._frontmatter_pattern = re.compile(
            r'^---\s*\n(.*?)\n---\s*\n',
            re.DOTALL
        )
        self._title_pattern = re.compile(r'^#\s+(.+)$', re.MULTILINE)

    def _parse_frontmatter(self, content: str) -> tuple[dict[str, str], str]:
        """
        Extract YAML frontmatter from markdown content.

        Returns:
            Tuple of (metadata dict, content without frontmatter)
        """
        metadata: dict[str, str] = {}

        match = self._frontmatter_pattern.match(content)
        if match:
            frontmatter = match.group(1)
            # Simple YAML parsing (key: value format)
            for line in frontmatter.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    metadata[key.strip()] = value.strip()
            content = content[match.end():]

        return metadata, content

    def _extract_title(self, content: str) -> Optional[str]:
        """Extract the document title from H1 header."""
        match = self._title_pattern.search(content)
        if match:
            return match.group(1).strip()
        return None

    def _detect_domain(self, file_path: Path, content: str) -> Optional[LearningDomain]:
        """
        Detect the learning domain from file path and content.

        Heuristics:
        1. Check parent directory name
        2. Check for domain keywords in content
        """
        # Check directory structure
        parts = file_path.parts
        domain_keywords = {
            "osdk": LearningDomain.OSDK,
            "foundry": LearningDomain.FOUNDRY,
            "blueprint": LearningDomain.BLUEPRINT,
            "workshop": LearningDomain.WORKSHOP,
            "react": LearningDomain.REACT,
            "typescript": LearningDomain.TYPESCRIPT,
            "ontology": LearningDomain.ONTOLOGY,
            "pipeline": LearningDomain.PIPELINE,
            "functions": LearningDomain.FUNCTIONS,
            "actions": LearningDomain.ACTIONS,
        }

        for part in parts:
            part_lower = part.lower()
            if part_lower in domain_keywords:
                return domain_keywords[part_lower]

        # Check content for domain keywords
        content_lower = content.lower()
        for keyword, domain in domain_keywords.items():
            if keyword in content_lower:
                return domain

        return None

    def _detect_difficulty(self, file_path: Path, content: str) -> Optional[DifficultyTier]:
        """
        Detect difficulty tier from file path and content.

        Heuristics:
        1. Check for difficulty keywords in path
        2. Check for difficulty indicators in content
        3. Check prerequisite count
        """
        path_str = str(file_path).lower()
        content_lower = content.lower()

        # Check path for difficulty indicators
        if any(kw in path_str for kw in ["beginner", "intro", "getting-started", "basics"]):
            return DifficultyTier.BEGINNER
        if any(kw in path_str for kw in ["intermediate", "practical", "building"]):
            return DifficultyTier.INTERMEDIATE
        if any(kw in path_str for kw in ["advanced", "expert", "optimization", "deep-dive"]):
            return DifficultyTier.ADVANCED

        # Check content for difficulty indicators
        if "no prior knowledge" in content_lower or "introduction" in content_lower:
            return DifficultyTier.BEGINNER
        if "assumes familiarity" in content_lower:
            return DifficultyTier.INTERMEDIATE
        if "advanced" in content_lower or "optimization" in content_lower:
            return DifficultyTier.ADVANCED

        return DifficultyTier.BEGINNER  # Default to beginner

    def _generate_concept_id(self, file_path: Path, domain: Optional[LearningDomain]) -> str:
        """
        Generate a concept ID from file path.

        Format: domain.tier.topic
        Example: osdk.beginner.installation
        """
        # Get filename without extension
        topic = file_path.stem.lower().replace("-", "_").replace(" ", "_")

        # Get domain prefix
        domain_prefix = domain.value if domain else "general"

        # Combine into concept ID
        return f"{domain_prefix}.{topic}"

    def extract_sections(self, content: str) -> dict[str, KBSection]:
        """
        Extract the 7-component sections from markdown content.

        Args:
            content: Raw markdown content

        Returns:
            Dictionary mapping section names to KBSection objects
        """
        sections: dict[str, KBSection] = {}
        lines = content.split('\n')

        current_section: Optional[str] = None
        section_lines: list[str] = []
        section_start: int = 0

        for i, line in enumerate(lines):
            # Check if this line is a section header
            match = self._section_pattern.match(line)
            if match:
                # Save previous section if exists
                if current_section:
                    sections[current_section] = KBSection(
                        name=current_section,
                        content='\n'.join(section_lines).strip(),
                        line_start=section_start,
                        line_end=i - 1,
                    )

                # Start new section
                current_section = match.group(2).upper()
                section_lines = []
                section_start = i + 1
            elif current_section:
                section_lines.append(line)

        # Don't forget the last section
        if current_section:
            sections[current_section] = KBSection(
                name=current_section,
                content='\n'.join(section_lines).strip(),
                line_start=section_start,
                line_end=len(lines) - 1,
            )

        return sections

    def parse_file(self, relative_path: str) -> ParsedKBDocument:
        """
        Parse a KB markdown file into a structured document.

        Args:
            relative_path: Path relative to kb_root

        Returns:
            ParsedKBDocument with extracted sections and metadata

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a valid markdown file
        """
        file_path = self.kb_root / relative_path

        if not file_path.exists():
            raise FileNotFoundError(f"KB file not found: {file_path}")

        if file_path.suffix.lower() not in ['.md', '.markdown']:
            raise ValueError(f"Not a markdown file: {file_path}")

        content = file_path.read_text(encoding='utf-8')

        # Extract frontmatter
        metadata, content_without_fm = self._parse_frontmatter(content)

        # Extract title
        title = self._extract_title(content_without_fm) or file_path.stem.replace("-", " ").title()

        # Detect domain and difficulty
        domain = self._detect_domain(file_path, content_without_fm)
        difficulty = self._detect_difficulty(file_path, content_without_fm)

        # Override with metadata if present
        if "domain" in metadata:
            try:
                domain = LearningDomain(metadata["domain"].lower())
            except ValueError:
                pass

        if "difficulty" in metadata:
            try:
                difficulty = DifficultyTier(metadata["difficulty"].lower())
            except ValueError:
                pass

        # Generate concept ID
        concept_id = metadata.get("concept_id") or self._generate_concept_id(file_path, domain)

        # Extract sections
        sections = self.extract_sections(content_without_fm)

        return ParsedKBDocument(
            file_path=str(file_path.absolute()),
            title=title,
            concept_id=concept_id,
            domain=domain,
            difficulty=difficulty,
            sections=sections,
            metadata=metadata,
        )

    def scan_directory(self, subdirectory: str = "") -> list[ParsedKBDocument]:
        """
        Scan a directory for KB markdown files and parse them all.

        Args:
            subdirectory: Optional subdirectory to scan

        Returns:
            List of ParsedKBDocument objects
        """
        scan_path = self.kb_root / subdirectory if subdirectory else self.kb_root

        if not scan_path.exists():
            return []

        documents: list[ParsedKBDocument] = []

        for md_file in scan_path.rglob("*.md"):
            try:
                relative = md_file.relative_to(self.kb_root)
                doc = self.parse_file(str(relative))
                documents.append(doc)
            except (ValueError, FileNotFoundError) as e:
                # Log but continue with other files
                print(f"Warning: Could not parse {md_file}: {e}")

        return documents

    def build_concept_library(self, subdirectory: str = "") -> list[LearningConcept]:
        """
        Build a library of LearningConcepts from KB files.

        Args:
            subdirectory: Optional subdirectory to scan

        Returns:
            List of LearningConcept objects
        """
        documents = self.scan_directory(subdirectory)
        return [doc.to_learning_concept() for doc in documents]
