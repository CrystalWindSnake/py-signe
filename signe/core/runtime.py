from __future__ import annotations
from typing import TYPE_CHECKING, Set, Dict
from .collections import Stack

from .effect import Effect

if TYPE_CHECKING:
    from .signal import Signal


class Executor:
    def __init__(self) -> None:
        self._observers: Set[Signal] = set()
        self.effect_running_stack = Stack[Effect]()
        self.execution_scheduler_stack = Stack[ExecutionScheduler]()
        self.__defalut_executionScheduler = ExecutionScheduler()

    @property
    def current_execution_scheduler(self):
        return (
            self.execution_scheduler_stack.get_current()
            or self.__defalut_executionScheduler
        )

    @property
    def is_running(self):
        return (
            self.current_execution_scheduler.is_running
            or len(self.effect_running_stack) > 0
        )


class ExecutionScheduler:
    def __init__(self) -> None:
        self.__tick = 0
        self.__signal_updates: Dict[Signal, None] = {}
        self.__effect_updates: Dict[Effect, None] = {}
        self.__running = False

    @property
    def tick(self):
        return self.__tick

    def add_signal(self, signal: Signal):
        self.__signal_updates[signal] = None
        return self

    def add_effect(self, effect: Effect):
        self.__effect_updates[effect] = None
        return self

    def next_tick(self):
        self.__tick += 1
        return self

    @property
    def is_running(self):
        return self.__running

    def run(self):
        self.__effect_updates.clear()
        self.next_tick()
        count = 0
        self.__running = True

        while len(self.__signal_updates) > 0 or len(self.__effect_updates) > 0:
            self._run_signal_updates()
            self._run_effect_updates()

            count += 1
            if count >= 10000:
                raise Exception("exceeded the maximum number of execution rounds.")

        self.__tick = 0
        self.__running = False

    def cleanup_signal_updates(self):
        self.__signal_updates.clear()

    def cleanup_effect_updates(self):
        self.__effect_updates.clear()

    def _run_signal_updates(self):
        signals = list(self.__signal_updates.keys())
        for s in signals:
            s.update()

        self.cleanup_signal_updates()

    def _run_effect_updates(self):
        effects = sorted(self.__effect_updates.keys(), key=lambda x: x.priority_level)
        for s in effects:
            s.update()
            s._reset_age()

        self.cleanup_effect_updates()


class BatchExecutionScheduler(ExecutionScheduler):
    def __init__(self) -> None:
        super().__init__()

    def run(self):
        pass

    def run_batch(self):
        return super().run()
