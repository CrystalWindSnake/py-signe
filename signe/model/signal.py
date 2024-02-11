from signe.core import Signal
from signe.core.signal import SignalOption, TSignalOptionInitComp
from signe.utils import get_current_executor
from typing import TypeVar, Optional, Protocol, cast

T = TypeVar("T")


class SignalProtocol(Protocol[T]):
    @property
    def value(self) -> T:
        ...

    @value.setter
    def value(self, value: T):
        ...


def signal(
    value: T,
    comp: TSignalOptionInitComp[T] = None,
    debug_name: Optional[str] = None,
):
    signal = Signal(get_current_executor(), value, SignalOption(comp), debug_name)
    return cast(SignalProtocol[T], signal)
