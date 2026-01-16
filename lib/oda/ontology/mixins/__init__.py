"""
Orion ODA v4.0 - Ontology Mixins
================================

This package provides mixin classes for OntologyObjects:
- StatusMixin: Lifecycle status management with transition validation

Schema Version: 4.0.0
"""

from lib.oda.ontology.mixins.status_mixin import (
    StatusMixin,
    StatusTransitionContext,
)

__all__ = [
    "StatusMixin",
    "StatusTransitionContext",
]
