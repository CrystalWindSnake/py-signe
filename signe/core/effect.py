from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    List,
    Set,
    Callable,
    Optional,
    cast,
)

from signe.core.idGenerator import IdGen
from signe.core.mixins import GetterMixin, CallerMixin
from .consts import EffectState

if TYPE_CHECKING:
    from .runtime import Executor


class EffectOption:
    def __init__(self, level=0) -> None:
        self.level = level


class Effect(CallerMixin):
    _id_gen = IdGen("Effect")

    def __init__(
        self,
        executor: Executor,
        fn: Callable[[], None],
        debug_trigger: Optional[Callable] = None,
        priority_level=1,
        debug_name: Optional[str] = None,
        capture_parent_effect=True,
    ) -> None:
        self.__id = self._id_gen.new()
        self._executor = executor
        self.fn = fn
        self._upstream_refs: Set[GetterMixin] = set()
        self.__debug_name = debug_name
        self._debug_trigger = debug_trigger
        self._state = EffectState.PENDING
        self._pending_deps: Set[GetterMixin] = set()
        self._cleanups: List[Callable[[], None]] = []
        # self.priority_level = priority_level

        self._sub_effects: List[Effect] = []

        running_caller = self._executor.get_running_caller()
        if running_caller and running_caller.is_effect:
            cast(Effect, running_caller).made_sub_effect(self)

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
        return self._state == EffectState.PENDING

    def made_sub_effect(self, sub: Effect):
        self._sub_effects.append(sub)

    def add_upstream_ref(self, getter: GetterMixin):
        self._upstream_refs.add(getter)

    def update(self):
        if not self.is_pedding:
            return
        try:
            self._exec_cleanups()
            self._executor.mark_running_caller(self)
            self._state = EffectState.RUNNING

            self._clear_all_deps()
            self._dispose_sub_effects()
            self.fn()
            if self._debug_trigger:
                self._debug_trigger()

        finally:
            self._state = EffectState.STALE
            self._executor.reset_running_caller(self)

    def update_pending(self, getter: GetterMixin, is_set_pending=True):
        if is_set_pending:
            self._pending_deps.add(getter)
        else:
            self._pending_deps.remove(getter)

        cur_is_pending = len(self._pending_deps) > 0

        if cur_is_pending:
            self._state = EffectState.PENDING

    def _clear_all_deps(self):
        for getter in self._upstream_refs:
            getter.remove_caller(self)

        self._upstream_refs.clear()

    def dispose(self):
        self._pending_deps.clear()
        self._clear_all_deps()
        self._exec_cleanups()
        self._dispose_sub_effects()

    def _dispose_sub_effects(self):
        for sub in self._sub_effects:
            sub.dispose()

        self._sub_effects.clear()

    def _exec_cleanups(self):
        for fn in self._cleanups:
            fn()

        self._cleanups.clear()

    def add_cleanup(self, fn: Callable[[], None]):
        self._cleanups.append(fn)

    def __repr__(self) -> str:
        return f"Effect(id ={self.id}, name={self.__debug_name})"
