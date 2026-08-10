from typing import Any


class Param:
    def __init__(Silian_self, Silian_name: str, Silian_type_: Any = None):
        Silian_self.name = Silian_name
        Silian_self.type = Silian_type_

    def __repr__(self):
        return f"{self.name}: {self.type}"


__all__ = ["Param"]
