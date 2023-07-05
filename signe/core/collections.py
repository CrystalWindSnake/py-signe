from typing import TypeVar, Generic, List


T = TypeVar("T")


class Stack(Generic[T]):
    def __init__(self) -> None:
        self.__stack: List[T] = []

    def set_current(self, obj: T):
        self.__stack.append(obj)

    def is_current(self, obj: T):
        return self.get_current() is obj

    def reset_current(self):
        return self.__stack.pop()

    def __len__(self):
        return len(self.__stack)

    def get_current(
        self,
    ):
        if len(self.__stack) <= 0:
            return None

        return self.__stack[len(self.__stack) - 1]
