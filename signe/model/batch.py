from signe.core.runtime import BatchExecutionScheduler
from signe.utils import get_current_executor
from typing import (
    Callable,
)


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
