import os
import platform
import shutil

import pytest
from pydantic import ValidationError

from glotter.settings import SettingsParser, Settings
from glotter.project import AcronymScheme
from glotter.singleton import Singleton

TEST_DATA_PATH = os.path.abspath(os.path.join("test", "integration", "data"))


def setup_settings_parser(tmp_dir, path, contents):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(contents)
    return SettingsParser(tmp_dir)


def test_locate_yml_when_glotter_yml_does_not_exist(tmp_dir, recwarn):
    settings_parser = SettingsParser(tmp_dir)
    assert settings_parser.yml_path == tmp_dir
    assert settings_parser.project_root == tmp_dir
    assert len(recwarn.list) == 1
    assert ".glotter.yml not found" in str(recwarn.pop(UserWarning).message)


def test_locate_yml_when_glotter_yml_does_exist(tmp_dir, glotter_yml, recwarn):
    expected = os.path.join(tmp_dir, ".glotter.yml")
    settings_parser = setup_settings_parser(tmp_dir, expected, glotter_yml)
    assert settings_parser.yml_path == expected
    assert settings_parser.project_root == tmp_dir
    assert len(recwarn.list) == 0


def test_locate_yml_when_glotter_yml_is_not_at_root(tmp_dir, glotter_yml, recwarn):
    expected = os.path.join(
        tmp_dir, "this", "is", "a", "few", "levels", "deeper", ".glotter.yml"
    )
    settings_parser = setup_settings_parser(tmp_dir, expected, glotter_yml)
    assert settings_parser.yml_path == expected
    assert len(recwarn.list) == 0


@pytest.mark.parametrize(
    ("scheme_str", "expected"),
    [
        ("upper", AcronymScheme.upper),
        ("Upper", AcronymScheme.upper),
        ("lower", AcronymScheme.lower),
        ("Lower", AcronymScheme.lower),
        ("two_letter_limit", AcronymScheme.two_letter_limit),
        ("Two_Letter_Limit", AcronymScheme.two_letter_limit),
    ],
)
def test_parse_acronym_scheme(scheme_str, expected, tmp_dir):
    glotter_yml = f'settings:\n  acronym_scheme: "{scheme_str}"'
    path = os.path.join(tmp_dir, ".glotter.yml")
    settings_parser = setup_settings_parser(tmp_dir, path, glotter_yml)
    assert settings_parser.acronym_scheme == expected


@pytest.mark.parametrize(
    ("scheme_str", "expected_error"),
    [('"bad"', "not a valid enum"), ("null", "none is not an allowed")],
)
def test_parse_acroynm_scheme_bad(scheme_str, expected_error, tmp_dir):
    glotter_yml = f"settings:\n  acronym_scheme: {scheme_str}"
    path = os.path.join(tmp_dir, ".glotter.yml")
    with pytest.raises(ValidationError) as e:
        setup_settings_parser(tmp_dir, path, glotter_yml)

    assert expected_error in str(e.value)


def test_parse_acroynm_scheme_no_settings(tmp_dir):
    path = os.path.join(tmp_dir, ".glotter.yml")
    settings_parser = setup_settings_parser(tmp_dir, path, "")
    assert settings_parser.acronym_scheme == AcronymScheme.two_letter_limit


def test_parse_source_root_when_path_absolute(tmp_dir):
    expected = os.path.abspath(os.path.join(tmp_dir, "subdir"))
    os.makedirs(expected)
    expected_escaped = expected
    if "win" in platform.platform().lower():
        expected_escaped = expected.replace("\\", "\\\\")

    glotter_yml = f'settings:\n  source_root: "{expected_escaped}"'
    path = os.path.join(tmp_dir, ".glotter.yml")
    settings_parser = setup_settings_parser(tmp_dir, path, glotter_yml)
    assert settings_parser.source_root == expected


def test_parse_source_root_when_path_relative(tmp_dir):
    expected = os.path.abspath(os.path.join(tmp_dir, "src"))
    os.makedirs(expected)
    glotter_yml = 'settings:\n  source_root: "../src"'
    path = os.path.join(tmp_dir, "subdir", ".glotter.yml")
    settings_parser = setup_settings_parser(tmp_dir, path, glotter_yml)
    assert settings_parser.source_root == expected


def test_parse_source_root_when_no_source_root(tmp_dir):
    path = os.path.join(tmp_dir, ".glotter.yml")
    settings_parser = setup_settings_parser(tmp_dir, path, "settings:")
    assert settings_parser.source_root is None


@pytest.mark.parametrize("source_root", ["[]", "{}"])
def test_parse_source_root_when_bad(source_root, tmp_dir):
    glotter_yml = f"settings:\n  source_root: {source_root}"
    path = os.path.join(tmp_dir, ".glotter.yml")
    with pytest.raises(ValidationError) as e:
        setup_settings_parser(tmp_dir, path, glotter_yml)

    assert "str type expected" in str(e.value)


def test_parse_projects_when_glotter_yml_does_not_exist(tmp_dir, recwarn):
    settings_parser = SettingsParser(tmp_dir)
    assert settings_parser.projects == {}
    assert len(recwarn.list) == 1


def test_parse_projects_when_no_projects(tmp_dir, recwarn):
    path = os.path.join(tmp_dir, ".glotter.yml")
    settings_parser = setup_settings_parser(tmp_dir, path, "")
    assert settings_parser.projects == {}
    assert len(recwarn.list) == 0


def test_parse_projects(tmp_dir, glotter_yml, glotter_yml_projects):
    path = os.path.join(tmp_dir, ".glotter.yml")
    settings_parser = setup_settings_parser(tmp_dir, path, glotter_yml)
    assert settings_parser.projects == glotter_yml_projects


def test_settings_bad_yml_type(tmp_dir):
    path = os.path.join(tmp_dir, ".glotter.yml")
    with pytest.raises(SystemExit) as e:
        setup_settings_parser(tmp_dir, path, "42")

    assert e.value.code != 0


@pytest.mark.parametrize(
    ("yml", "expected_errors"),
    [
        pytest.param(
            "settings: 42",
            ['"settings" item is not a valid dict'],
            id="bad-settings-type",
        ),
        pytest.param(
            "projects: []",
            ['"projects" item is not a valid dict'],
            id="bad-project-type",
        ),
        pytest.param(
            """\
projects:
    good:
        words:
            - "foo"
            - "bar"
    bad: "xyz"
    bad2: null
""",
            ["Project bad is not a valid dict", "Project bad2 is not a valid dict"],
            id="bad-project-item-type",
        ),
    ],
)
def test_settings_bad_item_type(yml, expected_errors, tmp_dir):
    path = os.path.join(tmp_dir, ".glotter.yml")
    with pytest.raises(ValidationError) as e:
        setup_settings_parser(tmp_dir, path, yml)

    for expected_error in expected_errors:
        assert expected_error in str(e.value)


def test_settings_good_use_tests(tmp_dir):
    valid_yml = """
                params:
                    -   name: "not sorted"
                        input: '"4, 5, 1, 3, 2"'
                        expected: '"1, 2, 3, 4, 5"'
                    -   name: "already sorted"
                        input: '"1, 2, 3, 4"'
                        expected: '"1, 2, 3, 4"'
                transformations:
                    - "strip"
"""
    invalid_yml = """
                params:
                    -   name: "no input"
                        input: null
                        expected: "Usage"
                    -   name: "empty input"
                        input: '""'
                        expected: "Usage"
                transformations:
                    - "strip"
"""
    yml = f"""\
projects:
    bubblesort:
        words:
            - "bubble"
            - "sort"
        requires_parameters: true
        tests:
            bubble_sort_valid:{valid_yml}
            bubble_sort_invalid:{invalid_yml}
    insertionsort:
        words:
            - "insertion"
            - "sort"
        use_tests:
            name: "bubblesort"
            search: "bubble_sort"
            replace: "insertion_sort"
    insertionsort:
        words:
            - "insertion"
            - "sort"
        use_tests:
            name: "bubblesort"
            search: "bubble_sort"
            replace: "insertion_sort"
    mergesort:
        words:
            - "merge"
            - "sort"
        use_tests:
            name: "bubblesort"
            search: "bubble_sort"
            replace: "merge_sort"
"""

    path = os.path.join(tmp_dir, ".glotter.yml")
    settings_parser = setup_settings_parser(tmp_dir, path, yml)

    yml = f"""\
projects:
    bubblesort:
        words:
            - "bubble"
            - "sort"
        requires_parameters: true
        tests:
            bubble_sort_valid:{valid_yml}
            bubble_sort_invalid:{invalid_yml}
    insertionsort:
        words:
            - "insertion"
            - "sort"
        requires_parameters: true
        tests:
            insertion_sort_valid:{valid_yml}
            insertion_sort_invalid:{invalid_yml}
    mergesort:
        words:
            - "merge"
            - "sort"
        requires_parameters: true
        tests:
            merge_sort_valid:{valid_yml}
            merge_sort_invalid:{invalid_yml}
"""
    expected_settings_parser = setup_settings_parser(tmp_dir, path, yml)
    assert settings_parser.projects == expected_settings_parser.projects


def test_settings_bad_use_tests(tmp_dir):
    yml = """\
projects:
    foobar:
        words:
            - "foo"
            - "bar"
        use_tests:
            name: "junk"
    barbaz:
        words:
            - "bar"
            - "baz"
        use_tests:
            name: "foobar"
    bazquux:
        words:
            - "bar"
            - "quux"
        use_tests:
            name: "pingpong"
    pingpong:
        words:
            - "ping"
            - "pong"
"""
    path = os.path.join(tmp_dir, ".glotter.yml")
    with pytest.raises(ValidationError) as e:
        setup_settings_parser(tmp_dir, path, yml)

    expected_errors = [
        'Project foobar has a "use_tests" item that refers to a non-existent project junk',
        'Project barbaz has a "use_tests" item that refers to another "use_tests" project '
        "foobar",
        'Project bazquux has a "use_tests" item that refers to project pingpong, which '
        'has no "tests" item',
    ]
    for expected_error in expected_errors:
        assert expected_error in str(e.value)


@pytest.mark.parametrize(
    ("src_filename", "expected_errors"),
    [
        pytest.param(
            "bad_settings",
            [
                "- settings -> acronym_scheme:\n    value is not a valid enumeration",
                "- settings -> source_root:\n    str type expected",
            ],
            id="bad-settings",
        ),
        pytest.param(
            "bad_projects",
            [
                "- projects -> helloworld -> words -> item 2:\n    str type expected",
                "- projects -> fibonacci -> words:\n    value is not a valid list",
                "- projects -> fibonacci -> requires_parameters:\n"
                "    value could not be parsed to a boolean",
                "- projects -> fibonacci -> acronyms -> item 1:\n    str type expected",
                "- projects -> primenumbers -> tests:\n    value is not a valid dict",
                "- projects -> insertionsort -> tests -> some_test -> params -> item 1 -> "
                'expected:\n    invalid "expected" type',
                "- projects -> insertionsort -> tests -> some_test -> transformations:\n"
                "    value is not a valid list",
                "- projects -> insertionsort -> use_tests:\n    value is not a valid dict",
                "- projects -> foo:\n    value is not a valid dict",
                "- projects -> badsort -> tests:\n"
                '    "tests" and "use_tests" items are mutually exclusive',
                "- projects -> binary_search -> tests -> test_valid -> params -> item 1 -> "
                "name:\n    field is required",
                "- projects -> binary_search -> tests -> test_valid -> params -> item 1 -> "
                "input:\n    field is required",
                "- projects -> binary_search -> tests -> test_valid -> params -> item 2:\n"
                "    argument of type 'int' is not iterable",
                "- projects -> binary_search -> tests -> test_valid -> params -> item 3 -> "
                "name:\n    value is must not be empty",
                "- projects -> binary_search -> tests -> test_valid -> params -> item 3 -> "
                "expected:\n    field is required",
                "- projects -> binary_search -> tests -> test_valid -> params -> item 4 -> "
                "name:\n    str type expected",
                "- projects -> binary_search -> tests -> test_valid -> params -> item 4 -> "
                "input:\n    str type expected",
                "- projects -> binary_search -> tests -> test_valid -> params -> item 4 -> "
                "expected:\n    str, list, or dict type expected",
                "- projects -> binary_search -> tests -> test_valid -> params -> item 5 -> "
                "expected -> item 2:\n    str type expected",
                "- projects -> binary_search -> tests -> test_valid -> params -> item 5 -> "
                "expected -> item 3:\n    str type expected",
                "- projects -> binary_search -> tests -> test_valid -> params -> item 6 -> "
                "expected:\n    too few items",
                "- projects -> binary_search -> tests -> test_valid -> params -> item 7 -> "
                "expected:\n    too many items",
                "- projects -> binary_search -> tests -> test_valid -> params -> item 8 -> "
                'expected:\n    invalid "expected" type',
                "- projects -> binary_search -> tests -> test_valid -> transformations -> "
                'item 1:\n    invalid transformation "blah"',
                "- projects -> binary_search -> tests -> test_valid -> transformations -> "
                "item 2 -> remove -> item 2:\n    str type expected",
                "- projects -> binary_search -> tests -> test_valid -> transformations -> "
                "item 3:\n    str or dict type expected",
                "- projects -> file_io -> tests -> file_io -> params -> item 1 -> expected -> "
                "exec:\n    str type expected",
                "- projects -> file_io2 -> tests -> file_io -> params -> item 1 -> expected -> "
                "exec:\n    value must not be empty",
                "- projects -> mergesort -> use_tests -> search:\n"
                '    "search" item without "replace" item',
                "?",
            ],
            id="bad-projects",
        ),
    ],
)
def test_bad_glotter_yml(
    src_filename, expected_errors, tmp_dir_chdir, clear_singleton, capsys
):
    src_path = os.path.join(TEST_DATA_PATH, src_filename)
    shutil.copy(src_path, ".glotter.yml")

    with pytest.raises(SystemExit) as e:
        Settings()

    assert e.value.code != 0

    output = capsys.readouterr().out
    for expected_error in expected_errors:
        assert expected_error in output


@pytest.fixture()
def clear_singleton():
    Singleton.clear()
    yield
    Singleton.clear()
