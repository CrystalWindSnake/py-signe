from __future__ import annotations
from typing import (
    Any,
    Dict,
    List,
    Callable,
    Optional,
    TypeVar,
    Union,
    cast,
    Generic,
    overload,
    TYPE_CHECKING,
)


from signe.core.idGenerator import IdGen
from signe.core.scope import Scope, ScopeSuite, _DEFAULT_SCOPE_SUITE

from .consts import EffectState
from .context import get_default_scheduler
from functools import partial

if TYPE_CHECKING:  # pragma: no cover
    from signe.core.deps import Dep
    from .runtime import ExecutionScheduler


_T = TypeVar("_T")


class EffectOption:  # pragma: no cover
    def __init__(self, level=0) -> None:
        self.level = level


class Effect(Generic[_T]):
    _id_gen = IdGen("Effect")

    def __init__(
        self,
        fn: Callable[[], _T],
        *,
        scheduler: ExecutionScheduler,
        scope: Union[Scope, ScopeSuite],
        trigger_fn: Optional[Callable[[Effect], None]] = None,
        scheduler_fn: Optional[Callable[[Effect], None]] = None,
        debug_trigger: Optional[Callable] = None,
        priority_level=1,
        debug_name: Optional[str] = None,
        capture_parent_effect=True,
        state: Optional[EffectState] = None,
    ) -> None:
        self.__id = self._id_gen.new()
        self._scheduler = scheduler
        self._active = True
        self._fn = fn
        self._trigger_fn = trigger_fn
        self._scheduler_fn = scheduler_fn
        self._upstream_refs: Dict[Dep, None] = {}
        self._debug_name = debug_name
        self._debug_trigger = debug_trigger

        self._state: EffectState = state or EffectState.NEED_UPDATE
        self._cleanups: List[Callable[[], None]] = []

        if isinstance(scope, Scope):
            scope.add_disposable(self)
        elif isinstance(scope, ScopeSuite):
            scope.mark_with_scope(self)

        self._sub_effects: List[Effect] = []

        if capture_parent_effect:
            running_caller = self._scheduler.get_running_caller()
            if running_caller and running_caller.is_effect:
                cast(Effect, running_caller).made_sub_effect(self)

    @property
    def id(self):
        return self.__id

    @property
    def state(self):
        return self._state

    @property
    def is_effect(self) -> bool:
        return True

    def calc_state(self):
        if self.state == EffectState.NEED_UPDATE:
            return

        self._state = EffectState.QUERYING
        # self._executor.pause_track()

        for dep in self._upstream_refs.keys():
            if dep.computed:
                dep.computed.confirm_state()
                if self._state <= EffectState.NEED_UPDATE:
                    break

        if self._state == EffectState.QUERYING:
            self._state = EffectState.STALE

        # self._executor.reset_track()

    def is_need_update(self):
        self.calc_state()
        return self.state <= EffectState.NEED_UPDATE

    def made_sub_effect(self, sub: Effect):
        self._sub_effects.append(sub)

    def trigger(self, state: EffectState):
        scheduler = self._scheduler
        scheduler.pause_scheduling()
        self._state = state

        if self._trigger_fn:
            self._trigger_fn(self)

        if self._scheduler_fn:
            self._scheduler.push_scheduler_fn(partial(self._scheduler_fn, self))

        scheduler.reset_scheduling()

    def add_upstream_ref(self, dep: Dep):
        self._upstream_refs[dep] = None

    def update_state(self, state: EffectState):
        self._state = state

    def update(self) -> _T:
        if not self._active:
            return self._fn()

        try:
            self._exec_cleanups()
            self._scheduler.mark_running_caller(self)
            self._state = EffectState.RUNNING

            self._clear_all_deps()

            self._dispose_sub_effects()
            result = self._fn()
            if self._debug_trigger:
                self._debug_trigger()

            return result

        finally:
            self._state = EffectState.STALE
            self._scheduler.reset_running_caller(self)

    def stop(self):
        self._clear_all_deps()
        self._active = False

    def _clear_all_deps(self):
        for dep in self._upstream_refs:
            dep.remove_caller(self)

        self._upstream_refs.clear()

    def dispose(self):
        self._clear_all_deps()
        self._exec_cleanups()
        self._dispose_sub_effects()

    def _dispose_sub_effects(self):
        for sub in self._sub_effects:
            sub.dispose()

        self._sub_effects.clear()

    def _exec_cleanups(self):
        for fn in self._cleanups:
            fn()

        self._cleanups.clear()

    def add_cleanup(self, fn: Callable[[], None]):
        self._cleanups.append(fn)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, __value: object) -> bool:  # pragma: no cover
        if isinstance(__value, self.__class__):
            return self.__hash__() == __value.__hash__()

        return False

    def __call__(self) -> Any:
        return self.update()

    def __repr__(self) -> str:
        return f"Effect(id ={self.id}, name={self._debug_name})"


_TEffect_Fn = Callable[[Callable[..., _T]], Effect]


@overload
def effect(
    fn: None = ...,
    *,
    immediate=True,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[Union[Scope, ScopeSuite]] = None,
    scheduler: Optional[ExecutionScheduler] = None,
) -> _TEffect_Fn[None]:
    ...


@overload
def effect(
    fn: Callable[[], None],
    *,
    immediate=True,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[Union[Scope, ScopeSuite]] = None,
    scheduler: Optional[ExecutionScheduler] = None,
) -> Effect:
    ...


def effect(
    fn: Optional[Callable[[], None]] = None,
    *,
    immediate=True,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[Union[Scope, ScopeSuite]] = None,
    scheduler: Optional[ExecutionScheduler] = None,
) -> Union[_TEffect_Fn[None], Effect]:
    kws = {
        "priority_level": priority_level,
        "debug_trigger": debug_trigger,
        "debug_name": debug_name,
        "immediate": immediate,
        "scheduler": scheduler or get_default_scheduler(),
    }

    if fn:
        if isinstance(fn, Effect):
            fn = fn._fn

        scope = scope or _DEFAULT_SCOPE_SUITE
        # executor = get_executor()

        def scheduler_fn(effect: Effect):
            if effect.is_need_update():
                effect.update()

        kws.pop("immediate")
        res = Effect(fn, scheduler_fn=scheduler_fn, **kws, scope=scope)
        if immediate:
            res.update()
        return res
    else:

        def wrap(fn: Callable[..., None]):
            return effect(fn, **kws, scope=scope)

        return wrap


def stop(effect: Effect):
    effect.stop()
