"""
Orion ODA v4.0 - Lifecycle Hooks
================================

Provides object lifecycle hooks for OntologyObjects:
- pre_save: Called before object is saved
- post_save: Called after object is saved
- pre_delete: Called before object is deleted
- validation: Custom validation hooks

Reference: lib/oda/pai/hooks/ for event-based hook patterns
"""

from lib.oda.ontology.hooks.lifecycle import (
    LifecycleHook,
    LifecycleHookType,
    LifecycleHookPriority,
    LifecycleHookRegistry,
    LifecycleContext,
    get_lifecycle_registry,
    register_lifecycle_hook,
    lifecycle_hook,
    run_hooks,
)

__all__ = [
    "LifecycleHook",
    "LifecycleHookType",
    "LifecycleHookPriority",
    "LifecycleHookRegistry",
    "LifecycleContext",
    "get_lifecycle_registry",
    "register_lifecycle_hook",
    "lifecycle_hook",
    "run_hooks",
]
