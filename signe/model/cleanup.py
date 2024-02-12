from typing import (
    Callable,
)

from signe.core.context import get_executor


def cleanup(fn: Callable[[], None]):
    current_caller = get_executor().get_running_caller()
    if current_caller:
        current_caller.add_cleanup(fn)
