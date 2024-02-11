from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    TypeVar,
    Callable,
    Optional,
    cast,
)

from signe.core.mixins import Tracker
from signe.core.protocols import CallerProtocol, GetterProtocol, IScope

from .effect import Effect

if TYPE_CHECKING:
    from .runtime import Executor


_T = TypeVar("_T")


class Computed(Effect[_T]):
    def __init__(
        self,
        executor: Executor,
        fn: Callable[[], _T],
        debug_trigger: Optional[Callable] = None,
        priority_level=1,
        debug_name: Optional[str] = None,
        scope: Optional[IScope] = None,
    ) -> None:
        super().__init__(
            executor,
            fn,
            False,
            None,
            debug_trigger,
            priority_level,
            debug_name,
            scope=scope,
        )
        self.tracker = cast(Tracker[_T], Tracker(self, executor, None))

    @property
    def is_effect(self) -> bool:
        return False

    @property
    def is_signal(self) -> bool:
        return False

    @property
    def callers(self):
        return self.tracker.callers

    @property
    def value(self):
        if self.state == "INIT" or self.state == "PENDING":
            self._update_value(mark_change_point=self.state == "PENDING")

        return self.tracker.get_value_with_track()

    def _update_value(self, mark_change_point=True):
        new_value = self.update()

        if self.tracker.get_value_without_track() != new_value and mark_change_point:
            scheduler = self._executor.get_current_scheduler()
            scheduler.mark_computed_change_point(self)

            self._update_caller_state()

        self.tracker.update_value(new_value)

    def _update_caller_state(self):
        for caller in self.tracker.callers:
            caller.update_pending(self, is_change_point=True)

    def mark_caller(self, caller: CallerProtocol):
        self.tracker.mark_caller(caller)

    def remove_caller(self, caller: CallerProtocol):
        self.tracker.remove_caller(caller)

    def confirm_state(self):
        self._update_value()

    def update_pending(
        self,
        getter: GetterProtocol,
        is_change_point: bool = True,
        is_set_pending=True,
    ):
        pre_is_pending = len(self._pending_deps) > 0

        if is_set_pending:
            self._pending_deps.add(getter)
        else:
            self._pending_deps.remove(getter)

        cur_is_pending = len(self._pending_deps) > 0

        if cur_is_pending:
            self._state = "PENDING"

        cur_is_pending = len(self._pending_deps) > 0

        if pre_is_pending ^ cur_is_pending:
            # pending state changed,nodify getters
            for caller in self.callers:
                caller.update_pending(self, False, cur_is_pending)

    def __repr__(self) -> str:
        return f"Computed(id ={self.id}, name={self._debug_name})"
