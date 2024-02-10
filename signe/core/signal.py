from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    Iterable,
    TypeVar,
    Generic,
    Callable,
    Set,
    Union,
    Optional,
    cast,
)
from signe.core.idGenerator import IdGen

from signe.core.mixins import GetterMixin, CallerMixin


if TYPE_CHECKING:
    from .runtime import Executor


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


class Signal(Generic[T], GetterMixin):
    _id_gen = IdGen("Signal")

    def __init__(
        self,
        executor: Executor,
        value: T,
        option: Optional[SignalOption[T]] = None,
        debug_name: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.__id = Signal._id_gen.new()
        self._value = value
        self._executor = executor
        self.option = option or SignalOption[T]()
        self.__debug_name = debug_name
        self._option_comp = cast(Callable[[T, T], bool], self.option.comp)

    @property
    def id(self):
        return self.__id

    def track(self):
        running_caller = self._executor.get_running_caller()

        if running_caller:
            self.__collecting_dependencies(running_caller)

    @property
    def value(self):
        self.track()
        return self._value

    @value.setter
    def value(self, new: T):
        self.__setValue(new)

    def __collecting_dependencies(self, running_effect: CallerMixin):
        self.mark_caller(running_effect)
        running_effect.add_upstream_ref(self)

    def __setValue(self, value: Union[T, Callable[[T], T]]):
        if isinstance(value, Callable):
            value = value(self._value)  # type: ignore

        if self._option_comp(self._value, value):  # type: ignore
            return

        self._value = value

        scheduler = self._executor.get_current_scheduler()
        scheduler.mark_change_point(self)

        self._update_caller_state()

        if not scheduler.is_running:
            scheduler.run()

    def _update_caller_state(self):
        for caller in self.callers:
            caller.update_pending(self)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, self.__class__):
            return self.__hash__() == __value.__hash__()

        return False

    def __repr__(self) -> str:
        return f"Signal(id= {self.id} , name = {self.__debug_name})"
