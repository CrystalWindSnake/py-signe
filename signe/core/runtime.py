from __future__ import annotations
from typing import Iterable, List, Dict, TYPE_CHECKING, cast

from signe.core.mixins import CallerMixin, GetterMixin
from .collections import Stack


class Executor:
    def __init__(self) -> None:
        self._caller_running_stack = Stack[CallerMixin]()
        self.execution_scheduler_stack = Stack[ExecutionScheduler]()
        self.__defalut_executionScheduler = ExecutionScheduler()

    def set_default_execution_scheduler(self, execution_scheduler: ExecutionScheduler):
        self.__defalut_executionScheduler = execution_scheduler

    def get_current_scheduler(self):
        return (
            self.execution_scheduler_stack.get_current()
            or self.__defalut_executionScheduler
        )

    def mark_running_caller(self, caller: CallerMixin):
        self._caller_running_stack.set_current(caller)

    def reset_running_caller(self, caller: CallerMixin):
        self._caller_running_stack.reset_current()

    def get_running_caller(self):
        return self._caller_running_stack.get_current()


class ExecutionScheduler:
    def __init__(self) -> None:
        self._getter_change_points: Dict[GetterMixin, None] = {}
        self.__effect_updates: Dict[CallerMixin, None] = {}
        self.__running = False

    @property
    def is_running(self):
        return self.__running

    def mark_change_point(self, getter: GetterMixin):
        self._getter_change_points[getter] = None

    def run(self):
        count = 0
        self.__running = True

        try:
            while len(self._getter_change_points) > 0 or len(self.__effect_updates) > 0:
                self._run_getter_updates()
                self._run_effect_updates()

                count += 1
                if count >= 10000:
                    raise Exception("exceeded the maximum number of execution rounds.")
        finally:
            self.__running = False

    def _run_getter_updates(self):
        for getter in self._getter_change_points:
            effects = self.__get_pending_effects(getter)
            for effect in effects:
                self.__effect_updates[effect] = None

        self._getter_change_points.clear()

    def _run_effect_updates(self):
        for effect in self.__effect_updates:
            if effect.is_pedding:
                effect.update()

            # if effect.is_need_update:
            #     effect.update()
            # else:
            #     # Let the upstream node determine the state
            #     effect.made_upstream_confirm_state()

        self.__effect_updates.clear()

    def __get_pending_effects(self, getter: GetterMixin) -> Iterable[CallerMixin]:
        stack: List[CallerMixin] = list(getter.callers)
        result: List[CallerMixin] = []

        while len(stack):
            current = stack.pop()

            if isinstance(current, GetterMixin):
                stack.extend(current.callers)

            elif current.is_effect and current.is_pedding:
                result.append(current)

        return result


class BatchExecutionScheduler(ExecutionScheduler):
    def __init__(self) -> None:
        super().__init__()

    def run(self):
        pass

    def run_batch(self):
        return super().run()
