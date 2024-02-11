from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    List,
)

from signe.core.protocols import IScope
from weakref import WeakSet

if TYPE_CHECKING:
    from .effect import Effect


class Scope(IScope):
    def __init__(self) -> None:
        self._effects: WeakSet[Effect] = WeakSet()

    def add_effect(self, effect: Effect):
        self._effects.add(effect)

    def dispose(self):
        for effect in self._effects:
            effect.dispose()

        self._effects.clear()
