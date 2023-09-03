from collections.abc import Iterable
import sys
from typing import Tuple, Union, TypeVar, cast, Dict, Any, Generic
from typing_extensions import SupportsIndex
from signe import batch, createSignal
from signe.utils import TGetter, TSetter
from collections import UserList, UserDict


T = TypeVar("T")

_proxy_map = {}


class Proxy:
    def __init__(self, obj) -> None:
        _proxy_map[id(obj)] = self

    def toRaw(self):
        pass


TKeySignalMapKey = Union[int, str]
TKeySignalMapValue = Tuple[TGetter[Any], TSetter[Any]]
TKeySignalMap = Dict[TKeySignalMapKey, TKeySignalMapValue]


class CollectionsProxy(Proxy):
    def __init__(self, obj) -> None:
        super().__init__(obj)
        self._keySignalMap: TKeySignalMap = {}

    def _create_signal(self, key: TKeySignalMapKey, value):
        signal = None
        if key not in self._keySignalMap:
            signal = createSignal(value,debug_name=str(key))
            self._keySignalMap[key] = signal
        else:
            signal = self._keySignalMap[key]

        return signal

    def _try_get_signal(self, key: TKeySignalMapKey):
        return self._keySignalMap.get(key, (None, None))

    def _ex_track(self, key, value):
        getter, _ = self._ex_track_return_signal(key, value)
        getter()

    def _ex_track_return_signal(self, key, value):
        getter, setter = self._create_signal(key, value)
        return getter, setter


class ListProxy(CollectionsProxy, UserList):
    def __init__(self, obj) -> None:
        super().__init__(obj)
        assert isinstance(obj, list)
        self.data = obj

    def __track_all_items(self):
        for idx in range(len(self.data)):
            self._ex_track(idx, self.data[idx])

    def __track_len(self):
        self._ex_track("__len__", len(self.data))

    def __trigger_len(self):
        _, setter = self._try_get_signal("__len__")
        if setter is not None:
            setter(len(self.data))

    def __trigger_index(self, start_idx: int):
        @batch
        def _():
            for idx in range(start_idx, len(self.data) + 1):
                _, setter = self._try_get_signal(idx)
                if setter is not None:
                    value = None if idx >= len(self.data) else self.data[idx]
                    setter(value)

    def __iter__(self):
        for item in self.data:
            yield createReactive(item)

        self.__track_all_items()
        self.__track_len()

    def __str__(self) -> str:
        value = str(self.data)  # type: ignore
        self.__track_all_items()
        return value

    def __getitem__(self, _key: int):
        value = self.data[_key]
        self._ex_track(_key, value)
        return createReactive(value)

    def __setitem__(self, _key: int, newVal):
        self.data[_key] = newVal

        _, setter = self._try_get_signal(_key)
        if setter is not None:
            setter(newVal)

    def pop(self, i: int = -1) -> Any:
        start = i
        if start == -1:
            start = len(self.data) - 1

        value = self.data.pop(i)

        @batch
        def _():
            self.__trigger_len()
            self.__trigger_index(start)

        return value

    def append(self, item: Any) -> None:
        self.data.append(item)

        @batch
        def _():
            self.__trigger_len()
            self.__trigger_index(0)

    def extend(self, other: Iterable) -> None:
        self.data.extend(other)

        @batch
        def _():
            self.__trigger_len()
            self.__trigger_index(0)

    def __len__(self) -> int:
        self.__track_len()
        return len(self.data)

    def clear(self) -> None:
        self.data.clear()

        @batch
        def _():
            self.__trigger_len()
            self.__trigger_index(0)

    def toRaw(self):
        return self.data

    def count(self, item: Any) -> int:
        if isReactive(item):
            item = item.toRaw()
        value = self.data.count(item)
        self.__track_len()
        self.__track_all_items()
        return value

    def index(
        self, item: Any, __start: SupportsIndex = 0, __stop: SupportsIndex = sys.maxsize
    ) -> int:
        value = self.data.index(item, __start, __stop)
        self.__track_len()
        self.__track_all_items()
        return value

    def insert(self, i: int, item: Any) -> None:
        self.data.insert(i, item)

        @batch
        def _():
            self.__trigger_len()
            self.__trigger_index(i)

    def remove(self, item: Any) -> None:
        org_len = len(self.data)
        self.data.remove(item)
        if len(self.data) < org_len:
            pass

            @batch
            def _():
                self.__trigger_len()
                self.__trigger_index(0)

    def sort(self, *, key: None = None, reverse: bool = False):
        self.data.sort(key=key, reverse=reverse)
        self.__trigger_index(0)

    def reverse(self):
        self.data.reverse()
        self.__trigger_index(0)


TDict = TypeVar("TDict", bound=Dict)


class DictProxy(CollectionsProxy, UserDict, Generic[TDict]):
    def __init__(self, obj: TDict) -> None:
        super().__init__(obj)
        assert isinstance(obj, dict)
        self.data = obj

    def __contains__(self, key: object) -> bool:
        result = key in self.data
        self._ex_track(key, result)
        return result

    def __track_all_items(self):
        for key, value in self.data.items():
            self._ex_track(key, value)

    def __track_len(self):
        self._ex_track("__len__", len(self.data))

    def __trigger_len(self):
        _, setter = self._try_get_signal("__len__")
        if setter is not None:
            setter(len(self.data))

    def __trigger_key(self, key, value):
        _, setter = self._try_get_signal(key)
        if setter is not None:
            setter(value)

    def __getitem__(self, _key: Any) -> Any:
        value = self.data[_key]
        self._ex_track(_key, value)
        return createReactive(value)

    def __setitem__(self, _key: Any, item: Any) -> None:
        has_key = _key in self.data
        self.data[_key] = item

        _, setter = self._try_get_signal(_key) # type: ignore
        if setter is not None:
            setter(item)

        if not has_key:
            @batch
            def _():
                self.__trigger_len()

    def __delitem__(self, key: Any) -> None:
        del self.data[key]

        @batch
        def _():
            self.__trigger_len()
            self.__trigger_key(key, None)

    def __len__(self) -> int:
        self.__track_len()
        return len(self.data)

    def get_signal(self, _key: Any):
        value = self.data[_key]
        return self._ex_track_return_signal(_key, value)

    def toRaw(self):
        return self.data


# d = DictProxy({"a": 1})


def isReactive(obj):
    return isinstance(obj, Proxy)


def createReactive(obj: T) -> T:
    if isinstance(obj, (str, int, float, tuple, bool)):
        # warn(f"Type [{type(obj)}] cannot be used as the target object of reactive.")
        return obj

    if isinstance(obj, Proxy):
        return obj

    if id(obj) in _proxy_map:
        return _proxy_map[id(obj)]

    if isinstance(obj, list):
        return cast(T, ListProxy(obj))

    if isinstance(obj, dict):
        return cast(T, DictProxy(obj))

    return obj
