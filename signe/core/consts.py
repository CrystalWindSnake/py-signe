from typing import Literal


EffectState = Literal["INIT", "PENDING", "NEED_UPDATE", "RUNNING", "STALE"]
# ComputedState = Literal["INIT", "PENDING", "RUNNING", "STALE"]

# class EffectState(Enum):
#     CURRENT = auto()
#     PENDING = auto()
#     NEED_UPDATE = auto()
#     RUNNING = auto()
#     STALE = auto()


# class ComputedState(Enum):
#     INIT = auto()
#     PENDING = auto()
#     RUNNING = auto()
#     STALE = auto()
