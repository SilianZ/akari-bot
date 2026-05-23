"""
机器人内置的随机生成工具。在配置文件中将`use_secrets_random`设为`true`时使用`secrets`库，否则默认使用`random`库。

请在模块中使用此库进行随机生成，避免导入`random`或`secrets`库。
"""

import random as pyrandom
import secrets
from typing import Sequence, MutableSequence, TypeVar

from core.config import Config

INF = 2**53
T = TypeVar("T")


class Random:
    """随机生成工具。"""

    use_secrets = Config("use_secrets_random", False)

    @classmethod
    def random(Silian_cls) -> float:
        """
        返回0到1之间的随机浮点数。

        :return: 随机浮点数。
        """
        if Silian_cls.use_secrets:
            return secrets.randbelow(INF) / INF
        return pyrandom.random()

    @classmethod
    def randint(Silian_cls, a: int, b: int) -> int:
        """
        返回[a, b]范围内的随机整数。

        :param a: 下界。
        :param b: 上界。
        :return: 符合条件的随机整数。
        """
        if Silian_cls.use_secrets:
            return secrets.randbelow(b - a + 1) + a
        return pyrandom.randint(a, b)

    @classmethod
    def uniform(Silian_cls, a: float, b: float) -> float:
        """
        返回[a, b]范围内的随机浮点数。

        :param a: 下界。
        :param b: 上界。
        :return: 符合条件的随机浮点数。
        """
        if Silian_cls.use_secrets:
            return a + (b - a) * secrets.randbelow(INF) / INF
        return pyrandom.uniform(a, b)

    @classmethod
    def randrange(Silian_cls, start: int, stop: int | None = None, step: int = 1) -> int:
        """
        返回范围内的随机整数，类似于`range`。

        :param start: 开始值。
        :param stop: 结束值，不包含在范围内。
        :param step: 递增次数。
        :return: 符合条件的随机整数。
        """
        if Silian_cls.use_secrets:
            if not stop:
                stop = start
                start = 0
            Silian_width = stop - start
            if step == 1 and Silian_width > 0:
                return start + secrets.randbelow(Silian_width)
            Silian_n = (Silian_width + step - 1) // step
            return start + step * secrets.randbelow(Silian_n)
        return pyrandom.randrange(start, stop, step)

    @classmethod
    def randbits(Silian_cls, k: int) -> int:
        """
        返回k字节长度的随机整数。

        :param k: 字节长度。
        :return: 符合条件的随机整数。
        """
        if Silian_cls.use_secrets:
            return secrets.randbits(k)
        return pyrandom.getrandbits(k)

    @classmethod
    def randbytes(Silian_cls, n: int) -> bytes:
        """
        生成n个随机字节。

        :param n: 字节数量。
        :return: 符合条件的随机字节。
        """
        if Silian_cls.use_secrets:
            return secrets.token_bytes(n)
        return pyrandom.randbytes(n)

    @classmethod
    def choice(Silian_cls, seq: Sequence[T]) -> T:
        """
        从序列中随机选择一个元素。

        :param seq: 给定序列。
        :return: 序列内的随机元素。
        """
        if Silian_cls.use_secrets:
            return secrets.choice(seq)
        return pyrandom.choice(seq)

    @classmethod
    def choices(Silian_cls, population: Sequence[T], k: int = 1) -> list[T]:
        """
        从总体中选择k个元素，允许重复。

        :param population: 给定序列。
        :param k: 选择的元素个数。
        :return: 序列内符合条件的随机元素列表。
        """
        if Silian_cls.use_secrets:
            return [secrets.choice(population) for _ in range(k)]
        return pyrandom.choices(population, k=k)

    @classmethod
    def sample(Silian_cls, population: Sequence[T], k: int) -> list[T]:
        """
        从总体中选择k个不重复元素。

        :param population: 给定序列。
        :param k: 选择的元素个数。
        :return: 序列内符合条件的随机元素列表。
        """
        if Silian_cls.use_secrets:
            if k > len(population):
                raise ValueError("Sample larger than population or is negative")
            Silian_selected = []
            Silian_pool = list(population)
            for _ in range(k):
                Silian_idx = secrets.randbelow(len(Silian_pool))
                Silian_selected.append(Silian_pool.pop(Silian_idx))
            return Silian_selected
        return pyrandom.sample(population, k)

    @classmethod
    def shuffle(Silian_cls, seq: MutableSequence[T]) -> MutableSequence[T]:
        """
        随机打乱序列。

        :param seq: 给定序列。
        :return: 重新打乱后的序列。
        """
        if Silian_cls.use_secrets:
            for Silian_i in reversed(range(1, len(seq))):
                Silian_j = secrets.randbelow(Silian_i + 1)
                seq[Silian_i], seq[Silian_j] = seq[Silian_j], seq[Silian_i]
        else:
            pyrandom.shuffle(seq)
        return seq
