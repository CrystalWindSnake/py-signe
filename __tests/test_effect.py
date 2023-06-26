import json
import _imports
import pytest
from signe import createReactive, effect, computed
import utils
from typing import Callable
import math


class Test_effect_basic:
    def test_run_once(self):
        fn_spy = utils.fn()

        effect(fn_spy)
        assert fn_spy.calledTimes == 1

    def test_observe_basic_prop(self):
        dummy = None
        obj = createReactive({"num": 0})

        @effect
        def _():
            nonlocal dummy
            dummy = obj["num"]

        assert dummy == 0
        obj["num"] = 99
        assert dummy == 99

    def test_observe_multiple_prop(self):
        dummy = None
        obj = createReactive({"num1": 0, "num2": 0})

        @effect
        def _():
            nonlocal dummy
            dummy = obj["num1"] + obj["num1"] + obj["num2"]

        assert dummy == 0

        obj["num1"] = 7
        obj["num2"] = 7
        assert dummy == 21

    def test_handle_multiple_effects(self):
        dummy1 = None
        dummy2 = None
        obj = createReactive({"num": 0})

        @effect
        def _():
            nonlocal dummy1
            dummy1 = obj["num"]

        @effect
        def _():
            nonlocal dummy2
            dummy2 = obj["num"]

        assert dummy1 == 0
        assert dummy2 == 0

        obj["num"] += 1

        assert dummy1 == 1
        assert dummy2 == 1

    def test_observe_nested_props(self):
        dummy = None
        obj = createReactive({"nested": {"num": 0}})

        @effect
        def _():
            nonlocal dummy
            dummy = obj["nested"]["num"]

        assert dummy == 0

        obj["nested"]["num"] = 99

        assert dummy == 99

    def test_observe_del_operations(self):
        dummy = None
        obj = createReactive({"prop": "value"})

        @effect
        def _():
            nonlocal dummy

            if "prop" in obj:
                dummy = obj["prop"]
            else:
                dummy = None

        assert dummy == "value"

        del obj["prop"]

        assert dummy is None

    def test_observe_in_operations(self):
        dummy = None
        obj = createReactive({"prop": "value"})

        @effect
        def _():
            nonlocal dummy
            dummy = "prop" in obj

        assert dummy == True

        del obj["prop"]
        assert dummy == False

        obj["prop"] = "new value"
        assert dummy == True

    def test_observe_func_call_chains(self):
        dummy = None
        obj = createReactive({"num": 0})

        def getNum():
            return obj["num"]

        @effect
        def _():
            nonlocal dummy
            dummy = getNum()

        assert dummy == 0

        obj["num"] = 99
        assert dummy == 99

    def test_observe_iter(self):
        dummy = None
        obj = createReactive(["hello"])

        @effect
        def _():
            nonlocal dummy
            dummy = " ".join(obj)

        assert dummy == "hello"

        obj.append("world")
        assert dummy == "hello world"

        obj.pop(0)
        assert dummy == "world"

    def test_observe_with_keys(self):
        dummy = None
        obj = createReactive({"num": 0})

        @effect
        def _():
            nonlocal dummy
            for key in obj.keys():
                dummy = obj[key]

        assert dummy == 0
        obj["num"] = 99
        assert dummy == 99

    @utils.mark_todo
    def test_observe_func_valued_prop(self):
        def oldFunc():
            pass

        def newFunc():
            pass

        dummy = None
        obj = createReactive({"func": oldFunc})

        @effect
        def _():
            nonlocal dummy
            dummy = obj["func"]

        assert dummy is oldFunc
        obj["func"] = newFunc
        assert dummy is newFunc

    def test_observe_chained_getter_relying_on_dict(self):
        def get_a():
            return obj["a"]

        dummy = None
        obj = createReactive({"a": 1, "b": get_a})

        @effect
        def _():
            nonlocal dummy
            dummy = obj["b"]()

        assert dummy == 1

        obj["a"] += 1

        assert dummy == 2

    def test_not_observe_set_oper_without_value_change(self):
        hasDummy = getDummy = None

        obj = createReactive({"prop": "value"})

        @utils.fn
        def getSpy():
            nonlocal getDummy
            getDummy = obj["prop"]

        @utils.fn
        def hasSpy():
            nonlocal hasDummy
            hasDummy = "prop" in obj

        effect(getSpy)
        effect(hasSpy)

        assert getDummy == "value"
        assert hasDummy == True

        obj["prop"] = "value"

        assert getSpy.calledTimes == 1
        assert hasSpy.calledTimes == 1

        assert getDummy == "value"
        assert hasDummy == True

    @utils.mark_todo
    def test_not_observe_raw(self):
        dummy = None
        obj = createReactive({"prop": "value"})

        @effect
        def _():
            nonlocal dummy
            dummy = toRaw(obj)["prop"]

        assert dummy == "value"
        obj["prop"] = "new value"
        assert dummy == "value"

    @utils.mark_todo
    def test_not_triggered_by_raw(self):
        dummy = None
        obj = createReactive({"prop": "value"})

        @effect
        def _():
            nonlocal dummy
            dummy = obj["prop"]

        assert dummy == "value"
        toRaw(obj)["prop"] = "new value"
        assert dummy == "value"

    @utils.mark_todo
    def test_avoid_implicit_infinite_recursive_loops_with_itself(self):
        counter = createReactive({"num": 0})

        @utils.fn
        def counter_spy():
            counter["num"] += 1

        effect(counter_spy)

        assert counter["num"] == 1

        assert counter_spy.calledTimes == 1

        counter["num"] = 4
        assert counter["num"] == 5
        assert counter_spy.calledTimes == 2

    @utils.mark_todo
    def test_allow_explicitly_recursive_raw_function_loops(self):
        counter = createReactive({"num": 0})

        @utils.fn
        def num_spy():
            counter["num"] += 1
            if counter["num"] < 10:
                num_spy()

        effect(num_spy)

        assert counter["num"] == 10

        assert num_spy.calledTimes == 10

    def test_avoid_infinite_loops_with_other_effects(self):
        nums = createReactive({"num1": 0, "num2": 1})

        @utils.fn
        def spy1():
            nums["num1"] = nums["num2"]

        @utils.fn
        def spy2():
            nums["num2"] = nums["num1"]

        effect(spy1)
        effect(spy2)

        assert nums["num1"] == 1
        assert nums["num2"] == 1

        assert spy1.calledTimes == 1
        assert spy2.calledTimes == 1

        nums["num1"] = 4

        assert nums["num1"] == 4
        assert nums["num2"] == 4

        assert spy1.calledTimes == 2
        assert spy2.calledTimes == 2

        nums["num1"] = 10

        assert nums["num1"] == 10
        assert nums["num2"] == 10

        assert spy1.calledTimes == 3
        assert spy2.calledTimes == 3

    def test_return__new_reactive_version_of_the_function(self):
        def greet():
            return "hello world"

        effect1 = effect(greet)
        effect2 = effect(greet)

        assert isinstance(effect1, Callable)
        assert isinstance(effect2, Callable)

        assert effect1 is not greet
        assert effect1 is not effect2

    def test_discover_new_branches_while_running_automatically(self):
        dummy = None
        obj = createReactive({"prop": "value", "run": False})

        @utils.fn
        def conditionalSpy():
            nonlocal dummy
            dummy = obj["prop"] if obj["run"] else "other"

        effect(conditionalSpy)

        assert dummy == "other"
        assert conditionalSpy.calledTimes == 1

        obj["prop"] = "hi"
        assert dummy == "other"
        assert conditionalSpy.calledTimes == 1

        obj["run"] = True
        assert dummy == "hi"
        assert conditionalSpy.calledTimes == 2

        obj["prop"] = "world"
        assert dummy == "world"
        assert conditionalSpy.calledTimes == 3

    @utils.mark_todo
    def test_discover_new_branches_when_running_manually(self):
        dummy = None
        run = False
        obj = createReactive({"prop": "value"})

        @effect
        def runner():
            nonlocal dummy
            dummy = obj["prop"] if run else "other"

        assert dummy == "other"
        runner()
        assert dummy == "other"
        run = True
        runner()
        assert dummy == "value"
        obj["prop"] = "world"
        assert dummy == "world"

    def test_not_be_triggered_by_mutating_a_property_which_is_used_in_an_inactive_branch(
        self,
    ):
        dummy = None
        obj = createReactive({"prop": "value", "run": True})

        @utils.fn
        def conditionalSpy():
            nonlocal dummy
            dummy = obj["prop"] if obj["run"] else "other"

        effect(conditionalSpy)

        assert dummy == "value"
        assert conditionalSpy.calledTimes == 1

        obj["run"] = False
        assert dummy == "other"
        assert conditionalSpy.calledTimes == 2

        obj["prop"] = "value2"
        assert dummy == "other"
        assert conditionalSpy.calledTimes == 2

    def test_should_handle_deep_effect_recursion_using_cleanup_fallback(self):
        results = createReactive([0] * 40)
        effects = []

        for i in range(1, 40):

            def run(index):
                @effect
                def fx():
                    results[index] = results[index - 1] * 2

                effects.append({"fx": fx, "index": index})

            run(i)

        assert results[39] == 0
        results[0] = 1
        assert results[39] == math.pow(2, 39)

    @utils.mark_todo
    def test_should_register_deps_independently_during_effect_recursion(self):
        input = createReactive({"a": 1, "b": 2, "c": 0})
        output = createReactive({"fx1": 0, "fx2": 0})

        @utils.fn
        def fx1Spy():
            result = 0
            if input["c"] < 2:
                result += input["a"]

            if input["c"] > 1:
                result += input["b"]

            output["fx1"] = result

        fx1 = effect(fx1Spy)

        @utils.fn
        def fx2Spy():
            result = 0
            if input["c"] > 1:
                result += input["a"]

            if input["c"] < 3:
                result += input["b"]

            output["fx2"] = result + output["fx1"]

        fx2 = effect(fx2Spy)

        assert fx1 is not None
        assert fx2 is not None

        assert output["fx1"] == 1
        assert output["fx2"] == (2 + 1)
        assert fx1Spy.calledTimes == 1
        assert fx2Spy.calledTimes == 1

        fx1Spy.mockClear()
        fx2Spy.mockClear()
        input["b"] = 3
        assert output["fx1"] == 1
        assert output["fx2"] == (3 + 1)
        assert fx1Spy.calledTimes == 0
        assert fx2Spy.calledTimes == 1

        fx1Spy.mockClear()
        fx2Spy.mockClear()
        input["c"] = 1
        assert output["fx1"] == 1
        assert output["fx2"] == (3 + 1)
        assert fx1Spy.calledTimes == 1
        assert fx2Spy.calledTimes == 1

        fx1Spy.mockClear()
        fx2Spy.mockClear()
        input["c"] = 2
        assert output["fx1"] == 3
        assert output["fx2"] == (1 + 3 + 3)
        assert fx1Spy.calledTimes == 1
        assert fx2Spy.calledTimes == 2

        fx1Spy.mockClear()
        fx2Spy.mockClear()
        input["c"] = 3
        assert output["fx1"] == 3
        assert output["fx2"] == (1 + 3)
        assert fx1Spy.calledTimes == 1
        assert fx2Spy.calledTimes == 1

        fx1Spy.mockClear()
        fx2Spy.mockClear()
        input["a"] = 10
        assert output["fx1"] == 3
        assert output["fx2"] == (10 + 3)
        assert fx1Spy.calledTimes == 0
        assert fx2Spy.calledTimes == 1

    @utils.mark_todo
    def test_should_not_double_wrap_if_the_passed_function_is_a_effect(self):
        runner = effect(lambda: ())
        otherRunner = effect(runner)

        assert runner is not otherRunner
        assert runner.effect.fn is otherRunner.effect.fn

    def test_should_not_run_multiple_times_for_a_single_mutation(self):
        dummy = None
        obj = createReactive({})

        @utils.fn
        def fnSpy():
            nonlocal dummy
            for key in obj.keys():
                dummy = obj[key]

            if "prop" in obj:
                dummy = obj["prop"]

        effect(fnSpy)

        assert fnSpy.calledTimes == 1

        obj["prop"] = 16
        assert dummy == 16
        assert fnSpy.calledTimes == 2

    @utils.mark_todo
    def test_should_allow_nested_effects(self):
        nums = createReactive({"num1": 0, "num2": 1, "num3": 2})
        dummy = {}

        @utils.fn
        def childSpy():
            dummy["num1"] = nums["num1"]

        childeffect = effect(childSpy)

        @utils.fn
        def parentSpy():
            dummy["num2"] = nums["num2"]
            childeffect()
            dummy["num3"] = nums["num3"]

        effect(parentSpy)

        assert dummy == {"num1": 0, "num2": 1, "num3": 2}
        assert parentSpy.calledTimes == 1
        assert childSpy.calledTimes == 2

        # this should only call the childeffect
        nums["num1"] = 4
        assert dummy == {"num1": 4, "num2": 1, "num3": 2}
        assert parentSpy.calledTimes == 1
        assert childSpy.calledTimes == 3

        # this calls the parenteffect, which calls the childeffect once
        nums["num2"] = 10
        assert dummy == {"num1": 4, "num2": 10, "num3": 2}
        assert parentSpy.calledTimes == 2
        assert childSpy.calledTimes == 4

        # this calls the parenteffect, which calls the childeffect once
        nums["num3"] = 7
        assert dummy == {"num1": 4, "num2": 10, "num3": 7}
        assert parentSpy.calledTimes == 3
        assert childSpy.calledTimes == 5

    @utils.mark_todo
    def test_should_observe_json_methods(self):
        dummy = {}
        obj = createReactive({})

        @effect
        def _():
            nonlocal dummy
            dummy = json.loads(json.dumps(obj))

        obj["a"] = 1

        assert dummy["a"] == 1

    @utils.mark_todo
    def test_should_observe_class_method_invocations(self):
        class Model:
            def __init__(self) -> None:
                self.calledTimes = 0

            def inc(self):
                self.calledTimes += 1

        model = createReactive(Model())
        dummy = None

        @effect
        def _():
            nonlocal dummy
            dummy = model.calledTimes

        assert dummy == 0
        model.inc()
        assert dummy == 1

    def test_lazy(self):
        obj = createReactive({"foo": 1})
        dummy = None

        @computed
        def runner():
            nonlocal dummy
            dummy = obj["foo"]
            return dummy

        assert dummy is None

        assert runner() == 1
        assert dummy == 1

        obj["foo"] = 2
        assert dummy == 2

    @utils.mark_todo
    def test_scheduler(self):
        assert False, "todo"

    @utils.mark_todo
    def test_events_onTrack(self):
        assert False, "todo"

    @utils.mark_todo
    def test_events_onTrigger(self):
        assert False, "todo"

    @utils.mark_todo
    def test_stop(self):
        dummy = None
        obj = createReactive({"prop": 1})

        @effect
        def runner():
            nonlocal dummy
            dummy = obj["prop"]

        obj["prop"] = 2
        assert dummy == 2
        stop(runner)

        obj["prop"] = 3
        assert dummy == 2

        # stopped effect should still be manually callable
        runner()
        assert dummy == 3
