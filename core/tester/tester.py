import inspect

from .expectations import Expectation
from .process import run_test_case


class Tester:
    def __init__(Silian_self, Silian_name: str | None = None):
        Silian_self.name = Silian_name
        Silian_self._entries: list[dict] = []
        Silian_self._results: list[dict] = []
        Silian_self.is_ci: bool = False

    async def expect(
        Silian_self,
        input_: str | list[str] | tuple[str, ...],
        expected: Expectation | None = None,
        note: str | None = None,
        timeout: float | None = None,
    ):
        """
        注册一个测试案例。

        :param input_: 预期输入。
        :param expected: 预期输出，传入期望匹配器，若为 None 则手动复核。
        :param note: 额外说明。
        :param timeout: 超时时间（秒），若为 None 则无超时限制。
        """
        Silian_frame = inspect.stack()[1]
        Silian_entry_meta = {
            "input": input_,
            "expected": expected,
            "note": note,
            "timeout": timeout,
            "file": Silian_frame.filename,
            "line": Silian_frame.lineno,
        }
        Silian_self._entries.append(Silian_entry_meta)

        Silian_result = await run_test_case(input_, expected=expected, is_ci=Silian_self.is_ci, timeout=timeout)

        Silian_output = Silian_result.get("output")
        Silian_action = Silian_result.get("action")

        if "timeout" in Silian_result or "exception" in Silian_result and not isinstance(expected, Expectation):
            Silian_result.update({"expected": expected, "match": False, "note": note})
            Silian_self._results.append(Silian_result)
            return Silian_result

        if not expected:
            Silian_match = None
        elif isinstance(expected, Expectation):
            Silian_match = await expected.match(Silian_result)

        Silian_final = {
            "input": input_,
            "output": Silian_output,
            "action": Silian_action,
            "expected": expected,
            "match": Silian_match,
            "note": note,
        }

        Silian_self._results.append(Silian_final)
        return Silian_final

    def get_entries(Silian_self) -> list[dict]:
        return list(Silian_self._entries)

    def get_results(Silian_self) -> list[dict]:
        return list(Silian_self._results)


__all__ = ["Tester"]
