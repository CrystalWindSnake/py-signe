from __future__ import annotations
from typing import (
    TypeVar,
    Generic,
    Callable,
    Union,
    Optional,
    cast,
)
from signe.core.consts import EffectState
from signe.core.idGenerator import IdGen
from signe.core.protocols import CallerProtocol, SignalProtocol

from signe.core.deps import GetterDepManager
from .context import get_executor


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
    _id_gen = IdGen("Signal")

    def __init__(
        self,
        value: T,
        option: Optional[SignalOption[T]] = None,
        debug_name: Optional[str] = None,
    ) -> None:
        super().__init__()
        self.__id = Signal._id_gen.new()
        self._value = value

        self._executor = get_executor()
        self._dep_manager = GetterDepManager()

        self.option = option or SignalOption[T]()
        self.__debug_name = debug_name
        self._option_comp = cast(Callable[[T, T], bool], self.option.comp)

    @property
    def id(self):
        return self.__id

    def get_value_without_track(self):
        return self._value

    # @property
    # def callers(self):
    #     return self._dep_manager.get_callers("value")

    @property
    def is_signal(self) -> bool:
        return True

    @property
    def value(self):
        self._dep_manager.tracked("value")

        return self._value

    def confirm_state(self):
        pass

    @value.setter
    def value(self, value: T):
        org_value = self._value

        if self._option_comp(org_value, value):  # type: ignore
            return

        self._value = value

        self._dep_manager.triggered("value", value, EffectState.NEED_UPDATE)

    # def mark_caller(self, caller: CallerProtocol):
    #     self._dep_manager.mark_caller(caller, "value")

    # def remove_caller(self, caller: CallerProtocol):
    #     self._dep_manager.remove_caller(caller)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, self.__class__):
            return self.__hash__() == __value.__hash__()

        return False

    def __repr__(self) -> str:
        return f"Signal(id= {self.id} , name = {self.__debug_name})"


def signal(
    value: T,
    comp: Union[TSignalOptionInitComp[T], bool] = None,
    debug_name: Optional[str] = None,
):
    signal = Signal(value, SignalOption(comp), debug_name)
    return cast(SignalProtocol[T], signal)
