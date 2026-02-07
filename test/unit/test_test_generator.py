import os
from unittest.mock import patch

import pytest

from glotter.project import Project
from glotter.test_generator import AUTO_GEN_TEST_PATH, TestGenerator, generate_tests

NO_TESTS_PROJECT = {"words": ["no", "tests"]}
HELLO_WORLD_PROJECT = {
    "words": ["hello", "world"],
    "requires_parameters": False,
    "tests": {
        "hello_world": {
            "params": [{"expected": "Hello, world!"}],
            "transformations": ["strip"],
        }
    },
}
PRIME_NUMBER_PROJECT = {
    "words": ["prime", "number"],
    "requires_parameters": True,
    "tests": {
        "prime_number_valid": {
            "params": [
                {"name": "one", "input": "1", "expected": "composite"},
                {"name": "two", "input": "2", "expected": "prime"},
                {"name": "four", "input": "4", "expected": "composite"},
                {"name": "five", "input": "5", "expected": "prime"},
            ],
            "transformations": ["strip", "lower"],
        },
        "prime_number_invalid": {
            "params": [
                {
                    "name": "no input",
                    "input": None,
                    "expected": "some error",
                },
                {
                    "name": "empty input",
                    "input": '""',
                    "expected": "some error",
                },
                {
                    "name": "bad input",
                    "input": '"a"',
                    "expected": "some error",
                },
            ],
            "transformations": ["strip"],
        },
    },
}
ROT13_PROJECT = {
    "words": ["rot13"],
    "requires_parameters": True,
    "strings": {"usage": "Usage: please provide a string to encrypt"},
    "tests": {
        "rot13_valid": {
            "params": [
                {
                    "name": "sample input lower case",
                    "input": '"the quick brown fox jumped over the lazy dog"',
                    "expected": "gur dhvpx oebja sbk whzcrq bire gur ynml qbt",
                },
                {
                    "name": "sample input upper case",
                    "input": '"THE QUICK BROWN FOX JUMPED OVER THE LAZY DOG"',
                    "expected": "GUR DHVPX OEBJA SBK WHZCRQ BIRE GUR YNML QBT",
                },
            ],
            "transformations": ["strip"],
        },
        "rot13_invalid": {
            "params": [
                {
                    "name": "no input",
                    "input": None,
                    "expected": {"string": "usage"},
                },
                {
                    "name": "empty input",
                    "input": '""',
                    "expected": {"string": "usage"},
                },
            ],
            "transformations": ["strip"],
        },
    },
}

UNIT_TEST_DATA_PATH = os.path.abspath(os.path.join("test", "unit", "data", "test_generator"))


def test_test_generator_with_no_tests():
    value = NO_TESTS_PROJECT

    project = Project(**value)
    project_name = "".join(project.words)
    test_gen = TestGenerator(project_name, project)

    assert test_gen.generate_tests() == ""


@pytest.mark.parametrize(
    ("value"),
    [
        pytest.param(HELLO_WORLD_PROJECT, id="no-requires-params"),
        pytest.param(PRIME_NUMBER_PROJECT, id="requires-params"),
        pytest.param(ROT13_PROJECT, id="requires-params-with-strings"),
    ],
)
def test_test_generator_with_tests(value):
    project = Project(**value)

    project_name = "".join(project.words)
    test_gen = TestGenerator(project_name, project)
    test_code = test_gen.generate_tests()

    project_name_underscores = "_".join(project.words)
    with open(
        os.path.join(UNIT_TEST_DATA_PATH, project_name_underscores),
        encoding="utf-8",
    ) as f:
        expected_test_code = f.read()

    assert test_code == expected_test_code


def test_generate_tests(mock_settings, temp_dir_chdir):
    generate_tests()

    filenames = ["test_hello_world.py", "test_prime_number.py", "test_rot13.py"]
    assert sorted(os.listdir(AUTO_GEN_TEST_PATH)) == sorted(filenames)

    for filename in filenames:
        with open(
            os.path.join(UNIT_TEST_DATA_PATH, filename.replace("test_", "").replace(".py", "")),
            encoding="utf-8",
        ) as f:
            contents = f.read()

        with open(os.path.join(AUTO_GEN_TEST_PATH, filename), encoding="utf-8") as f:
            expected_contents = f.read()

        assert contents == expected_contents, f"{filename} contents do not match"


@pytest.fixture()
def mock_settings():
    with patch("glotter.test_generator.get_settings") as mock:
        mock.return_value.projects = {
            "".join(value["words"]): Project(**value)
            for value in [
                NO_TESTS_PROJECT,
                HELLO_WORLD_PROJECT,
                PRIME_NUMBER_PROJECT,
                ROT13_PROJECT,
            ]
        }
        yield mock
