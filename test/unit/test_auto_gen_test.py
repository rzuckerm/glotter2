import string
import os

import pytest
from pydantic import ValidationError

from glotter.auto_gen_test import AutoGenParam, AutoGenTest


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
    assert param.dict() == expected_value


@pytest.mark.parametrize(
    ("value", "expected_error"),
    [
        pytest.param({}, "expected", id="empty"),
        pytest.param(
            {"name": None, "input": None, "expected": "some-str"},
            "name",
            id="bad-name",
        ),
        pytest.param(
            {"name": "x", "input": {"some-key": "some-value"}, "expected": "some-str"},
            "input",
            id="bad-input",
        ),
        pytest.param(
            {"name": "x", "input": "some-str", "expected": None},
            "none is not an allowed",
            id="bad-expected",
        ),
        pytest.param(
            {"name": "x", "input": "some-str", "expected": {"blah": "y"}},
            'Invalid key "blah" in "expected"',
            id="bad-expected-dict",
        ),
        pytest.param(
            {"name": "x", "input": "some-str", "expected": {"self": "", "exec": "foo"}},
            'Too many "expected" items',
            id="too-many-expected-dict",
        ),
        pytest.param(
            {"name": "x", "input": "some-str", "expected": {}},
            'Too few "expected" items',
            id="too-few-expected-dict",
        ),
        pytest.param(
            {"name": "x", "input": "some-str", "expected": {"exec": ""}},
            'No value for "exec" item in "expected"',
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
                "params": [{"name": "", "input": None, "expected": "foo"}],
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
            {"name": "test_name1", "params": []}, "at least 1 item", id="empty-params"
        ),
        pytest.param(
            {
                "name": "test_name2",
                "requires_parameters": True,
                "params": [{"input": "some-input", "expected": "some-str"}],
            },
            '"name" is not specified',
            id="missing-param-name",
        ),
        pytest.param(
            {
                "name": "test_name3",
                "requires_parameters": True,
                "params": [{"name": "", "input": "some-input", "expected": "some-str"}],
            },
            '"name" is empty',
            id="empty-param-name",
        ),
        pytest.param(
            {
                "name": "test_name3",
                "requires_parameters": True,
                "params": [{"name": "some-name", "expected": "some-str"}],
            },
            '"input" is not specified',
            id="missing-param-input",
        ),
    ],
)
def test_auto_gen_test_bad(value, expected_error):
    with pytest.raises(ValidationError) as e:
        AutoGenTest(**value)

    assert expected_error in str(e.value)


@pytest.mark.parametrize(
    ("transformations", "expected_actual_var", "expected_expected_var"),
    [
        pytest.param(["strip"], "actual.strip()", "expected", id="strip-scalar"),
        pytest.param(
            ["splitlines"], "actual.splitlines()", "expected", id="splitlines"
        ),
        pytest.param(["lower"], "actual.lower()", "expected", id="lower"),
        pytest.param(
            ["any_order"],
            "sorted(set(actual))",
            "sorted(set(expected))",
            id="any_order",
        ),
        pytest.param(
            ["strip_expected"], "actual", "expected.strip()", id="strip_expected"
        ),
        pytest.param(
            [{"remove": ["x", "y", '"']}],
            """actual.replace("x", "").replace("y", "").replace('"', "")""",
            "expected",
            id="remove",
        ),
        pytest.param(
            [{"strip": ["a", "'"]}],
            """actual.strip("a").strip("'")""",
            "expected",
            id="strip-dict",
        ),
    ],
)
def test_auto_gen_transform_vars(
    transformations, expected_actual_var, expected_expected_var
):
    value = {
        "name": "some_name",
        "params": [{"name": "some-param", "expected": "some-output"}],
        "transformations": transformations,
    }
    test = AutoGenTest(**value)

    actual_var, expected_var = test.transform_vars()
    assert actual_var == expected_actual_var
    assert expected_var == expected_expected_var


@pytest.mark.parametrize(
    ("transformation", "expected_error"),
    [
        pytest.param("foo", 'Invalid transformation "foo"', id="scalar"),
        pytest.param({"bar": ["x"]}, 'Invalid transformation "bar"', id="dict"),
        pytest.param(
            ["1", "2"], 'Invalid transformation data type "list"', id="bad-type-list"
        ),
        pytest.param(3, 'Invalid transformation data type "int"', id="bad-type-int"),
        pytest.param(
            None, 'Invalid transformation data type "NoneType"', id="bad-type-None"
        ),
        pytest.param({"strip": 32}, "not a valid list", id="bad-strip-int"),
        pytest.param(
            {"strip": {"blah": "what"}}, "not a valid list", id="bad-strip-dict"
        ),
        pytest.param(
            {"strip": ["a", 5, ["x"]]},
            "str type expected",
            id="bad-strip-bad-list-item",
        ),
        pytest.param(
            {"remove": None}, "none is not an allowed value", id="bad-remove-None"
        ),
        pytest.param(
            {"remove": [{"foo": "bar"}, "x"]},
            "str type expected",
            id="bad-remove-bad-list-item",
        ),
    ],
)
def test_auto_gen_bad_transformations(transformation, expected_error):
    value = {
        "name": "some_name",
        "params": [{"name": "some-param", "expected": "some-output"}],
        "transformations": [transformation],
    }
    with pytest.raises(ValidationError) as e:
        AutoGenTest(**value)

    assert expected_error in str(e.value)


@pytest.mark.parametrize(
    ("value", "expected_pytest_params"),
    [
        pytest.param(
            {
                "name": "name1",
                "requires_parameters": False,
                "params": [{"expected": "whatever"}],
            },
            "",
            id="no-pytest-params",
        ),
        pytest.param(
            {
                "name": "name2",
                "requires_parameters": True,
                "params": [
                    {"name": "some name 1", "input": "hello", "expected": "Hello"},
                    {"name": "some name 2", "input": "Goodbye", "expected": "Goodbye"},
                ],
            },
            """\
@pytest.mark.parametrize(
    ("in_params", "expected"),
    [
        pytest.param("hello", "Hello", id="some name 1"),
        pytest.param("Goodbye", "Goodbye", id="some name 2"),
    ]
)
""",
            id="pytest-params",
        ),
    ],
)
def test_auto_gen_test_get_pytest_params(value, expected_pytest_params):
    test = AutoGenTest(**value)
    assert test.get_pytest_params() == expected_pytest_params


@pytest.mark.parametrize(
    ("value", "project_name_underscores", "expected_value"),
    [
        pytest.param(
            {"name": "valid", "params": [{"expected": "foo"}]},
            "my_project",
            """\
def test_valid(my_project):
    actual = my_project.run()
""",
            id="no-requires-params",
        ),
        pytest.param(
            {
                "name": "something",
                "requires_parameters": True,
                "params": [{"name": "blah", "input": "foo", "expected": "bar"}],
            },
            "some_project",
            """\
def test_something(in_params, expected, some_project):
    actual = some_project.run(params=in_params)
""",
            id="requires-params",
        ),
    ],
)
def test_auto_gen_test_get_test_function_and_run(
    value, project_name_underscores, expected_value
):
    test = AutoGenTest(**value)
    assert test.get_test_function_and_run(project_name_underscores) == expected_value


@pytest.mark.parametrize(
    ("value", "project_name_underscores", "expected_value"),
    [
        pytest.param(
            {
                "name": "foo",
                "requires_parameters": True,
                "params": [{"name": "bar", "input": "bar", "expected": "foo"}],
            },
            "project1",
            "",
            id="requires-params",
        ),
        pytest.param(
            {
                "name": "name1",
                "requires_parameters": False,
                "params": [{"expected": "bar"}],
            },
            "project2",
            'expected = "bar"\n',
            id="expected-str",
        ),
        pytest.param(
            {
                "name": "name2",
                "requires_parameters": False,
                "params": [{"expected": ["12", "34"]}],
            },
            "project3",
            "expected = ['12', '34']\n",
            id="expected-list",
        ),
        pytest.param(
            {
                "name": "name3",
                "requires_parameters": False,
                "params": [{"expected": {"exec": "cat output.txt"}}],
            },
            "project4",
            'expected = project4.exec("cat output.txt")\n',
            id="expected-exec",
        ),
        pytest.param(
            {
                "name": "name4",
                "requires_parameters": False,
                "params": [{"expected": {"self": ""}}],
            },
            "project5",
            """\
with open(project5.full_path, "r", encoding="utf-8") as file:
    expected = file.read()
""",
            id="expected-self",
        ),
    ],
)
def test_auto_gen_test_get_expected_output(
    value, project_name_underscores, expected_value
):
    test = AutoGenTest(**value)
    assert test.get_expected_output(project_name_underscores) == expected_value


@pytest.mark.parametrize(
    ("value", "project_name_underscores"),
    [
        pytest.param(
            {
                "name": "hello_world",
                "requires_parameters": False,
                "params": [{"expected": "hello world"}],
            },
            "no_requires_params_string",
            id="project-no-params-string",
        ),
        pytest.param(
            {
                "name": "number_list",
                "requires_parameters": False,
                "params": [{"expected": ["1", "2"]}],
                "transformations": ["strip", "splitlines"],
            },
            "no_requires_params_list",
            id="project-no-params-list",
        ),
        pytest.param(
            {
                "name": "file_io",
                "requires_parameters": False,
                "params": [{"expected": {"exec": "cat output.txt"}}],
                "transformations": ["strip", "strip_expected"],
            },
            "no_requires_params_exec",
            id="project-no-params-exec",
        ),
        pytest.param(
            {
                "name": "quine",
                "requires_parameters": False,
                "params": [{"expected": {"self": ""}}],
                "transformations": ["strip", "strip_expected"],
            },
            "no_requires_params_self",
            id="project-no-params-self",
        ),
        pytest.param(
            {
                "name": "prime",
                "requires_parameters": True,
                "params": [
                    {"name": "one", "input": "1", "expected": "composite"},
                    {"name": "two", "input": "2", "expected": "prime"},
                    {"name": "four", "input": "4", "expected": "composite"},
                    {"name": "five", "input": "5", "expected": "prime"},
                ],
                "transformations": ["strip", "lower"],
            },
            "requires_params",
            id="project-params",
        ),
    ],
)
def test_auto_gen_test_generate_test(value, project_name_underscores):
    test = AutoGenTest(**value)

    with open(
        os.path.join("test", "unit", "data", project_name_underscores), encoding="utf-8"
    ) as f:
        expected_value = f.read()

    assert test.generate_test(project_name_underscores) == expected_value
