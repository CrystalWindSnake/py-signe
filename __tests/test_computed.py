from . import utils
from signe import signal, computed, effect


class Test_computed_case:
    def test_non_call_out_of_effect(self):
        @utils.fn
        def fn_spy():
            return 1

        m1 = computed(fn_spy)

        # not run
        assert not fn_spy.toHaveBeenCalled()

        # run
        value = m1.value
        assert value == 1
        assert fn_spy.calledTimes == 1

        # not run
        m1.value
        assert fn_spy.calledTimes == 1

    def test_non_call_out_of_effect_with_signal(self):
        num = signal(1)

        @utils.fn
        def fn_spy():
            return num.value

        m1 = computed(fn_spy)

        # not run
        assert not fn_spy.toHaveBeenCalled()

        # run
        value = m1.value
        assert value == 1
        assert fn_spy.calledTimes == 1

        # not run
        m1.value
        assert fn_spy.calledTimes == 1

        num.value = 2
        assert fn_spy.calledTimes == 1

        value = m1.value
        assert value == 2
        assert fn_spy.calledTimes == 2

    def test_no_external_signal_dependence(self):
        num = signal(1)

        @utils.fn
        def fn_spy():
            return 1

        m1 = computed(fn_spy)

        @effect
        def _():
            m1.value
            num.value

        assert fn_spy.calledTimes == 1

        num.value = 2
        assert fn_spy.calledTimes == 1

    def test_debug_trigger(self):
        num = signal(1)

        @utils.fn
        def fn_spy():
            return num.value + 1

        @utils.fn
        def trigger_fn():
            pass

        m1 = computed(fn_spy, debug_trigger=trigger_fn)

        @effect
        def _():
            m1.value

        assert fn_spy.calledTimes == 1
        assert trigger_fn.calledTimes == 1

        num.value = 1
        assert fn_spy.calledTimes == 1
        assert trigger_fn.calledTimes == 1

        num.value = 99
        assert fn_spy.calledTimes == 2
        assert trigger_fn.calledTimes == 2

        assert m1.value == 100

    def test_debug_trigger_decorator(self):
        num = signal(1)

        @utils.fn
        def trigger_fn():
            pass

        @computed(debug_trigger=trigger_fn)
        def m1():
            return num.value + 1

        @effect
        def _():
            m1()

        assert trigger_fn.calledTimes == 1

        num.value = 1
        assert trigger_fn.calledTimes == 1

        num.value = 99
        assert trigger_fn.calledTimes == 2

        assert m1() == 100
