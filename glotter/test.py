import re
import sys

import pytest

from glotter.source import get_sources, filter_sources
from glotter.settings import Settings


def test(args):
    test_args = ["-n", "auto"] if args.parallel else []
    if not (args.language or args.project or args.source):
        _run_pytest_and_exit(*test_args)

    all_tests = _collect_tests()
    sources_by_type = filter_sources(args, get_sources(Settings().source_root))
    for project_type, sources in sources_by_type.items():
        for source in sources:
            test_args += _get_tests(project_type, all_tests, source)

    if not test_args:
        _error_and_exit("No tests were found")

    _run_pytest_and_exit(*test_args)


def _get_tests(project_type, all_tests, src=None):
    test_functions = Settings().get_test_mapping_name(project_type)
    tests = []
    for test_func in test_functions:
        if src is not None:
            test_id = f"{src.language}/{src.name}{src.extension}"
            pattern = rf"^(\w/?)*\.py::{test_func}\[{re.escape(test_id)}(-.*)?\]$"
        else:
            pattern = rf"^(\w/?)*\.py::{test_func}\[.+\]$"
        tests.extend(
            [tst for tst in all_tests if re.fullmatch(pattern, tst) is not None]
        )
    return tests


def _run_pytest_and_exit(*args):
    args = ["-v"] + list(args)
    code = pytest.main(args=args)
    sys.exit(code)


def _error_and_exit(msg):
    print(msg)
    sys.exit(1)


class TestCollectionPlugin:
    def __init__(self):
        self.collected = []

    def pytest_collection_modifyitems(self, items):
        for item in items:
            self.collected.append(item.nodeid)


def _collect_tests():
    print(
        "============================= collect test totals =============================="
    )
    plugin = TestCollectionPlugin()
    pytest.main(["-qq", "--collect-only"], plugins=[plugin])
    return plugin.collected
