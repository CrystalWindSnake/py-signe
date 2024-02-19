from __future__ import annotations
from contextlib import contextmanager
from typing import (
    TYPE_CHECKING,
    List,
    Optional,
)

from signe.core.protocols import IScope
from weakref import WeakSet

if TYPE_CHECKING:
    from .protocols import DisposableProtocol


class Scope(IScope):
    def __init__(self) -> None:
        self._disposables: WeakSet[DisposableProtocol] = WeakSet()

    def add_disposable(self, disposable: DisposableProtocol):
        self._disposables.add(disposable)

    def dispose(self):
        for effect in self._disposables:
            effect.dispose()

        self._disposables.clear()


class GlobalScopeManager:
    def __init__(self) -> None:
        self._stack: List[Scope] = []

    def _get_last_scope(self):
        idx = len(self._stack) - 1
        if idx < 0:
            return None

        return self._stack[idx]

    def new_scope(self):
        s = Scope()
        self._stack.append(s)
        return s

    def dispose_scope(self):
        s = self._get_last_scope()
        if s:
            s.dispose()
            self._stack.pop()

    def mark_effect_with_scope(
        self, scope: Optional[Scope], effect: DisposableProtocol
    ):
        s = scope
        if s:
            s.add_disposable(effect)

        return effect

    def mark_effect(self, effect: DisposableProtocol):
        return self.mark_effect_with_scope(self._get_last_scope(), effect)


_GLOBAL_SCOPE_MANAGER = GlobalScopeManager()


@contextmanager
def scope():
    scope = _GLOBAL_SCOPE_MANAGER.new_scope()
    yield scope
    _GLOBAL_SCOPE_MANAGER.dispose_scope()
