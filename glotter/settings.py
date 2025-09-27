import os
from typing import Dict, Optional
from warnings import warn

import yaml
from pydantic import (
    BaseModel,
    Field,
    ValidationError,
    ValidationInfo,
    field_validator,
    model_validator,
)

from glotter.errors import get_error_details, raise_simple_validation_error, raise_validation_errors
from glotter.project import AcronymScheme, Project
from glotter.singleton import Singleton
from glotter.utils import error_and_exit, indent


class Settings(metaclass=Singleton):
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
                break

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
                project.set_tests(projects[use_tests_name])

        if errors:
            raise_validation_errors(self.__class__, errors)

        return self


class SettingsParser:
    def __init__(self, project_root):
        self._project_root = project_root
        self._yml_path = None
        self._acronym_scheme = None
        self._projects = None
        self._source_root = None
        self._yml_path = self._locate_yml()

        yml = None
        if self._yml_path is not None:
            yml = self._parse_yml()
        else:
            self._yml_path = project_root
            warn(f'.glotter.yml not found in directory "{project_root}"')

        if yml is None:
            yml = {}

        if not isinstance(yml, dict):
            error_and_exit(".glotter.yml does not contain a dict")

        config = SettingsConfig(**yml, yml_path=self._yml_path)
        self._acronym_scheme = config.settings.acronym_scheme
        self._source_root = config.settings.source_root
        self._projects = config.projects

    @property
    def project_root(self):
        return self._project_root

    @property
    def yml_path(self):
        return self._yml_path

    @property
    def source_root(self):
        return self._source_root

    @property
    def acronym_scheme(self):
        return self._acronym_scheme

    @property
    def projects(self):
        return self._projects

    def _parse_yml(self):
        with open(self._yml_path, "r", encoding="utf-8") as f:
            contents = f.read()

        return yaml.safe_load(contents)

    def _locate_yml(self):
        for root, _, files in os.walk(self._project_root):
            if ".glotter.yml" in files:
                path = os.path.abspath(root)
                return os.path.join(path, ".glotter.yml")

        return None
