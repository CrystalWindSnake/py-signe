from dataclasses import dataclass
import inspect
from signe.core import Effect
from signe.core.context import get_executor
from signe.core.reactive import is_reactive, track_all
from signe.core.scope import IScope
from typing import (
    Any,
    Dict,
    List,
    Sequence,
    TypeVar,
    Callable,
    Union,
    overload,
    Optional,
    Generic,
)

from .types import TGetter, TGetterSignal
from .signal import is_signal

T = TypeVar("T")


class GetterModel(Generic[T]):
    def __init__(self, fn: Callable[[], T], deep=False) -> None:
        assert isinstance(fn, Callable)
        self._fn = fn
        self._deep = deep
        self.__track = False

    @property
    def value(self):
        obj = self._fn()
        assert is_reactive(obj)

        if self.__track:
            track_all(obj, self._deep)

        return obj

    def enable_track(self):
        self.__track = True

    def disable_track(self):
        self.__track = False


@dataclass(frozen=True)
class WatchedState:
    current: Any
    previous: Any


def _get_func_args_count(fn):
    return len(inspect.getfullargspec(fn).args)


@overload
def on(
    getter: Union[TGetter, Sequence[TGetter]],
    fn: Optional[Callable[..., None]] = None,
    *,
    onchanges=False,
    effect_kws: Optional[Dict[str, Any]] = None,
    deep=False,
    scope: Optional[IScope] = None,
):
    ...


@overload
def on(
    getter: Union[TGetter, Sequence[TGetter]],
    fn: Optional[Callable[..., None]] = None,
    *,
    onchanges=False,
    deep=False,
    scope: Optional[IScope] = None,
):
    ...


def on(
    getter: Union[TGetter, Sequence[TGetter]],
    fn: Optional[Callable[..., None]] = None,
    *,
    onchanges=False,
    effect_kws: Optional[Dict[str, Any]] = None,
    deep=False,
    scope: Optional[IScope] = None,
):
    call_kws = {"onchanges": onchanges, "effect_kws": effect_kws, "deep": deep}

    if fn is None:

        def wrap_cp(fn: Callable[[], T]):
            return on(getter, fn, **call_kws, scope=scope)  # type: ignore

        return wrap_cp

    getters: List[TGetterSignal] = []
    if isinstance(getter, Sequence):
        getters = [g if is_signal(g) else GetterModel(g, deep) for g in getter]  # type: ignore
    else:
        getters = [getter if is_signal(getter) else GetterModel(getter, deep)]  # type: ignore

    targets = getters

    def getter_calls():
        return [g.value for g in getters]

    args_count = _get_func_args_count(fn)
    prev_values = getter_calls()

    def real_fn():
        nonlocal prev_values

        current_values = getter_calls()  # type: ignore

        states = (
            WatchedState(cur, prev)
            for cur, prev in zip(current_values, prev_values or current_values)
        )

        prev_values = current_values
        if args_count == 0:
            fn()
        else:
            fn(*states)

    scope = scope
    executor = get_executor()

    def trigger_fn(effect: Effect):
        executor.get_current_scheduler().mark_update(effect)

    effect = Effect(
        fn=real_fn,
        trigger_fn=trigger_fn,
        immediate=not onchanges,
        on=targets,  # type: ignore
        **(effect_kws or {}),
        scope=scope,
    )

    return effect
