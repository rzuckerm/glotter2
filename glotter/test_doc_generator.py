import os
import shlex
from contextlib import suppress

from glotter.settings import Settings
from glotter.utils import quote


def generate_test_docs(doc_dir, repo_name, repo_url):
    """
    Generate test documentation for all projects

    :param doc_dir: Documentation directory
    :param repo_name: Repository name
    :param repo_url: Repository URL
    """

    settings = Settings()
    for project_name, project in settings.projects.items():
        test_doc_generator = TestDocGenerator(project_name, project, doc_dir)
        test_doc_generator.generate_test_doc(repo_name, repo_url)


def remove_generated_test_docs(doc_dir):
    settings = Settings()
    for project_name, project in settings.projects.items():
        test_doc_generator = TestDocGenerator(project_name, project, doc_dir)
        test_doc_generator.remove_test_doc()


class TestDocGenerator:
    __test__ = False  # Indicate this is not a test

    def __init__(self, project_name, project, doc_dir):
        self.project_name = project_name
        self.project = project
        self.project_dir = os.path.join(doc_dir, "-".join(self.project.words))
        self.project_title = " ".join(self.project.words).title()
        self.testing_path = os.path.join(self.project_dir, "testing.md")

    def generate_test_doc(self, repo_name, repo_url):
        if not self.project.tests:
            return

        doc = self._get_test_intro(repo_name, repo_url)
        if self.project.requires_parameters:
            for test_obj in self.project.tests.values():
                test_doc_section_generator = TestDocSectionGenerator(test_obj)
                doc += test_doc_section_generator.get_test_section()

        os.makedirs(self.project_dir, exist_ok=True)
        with open(self.testing_path, "w", encoding="utf-8") as f:
            f.write("\n".join(doc).rstrip() + "\n")

    def remove_test_doc(self):
        if not self.project.tests:
            return

        with suppress(OSError):
            os.remove(self.testing_path)

    def _get_test_intro(self, repo_name, repo_url):
        if not self.project.requires_parameters:
            return [
                "Verify that the actual output matches the expected output ",
                "(see [Requirements](#requirements)).",
            ]

        doc = [
            f"Every project in the [{repo_name} repo]({repo_url}) should be tested.",
            f"In this section, we specify the set of tests specific to {self.project_title}.",
        ]
        if len(self.project.tests) > 1:
            doc += [
                "In order to keep things simple, we split up the testing as follows:",
                "",
            ]
            doc += [
                "- " + _get_test_section_title(test_obj)
                for test_obj in self.project.tests.values()
            ] + [""]

        return doc


def _get_test_section_title(test_obj):
    return test_obj.name.replace("_", " ").title()


class TestDocSectionGenerator:
    __test__ = False  # Indicate this is not a test

    def __init__(self, test_obj):
        self.test_obj = test_obj
        self.test_obj_name = _get_test_section_title(test_obj)

    def get_test_section(self):
        return (
            self._get_test_section_header()
            + self._get_test_table_header()
            + self._get_test_table()
        )

    def _get_test_section_header(self):
        return [f"### {self.test_obj_name}", ""]

    def _get_test_table_header(self):
        columns = ["Description"] + self.test_obj.inputs
        if self._any_test_output_is_different():
            columns.append("Output")

        return [
            "| " + " | ".join(columns) + " |",
            "| " + " | ".join("-" * len(column) for column in columns) + " |",
        ]

    def _any_test_output_is_different(self):
        if len(self.test_obj.params) < 2:
            return True

        first_expected = self.test_obj.params[0].expected
        return any(
            test_param.expected != first_expected
            for test_param in self.test_obj.params[1:]
        )

    def _get_test_table(self):
        doc = []
        has_output_column = self._any_test_output_is_different()
        num_input_params = len(self.test_obj.inputs)
        for test_param in self.test_obj.params:
            output = test_param.expected
            columns = [test_param.name.title()]
            if test_param.input is None:
                inputs = []
            else:
                inputs = shlex.split(test_param.input)[:num_input_params]
                columns += [quote(value) for value in inputs]

            columns += [""] * (num_input_params - len(inputs))

            if has_output_column:
                if isinstance(output, str):
                    columns.append(quote(output))
                else:
                    columns.append("<br>".join(quote(item) for item in output))

            doc.append("| " + " | ".join(columns) + " |")

        if not has_output_column:
            doc += [
                "",
                "All of these tests should output the following:",
                "",
                "```",
                self.test_obj.params[0].expected,
                "```",
            ]

        return doc + [""]
