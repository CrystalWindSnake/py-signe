from __future__ import annotations
from typing import Any, Dict, Optional, Set, TYPE_CHECKING
from signe.core.id_generator import IdGen
from .consts import EffectState


if TYPE_CHECKING:  # pragma: no cover
    from .computed import Computed
    from signe.core.protocols import CallerProtocol
    from .runtime import ExecutionScheduler


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

    def __hash__(self) -> int:
        return hash(self.__id)

    def __eq__(self, __value: object) -> bool:  # pragma: no cover
        if isinstance(__value, self.__class__):
            return self.__hash__() == __value.__hash__()

        return False


class GetterDepManager:
    def __init__(
        self,
        scheduler: ExecutionScheduler,
    ) -> None:
        self._scheduler = scheduler
        self._deps_map: Dict[str, Dep] = {}

    def tracked(
        self, key, value: Optional[Any] = None, computed: Optional[Computed] = None
    ):
        running_caller = self._scheduler.get_running_caller()

        if not (running_caller and self._scheduler.should_track()):
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

        scheduler = self._scheduler

        for caller in dep.get_callers():
            caller.trigger(state)

        if scheduler.should_run:
            scheduler.run()

    def dispose(self):
        self._deps_map.clear()
