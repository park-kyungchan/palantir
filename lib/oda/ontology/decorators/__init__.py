"""
Orion ODA v4.0 - Ontology Decorators

This package provides decorators for ODA ObjectTypes:
- computed.py: Computed property decorator with caching and invalidation

Schema Version: 4.0.0
"""

from lib.oda.ontology.decorators.computed import (
    computed_property,
    cached_computed,
    invalidate_computed,
    ComputedPropertyMixin,
)

__all__ = [
    "computed_property",
    "cached_computed",
    "invalidate_computed",
    "ComputedPropertyMixin",
]
