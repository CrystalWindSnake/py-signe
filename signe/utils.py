from signe.core.runtime import Executor, BatchExecutionScheduler
from signe.core.signal import Signal, SignalOption, TSignalOptionInitComp
from signe.core.effect import Effect
from signe.core.scope import Scope, IScope
from contextlib import contextmanager

from typing import (
    List,
    TypeVar,
    Callable,
    Union,
    Sequence,
    overload,
    Optional,
    cast,
)


T = TypeVar("T")

exec = Executor()

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

    def mark_effect(self, effect: Effect):
        s = self._get_last_scope()
        if s:
            s.add_effect(effect)

        return effect


_GLOBAL_SCOPE_MANAGER = GlobalScopeManager()


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
    s = Signal(exec, value, SignalOption(comp), debug_name)

    return s.getValue, s.setValue


_TEffect_Fn = Callable[[Callable[..., T]], Effect[T]]


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
) -> Effect[None]:
    ...


def effect(
    fn: Optional[Callable[..., None]] = None,
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[IScope] = None,
) -> Union[_TEffect_Fn[None], Effect[None]]:
    kws = {
        "priority_level": priority_level,
        "debug_trigger": debug_trigger,
        "debug_name": debug_name,
    }

    if fn:
        res = Effect(exec, fn, **kws)
        if scope:
            scope.add_effect(res)
        _GLOBAL_SCOPE_MANAGER.mark_effect(res)
        return res
    else:

        def wrap(fn: Callable[..., None]):
            return effect(fn, **kws, scope=scope)

        return wrap


@overload
def computed(
    fn: None = ...,
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[IScope] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    ...


@overload
def computed(
    fn: Callable[..., T],
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[IScope] = None,
) -> Callable[..., T]:
    ...


def computed(
    fn: Optional[Callable[[], T]] = None,
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[IScope] = None,
) -> Union[Callable[[Callable[..., T]], Callable[..., T]], Callable[..., T]]:
    kws = {
        "priority_level": priority_level,
        "debug_trigger": debug_trigger,
        "debug_name": debug_name,
    }

    if fn:
        current_effect = exec.effect_running_stack.get_current()

        def first():
            nonlocal real_fn, current_effect
            effect = Effect(exec, fn, **kws, capture_parent_effect=False)

            if scope:
                scope.add_effect(effect)
            _GLOBAL_SCOPE_MANAGER.mark_effect(effect)

            if current_effect is not None:
                current_effect._add_sub_effect(effect)

            del current_effect

            real_fn = effect
            return effect.getValue()

        real_fn = first

        def wrap():
            return real_fn()

        return wrap

    else:

        def wrap_cp(fn: Callable[[], T]):
            return computed(fn, **kws, scope=scope)

        return wrap_cp


def batch(fn: Callable[[], None]):
    if isinstance(exec.current_execution_scheduler, BatchExecutionScheduler):
        fn()
        return

    batch_exec = BatchExecutionScheduler()

    try:
        exec.execution_scheduler_stack.set_current(batch_exec)
        fn()
        batch_exec.run_batch()
    finally:
        exec.execution_scheduler_stack.reset_current()


def cleanup(fn: Callable[[], None]):
    current_effect = exec.effect_running_stack.get_current()
    if current_effect:
        current_effect.add_cleanup_callback(fn)


def _getter_calls(fns: Sequence[TGetter[T]]):
    for fn in fns:
        fn()


@overload
def on(
    getter: Union[TGetter[T], Sequence[TGetter[T]]], fn: Callable[..., None]
) -> Effect[None]:
    ...


@overload
def on(
    getter: Union[TGetter[T], Sequence[TGetter[T]]]
) -> Callable[[Callable], Effect[None]]:
    ...


def on(
    getter: Union[TGetter[T], Sequence[TGetter[T]]],
    fn: Optional[Callable[..., None]] = None,
):
    if fn is None:
        return cast(Callable[[Callable], Effect[None]], _on(getter))

    return _on(getter)(fn)


# immediate
def _on(
    getter: Union[TGetter[T], Sequence[TGetter[T]]],
):
    getter_call = getter
    if isinstance(getter, Sequence):
        getter_call = lambda: _getter_calls(getter)

    def warp(fn: Callable[..., None]):
        def _on():
            getter_call()  # type: ignore

            with pause_capture():
                value = fn()
            return value

        return effect(_on)

    return warp


class pause_capture:
    def __init__(self) -> None:
        self.__cur = None

    def __enter__(self):
        if len(exec.effect_running_stack):
            self.__cur = exec.effect_running_stack.reset_current()

    def __exit__(self, *_):
        if self.__cur:
            exec.effect_running_stack.set_current(self.__cur)

        self.__cur = None
