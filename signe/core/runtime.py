from __future__ import annotations
from typing import Dict, TYPE_CHECKING

from signe.core.consts import EffectState
from .collections import Stack
from .protocols import CallerProtocol

if TYPE_CHECKING:
    from signe.core import Effect


def _defatul_executor_builder():
    return Executor()


executor_builder = _defatul_executor_builder


class Executor:
    def __init__(self) -> None:
        self._caller_running_stack = Stack[CallerProtocol]()
        self.execution_scheduler_stack = Stack[ExecutionScheduler]()
        self.__defalut_executionScheduler = ExecutionScheduler()
        self._pause_track_count = 0

    def pause_track(self):
        self._pause_track_count += 1

    def reset_track(self):
        self._pause_track_count -= 1

    def should_track(self):
        return self._pause_track_count <= 0

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
        self._effect_updates: Dict[Effect, None] = {}
        self.__running = False
        self.pause_should_run_stack = 0

    @property
    def should_run(self):
        return not (self.__running or (self.pause_should_run_stack != 0))

    def pause_scheduling(self):
        self.pause_should_run_stack += 1

    def reset_scheduling(self):
        self.pause_should_run_stack -= 1

    def mark_update(self, effect: Effect):
        self._effect_updates[effect] = None

    def run(self):
        count = 0
        self.__running = True

        try:
            while self._effect_updates:
                self._run_effect_updates()

                count += 1
                if count >= 10000:
                    raise Exception("exceeded the maximum number of execution rounds.")
        finally:
            self.__running = False

    def _run_effect_updates(self):
        effects = tuple(self._effect_updates.keys())
        self._effect_updates.clear()
        for effect in effects:
            effect.calc_state()
            if effect.state <= EffectState.NEED_UPDATE:
                effect.update()


class BatchExecutionScheduler(ExecutionScheduler):
    def __init__(self) -> None:
        super().__init__()

    @property
    def should_run(self):
        return False

    def run(self):
        pass

    def run_batch(self):
        return super().run()
