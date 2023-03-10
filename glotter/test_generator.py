import os
import shutil
from functools import partial
import warnings

from black import format_str, Mode

from glotter.settings import Settings

AUTO_GEN_TEST_PATH = "test/generated"


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

    for project_name, test_code in test_codes.items():
        test_generators[project_name].write_tests(test_code)


class TestGenerator:
    __test__ = False  # Indicate this is not a test

    def __init__(self, project_name, project):
        self.project_name = project_name
        self.project = project
        self.long_project_name = "_".join(self.project.words)

    def generate_tests(self):
        if not self.project.tests:
            return ""

        test_code = self._get_imports() + self._get_project_fixture()
        for test_name, test_obj in self.project.tests.items():
            if test_obj.params:
                test_code += self._generate_test(test_name, test_obj)
            else:
                self._warning(test_name, "No 'params' item... skipping")

        return format_str(test_code, mode=Mode())

    def _warning(self, test_name, msg):
        warnings.warn(f"Project '{self.project_name}', Test '{test_name}': {msg}")

    def _get_imports(self):
        test_code = "from glotter import project_test, project_fixture\n"
        if self.project.requires_parameters:
            test_code += "import pytest\n"

        return test_code

    def _get_project_fixture(self):
        return f"""\
@project_fixture("{self.project_name}")
def {self.long_project_name}(request):
    request.param.build()
    yield request.param
    request.param.cleanup()
"""

    def _generate_test(self, test_name, test_obj):
        test_code = self._get_test_function_decorator()
        func_params = ""
        run_param = ""
        if self.project.requires_parameters:
            test_code += self._generate_params(test_obj)
            func_params = "in_params, expected, "
            run_param = "params=in_params"

        test_code += self._get_test_function_and_run(test_name, func_params, run_param)
        test_code += _indent(self._get_expected_output(test_obj), 4)
        actual_var, expected_var = self._get_transformation_vars(test_name, test_obj)
        test_code += _indent(
            _get_assert(actual_var, expected_var, test_obj.params[0].expected_output), 4
        )
        return test_code

    def _get_test_function_decorator(self):
        return f'@project_test("{self.project_name}")\n'

    def _generate_params(self, test_obj):
        pytest_params = "".join(
            _indent(self._generate_param(param), 8) for param in test_obj.params
        ).strip()
        return f"""\
@pytest.mark.parametrize(
    ("in_params", "expected"),
    [
        {pytest_params}
    ]
)
"""

    def _generate_param(self, param):
        input_param = param.input_param
        if isinstance(input_param, str):
            input_param = _quote(input_param)

        expected_output = param.expected_output
        if isinstance(expected_output, str):
            expected_output = _quote(expected_output)

        return f'pytest.param({input_param}, {expected_output}, id="{param.name}"),\n'

    def _get_test_function_and_run(self, test_name, func_params, run_param):
        return f"""\
def test_{test_name}({func_params}{self.long_project_name}):
    actual = {self.long_project_name}.run({run_param})
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

        return f"expected = {expected_output}\n"

    def _generate_expected_file(self, expected_output):
        test_code = ""
        if "exec" in expected_output:
            script = _quote(expected_output["exec"])
            test_code = f"expected = {self.long_project_name}.exec({script})\n"
        elif "self" in expected_output:
            test_code = f"""\
with open({self.long_project_name}.full_path, "r", encoding="utf-8") as file:
    expected = file.read()
"""
        return test_code

    def _get_transformation_vars(self, test_name, test_obj):
        scalar_transformation_funcs = {
            "strip": partial(_append_method_to_actual, "strip"),
            "splitlines": partial(_append_method_to_actual, "splitlines"),
            "lower": partial(_append_method_to_actual, "lower"),
            "any_order": _unique_sort,
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
                self._warning(test_name, f"Invalid transformation '{key}'... ignoring")

        return actual_var, expected_var

    def write_tests(self, test_code):
        os.makedirs(AUTO_GEN_TEST_PATH, exist_ok=True)
        with open(
            os.path.join(AUTO_GEN_TEST_PATH, f"test_{self.long_project_name}.py"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(test_code)


def _quote(value):
    if '"' in value:
        quote = '"""' if "'" in value else "'"
    else:
        quote = '"'

    return f"{quote}{value}{quote}"


def _indent(str_value, num_spaces):
    spaces = " " * num_spaces
    return "".join(f"{spaces}{line}" for line in str_value.splitlines(keepends=True))


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


def _unique_sort(actual_var, expected_var):
    return f"sorted(set({actual_var}))", f"sorted(set({expected_var}))"


def _get_assert(actual_var, expected_var, expected_output):
    if isinstance(expected_output, list):
        return f"""\
actual_list = {actual_var}
expected_list = {expected_var}
assert len(actual_list) == len(expected_list), "Length not equal"
for index in range(len(expected_list)):
    assert actual_list[index] == expected_list[index], f"Item {{index + 1}} is not equal"
"""

    test_code = ""
    if actual_var != "actual":
        test_code += f"actual = {actual_var}\n"

    if expected_var != "expected":
        test_code += f"expected = {expected_var}\n"

    return f"{test_code}assert actual == expected\n"
