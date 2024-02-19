from typing import Callable
from signe.core.protocols import ExecutorProtocol
from functools import lru_cache


_T_executor_builder = Callable[[], ExecutorProtocol]


@lru_cache(maxsize=1)
def default_executor_builder():
    from .runtime import Executor

    return Executor()


_executor_builder: _T_executor_builder = default_executor_builder


def set_executor_builder(fn: Callable[[], ExecutorProtocol]):
    global _executor_builder
    _executor_builder = fn


def get_executor() -> ExecutorProtocol:
    return _executor_builder()
