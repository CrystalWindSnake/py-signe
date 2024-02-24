from dataclasses import dataclass
from signe import reactive, computed, effect, signal, to_raw, to_value
from . import utils


class Test_base_case:
    @utils.mark_todo
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
        data[0].age += 99
        assert dummy == [100, 199]

    @utils.mark_todo
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

    def test_dict_remove_pop(self):
        dummy = []
        data = signal({"a": 1, "b": 2})

        @effect
        def _():
            dummy.append(len(data.value))

        assert dummy == [2]
        assert data.value.pop("b") == 2
        assert dummy == [2, 1]

        data.value.clear()
        assert dummy == [2, 1, 0]

    def test_list_(self):
        spyfn = utils.fn()
        data = signal([1, 2, 3, 4])

        @effect
        def _():
            spyfn()
            for i in data.value:
                print(i)

        assert spyfn.calledTimes == 1
        data.value.reverse()
        assert spyfn.calledTimes == 2

    def test_list_pop_clear_remove(self):
        dummy = []
        data = signal([1, 2, 3, 4])

        @effect
        def _():
            dummy.append(len(data.value))

        assert dummy == [4]
        assert data.value.pop() == 4
        assert dummy == [4, 3]

        data.value.remove(1)
        assert dummy == [4, 3, 2]

        data.value.clear()
        assert dummy == [4, 3, 2, 0]

    def test_dict_in(self):
        dummy = []
        data = signal({"a": 1, "b": 2})

        @effect
        def _():
            dummy.append("a" in data.value)

        assert dummy == [True]
        assert data.value.pop("a") == 1
        assert dummy == [True, False]

    def test_list_in(self):
        dummy = []
        data = signal([1, 2])

        @effect
        def _():
            dummy.append(2 in data.value)

        assert dummy == [True]
        assert data.value.pop() == 2
        assert dummy == [True, False]

    def test_should_call_ins_method(self):
        class M:
            def __getitem__(self, i):
                return i

            def fn1(self):
                return self[0]

        data = signal(M())

        assert data.value.fn1() == 0

    def test_ref_value_output_reactive(self):
        dummy1 = []
        dummy2 = []

        data = signal(
            [
                {"name": "n1", "age": 10},
                {"name": "n2", "age": 20},
                {"name": "n3", "age": 30},
            ]
        )

        @effect
        def eff1():
            dummy1.append(len(data.value))

        @effect
        def eff2():
            dummy2.append(data.value[0]["age"])

        assert dummy1 == [3]
        assert dummy2 == [10]
        data.value.append({"name": "n4", "age": 40})
        assert dummy1 == [3, 4]
        # not trigger eff2
        assert dummy2 == [10]

        data.value[1]["age"] = 99
        # not trigger eff1 and 2
        assert dummy1 == [3, 4]
        assert dummy2 == [10]

        data.value[0]["age"] = 99
        # not trigger eff2
        assert dummy1 == [3, 4]
        assert dummy2 == [10, 99]


class Test_to_raw:
    def test_signal_list(self):
        data = [[1, 2]]
        s = signal(data)

        assert to_raw(s.value[0]) is data[0]

    def test_dict_list(self):
        data = [{}]
        s = signal(data)

        assert to_raw(s.value[0]) is data[0]

    def test_class_list(self):
        class Model:
            pass

        data = [Model()]
        s = signal(data)

        assert to_raw(s.value[0]) is data[0]

    def test_dataclass_list(self):
        @dataclass
        class Model:
            pass

        data = [Model()]
        s = signal(data)

        assert to_raw(s.value[0]) is data[0]

    def test_shallow(self):
        dummy = []

        data = signal(
            [{"name": "n1"}],
            is_shallow=True,
        )

        @effect
        def _():
            dummy.append(data.value[0]["name"])

        # no effect
        data.value[0]["name"] = "new"
        assert dummy == ["n1"]

        data.value = [{"name": "new"}]
        assert dummy == ["n1", "new"]

    @utils.mark_todo
    def test_signal_dict_trigger_by_setattr(self):
        dummy = []

        data = signal(
            [{"name": "n1"}],
        )

        @effect
        def _():
            dummy.append(data.value[0]["name"])

        setattr(data.value[0], "name", "new")
        assert dummy == ["n1", "new"]

    def test_signal_class_trigger_by_setattr(self):
        @dataclass
        class Model:
            name: str

        dummy = []

        data = signal(
            [Model("n1")],
        )

        @effect
        def _():
            dummy.append(data.value[0].name)

        setattr(data.value[0], "name", "new")
        assert dummy == ["n1", "new"]


class Test_to_value:
    def test_to_value(self):
        assert to_value(1) == 1
        assert to_value(signal(1)) == 1
        assert to_value(computed(lambda: 1)) == 1
