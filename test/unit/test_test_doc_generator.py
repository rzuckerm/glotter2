from unittest.mock import patch
import os

import pytest

from glotter.test_doc_generator import TestDocGenerator, generate_test_docs
from glotter.project import Project

REPO_NAME = "Some Repo"
REPO_URL = "https://github.com/some-user/some-repo"

NO_TESTS_PROJECT = {"words": ["no", "tests"]}
HELLO_WORLD_PROJECT = {
    "words": ["hello", "world"],
    "requires_parameters": False,
    "tests": {
        "hello_world": {
            "params": [{"expected": "Hello, world!"}],
        }
    },
}
REVERSE_STRING_PROJECT = {
    "words": ["reverse", "string"],
    "requires_parameters": True,
    "tests": {
        "reverse_string": {
            "params": [
                {
                    "name": "No input",
                    "input": None,
                    "expected": "",
                },
                {
                    "name": "Empty input",
                    "input": '""',
                    "expected": "",
                },
                {
                    "name": "Ascii String",
                    "input": '"Hello, World"',
                    "expected": "dlroW, olleH",
                },
            ]
        }
    },
}
BINARY_SEARCH_PROJECT = {
    "words": ["binary", "search"],
    "requires_parameters": True,
    "tests": {
        "binary_search_valid": {
            "inputs": ["List Input", "Target Integer Input"],
            "params": [
                {
                    "name": "sample input: first true",
                    "input": '"1, 3, 5, 7" "1"',
                    "expected": "true",
                },
                {
                    "name": "sample input: many false",
                    "input": '"1, 3, 5, 6" "7"',
                    "expected": "false",
                },
            ],
        },
        "binary_search_invalid": {
            "inputs": ["List Input", "Target Integer Input"],
            "params": [
                {"name": "no input", "input": None, "expected": "some-usage"},
                {"name": "empty input", "input": '""', "expected": "some-usage"},
            ],
        },
    },
}
DIJKSTRA_PROJECT = {
    "words": ["dijkstra"],
    "requires_parameters": True,
    "tests": {
        "dijkstra_valid": {
            "inputs": ["Matrix", "Source", "Destination"],
            "params": [
                {
                    "name": "sample input: routine",
                    "input": '"0, 2, 0, 6, 0, 2, 0, 3, 8, 5, 0, 3, 0, 0, 7, 6, 8, 0, 0, 9, 0, 5, 7, 9, 0" "0" "1"',
                    "expected": "2",
                }
            ],
        },
        "dijkstra_invalid": {
            "inputs": ["Matrix", "Source", "Destination"],
            "params": [
                {
                    "name": "no input",
                    "input": None,
                    "expected": "some-usage",
                },
                {
                    "name": "empty input",
                    "input": '"" "" ""',
                    "expected": "some-usage",
                },
            ],
        },
    },
}
DUPLICATE_CHARACTER_COUNTER_PROJECT = {
    "words": ["duplicate", "character", "counter"],
    "requires_parameters": True,
    "tests": {
        "duplicate_character_counter_valid": {
            "params": [
                {
                    "name": "sample input: no duplicates",
                    "input": '"hola"',
                    "expected": ["No duplicate characters"],
                },
                {
                    "name": "sample input: routine",
                    "input": '"goodbyeblues"',
                    "expected": ["o: 2", "b: 2", "e: 2"],
                },
            ]
        },
        "duplicate_character_counter_invalid": {
            "params": [
                {"name": "no input", "input": None, "expected": "some-usage"},
                {"name": "empty input", "input": '""', "expected": "some-usage"},
            ]
        },
    },
}
EXTRA_INPUTS_PROJECT = {
    "words": ["extra", "inputs"],
    "requires_parameters": True,
    "tests": {
        "extra_inputs": {
            "params": [
                {
                    "name": "some input 1",
                    "input": '"4" "5"',
                    "expected": "42",
                },
                {
                    "name": "some input 2",
                    "input": '"6" "7" "8"',
                    "expected": "99",
                },
            ]
        }
    },
}

UNIT_TEST_DATA_PATH = os.path.abspath(
    os.path.join("test", "unit", "data", "test_doc_generator")
)


def test_test_doc_generator_with_no_tests():
    value = NO_TESTS_PROJECT

    project = Project(**value)
    test_doc_gen = TestDocGenerator(project)

    assert test_doc_gen.generate_test_doc(REPO_NAME, REPO_URL) == ""


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(HELLO_WORLD_PROJECT, id="only-requirements"),
        pytest.param(REVERSE_STRING_PROJECT, id="single-test"),
        pytest.param(BINARY_SEARCH_PROJECT, id="mult-tests-mult-inputs"),
        pytest.param(DIJKSTRA_PROJECT, id="mult-tests-mult-inputs-single-param"),
        pytest.param(
            DUPLICATE_CHARACTER_COUNTER_PROJECT,
            id="mult-tests-mult-inputs-mult-outputs",
        ),
        pytest.param(EXTRA_INPUTS_PROJECT, id="extra-input"),
    ],
)
def test_test_generator_with_tests(value):
    project = Project(**value)

    test_gen = TestDocGenerator(project)
    doc = test_gen.generate_test_doc(REPO_NAME, REPO_URL)

    project_name_dashes = "-".join(project.words)
    with open(
        os.path.join(UNIT_TEST_DATA_PATH, f"{project_name_dashes}-testing.md"),
        encoding="utf-8",
    ) as f:
        expected_doc = f.read()

    assert doc == expected_doc


def test_generate_tests(mock_settings, temp_dir_chdir):
    generate_test_docs("generated", REPO_NAME, REPO_URL)

    filenames = os.listdir(UNIT_TEST_DATA_PATH)
    for filename in filenames:
        with open(os.path.join(UNIT_TEST_DATA_PATH, filename), encoding="utf-8") as f:
            contents = f.read()

        with open(
            os.path.join(
                "generated", filename.replace("-testing.md", f"{os.path.sep}testing.md")
            ),
            encoding="utf-8",
        ) as f:
            expected_contents = f.read()

        assert contents == expected_contents, f"{filename} contents do not match"


@pytest.fixture()
def mock_settings():
    with patch("glotter.test_doc_generator.Settings") as mock:
        mock.return_value.projects = {
            "".join(value["words"]): Project(**value)
            for value in [
                NO_TESTS_PROJECT,
                HELLO_WORLD_PROJECT,
                REVERSE_STRING_PROJECT,
                BINARY_SEARCH_PROJECT,
                DIJKSTRA_PROJECT,
                DUPLICATE_CHARACTER_COUNTER_PROJECT,
                EXTRA_INPUTS_PROJECT,
            ]
        }
        yield mock
