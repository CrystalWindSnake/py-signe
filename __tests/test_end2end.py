import _imports
import pytest
import utils
from signe import createSignal, effect, computed, cleanup, createReactive, batch


class Test_signal_case:
    def test_memo_run_when_get_value(self):
        num, set_num = createSignal(1)

        @utils.fn
        def fn_spy():
            return num() + 1

        m1 = computed(fn_spy)

        # not run
        assert not fn_spy.toHaveBeenCalled()

        value = m1()
        assert value == 2
        assert fn_spy.calledTimes == 1

    def test_run_effect_once(self):
        num, set_num = createSignal(1)

        @computed
        def plus1():
            return num() + 1

        @computed
        def plus10():
            return num() + 10

        dummy = None

        @utils.fn
        def fn_spy():
            nonlocal dummy
            dummy = plus1() + plus10()

        effect(fn_spy)

        assert fn_spy.calledTimes == 1
        assert dummy == 13

        set_num(100)
        assert fn_spy.calledTimes == 2
        assert dummy == (101 + 110)

    def test_cycle_effect(self):
        num, set_num = createSignal(1)

        dummy = None

        @utils.fn
        def fn_spy():
            nonlocal dummy
            set_num(99)
            dummy = num()

        effect(fn_spy)

        assert fn_spy.calledTimes == 1
        assert num() == 99

        set_num(555)
        assert fn_spy.calledTimes == 2
        assert dummy == 99

    def test_batch_(self):
        num1, set_num1 = createSignal(1)
        num2, set_num2 = createSignal(10)

        dummy = None

        @utils.fn
        def fn_spy():
            nonlocal dummy
            dummy = num1() + num2()

        effect(fn_spy)

        assert fn_spy.calledTimes == 1
        assert dummy == 11

        @batch
        def _():
            set_num1(50)
            set_num2(100)

            assert num1() == 1
            assert num2() == 10

            assert fn_spy.calledTimes == 1
            assert dummy == 11

        assert fn_spy.calledTimes == 2
        assert dummy == 150

    def test_cleanup_not_trigger_when_init(self):
        num, set_num = createSignal(1)
        dummy = None

        @utils.fn
        def cleanup_spy():
            pass

        @effect
        def _():
            nonlocal dummy
            cleanup(cleanup_spy)
            dummy = num()

        assert cleanup_spy.calledTimes == 0

        set_num(99)

        assert cleanup_spy.calledTimes == 1

    def test_cleanup_should_trigger_condition(self):
        cond, set_cond = createSignal(True)

        @utils.fn
        def cleanup_spy():
            pass

        @effect
        def _():
            if cond():
                cleanup(cleanup_spy)

        assert cleanup_spy.calledTimes == 0

        set_cond(False)

        assert cleanup_spy.calledTimes == 1

    def test_todos(self):
        todos = createReactive(
            [
                {"name": "事项1", "done": False},
                {"name": "事项2", "done": False},
                {"name": "事项3", "done": False},
            ]
        )

        dummy_total = None
        dummy_show = None

        @utils.fn
        def total_spy():
            nonlocal dummy_total
            dummy_total = sum(1 for item in todos if item["done"])
            return dummy_total

        total = computed(total_spy)

        @utils.fn
        def show_spy():
            nonlocal dummy_show
            dummy_show = total()

        effect(show_spy)

        assert total_spy.calledTimes == 1
        assert show_spy.calledTimes == 1

        assert dummy_total == 0
        assert dummy_show == 0

        todos[0]["done"] = True
        assert total_spy.calledTimes == 2
        assert show_spy.calledTimes == 2

        assert dummy_total == 1
        assert dummy_show == 1

        todos[0]["done"] = False
        assert total_spy.calledTimes == 3
        assert show_spy.calledTimes == 3

        assert dummy_total == 0
        assert dummy_show == 0

    @utils.mark_todo
    def test_cycle_chain_effect(self):
        num1, set_num1 = createSignal(1)
        num2, set_num2 = createSignal(0)

        dummy1 = dummy2 = None

        @utils.fn
        def fn_spy1():
            nonlocal dummy1
            set_num2(num1() + 1)
            dummy1 = num1()

        effect(fn_spy1)

        @utils.fn
        def fn_spy2():
            nonlocal dummy2
            set_num1(lambda x: x + 1)
            dummy2 = num2()

        effect(fn_spy2)

        assert fn_spy1.calledTimes == 2
        assert fn_spy2.calledTimes == 1

        assert dummy1 == 2
        assert dummy2 == 3

        set_num1(100)
        assert fn_spy1.calledTimes == 3
        assert fn_spy2.calledTimes == 2

        assert dummy1 == 102
        assert dummy2 == 101
