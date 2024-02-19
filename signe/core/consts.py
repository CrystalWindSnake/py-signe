from enum import IntEnum
# EffectState = Literal["INIT", "PENDING", "NEED_UPDATE", "RUNNING", "STALE"]


class EffectState(IntEnum):
    COMPUTED_INIT = 1
    PENDING = 2
    NEED_UPDATE = 3
    RUNNING = 4
    STALE = 5
    QUERYING = 6
