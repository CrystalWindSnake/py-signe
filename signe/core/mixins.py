from __future__ import annotations
from typing import Any, Dict, Optional, TypeVar, Set

from signe.core.protocols import CallerProtocol
from .context import get_executor

_T = TypeVar("_T")


# class Tracker(Generic[_T]):
#     def __init__(
#         self, owner: GetterProtocol, executor: ExecutorProtocol, value: _T
#     ) -> None:
#         self._owner = weakref(owner)
#         self._callers: Set[CallerProtocol] = set()
#         self._value = value
#         self._executor = executor

#     def get_value_with_track(self):
#         self.track()
#         return self._value

#     def update_value(self, value: _T):
#         self._value = value

#     def get_value_without_track(self):
#         return self._value

#     @property
#     def callers(self):
#         return tuple(self._callers)

#     def track(self):
#         running_caller = self._executor.get_running_caller()

#         if running_caller and running_caller.auto_collecting_dep:
#             self.__collecting_dependencies(running_caller)

#     def mark_caller(self, caller: CallerProtocol):
#         self._callers.add(caller)

#     def remove_caller(self, caller: CallerProtocol):
#         self._callers.remove(caller)

#     def __collecting_dependencies(self, running_effect: CallerProtocol):
#         self.mark_caller(running_effect)

#         owner = self._owner()
#         if owner:
#             running_effect.add_upstream_ref(owner)


class DepRemover:
    def __init__(self, dep_manager: DepManager, key):
        self._key = key
        self._dep_manager = dep_manager

    def remove_caller(self, target_caller: CallerProtocol):
        for callers in self._dep_manager._deps_map.values():
            for caller in tuple(callers):
                if caller is target_caller:
                    callers.remove(caller)


class DepManager:
    def __init__(self, owner) -> None:
        self._owner = owner
        self._executor = get_executor()
        self._deps_map: Dict[str, Set[CallerProtocol]] = {}

    def get_callers(self, key):
        if key not in self._deps_map:
            return tuple()

        return tuple(self._deps_map[key])

    def tracked(self, key, value: Optional[Any] = None):
        running_caller = self._executor.get_running_caller()

        if not (running_caller and running_caller.auto_collecting_dep):
            return

        deps = self._deps_map.get(key)
        if not deps:
            deps = set()
            self._deps_map[key] = deps

        deps.add(running_caller)
        running_caller.add_upstream_ref(self._owner)

    def triggered(self, key, value):
        dep = self._deps_map.get(key)
        if not dep:
            return

        scheduler = self._executor.get_current_scheduler()

        for caller in dep:
            if caller.is_effect:
                pass
                # set need update
                caller.update_state("NEED_UPDATE")
            else:
                pass
                # set pending
                caller.update_pending()

            scheduler.mark_pending(caller)

        if not scheduler.is_running:
            scheduler.run()

    def remove_caller(self, target_caller: CallerProtocol):
        for callers in self._deps_map.values():
            for caller in tuple(callers):
                if caller is target_caller:
                    callers.remove(caller)

    def mark_caller(self, target_caller: CallerProtocol, key):
        deps = self._deps_map.get(key)
        if not deps:
            deps = set()
            self._deps_map[key] = deps

        deps.add(target_caller)
