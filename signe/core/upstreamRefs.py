from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    Set,
    Union,
    overload,
)


if TYPE_CHECKING:
    from .signal import Signal
    from .computed import Computed


class UpstreamRefs:
    def __init__(self) -> None:
        self._signals: Set[Signal] = set()
        self._computeds: Set[Computed] = set()

    @overload
    def add(self, obj: Signal):
        ...

    @overload
    def add(self, obj: Computed):
        ...

    def add(self, obj: Union[Signal, Computed]):
        if isinstance(obj, Signal):
            self._signals.add(obj)
        elif isinstance(obj, Computed):
            self._computeds.add(obj)
        else:
            pass
