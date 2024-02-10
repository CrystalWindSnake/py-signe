from __future__ import annotations
from abc import abstractmethod
from typing import Callable, Literal, Iterable


class GetterMixin:
    def remove_caller(self, caller: CallerMixin):
        ...

    def get_callers(self) -> Iterable[CallerMixin]:
        ...

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
