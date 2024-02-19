from typing import TypeVar, Union
from signe.core.protocols import ComputedResultProtocol, SignalResultProtocol


_T = TypeVar("_T")

TSignal = SignalResultProtocol[_T]
TGetterSignal = Union[SignalResultProtocol[_T], ComputedResultProtocol[_T]]
TMaybeSignal = Union[_T, TGetterSignal[_T]]
