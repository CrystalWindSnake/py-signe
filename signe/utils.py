from signe.core.runtime import Executor, BatchExecutionScheduler
from signe.core.signal import Signal, SignalOption, TSignalOptionInitComp
from signe.core.effect import Effect

from typing import Any, TypeVar, Callable, Generic, Union


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
