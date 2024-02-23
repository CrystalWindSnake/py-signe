from functools import lru_cache
from .runtime import ExecutionScheduler


@lru_cache(maxsize=1)
def get_default_scheduler():
    return ExecutionScheduler()
