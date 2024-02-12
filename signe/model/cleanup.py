from signe.utils import get_current_executor
from typing import (
    Callable,
)


def cleanup(fn: Callable[[], None]):
    current_caller = get_current_executor().get_running_caller()
    if current_caller:
        current_caller.add_cleanup(fn)
