"""
ODA PAI Blocks - Block Type System
===================================

This module provides the Block Type System for the PAI infrastructure.
Blocks are the fundamental units of content that can be composed,
transformed, and evaluated.

ObjectTypes:
    - BlockType: Base class for all content blocks
    - TextBlock: Plain or formatted text content
    - CodeBlock: Source code with syntax information
    - ImageBlock: Binary image data with metadata

Enums:
    - BlockKind: Category of block (TEXT, CODE, IMAGE, etc.)
    - ContentEncoding: How content is encoded (UTF8, BASE64, BINARY)
    - TextFormat: Text formatting types (PLAIN, MARKDOWN, HTML, RST)
    - ImageMimeType: Supported image MIME types

Usage:
    >>> from lib.oda.pai.blocks import TextBlock, CodeBlock, ImageBlock
    >>> from lib.oda.pai.blocks import BlockKind, TextFormat, ImageMimeType
    >>>
    >>> # Create a text block
    >>> text = TextBlock(text="Hello, World!", format=TextFormat.PLAIN)
    >>> print(text.word_count)
    2
    >>>
    >>> # Create a code block
    >>> code = CodeBlock(code="print('hello')", language="python")
    >>> print(code.line_count)
    1
    >>>
    >>> # Create an image block from file
    >>> image = ImageBlock.from_file("logo.png", alt_text="Company Logo")
"""

from .base import (
    BlockKind,
    BlockType,
    ContentEncoding,
    TextFormat,
)

from .primitives import (
    CodeBlock,
    ImageBlock,
    ImageMimeType,
    TextBlock,
)

__all__ = [
    # Base types
    "BlockKind",
    "BlockType",
    "ContentEncoding",
    "TextFormat",
    # Primitive blocks
    "CodeBlock",
    "ImageBlock",
    "ImageMimeType",
    "TextBlock",
]

__version__ = "1.0.0"
