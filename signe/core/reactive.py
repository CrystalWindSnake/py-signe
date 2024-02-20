from __future__ import annotations
from collections import UserDict, UserList
from typing import (
    Any,
    Callable,
    Iterator,
    Mapping,
    TypeVar,
    cast,
    Iterable,
)
from signe.core.consts import EffectState
from signe.core.deps import GetterDepManager
from signe.core.helper import is_object
from signe.core.protocols import RawableProtocol
from signe.core.utils import common_not_eq_value
from .context import get_executor
from .batch import batch
from weakref import WeakKeyDictionary, WeakValueDictionary
import types

T = TypeVar("T")
P = TypeVar("P")


_proxy_maps: WeakValueDictionary = WeakValueDictionary()


def track_all_deep(obj):
    stack = [obj]

    while len(stack):
        current = stack.pop()
        if isinstance(current, ListProxy):
            for value in current:
                if is_reactive(value):
                    stack.append(value)

        elif isinstance(current, DictProxy):
            for value in current.values():
                if is_reactive(value):
                    stack.append(value)
        elif isinstance(current, InstanceProxy):
            for key in _get_data_fields(current):
                value = getattr(current, key)
                if is_reactive(value):
                    stack.append(value)
        else:
            pass


def track_all(obj, deep=False):
    executor = get_executor()
    if not executor.should_track():
        return

    if isinstance(obj, (DictProxy, ListProxy)):
        if deep:
            track_all_deep(obj)
        else:
            iter(obj)
    elif isinstance(obj, (InstanceProxy)):
        if deep:
            track_all_deep(obj)
        else:
            for key in _get_data_fields(obj):
                getattr(obj, key)
    else:
        pass


def reactive(obj: T) -> T:
    if not is_object(obj) or is_reactive(obj):
        return cast(T, obj)

    obj_id = id(obj)
    proxy = _proxy_maps.get(obj_id)

    if proxy:
        return proxy  # type: ignore

    if isinstance(obj, Mapping):
        proxy = DictProxy(obj)

    elif isinstance(obj, Iterable):
        proxy = ListProxy(obj)
    else:
        proxy = InstanceProxy(obj)

    _proxy_maps[obj_id] = proxy
    return cast(T, proxy)

    # return obj


def to_reactive(obj: T) -> T:
    res = reactive(obj) if is_object(obj) else obj
    return cast(T, res)


def is_reactive(obj: object) -> bool:
    return _is_proxy(obj)


def to_raw(obj: T) -> T:
    if isinstance(obj, RawableProtocol):
        return obj.to_raw()
    return obj


def _is_proxy(obj):
    return isinstance(obj, (DictProxy, ListProxy, InstanceProxy))


class DictProxy(UserDict):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self._dep_manager = GetterDepManager()
        self.__nested = set()

    def __getitem__(self, key):
        self._dep_manager.tracked(key)
        res = reactive(self.data[key])
        if _is_proxy(res):
            self.__nested.add(res)
        return res

    def __setitem__(self, key, item):
        is_new = key not in self.data

        @batch
        def _():
            if is_new:
                self.data[key] = item
                self._dep_manager.triggered(
                    "len", len(self.data), EffectState.NEED_UPDATE
                )

            else:
                org_value = self.data[key]
                self.data[key] = item

                if common_not_eq_value(org_value, item):
                    self._dep_manager.triggered(key, item, EffectState.NEED_UPDATE)

            self._dep_manager.triggered("__iter__", None, EffectState.NEED_UPDATE)

    def __iter__(self) -> Iterator:
        self._dep_manager.tracked("__iter__")
        return super().__iter__()

    def __len__(self) -> int:
        self._dep_manager.tracked("len")

        return len(self.data)

    def __contains__(self, key: object) -> bool:
        result = key in self.data
        self._dep_manager.tracked("len")
        return result

    def __delitem__(self, key):
        del self.data[key]
        self._dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)

    def pop(self, i: int = -1) -> Any:
        super().pop(i)
        self._dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)

    def clear(self) -> None:
        super().clear()
        self._dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)

    def __hash__(self) -> int:
        return hash(id(self))

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, self.__class__):
            return self.__hash__() == __value.__hash__()

        return False

    def to_raw(self):
        return self.data


class ListProxy(UserList):
    def __init__(self, initlist):
        super().__init__(initlist)
        self._dep_manager = GetterDepManager()
        self.__nested = set()

    def __getitem__(self, i):
        self._dep_manager.tracked(i)
        res = reactive(self.data[i])
        if _is_proxy(res):
            self.__nested.add(res)
        return res

    def __setitem__(self, i, item):
        org_value = self.data[i]
        self.data[i] = item

        if common_not_eq_value(org_value, item):

            @batch
            def _():
                self._dep_manager.triggered(i, item, EffectState.NEED_UPDATE)
                self._dep_manager.triggered("__iter__", None, EffectState.NEED_UPDATE)

    def __iter__(self) -> Iterator:
        self._dep_manager.tracked("__iter__")
        return super().__iter__()

    def __len__(self) -> int:
        self._dep_manager.tracked("len")

        return len(self.data)

    def append(self, item: Any) -> None:
        super().append(to_raw(item))

        @batch
        def _():
            self._dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)
            self._dep_manager.triggered("__iter__", None, EffectState.NEED_UPDATE)

    def extend(self, other: Iterable) -> None:
        super().extend((to_raw(o) for o in other))

        @batch
        def _():
            self._dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)
            self._dep_manager.triggered("__iter__", None, EffectState.NEED_UPDATE)

    def remove(self, item: Any) -> None:
        super().remove(to_raw(item))

        @batch
        def _():
            self._dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)
            self._dep_manager.triggered("__iter__", None, EffectState.NEED_UPDATE)

    def pop(self, i: int = -1) -> Any:
        super().pop(i)

        @batch
        def _():
            self._dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)
            self._dep_manager.triggered("__iter__", None, EffectState.NEED_UPDATE)

    def clear(self) -> None:
        super().clear()

        @batch
        def _():
            self._dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)
            self._dep_manager.triggered("__iter__", None, EffectState.NEED_UPDATE)

    def __contains__(self, item) -> bool:
        result = to_raw(item) in self.data
        self._dep_manager.tracked("len")
        return result

    def to_raw(self):
        return self.data


_instance_proxy_maps: WeakKeyDictionary = WeakKeyDictionary()
_instance_dep_maps: WeakKeyDictionary = WeakKeyDictionary()


def _register_ins(
    proxy: InstanceProxy,
    ins,
):
    _instance_proxy_maps[proxy] = ins
    _instance_dep_maps[proxy] = GetterDepManager()


def _is_instance_method(obj, key: str):
    return isinstance(getattr(obj, key), Callable)


def _track_ins(proxy: InstanceProxy, key):
    ins = _instance_proxy_maps.get(proxy)
    if _is_instance_method(ins, key):
        method = getattr(ins, key)

        def replace_method(instance, *args, **kws):
            method.__func__(instance, *args, **kws)
            method(*args, **kws)

        fake_method = types.MethodType(replace_method, proxy)
        return fake_method
    else:
        dep_manager = _instance_dep_maps.get(proxy)
        assert ins
        assert dep_manager

        dep_manager.tracked(key)

        value = getattr(ins, key)

        return value


def _trigger_ins(proxy: InstanceProxy, key, value):
    ins = _instance_proxy_maps.get(proxy)
    dep_manager = _instance_dep_maps.get(proxy)

    assert ins
    assert dep_manager

    setattr(ins, key, value)
    dep_manager.triggered(key, value, EffectState.NEED_UPDATE)


def _get_data_fields(proxy: InstanceProxy):
    ins = _instance_proxy_maps.get(proxy)
    return [f for f in dir(ins) if f[0] != "_"]


class InstanceProxy:
    def __init__(self, ins) -> None:
        _register_ins(self, ins)

    def __getattr__(self, _name: str) -> Any:
        value = _track_ins(self, _name)
        return value

    def __setattr__(self, _name: str, _value: Any) -> None:
        _trigger_ins(self, _name, _value)
