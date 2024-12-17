from __future__ import annotations
from typing import (
    TYPE_CHECKING,
    TypeVar,
    Callable,
    Optional,
    Generic,
    Union,
    cast,
    overload,
)
from signe.core.consts import EffectState
from signe.core.context import get_default_scheduler
from signe.core.deps import GetterDepManager
from signe.core.helper import has_changed
from signe.core.id_generator import IdGen

from signe.core.protocols import ComputedResultProtocol
from signe.core.mixins import ReadableMixin

from .effect import Effect
from .scope import Scope, ScopeSuite, _DEFAULT_SCOPE_SUITE

if TYPE_CHECKING:  # pragma: no cover
    from .runtime import ExecutionScheduler

_T = TypeVar("_T")


class Computed(Generic[_T], ReadableMixin[_T]):
    _id_gen = IdGen("Computed")

    def __init__(
        self,
        fn: Callable[[], _T],
        *,
        scheduler: ExecutionScheduler,
        scope: Union[Scope, ScopeSuite],
        debug_trigger: Optional[Callable] = None,
        priority_level=1,
        debug_name: Optional[str] = None,
        capture_parent_effect=True,
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
            scheduler=scheduler,
            trigger_fn=trigger_fn,
            # immediate=False,
            debug_trigger=debug_trigger,
            scope=scope,
            state=EffectState.COMPUTED_INIT,
            debug_name=debug_name,
            capture_parent_effect=capture_parent_effect,
        )
        self._dep_manager = GetterDepManager(scheduler)

        if isinstance(scope, Scope):
            scope.add_disposable(self)
        elif isinstance(scope, ScopeSuite):
            scope.mark_with_scope(self)

    @property
    def id(self):
        return self.__id  # pragma: no cover

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

        if has_changed(self._value, new_value):
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
    scope: Optional[Union[Scope, ScopeSuite]] = None,
    scheduler: Optional[ExecutionScheduler] = None,
) -> _T_computed_setter: ...


@overload
def computed(
    fn: Callable[[], _T],
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[Union[Scope, ScopeSuite]] = None,
    scheduler: Optional[ExecutionScheduler] = None,
) -> _T_computed[_T]: ...


def computed(
    fn: Optional[Callable[[], _T]] = None,
    *,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[Union[Scope, ScopeSuite]] = None,
    scheduler: Optional[ExecutionScheduler] = None,
) -> Union[_T_computed_setter, _T_computed[_T]]:
    kws = {
        "priority_level": priority_level,
        "debug_trigger": debug_trigger,
        "debug_name": debug_name,
        "scheduler": scheduler or get_default_scheduler(),
    }

    if fn:
        cp = Computed(fn, **kws, scope=scope or _DEFAULT_SCOPE_SUITE)
        return cast(ComputedResultProtocol[_T], cp)
    else:

        def wrap_cp(fn: Callable[[], _T]):
            return computed(fn, **kws, scope=scope)

        return wrap_cp
