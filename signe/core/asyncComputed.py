from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    Any,
    Coroutine,
    Sequence,
    TypeVar,
    Callable,
    Optional,
    Generic,
    Union,
    cast,
)
from signe.core.signal import signal
from signe.core.context import get_default_scheduler
from signe.core.on import on

from signe.core.protocols import ComputedResultProtocol

from .types import TGetter, TSignal
from .scope import Scope, ScopeSuite, _DEFAULT_SCOPE_SUITE

if TYPE_CHECKING:  # pragma: no cover
    from .runtime import ExecutionScheduler

_T = TypeVar("_T")


_T_async_fn = Callable[[], Coroutine[Any, Any, _T]]
_T_wrap_fn = Callable[[_T_async_fn], ComputedResultProtocol[_T]]


def async_computed(
    source: Union[TGetter, Sequence[TGetter]],
    *,
    init: Optional[_T] = None,
    evaluating: Optional[TSignal[bool]] = None,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[Union[Scope, ScopeSuite]] = None,
    scheduler: Optional[ExecutionScheduler] = None,
) -> _T_wrap_fn[_T]:
    kws = {
        "init": init,
        "evaluating": evaluating,
        "debug_trigger": debug_trigger,
        "debug_name": debug_name,
        "scheduler": scheduler or get_default_scheduler(),
    }

    def wrap_cp(fn: _T_async_fn):
        current = signal(init, is_shallow=True)
        evaluating_ref = evaluating or signal(False, is_shallow=True)
        evaluating_ref.value = False

        effect_kws = {
            "debug_name": kws.pop("debug_name"),
            "debug_trigger": kws.pop("debug_trigger"),
        }

        @on(
            source,
            onchanges=True,
            effect_kws=effect_kws,
            scheduler=kws.get("scheduler"),
            scope=scope or _DEFAULT_SCOPE_SUITE,
        )
        async def _():
            evaluating_ref.value = True

            try:
                current.value = await fn()
            finally:
                evaluating_ref.value = False

        return cast(ComputedResultProtocol[_T], AsyncComputedResult(current, fn))

    return wrap_cp


class AsyncComputedResult(Generic[_T]):
    __slot__ = ("_result", "_fn")

    def __init__(self, result: TSignal[_T], fn: _T_async_fn[_T]) -> None:
        self._result = result
        self._fn = fn

    @property
    def value(self):
        return self._result.value

    def __call__(self) -> Any:
        return self._fn()
