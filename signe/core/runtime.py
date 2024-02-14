from __future__ import annotations
from typing import Iterable, List, Dict, TYPE_CHECKING, cast
from .collections import Stack
from .protocols import CallerProtocol, GetterProtocol
from signe.core.effect import Effect

if TYPE_CHECKING:
    from signe.core.signal import Signal
    from signe.core.computed import Computed


def _defatul_executor_builder():
    return Executor()


executor_builder = _defatul_executor_builder


def get_executor():
    pass


class Executor:
    def __init__(self) -> None:
        self._caller_running_stack = Stack[CallerProtocol]()
        self.execution_scheduler_stack = Stack[ExecutionScheduler]()
        self.__defalut_executionScheduler = ExecutionScheduler()

    def set_default_execution_scheduler(self, execution_scheduler: ExecutionScheduler):
        self.__defalut_executionScheduler = execution_scheduler

    def get_current_scheduler(self):
        return (
            self.execution_scheduler_stack.get_current()
            or self.__defalut_executionScheduler
        )

    def mark_running_caller(self, caller: CallerProtocol):
        self._caller_running_stack.set_current(caller)

    def reset_running_caller(self, caller: CallerProtocol):
        self._caller_running_stack.reset_current()

    def get_running_caller(self):
        return self._caller_running_stack.get_current()


class ExecutionScheduler:
    def __init__(self) -> None:
        self._signal_change_points: Dict[Signal, None] = {}

        self._pending_queue: Dict[CallerProtocol, None] = {}

        self._computed_change_points: Dict[Computed, None] = {}
        self._effect_updates: Dict[Effect, None] = {}
        self.__running = False

    @property
    def is_running(self):
        return self.__running

    def mark_signal_change_point(self, signal: Signal):
        self._signal_change_points[signal] = None

    def mark_computed_change_point(self, computed: Computed):
        self._computed_change_points[computed] = None

    def mark_pending(self, caller: CallerProtocol):
        self._pending_queue[caller] = None

    def mark_update(self, caller: CallerProtocol):
        self._effect_updates[cast(Effect, caller)] = None

    def run(self):
        count = 0
        self.__running = True

        try:
            while (
                self._pending_queue
                # or self._computed_change_points
                or self._effect_updates
            ):
                # self._run_signal_updates()
                # self._run_computed_updates()
                self._run_pending_updates()
                self._run_effect_updates()

                count += 1
                if count >= 10000:
                    raise Exception("exceeded the maximum number of execution rounds.")
        finally:
            self.__running = False

    def _run_pending_updates(self):
        for caller in self._pending_queue:
            if caller.is_effect and caller.state == "NEED_UPDATE":
                self.mark_update(caller)
                continue

            if caller.is_pending:
                effects = self.__get_pending_or_update_effects(caller)
                for effect in effects:
                    self._effect_updates[effect] = None

        self._pending_queue.clear()

    # def _run_signal_updates(self):
    #     for getter in self._signal_change_points:
    #         effects = self.__get_pending_or_update_effects(getter)
    #         for effect in effects:
    #             self._effect_updates[effect] = None

    #     self._signal_change_points.clear()

    # def _run_computed_updates(self):
    #     for getter in self._computed_change_points:
    #         effects = self.__get_pending_or_update_effects(getter)
    #         for effect in effects:
    #             self._effect_updates[effect] = None

    #     self._computed_change_points.clear()

    def _run_effect_updates(self):
        for effect in self._effect_updates:
            if effect.state == "NEED_UPDATE":
                effect.update()
            else:
                # Let the upstream node determine the state
                effect.made_upstream_confirm_state()

        self._effect_updates.clear()

    def __get_pending_or_update_effects(
        self, caller: CallerProtocol
    ) -> Iterable[Effect]:
        stack: List[CallerProtocol] = [caller]
        result: List[Effect] = []

        while len(stack):
            current = stack.pop()

            if not current.is_effect:
                stack.extend(cast(GetterProtocol, current).callers)

            else:
                result.append(cast(Effect, current))

        return result


class BatchExecutionScheduler(ExecutionScheduler):
    def __init__(self) -> None:
        super().__init__()

    def run(self):
        pass

    def run_batch(self):
        return super().run()
