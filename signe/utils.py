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


def createSignal(value: T, comp: TSignalOptionInitComp[T] = None):
    s = Signal(exec, value, SignalOption(comp))

    return s.getValue, s.setValue


def effect(fn: Callable[[], None]):
    return Effect(exec, fn)


class computed(Generic[T]):
    def __init__(self, fn: Callable[[], T]) -> None:
        self.fn = fn

        def getter():
            effect = Effect(exec, fn)
            self.getter = effect
            return effect.getValue()

        self.getter = getter

    def __call__(self, *args: Any, **kwds: Any) -> T:
        return self.getter()  # type: ignore


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
