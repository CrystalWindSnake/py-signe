from typing import Any, Callable, Coroutine, TypeVar, Union
from signe.core.protocols import ComputedResultProtocol, SignalResultProtocol


_T = TypeVar("_T")
_T_async_fn = Callable[[], Coroutine[Any, Any, _T]]

TSignal = SignalResultProtocol[_T]
TGetterSignal = Union[SignalResultProtocol[_T], ComputedResultProtocol[_T]]
TGetter = Union[TGetterSignal[_T], Callable[[], _T]]
TMaybeSignal = Union[_T, TGetter[_T]]
