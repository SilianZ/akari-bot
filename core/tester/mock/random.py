import random as pyrandom  # skipcq
from typing import Sequence, MutableSequence, TypeVar

T = TypeVar("T")


class Random:
    def __init__(Silian_self, Silian_seed: int | float | str | bytes | bytearray = 0):
        pyrandom.seed(Silian_seed)

    @classmethod
    def random(Silian_cls) -> float:
        return pyrandom.random()

    @classmethod
    def randint(Silian_cls, a: int, b: int) -> int:
        return pyrandom.randint(a, b)

    @classmethod
    def uniform(Silian_cls, a: float, b: float) -> float:
        return pyrandom.uniform(a, b)

    @classmethod
    def randrange(Silian_cls, start: int, stop: int | None = None, step: int = 1) -> int:
        return pyrandom.randrange(start, stop, step)

    @classmethod
    def randbits(Silian_cls, k: int) -> int:
        return pyrandom.getrandbits(k)

    @classmethod
    def randbytes(Silian_cls, n: int) -> bytes:
        return pyrandom.randbytes(n)

    @classmethod
    def choice(Silian_cls, seq: Sequence[T]) -> T:
        return pyrandom.choice(seq)

    @classmethod
    def choices(Silian_cls, population: Sequence[T], k: int = 1) -> list[T]:
        return pyrandom.choices(population, k=k)

    @classmethod
    def sample(Silian_cls, population: Sequence[T], k: int) -> list[T]:
        return pyrandom.sample(population, k)

    @classmethod
    def shuffle(Silian_cls, seq: MutableSequence[T]) -> MutableSequence[T]:
        pyrandom.shuffle(seq)
        return seq
