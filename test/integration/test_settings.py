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
