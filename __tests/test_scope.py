from . import utils
from signe import signal, effect, computed, scope, on
import gc
import weakref
import logging

logging.basicConfig(level=logging.DEBUG)
mylogger = logging.getLogger()


def log_refs(obj):
    refs = gc.get_referrers(obj)
    mylogger.warning(f"====[{refs}]")


class RefChecker:
    def __init__(self) -> None:
        @utils.fn
        def spy(*args):
            print("spy")

        self._spy = spy

        self._wrefs = []

    def collect(self, obj):
        self._wrefs.append(weakref.ref(obj, self._spy))

    @property
    def calledTimes(self):
        return self._spy.calledTimes


def test_base():
    parent_scope = scope()

    @parent_scope.run
    def _():
        child_scope1 = scope()

        child_scope2 = scope()

        child_scope1.dispose()
        child_scope2.dispose()

    parent_scope.dispose()


def test_should_release_signal():
    rc = RefChecker()

    def fn():
        num = signal(1)
        rc.collect(num)

    fn()

    gc.collect()
    assert rc.calledTimes == 1


def test_should_release_with_computed():
    computed_rc = RefChecker()
    effect_rc = RefChecker()
    on_rc = RefChecker()

    num = signal(1)

    def temp_run(x):
        current_scope = scope()

        @current_scope.run
        def _():
            @computed
            def cp_1():
                print(x)
                return num.value

            computed_rc.collect(cp_1)

            @effect
            def eff1():
                pass
                cp_1.value

            effect_rc.collect(eff1)

            @on
            def on_spy():
                pass
                cp_1.value

            on_rc.collect(on_spy)

        current_scope.dispose()

    temp_run(1)
    temp_run(2)
    temp_run(3)
    temp_run(4)
    gc.collect()
    assert computed_rc.calledTimes == 4
    assert effect_rc.calledTimes == 4
    assert on_rc.calledTimes == 4


def test_should_not_release_computed_call():
    # test_should_not_release_computed_call_in_scope
    computed_rc = RefChecker()
    effect_rc = RefChecker()

    num = signal(1)

    @utils.fn
    def cp_1_spy():
        return num.value

    cp_1 = computed(cp_1_spy)

    computed_rc.collect(cp_1)

    def temp_run():
        current_scope = scope()

        @current_scope.run
        def _():
            @effect
            def ef1():
                cp_1.value

            effect_rc.collect(ef1)

        current_scope.dispose()

    temp_run()

    @effect
    def _():
        cp_1.value

    gc.collect()
    assert cp_1_spy.calledTimes == 1

    num.value = 2
    gc.collect()
    assert cp_1_spy.calledTimes == 2

    # Only the effects defined within the scope should be released, not the computeds defined outside the scope.
    gc.collect()
    assert computed_rc.calledTimes == 0
    assert effect_rc.calledTimes == 1


def test_nested_scope():
    computed_rc = RefChecker()
    signal_rc = RefChecker()

    num = signal(1)

    signal_rc.collect(num)

    def temp_run(x):
        current_scope = scope()

        @current_scope.run
        def _():
            @computed
            def cp_1():
                print(x)
                return num.value

            computed_rc.collect(cp_1)

            def inner_fn():
                nested_scope = scope()

                @nested_scope.run
                def _():
                    @computed
                    def cp_2():
                        return cp_1.value

                    cp_2.value

                    computed_rc.collect(cp_2)

                nested_scope.dispose()

            inner_fn()

        current_scope.dispose()

        gc.collect()

    assert signal_rc.calledTimes == 0
    assert computed_rc.calledTimes == 0

    temp_run(1)
    assert computed_rc.calledTimes == 2
