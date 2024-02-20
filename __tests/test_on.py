from signe import signal, on, computed, batch, reactive
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
        num1 = signal(1)
        num2 = signal(2)

        @utils.fn
        def fn_spy(*args):
            nonlocal dummy1, dummy2
            dummy1 = num1.value
            dummy2 = num2.value

        on(num1, fn_spy, onchanges=True)

        assert fn_spy.calledTimes == 0
        assert dummy1 is None
        assert dummy2 is None

        num2.value = 99

        assert fn_spy.calledTimes == 0
        assert dummy1 is None
        assert dummy2 is None

        num1.value = 100
        assert fn_spy.calledTimes == 1
        assert dummy1 == 100
        assert dummy2 == 99

    def test_watch_on_reactive_by_list(self):
        dummy = []

        data = reactive([1, 2, 3, 4])
        s = signal(1)

        @on(lambda: data, deep=True)
        def _():
            dummy.append(data[0])
            s.value

        assert dummy == [1]
        data[0] = 99
        s.value = 99
        assert dummy == [1, 99]

    def test_watch_on_reactive_by_dict(self):
        dummy = []

        data = reactive({"x": 1, "y": 2})
        s = signal(1)

        @on(lambda: data, deep=True)
        def _():
            dummy.append(data["x"])
            s.value

        assert dummy == [1]
        data["x"] = 99
        s.value = 99
        assert dummy == [1, 99]

    def test_watch_on_reactive_with_deep_mode(self):
        dummy = []

        data = reactive(
            [
                {"name": "n1", "age": 10},
                {"name": "n2", "age": 20},
                {"name": "n3", "age": 30},
            ]
        )

        @on(lambda: data, deep=True)
        def _():
            dummy.append(data[0]["age"])

        assert dummy == [10]
        data[0]["age"] = 99
        assert dummy == [10, 99]

    def test_watch_on_reactive_by_class(self):
        dummy = []

        class Model:
            def __init__(self) -> None:
                self.x = 1
                self.y = 2

            def inc(self):
                pass

        data = reactive(Model())
        s = signal(1)

        @on(lambda: data, deep=True)
        def _():
            dummy.append(data.x)
            s.value

        assert dummy == [1]
        data.x = 99
        s.value = 99
        assert dummy == [1, 99]

    def test_should_executed_twice(self):
        result = []
        num1 = signal(1)
        num2 = signal(2)

        cp_total = computed(lambda: num1.value + num2.value)

        @on([num1, num2, cp_total])
        def _on2():
            result.append(cp_total.value)

        # change 1
        @batch
        def _():
            num1.value = 666
            num2.value = 666

        assert result == [3, 666 + 666]

    def test_watch_state_by_batch(self):
        class RunState:
            def __init__(self, time: int) -> None:
                self._time = time

            def next_state(self):
                self._time += 1

            @property
            def time(self):
                return self._time

        num1 = signal(1, debug_name="num1")
        num2 = signal(2)

        @computed(debug_name="cp tota")
        def cp_total():
            return num1.value + num2.value

        run_state_on1 = RunState(1)

        @on(num1, onchanges=True, effect_kws={"debug_name": "on1"})
        def _on1(s1):
            if run_state_on1.time == 1:
                assert s1.previous == 1
                assert s1.current == 666

            if run_state_on1.time == 2:
                assert s1.previous == 666
                assert s1.current == 999

            run_state_on1.next_state()

        run_state_on2 = RunState(0)

        @on([num1, num2, cp_total], effect_kws={"debug_name": "on2"})
        def _on2(s1, s2, s3):
            if run_state_on2.time == 0:
                assert s1.previous is None
                assert s1.current == 1
                assert s2.previous is None
                assert s2.current == 2
                assert s3.previous is None
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
            num1.value = 666
            num2.value = 666

        # change 2
        num1.value = 999

    def test_ref_value_output_reactive(self):
        records_len = []
        records_age = []

        records_age_without_deep = []

        data = signal(
            [
                {"name": "n1", "age": 10},
                {"name": "n2", "age": 20},
                {"name": "n3", "age": 30},
            ]
        )

        @on(data, deep=True)
        def _():
            records_len.append(len(data.value))
            records_age.append(data.value[1]["age"])

        # deep=False
        @on(data)
        def _():
            records_age_without_deep.append(data.value[1]["age"])

        assert records_len == [3]
        assert records_age == [20]
        assert records_age_without_deep == [20]
        data.value.append({"name": "n4", "age": 40})
        assert records_len == [3, 4]
        assert records_age == [20, 20]
        assert records_age_without_deep == [20]

        data.value[1]["age"] = 99
        assert records_len == [3, 4, 4]
        assert records_age == [20, 20, 99]
        assert records_age_without_deep == [20]

        #
        data.value = [
            {"name": "n1", "age": 10},
            {"name": "n2", "age": 666},
        ]

        assert records_age == [20, 20, 99, 666]
        assert records_len == [3, 4, 4, 2]
        assert records_age_without_deep == [20, 666]

    def test_ref_value_dynamic_addition_list(self):
        records = []
        records_calc = []

        data = signal([])

        @on(data, deep=True)
        def _():
            records.append(len(data.value))
            records_calc.append(sum(r["age"] for r in data.value))

        assert records == [0]
        assert records_calc == [0]

        data.value.extend(
            [
                {"name": "n1", "age": 10},
                {"name": "n2", "age": 20},
                {"name": "n3", "age": 30},
            ]
        )

        assert records == [0, 3]
        assert records_calc == [0, 60]

        data.value[0]["age"] = 66
        assert records_calc == [0, 60, 66 + 20 + 30]
