import os
import shutil

import pytest

from glotter.settings import Settings
from glotter.project import Project

UNIT_TEST_PATH = os.path.abspath(os.path.join("test", "unit"))


def test_add_test_mapping_when_project_type_not_in_projects():
    with pytest.raises(KeyError):
        Settings().add_test_mapping("notarealprojectype", None)


def test_add_test_mapping_when_project_type_has_no_mappings():
    def test_func():
        pass

    Settings().add_test_mapping("baklava", test_func)
    assert test_func.__name__ in Settings().get_test_mapping_name("baklava")


def test_add_test_mapping_when_project_type_already_has_mapping():
    def test_func():
        pass

    def test_func2():
        pass

    Settings().add_test_mapping("baklava", test_func)
    Settings().add_test_mapping("baklava", test_func2)
    assert test_func.__name__ in Settings().get_test_mapping_name("baklava")
    assert test_func2.__name__ in Settings().get_test_mapping_name("baklava")


def test_get_test_mapping_name_when_project_type_not_found():
    assert Settings().get_test_mapping_name("nonexistentproject") == []


def test_projects():
    assert Settings().projects == {
        "baklava": Project(words=["baklava"], requires_parameters=False),
        "fileio": Project(
            words=["file", "io"], requires_parameters=False, acronyms=["io"]
        ),
        "fibonacci": Project(words=["fibonacci"], requires_parameters=True),
    }


def test_project_root(temp_dir_chdir):
    copy_glotter_yml(".glotter.yml", temp_dir_chdir)

    assert Settings().project_root == temp_dir_chdir


@pytest.mark.parametrize(
    ("glotter_yml_filename", "expected_source_root"),
    [
        pytest.param(".glotter.yml", ".", id="no-source-root"),
        pytest.param(".glotter_source_root.yml", "./data", id="source-root"),
    ],
)
def test_source_root(glotter_yml_filename, expected_source_root, temp_dir_chdir):
    copy_glotter_yml(glotter_yml_filename, temp_dir_chdir)

    assert Settings().source_root == os.path.abspath(
        os.path.join(temp_dir_chdir, expected_source_root)
    )


def test_source_root_setter_empty_value(temp_dir_chdir):
    copy_glotter_yml(".glotter.yml", temp_dir_chdir)

    Settings().source_root = ""
    assert Settings().source_root == temp_dir_chdir


def test_source_root_setter_value(temp_dir_chdir):
    copy_glotter_yml(".glotter.yml", temp_dir_chdir)

    value = os.path.join(temp_dir_chdir, "data")
    Settings().source_root = value
    assert Settings().source_root == value


def copy_glotter_yml(src_filename, dest_path):
    shutil.copy(
        os.path.join(UNIT_TEST_PATH, src_filename),
        os.path.join(dest_path, ".glotter.yml"),
    )
