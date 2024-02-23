from signe import computed, effect, signal
from signe.core.runtime import ExecutionScheduler


class Test_custom:
    def test_base_(self):
        class CusScheduler(ExecutionScheduler):
            pass

        dummy = []

        cs = CusScheduler()

        items = signal(
            [
                {"value": True},
                {"value": False},
            ],
            scheduler=cs,
        )

        @computed(scheduler=cs)
        def total():
            return sum(s["value"] for s in items.value)

        @effect(scheduler=cs)
        def _():
            dummy.append(total.value)

        assert dummy == [1]

        items.value[1]["value"] = True
        assert dummy == [1, 2]
