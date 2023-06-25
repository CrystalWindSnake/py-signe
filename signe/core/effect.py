from __future__ import annotations
from typing import TYPE_CHECKING, Any, TypeVar, Set, Callable, Optional, Generic
from .consts import EffectState

if TYPE_CHECKING:
    from .runtime import Executor
    from .signal import Signal

T = TypeVar("T")


class EffectOption:
    def __init__(self, level=0) -> None:
        self.level = level


class Effect(Generic[T]):
    _g_id = 0

    def __init__(self, executor: Executor, fn: Callable[[], T]) -> None:
        Effect._g_id += 1
        self.id = Effect._g_id
        self.__executor = executor
        self.value: Optional[T] = None
        self.fn = fn
        self._age = 0
        self._state = EffectState.CURRENT
        self.__dep_signals: Set[Signal] = set()
        self.__dep_effects: Set[Effect] = set()
        self._sub_effects: list[Effect] = []

        self._cleanup_callbacks: list[Callable] = []

        self.__init_run_fn()

    def _add_sub_effect(self, effect: Effect):
        self._sub_effects.append(effect)

    def add_dep_signal(self, signal: Signal):
        self.__dep_signals.add(signal)

    def add_dep_effect(self, effect: Effect):
        self.__dep_effects.add(effect)

    def getValue(self):
        tick = self.__executor.current_execution_scheduler.tick
        current_effect = self.__executor.effect_running_stack.get_current()

        if current_effect:
            if self._age == tick:
                if self._state == EffectState.RUNNING:
                    raise Exception("circular running")

                self.update()

            self.__dep_effects.add(current_effect)
            current_effect.add_dep_effect(self)

        return self.value

    def _push_scheduler(self):
        tick = self.__executor.current_execution_scheduler.tick

        if self._age >= tick:
            return

        self._age = tick
        self._state = EffectState.STALE

        self.__executor.current_execution_scheduler.add_effect(self)

        for effect in self.__dep_effects:
            effect._push_scheduler()

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self.getValue()

    def update(self):
        if self._state != EffectState.STALE:
            return

        self.__run_fn()

    def __init_run_fn(self):
        current_effect = self.__executor.effect_running_stack.get_current()

        if current_effect is not None and current_effect is not self:
            current_effect._add_sub_effect(self)

        try:
            self.__executor.effect_running_stack.set_current(self)
            self.value = self.fn()

        finally:
            self.__executor.effect_running_stack.reset_current()

    def add_cleanup_callback(self, callback: Callable):
        self._cleanup_callbacks.append(callback)

    def __run_fn(self):
        self._cleanup_source_before_update()

        current_effect = self.__executor.effect_running_stack.get_current()

        if current_effect is not None and current_effect is not self:
            current_effect._add_sub_effect(self)

        try:
            self.__executor.effect_running_stack.set_current(self)

            self._state = EffectState.RUNNING

            self.cleanup_deps()

            self.value = self.fn()

            self._state = EffectState.CURRENT

        finally:
            self.__executor.effect_running_stack.reset_current()

    def cleanup_dep_effect(self, effect: Effect):
        self.__dep_effects.remove(effect)

    def cleanup_deps(self):
        for s in self.__dep_signals:
            s.cleanup_dep_effect(self)

        self.__dep_signals.clear()

        for effect in self.__dep_effects:
            effect.cleanup_dep_effect(self)

        self.__dep_effects.clear()

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, self.__class__):
            return self.__hash__() == __value.__hash__()

        return False

    def _cleanup_source_before_update(self):
        self._cleanup_sub_effects()

        for cb in self._cleanup_callbacks:
            cb()

        self._cleanup_callbacks.clear()

    def _cleanup_sub_effects(self):
        # for effect in self._sub_effects:
        #     effect.dispose()

        self._sub_effects.clear()

    def dispose(self):
        self._cleanup_sub_effects()
        self.cleanup_deps()
        # self.fn = None

    def _reset_age(self):
        self._age = 0
