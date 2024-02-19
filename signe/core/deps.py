from __future__ import annotations
from typing import Any, Dict, Optional, Set, TYPE_CHECKING
from signe.core.idGenerator import IdGen


from .context import get_executor
from .consts import EffectState


if TYPE_CHECKING:
    from .computed import Computed
    from signe.core.protocols import CallerProtocol


class Dep:
    _id_gen = IdGen("Dep")

    def __init__(self, computed: Optional[Computed] = None) -> None:
        self.__id = Dep._id_gen.new()
        self.computed = computed
        self._deps: Set[CallerProtocol] = set()

    def get_callers(self):
        return tuple(self._deps)

    def add_caller(self, caller: CallerProtocol):
        self._deps.add(caller)

    def remove_caller(self, caller: CallerProtocol):
        self._deps.remove(caller)

    def mark_caller(self, caller: CallerProtocol, key):
        self._deps.add(caller)

    def __hash__(self) -> int:
        return hash(self.__id)

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, self.__class__):
            return self.__hash__() == __value.__hash__()

        return False


class GetterDepManager:
    def __init__(self) -> None:
        self._executor = get_executor()
        self._deps_map: Dict[str, Dep] = {}

    def tracked(
        self, key, value: Optional[Any] = None, computed: Optional[Computed] = None
    ):
        running_caller = self._executor.get_running_caller()

        if not (
            running_caller
            and running_caller.auto_collecting_dep
            and self._executor.should_track
        ):
            return

        dep = self._deps_map.get(key)
        if not dep:
            dep = Dep(computed)
            self._deps_map[key] = dep

        dep.add_caller(running_caller)
        running_caller.add_upstream_ref(dep)

    def triggered(self, key, value, state: EffectState):
        dep = self._deps_map.get(key)
        if not dep:
            return

        scheduler = self._executor.get_current_scheduler()

        for caller in dep.get_callers():
            caller.trigger(state)

        if scheduler.should_run:
            scheduler.run()
