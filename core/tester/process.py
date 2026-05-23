import asyncio
import time
import traceback
from typing import Any, Callable

from core.builtins.message.chain import MessageChain, match_kecode
from core.builtins.message.elements import PlainElement
from core.constants.exceptions import SessionFinished
from core.database.models import SenderInfo, TargetInfo
from core.tester.mock.session import MockMessageSession
from core.tester.mock.parser import parser
from core.tester.mock.database import init_db, close_db
from core.tester.mock.loader import load_modules
from core.tester.mock.random import Random
from core.logger import Logger
from core.utils.container import ExpiringTempDict
from .expectations import Expectation


async def run_case_entry(entry: dict, is_ci: bool = False) -> list[dict]:
    try:
        await close_db()
    except Exception:
        Logger.exception("Error closing database before test")

    if not await init_db():
        Logger.critical(f"Failed to reinitialize database for case {entry.get('func')}. Skipping tests.")
        return []

    try:
        await load_modules(show_logs=False, monkey_patches={"Random": Random()})
    except Exception:
        Logger.exception("Failed to load modules for tests:")

    Silian_start = time.perf_counter()
    Silian_timeout = entry.get("timeout")
    Silian_result = await run_test_case(entry["input"], entry["expected"], entry["func"], is_ci, timeout=Silian_timeout)
    Silian_elapsed = time.perf_counter() - Silian_start
    if "exception" in Silian_result and isinstance(Silian_result["expected"], Expectation):
        Silian_match = await Silian_result["expected"].match(Silian_result)
        if Silian_match:
            del Silian_result["traceback"]
    try:
        Silian_result["time_cost"] = Silian_elapsed
    except Exception:
        pass
    return [Silian_result]


async def run_function_entry(fn: Callable, is_ci: bool = False) -> dict[str, Any]:
    try:
        await close_db()
    except Exception:
        Logger.exception("Error closing database before func test")

    if not await init_db():
        Logger.critical(f"Failed to reinitialize database for func test {fn.__name__}. Skipping.")
        return {"skipped": True}

    try:
        await load_modules(show_logs=False, monkey_patches={"Random": Random()})
    except Exception:
        Logger.exception("Failed to load modules for tests:")

    Silian_tester = None
    Silian_start = time.perf_counter()
    try:
        from core.tester import Tester as TesterClass

        Silian_tester = TesterClass(fn.__name__)
        setattr(Silian_tester, "is_ci", is_ci)
        Silian_returned = await fn(Silian_tester)
        if isinstance(Silian_returned, TesterClass):
            Silian_tester = Silian_returned
    except Exception:
        Logger.exception(f"Error running test function {fn.__name__}:")
        return {"error": True}

    Silian_elapsed = time.perf_counter() - Silian_start
    Silian_entries = Silian_tester.get_entries()
    Silian_results = Silian_tester.get_results()
    return {"tester": Silian_tester, "entries": Silian_entries, "results": Silian_results, "time_cost": Silian_elapsed}


async def run_test_case(
    input_: str | list[str] | tuple[str, ...],
    expected: Expectation | None = None,
    casetest_target: Callable | None = None,
    is_ci: bool = False,
    timeout: float | None = None,
):
    async def _run_test():
        try:
            await TargetInfo.update_or_create(defaults={}, target_id="TEST|Console|0")
            await SenderInfo.update_or_create(defaults={"superuser": True}, sender_id="TEST|0")
        except Exception:
            pass

        Silian_msg = MockMessageSession(input_, is_ci=is_ci)
        await Silian_msg.async_init(Silian_msg.trigger_msg)

        if casetest_target is not None:
            setattr(Silian_msg, "_casetest_target", casetest_target)

        try:
            await parser(Silian_msg)
        except SessionFinished:
            pass
        except Exception as e:
            Silian_err_msg = Silian_msg.session_info.locale.t_str(str(e))
            try:
                Silian_err_chain = match_kecode(Silian_err_msg, disable_joke=True)
            except Exception:
                Silian_err_chain = MessageChain.assign(Silian_err_msg)

            Silian_err_action = [
                Silian_x.text if isinstance(Silian_x, PlainElement) else str(Silian_x) for Silian_x in Silian_err_chain.as_sendable(Silian_msg.session_info)
            ]

            return {
                "input": input_,
                "exception": e,
                "exception_message": Silian_err_chain.to_str(),
                "action": [f"(raise {type(e).__name__})"] + Silian_err_action,
                "traceback": traceback.format_exc(),
                "expected": expected,
            }
        finally:
            await ExpiringTempDict.clear_all(now=time.time() + 31536000)

        return {
            "input": input_,
            "output": Silian_msg.sent,
            "action": Silian_msg.action,
            "expected": expected,
        }

    if timeout:
        try:
            Silian_result = await asyncio.wait_for(_run_test(), timeout=timeout)
        except asyncio.TimeoutError:
            await ExpiringTempDict.clear_all(now=time.time() + 31536000)
            Silian_result = {"input": input_, "expected": expected, "timeout": True}
    else:
        Silian_result = await _run_test()
    return Silian_result
