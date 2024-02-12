from __future__ import annotations
from collections import UserDict
from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterator

from weakref import WeakValueDictionary
from functools import partial

from signe.core.signal import Signal, SignalOption


@dataclass
class MethodTrigger:
    name: str
    method: Callable[[DictProxy], Any]


def len_trigger(proxy: DictProxy):
    return len(proxy.data)


def iter_trigger(proxy: DictProxy):
    return None


_method_triggers = {
    "remove": [
        MethodTrigger("len", len_trigger),
        MethodTrigger("__iter__", iter_trigger),
    ],
    "clear": [
        MethodTrigger("len", len_trigger),
        MethodTrigger("__iter__", iter_trigger),
    ],
}


def track(proxy: DictProxy, dict: Dict, key, new_value_method, sinal_opt=None):
    signal = dict.get(key)
    if not signal:
        value = new_value_method()
        signal = Signal(value, sinal_opt)
        dict[key] = signal

    return signal


class DictProxy(UserDict):
    def __init__(self, data):
        self._key_signal_map: Dict[str, Signal] = {}
        self._method_signal_map: Dict[str, Signal] = {}
        super().__init__(data)

    def __getitem__(self, key):
        signal = track(
            self, self._key_signal_map, key, partial(super().__getitem__, key)
        )

        return signal.value

    def __setitem__(self, key, item):
        self.data[key] = item
        signal = self._key_signal_map.get(key)
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

    def pop(self, i: int = -1) -> Any:
        super().pop(i)
        self.__trigger_signals("remove")

    def clear(self) -> None:
        super().clear()
        self.__trigger_signals("clear")
