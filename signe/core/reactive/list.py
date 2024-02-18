from __future__ import annotations
from collections import UserList
from typing import Any, Iterable
from signe.core.consts import EffectState

from signe.core.deps import GetterDepManager

from signe.core.utils import common_not_eq_value


class ListProxy(UserList):
    def __init__(self, initlist):
        super().__init__(initlist)

        self._dep_manager = GetterDepManager()

    def __getitem__(self, i):
        self._dep_manager.tracked(i)
        return self.data[i]

    def __setitem__(self, i, item):
        org_value = self.data[i]
        self.data[i] = item

        if common_not_eq_value(org_value, item):
            self._dep_manager.triggered(i, item, EffectState.NEED_UPDATE)

    # def __iter__(self) -> Iterator:
    #     signal = track(
    #         self, self._method_signal_map, "__iter__", lambda: None, SignalOption(False)
    #     )
    #     signal.value
    #     return super().__iter__()

    def __len__(self) -> int:
        self._dep_manager.tracked("len")

        return len(self.data)

    def append(self, item: Any) -> None:
        super().append(item)

        self._dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)

    def extend(self, other: Iterable) -> None:
        super().extend(other)
        self._dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)

    def remove(self, item: Any) -> None:
        super().remove(item)
        self._dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)

    def pop(self, i: int = -1) -> Any:
        super().pop(i)
        self._dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)

    def clear(self) -> None:
        super().clear()
        self._dep_manager.triggered("len", len(self.data), EffectState.NEED_UPDATE)
