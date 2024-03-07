from typing import Callable, Generic, TypeVar, cast

from signe.core.types import TMaybeSignal, TSignal

_T = TypeVar("_T")


class ReadableMixin(Generic[_T]):
    __slots__ = ("__weakref__",)

    @property
    def value(self) -> _T:
        ...


def is_signal(obj: TMaybeSignal):
    """Checks if a value is a signal or computed object.

    Args:
        obj (_type_): _description_
    """
    return isinstance(obj, ReadableMixin)


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

    if isinstance(obj, Callable):
        return obj()

    return cast(_T, obj)
