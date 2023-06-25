from __future__ import annotations
from typing import TYPE_CHECKING, List, Dict
from itertools import chain

if TYPE_CHECKING:
    from .signal import Signal


class Transition:
    def __init__(self) -> None:
        self.signals: List[Signal] = []

    def add_signal(self, signal: Signal):
        self.signals.append(signal)

    def _ex_execute(self):
        raise NotImplementedError()


class BatchTransition(Transition):
    def __init__(self) -> None:
        super().__init__()

    def _ex_execute(self):
        signals: Dict[int, Signal] = {}

        for s in self.signals:
            signals[s.id] = s

        all_signals = [
            s
            for s in signals.values()
            if not s._option_comp(s.value, s.transition_value)
        ]

        for s in all_signals:
            s._transition_to_value()

        all_subs = (s.subs for s in all_signals)
        all_subs = set(chain.from_iterable(all_subs))

        subs = sorted(all_subs, key=lambda d: d.level, reverse=True)
        for sub in subs:
            sub.run()
