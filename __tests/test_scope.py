import _imports
import pytest
import utils
from signe.core import signal, effect, computed
from signe.core.signal import Signal
from signe.core.effect import Effect
from signe.core.computed import Computed
import gc
import logging

logging.basicConfig(level=logging.DEBUG)
mylogger = logging.getLogger()


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


@pytest.fixture(scope="function")
def computed_del_spy():
    @utils.fn
    def spy():
        pass

    def __del__(self):
        spy()

    Computed.__del__ = __del__
    yield spy
    delattr(Computed, "__del__")


def test_should_release_signal(signal_del_spy: utils.fn):
    def fn():
        num = signal(1)

    fn()

    gc.collect()
    assert signal_del_spy.calledTimes == 1


def test_should_release_with_computed(
    signal_del_spy: utils.fn, effect_del_spy: utils.fn, computed_del_spy: utils.fn
):
    num = signal(1)

    def temp_run(x):
        with scope():

            @computed
            def cp_1():
                print(x)
                return num.value

            @effect
            def _():
                pass
                cp_1.value

    assert signal_del_spy.calledTimes == 0
    assert effect_del_spy.calledTimes == 0
    assert computed_del_spy.calledTimes == 0

    temp_run(1)
    temp_run(2)
    temp_run(3)
    temp_run(4)
    gc.collect()
    assert effect_del_spy.calledTimes == 4
    assert computed_del_spy.calledTimes == 4


def test_should_not_release_computed_call_in_scope(
    signal_del_spy: utils.fn, effect_del_spy: utils.fn
):
    num = signal(1)

    @utils.fn
    def cp_1_spy():
        return num.value

    cp_1 = computed(cp_1_spy)

    def temp_run():
        with scope():

            @effect
            def _():
                cp_1.value

    temp_run()

    @effect
    def _():
        cp_1.value

    gc.collect()
    assert cp_1_spy.calledTimes == 1

    num.value = 2
    gc.collect()
    assert cp_1_spy.calledTimes == 2

    # Only the effects defined within the scope should be released, not the computeds defined outside the scope.
    gc.collect()
    assert effect_del_spy.calledTimes == 1


def test_nested_scope(signal_del_spy: utils.fn, effect_del_spy: utils.fn):
    num = signal(1)

    def temp_run(x):
        with scope():

            @computed
            def cp_1():
                print(x)
                return num.value

            def inner_fn():
                with scope():

                    @computed
                    def cp_2():
                        return cp_1.value

                    cp_2.value

            inner_fn()

    assert signal_del_spy.calledTimes == 0
    assert effect_del_spy.calledTimes == 0

    temp_run(1)
    assert effect_del_spy.calledTimes == 2
