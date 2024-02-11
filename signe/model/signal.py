from signe.core import Signal
from signe.core.signal import SignalOption, TSignalOptionInitComp
from signe.model.protocols import SignalProtocol
from signe.utils import get_current_executor
from typing import TypeVar, Optional, Protocol, cast

T = TypeVar("T")


def signal(
    value: T,
    comp: TSignalOptionInitComp[T] = None,
    debug_name: Optional[str] = None,
):
    signal = Signal(get_current_executor(), value, SignalOption(comp), debug_name)
    return cast(SignalProtocol[T], signal)
