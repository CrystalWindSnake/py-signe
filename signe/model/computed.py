from signe.core import Computed
from signe.core.scope import IScope
from signe.utils import get_current_executor
from typing import (
    TypeVar,
    Callable,
    Union,
    overload,
    Optional,
)


T = TypeVar("T")


_T_computed = Callable[[], T]
_T_computed_setter = Callable[[Callable[[], T]], _T_computed]


@overload
def computed(
    fn: None = ...,
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[IScope] = None,
) -> _T_computed_setter:
    ...


@overload
def computed(
    fn: Callable[[], T],
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[IScope] = None,
) -> _T_computed[T]:
    ...


def computed(
    fn: Optional[Callable[[], T]] = None,
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[IScope] = None,
) -> Union[_T_computed_setter, _T_computed[T]]:
    kws = {
        "priority_level": priority_level,
        "debug_trigger": debug_trigger,
        "debug_name": debug_name,
    }

    if fn:
        cp = Computed(get_current_executor(), fn, **kws)

        def getter():
            return cp.value

        return getter
    else:

        def wrap_cp(fn: Callable[[], T]):
            return computed(fn, **kws, scope=scope)

        return wrap_cp
