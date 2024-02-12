from signe.core import Computed
from signe.core.scope import IScope
from signe.model.protocols import GetterProtocol
from signe.utils import _GLOBAL_SCOPE_MANAGER


from typing import TypeVar, Callable, Union, cast, overload, Optional

T = TypeVar("T")


_T_computed = GetterProtocol[T]
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
        scope = scope or _GLOBAL_SCOPE_MANAGER._get_last_scope()
        cp = Computed(fn, **kws, scope=scope)
        return cast(GetterProtocol[T], cp)
    else:

        def wrap_cp(fn: Callable[[], T]):
            return computed(fn, **kws, scope=scope)

        return wrap_cp
