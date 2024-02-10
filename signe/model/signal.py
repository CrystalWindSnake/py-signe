from signe.core import Signal
from signe.core.signal import SignalOption, TSignalOptionInitComp
from signe.utils import get_current_executor
from typing import (
    TypeVar,
    Optional,
)


T = TypeVar("T")


def signal(
    value: T,
    comp: TSignalOptionInitComp[T] = None,
    debug_name: Optional[str] = None,
):
    return Signal(get_current_executor(), value, SignalOption(comp), debug_name)
