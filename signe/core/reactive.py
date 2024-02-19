from __future__ import annotations
from collections import UserDict, UserList
from datetime import date, datetime
from typing import (
    Any,
    Callable,
    Dict,
    Iterator,
    List,
    Mapping,
    TypeVar,
    Union,
    overload,
    cast,
    Iterable,
)
from signe.core.consts import EffectState
from signe.core.deps import GetterDepManager
from signe.core.protocols import RawableProtocol
from signe.core.utils import common_not_eq_value
from .batch import batch
from weakref import WeakKeyDictionary, WeakValueDictionary
import types

T = TypeVar("T")
P = TypeVar("P")


_proxy_maps: WeakValueDictionary = WeakValueDictionary()


def reactive(obj: T) -> T:
    if isinstance(
        obj,
        (
            str,
            int,
            float,
            date,
            datetime,
            ListProxy,
            DictProxy,
            Callable,
            InstanceProxy,
        ),
    ):
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
            self._dep_manager.triggered(i, item, EffectState.NEED_UPDATE)

    def __iter__(self) -> Iterator:
        self._dep_manager.tracked("__iter__")
        return super().__iter__()

    def __len__(self) -> int:
        self._dep_manager.tracked("len")

        return len(self.data)

    def append(self, item: Any) -> None:
        super().append(item)

        self._dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)
        self._dep_manager.triggered("__iter__", None, EffectState.NEED_UPDATE)

    def extend(self, other: Iterable) -> None:
        super().extend(other)
        self._dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)
        self._dep_manager.triggered("__iter__", None, EffectState.NEED_UPDATE)

    def remove(self, item: Any) -> None:
        super().remove(item)
        self._dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)
        self._dep_manager.triggered("__iter__", None, EffectState.NEED_UPDATE)

    def pop(self, i: int = -1) -> Any:
        super().pop(i)
        self._dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)
        self._dep_manager.triggered("__iter__", None, EffectState.NEED_UPDATE)

    def clear(self) -> None:
        super().clear()
        self._dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)
        self._dep_manager.triggered("__iter__", None, EffectState.NEED_UPDATE)

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


class InstanceProxy:
    def __init__(self, ins) -> None:
        _register_ins(self, ins)

    def __getattr__(self, _name: str) -> Any:
        value = _track_ins(self, _name)
        return value

    def __setattr__(self, _name: str, _value: Any) -> None:
        _trigger_ins(self, _name, _value)
