from dataclasses import dataclass
import inspect
from signe.core import Effect, effect
from signe.core.context import get_executor
from signe.core.reactive import is_reactive, track_all
from signe.core.scope import _GLOBAL_SCOPE_MANAGER, IScope
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

T = TypeVar("T")


class OnGetterModel(Generic[T]):
    def __init__(self, ref: Union[TSignal, Callable[[], T]], deep=False) -> None:
        self._is_signal = is_signal(ref)

        self._ref = ref

        # with track
        if self._is_signal:

            def getter(track=True):
                value = self._ref.value
                if is_reactive(value) and track:
                    track_all(value, deep)

                return value

            self._fn = getter
        else:

            def getter_reactive_fn(track=True):
                obj = cast(Callable, ref)()
                if track:
                    track_all(obj, deep)
                return obj

            self._fn = getter_reactive_fn

    def get_value_with_track(self):
        return self._fn()

    def get_value_without_track(self):
        return self._fn(track=False)


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

    getters: List[OnGetterModel] = []
    if isinstance(getter, Sequence):
        getters = [OnGetterModel(g, deep) for g in getter]  # type: ignore
    else:
        getters = [OnGetterModel(getter, deep)]  # type: ignore

    # targets = getters

    def getter_calls():
        return [g.get_value_without_track() for g in getters]

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
    executor = get_executor()

    # def trigger_fn(effect: Effect):
    #     executor.get_current_scheduler().mark_update(effect)

    @effect(immediate=not onchanges, **(effect_kws or {}), scope=scope)
    def _():
        for getter in getters:
            getter.get_value_with_track()

        executor.pause_track()
        fn()
        executor.reset_track()


# def on(
#     getter: Union[TGetter, Sequence[TGetter]],
#     fn: Optional[Callable[..., None]] = None,
#     *,
#     onchanges=False,
#     effect_kws: Optional[Dict[str, Any]] = None,
#     deep=False,
#     scope: Optional[IScope] = None,
# ):
#     call_kws = {"onchanges": onchanges, "effect_kws": effect_kws, "deep": deep}

#     if fn is None:

#         def wrap_cp(fn: Callable[[], T]):
#             return on(getter, fn, **call_kws, scope=scope)  # type: ignore

#         return wrap_cp

#     getters: List[OnGetterModel] = []
#     if isinstance(getter, Sequence):
#         getters = [OnGetterModel(g, deep) for g in getter]  # type: ignore
#     else:
#         getters = [OnGetterModel(getter, deep)]  # type: ignore

#     targets = getters

#     def getter_calls():
#         return [g.get_value_without_track() for g in getters]

#     args_count = _get_func_args_count(fn)
#     prev_values = getter_calls()

#     def real_fn():
#         nonlocal prev_values

#         current_values = getter_calls()  # type: ignore

#         states = (
#             WatchedState(cur, prev)
#             for cur, prev in zip(current_values, prev_values or current_values)
#         )

#         prev_values = current_values
#         if args_count == 0:
#             fn()
#         else:
#             fn(*states)

#     scope = scope
#     executor = get_executor()

#     def trigger_fn(effect: Effect):
#         executor.get_current_scheduler().mark_update(effect)

#     effect = Effect(
#         fn=real_fn,
#         trigger_fn=trigger_fn,
#         immediate=not onchanges,
#         on=targets,  # type: ignore
#         **(effect_kws or {}),
#         scope=scope,
#     )

#     return effect
