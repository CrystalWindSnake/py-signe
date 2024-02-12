from typing import TypeVar, Union
from signe.core.computed import Computed

from signe.core.signal import Signal

_T = TypeVar("_T")

TSignal = Union[Signal[_T], Computed[_T]]
TMaybeSignal = Union[_T, Signal[_T], Computed[_T]]
