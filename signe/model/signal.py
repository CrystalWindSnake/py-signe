from signe.core import Signal
from signe.core.signal import SignalOption, TSignalOptionInitComp
from signe.model.protocols import SignalProtocol
from typing import TypeVar, Optional, cast

T = TypeVar("T")


def signal(
    value: T,
    comp: TSignalOptionInitComp[T] = None,
    debug_name: Optional[str] = None,
):
    signal = Signal(value, SignalOption(comp), debug_name)
    return cast(SignalProtocol[T], signal)
