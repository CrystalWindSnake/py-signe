from __future__ import annotations
from typing import Callable, Literal, Iterable


class GetterMixin:
    def remove_caller(self, caller: CallerMixin):
        ...

    def get_callers(self) -> Iterable[CallerMixin]:
        ...

    @property
    def value(self):
        ...


_T_mark_pending_type = Literal["add", "remove"]


class CallerMixin:
    @property
    def is_effect(self) -> bool:
        ...

    @property
    def is_pedding(self) -> bool:
        ...

    def update(self):
        ...

    def add_upstream_ref(self, signal: GetterMixin):
        ...

    def update_pending(self, getter: GetterMixin, is_set_pending=True):
        ...

    def add_cleanup(self, fn: Callable[[], None]):
        ...
