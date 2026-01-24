from __future__ import annotations

import pytest

from lib.oda.ontology.hooks import (
    LifecycleContext,
    LifecycleHookPriority,
    LifecycleHookRegistry,
    LifecycleHookType,
    get_lifecycle_registry,
    lifecycle_hook,
    run_hooks,
)
from lib.oda.ontology.hooks.lifecycle import HookResult
from lib.oda.ontology.ontology_types import OntologyObject


class _Doc(OntologyObject):
    name: str


@pytest.mark.asyncio
async def test_lifecycle_hooks_run_in_priority_order_and_can_modify_object() -> None:
    LifecycleHookRegistry.reset_instance()
    _ = get_lifecycle_registry()

    @lifecycle_hook(LifecycleHookType.PRE_SAVE, priority=LifecycleHookPriority.CRITICAL)
    async def forbid_empty(obj: _Doc, context: LifecycleContext) -> HookResult:
        if not obj.name.strip():
            return HookResult.abort_operation("empty")
        return HookResult.ok(hook="forbid_empty")

    @lifecycle_hook(LifecycleHookType.PRE_SAVE, priority=LifecycleHookPriority.HIGH)
    async def normalize(obj: _Doc, context: LifecycleContext) -> HookResult:
        obj.name = obj.name.strip()
        return HookResult.ok(modified_object=obj, hook="normalize")

    doc = _Doc(name="  hello  ")
    ctx = LifecycleContext.for_save(doc, actor_id="tester")
    result = await run_hooks(LifecycleHookType.PRE_SAVE, obj=doc, context=ctx)

    assert result.aborted is False
    assert result.final_object is not None
    assert result.final_object.name == "hello"
    assert [r.metadata.get("hook") for r in result.hook_results] == ["forbid_empty", "normalize"]


@pytest.mark.asyncio
async def test_lifecycle_hooks_can_abort_chain() -> None:
    LifecycleHookRegistry.reset_instance()
    _ = get_lifecycle_registry()

    @lifecycle_hook(LifecycleHookType.PRE_SAVE, priority=LifecycleHookPriority.CRITICAL)
    async def forbid_empty(obj: _Doc, context: LifecycleContext) -> HookResult:
        if not obj.name.strip():
            return HookResult.abort_operation("empty")
        return HookResult.ok()

    @lifecycle_hook(LifecycleHookType.PRE_SAVE, priority=LifecycleHookPriority.HIGH)
    async def should_not_run(obj: _Doc, context: LifecycleContext) -> HookResult:
        return HookResult.ok(hook="should_not_run")

    doc = _Doc(name="   ")
    ctx = LifecycleContext.for_save(doc, actor_id="tester")
    result = await run_hooks(LifecycleHookType.PRE_SAVE, obj=doc, context=ctx)

    assert result.aborted is True
    assert result.abort_reason == "empty"
    assert [r.metadata.get("hook") for r in result.hook_results] == [None]

