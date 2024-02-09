from enum import Enum, auto


class EffectState(Enum):
    CURRENT = auto()
    PENDING = auto()
    RUNNING = auto()
    STALE = auto()


class ComputedState(Enum):
    INIT = auto()
    PENDING = auto()
    RUNNING = auto()
    STALE = auto()
