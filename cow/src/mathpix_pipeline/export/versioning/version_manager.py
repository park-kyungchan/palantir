"""
Version Manager for Editable YAML Documents.

Provides git-style version control with:
- Snapshot-based versioning
- DeepDiff structural comparison
- Human-readable diff summaries
- Rollback capability

Module Version: 1.0.0
"""

import hashlib
import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from ...schemas.editable_yaml import VersionInfo

logger = logging.getLogger(__name__)


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class VersionMetadata:
    """Metadata for a single version.

    Stored in versions.json index file.
    """
    version_id: str
    created_at: datetime
    created_by: str = "system"
    parent_version_id: Optional[str] = None
    change_summary: str = ""
    changes_count: int = 0
    file_path: str = ""
    file_size: int = 0
    checksum: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "version_id": self.version_id,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "parent_version_id": self.parent_version_id,
            "change_summary": self.change_summary,
            "changes_count": self.changes_count,
            "file_path": self.file_path,
            "file_size": self.file_size,
            "checksum": self.checksum,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VersionMetadata":
        """Create from dictionary."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        elif created_at is None:
            created_at = datetime.now(timezone.utc)

        return cls(
            version_id=data["version_id"],
            created_at=created_at,
            created_by=data.get("created_by", "system"),
            parent_version_id=data.get("parent_version_id"),
            change_summary=data.get("change_summary", ""),
            changes_count=data.get("changes_count", 0),
            file_path=data.get("file_path", ""),
            file_size=data.get("file_size", 0),
            checksum=data.get("checksum", ""),
        )


@dataclass
class DiffResult:
    """Result of comparing two versions."""
    version_from: str
    version_to: str
    changes: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    added_count: int = 0
    removed_count: int = 0
    modified_count: int = 0
    type_changes_count: int = 0

    @property
    def total_changes(self) -> int:
        """Total number of changes."""
        return self.added_count + self.removed_count + self.modified_count + self.type_changes_count

    @property
    def has_changes(self) -> bool:
        """Check if there are any changes."""
        return self.total_changes > 0


# =============================================================================
# Version Manager
# =============================================================================

class VersionManager:
    """Git-style version control for editable YAML documents.

    Uses snapshot-based storage with DeepDiff for structural comparison.

    Directory Structure:
        .mathpdf_versions/
        └── {image_id}/
            ├── versions.json      # Version metadata index
            ├── v1_20260202_120000.yaml
            ├── v2_20260202_130000.yaml
            └── ...

    Usage:
        manager = VersionManager()

        # Save a new version
        version_id = manager.save_version(yaml_content, "img_123", "Fixed equation")

        # List all versions
        versions = manager.list_versions("img_123")

        # Get specific version
        content = manager.get_version("img_123", "v1_20260202_120000")

        # Compare versions
        diff = manager.diff("img_123", "v1_...", "v2_...")

        # Rollback to previous version
        content = manager.rollback("img_123", "v1_20260202_120000")
    """

    VERSION_FILE = "versions.json"

    def __init__(self, storage_path: Optional[Path] = None):
        """Initialize version manager.

        Args:
            storage_path: Base path for version storage.
                         Defaults to .mathpdf_versions/
        """
        self.storage_path = Path(storage_path) if storage_path else Path(".mathpdf_versions")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        logger.debug(f"VersionManager initialized: storage={self.storage_path}")

    def _get_image_dir(self, image_id: str) -> Path:
        """Get directory for image versions."""
        return self.storage_path / image_id

    def _get_metadata_path(self, image_id: str) -> Path:
        """Get path to versions.json."""
        return self._get_image_dir(image_id) / self.VERSION_FILE

    def _load_metadata(self, image_id: str) -> Optional[Dict[str, Any]]:
        """Load versions.json for an image."""
        metadata_path = self._get_metadata_path(image_id)
        if not metadata_path.exists():
            return None

        try:
            return json.loads(metadata_path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"Failed to load metadata for {image_id}: {e}")
            return None

    def _save_metadata(self, image_id: str, metadata: Dict[str, Any]) -> None:
        """Save versions.json for an image."""
        image_dir = self._get_image_dir(image_id)
        image_dir.mkdir(parents=True, exist_ok=True)

        metadata_path = self._get_metadata_path(image_id)
        metadata_path.write_text(
            json.dumps(metadata, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _calculate_checksum(self, filepath: Path) -> str:
        """Calculate SHA256 checksum of file."""
        content = filepath.read_bytes()
        return f"sha256:{hashlib.sha256(content).hexdigest()}"

    def _get_next_version_number(self, image_id: str) -> int:
        """Get next version number for an image."""
        metadata = self._load_metadata(image_id)
        if not metadata:
            return 1

        versions = metadata.get("versions", [])
        return len(versions) + 1

    def save_version(
        self,
        yaml_content: str,
        image_id: str,
        message: str = "",
        author: str = "system",
    ) -> str:
        """Save current YAML state as a new version.

        Args:
            yaml_content: YAML content to save
            image_id: Image identifier
            message: Change summary message
            author: Author identifier

        Returns:
            Generated version_id
        """
        # 1. Generate version ID
        version_num = self._get_next_version_number(image_id)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        version_id = f"v{version_num}_{timestamp}"

        # 2. Create directories
        image_dir = self._get_image_dir(image_id)
        image_dir.mkdir(parents=True, exist_ok=True)

        # 3. Write YAML file
        yaml_path = image_dir / f"{version_id}.yaml"
        yaml_path.write_text(yaml_content, encoding="utf-8")

        # 4. Calculate metadata
        file_size = yaml_path.stat().st_size
        checksum = self._calculate_checksum(yaml_path)

        # 5. Count changes (if parent exists)
        changes_count = 0
        parent_version_id = None
        current = self._load_metadata(image_id)

        if current and current.get("current_version"):
            parent_version_id = current["current_version"]
            try:
                diff = self.diff(image_id, parent_version_id, version_id)
                changes_count = diff.total_changes
            except Exception:
                pass

        # 6. Create metadata
        version_metadata = VersionMetadata(
            version_id=version_id,
            created_at=datetime.now(timezone.utc),
            created_by=author,
            parent_version_id=parent_version_id,
            change_summary=message or "Version saved",
            changes_count=changes_count,
            file_path=f"{version_id}.yaml",
            file_size=file_size,
            checksum=checksum,
        )

        # 7. Update versions.json
        if current is None:
            current = {
                "image_id": image_id,
                "current_version": version_id,
                "versions": [],
            }

        current["current_version"] = version_id
        current["versions"].append(version_metadata.to_dict())

        self._save_metadata(image_id, current)

        logger.info(f"Saved version {version_id} for {image_id}")
        return version_id

    def get_version(self, image_id: str, version_id: str) -> str:
        """Load YAML content for specific version.

        Args:
            image_id: Image identifier
            version_id: Version to retrieve

        Returns:
            YAML content string

        Raises:
            ValueError: If version not found
        """
        yaml_path = self._get_image_dir(image_id) / f"{version_id}.yaml"

        if not yaml_path.exists():
            raise ValueError(f"Version {version_id} not found for {image_id}")

        return yaml_path.read_text(encoding="utf-8")

    def get_current_version(self, image_id: str) -> Optional[str]:
        """Get current version ID for an image.

        Args:
            image_id: Image identifier

        Returns:
            Current version ID or None if no versions
        """
        metadata = self._load_metadata(image_id)
        if not metadata:
            return None
        return metadata.get("current_version")

    def list_versions(self, image_id: str) -> List[VersionInfo]:
        """Get all versions for an image.

        Args:
            image_id: Image identifier

        Returns:
            List of VersionInfo objects (newest first)
        """
        metadata = self._load_metadata(image_id)
        if not metadata:
            return []

        versions = []
        for v in metadata.get("versions", []):
            vm = VersionMetadata.from_dict(v)
            versions.append(VersionInfo(
                version_id=vm.version_id,
                created_at=vm.created_at,
                created_by=vm.created_by,
                parent_version_id=vm.parent_version_id,
                change_summary=vm.change_summary,
                changes_count=vm.changes_count,
            ))

        # Return newest first
        return list(reversed(versions))

    def diff(
        self,
        image_id: str,
        version_from: str,
        version_to: str,
    ) -> DiffResult:
        """Compare two versions using DeepDiff.

        Args:
            image_id: Image identifier
            version_from: Source version ID
            version_to: Target version ID

        Returns:
            DiffResult with structural comparison
        """
        # 1. Load both versions
        yaml1 = self.get_version(image_id, version_from)
        yaml2 = self.get_version(image_id, version_to)

        # 2. Parse to dict
        spec1 = self._parse_yaml(yaml1)
        spec2 = self._parse_yaml(yaml2)

        # 3. DeepDiff comparison
        try:
            from deepdiff import DeepDiff

            diff = DeepDiff(
                spec1,
                spec2,
                ignore_order=True,
                verbose_level=2,
            )

            # 4. Analyze changes
            added = len(diff.get("dictionary_item_added", []))
            added += len(diff.get("iterable_item_added", []))
            removed = len(diff.get("dictionary_item_removed", []))
            removed += len(diff.get("iterable_item_removed", []))
            modified = len(diff.get("values_changed", []))
            type_changes = len(diff.get("type_changes", []))

            # 5. Generate summary
            summary = self._generate_diff_summary(diff, added, removed, modified)

            return DiffResult(
                version_from=version_from,
                version_to=version_to,
                changes=dict(diff),
                summary=summary,
                added_count=added,
                removed_count=removed,
                modified_count=modified,
                type_changes_count=type_changes,
            )

        except ImportError:
            # Fallback without DeepDiff
            logger.warning("DeepDiff not installed, using simple comparison")
            has_changes = spec1 != spec2
            return DiffResult(
                version_from=version_from,
                version_to=version_to,
                changes={"has_changes": has_changes},
                summary="Changes detected" if has_changes else "No changes",
                modified_count=1 if has_changes else 0,
            )

    def _parse_yaml(self, content: str) -> Dict[str, Any]:
        """Parse YAML string to dictionary."""
        try:
            from ruamel.yaml import YAML
            from io import StringIO

            yaml = YAML()
            result = yaml.load(StringIO(content))
            return dict(result) if result else {}

        except ImportError:
            import yaml
            return yaml.safe_load(content) or {}

    def _generate_diff_summary(
        self,
        diff: Any,
        added: int,
        removed: int,
        modified: int,
    ) -> str:
        """Generate human-readable diff summary.

        Args:
            diff: DeepDiff result
            added: Number of added items
            removed: Number of removed items
            modified: Number of modified items

        Returns:
            Summary string
        """
        parts = []

        if added:
            parts.append(f"{added} added")
        if removed:
            parts.append(f"{removed} removed")
        if modified:
            parts.append(f"{modified} modified")

        if not parts:
            return "No changes detected"

        summary = ", ".join(parts)

        # Add specific changes for elements
        values_changed = diff.get("values_changed", {})
        for key, change in list(values_changed.items())[:3]:
            if "latex" in key:
                summary += f"\n  - LaTeX modified"
            elif "position" in key:
                summary += f"\n  - Position adjusted"
            elif "style" in key:
                summary += f"\n  - Style updated"

        return summary

    def rollback(self, image_id: str, version_id: str) -> str:
        """Rollback to a previous version.

        Creates a new version with the content of the specified version.

        Args:
            image_id: Image identifier
            version_id: Version to rollback to

        Returns:
            New version_id (rollback creates a new version)
        """
        # Get content from target version
        content = self.get_version(image_id, version_id)

        # Save as new version
        new_version_id = self.save_version(
            yaml_content=content,
            image_id=image_id,
            message=f"Rollback to {version_id}",
            author="system",
        )

        logger.info(f"Rolled back {image_id} to {version_id} (new: {new_version_id})")
        return new_version_id

    def delete_version(self, image_id: str, version_id: str) -> bool:
        """Delete a specific version.

        Args:
            image_id: Image identifier
            version_id: Version to delete

        Returns:
            True if deleted, False if not found
        """
        yaml_path = self._get_image_dir(image_id) / f"{version_id}.yaml"

        if not yaml_path.exists():
            return False

        # Remove file
        yaml_path.unlink()

        # Update metadata
        metadata = self._load_metadata(image_id)
        if metadata:
            metadata["versions"] = [
                v for v in metadata.get("versions", [])
                if v.get("version_id") != version_id
            ]

            # Update current if needed
            if metadata.get("current_version") == version_id:
                versions = metadata.get("versions", [])
                metadata["current_version"] = versions[-1]["version_id"] if versions else None

            self._save_metadata(image_id, metadata)

        logger.info(f"Deleted version {version_id} for {image_id}")
        return True

    def get_version_count(self, image_id: str) -> int:
        """Get number of versions for an image.

        Args:
            image_id: Image identifier

        Returns:
            Number of versions
        """
        metadata = self._load_metadata(image_id)
        if not metadata:
            return 0
        return len(metadata.get("versions", []))


# =============================================================================
# Export
# =============================================================================

__all__ = [
    "DiffResult",
    "VersionManager",
    "VersionMetadata",
]
