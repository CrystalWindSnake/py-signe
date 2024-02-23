from typing import (
    Callable,
    Optional,
)

from signe.core.context import get_default_scheduler

from .runtime import ExecutionScheduler


def cleanup(
    fn: Callable[[], None],
    scheduler: Optional[ExecutionScheduler] = None,
):
    return api_cleanup(fn, scheduler or get_default_scheduler())


def api_cleanup(
    fn: Callable[[], None],
    scheduler: ExecutionScheduler,
):
    current_caller = scheduler.get_running_caller()
    if current_caller:
        current_caller.add_cleanup(fn)
