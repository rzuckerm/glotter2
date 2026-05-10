import os
from dataclasses import dataclass
from functools import cache
from typing import Dict, Optional

from glotter_core.project import AcronymScheme
from glotter_core.settings import CoreSettingsParser
from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)

from glotter.errors import get_error_details, raise_simple_validation_error, raise_validation_errors
from glotter.project import Project
from glotter.utils import error_and_exit, indent


@cache
def get_settings():
    """
    Get Settings as a singleton
    """
    return Settings()


class Settings:
    def __init__(self):
        self._project_root = os.getcwd()
        try:
            self._parser = SettingsParser(self._project_root)
        except ValidationError as e:
            error_and_exit(_format_validate_error(e))

        self._projects = self._parser.projects
        self._source_root = self._parser.source_root or self._project_root
        self._test_mappings = {}

    @property
    def projects(self):
        return self._projects

    @property
    def project_root(self):
        return self._project_root

    @property
    def source_root(self):
        return self._source_root

    @source_root.setter
    def source_root(self, value):
        self._source_root = value or self._project_root

    @property
    def test_mappings(self):
        return self._test_mappings

    def get_test_mapping_name(self, project_type):
        mappings = self._test_mappings.get(project_type)
        if mappings:
            return [func.__name__ for func in mappings]
        return []

    def add_test_mapping(self, project_type, func):
        if project_type not in self._projects:
            raise KeyError(f"Project type {project_type} was not found in glotter.yml")

        if project_type not in self._test_mappings:
            self._test_mappings[project_type] = []
        self._test_mappings[project_type].append(func)

    def verify_project_type(self, name):
        return name.lower() in self.projects


def _format_validate_error(validation_error: ValidationError) -> str:
    error_msgs = []
    for error in validation_error.errors():
        error_msgs.append(
            "- "
            + ".".join(
                _format_location_item(location)
                for location in error["loc"]
                if location != "__root__"
            )
            + ":"
        )
        error_msgs.append(indent(error["msg"], 4))

    return "Errors found in the following items:\n" + "\n".join(error_msgs)


def _format_location_item(location) -> str:
    if isinstance(location, int):
        return f"item {location + 1}"

    return str(location)


def _validate_use_tests_repeat(projects: object) -> list:
    errors = []

    if not isinstance(projects, dict):
        return errors

    for project_name, project in projects.items():
        if not isinstance(project, dict):
            continue

        use_tests = project.get("use_tests")
        repeat = project.get("repeat")
        if not isinstance(use_tests, dict) or not isinstance(repeat, dict):
            continue

        use_tests_name = use_tests.get("name")
        target_project = projects.get(use_tests_name)
        if not isinstance(use_tests_name, str) or not isinstance(target_project, dict):
            continue

        tests = target_project.get("tests")
        if not isinstance(tests, dict):
            continue

        search = use_tests.get("search")
        replace = use_tests.get("replace")
        if not isinstance(search, str) or not isinstance(replace, str):
            continue

        valid_test_names = {
            test_name.replace(search, replace)
            for test_name in tests.keys()
            if isinstance(test_name, str)
        }

        for repeat_name in repeat:
            if isinstance(repeat_name, str) and repeat_name not in valid_test_names:
                errors.append(
                    get_error_details(
                        f"Refers to a non-existent test name {repeat_name}",
                        ("projects", project_name, "repeat", repeat_name),
                        repeat_name,
                    )
                )

    return errors


def _convert_validation_error_to_error_details(validation_error: ValidationError) -> list:
    errors = []
    for error in validation_error.errors():
        errors.append(
            get_error_details(
                error["msg"],
                tuple(error.get("loc", ())),
                error.get("input"),
            )
        )
    return errors


class SettingsConfigSettings(BaseModel):
    acronym_scheme: AcronymScheme = Field(AcronymScheme.two_letter_limit, validate_default=True)
    yml_path: str
    source_root: Optional[str] = None

    @field_validator("acronym_scheme", mode="before")
    @classmethod
    def get_acronym_scheme(cls, value):
        if isinstance(value, str):
            return value.lower()

        return value

    @field_validator("source_root", mode="after")
    @classmethod
    def get_source_root(cls, value, info: ValidationInfo):
        if os.path.isabs(value):
            return value

        yml_dir = os.path.dirname(info.data["yml_path"])
        return os.path.abspath(os.path.join(yml_dir, value))


class SettingsConfig(BaseModel):
    yml_path: str
    settings: Optional[SettingsConfigSettings] = Field(None, validate_default=True)
    projects: Dict[str, Project] = {}

    @field_validator("settings", mode="before")
    @classmethod
    def get_settings(cls, value, info: ValidationInfo):
        if value is None:
            return {"yml_path": info.data["yml_path"]}

        if isinstance(value, dict):
            return {**value, "yml_path": info.data["yml_path"]}

        return value

    @field_validator("projects", mode="before")
    @classmethod
    def get_projects(cls, value, info: ValidationInfo):
        if not isinstance(value, dict):
            raise_simple_validation_error(cls, "Input should be a valid dictionary", value)

        acronym_scheme = info.data["settings"].acronym_scheme
        for project_name, item in value.items():
            if not isinstance(item, dict):
                continue

            value[project_name] = {**item, "acronym_scheme": acronym_scheme}

        return value

    @model_validator(mode="after")
    def validate_projects(self):
        projects = self.projects
        if not isinstance(projects, dict):
            return self

        projects_with_use_tests = {
            project_name: project for project_name, project in projects.items() if project.use_tests
        }

        errors = []
        for project_name, project in projects_with_use_tests.items():
            use_tests_name = project.use_tests.name
            loc = ("projects", project_name, "use_tests")

            # Make sure "use_tests" item refers to an actual project
            if use_tests_name not in projects:
                errors.append(
                    get_error_details(
                        f"Refers to a non-existent project {use_tests_name}",
                        loc=loc,
                        input=use_tests_name,
                    )
                )
            # Make sure one "use_tests" item does not refer to another "use_tests" item
            elif use_tests_name in projects_with_use_tests:
                errors.append(
                    get_error_details(
                        f'Refers to another "use_tests" project {use_tests_name}',
                        loc=loc,
                        input=use_tests_name,
                    )
                )
            # Make sure "use_tests" item refers to a project with tests
            elif not projects[use_tests_name].tests:
                errors.append(
                    get_error_details(
                        f'Refers to project {use_tests_name}, which has no "tests" item',
                        loc=loc,
                        input=use_tests_name,
                    )
                )
            # Otherwise, set the tests that the "use_tests" item refers to with the tests renamed
            else:
                errors += project.set_tests(
                    projects[use_tests_name], loc_prefix=("projects", project_name)
                )

        if errors:
            raise_validation_errors(self.__class__, errors)

        return self


@dataclass(frozen=True)
class SettingsParser(CoreSettingsParser):
    def __init__(self, project_root):
        try:
            super().__init__(project_root)
        except ValueError as exc:
            error_and_exit(str(exc))

        try:
            config = SettingsConfig(**self.yml, yml_path=self.yml_path)
        except ValidationError as exc:
            extra_errors = _validate_use_tests_repeat(self.yml.get("projects", {}))
            if extra_errors:
                combined_errors = _convert_validation_error_to_error_details(exc) + extra_errors
                raise ValidationError.from_exception_data(
                    title=SettingsConfig.__name__,
                    line_errors=combined_errors,
                )
            raise

        object.__setattr__(self, "acronym_scheme", config.settings.acronym_scheme)
        object.__setattr__(self, "source_root", config.settings.source_root)
        object.__setattr__(self, "projects", config.projects)
