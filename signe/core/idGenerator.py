from itertools import count


class IdGen:
    def __init__(self, name: str):
        self._name = name
        self._num = count()

    def new(self):
        return f"{self._name}_{next(self._num)}"
