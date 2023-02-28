import re
import os
import sys

import pytest

from glotter.source import get_sources
from glotter.settings import Settings
from glotter.utils import error_and_exit


def test(args):
    if args.language:
        _test_language(args.language)
    elif args.project:
        _test_project(args.project)
    elif args.source:
        _test_source(args.source)
    else:
        _test_all()


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


def _test_all():
    _run_pytest_and_exit()


def _test_language(language):
    all_tests = _collect_tests()
    sources_by_type = get_sources(path=os.path.join("archive", language[0], language))
    if not any(sources_by_type.values()):
        error_and_exit(f'No valid sources found for language: "{language}"')
    tests = []
    for project_type, sources in sources_by_type.items():
        for src in sources:
            tests.extend(_get_tests(project_type, all_tests, src))
    try:
        _verify_test_list_not_empty(tests)
        _run_pytest_and_exit(*tests)
    except KeyError:
        error_and_exit(f'No tests found for sources in language "{language}"')


def _test_project(project):
    try:
        Settings().verify_project_type(project)
        tests = _get_tests(project, _collect_tests())
        _verify_test_list_not_empty(tests)
        _run_pytest_and_exit(*tests)
    except KeyError:
        error_and_exit(f'Either tests or sources not found for project: "{project}"')


def _test_source(source):
    all_tests = _collect_tests()
    sources_by_type = get_sources("archive")
    for project_type, sources in sources_by_type.items():
        for src in sources:
            filename = f"{src.name}{src.extension}"
            if filename.lower() == source.lower():
                tests = _get_tests(project_type, all_tests, src)
                try:
                    _verify_test_list_not_empty(tests)
                    _run_pytest_and_exit(*tests)
                except KeyError:
                    error_and_exit(f'No tests could be found for source "{source}"')

    error_and_exit(f'Source "{source}" could not be found')


def _verify_test_list_not_empty(tests):
    if not tests:
        raise KeyError("No tests were found")


def _run_pytest_and_exit(*args):
    args = ["-v"] + list(args)
    code = pytest.main(args=args)
    sys.exit(code)


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
