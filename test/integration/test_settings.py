import os
import platform

import pytest
from pydantic import ValidationError

from glotter.settings import SettingsParser
from glotter.project import AcronymScheme


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
