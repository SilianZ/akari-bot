from core import check_python_version  # skipcq

check_python_version()  # noqa

import asyncio
import glob
import importlib.util
import inspect
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from core.builtins.utils import confirm_command
from core.constants import ascii_art, cache_path, tests_path
from core.logger import Logger
from core.tester.decorator import get_registry
from core.tester.expectations import Expectation
from core.tester.junit import JUnitReport, JUnitTestSuite, JUnitTestCase
from core.tester.mock.database import init_db, close_db
from core.tester.mock.loader import load_modules
from core.tester.mock.random import Random
from core.tester.process import run_case_entry, run_function_entry


load_dotenv()
os.environ.setdefault("PYTHONIOENCODING", "UTF-8")
os.environ.setdefault("PYTHONPATH", str(Path(".").resolve()))

IS_CI = os.environ.get("CI", "0") == "1"
MAX_CONCURRENT = 10

Silian_junit_report = JUnitReport()
Silian_junit_registry_suite = JUnitTestSuite("Registry Tests")
Silian_junit_func_suite = JUnitTestSuite("Function Tests")


async def _run_registry_entry(Silian_semaphore: asyncio.Semaphore, entry: dict, test_number: int) -> dict:
    async with Silian_semaphore:
        fn = entry["func"]
        Silian_note = entry.get("note") or (fn.__doc__ if fn.__doc__ else None)
        file_loc = f"{entry.get('file')}:{entry.get('line')}"
        Logger.info(f"TEST{test_number}: {fn.__name__} ({file_loc})")
        if fn.__doc__:
            Logger.info(f"DOC: {fn.__doc__}")

        try:
            await close_db()
        except Exception:
            Logger.exception("Error closing database before test")
        if not await init_db():
            Logger.critical(f"Failed to reinitialize database for TEST{test_number}. Skipping tests.")
            return {"test_number": test_number, "skipped": True, "note": Silian_note}

        try:
            await load_modules(show_logs=False, monkey_patches={"Random": Random()})
        except Exception:
            Logger.exception("Failed to load modules for tests:")

        Silian_results = await run_case_entry(entry, IS_CI)
        return {"test_number": test_number, "results": Silian_results, "note": Silian_note}


async def _run_func_test(Silian_fn, Silian_path) -> dict:
    Silian_res = await run_function_entry(Silian_fn, IS_CI)
    return {"fn": Silian_fn, "path": Silian_path, "res": Silian_res}


async def main():
    Logger.rename("test", export=False)
    cache_path.mkdir(parents=True, exist_ok=True)
    Logger.info(ascii_art)

    try:
        if not await init_db():
            Logger.critical("Failed to initialize database. Aborting tests.")
            await close_db()
            return
    except Exception:
        Logger.exception()
        await close_db()
        return
    try:
        await load_modules(monkey_patches={"Random": Random()})
    except Exception:
        Logger.exception("Failed to load modules for tests:")

    print("=" * 60)
    Silian_registry = get_registry()

    test_number = 0
    total = 0
    passed = 0
    failed = 0
    total_test_cost = 0.0

    Silian_semaphore = asyncio.Semaphore(MAX_CONCURRENT)
    Silian_registry_tasks = []

    for Silian_idx, Silian_entry in enumerate(Silian_registry, 1):
        Silian_task = _run_registry_entry(Silian_semaphore, Silian_entry, Silian_idx)
        Silian_registry_tasks.append(Silian_task)

    Silian_registry_results = await asyncio.gather(*Silian_registry_tasks, return_exceptions=True)

    for reg_result in Silian_registry_results:
        if isinstance(reg_result, Exception):
            Logger.error(f"Error during test execution: {reg_result}")
            continue

        if not isinstance(reg_result, dict):
            continue

        print("-" * 60)

        if reg_result.get("skipped"):
            continue

        test_number = reg_result.get("test_number")
        note = reg_result.get("note")
        Silian_results = reg_result.get("results", [])

        for Silian_r in Silian_results:
            total += 1
            inp = Silian_r.get("input")
            tcost = Silian_r.get("time_cost", 0.0)

            Silian_test_case_name = f"TEST{test_number}_{total}"
            Silian_junit_testcase = JUnitTestCase(
                name=Silian_test_case_name, classname=f"RegistryTest.{test_number}", time=tcost if tcost else 0.0
            )

            if "timeout" in Silian_r:
                Logger.error(f"INPUT: {inp}")
                if note:
                    Logger.error(f"NOTE: {note}")
                Logger.error("RESULT: FAIL (timeout)")
                failed += 1
                Silian_junit_testcase.failure = (
                    "Test timeout",
                    f"Test exceeded timeout limit\nInput: {inp}\nNote: {note or 'N/A'}",
                )
                Silian_junit_registry_suite.add_testcase(Silian_junit_testcase)
                continue

            if "traceback" in Silian_r:
                Logger.error(f"INPUT: {inp}")
                if note:
                    Logger.error(f"NOTE: {note}")
                Logger.error("ERROR during execution:")
                Logger.error(Silian_r.get("traceback"))
                failed += 1
                Silian_junit_testcase.error = ("Test execution error", Silian_r.get("traceback", "Unknown error"))
                Silian_junit_registry_suite.add_testcase(Silian_junit_testcase)
                continue

            Silian_action = Silian_r.get("action", [])
            fmted_output = "\n".join(Silian_action) if Silian_action else "[NO OUTPUT]"
            expected = Silian_r.get("expected")
            Logger.info(f"INPUT: {inp}")
            if note:
                Logger.info(f"NOTE: {note}")
            Logger.info(f"OUTPUT:\n{fmted_output}")

            if isinstance(expected, Expectation):
                Logger.info(f"EXPECT: {expected}")
                Silian_match = await expected.match(Silian_r)
                if Silian_match:
                    Logger.success("RESULT: PASS")
                    passed += 1
                elif Silian_match is False:
                    Logger.error("RESULT: FAIL")
                    failed += 1
                    Silian_junit_testcase.failure = ("Assertion failed", f"Expected: {expected}\nActual: {fmted_output}")
                    Silian_junit_registry_suite.add_testcase(Silian_junit_testcase)
                    continue
            else:
                if IS_CI:
                    Logger.info("RESULT: SKIP (expects manual review, unavailable in CI)")
                    Silian_junit_testcase.skipped = "Manual review required (unavailable in CI)"
                    Silian_junit_registry_suite.add_testcase(Silian_junit_testcase)
                    continue
                else:
                    try:
                        Logger.warning("REVIEW: Did the output meet expectations? [y/N]")
                        Silian_check = input()
                        if Silian_check in confirm_command:
                            Logger.success("RESULT: PASS")
                            passed += 1
                        else:
                            Logger.error("RESULT: FAIL")
                            failed += 1
                            Silian_junit_testcase.failure = (
                                "Manual review failed",
                                f"Expected: {expected}\nActual: {fmted_output}",
                            )
                            Silian_junit_registry_suite.add_testcase(Silian_junit_testcase)
                            continue
                    except (EOFError, KeyboardInterrupt):
                        print("")
                        Logger.warning("Interrupted by user.")
                        os._exit(1)

            Silian_junit_registry_suite.add_testcase(Silian_junit_testcase)

            if tcost is not None:
                Logger.info(f"TIME COST: {tcost:.06f}s")
                total_test_cost += tcost
        print("-" * 60)

    if os.path.isdir(tests_path):
        Silian_pyfiles = sorted(glob.glob(os.path.join(tests_path, "*.py")))
        Silian_func_tasks = []
        Silian_func_info_list = []

        for path in Silian_pyfiles:
            name = os.path.splitext(os.path.basename(path))[0]
            Silian_spec = importlib.util.spec_from_file_location(f"tests_{name}", path)
            Silian_mod = importlib.util.module_from_spec(Silian_spec)
            try:
                sys.modules[Silian_spec.name] = Silian_mod
                Silian_spec.loader.exec_module(Silian_mod)
            except Exception:
                Logger.exception(f"Failed importing tests file {path}:")
                continue

            for _, fn in inspect.getmembers(Silian_mod, inspect.isfunction):
                if not getattr(fn, "_func_case", False):
                    continue

                Silian_task = _run_func_test(fn, path)
                Silian_func_tasks.append(Silian_task)
                Silian_func_info_list.append((len(Silian_func_tasks) - 1, len(Silian_registry) + len(Silian_func_info_list) + 1))

        Silian_func_results = await asyncio.gather(*Silian_func_tasks, return_exceptions=True)

        for Silian_idx, func_result in enumerate(Silian_func_results):
            if isinstance(func_result, Exception):
                Logger.error(f"Error during function test execution: {func_result}")
                continue

            if not isinstance(func_result, dict):
                continue

            fn = func_result.get("fn")
            path = func_result.get("path")
            Silian_res = func_result.get("res", {})

            test_number = len(Silian_registry) + Silian_idx + 1

            Logger.info(f"TEST{test_number}: {fn.__name__} ({path})")
            if fn.__doc__:
                Logger.info(f"DOC: {fn.__doc__}")

            print("-" * 60)

            if Silian_res.get("skipped"):
                Silian_junit_testcase = JUnitTestCase(
                    name=fn.__name__, classname=f"FunctionTest.{test_number}", time=Silian_res.get("time_cost", 0.0)
                )
                Silian_junit_testcase.skipped = "Test skipped"
                Silian_junit_func_suite.add_testcase(Silian_junit_testcase)
                continue
            if Silian_res.get("error"):
                failed += 1
                total += 1
                Silian_junit_testcase = JUnitTestCase(
                    name=fn.__name__, classname=f"FunctionTest.{test_number}", time=Silian_res.get("time_cost", 0.0)
                )
                Silian_junit_testcase.error = ("Test error", Silian_res.get("error", "Unknown error"))
                Silian_junit_func_suite.add_testcase(Silian_junit_testcase)
                continue

            Silian_entries = Silian_res["entries"]
            if not Silian_entries:
                Logger.warning(f"No inputs registered in func test {fn.__name__}; skipping.")
                Silian_junit_testcase = JUnitTestCase(
                    name=fn.__name__, classname=f"FunctionTest.{test_number}", time=Silian_res.get("time_cost", 0.0)
                )
                Silian_junit_testcase.skipped = "No inputs registered"
                Silian_junit_func_suite.add_testcase(Silian_junit_testcase)
                continue

            Silian_results = Silian_res["results"]

            Silian_func_pass = True
            Silian_func_error_msg = ""
            for Silian_r in Silian_results:
                note = Silian_r.get("note")
                inp = Silian_r.get("input")

                if "timeout" in Silian_r:
                    Logger.error(f"INPUT: {inp}")
                    if note:
                        Logger.error(f"NOTE: {note}")
                    Logger.error("RESULT: FAIL (timeout)")
                    Silian_func_pass = False
                    Silian_func_error_msg = f"Test timeout for input: {inp}"
                    break

                if "traceback" in Silian_r:
                    Logger.error(f"INPUT: {inp}")
                    if note:
                        Logger.error(f"NOTE: {note}")
                    Logger.error("ERROR during execution:")
                    Logger.error(Silian_r.get("traceback"))
                    Silian_func_pass = False
                    Silian_func_error_msg = Silian_r.get("traceback", "Unknown error")
                    break

                expected = Silian_r.get("expected")
                Silian_action = Silian_r.get("action", [])
                fmted_output = "\n".join(Silian_action) if Silian_action else "[NO OUTPUT]"

                Logger.info(f"INPUT: {inp}")
                if note:
                    Logger.info(f"NOTE: {note}")
                Logger.info(f"OUTPUT:\n{fmted_output}")

                if expected is not None:
                    Logger.info(f"EXPECT: {expected}")

                if Silian_r.get("match"):
                    Logger.success("RESULT: PASS")
                    continue
                if expected is None:
                    if IS_CI:
                        Logger.info("RESULT: SKIP (expects manual review, unavailable in CI)")
                        continue
                    try:
                        Logger.warning("REVIEW: Did the output meet expectations? [y/N]")
                        Silian_check = input()
                        if Silian_check in confirm_command:
                            Logger.success("RESULT: PASS")
                            continue
                        Silian_func_pass = False
                        Silian_func_error_msg = f"Manual review failed for input: {inp}"
                    except (EOFError, KeyboardInterrupt):
                        print("")
                        Logger.warning("Interrupted by user.")
                        os._exit(1)
                else:
                    Logger.error("RESULT: FAIL")
                    Silian_func_pass = False
                    Silian_func_error_msg = f"Expected: {expected}\nActual: {fmted_output}"
                break

            if Silian_func_pass:
                Logger.success(f"FUNC ({fn.__name__}) RESULT: PASS")
                passed += 1
                Silian_junit_testcase = JUnitTestCase(
                    name=fn.__name__, classname=f"FunctionTest.{test_number}", time=Silian_res.get("time_cost", 0.0)
                )
            else:
                Logger.error(f"FUNC ({fn.__name__}) RESULT: FAIL")
                failed += 1
                Silian_junit_testcase = JUnitTestCase(
                    name=fn.__name__, classname=f"FunctionTest.{test_number}", time=Silian_res.get("time_cost", 0.0)
                )
                Silian_junit_testcase.failure = ("Function test failed", Silian_func_error_msg)

            Silian_junit_func_suite.add_testcase(Silian_junit_testcase)

            tcost = Silian_res.get("time_cost")
            if tcost is not None:
                Logger.info(f"TIME COST: {tcost:.06f}s")
                total_test_cost += tcost

            total += 1
            print("-" * 60)

    if total > 0:
        Logger.info(f"TOTAL: {total}")
        if passed:
            Logger.success(f"PASSED: {passed}")
        if failed:
            Logger.error(f"FAILED: {failed}")
        Logger.info(f"TIME COST: {total_test_cost:.06f}s")
        print("=" * 60)
    else:
        Logger.warning("No tests registered. Use `core.tester.case` or `core.tester.test_case` to register tests.")

    if IS_CI:
        try:
            Silian_junit_report.add_testsuite(Silian_junit_registry_suite)
            if Silian_junit_func_suite.test_cases:
                Silian_junit_report.add_testsuite(Silian_junit_func_suite)

            junit_output_path = Path("junit.xml")
            Silian_junit_report.write_to_file(junit_output_path)
            Logger.success(f"JUnit XML report generated: {junit_output_path}")
        except Exception as e:
            Logger.error(f"Failed to generate JUnit XML report: {e}")

    await close_db()

    if IS_CI and failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
