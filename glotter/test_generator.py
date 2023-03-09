import os
import shutil
from functools import partial

from black import format_str, Mode

from glotter.settings import Settings

AUTO_GEN_TEST_PATH = ".generated"


def generate_tests():
    """
    Generate tests for all projects
    """

    shutil.rmtree(AUTO_GEN_TEST_PATH, ignore_errors=True)
    settings = Settings()
    test_generators = {
        project_name: TestGenerator(project_name, project)
        for project_name, project in settings.projects.items()
    }
    test_codes = {}
    for project_name, test_generator in test_generators.items():
        test_code = test_generator.generate_tests()
        if test_code:
            test_codes[project_name] = test_code

    for project_name, test_code in test_codes.item():
        test_generators[project_name].write_tests(test_code)


class TestGenerator:
    def __init__(self, project_name, project):
        self.project_name = project_name
        self.project = project

    def generate_tests(self):
        if not self.project.tests:
            return ""

        test_code = self._generate_fixture()
        for test_name, test_obj in self.project.tests.items():
            test_code += self._generate_test(test_name, test_obj)

        return format_str(test_code, mode=Mode())

    def _generate_fixture(self):
        return f"""\
from glotter import project_test, project_fixture
@project_filter("{self.project_name}")
def {self._get_fixture_name()}(request):
    request.param.build()
    yield request.param
    request.param.cleanup()
"""

    def _get_fixture_name(self):
        return "_".join(self.project.words)

    def _generate_test(self, test_name, test_obj):
        test_code = f"""\
@project_test("{self.project_name}")
"""
        func_params = ""
        run_param = ""
        if self.project.requires_parameters:
            test_code += self._generate_params(test_obj)
            func_params = "in_param, expected, "
            run_param = "param=in_param"

        fixture_name = self._get_fixture_name()
        test_code += f"""\
def test_{test_name}({func_params}{fixture_name}):
    actual = {fixture_name}.run({run_param})
"""
        test_code += self._get_expected_output(test_obj)
        actual_var, expected_var = self._get_transformation_vars(test_name, test_obj)
        test_code += _get_assert(
            actual_var, expected_var, test_obj.params[0].expected_output
        )
        return test_code

    def _generate_params(self, test_obj):
        pytest_params = ""
        for param in test_obj.params:
            input_param = _quote(param.input_param)
            expected_output = param.expected
            if isinstance(expected_output, str):
                expected_output = _quote(expected_output)

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

    def _get_expected_output(self, test_obj):
        if self.project.requires_parameters:
            return ""

        expected_output = test_obj.params[0].expected_output
        if isinstance(expected_output, dict):
            return self._generate_expected_file(expected_output)
        elif isinstance(expected_output, str):
            expected_output = _quote(expected_output)
        else:
            expected_output = str(expected_output)

        return f"""\
    expected = {expected_output}
"""

    def _generate_expected_file(self, expected_output):
        test_code = ""
        fixture_name = self._get_fixture_name()
        if "exec" in expected_output:
            script = _quote(expected_output["exec"])
            test_code = f"""\
    expected = {fixture_name}.exec({script})
"""
        elif "self" in expected_output:
            test_code = f"""\
    with open({fixture_name}.full_path, "r", encoding="utf-8") as file:
        expected = file.read()
"""
        return test_code

    def _get_transformation_vars(self, test_name, test_obj):
        scalar_transformation_funcs = {
            "strip": partial(_append_method_to_actual, "strip"),
            "splitlines": partial(_append_method_to_actual, "splitlines"),
            "lower": partial(_append_method_to_actual, "lower"),
            "any_order": partial(_apply_method_to_both, "set"),
            "strip_expected": partial(_append_method_to_expected, "strip"),
        }
        dict_transformation_funcs = {
            "remove": _remove_chars,
            "strip": _strip_chars,
        }

        actual_var = "actual"
        expected_var = "expected"
        for transformation in test_obj.transformations:
            bad_key = ""
            if isinstance(transformation, str):
                key = transformation
                try:
                    actual_var, expected_var = scalar_transformation_funcs[
                        transformation
                    ](actual_var, expected_var)
                except KeyError:
                    bad_key = transformation
            else:
                key, value = tuple(*transformation.items())
                try:
                    actual_var, expected_var = dict_transformation_funcs[key](
                        actual_var, expected_var, value
                    )
                except KeyError:
                    bad_key = key

            if bad_key:
                print(
                    f"WARNING: Invalid transformation '{key}' for project {self.project_name}, "
                    f"test case {test_name}"
                )

        return actual_var, expected_var

    def write_tests(self, test_code):
        os.makedirs(AUTO_GEN_TEST_PATH, exist_ok=True)
        with open(
            os.path.join(AUTO_GEN_TEST_PATH, f"{self.project_name}.py"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(test_code)


def _quote(str_value):
    return str_value.replace('"', '\\"')


def _append_method_to_actual(method, actual_var, expected_var):
    return f"{actual_var}.{method}()", expected_var


def _append_method_to_expected(method, actual_var, expected_var):
    return actual_var, f"{expected_var}.{method}()"


def _remove_chars(actual_var, expected_var, values):
    for value in values:
        actual_var += f".replace({_quote(value)}, '')"

    return actual_var, expected_var


def _strip_chars(actual_var, expected_var, values):
    for value in values:
        actual_var += f".strip({_quote(value)})"

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
