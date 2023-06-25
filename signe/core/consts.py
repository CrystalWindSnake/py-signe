class NotPending:
    pass

    def __bool__(self):
        return False


NOT_PENDING = NotPending()


def is_not_pending(value):
    return isinstance(value, NotPending)


from enum import Enum


class EffectState(Enum):
    CURRENT = 0
    STALE = 1
    RUNNING = 2
