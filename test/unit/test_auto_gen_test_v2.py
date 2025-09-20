import os
import string

import pytest
from pydantic import ValidationError

from glotter.auto_gen_test_v2 import AutoGenParam

UNIT_TEST_DATA_PATH = os.path.abspath(os.path.join("test", "unit", "data", "auto_gen_test"))

VALID_CHARS = string.ascii_letters + string.digits + "_"
BAD_NAMES = ["a#xyz", "z_x blah", "yoo-hoo"]


@pytest.mark.parametrize(
    ("value", "expected_value"),
    [
        pytest.param(
            {"expected": "hello"},
            {"name": "", "input": None, "expected": "hello"},
            id="expected_only",
        ),
        pytest.param(
            {"name": "input1", "input": None, "expected": "some-str"},
            {"name": "input1", "input": None, "expected": "some-str"},
            id="input_None-expected_str",
        ),
        pytest.param(
            {
                "name": "input2",
                "input": "some-input-str",
                "expected": ["some-item1", "some-item2"],
            },
            {
                "name": "input2",
                "input": "some-input-str",
                "expected": ["some-item1", "some-item2"],
            },
            id="input_str-expected_list",
        ),
        pytest.param(
            {
                "name": "input3",
                "input": "some-input-str",
                "expected": {"exec": "cat output.txt"},
            },
            {
                "name": "input3",
                "input": "some-input-str",
                "expected": {"exec": "cat output.txt"},
            },
            id="input_str-expected_exec",
        ),
        pytest.param(
            {
                "name": "input4",
                "input": "some-input-str",
                "expected": {"self": ""},
            },
            {
                "name": "input4",
                "input": "some-input-str",
                "expected": {"self": ""},
            },
            id="input_str-expected_self",
        ),
    ],
)
def test_auto_gen_param_good(value, expected_value):
    param = AutoGenParam(**value)
    assert param.model_dump() == expected_value


@pytest.mark.parametrize(
    ("value", "expected_error"),
    [
        pytest.param(
            {"name": None, "input": None, "expected": "some-str"},
            "name\n  Input should be a valid string",
            id="bad-name",
        ),
        pytest.param(
            {"name": "x", "input": {"some-key": "some-value"}, "expected": "some-str"},
            "input\n  Input should be a valid string",
            id="bad-input",
        ),
        pytest.param(
            {"name": "x", "input": "some-str", "expected": None},
            "expected\n  str, list, or dict type expected",
            id="bad-expected",
        ),
        pytest.param(
            {"name": "x", "input": "some-str", "expected": {"blah": "y"}},
            'expected\n  invalid "expected" type',
            id="bad-expected-dict",
        ),
        pytest.param(
            {"name": "x", "input": "some-str", "expected": {"self": "", "exec": "foo"}},
            "expected\n  too many items",
            id="too-many-expected-dict",
        ),
        pytest.param(
            {"name": "x", "input": "some-str", "expected": {}},
            "expected\n  too few items",
            id="too-few-expected-dict",
        ),
        pytest.param(
            {"name": "x", "input": "some-str", "expected": {"exec": ""}},
            "expected.exec\n  value must not be empty",
            id="empty-expected-exec",
        ),
    ],
)
def test_auto_gen_param_bad(value, expected_error):
    with pytest.raises(ValidationError) as e:
        AutoGenParam(**value)

    assert expected_error in str(e.value)


@pytest.mark.parametrize(
    ("value", "expected_pytest_param"),
    [
        pytest.param({"expected": "blah"}, "", id="only_expected"),
        pytest.param(
            {"name": "some name", "expected": "blah"},
            'pytest.param(None, "blah", id="some name"),\n',
            id="no_input-expected_str",
        ),
        pytest.param(
            {"name": "other name", "input": '"55, 56"', "expected": "blah"},
            """pytest.param('"55, 56"', "blah", id="other name"),\n""",
            id="input_str-expected_str",
        ),
        pytest.param(
            {"name": "this name", "input": "blah", "expected": ["1", "2", "3"]},
            """pytest.param("blah", ['1', '2', '3'], id="this name"),\n""",
            id="input_str-expected_list",
        ),
        pytest.param(
            {
                "name": "this name",
                "input": "blah",
                "expected": {"exec": "cat output.txt"},
            },
            """pytest.param("blah", {'exec': 'cat output.txt'}, id="this name"),\n""",
            id="input_str-expected_dict",
        ),
    ],
)
def test_auto_gen_param_get_pytest_param(value, expected_pytest_param):
    param = AutoGenParam(**value)
    assert param.get_pytest_param() == expected_pytest_param
