from datetime import date, datetime
from typing import Dict, List, Mapping, TypeVar, Union, overload, cast, Iterable
from signe.core.context import get_executor

T = TypeVar("T")
P = TypeVar("P")


@overload
def reactive(obj: List[T]) -> List[T]:
    ...


@overload
def reactive(obj: Dict[T, P]) -> Dict[T, P]:
    ...


@overload
def reactive(obj: T) -> T:
    ...


def reactive(obj: Union[List, Dict, T]) -> Union[List, Dict, T]:
    from . import ListProxy, DictProxy, InstanceProxy

    if isinstance(
        obj, (str, int, float, date, datetime, ListProxy, DictProxy, InstanceProxy)
    ):
        return obj

    if isinstance(obj, Mapping):
        return cast(Dict, DictProxy(obj))
    if isinstance(obj, Iterable):
        return cast(List, ListProxy(obj))

    return cast(T, InstanceProxy(obj))
