from typing import Any, Callable, Optional
import pytest


class fn:
    def __init__(self, fn: Optional[Callable] = None) -> None:
        self._fn = fn
        self._called_count = 0

    def mockClear(self):
        self._called_count = 0
        return self

    @property
    def calledTimes(self):
        return self._called_count

    def toHaveBeenCalled(self):
        return self.calledTimes > 0

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        if self._fn is None:
            pass
            self._called_count += 1
            return

        assert self._fn is not None
        result = self._fn(*args, **kwds)
        self._called_count += 1

        return result


mark_todo = pytest.mark.skip("todo")
