from dataclasses import dataclass
import _imports
import pytest
import utils

from signe.core import reactive, computed, effect, on, batch, signal


class Test_base_case:
    def test_should_observe_class_method_invocations(self):
        class Model:
            def __init__(self) -> None:
                self.calledTimes = 0

            def inc(self):
                self.calledTimes += 1

        model = reactive(Model())
        dummy = None

        @effect
        def _():
            nonlocal dummy
            dummy = model.calledTimes

        assert dummy == 0
        model.inc()
        assert dummy == 1

    def test_dataclass(self):
        dummy = []

        @dataclass
        class T:
            name: str
            age: int

            def inc_agg(self, num: int):
                self.age += num

        data = reactive(
            [
                T("t1", 10),
                T("t2", 20),
                T("t3", 30),
                T("t4", 40),
            ]
        )

        @computed
        def cp1():
            return sum(t.age for t in data)

        x = cp1.value

        assert x == 100

        @effect
        def _():
            dummy.append(cp1.value)

        assert dummy == [100]
        data[0].inc_agg(99)
        assert dummy == [100, 199]

    def test_isinstance_method_with_args(self):
        dummy = []

        @dataclass
        class T:
            name: str
            age: int

            def inc_agg(self, num: int):
                self.age += num

        data = reactive(
            [
                T("t1", 10),
                T("t2", 20),
                T("t3", 30),
                T("t4", 40),
            ]
        )

        @computed
        def cp1():
            return sum(t.age for t in data)

        x = cp1.value

        assert x == 100

        @effect
        def _():
            dummy.append(cp1.value)

        assert dummy == [100]
        data[0].inc_agg(99)
        assert dummy == [100, 199]

    def test_ref_value_output_reactive(self):
        dummy = []

        data = signal(
            [
                {"name": "n1", "age": 10},
                {"name": "n2", "age": 20},
                {"name": "n3", "age": 30},
            ]
        )

        @effect
        def _():
            dummy.append(len(data.value))

        assert dummy == [3], f"{dummy=}"
        data.value.append({"name": "n4", "age": 40})
        assert dummy == [3, 4], f"{dummy=}"
