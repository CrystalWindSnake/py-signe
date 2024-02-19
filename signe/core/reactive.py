from collections import UserDict, UserList
from datetime import date, datetime
from typing import (
    Any,
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
from weakref import WeakValueDictionary

T = TypeVar("T")
P = TypeVar("P")


_proxy_maps: WeakValueDictionary = WeakValueDictionary()


@overload
def reactive(obj: List[T]) -> List[T]:
    ...


@overload
def reactive(obj: Dict[T, P]) -> Dict[T, P]:
    ...


@overload
def reactive(obj: T) -> T:
    ...


def reactive(obj: Union[List, Dict, T]) -> Union[List, Dict, T]:
    if isinstance(obj, (str, int, float, date, datetime, ListProxy, DictProxy)):
        return obj

    obj_id = id(obj)
    proxy = _proxy_maps.get(obj_id)

    if proxy:
        return proxy  # type: ignore

    if isinstance(obj, Mapping):
        proxy = cast(Dict, DictProxy(obj))
        _proxy_maps[obj_id] = proxy
        return proxy

    if isinstance(obj, Iterable):
        proxy = cast(List, ListProxy(obj))
        _proxy_maps[obj_id] = proxy
        return proxy
    return obj

    # return cast(T, InstanceProxy(obj))


def to_raw(obj: T) -> T:
    if isinstance(obj, RawableProtocol):
        return obj.to_raw()
    return obj


class DictProxy(UserDict):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self._dep_manager = GetterDepManager()
        self.__nested = set()

    def __getitem__(self, key):
        self._dep_manager.tracked(key)
        res = reactive(self.data[key])
        if isinstance(res, (DictProxy, ListProxy)):
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
        if isinstance(res, (DictProxy, ListProxy)):
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
