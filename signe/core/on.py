from dataclasses import dataclass
from signe.core.context import get_default_scheduler
from signe.core.effect import Effect
from signe.core.helper import has_changed, get_func_args_count
from signe.core.reactive import is_reactive, track_all
from signe.core.scope import Scope, _DEFAULT_SCOPE_SUITE, ScopeSuite
from typing import (
    Any,
    Dict,
    List,
    Sequence,
    TypeVar,
    Callable,
    Union,
    cast,
    overload,
    Optional,
    Generic,
)

from .types import TGetter, TSignal
from .signal import is_signal

from .runtime import ExecutionScheduler


T = TypeVar("T")


class OnGetterModel(Generic[T]):
    __slots__ = ("_ref", "_fn")

    def __init__(
        self,
        ref: Union[TSignal, Callable[[], T]],
        scheduler: ExecutionScheduler,
        deep=False,
    ) -> None:
        self._ref = ref

        # with track
        if is_signal(ref):

            def getter():
                value = self._ref.value
                if is_reactive(value):
                    track_all(value, scheduler, deep)
                return value

            self._fn = getter
        else:

            def getter_reactive_fn():
                obj = cast(Callable, ref)()
                track_all(obj, scheduler, deep)
                return obj

            self._fn = getter_reactive_fn

    def get_value(self):
        return self._fn()


@dataclass(frozen=True)
class WatchedState:
    __slot__ = ("current", "previous")
    current: Any
    previous: Any


@overload
def on(
    source: Union[TGetter, Sequence[TGetter]],
    fn: Optional[Callable[..., None]] = None,
    *,
    onchanges=False,
    effect_kws: Optional[Dict[str, Any]] = None,
    deep=False,
    scope: Optional[Union[Scope, ScopeSuite]] = None,
    scheduler: Optional[ExecutionScheduler] = None,
):
    ...


@overload
def on(
    source: Union[TGetter, Sequence[TGetter]],
    fn: Optional[Callable[..., None]] = None,
    *,
    onchanges=False,
    deep=False,
    scope: Optional[Union[Scope, ScopeSuite]] = None,
    scheduler: Optional[ExecutionScheduler] = None,
):
    ...


def on(
    source: Union[TGetter, Sequence[TGetter]],
    fn: Optional[Callable[..., None]] = None,
    *,
    onchanges=False,
    effect_kws: Optional[Dict[str, Any]] = None,
    deep=False,
    scope: Optional[Union[Scope, ScopeSuite]] = None,
    scheduler: Optional[ExecutionScheduler] = None,
):
    call_kws = {
        "onchanges": onchanges,
        "effect_kws": effect_kws,
        "deep": deep,
        "scheduler": scheduler or get_default_scheduler(),
    }

    if fn is None:

        def wrap_cp(fn: Callable[[], T]):
            return on(source, fn, **call_kws, scope=scope)  # type: ignore

        return wrap_cp

    getters: List[OnGetterModel] = []
    if isinstance(source, Sequence):
        getters = [OnGetterModel(g, call_kws["scheduler"], deep) for g in source]  # type: ignore
    else:
        getters = [OnGetterModel(source, call_kws["scheduler"], deep)]  # type: ignore

    def getter():
        return [g.get_value() for g in getters]

    args_count = get_func_args_count(fn)
    prev_values = [None] * len(getters)

    def scheduler_fn(effect: Effect):
        nonlocal prev_values
        if (not effect._active) or (not effect.is_need_update()):
            return

        new_values = effect.update()
        if deep or any(has_changed(n, v) for n, v in zip(new_values, prev_values)):
            states = (
                WatchedState(cur, prev)
                for cur, prev in zip(new_values, prev_values or new_values)
            )
            if args_count == 0:
                fn()
            else:
                fn(*states)

        prev_values = new_values

    effect = Effect(
        getter,
        scheduler=scheduler or get_default_scheduler(),
        scheduler_fn=scheduler_fn,
        **(effect_kws or {}),
        scope=scope or _DEFAULT_SCOPE_SUITE,
    )

    if onchanges:
        prev_values = effect.update()
    else:
        scheduler_fn(effect)
