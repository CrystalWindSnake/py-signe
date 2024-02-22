from datetime import datetime, date
import inspect
from typing import Callable, Tuple


def get_func_args_count(fn):
    return len(inspect.getfullargspec(fn).args)


def is_object(obj):
    return obj is not None and (
        not isinstance(obj, (int, str, Tuple, float, datetime, date, Callable))
    )


def has_changed(a, b):
    try:
        return bool(a != b)
    except ValueError:  # pragma: no cover
        return True
