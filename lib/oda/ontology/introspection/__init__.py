"""
Orion ODA V4.0 - Introspection Utilities
=========================================
Runtime introspection utilities for ODA ontology.

This package provides:
- LinkIntrospector: Query and analyze link relationships
- ObjectIntrospector: Query and analyze object types (Phase 2)

Schema Version: 4.0.0
"""

from lib.oda.ontology.introspection.links import (
    LinkIntrospector,
    LinkGraphNode,
    LinkPath,
    LinkAnalysis,
)

__all__ = [
    "LinkIntrospector",
    "LinkGraphNode",
    "LinkPath",
    "LinkAnalysis",
]
