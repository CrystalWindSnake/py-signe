from __future__ import annotations
from typing import (
    Callable,
    Generic,
    Protocol,
    TypeVar,
    TYPE_CHECKING,
    runtime_checkable,
)


if TYPE_CHECKING:
    from signe.core.deps import Dep
    from .consts import EffectState

_T = TypeVar("_T")


@runtime_checkable
class OnGetterProtocol(Protocol):
    def get_value_with_track(self):
        ...

    def get_value_without_track(self):
        ...


class DisposableProtocol(Protocol):
    def dispose(self):
        ...


class GetterProtocol(Protocol[_T]):  # type: ignore
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


class CallerProtocol(Protocol[_T]):  # type: ignore
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
    def add_disposable(self, disposable: DisposableProtocol):
        ...

    def dispose(self):
        ...


class SignalResultProtocol(Protocol[_T]):
    @property
    def value(self) -> _T:
        ...

    @value.setter
    def value(self, value: _T):
        ...


class ComputedResultProtocol(Generic[_T], Protocol):  # type: ignore
    @property
    def value(self) -> _T:
        ...

    def __call__(
        self,
    ) -> _T:
        ...


@runtime_checkable
class RawableProtocol(Protocol[_T]):
    def to_raw(self) -> _T:
        ...
