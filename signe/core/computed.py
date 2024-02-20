from __future__ import annotations
from typing import (
    TypeVar,
    Callable,
    Optional,
    Generic,
    Union,
    cast,
    overload,
)
from signe.core.consts import EffectState
from signe.core.deps import GetterDepManager
from signe.core.idGenerator import IdGen

from signe.core.protocols import ComputedResultProtocol, IScope
from signe.core.utils import common_not_eq_value

from .effect import Effect
from .scope import _GLOBAL_SCOPE_MANAGER


_T = TypeVar("_T")


class Computed(Generic[_T]):
    _id_gen = IdGen("Computed")

    def __init__(
        self,
        fn: Callable[[], _T],
        debug_trigger: Optional[Callable] = None,
        priority_level=1,
        debug_name: Optional[str] = None,
        scope: Optional[IScope] = None,
    ) -> None:
        self.__id = self._id_gen.new()
        self._value = None
        self._debug_name = debug_name

        def getter():
            return fn()

        def trigger_fn(_):
            self.trigger(EffectState.PENDING)

        self._effect = Effect(
            getter,
            trigger_fn,
            immediate=False,
            debug_trigger=debug_trigger,
            scope=scope,
            state=EffectState.COMPUTED_INIT,
            debug_name=debug_name,
        )
        self._dep_manager = GetterDepManager()
        if scope:
            scope.add_disposable(self)

    @property
    def id(self):
        return self.__id

    @property
    def is_effect(self) -> bool:
        return False

    @property
    def is_signal(self) -> bool:
        return False

    def trigger(self, state: EffectState):
        state = EffectState.PENDING if state == EffectState.NEED_UPDATE else state
        self._effect.update_state(state)  # type: ignore

        self._dep_manager.triggered("value", self._value, state)

    def confirm_state(self):
        if self._effect.state <= EffectState.NEED_UPDATE:  # type: ignore
            self._update_value()

    def dispose(self):
        self._effect = None
        self._value = None
        self._dep_manager.dispose()

    @property
    def value(self):
        if self._effect.state <= EffectState.NEED_UPDATE:  # type: ignore
            self._update_value()

        self._dep_manager.tracked("value", computed=self)
        return self._value

    def __call__(self) -> _T:
        return self.value  # type: ignore

    def _update_value(self):
        new_value = self._effect.update()  # type: ignore

        if common_not_eq_value(self._value, new_value):
            self._dep_manager.triggered("value", new_value, EffectState.NEED_UPDATE)

        self._value = new_value

    def __repr__(self) -> str:
        state = self._effect.state  # type: ignore
        return f"Computed(id ={self.id}, name={self._debug_name}),state={state}"


_T_computed = ComputedResultProtocol[_T]
_T_computed_setter = Callable[[Callable[[], _T]], _T_computed]


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
    fn: Callable[[], _T],
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[IScope] = None,
) -> _T_computed[_T]:
    ...


def computed(
    fn: Optional[Callable[[], _T]] = None,
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[IScope] = None,
) -> Union[_T_computed_setter, _T_computed[_T]]:
    kws = {
        "priority_level": priority_level,
        "debug_trigger": debug_trigger,
        "debug_name": debug_name,
    }

    if fn:
        scope = scope or _GLOBAL_SCOPE_MANAGER._get_last_scope()
        cp = Computed(fn, **kws, scope=scope)
        return cast(ComputedResultProtocol[_T], cp)
    else:

        def wrap_cp(fn: Callable[[], _T]):
            return computed(fn, **kws, scope=scope)

        return wrap_cp
