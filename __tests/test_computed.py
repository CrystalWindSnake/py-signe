import asyncio
from . import utils
from signe import signal, computed, effect, async_computed


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

    def test_should_trigger_on_demand(self):
        use_s2_spy = utils.fn()
        only_s1_spy = utils.fn()

        s1 = signal(1)
        s2 = signal(2)
        use_s2 = signal(True)

        @computed
        def total():
            if use_s2.value:
                use_s2_spy()
                return s1.value + s2.value

            only_s1_spy()
            return s1.value

        @effect
        def _():
            print(total.value)

        assert use_s2_spy.calledTimes == 1
        assert only_s1_spy.calledTimes == 0

        s1.value += 1
        s2.value += 1
        assert use_s2_spy.calledTimes == 3
        assert only_s1_spy.calledTimes == 0

        use_s2.value = False
        assert use_s2_spy.calledTimes == 3
        assert only_s1_spy.calledTimes == 1

        s2.value += 1
        assert use_s2_spy.calledTimes == 3
        assert only_s1_spy.calledTimes == 1

        s1.value += 1
        assert use_s2_spy.calledTimes == 3
        assert only_s1_spy.calledTimes == 2


class Test_async_computed:
    def test_should_be_correct_order(self):
        async def main():
            dummy_orders = []
            dummy_values = []
            a = signal(1)

            @async_computed(a, init=0)
            async def test():
                dummy_orders.append("start computed")
                await asyncio.sleep(0.1)
                dummy_orders.append("end computed")
                return a.value + 1

            @effect
            def _():
                dummy_orders.append("effect start")
                dummy_values.append(test.value)

            a.value = 99
            dummy_orders.append("modify a")
            await asyncio.sleep(0.1)
            dummy_orders.append("back to main")

            await asyncio.sleep(0.2)
            assert dummy_orders == [
                "effect start",
                "modify a",
                "start computed",
                "back to main",
                "end computed",
                "effect start",
            ]

            assert dummy_values == [0, 100]

        asyncio.run(main())

    def test_should_be_immediate_run(self):
        async def main():
            dummy_orders = []
            dummy_values = []
            a = signal(1)

            @async_computed(a, init=0, onchanges=False)
            async def test():
                dummy_orders.append("start computed")
                await asyncio.sleep(0.1)
                dummy_orders.append("end computed")
                return a.value + 1

            @effect
            def _():
                dummy_orders.append("effect start")
                dummy_values.append(test.value)

            dummy_orders.append("modify a")
            await asyncio.sleep(0.1)
            dummy_orders.append("back to main")

            await asyncio.sleep(0.2)
            assert dummy_orders == [
                "effect start",
                "modify a",
                "start computed",
                "back to main",
                "end computed",
                "effect start",
            ]

            assert dummy_values == [0, 2]

        asyncio.run(main())

    def test_should_be_immediate_run_with_source_none(self):
        async def main():
            dummy_orders = []
            dummy_values = []
            a = signal(None)

            @async_computed(a, init=0, onchanges=False)
            async def test():
                dummy_orders.append("start computed")
                await asyncio.sleep(0.1)
                dummy_orders.append("end computed")
                return (a.value or 99) + 1

            @effect
            def _():
                dummy_orders.append("effect start")
                dummy_values.append(test.value)

            dummy_orders.append("modify a")
            await asyncio.sleep(0.1)
            dummy_orders.append("back to main")

            await asyncio.sleep(0.2)
            assert dummy_orders == [
                "effect start",
                "modify a",
                "start computed",
                "back to main",
                "end computed",
                "effect start",
            ]

            assert dummy_values == [0, 100]

        asyncio.run(main())
