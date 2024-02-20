from dataclasses import dataclass
import inspect
from signe.core import Effect
from signe.core.context import get_executor
from signe.core.helper import has_changed
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

            def getter():
                value = self._ref.value
                if is_reactive(value):
                    track_all(value, deep)
                return value

            self._fn = getter
        else:

            def getter_reactive_fn():
                obj = cast(Callable, ref)()
                track_all(obj, deep)
                return obj

            self._fn = getter_reactive_fn

    def get_value(self):
        return self._fn()


@dataclass(frozen=True)
class WatchedState:
    current: Any
    previous: Any


def _get_func_args_count(fn):
    return len(inspect.getfullargspec(fn).args)


@overload
def on(
    source: Union[TGetter, Sequence[TGetter]],
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
    source: Union[TGetter, Sequence[TGetter]],
    fn: Optional[Callable[..., None]] = None,
    *,
    onchanges=False,
    deep=False,
    scope: Optional[IScope] = None,
):
    ...


def on(
    source: Union[TGetter, Sequence[TGetter]],
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
            return on(source, fn, **call_kws, scope=scope)  # type: ignore

        return wrap_cp

    getters: List[OnGetterModel] = []
    if isinstance(source, Sequence):
        getters = [OnGetterModel(g, deep) for g in source]  # type: ignore
    else:
        getters = [OnGetterModel(source, deep)]  # type: ignore

    def getter():
        return [g.get_value() for g in getters]

    # targets = getters

    # def getter_calls():
    #     return [t.get_value_without_track() for t in targets]

    args_count = _get_func_args_count(fn)
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

    scope = scope or _GLOBAL_SCOPE_MANAGER._get_last_scope()

    effect = Effect(
        getter, scheduler_fn=scheduler_fn, **(effect_kws or {}), scope=scope
    )

    if onchanges:
        prev_values = effect.update()
    else:
        scheduler_fn(effect)


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

#     res = Effect(
#         fn=real_fn,
#         trigger_fn=trigger_fn,
#         immediate=not onchanges,
#         on=targets,  # type: ignore
#         **(effect_kws or {}),
#         scope=scope,
#     )

#     return effect
