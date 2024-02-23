from typing import (
    Callable,
    Optional,
)

from signe.core.context import get_default_scheduler

from .runtime import ExecutionScheduler


def batch(
    fn: Callable[[], None],
    scheduler: Optional[ExecutionScheduler] = None,
):
    return api_batch(fn, scheduler or get_default_scheduler())


def api_batch(
    fn: Callable[[], None],
    scheduler: ExecutionScheduler,
):
    scheduler.pause_scheduling()

    try:
        fn()
    finally:
        scheduler.reset_scheduling()
        scheduler.run()
