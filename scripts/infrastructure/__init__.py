"""
Orion Infrastructure Layer
===========================
Cross-cutting concerns: Event Bus, Caching, Metrics, etc.
"""

from scripts.infrastructure.event_bus import EventBus, DomainEvent

__all__ = ["EventBus", "DomainEvent"]
