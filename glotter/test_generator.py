import os
import shutil

from black import format_str, Mode

from glotter.settings import Settings

AUTO_GEN_TEST_PATH = os.path.join("test", "generated")


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
        for test_obj in self.project.tests.values():
            test_code += test_obj.generate_test(self.long_project_name)

        return format_str(test_code, mode=Mode())

    def _get_imports(self):
        test_code = ""
        if self.project.requires_parameters:
            test_code += "import pytest\n"

        test_code += "from glotter import project_test, project_fixture\n"
        return test_code

    def _get_project_fixture(self):
        return f"""\
PROJECT_NAME="{self.project_name}"
@project_fixture(PROJECT_NAME)
def {self.long_project_name}(request):
    try:
        request.param.build()
        yield request.param
    finally:
        request.param.cleanup()
"""

    def write_tests(self, test_code):
        os.makedirs(AUTO_GEN_TEST_PATH, exist_ok=True)
        with open(
            os.path.join(AUTO_GEN_TEST_PATH, f"test_{self.long_project_name}.py"),
            "w",
            encoding="utf-8",
        ) as f:
            f.write(test_code)
