from signe.core.runtime import Executor, BatchExecutionScheduler, ExecutionScheduler
from signe.core.signal import Signal, SignalOption, TSignalOptionInitComp
from signe.core.effect import Effect
from signe.core.computed import Computed
from signe.core.scope import Scope, IScope
from contextlib import contextmanager
from functools import lru_cache
from typing import (
    Any,
    Dict,
    List,
    Tuple,
    TypeVar,
    Callable,
    Union,
    Sequence,
    overload,
    Optional,
    cast,
)


T = TypeVar("T")


TGetter = Callable[[], T]

TSetterParme = Union[T, Callable[[T], T]]
TSetter = Callable[[TSetterParme[T]], T]


class GlobalScopeManager:
    def __init__(self) -> None:
        self._stack: List[Scope] = []

    def _get_last_scope(self):
        idx = len(self._stack) - 1
        if idx < 0:
            return None

        return self._stack[idx]

    def new_scope(self):
        s = Scope()
        self._stack.append(s)
        return s

    def dispose_scope(self):
        s = self._get_last_scope()
        if s:
            s.dispose()
            self._stack.pop()

    def mark_effect_with_scope(self, scope: Optional[Scope], effect: Effect):
        s = scope
        if s:
            s.add_effect(effect)

        return effect

    def mark_effect(self, effect: Effect):
        return self.mark_effect_with_scope(self._get_last_scope(), effect)


_GLOBAL_SCOPE_MANAGER = GlobalScopeManager()


_executor_builder = None


def set_executor(executor: Executor):
    global _executor_builder
    _executor_builder = executor


@lru_cache(maxsize=1)
def get_current_executor():
    return _executor_builder or Executor()


@contextmanager
def scope():
    _GLOBAL_SCOPE_MANAGER.new_scope()
    yield
    _GLOBAL_SCOPE_MANAGER.dispose_scope()


def createSignal(
    value: T,
    comp: TSignalOptionInitComp[T] = None,
    debug_name: Optional[str] = None,
):
    s = Signal(get_current_executor(), value, SignalOption(comp), debug_name)

    def getValue():
        return s.value

    def setValue(new: T):
        s.value = new

    return cast(Tuple[Callable[[], T], Callable[[T], None]], (getValue, setValue))


_TEffect_Fn = Callable[[Callable[..., T]], Effect]


@overload
def effect(
    fn: None = ...,
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[IScope] = None,
) -> _TEffect_Fn[None]:
    ...


@overload
def effect(
    fn: Callable[..., None],
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[IScope] = None,
) -> Effect:
    ...


def effect(
    fn: Optional[Callable[..., None]] = None,
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[IScope] = None,
) -> Union[_TEffect_Fn[None], Effect]:
    kws = {
        "priority_level": priority_level,
        "debug_trigger": debug_trigger,
        "debug_name": debug_name,
    }

    if fn:
        res = Effect(get_current_executor(), fn, **kws)
        if scope:
            scope.add_effect(res)
        else:
            _GLOBAL_SCOPE_MANAGER.mark_effect(res)
        return res
    else:

        def wrap(fn: Callable[..., None]):
            return effect(fn, **kws, scope=scope)

        return wrap


_T_computed = Callable[[], T]
_T_computed_setter = Callable[[Callable[[], T]], _T_computed]


@overload
def computed(
    fn: None = ...,
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[IScope] = None,
) -> _T_computed_setter:
    ...


@overload
def computed(
    fn: Callable[[], T],
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[IScope] = None,
) -> _T_computed[T]:
    ...


def computed(
    fn: Optional[Callable[[], T]] = None,
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[IScope] = None,
) -> Union[_T_computed_setter, _T_computed[T]]:
    kws = {
        "priority_level": priority_level,
        "debug_trigger": debug_trigger,
        "debug_name": debug_name,
    }

    if fn:
        cp = Computed(get_current_executor(), fn, **kws)

        def getter():
            return cp.value

        return getter
    else:

        def wrap_cp(fn: Callable[[], T]):
            return computed(fn, **kws, scope=scope)

        return wrap_cp


# def computed(
#     fn: Optional[Callable[[], T]] = None,
#     *,
#     priority_level=1,
#     debug_trigger: Optional[Callable] = None,
#     debug_name: Optional[str] = None,
#     scope: Optional[IScope] = None,
# ) -> Union[Callable[[Callable[..., T]], Callable[..., T]], Callable[..., T]]:
#     kws = {
#         "priority_level": priority_level,
#         "debug_trigger": debug_trigger,
#         "debug_name": debug_name,
#     }

#     if fn:
#         current_effect = get_current_executor().effect_running_stack.get_current()

#         def mark_scope(
#             effect: Effect,
#             global_scope=_GLOBAL_SCOPE_MANAGER._get_last_scope(),
#         ):
#             if scope:
#                 scope.add_effect(effect)
#                 return

#             if global_scope:
#                 _GLOBAL_SCOPE_MANAGER.mark_effect(effect)

#         def mark_sub_effect(
#             effect: Effect,
#             current_effect=current_effect,
#         ):
#             if current_effect is not None:
#                 current_effect._add_sub_effect(effect)

#             del current_effect

#         effect = None

#         def wrap():
#             nonlocal effect
#             if effect is None:
#                 effect = Effect(
#                     get_current_executor(), fn, **kws, capture_parent_effect=False
#                 )
#                 mark_scope(effect)
#                 mark_sub_effect(effect)

#             return effect()

#         return wrap

#     else:

#         def wrap_cp(fn: Callable[[], T]):
#             return computed(fn, **kws, scope=scope)

#         return wrap_cp


def batch(fn: Callable[[], None]):
    if isinstance(
        get_current_executor().get_current_scheduler(), BatchExecutionScheduler
    ):
        fn()
        return

    batch_exec = BatchExecutionScheduler()

    try:
        get_current_executor().execution_scheduler_stack.set_current(batch_exec)
        fn()
        batch_exec.run_batch()
    finally:
        get_current_executor().execution_scheduler_stack.reset_current()


def cleanup(fn: Callable[[], None]):
    current_caller = get_current_executor().get_running_caller()
    if current_caller:
        current_caller.add_cleanup(fn)


def _getter_calls(fns: Sequence[TGetter[T]]):
    return tuple(fn() for fn in fns)


@overload
def on(
    getter: Union[TGetter[T], Sequence[TGetter[T]]],
    fn: Callable[..., None],
    onchanges=False,
    effect_kws: Optional[Dict[str, Any]] = None,
) -> Effect:
    ...


@overload
def on(
    getter: Union[TGetter[T], Sequence[TGetter[T]]],
    fn: Optional[Callable[..., None]] = None,
    onchanges=False,
) -> Callable[[Callable], Effect]:
    ...


def on(
    getter: Union[TGetter[T], Sequence[TGetter[T]]],
    fn: Optional[Callable[..., None]] = None,
    onchanges=False,
    effect_kws: Optional[Dict[str, Any]] = None,
):
    call_kws = {"onchanges": onchanges, "effect_kws": effect_kws}

    if fn is None:
        return cast(
            Callable[[Callable], Effect],
            _on(getter, **call_kws),
        )

    return _on(getter, **call_kws)(fn)


import inspect
from dataclasses import dataclass


@dataclass(frozen=True)
class WatchedState:
    current: Any
    previous: Any


def _get_func_args_count(fn):
    return len(inspect.getfullargspec(fn).args)


# immediate
def _on(
    getter: Union[TGetter[T], Sequence[TGetter[T]]],
    onchanges=False,
    effect_kws: Optional[Dict[str, Any]] = None,
):
    getters = getter
    if not isinstance(getter, Sequence):
        getters = [getter]

    def getter_calls():
        return _getter_calls(getters)  # type: ignore

    def warp(fn: Callable[..., None]):
        args_count = _get_func_args_count(fn)
        prev_values = None

        def _on():
            nonlocal onchanges, prev_values
            current_values = getter_calls()  # type: ignore

            states = (
                WatchedState(cur, prev)
                for cur, prev in zip(current_values, prev_values or current_values)
            )

            prev_values = current_values

            if onchanges:
                onchanges = False
                return

            with pause_capture():
                if args_count == 0:
                    fn()
                else:
                    fn(*states)

        return effect(_on, **effect_kws or {})

    return warp


class pause_capture:
    def __init__(self) -> None:
        self._current_scheduler = None

    def __enter__(self):
        if len(get_current_executor().execution_scheduler_stack):
            self._current_scheduler = (
                get_current_executor().execution_scheduler_stack.reset_current()
            )

    def __exit__(self, *_):
        if self._current_scheduler:
            get_current_executor().execution_scheduler_stack.set_current(
                self._current_scheduler
            )

        self._current_scheduler = None
