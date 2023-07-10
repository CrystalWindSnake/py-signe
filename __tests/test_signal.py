import _imports
import pytest
import utils
from signe import createSignal, effect, computed, cleanup, createReactive, batch
from signe.core.signal import Signal
from signe.core.effect import Effect
import gc


@pytest.fixture(scope="function")
def signal_del_spy():
    @utils.fn
    def spy():
        pass

    def __del__(self):
        spy()

    Signal.__del__ = __del__
    yield spy
    delattr(Signal, "__del__")


@pytest.fixture(scope="function")
def effect_del_spy():
    @utils.fn
    def spy():
        pass

    def __del__(self):
        spy()

    Effect.__del__ = __del__
    yield spy
    delattr(Effect, "__del__")


def test_should_release(signal_del_spy: utils.fn):
    def fn():
        _, _ = createSignal(1)

    fn()

    assert signal_del_spy.calledTimes == 1


@utils.mark_todo
def test_should_release_with_computed(
    signal_del_spy: utils.fn, effect_del_spy: utils.fn
):
    num, set_num = createSignal(1)

    def temp_run(x):
        pass

        @computed
        def cp_1():
            print(x)
            return num()

        @effect
        def _():
            cp_1()

    assert signal_del_spy.calledTimes == 0
    assert effect_del_spy.calledTimes == 0

    temp_run(1)
    temp_run(2)
    temp_run(3)
    temp_run(4)
    assert effect_del_spy.calledTimes == 1
    # assert signal_del_spy.calledTimes == 1
