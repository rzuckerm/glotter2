import os
import shlex

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
    for project in settings.projects.values():
        test_doc_generator = TestDocGenerator(project)
        doc = test_doc_generator.generate_test_doc(repo_name, repo_url)
        if doc:
            project_dir = os.path.join(doc_dir, "-".join(project.words))
            os.makedirs(project_dir)
            project_doc_path = os.path.join(project_dir, "testing.md")
            with open(os.path.join(project_doc_path), "w", encoding="utf-8") as f:
                f.write(doc)


class TestDocGenerator:
    __test__ = False  # Indicate this is not a test

    def __init__(self, project):
        self.project = project
        self.project_title = " ".join(self.project.words).title()

    def generate_test_doc(self, repo_name, repo_url):
        if not self.project.tests:
            return ""

        doc = self._get_test_intro(repo_name, repo_url)
        if self.project.requires_parameters:
            for test_obj in self.project.tests.values():
                test_doc_section_generator = TestDocSectionGenerator(test_obj)
                doc += test_doc_section_generator.get_test_section()

        return "\n".join(doc).rstrip() + "\n"

    def _get_test_intro(self, repo_name, repo_url):
        if not self.project.requires_parameters:
            return [
                "Verify that the actual output matches the expected output",
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
            ]

        return doc + [""]


def _get_test_section_title(test_obj):
    return test_obj.name.replace("_", " ").title() + " Tests"


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
        cells = ["Description"] + self.test_obj.inputs
        if self._any_test_output_is_different():
            cells.append("Output")

        return [
            _cells_to_table_line(cells),
            _cells_to_table_line("-" * len(cell) for cell in cells),
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
            cells = [test_param.name.title()]
            if test_param.input is None:
                inputs = []
            else:
                inputs = shlex.split(test_param.input)
                extra_inputs = inputs[num_input_params:]
                inputs = inputs[:num_input_params]
                cells += [quote(value) for value in inputs]
                if extra_inputs:
                    cells[-1] += " " + " ".join(quote(value) for value in extra_inputs)

            cells += [""] * (num_input_params - len(inputs))

            if has_output_column:
                if isinstance(output, str):
                    cells.append(quote(output))
                else:
                    cells.append("<br>".join(quote(item) for item in output))

            doc.append(_cells_to_table_line(cells))

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


def _cells_to_table_line(cells):
    return "| " + " | ".join(cells) + " |"
