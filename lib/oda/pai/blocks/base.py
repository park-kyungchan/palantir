"""
ODA PAI Blocks - Base Types
============================

Defines the foundational block types for the PAI Block Type System.
Blocks are the fundamental units of content in the PAI infrastructure.

ObjectTypes:
    - BlockType: Base class for all content blocks

Enums:
    - BlockKind: Category of block (TEXT, CODE, IMAGE, etc.)
    - ContentEncoding: How content is encoded (UTF8, BASE64, BINARY)
    - TextFormat: Text formatting types (PLAIN, MARKDOWN, HTML, RST)
"""

from __future__ import annotations

import hashlib
from abc import abstractmethod
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import ConfigDict, Field, field_validator

from lib.oda.ontology.ontology_types import OntologyObject
from lib.oda.ontology.registry import register_object_type


# =============================================================================
# ENUMS
# =============================================================================


class BlockKind(str, Enum):
    """
    Categories of content blocks in the PAI system.

    - TEXT: Plain or formatted text content
    - CODE: Source code with syntax highlighting
    - IMAGE: Binary image data (PNG, JPEG, etc.)
    - COMPOSITE: Container for nested blocks
    - REFERENCE: Link to external content
    """

    TEXT = "text"
    CODE = "code"
    IMAGE = "image"
    COMPOSITE = "composite"
    REFERENCE = "reference"

    @property
    def is_container(self) -> bool:
        """Check if this block kind can contain child blocks."""
        return self == BlockKind.COMPOSITE

    @property
    def is_binary(self) -> bool:
        """Check if this block kind contains binary data."""
        return self == BlockKind.IMAGE


class ContentEncoding(str, Enum):
    """
    Content encoding types for block data.

    - UTF8: Standard UTF-8 text encoding
    - BASE64: Base64-encoded binary data
    - BINARY: Raw binary data
    """

    UTF8 = "utf8"
    BASE64 = "base64"
    BINARY = "binary"

    @property
    def is_text_based(self) -> bool:
        """Check if this encoding represents text content."""
        return self == ContentEncoding.UTF8


class TextFormat(str, Enum):
    """
    Text formatting types for text blocks.

    - PLAIN: Unformatted plain text
    - MARKDOWN: Markdown-formatted text
    - HTML: HTML-formatted text
    - RST: reStructuredText format
    """

    PLAIN = "plain"
    MARKDOWN = "markdown"
    HTML = "html"
    RST = "rst"

    @property
    def supports_rich_formatting(self) -> bool:
        """Check if this format supports rich text formatting."""
        return self in (TextFormat.MARKDOWN, TextFormat.HTML, TextFormat.RST)

    @property
    def file_extension(self) -> str:
        """Get the typical file extension for this format."""
        extensions = {
            TextFormat.PLAIN: ".txt",
            TextFormat.MARKDOWN: ".md",
            TextFormat.HTML: ".html",
            TextFormat.RST: ".rst",
        }
        return extensions[self]


# =============================================================================
# BASE BLOCK TYPE
# =============================================================================


@register_object_type
class BlockType(OntologyObject):
    """
    Base class for all block types in the PAI Block Type System.

    BlockType provides the foundational structure for content blocks:
    - Unique identification via OntologyObject inheritance
    - Content hashing for integrity verification
    - Hierarchical positioning for document structure
    - Extensible metadata for custom attributes

    All specific block types (TextBlock, CodeBlock, ImageBlock, etc.)
    inherit from this base class.
    """

    block_kind: BlockKind = Field(
        description="The category of this block (TEXT, CODE, IMAGE, etc.)"
    )

    content_hash: str = Field(
        default="",
        description="SHA-256 hash of the block content for integrity verification",
        pattern=r"^([a-f0-9]{64})?$",
    )

    content_encoding: ContentEncoding = Field(
        default=ContentEncoding.UTF8,
        description="The encoding format of the block content",
    )

    parent_block_id: Optional[str] = Field(
        default=None,
        description="Reference to parent composite block (if nested)",
    )

    position: int = Field(
        default=0,
        description="Order position within parent block (0-indexed)",
        ge=0,
    )

    block_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible key-value metadata store for custom attributes",
    )

    model_config = ConfigDict(
        use_enum_values=False,
        validate_assignment=True,
        extra="forbid",
    )

    @field_validator("content_hash")
    @classmethod
    def validate_content_hash(cls, v: str) -> str:
        """Validate that content_hash is a valid SHA-256 hex string or empty."""
        if v and len(v) != 64:
            raise ValueError("content_hash must be a 64-character SHA-256 hex string")
        return v.lower() if v else v

    @abstractmethod
    def encode_content(self) -> bytes:
        """
        Encode the block content to bytes for hashing or storage.

        Returns:
            The content encoded as bytes.
        """
        raise NotImplementedError("Subclasses must implement encode_content()")

    @abstractmethod
    def decode_content(self, data: bytes) -> None:
        """
        Decode bytes and populate the block content fields.

        Args:
            data: The encoded content as bytes.
        """
        raise NotImplementedError("Subclasses must implement decode_content()")

    def compute_hash(self) -> str:
        """
        Compute the SHA-256 hash of the block content.

        Returns:
            The SHA-256 hash as a 64-character lowercase hex string.
        """
        content_bytes = self.encode_content()
        return hashlib.sha256(content_bytes).hexdigest()

    def update_hash(self) -> str:
        """
        Compute and update the content_hash field.

        Returns:
            The newly computed hash.
        """
        self.content_hash = self.compute_hash()
        return self.content_hash

    def verify_integrity(self) -> bool:
        """
        Verify that the content matches the stored hash.

        Returns:
            True if the computed hash matches the stored hash.
        """
        if not self.content_hash:
            return True  # No hash to verify against
        return self.compute_hash() == self.content_hash

    @property
    def is_nested(self) -> bool:
        """Check if this block is nested within a parent block."""
        return self.parent_block_id is not None

    def set_metadata(self, key: str, value: Any) -> None:
        """Set a metadata key-value pair."""
        self.block_metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get a metadata value by key."""
        return self.block_metadata.get(key, default)
