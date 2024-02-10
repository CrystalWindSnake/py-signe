from __future__ import annotations
from abc import abstractmethod
from typing import Callable, List, Literal, Iterable, Set


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
