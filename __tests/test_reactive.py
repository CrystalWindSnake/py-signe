from copy import deepcopy
from dataclasses import dataclass
from signe import (
    reactive,
    computed,
    effect,
    signal,
    to_raw,
    to_value,
    is_signal,
    async_computed,
)
from signe.core.reactive import NoProxy
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

    def test_dict_pop_by_print(self):
        raw_data = {"a": 1, "b": 2, "c": 3}
        data = signal(raw_data)

        collects = []

        @effect
        def _():
            print(data.value)
            collects.append(deepcopy(raw_data))

        # not trigger effect because no change
        a = data.value.pop("x", 10)
        assert a == 10
        data.value.pop("b")
        data.value.pop("c")

        assert collects == [{"a": 1, "b": 2, "c": 3}, {"a": 1, "c": 3}, {"a": 1}]

    def test_to_str_track(self):
        spy_list = utils.fn()
        spy_dict = utils.fn()
        spy_deep = utils.fn()

        list_data = signal([1, 2, 3])
        dict_data = signal({"a": 1, "b": 2})
        deep_data = signal({"a": {"b": {"c": [{"e": 1}], "d": 2}}})

        @effect
        def _():
            spy_list()
            print(list_data.value)

        @effect
        def _():
            spy_dict()
            print(dict_data.value)

        @effect
        def _():
            spy_deep()
            print(deep_data.value)

        list_data.value[0] = 66
        list_data.value[1] = 2  # not trigger

        assert spy_list.calledTimes == 2

        dict_data.value["a"] = 66
        dict_data.value["b"] = 2  # not trigger
        assert spy_dict.calledTimes == 2

        deep_data.value["a"]["b"]["c"][0]["e"] = 66
        deep_data.value["a"]["b"]["d"] = 2  # not trigger
        assert spy_deep.calledTimes == 2

        list_data.value = [10, 20, 30]
        assert spy_list.calledTimes == 3

        dict_data.value = {"c": 99}
        assert spy_dict.calledTimes == 3

    def test_list_sort(self):
        spy_for = utils.fn()
        spy_len = utils.fn()
        spy_get0 = utils.fn()
        spy_get1 = utils.fn()
        spy_print_value = utils.fn()

        data = signal([3, 2, 1])

        # should trigger
        @effect
        def _():
            spy_for()
            for i in data.value:
                print(i)

        # should not trigger
        @effect
        def _():
            spy_len()
            print(len(data.value))

        # should trigger
        @effect
        def _():
            spy_get0()
            print(data.value[0])

        # should not trigger
        @effect
        def _():
            spy_get1()
            print(data.value[1])

        # should  trigger
        @effect
        def _():
            spy_print_value()
            print(data.value)

        data.value.sort()

        assert spy_for.calledTimes == 2
        assert spy_len.calledTimes == 1
        assert spy_get0.calledTimes == 2
        assert spy_get1.calledTimes == 1
        assert spy_print_value.calledTimes == 2

    def test_list_reverse(self):
        spy_for = utils.fn()
        spy_len = utils.fn()
        spy_get0 = utils.fn()
        spy_get1 = utils.fn()
        spy_print_value = utils.fn()

        data = signal([1, 2, 3])

        # should trigger
        @effect
        def _():
            spy_for()
            for i in data.value:
                print(i)

        # should not trigger
        @effect
        def _():
            spy_len()
            print(len(data.value))

        # should trigger
        @effect
        def _():
            spy_get0()
            print(data.value[0])

        # should not trigger
        @effect
        def _():
            spy_get1()
            print(data.value[1])

        # should  trigger
        @effect
        def _():
            spy_print_value()
            print(data.value)

        data.value.reverse()

        assert spy_for.calledTimes == 2
        assert spy_len.calledTimes == 1
        assert spy_get0.calledTimes == 2
        assert spy_get1.calledTimes == 1
        assert spy_print_value.calledTimes == 2

    def test_list_reverse_by_dict(self):
        spy_get0 = utils.fn()
        spy_get1 = utils.fn()

        data = signal(
            [
                {"v": 1},
                {"v": 2},
                {"v": 3},
            ]
        )

        # should trigger
        @effect
        def _():
            spy_get0()
            print(data.value[0]["v"])

        # should not trigger
        @effect
        def _():
            spy_get1()
            print(data.value[1]["v"])

        data.value.reverse()

        assert spy_get0.calledTimes == 2
        assert spy_get1.calledTimes == 1

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

    def test_list_slice(self):
        dummy = []

        data = signal(["1", "2", "3", "4", "5", "6"])

        # should trigger
        @effect
        def _():
            dummy.append(",".join(data.value[1:-2]))

        assert dummy == ["2,3,4"]
        data.value[1] = "99"

        assert dummy == ["2,3,4", "99,3,4"]

        data.value[0] = "99"
        assert dummy == ["2,3,4", "99,3,4", "99,3,4"]

        data.value.append("7")
        assert dummy == ["2,3,4", "99,3,4", "99,3,4", "99,3,4,5"]

        data.value.insert(0, "0")
        assert dummy == ["2,3,4", "99,3,4", "99,3,4", "99,3,4,5", "99,99,3,4,5"]

    def test_list_append(self):
        dummy = []

        data = signal(["1", "2", "3"])

        # should trigger
        @effect
        def _():
            dummy.append(",".join(data.value))

        assert dummy == ["1,2,3"]
        data.value.append("4")

        assert dummy == ["1,2,3", "1,2,3,4"]

    def test_list_insert(self):
        dummy = []

        data = signal(["1", "2", "3"])

        # should trigger
        @effect
        def _():
            dummy.append(",".join(data.value))

        assert dummy == ["1,2,3"]
        data.value.insert(1, "66")

        assert dummy == ["1,2,3", "1,66,2,3"]

    def test_list_del_item(self):
        dummy = []

        data = signal(["1", "2", "3"])

        @effect
        def _():
            dummy.append(",".join(data.value))

        assert dummy == ["1,2,3"]
        del data.value[1]

        assert dummy == ["1,2,3", "1,3"]

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

    def test_should_return_ref_directly_from_reactive(self):
        s = signal(1)
        data = {"s": s}

        assert data["s"] is s

    def test_should_same_proxy_from_getting_same_empty_list(self):
        data = signal({"rows": []})

        first = data.value["rows"]
        second = data.value["rows"]
        assert first is second

    def test_no_proxy(self):
        class Model(NoProxy):
            pass

        m = Model()
        data = signal([m], is_shallow=False)

        assert isinstance(data.value[0], Model)
        assert data.value[0] is m


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
        s = signal(1)
        assert to_value(1) == 1
        assert to_value(s) == 1
        assert to_value(computed(lambda: 1)) == 1
        assert to_value(lambda: s.value + 1) == 2


class Test_is_signal:
    def test_base(self):
        s = signal(1)

        @computed
        def cp():
            return s.value + 1

        @async_computed(s)
        async def cp1():
            return s.value + 1

        assert is_signal(s)
        assert is_signal(cp)
        assert is_signal(cp1)
