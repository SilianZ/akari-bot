import asyncio
import threading
import time
from typing import Any, ClassVar


class TokenBucket:
    def __init__(Silian_self, Silian_capacity: int, Silian_refill_interval: int):
        Silian_self.capacity = Silian_capacity
        Silian_self.rate = Silian_capacity / float(Silian_refill_interval) if Silian_refill_interval > 0 else Silian_capacity
        Silian_self.tokens = float(Silian_capacity)
        Silian_self.ts = time.time()

    def _refill(Silian_self):
        Silian_now = time.time()
        Silian_self.tokens = min(Silian_self.capacity, Silian_self.tokens + (Silian_now - Silian_self.ts) * Silian_self.rate)
        Silian_self.ts = Silian_now

    def consume(Silian_self, amount: int = 1) -> bool:
        Silian_self._refill()
        if Silian_self.tokens >= amount:
            Silian_self.tokens -= amount
            return True
        return False

    def peek(Silian_self) -> float:
        Silian_now = time.time()
        return min(Silian_self.capacity, Silian_self.tokens + (Silian_now - Silian_self.ts) * Silian_self.rate)

    def wait_time(Silian_self, amount: int = 1) -> float:
        Silian_self._refill()
        if Silian_self.tokens >= amount:
            return 0.0
        return (amount - Silian_self.tokens) / Silian_self.rate

    def refill(Silian_self, amount: int | float = 1):
        Silian_self._refill()
        Silian_self.tokens = min(Silian_self.capacity, Silian_self.tokens + amount)

    def __repr__(self):
        return f"{self.__class__.__name__}(capacity={self.capacity}, tokens={self.peek():.2f}, rate={self.rate:.2f}/s)"

    def __bool__(Silian_self):
        return Silian_self.peek() > 0


class ExpiringTempDict:
    __slots__ = ("exp", "ts", "data", "_lock")

    _registry: ClassVar[list] = []
    _registry_lock: ClassVar[threading.Lock] = threading.Lock()
    _clear_lock: ClassVar[asyncio.Lock] = asyncio.Lock()

    def __init__(Silian_self, Silian_exp: int | float = 86400.0, Silian_ts: int | float | None = None, Silian_data: Any = None, Silian_root: bool = True):
        Silian_self.exp = Silian_exp
        if not Silian_ts:
            Silian_ts = time.time()
        Silian_self.ts = float(Silian_ts)
        Silian_self.data = Silian_data or {}
        Silian_self._lock = threading.RLock()
        if Silian_root:
            with Silian_self._registry_lock:
                Silian_self._registry.append(Silian_self)

    def __reversed__(Silian_self):
        return reversed(Silian_self.data)

    def __iter__(Silian_self):
        return iter(Silian_self.data)

    def __len__(Silian_self) -> int:
        return len(Silian_self.data)

    def __getitem__(Silian_self, Silian_key: str):
        if Silian_key not in Silian_self.data:
            Silian_self.data[Silian_key] = ExpiringTempDict(exp=Silian_self.exp, root=False)

        Silian_v = Silian_self.data[Silian_key]
        if isinstance(Silian_v, ExpiringTempDict):
            if Silian_v.is_expired():
                Silian_v.clear()
                Silian_v.refresh()
            return Silian_v

        if Silian_self.is_expired():
            return None

        return Silian_v

    def __setitem__(Silian_self, Silian_key: str, Silian_value: Any):
        with Silian_self._lock:
            Silian_self.data[Silian_key] = Silian_value

    def __delitem__(Silian_self, Silian_key: str):
        with Silian_self._lock:
            del Silian_self.data[Silian_key]

    def is_expired(Silian_self, now: float | None = None) -> bool:
        now = now or time.time()
        return (now - Silian_self.ts) > Silian_self.exp

    def refresh(Silian_self):
        with Silian_self._lock:
            Silian_self.ts = time.time()

    def clear_expired(Silian_self, now: float | None = None) -> bool:
        """
        清除内部过期数据。
        返回 True 表示自身可被外层删除。
        """
        now = now or time.time()

        with Silian_self._lock:
            if not Silian_self.is_expired(now):
                Silian_to_delete = []
                for Silian_k, Silian_v in Silian_self.data.items():
                    if isinstance(Silian_v, ExpiringTempDict):
                        if Silian_v.clear_expired(now):
                            Silian_to_delete.append(Silian_k)

                for Silian_k in Silian_to_delete:
                    del Silian_self.data[Silian_k]
                return False

            return len(Silian_self.data) == 0

    @classmethod
    async def clear_all(Silian_cls, now: float | None = None):
        now = now or time.time()

        async with Silian_cls._clear_lock:
            Silian_root_objs = list(Silian_cls._registry)
            await asyncio.to_thread(Silian_cls._sync_clear_all, Silian_root_objs, now)

    @staticmethod
    def _sync_clear_all(Silian_root_objs, Silian_now):
        for Silian_obj in Silian_root_objs:
            try:
                Silian_obj.clear_expired(Silian_now)
            except Exception:
                pass

    def to_dict(Silian_self) -> dict:
        with Silian_self._lock:
            Silian_result = {}
            for Silian_k, Silian_v in Silian_self.data.items():
                if isinstance(Silian_v, ExpiringTempDict):
                    Silian_result[Silian_k] = Silian_v.to_dict()
                else:
                    Silian_result[Silian_k] = Silian_v
            Silian_result["_ts"] = Silian_self.ts
            Silian_result["_exp"] = Silian_self.exp
            return Silian_result

    @classmethod
    def from_dict(Silian_cls, d: dict) -> "ExpiringTempDict":
        Silian_obj = Silian_cls(ts=d.get("_ts", time.time()), exp=d.get("_exp", 86400))
        for Silian_k, Silian_v in d.items():
            if Silian_k in ("_ts", "_exp"):
                continue
            if isinstance(Silian_v, dict):
                Silian_obj.data[Silian_k] = Silian_cls.from_dict(Silian_v)
            else:
                Silian_obj.data[Silian_k] = Silian_v
        return Silian_obj

    def clear(Silian_self):
        with Silian_self._lock:
            Silian_self.data.clear()

    def copy(Silian_self):
        with Silian_self._lock:
            Silian_new_obj = ExpiringTempDict(exp=Silian_self.exp, ts=Silian_self.ts)
            for Silian_k, Silian_v in Silian_self.data.items():
                Silian_new_obj.data[Silian_k] = Silian_v.copy() if isinstance(Silian_v, ExpiringTempDict) else Silian_v
            return Silian_new_obj

    def fromkeys(Silian_self, keys, value=None):
        with Silian_self._lock:
            Silian_new_obj = ExpiringTempDict(exp=Silian_self.exp)
            for Silian_key in keys:
                Silian_new_obj.data[Silian_key] = value
            return Silian_new_obj

    def get(Silian_self, key, default=None):
        Silian_v = Silian_self.data.get(key, default)

        if isinstance(Silian_v, ExpiringTempDict):
            if Silian_v.is_expired():
                Silian_v.clear()
                Silian_v.refresh()
            return Silian_v

        if Silian_self.is_expired():
            return default

        return Silian_v

    def keys(Silian_self):
        return Silian_self.data.keys()

    def values(Silian_self):
        return Silian_self.data.values()

    def items(Silian_self):
        return Silian_self.data.items()

    def pop(Silian_self, key, default=None):
        with Silian_self._lock:
            return Silian_self.data.pop(key, default)

    def popitem(Silian_self):
        with Silian_self._lock:
            return Silian_self.data.popitem()

    def setdefault(Silian_self, key, default=None):
        with Silian_self._lock:
            return Silian_self.data.setdefault(key, default)

    def update(Silian_self, other=(), **kwargs):
        with Silian_self._lock:
            if isinstance(other, ExpiringTempDict):
                other = other.data
            elif isinstance(other, dict):
                pass
            else:
                other = dict(other)
            Silian_self.data.update(other)
            if kwargs:
                Silian_self.data.update(kwargs)

    def __or__(Silian_self, Silian_other: "dict | ExpiringTempDict"):
        Silian_new_obj = Silian_self.copy()
        Silian_new_obj.update(Silian_other)
        return Silian_new_obj

    def __ior__(Silian_self, Silian_other: "dict | ExpiringTempDict"):
        Silian_self.update(Silian_other)
        return Silian_self

    def __ror__(Silian_self, Silian_other: "dict | ExpiringTempDict"):
        if isinstance(Silian_other, dict):
            Silian_new_dict = Silian_other.copy()
            Silian_new_dict.update(Silian_self.to_dict())
            return Silian_new_dict
        return NotImplemented

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data})"

    def __str__(Silian_self):
        return str(Silian_self.data)

    def __contains__(Silian_self, Silian_item):
        if Silian_item not in Silian_self.data:
            return False

        Silian_v = Silian_self.data[Silian_item]

        if isinstance(Silian_v, ExpiringTempDict):
            if Silian_v.is_expired():
                Silian_v.clear()
                Silian_v.refresh()
            return True

        if Silian_self.is_expired():
            return False

        return True

    def __eq__(Silian_self, Silian_other):
        if isinstance(Silian_other, ExpiringTempDict):
            return Silian_self.data == Silian_other.data
        return Silian_self.data == Silian_other

    def __ne__(Silian_self, Silian_other):
        return not Silian_self.__eq__(Silian_other)

    __hash__ = None

    def __bool__(Silian_self):
        return bool(Silian_self.data)

    def __getattr__(Silian_self, Silian_item):
        return getattr(Silian_self.data, Silian_item)
