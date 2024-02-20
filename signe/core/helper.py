from datetime import datetime, date
from typing import Callable, Tuple


def is_object(obj):
    return obj is not None and (
        not isinstance(obj, (int, str, Tuple, float, datetime, date, Callable))
    )


def has_changed(a, b):
    try:
        return bool(a != b)
    except ValueError:
        return True
