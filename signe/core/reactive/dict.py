from __future__ import annotations
from collections import UserDict
from typing import Any
from signe.core.reactive.reactive import reactive
from signe.core.consts import EffectState

from signe.core.deps import GetterDepManager

from signe.core.utils import common_not_eq_value
from weakref import WeakValueDictionary, WeakKeyDictionary


# _ins_map: WeakValueDictionary[DictProxy, object] = WeakValueDictionary()
_proxy_dep_map: WeakKeyDictionary[DictProxy, GetterDepManager] = WeakKeyDictionary()


class DictProxy(UserDict):
    def __init__(self, data):
        super().__init__()
        self.data = data
        _proxy_dep_map[self] = GetterDepManager()

    def __getitem__(self, key):
        dep_manager = _proxy_dep_map[self]

        dep_manager.tracked(key)
        res = self.data[key]
        return reactive(res)

    def __setitem__(self, key, item):
        org_value = self.data[key]
        self.data[key] = item

        if common_not_eq_value(org_value, item):
            self.__dep_manager.triggered(key, item, EffectState.NEED_UPDATE)

    # def __iter__(self) -> Iterator:
    #     signal = track(
    #         self, self._method_signal_map, "__iter__", lambda: None, SignalOption(False)
    #     )
    #     signal.value
    #     return super().__iter__()

    def __len__(self) -> int:
        self.__dep_manager.tracked("len")

        return len(self.data)

    def pop(self, i: int = -1) -> Any:
        super().pop(i)
        self.__dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)

    def clear(self) -> None:
        super().clear()
        self.__dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)
