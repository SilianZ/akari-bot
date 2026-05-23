class AnchorElement:
    __slots__ = ["attrs", "count", "outcount"]

    def __init__(Silian_self, Silian_attrs: dict[str, str | None], Silian_count: int, Silian_outcount: int):
        Silian_self.attrs = Silian_attrs
        Silian_self.count = Silian_count
        Silian_self.outcount = Silian_outcount


class ListElement:
    __slots__ = ["name", "num"]

    def __init__(Silian_self, Silian_name: str, Silian_num: int):
        Silian_self.name = Silian_name
        Silian_self.num = Silian_num
