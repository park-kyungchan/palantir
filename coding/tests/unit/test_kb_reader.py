# tests/unit/test_kb_reader.py
"""
Unit tests for the Knowledge Base Reader.

Tests:
- Markdown parsing
- Section extraction
- Domain/difficulty detection
- Concept generation
"""
import pytest
from pathlib import Path
from palantir_fde_learning.adapters.kb_reader import (
    KBReader,
    KBSection,
    ParsedKBDocument,
    KB_SECTIONS,
)
from palantir_fde_learning.domain.types import (
    LearningDomain,
    DifficultyTier,
)


@pytest.fixture
def kb_root(tmp_path):
    """Create a temporary KB directory with sample files."""
    kb_dir = tmp_path / "knowledge_bases"
    kb_dir.mkdir()
    return kb_dir


@pytest.fixture
def sample_kb_file(kb_root):
    """Create a sample KB markdown file."""
    content = """---
domain: osdk
difficulty: beginner
tags: setup,installation
---
# OSDK Getting Started Guide

## OVERVIEW
This is an overview of the OSDK setup process.

## PREREQUISITES
None required for this beginner module.

## CORE_CONTENT
Install the OSDK using npm:
```bash
npm install @palantir/osdk
```

## EXAMPLES
```typescript
import { OntologyClient } from '@palantir/osdk';
const client = new OntologyClient();
```

## COMMON_PITFALLS
- Forgetting to configure authentication
- Using wrong environment endpoints

## BEST_PRACTICES
- Always use typed objects
- Prefer async/await patterns

## REFERENCES
- https://www.palantir.com/docs/foundry/ontology-sdk/
"""
    file_path = kb_root / "osdk_getting_started.md"
    file_path.write_text(content)
    return file_path


@pytest.fixture
def reader(kb_root):
    """Create a KBReader instance."""
    return KBReader(str(kb_root))


class TestKBSection:
    """Test KBSection model."""

    def test_is_empty_true(self):
        section = KBSection(name="TEST", content="   ", line_start=0, line_end=1)
        assert section.is_empty() is True

    def test_is_empty_false(self):
        section = KBSection(name="TEST", content="Some content", line_start=0, line_end=1)
        assert section.is_empty() is False

    def test_word_count(self):
        section = KBSection(name="TEST", content="one two three four", line_start=0, line_end=1)
        assert section.word_count() == 4


class TestKBReader:
    """Test KBReader parsing functionality."""

    def test_parse_file_exists(self, reader, sample_kb_file, kb_root):
        doc = reader.parse_file("osdk_getting_started.md")
        assert doc.title == "OSDK Getting Started Guide"
        assert doc.domain == LearningDomain.OSDK
        assert doc.difficulty == DifficultyTier.BEGINNER

    def test_parse_file_not_found(self, reader):
        with pytest.raises(FileNotFoundError):
            reader.parse_file("nonexistent.md")

    def test_parse_file_invalid_extension(self, reader, kb_root):
        txt_file = kb_root / "invalid.txt"
        txt_file.write_text("Not markdown")
        with pytest.raises(ValueError, match="Not a markdown file"):
            reader.parse_file("invalid.txt")

    def test_extract_sections(self, reader, sample_kb_file):
        content = sample_kb_file.read_text()
        sections = reader.extract_sections(content)
        
        assert "OVERVIEW" in sections
        assert "PREREQUISITES" in sections
        assert "CORE_CONTENT" in sections
        assert "EXAMPLES" in sections
        assert "COMMON_PITFALLS" in sections
        assert "BEST_PRACTICES" in sections
        assert "REFERENCES" in sections

    def test_section_content_extracted(self, reader, sample_kb_file):
        content = sample_kb_file.read_text()
        sections = reader.extract_sections(content)
        
        overview = sections["OVERVIEW"]
        assert "OSDK setup process" in overview.content

    def test_frontmatter_parsing(self, reader, sample_kb_file, kb_root):
        doc = reader.parse_file("osdk_getting_started.md")
        assert doc.metadata.get("domain") == "osdk"
        assert doc.metadata.get("difficulty") == "beginner"

    def test_concept_id_generation(self, reader, sample_kb_file, kb_root):
        doc = reader.parse_file("osdk_getting_started.md")
        # concept_id should be domain.filename
        assert "osdk" in doc.concept_id.lower()

    def test_to_learning_concept(self, reader, sample_kb_file, kb_root):
        doc = reader.parse_file("osdk_getting_started.md")
        concept = doc.to_learning_concept()
        
        assert concept.domain == LearningDomain.OSDK
        assert concept.difficulty_tier == DifficultyTier.BEGINNER
        assert concept.title == "OSDK Getting Started Guide"

    def test_completeness_score(self, reader, sample_kb_file, kb_root):
        doc = reader.parse_file("osdk_getting_started.md")
        score = doc.completeness_score()
        
        # All 7 sections present
        assert score == 1.0

    def test_scan_directory(self, reader, sample_kb_file, kb_root):
        # Create another file
        another_file = kb_root / "another_topic.md"
        another_file.write_text("# Another Topic\n\n## OVERVIEW\nContent here.")
        
        docs = reader.scan_directory()
        assert len(docs) == 2

    def test_build_concept_library(self, reader, sample_kb_file, kb_root):
        concepts = reader.build_concept_library()
        assert len(concepts) == 1
        assert concepts[0].domain == LearningDomain.OSDK


class TestParsedKBDocument:
    """Test ParsedKBDocument model methods."""

    def test_has_section(self, reader, sample_kb_file, kb_root):
        doc = reader.parse_file("osdk_getting_started.md")
        assert doc.has_section("OVERVIEW") is True
        assert doc.has_section("NONEXISTENT") is False

    def test_get_section_content(self, reader, sample_kb_file, kb_root):
        doc = reader.parse_file("osdk_getting_started.md")
        content = doc.get_section_content("OVERVIEW")
        assert content is not None
        assert "OSDK" in content

    def test_get_section_content_missing(self, reader, sample_kb_file, kb_root):
        doc = reader.parse_file("osdk_getting_started.md")
        content = doc.get_section_content("NONEXISTENT")
        assert content is None
