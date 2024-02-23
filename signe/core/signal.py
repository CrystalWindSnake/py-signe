from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    TypeVar,
    Generic,
    Callable,
    Union,
    Optional,
    cast,
    overload,
)
from signe.core.computed import Computed
from signe.core.reactive import to_raw, to_reactive
from signe.core.consts import EffectState
from signe.core.idGenerator import IdGen

from signe.core.deps import GetterDepManager
from signe.core.protocols import SignalResultProtocol
from .context import get_default_scheduler
from .types import TMaybeSignal, TSignal
from collections.abc import Hashable
import operator


if TYPE_CHECKING:  # pragma: no cover
    from .runtime import ExecutionScheduler

_T = TypeVar("_T")

TComp = TypeVar("TComp")

TSignalOptionComp = Callable[[TComp, TComp], bool]
TSignalOptionInitComp = Optional[Union[bool, TSignalOptionComp[TComp]]]


def _eq_base_comp(old, new):
    if isinstance(old, Hashable) and isinstance(new, Hashable):
        return operator.eq(old, new)

    return old is new


def _always_false_comp(old, new):
    return False


class SignalOption(Generic[_T]):
    __slots__ = ("comp",)

    def __init__(self, comp: TSignalOptionInitComp[_T] = None) -> None:
        if comp is None:
            comp = _eq_base_comp
        elif comp is False:
            comp = _always_false_comp
        self.comp: TSignalOptionComp = comp  # type: ignore


class Signal(Generic[_T]):
    __slots__ = (
        "__id",
        "_is_shallow",
        "_value",
        "_raw_value",
        "_scheduler",
        "_dep_manager",
        "option",
        "__debug_name",
        "_option_comp",
        "__weakref__",
    )
    _id_gen = IdGen("Signal")

    def __init__(
        self,
        value: _T,
        *,
        scheduler: ExecutionScheduler,
        option: Optional[SignalOption[_T]] = None,
        debug_name: Optional[str] = None,
        is_shallow: bool,
    ) -> None:
        super().__init__()
        self.__id = Signal._id_gen.new()
        self._is_shallow = is_shallow
        self._value = value if is_shallow else to_reactive(value)
        self._raw_value = value if is_shallow else to_raw(value)

        self._scheduler = scheduler or get_default_scheduler()
        self._dep_manager = GetterDepManager(self._scheduler)

        self.option = option or SignalOption[_T]()
        self.__debug_name = debug_name
        self._option_comp = cast(Callable[[_T, _T], bool], self.option.comp)

    @property
    def id(self):
        return self.__id  # pragma: no cover

    @property
    def value(self):
        self._dep_manager.tracked("value")

        return self._value

    @value.setter
    def value(self, value: _T):
        use_direct = self._is_shallow
        new_value = value if use_direct else to_raw(value)

        if self._option_comp(self._raw_value, new_value):  # type: ignore
            return

        self._raw_value = new_value
        self._value = new_value if use_direct else to_reactive(new_value)

        self._dep_manager.triggered("value", new_value, EffectState.NEED_UPDATE)

    def __repr__(self) -> str:
        return f"Signal(id= {self.id} , name = {self.__debug_name})"


@overload
def signal(
    value: SignalResultProtocol[_T],
    comp: Union[TSignalOptionInitComp[_T], bool] = None,
    debug_name: Optional[str] = None,
    *,
    scheduler: Optional[ExecutionScheduler] = None,
) -> SignalResultProtocol[_T]:
    ...


@overload
def signal(
    value: _T,
    comp: Union[TSignalOptionInitComp[_T], bool] = None,
    debug_name: Optional[str] = None,
    *,
    is_shallow=False,
    scheduler: Optional[ExecutionScheduler] = None,
) -> SignalResultProtocol[_T]:
    ...


@overload
def signal(
    value: TMaybeSignal[_T],
    comp: Union[TSignalOptionInitComp[_T], bool] = None,
    debug_name: Optional[str] = None,
    *,
    is_shallow=False,
    scheduler: Optional[ExecutionScheduler] = None,
) -> SignalResultProtocol[_T]:
    ...


def signal(
    value: Union[_T, SignalResultProtocol[_T], TMaybeSignal[_T]],
    comp: Union[TSignalOptionInitComp[_T], bool] = None,
    debug_name: Optional[str] = None,
    *,
    is_shallow=False,
    scheduler: Optional[ExecutionScheduler] = None,
) -> SignalResultProtocol[_T]:
    if isinstance(value, Signal):
        return value
    signal = Signal(
        value,
        scheduler=scheduler or get_default_scheduler(),
        option=SignalOption(comp),
        debug_name=debug_name,
        is_shallow=is_shallow,
    )
    return cast(SignalResultProtocol[_T], signal)


def is_signal(obj: TMaybeSignal):
    """Checks if a value is a signal or computed object.

    Args:
        obj (_type_): _description_
    """
    return isinstance(obj, (Signal, Computed))


def to_value(obj: TMaybeSignal[_T]) -> _T:
    """Normalizes values / signals / getters to values.

    Args:
        obj (_type_): _description_

    ## Example
    ```
    to_value(1)          #    --> 1
    to_value(signal(1))  #    --> 1
    ```

    """
    if is_signal(obj):
        return cast(TSignal, obj).value

    # if isinstance(obj, Callable):
    #     return obj()

    return cast(_T, obj)
