from __future__ import annotations
from typing import TypeVar, Generic, Set

from signe.core.protocols import CallerProtocol, GetterProtocol
from weakref import ref as weakref
from .protocols import ExecutorProtocol

_T = TypeVar("_T")


class Tracker(Generic[_T]):
    def __init__(
        self, owner: GetterProtocol, executor: ExecutorProtocol, value: _T
    ) -> None:
        self._owner = weakref(owner)
        self._callers: Set[CallerProtocol] = set()
        self._value = value
        self._executor = executor

    def get_value_with_track(self):
        self.track()
        return self._value

    def update_value(self, value: _T):
        self._value = value

    def get_value_without_track(self):
        return self._value

    @property
    def callers(self):
        return tuple(self._callers)

    def track(self):
        running_caller = self._executor.get_running_caller()

        if running_caller and running_caller.auto_collecting_dep:
            self.__collecting_dependencies(running_caller)

    def mark_caller(self, caller: CallerProtocol):
        self._callers.add(caller)

    def remove_caller(self, caller: CallerProtocol):
        self._callers.remove(caller)

    def __collecting_dependencies(self, running_effect: CallerProtocol):
        self.mark_caller(running_effect)

        owner = self._owner()
        if owner:
            running_effect.add_upstream_ref(owner)
