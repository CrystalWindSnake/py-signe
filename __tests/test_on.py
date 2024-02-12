from typing import List
from signe.model import signal, on, computed
import utils


class Test_on:
    def test_basic(self):
        dummy1 = dummy2 = None
        num1 = signal(1)
        num2 = signal(2)

        @utils.fn
        def fn_spy(*args):
            nonlocal dummy1, dummy2
            dummy1 = num1.value
            dummy2 = num2.value

        on(num1, fn_spy)

        assert fn_spy.calledTimes == 1
        assert dummy1 == 1
        assert dummy2 == 2

        num2.value = 99

        assert fn_spy.calledTimes == 1
        assert dummy1 == 1
        assert dummy2 == 2

        num1.value = 100
        assert fn_spy.calledTimes == 2
        assert dummy1 == 100
        assert dummy2 == 99

    def test_basic_with_watchState(self):
        a = signal(1)

        @computed
        def cp1():
            return a.value + 1

        @utils.fn
        def fn_spy(state):
            pass

        on(cp1, fn_spy)

        assert fn_spy.calledTimes == 1
        a.value += 1
        assert fn_spy.calledTimes == 2

    def test_onchanges(self):
        dummy1 = dummy2 = None
        num1, set_num1 = createSignal(1)
        num2, set_num2 = createSignal(2)

        @utils.fn
        def fn_spy(*args):
            nonlocal dummy1, dummy2
            dummy1 = num1()
            dummy2 = num2()

        on(num1, fn_spy, onchanges=True)

        assert fn_spy.calledTimes == 0
        assert dummy1 is None
        assert dummy2 is None

        set_num2(99)

        assert fn_spy.calledTimes == 0
        assert dummy1 is None
        assert dummy2 is None

        set_num1(100)
        assert fn_spy.calledTimes == 1
        assert dummy1 == 100
        assert dummy2 == 99

    def test_should_executed_twice(self):
        result = []
        num1, set_num1 = createSignal(1)
        num2, set_num2 = createSignal(2)

        cp_total = computed(lambda: num1() + num2())

        @on([num1, num2, cp_total])
        def _on2():
            result.append(cp_total())

        # change 1
        @batch
        def _():
            set_num1(666)
            set_num2(666)

        assert result == [3, 666 + 666]

    def test_watch_state_by_batch(self):
        from signe import createSignal, on, batch, computed

        class RunState:
            def __init__(self, time: int) -> None:
                self._time = time

            def next_state(self):
                self._time += 1

            @property
            def time(self):
                return self._time

        num1, set_num1 = createSignal(1)
        num2, set_num2 = createSignal(2)

        cp_total = computed(lambda: num1() + num2())

        run_state_on1 = RunState(1)

        @on(num1, onchanges=True)
        def _on1(s1):
            if run_state_on1.time == 1:
                assert s1.previous == 1
                assert s1.current == 666

            if run_state_on1.time == 2:
                assert s1.previous == 666
                assert s1.current == 999

            run_state_on1.next_state()

        run_state_on2 = RunState(0)

        @on([num1, num2, cp_total])
        def _on2(s1, s2, s3):
            if run_state_on2.time == 0:
                assert s1.previous == 1
                assert s1.current == 1
                assert s2.previous == 2
                assert s2.current == 2
                assert s3.previous == 3
                assert s3.current == 3

            if run_state_on2.time == 1:
                assert s1.previous == 1
                assert s1.current == 666
                assert s2.previous == 2
                assert s2.current == 666
                assert s3.previous == 3
                assert s3.current == 666 + 666

            if run_state_on2.time == 2:
                assert s1.previous == 666
                assert s1.current == 999
                assert s2.previous == 666
                assert s2.current == 666
                assert s3.previous == 666 + 666
                assert s3.current == 666 + 999

            run_state_on2.next_state()

        # change 1
        @batch
        def _():
            set_num1(666)
            set_num2(666)

        # change 2
        set_num1(999)
