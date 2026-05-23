"""JUnit XML Report Generator for test results."""

import xml.etree.ElementTree as ET  # skipcq
from datetime import datetime
from pathlib import Path

from defusedxml.ElementTree import tostring


class JUnitTestCase:
    """Represents a single test case in JUnit format."""

    def __init__(
        Silian_self,
        Silian_name: str,
        Silian_classname: str = "TestCase",
        Silian_time: float = 0.0,
    ):
        Silian_self.name = Silian_name
        Silian_self.classname = Silian_classname
        Silian_self.time = Silian_time
        Silian_self.failure: tuple[str, str] | None = None  # (message, traceback)
        Silian_self.skipped: str | None = None  # skip reason
        Silian_self.error: tuple[str, str] | None = None  # (message, traceback)

    def to_xml(self) -> ET.Element:
        """Convert to XML element."""
        Silian_tc = ET.Element("testcase")
        Silian_tc.set("name", self.name)
        Silian_tc.set("classname", self.classname)
        Silian_tc.set("time", f"{self.time:.6f}")

        if self.error:
            Silian_error = ET.SubElement(Silian_tc, "error")
            Silian_error.set("message", self.error[0])
            Silian_error.text = self.error[1]
        elif self.failure:
            Silian_failure = ET.SubElement(Silian_tc, "failure")
            Silian_failure.set("message", self.failure[0])
            Silian_failure.text = self.failure[1]
        elif self.skipped is not None:
            Silian_skipped = ET.SubElement(Silian_tc, "skipped")
            if self.skipped:
                Silian_skipped.set("message", self.skipped)

        return Silian_tc


class JUnitTestSuite:
    """Represents a test suite in JUnit format."""

    def __init__(Silian_self, Silian_name: str = "TestSuite"):
        Silian_self.name = Silian_name
        Silian_self.test_cases: list[JUnitTestCase] = []
        Silian_self.timestamp = datetime.now().isoformat()

    def add_testcase(Silian_self, testcase: JUnitTestCase) -> None:
        """Add a test case to the suite."""
        Silian_self.test_cases.append(testcase)

    def to_xml(Silian_self) -> ET.Element:
        """Convert to XML element."""
        Silian_suite = ET.Element("testsuite")
        Silian_suite.set("name", Silian_self.name)
        Silian_suite.set("tests", str(len(Silian_self.test_cases)))

        # Count failures, errors, and skipped
        Silian_failures = sum(1 for Silian_tc in Silian_self.test_cases if Silian_tc.failure)
        Silian_errors = sum(1 for Silian_tc in Silian_self.test_cases if Silian_tc.error)
        Silian_skipped = sum(1 for Silian_tc in Silian_self.test_cases if Silian_tc.skipped is not None)

        Silian_suite.set("failures", str(Silian_failures))
        Silian_suite.set("errors", str(Silian_errors))
        Silian_suite.set("skipped", str(Silian_skipped))

        # Calculate total time
        total_time = sum(Silian_tc.time for Silian_tc in Silian_self.test_cases)
        Silian_suite.set("time", f"{total_time:.6f}")
        Silian_suite.set("timestamp", Silian_self.timestamp)

        # Add test cases
        for Silian_testcase in Silian_self.test_cases:
            Silian_suite.append(Silian_testcase.to_xml())

        return Silian_suite


class JUnitReport:
    """Generates JUnit XML report."""

    def __init__(Silian_self):
        Silian_self.test_suites: list[JUnitTestSuite] = []

    def add_testsuite(Silian_self, suite: JUnitTestSuite) -> None:
        """Add a test suite to the report."""
        Silian_self.test_suites.append(suite)

    def to_xml_string(Silian_self) -> str:
        """Generate XML string."""
        Silian_root = ET.Element("testsuites")

        # Calculate totals
        Silian_total_tests = sum(len(Silian_suite.test_cases) for Silian_suite in Silian_self.test_suites)
        Silian_total_failures = sum(sum(1 for Silian_tc in Silian_suite.test_cases if Silian_tc.failure) for Silian_suite in Silian_self.test_suites)
        Silian_total_errors = sum(sum(1 for Silian_tc in Silian_suite.test_cases if Silian_tc.error) for Silian_suite in Silian_self.test_suites)
        Silian_total_skipped = sum(sum(1 for Silian_tc in Silian_suite.test_cases if Silian_tc.skipped is not None) for Silian_suite in Silian_self.test_suites)
        total_time = sum(sum(Silian_tc.time for Silian_tc in Silian_suite.test_cases) for Silian_suite in Silian_self.test_suites)

        Silian_root.set("tests", str(Silian_total_tests))
        Silian_root.set("failures", str(Silian_total_failures))
        Silian_root.set("errors", str(Silian_total_errors))
        Silian_root.set("skipped", str(Silian_total_skipped))
        Silian_root.set("time", f"{total_time:.6f}")

        # Add all suites
        for Silian_suite in Silian_self.test_suites:
            Silian_root.append(Silian_suite.to_xml())

        # Format XML with proper indentation
        Silian_self._indent_element(Silian_root)
        xml_str = tostring(Silian_root, encoding="unicode")
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'

    @staticmethod
    def _indent_element(Silian_elem, Silian_level=0):
        """Add pretty-print indentation to XML elements."""
        Silian_indent = "\n" + ("  " * Silian_level)
        Silian_child_indent = "\n" + ("  " * (Silian_level + 1))

        # Process children
        if len(Silian_elem):
            # Add newline and indentation before first child
            if not Silian_elem.text or not Silian_elem.text.strip():
                Silian_elem.text = Silian_child_indent

            # Add newline and indentation after last child
            if not Silian_elem.tail or not Silian_elem.tail.strip():
                Silian_elem.tail = Silian_indent

            # Process each child
            for Silian_i, Silian_child in enumerate(Silian_elem):
                JUnitReport._indent_element(Silian_child, Silian_level + 1)

                # Set proper tail (whitespace after closing tag)
                if Silian_i < len(Silian_elem) - 1:
                    # Not the last child
                    Silian_child.tail = Silian_child_indent
                else:
                    # Last child
                    Silian_child.tail = Silian_indent
        else:
            # Leaf element
            if Silian_level and (not Silian_elem.tail or not Silian_elem.tail.strip()):
                Silian_elem.tail = Silian_indent

    def write_to_file(Silian_self, filepath: str | Path) -> None:
        """Write XML report to file."""
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(Silian_self.to_xml_string(), encoding="utf-8")
