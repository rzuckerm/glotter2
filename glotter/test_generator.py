import os
import shlex
from functools import partial

from black import format_str, Mode

from glotter.settings import Settings


def test_generator():
    """
    Generate tests for all projects
    """

    settings = Settings()
    for project_name, project in settings.projects.items():
        test_code = _generate_tests(project_name, project)
        if test_code:
            test_code = format_str(test_code, mode=Mode())
            _write_tests(".generated", project_name, test_code)


def _generate_tests(project_name, project):
    if not project.tests:
        return ""

    test_code = _generate_fixture(project_name, project)
    for test_name, test_obj in project.tests.items():
        test_code += _generate_test(project_name, project, test_name, test_obj)
    return test_code


def _generate_fixture(project_name, project):
    return f"""\
from glotter import project_test, project_fixture
@project_filter("{project_name}")
def {_get_fixture_name(project)}:
    request.param.build()
    yield request.param
    request.param.cleanup()
"""


def _get_fixture_name(project):
    return "_".join(project.words)


def _generate_test(project_name, project, test_name, test_obj):
    test_code = f'@project_test("{project_name}")'
    func_params = ""
    run_param = ""
    if project.requires_parameters:
        test_code += _generate_params(test_obj)
        func_params = "in_param, expected, "
        run_param = "param=in_param"

    fixture_name = _get_fixture_name(project)
    test_code += f"""\
def test_{test_name}({func_params}{fixture_name}:
    actual = {fixture_name}.run({run_param})
"""
    test_code += _get_expected_output(project, test_obj)
    actual_var, expected_var = _get_filtered_vars(test_obj)
    test_code += _get_assert(
        actual_var, expected_var, test_obj.params[0].expected_output
    )
    return test_code


def _generate_params(test_obj):
    pytest_params = ""
    for param in test_obj.params:
        input_param = shlex.quote(param.input_param)
        expected_output = param.expected_output
        if isinstance(expected_output, str):
            expected_output = shlex.quote(expected_output)

        pytest_params += f"""\
        pytest.param(
            "{input_param}",
            {expected_output},
            id="{param.name}"
        ),
"""

    return f"""\
@pytest.mark.parametrize(
    ("in_param", "expected")
    [
        {pytest_params}
    ]
)
"""


def _get_expected_output(project, test_obj):
    if project.requires_parameters:
        return ""

    expected_output = test_obj.expected_output
    if isinstance(expected_output, dict):
        return _generate_expected_file(expected_output, project)
    elif isinstance(expected_output, str):
        expected_output = shlex.quote(expected_output)
    else:
        expected_output = str(expected_output)

    return f"    expected = {expected_output}"


def _generate_expected_file(expected_output, project):
    test_code = ""
    fixture_name = _get_fixture_name(project)
    if "exec" in expected_output:
        script = shlex.quote(expected_output["exec"])
        test_code = f"""\
    expected = {fixture_name}.exec({script})
"""
    elif "self" in expected_output:
        test_code = f"""\
    with open({fixture_name}.full_path, "r", encoding="utf-8") as file:
        expected = file.read()
"""
    return test_code


def _get_filtered_vars(test_obj):
    scalar_test_output_funcs = {
        "strip": partial(_append_method_to_actual, "strip"),
        "splitlines": partial(_append_method_to_actual, "splitlines"),
        "lower": partial(_append_method_to_actual, "lower"),
        "any_order": partial(_apply_method_to_both, "set"),
        "strip_expected": partial(_append_method_to_expected, "strip"),
    }
    dict_test_output_funcs = {
        "remove": _remove_chars,
        "strip": _strip_chars,
    }

    actual_var = "actual"
    expected_var = "expected"
    for test_output_filter in test_obj.test_output_filters:
        try:
            if isinstance(test_output_filter, str):
                actual_var, expected_var = scalar_test_output_funcs[test_output_filter](
                    actual_var, expected_var
                )
            else:
                key, value = tuple(*test_output_filter.items())
                actual_var, expected_var = dict_test_output_funcs[key](
                    actual_var, expected_var, value
                )
        except KeyError:
            continue

    return actual_var, expected_var


def _append_method_to_actual(method, actual_var, expected_var):
    return f"{actual_var}.{method}()", expected_var


def _append_method_to_expected(method, actual_var, expected_var):
    return actual_var, f"{expected_var}.{method}()"


def _remove_chars(actual_var, expected_var, values):
    for value in values:
        actual_var += f".replace({shlex.quote(value)}, '')"

    return actual_var, expected_var


def _strip_chars(actual_var, expected_var, values):
    for value in values:
        actual_var += f".strip({shlex.quote(value)})"

    return actual_var, expected_var


def _apply_method_to_both(method, actual_var, expected_var):
    return f"{method}({actual_var}), {method}({expected_var})"


def _get_assert(actual_var, expected_var, expected_output):
    if isinstance(expected_output, str):
        return f"""\
    assert {actual_var} == {expected_var}
"""

    return f"""\
    actual_list = {actual_var}
    expected_list = {expected_var}
    assert len(actual_list) == len(expected_list), "Length not equal"
    for index in range(len(expected_list)):
        assert actual_list[index] == expected_list[index], f"Item {{index + 1}} is not equal"
"""


def _write_tests(path, project_name, test_code):
    os.makedirs(path, exist_ok=True)
    with open(os.path.join(path, f"{project_name}.py"), "w", encoding="utf-8") as f:
        f.write(test_code)
