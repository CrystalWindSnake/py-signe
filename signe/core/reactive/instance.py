from __future__ import annotations
from typing import Any, TYPE_CHECKING, Dict, cast
from weakref import WeakValueDictionary, WeakKeyDictionary
from signe.core.deps import DepManager


_ins_map: WeakValueDictionary[InstanceProxy, object] = WeakValueDictionary()
_proxy_dep_map: WeakKeyDictionary[InstanceProxy, DepManager] = WeakKeyDictionary()


def register(
    proxy: InstanceProxy,
    ins,
):
    _ins_map[proxy] = ins
    _proxy_dep_map[proxy] = DepManager(ins)


def track(proxy: InstanceProxy, key):
    ins = _ins_map.get(proxy)
    dep_manager = _proxy_dep_map.get(proxy)
    assert ins
    assert dep_manager

    dep_manager.tracked(key)

    value = getattr(ins, key)

    return value


def trigger(proxy: InstanceProxy, key, value):
    ins = _ins_map.get(proxy)
    dep_manager = _proxy_dep_map.get(proxy)

    assert ins
    assert dep_manager

    setattr(ins, key, value)
    dep_manager.triggered(key, value)


class InstanceProxy:
    def __init__(self, ins) -> None:
        register(self, ins)

    def __getattr__(self, _name: str) -> Any:
        value = track(self, _name)
        return value

    def __setattr__(self, _name: str, _value: Any) -> None:
        trigger(self, _name, _value)
