from typing import List
from signe import createSignal, on
import utils
from typing_extensions import Literal


class Test_on:
    def test_basic(self):
        dummy1 = dummy2 = None
        num1, set_num1 = createSignal(1)
        num2, set_num2 = createSignal(2)

        @utils.fn
        def fn_spy():
            nonlocal dummy1, dummy2
            dummy1 = num1()
            dummy2 = num2()

        on(num1, fn_spy)

        assert fn_spy.calledTimes == 1
        assert dummy1 == 1
        assert dummy2 == 2

        set_num2(99)

        assert fn_spy.calledTimes == 1
        assert dummy1 == 1
        assert dummy2 == 2

        set_num1(100)
        assert fn_spy.calledTimes == 2
        assert dummy1 == 100
        assert dummy2 == 99

    def test_onchanges(self):
        dummy1 = dummy2 = None
        num1, set_num1 = createSignal(1)
        num2, set_num2 = createSignal(2)

        @utils.fn
        def fn_spy():
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

    def test_watch_state(self):
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

        @on([num1, num2])
        def _on2(s1, s2):
            if run_state_on2.time == 0:
                assert s1.previous is None
                assert s1.current == 1
                assert s2.previous is None
                assert s2.current == 2

            if run_state_on2.time == 1:
                assert s1.previous == 1
                assert s1.current == 666
                assert s2.previous is None
                assert s2.current == 2

            if run_state_on2.time == 2:
                assert s1.previous == 1
                assert s1.current == 666
                assert s2.previous == 2
                assert s2.current == 666

            run_state_on2.next_state()

        set_num1(666)

        set_num2(666)
