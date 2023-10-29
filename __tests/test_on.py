import json
import _imports
import pytest
from signe import createSignal, effect, on
import utils
from typing import Callable
import math


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
