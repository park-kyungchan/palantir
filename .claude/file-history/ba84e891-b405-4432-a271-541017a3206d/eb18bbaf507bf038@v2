"""
Unit tests for Versioning and Governance metadata definitions.

Tests cover:
- AuditMetadata: Creation/modification tracking
- ExportMetadata: Export history tracking
- VersionMetadata: Semantic versioning and change tracking
- TagMetadata: Tagging and categorization
- ObjectTypeMetadata: Combined metadata for ObjectType
- InterfaceMetadata: Combined metadata for Interface
- LinkTypeMetadata: Combined metadata for LinkType
- ActionTypeMetadata: Combined metadata for ActionType
"""

import pytest
from datetime import datetime, timezone

from ontology_definition.core.metadata import (
    AuditMetadata,
    ExportMetadata,
    VersionMetadata,
    TagMetadata,
    ObjectTypeMetadata,
    InterfaceMetadata,
    LinkTypeMetadata,
    ActionTypeMetadata,
)


class TestAuditMetadata:
    """Tests for AuditMetadata - audit trail tracking."""

    def test_default_creation(self):
        """Default audit metadata should have timestamps and version 1."""
        audit = AuditMetadata()
        assert audit.version == 1
        assert audit.created_at is not None
        assert audit.modified_at is not None

    def test_with_creator(self):
        """Audit metadata with creator specified."""
        audit = AuditMetadata(created_by="user:admin@example.com")
        assert audit.created_by == "user:admin@example.com"

    def test_touch_increments_version(self):
        """touch() should increment version and update modified_at."""
        original = AuditMetadata(version=1)
        touched = original.touch(modified_by="user:editor@example.com")

        assert touched.version == 2
        assert touched.modified_by == "user:editor@example.com"
        assert touched.modified_at > original.modified_at

    def test_touch_preserves_creation_info(self):
        """touch() should preserve creation timestamp and creator."""
        original = AuditMetadata(
            created_by="user:creator@example.com"
        )
        touched = original.touch()

        assert touched.created_at == original.created_at
        assert touched.created_by == original.created_by

    def test_to_foundry_dict(self):
        """Export to Foundry dictionary format."""
        audit = AuditMetadata(
            created_by="user:admin",
            modified_by="user:editor",
            version=3
        )
        result = audit.to_foundry_dict()

        assert "createdAt" in result
        assert "modifiedAt" in result
        assert result["createdBy"] == "user:admin"
        assert result["modifiedBy"] == "user:editor"
        assert result["version"] == 3

    def test_from_foundry_dict(self):
        """Create from Foundry dictionary format."""
        now = datetime.now(timezone.utc)
        data = {
            "createdAt": now.isoformat(),
            "createdBy": "user:test",
            "modifiedAt": now.isoformat(),
            "modifiedBy": "user:test",
            "version": 5
        }
        audit = AuditMetadata.from_foundry_dict(data)

        assert audit.created_by == "user:test"
        assert audit.version == 5


class TestExportMetadata:
    """Tests for ExportMetadata - export history tracking."""

    def test_default_export(self):
        """Default export metadata."""
        export = ExportMetadata()
        assert export.export_format == "foundry_json"
        assert export.export_version == "1.0.0"

    def test_custom_export(self):
        """Custom export metadata."""
        export = ExportMetadata(
            exported_by="user:admin",
            export_format="json_schema",
            target_environment="production",
            includes_examples=True,
            checksum="sha256:abc123..."
        )
        assert export.export_format == "json_schema"
        assert export.target_environment == "production"
        assert export.includes_examples is True

    def test_to_foundry_dict(self):
        """Export to dictionary format."""
        export = ExportMetadata(
            export_format="llm_schema",
            target_environment="staging"
        )
        result = export.to_foundry_dict()

        assert result["exportFormat"] == "llm_schema"
        assert result["targetEnvironment"] == "staging"


class TestVersionMetadata:
    """Tests for VersionMetadata - semantic versioning."""

    def test_default_version(self):
        """Default version should be 1.0.0."""
        version = VersionMetadata()
        assert version.current_version == "1.0.0"
        assert version.breaking_change is False

    def test_increment_major(self):
        """Major version increment (breaking change)."""
        original = VersionMetadata(current_version="1.2.3")
        incremented = original.increment_major(change_log="Breaking API change")

        assert incremented.current_version == "2.0.0"
        assert incremented.breaking_change is True
        assert "1.2.3" in incremented.previous_versions

    def test_increment_minor(self):
        """Minor version increment (new feature)."""
        original = VersionMetadata(current_version="1.2.3")
        incremented = original.increment_minor(change_log="Added new property")

        assert incremented.current_version == "1.3.0"
        assert incremented.breaking_change is False

    def test_increment_patch(self):
        """Patch version increment (bug fix)."""
        original = VersionMetadata(current_version="1.2.3")
        incremented = original.increment_patch(change_log="Fixed validation bug")

        assert incremented.current_version == "1.2.4"
        assert incremented.breaking_change is False

    def test_version_history(self):
        """Version history should accumulate."""
        v1 = VersionMetadata(current_version="1.0.0")
        v2 = v1.increment_minor()
        v3 = v2.increment_patch()
        v4 = v3.increment_major()

        assert v4.previous_versions == ["1.0.0", "1.1.0", "1.1.1"]
        assert v4.current_version == "2.0.0"

    def test_deprecation_tracking(self):
        """Deprecation and removal tracking."""
        version = VersionMetadata(
            current_version="2.0.0",
            deprecated_since="1.5.0",
            removal_version="3.0.0"
        )
        assert version.deprecated_since == "1.5.0"
        assert version.removal_version == "3.0.0"

    def test_invalid_version_pattern(self):
        """Invalid version pattern should fail."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            VersionMetadata(current_version="invalid")


class TestTagMetadata:
    """Tests for TagMetadata - tagging and categorization."""

    def test_default_tags(self):
        """Default tag metadata."""
        tags = TagMetadata()
        assert tags.tags == []
        assert tags.labels == {}

    def test_with_tags_and_labels(self):
        """Tag metadata with tags and labels."""
        tags = TagMetadata(
            tags=["security", "pii"],
            category="sensitive",
            labels={"team": "platform", "priority": "high"},
            owner="security-team"
        )
        assert "security" in tags.tags
        assert tags.category == "sensitive"
        assert tags.labels["team"] == "platform"

    def test_add_tag(self):
        """add_tag() should add unique tags."""
        original = TagMetadata(tags=["existing"])
        updated = original.add_tag("new")

        assert "new" in updated.tags
        assert "existing" in updated.tags

    def test_add_tag_idempotent(self):
        """Adding existing tag should be idempotent."""
        original = TagMetadata(tags=["existing"])
        same = original.add_tag("existing")

        assert same is original  # Same instance returned

    def test_add_label(self):
        """add_label() should add/update labels."""
        original = TagMetadata(labels={"key1": "value1"})
        updated = original.add_label("key2", "value2")

        assert updated.labels["key1"] == "value1"
        assert updated.labels["key2"] == "value2"


class TestObjectTypeMetadata:
    """Tests for ObjectTypeMetadata - combined metadata."""

    def test_default_metadata(self):
        """Default ObjectType metadata."""
        meta = ObjectTypeMetadata()
        assert meta.audit.version == 1
        assert meta.version.current_version == "1.0.0"
        assert meta.tags.tags == []

    def test_touch_updates_audit(self):
        """touch() should update audit metadata."""
        original = ObjectTypeMetadata()
        touched = original.touch(modified_by="user:editor")

        assert touched.audit.version == 2
        assert touched.audit.modified_by == "user:editor"
        assert touched.version == original.version  # Version unchanged

    def test_record_export(self):
        """record_export() should add to export history."""
        meta = ObjectTypeMetadata()
        export = ExportMetadata(
            export_format="json_schema",
            target_environment="production"
        )
        updated = meta.record_export(export)

        assert len(updated.export_history) == 1
        assert updated.export_history[0].export_format == "json_schema"


class TestInterfaceMetadata:
    """Tests for InterfaceMetadata - Interface-specific metadata."""

    def test_default_metadata(self):
        """Default Interface metadata."""
        meta = InterfaceMetadata()
        assert meta.implementer_count == 0

    def test_with_implementer_count(self):
        """Interface metadata with implementer count."""
        meta = InterfaceMetadata(implementer_count=15)
        assert meta.implementer_count == 15

    def test_touch_preserves_implementer_count(self):
        """touch() should preserve implementer count."""
        original = InterfaceMetadata(implementer_count=10)
        touched = original.touch()

        assert touched.implementer_count == 10


class TestLinkTypeMetadata:
    """Tests for LinkTypeMetadata - LinkType-specific metadata."""

    def test_default_metadata(self):
        """Default LinkType metadata."""
        meta = LinkTypeMetadata()
        assert meta.audit.version == 1
        assert meta.version.current_version == "1.0.0"


class TestActionTypeMetadata:
    """Tests for ActionTypeMetadata - ActionType-specific metadata."""

    def test_default_metadata(self):
        """Default ActionType metadata."""
        meta = ActionTypeMetadata()
        assert meta.execution_count == 0

    def test_with_execution_count(self):
        """ActionType metadata with execution count."""
        meta = ActionTypeMetadata(execution_count=1000)
        assert meta.execution_count == 1000

