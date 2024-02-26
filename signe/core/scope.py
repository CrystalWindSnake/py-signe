from __future__ import annotations
from typing import TYPE_CHECKING, Callable, List, Optional, TypeVar, Union

from weakref import WeakSet
import warnings

if TYPE_CHECKING:  # pragma: no cover
    from .protocols import DisposableProtocol


_T = TypeVar("_T")

_ACTIVE_SCOPE: Optional[Scope] = None


class Scope:
    def __init__(self, detached=False) -> None:
        self._active = True
        self._detached = detached
        self._disposables: WeakSet[DisposableProtocol] = WeakSet()
        self._cleanups: List[Callable[[], None]] = []
        self._parent: Optional[Scope] = None
        self._scopes: List[Scope] = []

        # child scope's index in parent's `self._scopes`
        self._index = -1

        self._parent = _ACTIVE_SCOPE
        if not detached and _ACTIVE_SCOPE:
            _ACTIVE_SCOPE._scopes.append(self)
            self._index = len(_ACTIVE_SCOPE._scopes)

    @property
    def active(self):
        return self._active

    def run(self, fn: Callable[[], _T]) -> Union[_T, None]:
        global _ACTIVE_SCOPE

        if self.active:
            current_scope = _ACTIVE_SCOPE
            try:
                _ACTIVE_SCOPE = self
                return fn()
            finally:
                _ACTIVE_SCOPE = current_scope
        else:
            warnings.warn("cannot run inactive scope.")

    def on(self):
        """
        only be called on non-detached scopes
        """
        global _ACTIVE_SCOPE
        _ACTIVE_SCOPE = self

    def off(self):
        """
        only be called on non-detached scopes
        """
        global _ACTIVE_SCOPE
        _ACTIVE_SCOPE = self._parent

    def add_disposable(self, disposable: DisposableProtocol):
        self._disposables.add(disposable)

    def dispose(self, from_parent=False):
        if self._active:
            for effect in self._disposables:
                effect.dispose()

            for cleanup in self._cleanups:
                cleanup()

            for child_scope in self._scopes:
                child_scope.dispose(True)

            if (
                (not self._detached)
                and self._parent
                and (not from_parent)
                and self._parent._scopes
            ):
                last = self._parent._scopes.pop()
                if last is not self:
                    # swap position with the last element
                    self._parent._scopes[self._index] = last
                    last._index = self._index

            self._disposables.clear()
            self._parent = None
            self._active = False


def scope(detached=False):
    return Scope(detached)


def mark_with_scope(effect: DisposableProtocol, scope: Optional[Scope] = None):
    scope = scope or _ACTIVE_SCOPE
    if scope:
        scope.add_disposable(effect)


def get_current_scope():
    return _ACTIVE_SCOPE


def on_scope_dispose(callback: Callable[[], None]):
    if _ACTIVE_SCOPE:
        _ACTIVE_SCOPE._cleanups.append(callback)
    else:
        warnings.warn("There are no active scopes.")


# class GlobalScopeManager:
#     def __init__(self) -> None:
#         self._stack: List[Scope] = []

#     def _get_last_scope(self):
#         idx = len(self._stack) - 1
#         if idx < 0:
#             return None

#         return self._stack[idx]

#     def new_scope(self):
#         s = Scope()
#         self._stack.append(s)
#         return s

#     def dispose_scope(self):
#         s = self._get_last_scope()
#         if s:
#             s.dispose()
#             self._stack.pop()

#     def mark_effect_with_scope(
#         self, scope: Optional[Scope], effect: DisposableProtocol
#     ):
#         s = scope
#         if s:
#             s.add_disposable(effect)

#         return effect

#     def mark_effect(self, effect: DisposableProtocol):
#         return self.mark_effect_with_scope(self._get_last_scope(), effect)


# _GLOBAL_SCOPE_MANAGER = GlobalScopeManager()


# @contextmanager
# def scope():
#     scope = _GLOBAL_SCOPE_MANAGER.new_scope()
#     yield scope
#     _GLOBAL_SCOPE_MANAGER.dispose_scope()
