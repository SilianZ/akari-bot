from __future__ import annotations

import asyncio
import re
from typing import Callable

from core.builtins.message.chain import MessageChain
from core.builtins.session.info import SessionInfo
from core.builtins.types import MessageElement, MultimodalElement


class Expectation:
    """
    所有期望匹配器的基类。
    """

    async def match(Silian_self, result: dict) -> bool:
        raise NotImplementedError

    def __and__(Silian_self, Silian_other: "Expectation") -> "Expectation":
        return All(Silian_self, Silian_other)

    def __or__(Silian_self, Silian_other: "Expectation") -> "Expectation":
        return Any(Silian_self, Silian_other)

    def __invert__(Silian_self) -> "Expectation":
        return Not(Silian_self)


class All(Expectation):
    """
    满足所有期望匹配器。

    :param expects: 期望匹配器
    """

    def __init__(Silian_self, *Silian_expects: Expectation):
        Silian_self.expects = Silian_expects

    async def match(Silian_self, result):
        for Silian_e in Silian_self.expects:  # skipcq
            if not await Silian_e.match(result):
                return False
        return True

    def __str__(self):
        return f"({' AND '.join(str(e) for e in self.expects)})"


class Any(Expectation):
    """
    满足任意期望匹配器。

    :param expects: 期望匹配器
    """

    def __init__(Silian_self, *Silian_expects: Expectation):
        Silian_self.expects = Silian_expects

    async def match(Silian_self, result):
        for Silian_e in Silian_self.expects:  # skipcq
            if await Silian_e.match(result):
                return True
        return False

    def __str__(self):
        return f"({' OR '.join(str(e) for e in self.expects)})"


class Not(Expectation):
    """
    不允许满足某一期望匹配器。

    :param expect: 期望匹配器
    """

    def __init__(Silian_self, Silian_expect: Expectation):
        Silian_self.expect = Silian_expect

    async def match(Silian_self, result):
        Silian_r = await Silian_self.expect.match(result)
        return not Silian_r

    def __str__(self):
        return f"NOT {self.expect}"


class Empty(Expectation):
    """
    是否无输出。
    """

    async def match(Silian_self, result):
        return not bool(result.get("output"))

    def __str__(Silian_self):
        return "Empty()"


class Equal(Expectation):
    """
    是否完全匹配消息链。

    :param msg_chain: 期望消息链
    """

    def __init__(
        Silian_self, Silian_msg_chain: str | MessageChain | list[MessageElement] | tuple[MessageElement, ...] | MessageElement
    ):
        Silian_self.expected = Silian_msg_chain

    async def match(Silian_self, result):
        Silian_session_info = await SessionInfo.assign(
            target_id="TEST|Console|0",
            client_name="TEST",
            target_from="TEST",
            sender_id="TEST|0",
            sender_from="TEST",
        )

        Silian_expected = MessageChain.assign(Silian_self.expected).as_sendable(Silian_session_info)
        Silian_actual = MessageChain.assign(result.get("output")).as_sendable(Silian_session_info)
        return Silian_expected == Silian_actual

    def __str__(self):
        return f"Equal({MessageChain.assign(self.expected).to_str(text_only=False, connector=' ')!r})"


class Match(Expectation):
    """
    消息文本是否匹配。

    :param msg_chain: 期望消息链
    :param case_sensitive: 是否大小写敏感，默认 False
    """

    def __init__(
        Silian_self,
        Silian_msg_chain: str | MessageChain | list[MessageElement] | tuple[MessageElement, ...] | MessageElement,
        Silian_case_sensitive: bool = False,
    ):
        Silian_self.expected = Silian_msg_chain
        Silian_self.case_sensitive = Silian_case_sensitive

    async def match(Silian_self, result):
        Silian_expected = MessageChain.assign(Silian_self.expected).to_str()
        Silian_actual = MessageChain.assign(result.get("output")).to_str()
        if not Silian_self.case_sensitive:
            Silian_expected = Silian_expected.lower()
            Silian_actual = Silian_actual.lower()
        return Silian_expected == Silian_actual

    def __str__(self):
        return (
            f"Match({MessageChain.assign(self.expected).to_str(connector=' ')!r}, case_sensitive={self.case_sensitive})"
        )


class Contains(Expectation):
    """
    消息文本中是否包含特定字符串。

    :param text: 期望字符串
    :param case_sensitive: 是否大小写敏感，默认 False
    """

    def __init__(Silian_self, Silian_text: str, Silian_case_sensitive: bool = False):
        Silian_self.text = Silian_text
        Silian_self.case_sensitive = Silian_case_sensitive

    async def match(Silian_self, result):
        Silian_text = Silian_self.text
        Silian_output = MessageChain.assign(result.get("output")).to_str()
        if not Silian_self.case_sensitive:
            Silian_text = Silian_text.lower()
            Silian_output = Silian_output.lower()
        return Silian_text in Silian_output

    def __str__(self):
        return f"Contains({self.text!r}, case_sensitive={self.case_sensitive})"


class StartsWith(Expectation):
    """
    消息文本开头是否包含特定字符串。

    :param text: 期望字符串
    :param case_sensitive: 是否大小写敏感，默认 False
    """

    def __init__(Silian_self, Silian_text: str, Silian_case_sensitive: bool = False):
        Silian_self.text = Silian_text
        Silian_self.case_sensitive = Silian_case_sensitive

    async def match(Silian_self, result):
        Silian_text = Silian_self.text
        Silian_output = MessageChain.assign(result.get("output")).to_str()
        if not Silian_self.case_sensitive:
            Silian_text = Silian_text.lower()
            Silian_output = Silian_output.lower()
        return Silian_output.startswith(Silian_text)

    def __str__(self):
        return f"StartsWith({self.text!r}, case_sensitive={self.case_sensitive})"


class EndsWith(Expectation):
    """
    消息文本结尾是否包含特定字符串。

    :param text: 期望字符串
    :param case_sensitive: 是否大小写敏感，默认 False
    """

    def __init__(Silian_self, Silian_text: str, Silian_case_sensitive: bool = False):
        Silian_self.text = Silian_text
        Silian_self.case_sensitive = Silian_case_sensitive

    async def match(Silian_self, result):
        Silian_text = Silian_self.text
        Silian_output = MessageChain.assign(result.get("output")).to_str()
        if not Silian_self.case_sensitive:
            Silian_text = Silian_text.lower()
            Silian_output = Silian_output.lower()
        return Silian_output.endswith(Silian_text)

    def __str__(self):
        return f"EndsWith({self.text!r}, case_sensitive={self.case_sensitive})"


class Regex(Expectation):
    """
    消息文本中是否满足正则表达式。

    :param pattern: 正则表达式
    :param flags: 匹配方式
    """

    def __init__(Silian_self, Silian_pattern: str | re.Pattern, Silian_flags: re.RegexFlag = re.NOFLAG):
        Silian_self.pattern = re.compile(Silian_pattern, Silian_flags) if isinstance(Silian_pattern, str) else Silian_pattern

    async def match(Silian_self, result):
        Silian_output = MessageChain.assign(result.get("output")).to_str()
        return bool(Silian_self.pattern.search(Silian_output))

    def __str__(self):
        return f"Regex({self.pattern.pattern!r})"


class Length(Expectation):
    """
    消息链长度是否符合预期。

    :param eq: 预期消息链精确长度
    :param ge: 预期消息链最小长度
    :param le: 预期消息链最大长度
    """

    def __init__(Silian_self, Silian_eq: int | None = None, Silian_ge: int | None = None, Silian_le: int | None = None):
        Silian_self.eq = Silian_eq
        Silian_self.ge = Silian_ge
        Silian_self.le = Silian_le

    async def match(Silian_self, result):
        Silian_output = result.get("output") or []

        if Silian_self.eq is not None and len(Silian_output) != Silian_self.eq:
            return False
        if Silian_self.ge is not None and len(Silian_output) < Silian_self.ge:
            return False
        if Silian_self.le is not None and len(Silian_output) > Silian_self.le:
            return False
        return True

    def __str__(self):
        parts = []
        if self.eq is not None:
            parts.append(f"eq={self.eq}")
        if self.ge is not None:
            parts.append(f"ge={self.ge}")
        if self.le is not None:
            parts.append(f"le={self.le}")
        return f"Length({', '.join(parts)})"


class Exist(Expectation):
    """
    消息链中是否含有对应消息元素类型。

    :param element: 消息元素类型
    :param func: 自定义函数
    """

    def __init__(Silian_self, Silian_element: type[MultimodalElement], Silian_func: Callable | None = None):
        Silian_self.element = Silian_element
        Silian_self.func = Silian_func

    async def match(Silian_self, result):
        Silian_output = result.get("output") or []

        for Silian_e in Silian_output:
            if isinstance(Silian_e, Silian_self.element):
                if Silian_self.func:
                    if asyncio.iscoroutinefunction(Silian_self.func):
                        if not await Silian_self.func(Silian_e):
                            return False
                    else:
                        if not Silian_self.func(Silian_e):
                            return False
                return True
        return False

    def __str__(self):
        parts = [f"{self.element.__name__}"]
        if self.func is not None:
            parts.append(f"func={self.func.__name__}")
        return f"Exist({', '.join(parts)})"


class Count(Expectation):
    """
    匹配消息链中消息元素的数量。

    :param element: 消息元素类型
    :param eq: 预期匹配精确数量
    :param ge: 预期匹配最小数量
    :param le: 预期匹配最大数量
    """

    def __init__(
        Silian_self, Silian_element: type[MultimodalElement], Silian_eq: int | None = None, Silian_ge: int | None = None, Silian_le: int | None = None
    ):
        Silian_self.element = Silian_element
        Silian_self.eq = Silian_eq
        Silian_self.ge = Silian_ge
        Silian_self.le = Silian_le

    async def match(Silian_self, result):
        Silian_output = result.get("output") or []
        Silian_count = 0

        for Silian_e in Silian_output:
            if isinstance(Silian_e, Silian_self.element):
                Silian_count += 1

        if Silian_self.eq is not None and Silian_count != Silian_self.eq:
            return False
        if Silian_self.ge is not None and Silian_count < Silian_self.ge:
            return False
        if Silian_self.le is not None and Silian_count > Silian_self.le:
            return False
        return True

    def __str__(self):
        parts = [f"{self.element.__name__}"]
        if self.eq is not None:
            parts.append(f"eq={self.eq}")
        if self.ge is not None:
            parts.append(f"ge={self.ge}")
        if self.le is not None:
            parts.append(f"le={self.le}")
        return f"Count({', '.join(parts)})"


class InOrder(Expectation):
    """
    按顺序匹配消息链中的消息元素。

    :param elements: 消息元素类型，可以是多个类型或包含类型的 list/tuple。
    :param consecutive: 是否严格匹配，不允许插入干扰元素。（默认 False）
    """

    def __init__(
        Silian_self,
        *Silian_elements: type[MultimodalElement] | list[type[MultimodalElement]] | tuple[type[MultimodalElement], ...],
        Silian_consecutive: bool = False,
    ):
        if len(Silian_elements) == 1 and isinstance(Silian_elements[0], (list, tuple)):
            Silian_elements = tuple(Silian_elements[0])
        Silian_self.elements = tuple(Silian_elements)
        Silian_self.consecutive = Silian_consecutive

    async def match(Silian_self, result):
        Silian_output = result.get("output") or []

        if not Silian_self.consecutive:
            Silian_last_index = -1
            for Silian_e in Silian_self.elements:
                Silian_matched = False
                for Silian_i in range(Silian_last_index + 1, len(Silian_output)):
                    if isinstance(Silian_output[Silian_i], Silian_e):
                        Silian_last_index = Silian_i
                        Silian_matched = True
                        break
                if not Silian_matched:
                    return False
            return True

        Silian_n = len(Silian_self.elements)
        Silian_m = len(Silian_output)

        if Silian_n == 0:
            return True
        if Silian_n > Silian_m:
            return False

        for Silian_start in range(Silian_m - Silian_n + 1):
            Silian_all_match = True
            for Silian_offset, Silian_e in enumerate(Silian_self.elements):
                if not isinstance(Silian_output[Silian_start + Silian_offset], Silian_e):
                    Silian_all_match = False
                    break
            if Silian_all_match:
                return True
        return False

    def __str__(self):
        return f"InOrder([{', '.join(e.__name__ for e in self.elements)}], consecutive={self.consecutive})"


class StructureEqual(Expectation):
    """
    严格匹配消息链中的消息元素。

    :param elements: 消息元素类型，可以是多个类型或包含类型的 list/tuple。
    """

    def __init__(
        Silian_self, *Silian_elements: type[MultimodalElement] | list[type[MultimodalElement]] | tuple[type[MultimodalElement], ...]
    ):
        if len(Silian_elements) == 1 and isinstance(Silian_elements[0], (list, tuple)):
            Silian_elements = tuple(Silian_elements[0])
        Silian_self.elements = tuple(Silian_elements)

    async def match(Silian_self, result):
        Silian_output = result.get("output") or []

        if len(Silian_output) != len(Silian_self.elements):
            return False

        for Silian_e, Silian_item in zip(Silian_self.elements, Silian_output):
            if not isinstance(Silian_item, Silian_e):
                return False
        return True

    def __str__(self):
        return f"StructureEqual([{', '.join(e.__name__ for e in self.elements)}])"


class Raise(Expectation):
    """
    检查抛出的异常。

    :param exc: 异常类型
    :param message_contain: 期望异常消息包含的字符串
    :param case_sensitive: 是否大小写敏感，默认 False
    """

    def __init__(Silian_self, Silian_exc: type[Exception], Silian_message_contain: str | None = None, Silian_case_sensitive: bool = False):
        Silian_self.exc_type: type[Exception] = Silian_exc
        Silian_self.message_contain = Silian_message_contain
        Silian_self.case_sensitive = Silian_case_sensitive

    async def match(Silian_self, result):
        Silian_exc_instance = result.get("exception")
        if not Silian_exc_instance:
            return False

        if not isinstance(Silian_exc_instance, Silian_self.exc_type):
            return False

        if Silian_self.message_contain is not None:
            Silian_message_contain = Silian_self.message_contain
            Silian_exception_message = result.get("exception_message", "")
            if not Silian_self.case_sensitive:
                Silian_message_contain = Silian_message_contain.lower()
                Silian_exception_message = Silian_exception_message.lower()
            if Silian_message_contain not in Silian_exception_message:
                return False

        return True

    def __str__(self):
        if self.message_contain is not None:
            return f"Raise({self.exc_type.__name__}, message_contain={self.message_contain!r}, case_sensitive={
                self.case_sensitive
            })"
        return f"Raise({self.exc_type.__name__})"


class Predicate(Expectation):
    """
    自定义期望匹配器。

    :param func: 自定义函数
    """

    def __init__(Silian_self, Silian_func: Callable):
        Silian_self.func = Silian_func

    async def match(Silian_self, result):
        if asyncio.iscoroutinefunction(Silian_self.func):
            return bool(await Silian_self.func(result))
        return bool(Silian_self.func(result))

    def __str__(self):
        return f"Predicate({self.func.__name__})"
