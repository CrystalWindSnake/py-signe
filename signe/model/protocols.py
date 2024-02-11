from typing import Callable, TypeVar, Protocol

T = TypeVar("T")


class SignalProtocol(Protocol[T]):
    @property
    def value(self) -> T:
        ...

    @value.setter
    def value(self, value: T):
        ...


class GetterProtocol(Protocol[T]):
    @property
    def value(self) -> T:
        ...
