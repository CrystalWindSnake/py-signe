from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    List,
    NewType,
    TypeVar,
    Generic,
    Callable,
    Set,
    Union,
    Optional,
    cast,
)


if TYPE_CHECKING:
    from .effect import Effect


class Scope:
    def __init__(self) -> None:
        self._effects: List[Effect] = []

    def add_effect(self, effect: Effect):
        self._effects.append(effect)

    def dispose(self):
        for effect in self._effects:
            effect.cleanup_deps()

        self._effects.clear()
