from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Set,
    Callable,
    Optional,
    TypeVar,
    cast,
    Generic,
)

from signe.core.idGenerator import IdGen

from signe.core.protocols import GetterProtocol, IScope
from .consts import EffectState
from .context import get_executor


_T = TypeVar("_T")


class EffectOption:
    def __init__(self, level=0) -> None:
        self.level = level


class Effect(Generic[_T]):
    _id_gen = IdGen("Effect")

    def __init__(
        self,
        fn: Callable[[], _T],
        immediate=True,
        on: Optional[List[GetterProtocol]] = None,
        debug_trigger: Optional[Callable] = None,
        priority_level=1,
        debug_name: Optional[str] = None,
        capture_parent_effect=True,
        scope: Optional[IScope] = None,
    ) -> None:
        self.__id = self._id_gen.new()
        self._executor = get_executor()
        self.fn = fn
        self._upstream_refs: Set[GetterProtocol] = set()
        self._debug_name = debug_name
        self._debug_trigger = debug_trigger

        self.auto_collecting_dep = not bool(on)

        self._state: EffectState = "INIT"
        self._pending_count = 0
        self._cleanups: List[Callable[[], None]] = []
        # self.priority_level = priority_level

        if scope:
            scope.add_effect(self)

        self._sub_effects: List[Effect] = []

        running_caller = self._executor.get_running_caller()
        if running_caller and running_caller.is_effect:
            cast(Effect, running_caller).made_sub_effect(self)

        if not self.auto_collecting_dep:
            assert on
            for getter in on:
                getter.mark_caller(self)
                self.add_upstream_ref(getter)

        if immediate:
            self.update()

    @property
    def id(self):
        return self.__id

    @property
    def state(self):
        return self._state

    @property
    def is_effect(self) -> bool:
        return True

    @property
    def is_pedding(self) -> bool:
        return self._state == "PENDING"

    @property
    def is_need_update(self) -> bool:
        return self._state == "NEED_UPDATE"

    def made_sub_effect(self, sub: Effect):
        self._sub_effects.append(sub)

    def add_upstream_ref(self, getter: GetterProtocol):
        self._upstream_refs.add(getter)

    def update_state(self, state: EffectState):
        self._state = state

    def made_upstream_confirm_state(self):
        for us in self._upstream_refs:
            if isinstance(us, Effect):
                us.confirm_state()

    def confirm_state(self):
        pass

    def update(self) -> _T:
        try:
            self._exec_cleanups()
            self._executor.mark_running_caller(self)
            self._state = "RUNNING"

            if self.auto_collecting_dep:
                self._clear_all_deps()

            self._dispose_sub_effects()
            result = self.fn()
            if self._debug_trigger:
                self._debug_trigger()

            return result

        finally:
            self._state = "STALE"
            self._executor.reset_running_caller(self)

    def update_pending(self, is_change_point: bool = True, is_set_pending=True):
        if is_change_point:
            self._state = "NEED_UPDATE"
            return

        if is_set_pending:
            self._pending_count += 1
        else:
            self._pending_count -= 1

        cur_is_pending = self._pending_count > 0

        if cur_is_pending:
            self._state = "PENDING"

    def _clear_all_deps(self):
        for getter in self._upstream_refs:
            getter.remove_caller(self)

        self._upstream_refs.clear()

    def dispose(self):
        # self._pending_deps.clear()
        self._clear_all_deps()
        self._exec_cleanups()
        self._dispose_sub_effects()

    def _dispose_sub_effects(self):
        for sub in self._sub_effects:
            sub.dispose()

        self._sub_effects.clear()

    @property
    def is_pending(self) -> bool:
        return self.state == "PENDING"

    def _exec_cleanups(self):
        for fn in self._cleanups:
            fn()

        self._cleanups.clear()

    def add_cleanup(self, fn: Callable[[], None]):
        self._cleanups.append(fn)

    def __call__(self) -> Any:
        return self.update()

    def __repr__(self) -> str:
        return f"Effect(id ={self.id}, name={self._debug_name})"
