from __future__ import annotations
from typing import Callable, Generic, Optional, Protocol, TypeVar, TYPE_CHECKING


if TYPE_CHECKING:
    from signe.core.collections import Stack
    from signe.core.deps import Dep
    from .consts import EffectState
    from .effect import Effect
    from .runtime import ExecutionScheduler

_T = TypeVar("_T")


class GetterProtocol(Protocol[_T]):
    @property
    def id(self) -> str:
        ...

    @property
    def is_signal(self) -> bool:
        ...

    @property
    def value(self) -> _T:
        ...

    def confirm_state(self):
        ...


class CallerProtocol(Protocol[_T]):
    auto_collecting_dep: bool

    @property
    def id(self) -> str:
        ...

    def trigger(self, state: EffectState):
        ...

    @property
    def is_effect(self) -> bool:
        ...

    @property
    def state(self) -> EffectState:
        ...

    def update(self) -> _T:
        ...

    def add_upstream_ref(self, dep: Dep):
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

    def pause_track(self):
        ...

    def reset_track(self):
        ...

    def should_track(self) -> bool:
        ...


class SignalResultProtocol(Protocol[_T]):
    @property
    def value(self) -> _T:
        ...

    @value.setter
    def value(self, value: _T):
        ...


class ComputedResultProtocol(Generic[_T], Protocol):
    @property
    def value(self) -> _T:
        ...

    def __call__(
        self,
    ) -> _T:
        ...
