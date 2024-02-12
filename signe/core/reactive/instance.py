from __future__ import annotations
from typing import Any, TYPE_CHECKING, Dict
from weakref import WeakValueDictionary, WeakKeyDictionary

from signe.core.signal import Signal


from dataclasses import dataclass, field


@dataclass
class ProxyInfo:
    key2signal: Dict[str, Signal] = field(default_factory=lambda: {})


_ins_map: WeakValueDictionary[InstanceProxy, object] = WeakValueDictionary()
_proxy_info_map: WeakKeyDictionary[InstanceProxy, ProxyInfo] = WeakKeyDictionary()


def register(
    proxy: InstanceProxy,
    ins,
):
    _ins_map[proxy] = ins
    _proxy_info_map[proxy] = ProxyInfo()


def track(proxy: InstanceProxy, key):
    ins = _ins_map.get(proxy)
    info = _proxy_info_map.get(proxy)

    assert ins
    assert info
    key_signal_map = info.key2signal

    signal = key_signal_map.get(key)

    if not signal:
        value = getattr(ins, key)
        signal = Signal(value)
        key_signal_map[key] = signal

    return signal.value


def trigger(proxy: InstanceProxy, key, value):
    ins = _ins_map.get(proxy)
    info = _proxy_info_map.get(proxy)

    assert ins
    assert info
    key_signal_map = info.key2signal

    signal = key_signal_map.get(key)
    if not signal:
        return
    signal.value = value


class InstanceProxy:
    def __init__(self, ins) -> None:
        register(self, ins)

    def __getattr__(self, _name: str) -> Any:
        value = track(self, _name)
        return value

    def __setattr__(self, _name: str, _value: Any) -> None:
        trigger(self, _name, _value)
