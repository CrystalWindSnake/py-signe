from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    NewType,
    TypeVar,
    Generic,
    Callable,
    Set,
    Union,
    Optional,
    cast,
)
from .consts import NOT_PENDING, is_not_pending


if TYPE_CHECKING:
    from .runtime import Executor
    from .effect import Effect

T = TypeVar("T")

TComp = TypeVar("TComp")

TSignalOptionComp = Callable[[TComp, TComp], bool]
TSignalOptionInitComp = Optional[Union[bool, TSignalOptionComp[TComp]]]


class SignalOption(Generic[T]):
    __slots__ = ("comp",)

    def __init__(self, comp: TSignalOptionInitComp[T] = None) -> None:
        if comp is None:
            comp = lambda old, new: old == new
        elif comp == False:
            comp = lambda old, new: False
        self.comp: TSignalOptionComp = comp  # type: ignore


class Signal(Generic[T]):
    _g_id = 0

    def __init__(
        self, executor: Executor, value: T, option: Optional[SignalOption[T]] = None
    ) -> None:
        Signal._g_id += 1
        self.id = Signal._g_id
        self.__executor = executor
        self.value = value
        self.__dep_effects: Set[Effect] = set()
        self.option = option or SignalOption[T]()
        self._pending = NOT_PENDING

        self._option_comp = cast(Callable[[T, T], bool], self.option.comp)

    def getValue(self) -> T:
        current_effect = self.__executor.effect_running_stack.get_current()

        if current_effect:
            self.__dep_effects.add(current_effect)
            current_effect.add_dep_signal(self)

        return self.value  # type: ignore

    def setValue(self, value: Union[T, Callable[[T], T]]) -> T:
        if isinstance(value, Callable):
            value = value(self.value if is_not_pending(self._pending) else self._pending)  # type: ignore

        if self._option_comp(self.value, value):  # type: ignore
            return self.value  # type: ignore

        if len(self.__dep_effects) <= 0:
            self.value = value
            return self.value

        self._pending = value
        self.__executor.current_execution_scheduler.add_signal(self).run()

        return value  # type: ignore

    def update(self):
        self.value = self._pending
        self._pending = NOT_PENDING
        for sub in self.__dep_effects:
            sub._push_scheduler()

    def cleanup_dep_effect(self, effect: Effect):
        self.__dep_effects.remove(effect)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, self.__class__):
            return self.__hash__() == __value.__hash__()

        return False
