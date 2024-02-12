from signe.core.computed import Computed
from signe.core.signal import Signal
from signe.model.types import TMaybeSignal


def is_signal(obj: TMaybeSignal):
    """Checks if a value is a signal or computed object.

    Args:
        obj (_type_): _description_
    """
    return isinstance(obj, (Signal, Computed))


def to_value(obj: TMaybeSignal):
    """Normalizes values / signals / getters to values.

    Args:
        obj (_type_): _description_

    ## Example
    ```
    to_value(1)          #    --> 1
    to_value(signal(1))  #    --> 1
    ```

    """
    if is_signal(obj):
        return obj.value

    return obj
