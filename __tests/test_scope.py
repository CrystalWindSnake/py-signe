import _imports
import pytest
import utils
from signe import createSignal, effect, computed, scope, createReactive, batch
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


def test_should_release_signal(signal_del_spy: utils.fn):
    def fn():
        x, y = createSignal(1)

    fn()

    assert signal_del_spy.calledTimes == 1


def test_should_release_with_computed(
    signal_del_spy: utils.fn, effect_del_spy: utils.fn
):
    num, set_num = createSignal(1)

    def temp_run(x):
        with scope():

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
    assert effect_del_spy.calledTimes == 8


def test_should_not_release_computed_call_in_scope(
    signal_del_spy: utils.fn, effect_del_spy: utils.fn
):
    num, set_num = createSignal(1)

    def cp_1():
        return num()

    cp_1_spy = utils.fn(cp_1)

    cp_1 = computed(cp_1_spy)

    def temp_run():
        with scope():

            @effect
            def _():
                cp_1()

    temp_run()

    @effect
    def _():
        cp_1()

    assert cp_1_spy.calledTimes == 1

    set_num(2)
    assert cp_1_spy.calledTimes == 2

    # Only the effects defined within the scope should be released, not the computeds defined outside the scope.
    assert effect_del_spy.calledTimes == 1


def test_nested_scope(signal_del_spy: utils.fn, effect_del_spy: utils.fn):
    num, set_num = createSignal(1)

    def temp_run(x):
        with scope():

            @computed
            def cp_1():
                print(x)
                return num()

            def inner_fn():
                with scope():

                    @computed
                    def cp_2():
                        return cp_1()

                    cp_2()

            inner_fn()

    assert signal_del_spy.calledTimes == 0
    assert effect_del_spy.calledTimes == 0

    temp_run(1)
    assert effect_del_spy.calledTimes == 2
