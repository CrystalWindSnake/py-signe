from signe.core import Effect
from signe.core.scope import IScope
from signe.utils import get_current_executor, _GLOBAL_SCOPE_MANAGER
from typing import (
    TypeVar,
    Callable,
    Union,
    overload,
    Optional,
)


T = TypeVar("T")


_TEffect_Fn = Callable[[Callable[..., T]], Effect]


@overload
def effect(
    fn: None = ...,
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[IScope] = None,
) -> _TEffect_Fn[None]:
    ...


@overload
def effect(
    fn: Callable[[], None],
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[IScope] = None,
) -> Effect:
    ...


def effect(
    fn: Optional[Callable[[], None]] = None,
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[IScope] = None,
) -> Union[_TEffect_Fn[None], Effect]:
    kws = {
        "priority_level": priority_level,
        "debug_trigger": debug_trigger,
        "debug_name": debug_name,
    }

    if fn:
        scope = scope or _GLOBAL_SCOPE_MANAGER._get_last_scope()
        res = Effect(get_current_executor(), fn, **kws, scope=scope)
        return res
    else:

        def wrap(fn: Callable[..., None]):
            return effect(fn, **kws, scope=scope)

        return wrap
