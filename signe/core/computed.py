from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    Iterable,
    TypeVar,
    Set,
    Callable,
    Optional,
    Generic,
    cast,
)

from signe.core.idGenerator import IdGen
from signe.core.mixins import GetterMixin, CallerMixin
from .consts import ComputedState

if TYPE_CHECKING:
    from .runtime import Executor


T = TypeVar("T")


class Computed(Generic[T], CallerMixin, GetterMixin):
    _id_gen = IdGen("Computed")

    def __init__(
        self,
        executor: Executor,
        fn: Callable[[], T],
        debug_trigger: Optional[Callable] = None,
        priority_level=1,
        debug_name: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.__id = self._id_gen.new()
        self._executor = executor
        self.fn = fn
        self._value = None
        self._upstream_refs: Set[GetterMixin] = set()
        self.__debug_name = debug_name
        self._debug_trigger = debug_trigger
        self._state = ComputedState.INIT
        self._callers: Set[CallerMixin] = set()
        self._pending_deps: Set[GetterMixin] = set()

    @property
    def id(self):
        return self.__id

    @property
    def is_effect(self) -> bool:
        return False

    @property
    def is_pedding(self) -> bool:
        return self._state == ComputedState.PENDING

    @property
    def is_need_update(self) -> bool:
        return False

    def remove_caller(self, caller: CallerMixin):
        self._callers.remove(caller)

    def get_callers(self) -> Iterable[CallerMixin]:
        return tuple(self._callers)

    @property
    def value(self):
        running_caller = self._executor.get_running_caller()

        if running_caller:
            self.__collecting_dependencies(running_caller)

        if self._state == ComputedState.INIT or self._state == ComputedState.PENDING:
            self.update()

        return cast(T, self._value)

    def made_upstream_confirm_state(self):
        pass

    def confirm_state(self):
        if self.is_pedding:
            self.update()

    def update(self):
        try:
            self._executor.mark_running_caller(self)
            self._state = ComputedState.RUNNING

            self._cleanup_deps()
            result = self.fn()
            if result != self._value:
                scheduler = self._executor.get_current_scheduler()

                if scheduler.is_running:
                    scheduler.mark_change_point(self)

                for caller in self._callers:
                    caller.update_pending(self)

            self._value = result
            if self._debug_trigger:
                self._debug_trigger()
            self._pending_deps.clear()

        finally:
            self._state = ComputedState.STALE
            self._executor.reset_running_caller(self)

    def add_upstream_ref(self, getter: GetterMixin):
        self._upstream_refs.add(getter)

    def update_pending(
        self, getter: GetterMixin, is_change_point: bool = True, is_set_pending=True
    ):
        pre_is_pending = len(self._pending_deps) > 0

        if is_set_pending:
            self._pending_deps.add(getter)
        else:
            self._pending_deps.remove(getter)

        cur_is_pending = len(self._pending_deps) > 0

        if cur_is_pending:
            self._state = ComputedState.PENDING

        if pre_is_pending ^ cur_is_pending:
            # pending state changed,nodify getters
            for caller in self._callers:
                caller.update_pending(self, cur_is_pending)

    def __collecting_dependencies(self, running_effect: CallerMixin):
        self._callers.add(running_effect)
        running_effect.add_upstream_ref(self)

    def _cleanup_deps(self):
        for getter in self._upstream_refs:
            getter.remove_caller(self)

        self._upstream_refs.clear()

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, self.__class__):
            return self.__hash__() == __value.__hash__()

        return False

    def dispose(self):
        self._pending_deps.clear()
        self._cleanup_deps()

    def __repr__(self) -> str:
        return f"Computed(id= {self.id} , name = {self.__debug_name})"
