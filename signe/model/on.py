from dataclasses import dataclass
import inspect
from signe.core import Effect
from signe.core.computed import Computed
from signe.core.scope import IScope
from signe.core.signal import Signal
from signe.utils import GetterProtocol, get_current_executor, _GLOBAL_SCOPE_MANAGER
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
)


T = TypeVar("T")

_T_Getter = Union[Signal, Computed]


@dataclass(frozen=True)
class WatchedState:
    current: Any
    previous: Any


def _get_func_args_count(fn):
    return len(inspect.getfullargspec(fn).args)


@overload
def on(
    getter: Union[GetterProtocol, Sequence[GetterProtocol]],
    fn: Optional[Callable[..., None]] = None,
    *,
    onchanges=False,
    effect_kws: Optional[Dict[str, Any]] = None,
    scope: Optional[IScope] = None,
):
    ...


@overload
def on(
    getter: Union[GetterProtocol, Sequence[GetterProtocol]],
    fn: Optional[Callable[..., None]] = None,
    *,
    onchanges=False,
    scope: Optional[IScope] = None,
):
    ...


def on(
    getter: Union[GetterProtocol, Sequence[GetterProtocol]],
    fn: Optional[Callable[..., None]] = None,
    *,
    onchanges=False,
    effect_kws: Optional[Dict[str, Any]] = None,
    scope: Optional[IScope] = None,
):
    call_kws = {"onchanges": onchanges, "effect_kws": effect_kws}

    if fn is None:

        def wrap_cp(fn: Callable[[], T]):
            return on(getter, fn, **call_kws, scope=scope)  # type: ignore

        return wrap_cp

    getters: List[GetterProtocol] = []
    if isinstance(getter, Sequence):
        getters = getter  # type: ignore
    else:
        getters = [getter]  # type: ignore

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

    scope = scope or _GLOBAL_SCOPE_MANAGER._get_last_scope()
    return Effect(
        executor=get_current_executor(),
        fn=real_fn,
        immediate=not onchanges,
        on=targets,  # type: ignore
        **(effect_kws or {}),
        scope=scope,
    )