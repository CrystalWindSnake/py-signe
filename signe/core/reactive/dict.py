from __future__ import annotations
from collections import UserDict
from typing import Any

from signe.core.deps import DepManager

from signe.core.utils import common_not_eq_value


class DictProxy(UserDict):
    def __init__(self, data):
        super().__init__(data)
        self.__dep_manager = DepManager(self)

    def __getitem__(self, key):
        self.__dep_manager.tracked(key)
        return self.data[key]

    def __setitem__(self, key, item):
        org_value = self.data[key]
        self.data[key] = item

        if common_not_eq_value(org_value, item):
            self.__dep_manager.triggered(key, item)

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
        self.__dep_manager.triggered("len", len(self.data))

    def clear(self) -> None:
        super().clear()
        self.__dep_manager.triggered("len", len(self.data))
