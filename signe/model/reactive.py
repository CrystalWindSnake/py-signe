from datetime import date, datetime
from signe.utils import get_current_executor
from typing import Dict, List, Mapping, TypeVar, Union, overload, cast, Iterable

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
    from signe.core.reactive import ListProxy, DictProxy, InstanceProxy

    if isinstance(obj, (str, int, float, date, datetime)):
        return obj

    if isinstance(obj, Mapping):
        return cast(Dict, DictProxy(get_current_executor(), obj))
    if isinstance(obj, Iterable):
        return cast(List, ListProxy(get_current_executor(), obj))

    return cast(T, InstanceProxy(get_current_executor(), obj))
