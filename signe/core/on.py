from dataclasses import dataclass
import inspect
from signe.core import Effect
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
)

from .protocols import SignalResultProtocol, ComputedResultProtocol

T = TypeVar("T")

_T_Ref = Union[SignalResultProtocol, ComputedResultProtocol]


@dataclass(frozen=True)
class WatchedState:
    current: Any
    previous: Any


def _get_func_args_count(fn):
    return len(inspect.getfullargspec(fn).args)


@overload
def on(
    getter: Union[_T_Ref, Sequence[_T_Ref]],
    fn: Optional[Callable[..., None]] = None,
    *,
    onchanges=False,
    effect_kws: Optional[Dict[str, Any]] = None,
    scope: Optional[IScope] = None,
):
    ...


@overload
def on(
    getter: Union[_T_Ref, Sequence[_T_Ref]],
    fn: Optional[Callable[..., None]] = None,
    *,
    onchanges=False,
    scope: Optional[IScope] = None,
):
    ...


def on(
    getter: Union[_T_Ref, Sequence[_T_Ref]],
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

    getters: List[_T_Ref] = []
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

    scope = scope
    return Effect(
        fn=real_fn,
        immediate=not onchanges,
        on=targets,  # type: ignore
        **(effect_kws or {}),
        scope=scope,
    )
