from typing import Any, Callable, Coroutine, Generic, TypeVar, Union
from signe.core.protocols import ComputedResultProtocol, SignalResultProtocol


_T = TypeVar("_T")
_T_async_fn = Callable[[], Coroutine[Any, Any, _T]]

TSignal = SignalResultProtocol[_T]
TGetterSignal = Union[SignalResultProtocol[_T], ComputedResultProtocol[_T]]
TGetter = Union[TGetterSignal[_T], Callable[[], _T]]
TMaybeSignal = Union[_T, TGetter[_T]]


class AsyncComputedResult(Generic[_T]):
    __slot__ = ("_result", "_fn")

    def __init__(self, result: TSignal[_T], fn: _T_async_fn[_T]) -> None:
        self._result = result
        self._fn = fn

    @property
    def value(self):
        return self._result.value

    def __call__(self) -> Any:
        return self._fn()
