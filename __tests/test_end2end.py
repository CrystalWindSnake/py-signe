from . import utils
from signe import signal, effect, computed, cleanup, reactive, batch


class Test_signal_case:
    def test_should_work_fine_after_effecting_error(self):
        num1 = signal(1)

        dummy = 0

        @effect
        def error_effect():
            nonlocal dummy
            if num1.value == 99:
                raise Exception("error")

            dummy = num1.value

        try:
            num1.value = 99
        except Exception:
            pass
        finally:
            pass

        assert dummy == 1

        num2 = signal(1)

        dummy2 = 0

        @effect
        def normal_effect():
            nonlocal dummy2

            dummy2 = num2.value

        assert dummy2 == 1

        num2.value = 666
        assert dummy2 == 666

    def test_memo_run_when_get_value(self):
        num = signal(1)

        @utils.fn
        def fn_spy():
            return num.value + 1

        m1 = computed(fn_spy)

        # not run
        assert not fn_spy.toHaveBeenCalled()

        value = m1()
        assert value == 2
        assert fn_spy.calledTimes == 1

    def test_run_effect_once(self):
        num = signal(1)

        @computed
        def plus1():
            return num.value + 1

        @computed
        def plus10():
            return num.value + 10

        dummy = None

        @utils.fn
        def fn_spy():
            nonlocal dummy
            dummy = plus1() + plus10()

        effect(fn_spy)

        assert fn_spy.calledTimes == 1
        assert dummy == 13

        num.value = 100
        assert fn_spy.calledTimes == 2
        assert dummy == (101 + 110)

    def test_cycle_effect(self):
        num = signal(1)

        dummy = None

        @utils.fn
        def fn_spy():
            nonlocal dummy
            num.value = 99
            dummy = num.value

        effect(fn_spy)

        assert fn_spy.calledTimes == 1
        assert num.value == 99

        num.value = 555
        assert fn_spy.calledTimes == 2
        assert dummy == 99

    def test_batch_(self):
        num1 = signal(1)
        num2 = signal(10)

        dummy = None

        @utils.fn
        def fn_spy():
            nonlocal dummy
            dummy = num1.value + num2.value

        effect(fn_spy)

        assert fn_spy.calledTimes == 1
        assert dummy == 11

        @batch
        def _():
            num1.value = 50
            num2.value = 100

            assert num1.value == 50
            assert num2.value == 100

            assert fn_spy.calledTimes == 1
            assert dummy == 11

        assert fn_spy.calledTimes == 2
        assert dummy == 150

    def test_cleanup_not_trigger_when_init(self):
        num = signal(1)
        dummy = None

        @utils.fn
        def cleanup_spy():
            pass

        @effect
        def _():
            nonlocal dummy
            cleanup(cleanup_spy)
            dummy = num.value

        assert cleanup_spy.calledTimes == 0

        num.value = 99

        assert cleanup_spy.calledTimes == 1

    def test_cleanup_should_trigger_condition(self):
        cond = signal(True)

        @utils.fn
        def cleanup_spy():
            pass

        @effect
        def _():
            if cond.value:
                cleanup(cleanup_spy)

        assert cleanup_spy.calledTimes == 0

        cond.value = False

        assert cleanup_spy.calledTimes == 1

    def test_todos(self):
        todos = reactive(
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

        total = computed(total_spy, debug_name="total_spy")

        @utils.fn
        def show_spy():
            nonlocal dummy_show
            dummy_show = total.value

        effect(show_spy, debug_name="show_spy")

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

    def test_signal_assignment_triggere_in_effect(self):
        '''"During an execution, the signal assignment operation is triggered in method A."'''
        num = signal(0)
        get_cp_num1 = signal(99)

        @computed
        def cp_1():
            return get_cp_num1.value + 1

        @effect
        def _():
            num.value
            cp_1()

        dummy1 = None

        @utils.fn
        def spy_fn():
            nonlocal dummy1
            dummy1 = cp_1()
            num.value = 99

        effect(spy_fn)

        assert spy_fn.calledTimes == 1
        assert dummy1 == 100

        get_cp_num1.value = 10

        assert spy_fn.calledTimes == 2
        assert dummy1 == 11

    @utils.mark_todo
    def test_cycle_chain_effect(self):
        num1 = signal(1)
        num2 = signal(0)

        dummy1 = dummy2 = None

        @utils.fn
        def fn_spy1():
            nonlocal dummy1
            num2.value = num1.value + 1
            dummy1 = num1.value

        effect(fn_spy1)

        @utils.fn
        def fn_spy2():
            nonlocal dummy2
            num1.value += 1
            # set_num1(lambda x: x + 1)
            dummy2 = num2.value

        effect(fn_spy2)

        assert fn_spy1.calledTimes == 2
        assert fn_spy2.calledTimes == 1

        assert dummy1 == 2
        assert dummy2 == 3

        num1.value = 100
        assert fn_spy1.calledTimes == 3
        assert fn_spy2.calledTimes == 2

        assert dummy1 == 102
        assert dummy2 == 101
