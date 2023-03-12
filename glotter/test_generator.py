import os
import shutil

from black import format_str, Mode

from glotter.settings import Settings
from glotter.utils import quote, indent

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
        for test_obj in self.project.tests:
            test_code += self._generate_test(test_obj)

        return format_str(test_code, mode=Mode())

    def _get_imports(self):
        test_code = "from glotter import project_test, project_fixture\n"
        if self.project.requires_parameters:
            test_code += "import pytest\n"

        return test_code

    def _get_project_fixture(self):
        return f"""\
PROJECT_NAME="{self.project_name}"
@project_fixture(PROJECT_NAME)
def {self.long_project_name}(request):
    request.param.build()
    yield request.param
    request.param.cleanup()
"""

    def _generate_test(self, test_obj):
        test_code = "@project_test(PROJECT_NAME)\n"
        func_params = ""
        run_param = ""
        if self.project.requires_parameters:
            test_code += test_obj.get_pytest_params()
            func_params = "in_params, expected, "
            run_param = "params=in_params"

        test_code += self._get_test_function_and_run(test_obj, func_params, run_param)
        test_code += indent(self._get_expected_output(test_obj), 4)
        actual_var, expected_var = test_obj.transform_vars()
        test_code += indent(
            _get_assert(actual_var, expected_var, test_obj.params[0].expected), 4
        )
        return test_code

    def _get_test_function_and_run(self, test_obj, func_params, run_param):
        return f"""\
def test_{test_obj.name}({func_params}{self.long_project_name}):
    actual = {self.long_project_name}.run({run_param})
"""

    def _get_expected_output(self, test_obj):
        if self.project.requires_parameters:
            return ""

        expected_output = test_obj.params[0].expected
        if isinstance(expected_output, dict):
            return self._generate_expected_file(expected_output)
        elif isinstance(expected_output, str):
            expected_output = quote(expected_output)
        else:
            expected_output = str(expected_output)

        return f"expected = {expected_output}\n"

    def _generate_expected_file(self, expected_output):
        test_code = ""
        if "exec" in expected_output:
            script = quote(expected_output["exec"])
            test_code = f"expected = {self.long_project_name}.exec({script})\n"
        elif "self" in expected_output:
            test_code = f"""\
with open({self.long_project_name}.full_path, "r", encoding="utf-8") as file:
    expected = file.read()
"""
        return test_code

    def write_tests(self, test_code):
        os.makedirs(AUTO_GEN_TEST_PATH, exist_ok=True)
        with open(
            os.path.join(AUTO_GEN_TEST_PATH, f"test_{self.long_project_name}.py"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(test_code)


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
