import string

import pytest
from pydantic import ValidationError

from glotter.auto_gen_test import AutoGenParam, AutoGenTest


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(
            {"name": "input1", "input": None, "expected": "some-str"},
            id="input_None-expected_str",
        ),
        pytest.param(
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
                "expected": {"some-key": "some-value"},
            },
            id="input_str-expected_dict",
        ),
    ],
)
def test_auto_gen_param_good(value):
    param = AutoGenParam(**value)
    assert param.dict() == value


@pytest.mark.parametrize(
    "value",
    [
        pytest.param({}, id="empty"),
        pytest.param(
            {"name": None, "input": None, "expected": "some-str"},
            id="bad-name",
        ),
        pytest.param(
            {"name": "", "input": None, "expected": "some-str"},
            id="empty-name",
        ),
        pytest.param(
            {"name": None, "input": {"some-key": "some-value"}, "expected": "some-str"},
            id="bad-input",
        ),
        pytest.param(
            {"name": None, "input": "some-str", "expected": 42},
            id="bad-expected",
        ),
    ],
)
def test_auto_gen_param_bad(value):
    with pytest.raises(ValidationError):
        AutoGenParam(**value)


@pytest.mark.parametrize(
    ("value", "expected_value"),
    [
        pytest.param(
            {
                "name": char,
                "params": [{"name": "some-name", "expected": "some-str"}],
                "transformations": ["strip"],
            },
            {
                "name": char,
                "requires_parameters": False,
                "params": [
                    {"name": "some-name", "input": None, "expected": "some-str"}
                ],
                "transformations": ["strip"],
            },
            id=f"name_{char}-single_param-single_transformation",
        )
        for char in string.ascii_letters
    ]
    + [
        pytest.param(
            {"name": "some_name", "params": [{"expected": "foo"}]},
            {
                "name": "some_name",
                "requires_parameters": False,
                "params": [{"name": "na", "input": None, "expected": "foo"}],
                "transformations": [],
            },
            id="no_param_name",
        )
    ]
    + [
        pytest.param(
            {
                "name": f"foo_{char}_bar",
                "params": [{"name": "some-name", "expected": "some-str"}],
                "transformations": ["strip"],
            },
            {
                "name": f"foo_{char}_bar",
                "requires_parameters": False,
                "params": [
                    {"name": "some-name", "input": None, "expected": "some-str"}
                ],
                "transformations": ["strip"],
            },
            id=f"name_foo_{char}_bar-single_param-single_transformation",
        )
        for char in string.ascii_letters + string.digits + "_"
    ]
    + [
        pytest.param(
            {
                "name": "test_name2",
                "requires_parameters": True,
                "params": [
                    {
                        "name": "some-name1",
                        "input": "some-input1",
                        "expected": ["item1", "item2"],
                    },
                    {
                        "name": "some-name2",
                        "input": "some-input2",
                        "expected": ["item3"],
                    },
                ],
                "transformations": ["strip", "splitlines"],
            },
            {
                "name": "test_name2",
                "requires_parameters": True,
                "params": [
                    {
                        "name": "some-name1",
                        "input": "some-input1",
                        "expected": ["item1", "item2"],
                    },
                    {
                        "name": "some-name2",
                        "input": "some-input2",
                        "expected": ["item3"],
                    },
                ],
                "transformations": ["strip", "splitlines"],
            },
            id="muli_param-multi_transformation",
        ),
    ],
)
def test_auto_gen_test_good(value, expected_value):
    test = AutoGenTest(**value)
    assert test.dict() == expected_value


@pytest.mark.parametrize(
    ("value", "expected_error"),
    [
        pytest.param(
            {"params": [{"name": "some-name", "expected": "some-str"}]},
            "name",
            id="no-name",
        ),
        pytest.param(
            {"name": "", "params": [{"name": "some-name", "expected": "some-str"}]},
            "value has at least 1 character",
            id="empty-name",
        ),
        pytest.param(
            {"name": "9", "params": [{"name": "some-name", "expected": "some-str"}]},
            "does not match regex",
            id="name-start-with-number",
        ),
    ]
    + [
        pytest.param(
            {
                "name": bad_name,
                "params": [{"name": "some-name", "expected": "some-str"}],
            },
            "does not match regex",
            id=f"name-has-bad-chars-{bad_name}",
        )
        for bad_name in ["a#xyz", "z_x blah", "yoo-hoo"]
    ]
    + [
        pytest.param(
            {"name": "test-name1", "params": []}, "at least 1 item", id="empty-params"
        ),
        pytest.param(
            {
                "name": "test-name2",
                "requires_parameters": True,
                "params": [{"name": "some-name", "expected": "some-str"}],
            },
            "input",
            id="missing-input",
        ),
    ],
)
def test_auto_gen_test_bad(value, expected_error):
    with pytest.raises(ValidationError) as e:
        AutoGenTest(**value)

    assert expected_error in str(e.value)
