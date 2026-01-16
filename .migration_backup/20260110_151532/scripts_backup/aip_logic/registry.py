from __future__ import annotations

from typing import Dict, Type

from scripts.aip_logic.function import LogicFunction, Input, Output

_REGISTRY: Dict[str, Type[LogicFunction[Input, Output]]] = {}


def register_logic(name: str):
    def _decorator(fn_cls: Type[LogicFunction[Input, Output]]):
        _REGISTRY[name] = fn_cls
        return fn_cls
    return _decorator


def get_logic_function(name: str) -> Type[LogicFunction[Input, Output]]:
    if name not in _REGISTRY:
        raise KeyError(f"LogicFunction not registered: {name}")
    return _REGISTRY[name]


def list_logic_functions() -> Dict[str, Type[LogicFunction[Input, Output]]]:
    return dict(_REGISTRY)
