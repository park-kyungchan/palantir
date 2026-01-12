"""
ODA Memory Module
=================
Memory management and semantic memory integration.

Modules:
- manager: Hybrid memory manager with ODA action integration
- recall: Memory recall utilities (format_as_xml, recall)
- init_db: Database initialization
- semantic_memory: Semantic memory store
"""

# Note: Lazy imports for modules with heavy dependencies
# from lib.oda.memory.manager import MemoryManager
# from lib.oda.memory.recall import recall, format_as_xml
# from lib.oda.memory.semantic_memory import SemanticMemory

__all__ = [
    "MemoryManager",
    "recall",
    "format_as_xml",
    "SemanticMemory",
]


def __getattr__(name: str):
    """Lazy import for modules with dependencies."""
    if name == "MemoryManager":
        from lib.oda.memory.manager import MemoryManager
        return MemoryManager
    if name == "recall":
        from lib.oda.memory.recall import recall
        return recall
    if name == "format_as_xml":
        from lib.oda.memory.recall import format_as_xml
        return format_as_xml
    if name == "SemanticMemory":
        from lib.oda.memory.semantic_memory import SemanticMemory
        return SemanticMemory
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
