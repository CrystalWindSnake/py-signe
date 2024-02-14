from __future__ import annotations
from typing import (
    TypeVar,
    Callable,
    Optional,
)
from signe.core.deps import DepManager

from signe.core.protocols import CallerProtocol, IScope

from .effect import Effect


_T = TypeVar("_T")


class Computed(Effect[_T]):
    def __init__(
        self,
        fn: Callable[[], _T],
        debug_trigger: Optional[Callable] = None,
        priority_level=1,
        debug_name: Optional[str] = None,
        scope: Optional[IScope] = None,
    ) -> None:
        super().__init__(
            fn,
            False,
            None,
            debug_trigger,
            priority_level,
            debug_name,
            scope=scope,
        )
        # self.tracker = cast(Tracker[_T], Tracker(self, self._executor, None))
        self._value = None
        self._dep_manager = DepManager(self)

    @property
    def is_effect(self) -> bool:
        return False

    @property
    def is_signal(self) -> bool:
        return False

    @property
    def callers(self):
        return self._dep_manager.get_callers("value")

    @property
    def value(self):
        if self.state == "INIT" or self.state == "PENDING":
            self._update_value(mark_change_point=self.state == "PENDING")

        self._dep_manager.tracked("value")
        return self._value

    def _update_value(self, mark_change_point=True):
        new_value = self.update()

        if self.__not_eq_value(self._value, new_value) and mark_change_point:
            self._dep_manager.triggered("value", new_value)

        self._value = new_value

    def __not_eq_value(self, a, b):
        try:
            return bool(a != b)
        except ValueError:
            return True

    def mark_caller(self, caller: CallerProtocol):
        self._dep_manager.mark_caller(caller, "value")

    def remove_caller(self, caller: CallerProtocol):
        self._dep_manager.remove_caller(caller)

    def confirm_state(self):
        self._update_value()

    def update_pending(
        self,
        is_change_point: bool = True,
        is_set_pending=True,
    ):
        pre_is_pending = self._pending_count > 0

        if is_set_pending:
            self._pending_count += 1
        else:
            self._pending_count -= 1

        cur_is_pending = self._pending_count > 0

        if cur_is_pending:
            self._state = "PENDING"

        if pre_is_pending ^ cur_is_pending:
            # pending state changed,nodify getters
            for caller in self.callers:
                caller.update_pending(False, cur_is_pending)

    def __repr__(self) -> str:
        return f"Computed(id ={self.id}, name={self._debug_name})"
