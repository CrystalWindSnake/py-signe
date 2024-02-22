from typing import Callable
from functools import lru_cache
from .runtime import Executor


_T_executor_builder = Callable[[], Executor]


@lru_cache(maxsize=1)
def default_executor_builder():
    return Executor()


_executor_builder: _T_executor_builder = default_executor_builder


def set_executor_builder(fn: Callable[[], Executor]):
    global _executor_builder
    _executor_builder = fn  # pragma: no cover


def get_executor() -> Executor:
    return _executor_builder()
