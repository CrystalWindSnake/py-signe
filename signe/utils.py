from signe.core.runtime import Executor, BatchExecutionScheduler
from signe.core.signal import Signal, SignalOption, TSignalOptionInitComp
from signe.core.effect import Effect

from typing import (
    Any,
    TypeVar,
    Callable,
    Generic,
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
) -> _TEffect_Fn[None]:
    ...


@overload
def effect(
    fn: Callable[..., None],
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
) -> Effect[None]:
    ...


def effect(
    fn: Optional[Callable[..., None]] = None,
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
) -> Union[_TEffect_Fn[None], Effect[None]]:
    kws = {
        "priority_level": priority_level,
        "debug_trigger": debug_trigger,
        "debug_name": debug_name,
    }

    if fn:
        return Effect(exec, fn, **kws)
    else:

        def wrap(fn: Callable[..., None]):
            return Effect(exec, fn, **kws)

        return wrap


@overload
def computed(
    fn: None = ...,
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    ...


@overload
def computed(
    fn: Callable[..., T],
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
) -> Callable[..., T]:
    ...


def computed(
    fn: Optional[Callable[[], T]] = None,
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
) -> Union[Callable[[Callable[..., T]], Callable[..., T]], Callable[..., T]]:
    kws = {
        "priority_level": priority_level,
        "debug_trigger": debug_trigger,
        "debug_name": debug_name,
    }

    if fn:

        def first():
            nonlocal real_fn
            effect = Effect(exec, fn, **kws)
            real_fn = effect
            return effect.getValue()

        real_fn = first

        def wrap():
            return real_fn()

        return wrap

    else:

        def wrap_cp(fn: Callable[[], T]):
            return computed(fn, **kws)

        return wrap_cp


# class computed(Generic[T]):
#     def __init__(
#         self,
#         fn: Callable[[], T],
#         debug_trigger: Optional[Callable] = None,
#         priority_level=1,
#     ) -> None:
#         self.fn = fn

#         def getter():
#             effect = Effect(exec, fn, debug_trigger, priority_level)
#             self.getter = effect
#             return effect.getValue()

#         self.getter = getter

#     @staticmethod
#     def with_opts(priority_level=1, debug_trigger: Optional[Callable] = None):
#         def wrap(
#             fn: Callable[[], T],
#         ):
#             return computed(fn, debug_trigger, priority_level)

#         return wrap

#     def __call__(self, *args: Any, **kwds: Any) -> T:
#         return self.getter()  # type: ignore


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
