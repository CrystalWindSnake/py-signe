from signe.core.runtime import BatchExecutionScheduler
from typing import (
    Callable,
)

from signe.core.context import get_executor


def batch(fn: Callable[[], None]):
    executor = get_executor()
    scheduler = executor.get_current_scheduler()

    if isinstance(scheduler, BatchExecutionScheduler):
        fn()
        return

    batch_exec = BatchExecutionScheduler()

    try:
        executor.execution_scheduler_stack.set_current(batch_exec)
        fn()
        batch_exec.run_batch()
    finally:
        executor.execution_scheduler_stack.reset_current()
