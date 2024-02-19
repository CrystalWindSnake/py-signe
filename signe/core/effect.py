from __future__ import annotations
from typing import (
    Any,
    List,
    Set,
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

from signe.core.protocols import GetterProtocol, IScope
from signe.core.scope import _GLOBAL_SCOPE_MANAGER
from .consts import EffectState
from .context import get_executor

if TYPE_CHECKING:
    from signe.core.deps import Dep

_T = TypeVar("_T")


class EffectOption:
    def __init__(self, level=0) -> None:
        self.level = level


class Effect(Generic[_T]):
    _id_gen = IdGen("Effect")

    def __init__(
        self,
        fn: Callable[[], _T],
        trigger_fn: Optional[Callable[[], None]] = None,
        immediate=True,
        on: Optional[List[GetterProtocol]] = None,
        debug_trigger: Optional[Callable] = None,
        priority_level=1,
        debug_name: Optional[str] = None,
        capture_parent_effect=True,
        scope: Optional[IScope] = None,
        state: Optional[EffectState] = None,
    ) -> None:
        self.__id = self._id_gen.new()
        self._executor = get_executor()
        self.fn = fn
        self._trigger_fn = trigger_fn
        self._upstream_refs: Set[Dep] = set()
        self._debug_name = debug_name
        self._debug_trigger = debug_trigger

        self.auto_collecting_dep = not bool(on)

        self._state: EffectState = state or EffectState.STALE
        self._pending_count = 0
        self._cleanups: List[Callable[[], None]] = []

        if scope:
            scope.add_effect(self)

        self._sub_effects: List[Effect] = []

        running_caller = self._executor.get_running_caller()
        if running_caller and running_caller.is_effect:
            cast(Effect, running_caller).made_sub_effect(self)

        if not self.auto_collecting_dep:
            assert on

            self._executor.mark_running_caller(self)
            self.auto_collecting_dep = True

            for getter in on:
                getter.value

            self.auto_collecting_dep = False
            self._executor.reset_running_caller(self)

        if immediate:
            self.update()

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
        self._executor.pause_track()

        for dep in self._upstream_refs:
            if dep.computed:
                dep.computed.confirm_state()
                if self._state >= EffectState.NEED_UPDATE:
                    break

        if self._state == EffectState.QUERYING:
            self._state = EffectState.STALE

        self._executor.reset_track()

    def is_need_update(self):
        return self.state <= EffectState.NEED_UPDATE

    def made_sub_effect(self, sub: Effect):
        self._sub_effects.append(sub)

    def trigger(self, state: EffectState):
        self._state = state

        if self._trigger_fn:
            self._trigger_fn()

    def add_upstream_ref(self, dep: Dep):
        self._upstream_refs.add(dep)

    def update_state(self, state: EffectState):
        self._state = state

    def update(self) -> _T:
        try:
            self._exec_cleanups()
            self._executor.mark_running_caller(self)
            self._state = EffectState.RUNNING

            if self.auto_collecting_dep:
                self._clear_all_deps()

            self._dispose_sub_effects()
            result = self.fn()
            if self._debug_trigger:
                self._debug_trigger()

            return result

        finally:
            self._state = EffectState.STALE
            self._executor.reset_running_caller(self)

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

    def __eq__(self, __value: object) -> bool:
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
    scope: Optional[IScope] = None,
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
    scope: Optional[IScope] = None,
) -> Effect:
    ...


def effect(
    fn: Optional[Callable[[], None]] = None,
    *,
    immediate=True,
    priority_level=1,
    debug_trigger: Optional[Callable] = None,
    debug_name: Optional[str] = None,
    scope: Optional[IScope] = None,
) -> Union[_TEffect_Fn[None], Effect]:
    kws = {
        "priority_level": priority_level,
        "debug_trigger": debug_trigger,
        "debug_name": debug_name,
        "immediate": immediate,
    }

    if fn:
        scope = scope or _GLOBAL_SCOPE_MANAGER._get_last_scope()

        executor = get_executor()

        def trigger_fn():
            if res.is_need_update():
                executor.get_current_scheduler().mark_update(res)

        res = Effect(fn, trigger_fn, **kws, scope=scope)
        return res
    else:

        def wrap(fn: Callable[..., None]):
            return effect(fn, **kws, scope=scope)

        return wrap
