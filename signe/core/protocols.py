from __future__ import annotations
from typing import Callable, Iterable, Protocol, TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from .effect import Effect

_T = TypeVar("_T")


class GetterProtocol(Protocol[_T]):
    def mark_caller(self, caller: CallerProtocol):
        ...

    def remove_caller(self, caller: CallerProtocol):
        ...

    @property
    def is_signal(self) -> bool:
        ...

    @property
    def callers(self) -> Iterable[CallerProtocol]:
        ...

    @property
    def value(self) -> _T:
        ...


class CallerProtocol(Protocol[_T]):
    auto_collecting_dep: bool

    @property
    def is_effect(self) -> bool:
        ...

    def update(self) -> _T:
        ...

    def add_upstream_ref(self, getter: GetterProtocol):
        ...

    def update_pending(
        self, getter: GetterProtocol, is_change_point: bool = True, is_set_pending=True
    ):
        ...

    def add_cleanup(self, fn: Callable[[], None]):
        ...


class IScope(Protocol):
    def add_effect(self, effect: Effect):
        ...

    def dispose(self):
        ...
