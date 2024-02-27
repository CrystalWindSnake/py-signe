from __future__ import annotations
from typing import TYPE_CHECKING, Callable, List, Optional, TypeVar, Union

from weakref import WeakSet
import warnings

if TYPE_CHECKING:  # pragma: no cover
    from .protocols import DisposableProtocol


_T = TypeVar("_T")


class Scope:
    def __init__(self, suite: ScopeSuite, detached=False) -> None:
        self._suite = suite
        self._active = True
        self._detached = detached
        self._disposables: WeakSet[DisposableProtocol] = WeakSet()
        self._cleanups: List[Callable[[], None]] = []
        self._parent: Optional[Scope] = None
        self._scopes: List[Scope] = []

        # child scope's index in parent's `self._scopes`
        self._index = -1

        self._parent = suite._ACTIVE_SCOPE
        if not detached and suite._ACTIVE_SCOPE:
            suite._ACTIVE_SCOPE._scopes.append(self)
            self._index = len(suite._ACTIVE_SCOPE._scopes)

    @property
    def active(self):
        return self._active

    def run(self, fn: Callable[[], _T]) -> Union[_T, None]:
        if self.active:
            current_scope = self._suite._ACTIVE_SCOPE
            try:
                self._suite._ACTIVE_SCOPE = self
                return fn()
            finally:
                self._suite._ACTIVE_SCOPE = current_scope
        else:
            warnings.warn("cannot run inactive scope.")

    def on(self):
        """
        only be called on non-detached scopes
        """
        self._suite._ACTIVE_SCOPE = self

    def off(self):
        """
        only be called on non-detached scopes
        """
        self._suite._ACTIVE_SCOPE = self._parent

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

    # def mark_with_scope(self, effect: DisposableProtocol):
    #     scope = scope or self._suite._ACTIVE_SCOPE
    #     if scope:
    #         scope._add_disposable(effect)


class ScopeSuite:
    def __init__(self) -> None:
        self._ACTIVE_SCOPE: Optional[Scope] = None

    def scope(self, detached=False):
        return Scope(self, detached)

    def mark_with_scope(self, effect: DisposableProtocol):
        if self._ACTIVE_SCOPE:
            self._ACTIVE_SCOPE.add_disposable(effect)

    def get_current_scope(
        self,
    ):
        return self._ACTIVE_SCOPE

    def on_scope_dispose(self, callback: Callable[[], None]):
        if self._ACTIVE_SCOPE:
            self._ACTIVE_SCOPE._cleanups.append(callback)
        else:
            warnings.warn("There are no active scopes.")


_DEFAULT_SCOPE_SUITE = ScopeSuite()

scope = _DEFAULT_SCOPE_SUITE.scope
