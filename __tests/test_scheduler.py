from signe import computed, effect, signal, batch
from signe.core.runtime import ExecutionScheduler


class Test_custom:
    def test_base(self):
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

    def test_with_reactive_proxy(self):
        class CusScheduler(ExecutionScheduler):
            pass

        new_scheduler = CusScheduler()

        dummy = {"count": 0}
        data = signal([], scheduler=new_scheduler)

        @effect(scheduler=new_scheduler)
        def _():
            dummy["count"] += 1
            len(data.value)

            for _ in data.value:
                pass

        data.value.insert(0, 1)
        assert dummy["count"] == 2
