from __future__ import annotations
from typing import Callable, Iterable, Optional, Protocol, TypeVar, TYPE_CHECKING, Union

from signe.core.collections import Stack
from .consts import EffectState

if TYPE_CHECKING:
    from .effect import Effect
    from .runtime import ExecutionScheduler

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

    @property
    def state(self) -> EffectState:
        ...

    def update(self) -> _T:
        ...

    @property
    def is_pending(self) -> bool:
        ...

    def update_state(self, state: EffectState):
        ...

    def add_upstream_ref(self, getter: GetterProtocol):
        ...

    def update_pending(self, is_change_point: bool = True, is_set_pending=True):
        ...

    def add_cleanup(self, fn: Callable[[], None]):
        ...


class IScope(Protocol):
    def add_effect(self, effect: Effect):
        ...

    def dispose(self):
        ...


class ExecutorProtocol(Protocol):
    execution_scheduler_stack: Stack[ExecutionScheduler]

    def mark_running_caller(self, caller: CallerProtocol):
        ...

    def reset_running_caller(self, caller: CallerProtocol):
        ...

    def get_running_caller(self) -> Optional[CallerProtocol]:
        ...

    def get_current_scheduler(self) -> ExecutionScheduler:
        ...
