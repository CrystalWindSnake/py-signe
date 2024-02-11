from __future__ import annotations
from abc import abstractmethod
from typing import Callable, List, TypeVar, Generic, Set, TYPE_CHECKING

from signe.core.protocols import CallerProtocol, GetterProtocol
from weakref import ref as weakref

if TYPE_CHECKING:
    from .runtime import Executor

_T = TypeVar("_T")


class GetterMixin:
    def __init__(self) -> None:
        self.__callers: Set[CallerMixin] = set()

    def mark_caller(self, caller: CallerMixin):
        self.__callers.add(caller)

    def remove_caller(self, caller: CallerMixin):
        self.__callers.remove(caller)

    def track(self):
        ...

    @property
    def callers(self):
        return tuple(self.__callers)

    @property
    def value(self):
        ...


class CallerMixin:
    @property
    def is_effect(self) -> bool:
        ...

    @property
    def is_pedding(self) -> bool:
        ...

    @property
    def is_need_update(self) -> bool:
        ...

    @property
    def auto_collecting_dep(self) -> bool:
        ...

    def update(self):
        ...

    def add_upstream_ref(self, signal: GetterMixin):
        ...

    def update_pending(
        self, getter: GetterMixin, is_change_point: bool = True, is_set_pending=True
    ):
        ...

    def add_cleanup(self, fn: Callable[[], None]):
        ...

    @abstractmethod
    def made_upstream_confirm_state(self):
        pass

    @abstractmethod
    def confirm_state(self):
        pass


class Tracker(Generic[_T]):
    def __init__(self, owner: GetterProtocol, executor: Executor, value: _T) -> None:
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
