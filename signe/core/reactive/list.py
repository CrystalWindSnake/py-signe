from __future__ import annotations
from collections import UserList
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, Iterable, Iterator, List

from weakref import WeakValueDictionary
from functools import partial

from signe.core.signal import Signal, SignalOption
from signe.model import reactive


@dataclass
class MethodTrigger:
    name: str
    method: Callable[[ListProxy], Any]


def len_trigger(proxy: ListProxy):
    return len(proxy.data)


def iter_trigger(proxy: ListProxy):
    return None


_method_triggers = {
    "append": [
        MethodTrigger("len", len_trigger),
        MethodTrigger("__iter__", iter_trigger),
    ],
    "remove": [
        MethodTrigger("len", len_trigger),
        MethodTrigger("__iter__", iter_trigger),
    ],
    "clear": [
        MethodTrigger("len", len_trigger),
        MethodTrigger("__iter__", iter_trigger),
    ],
}


def track(
    proxy: ListProxy, dict: WeakValueDictionary, key, new_value_method, sinal_opt=None
):
    signal = dict.get(key)
    if not signal:
        value = new_value_method()
        signal = Signal(value, sinal_opt)
        dict[key] = signal

    return signal


class ListProxy(UserList):
    def __init__(self, initlist):
        super().__init__(initlist)
        self._index_signal_map: WeakValueDictionary[int, Signal] = WeakValueDictionary()
        self._method_signal_map: WeakValueDictionary[
            str, Signal
        ] = WeakValueDictionary()

    def __getitem__(self, i):
        signal = track(self, self._index_signal_map, i, partial(super().__getitem__, i))

        obj = reactive(signal.value)
        signal.value = obj
        return obj

    def __setitem__(self, i, item):
        self.data[i] = item
        signal = self._index_signal_map.get(i)
        if not signal:
            return
        signal.value = item

    def __trigger_signals(self, target: str):
        for trigger in _method_triggers.get(target, ()):
            signal = self._method_signal_map.get(trigger.name)

            if signal:
                signal.value = trigger.method(self)

    def __iter__(self) -> Iterator:
        signal = track(
            self, self._method_signal_map, "__iter__", lambda: None, SignalOption(False)
        )
        signal.value
        return super().__iter__()

    def __len__(self) -> int:
        signal = track(self, self._method_signal_map, "len", super().__len__)

        return signal.value

    def append(self, item: Any) -> None:
        super().append(item)

        self.__trigger_signals("append")

    def extend(self, other: Iterable) -> None:
        super().extend(other)
        self.__trigger_signals("append")

    def remove(self, item: Any) -> None:
        super().remove(item)
        self.__trigger_signals("remove")

    def pop(self, i: int = -1) -> Any:
        super().pop(i)
        self.__trigger_signals("remove")

    def clear(self) -> None:
        super().clear()
        self.__trigger_signals("clear")
