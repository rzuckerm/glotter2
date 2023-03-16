# pylint hates pydantic
# pylint: disable=E0213,E0611
from typing import Optional, Dict
import os
from warnings import warn

import yaml
from pydantic import BaseModel, validator, root_validator

from glotter.project import Project, AcronymScheme
from glotter.singleton import Singleton


class Settings(metaclass=Singleton):
    def __init__(self):
        self._project_root = os.getcwd()
        self._parser = SettingsParser(self._project_root)
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


class SettingsConfigSettings(BaseModel):
    acronym_scheme: AcronymScheme = AcronymScheme.two_letter_limit
    yml_path: str
    source_root: Optional[str] = None

    @validator("acronym_scheme", pre=True)
    def get_acronym_scheme(cls, value):
        if isinstance(value, str):
            return value.lower()

        return value

    @validator("source_root")
    def get_source_root(cls, value, values):
        if os.path.isabs(value):
            return value

        yml_dir = os.path.dirname(values["yml_path"])
        return os.path.abspath(os.path.join(yml_dir, value))


class SettingsConfig(BaseModel):
    yml_path: str
    settings: Optional[SettingsConfigSettings] = None
    projects: Dict[str, Project] = {}

    @validator("settings", pre=True, always=True)
    def get_settings(cls, value, values):
        if value is None:
            return {"yml_path": values["yml_path"]}

        if isinstance(value, dict):
            return {**value, "yml_path": values["yml_path"]}

        return value

    @validator("projects", pre=True)
    def get_projects(cls, value, values):
        if not isinstance(value, dict) or not all(
            isinstance(item, dict) for item in value.values()
        ):
            return value

        return {
            project_name: {**item, "acronym_scheme": values.get("acronym_scheme")}
            for project_name, item in value.items()
        }

    @root_validator()
    def validate_projects(cls, values):
        projects = values["projects"]
        projects_with_use_tests = {
            project_name: project
            for project_name, project in projects.items()
            if project.use_tests
        }

        errors = []
        for project_name, project in projects_with_use_tests.items():
            use_tests_name = project.use_tests.name

            # Make sure one "use_tests" item does not refer to another "use_tests" item
            if use_tests_name in projects_with_use_tests:
                errors.append(
                    f'Project {project_name} has a "use_tests" item that refers to '
                    f'another "use_tests" item "{use_tests_name}"'
                )
            # Make sure "use_tests" item refers to an actual project
            elif use_tests_name not in projects:
                errors.append(
                    f'Project {project_name} has a "use_tests" item that refers to a '
                    f"non-existent project {project.use_tests.name}"
                )
            # Make sure "use_tests" item refers to a project with tests
            elif not projects[use_tests_name].tests:
                errors.append(
                    f'Project {project_name} has a "use_tests" item that refers to project '
                    f'{use_tests_name}, which has no "tests" item'
                )
            # Otherwise, set the tests that the "use_tests" item refers to with the tests renamed
            else:
                project.set_tests(projects[use_tests_name].tests)

        if errors:
            raise ValueError("\n".join(errors))

        return values


class SettingsParser:
    def __init__(self, project_root):
        self._project_root = project_root
        self._yml_path = None
        self._yml = None
        self._acronym_scheme = None
        self._projects = None
        self._source_root = None
        self._yml_path = self._locate_yml()
        if self._yml_path is not None:
            self._yml = self._parse_yml()
            if self._yml is None:
                self._yml = {}
        else:
            self._yml_path = project_root
            self._yml = {}
            warn(f'.glotter.yml not found in directory "{project_root}"')

        config = SettingsConfig(**self._yml, yml_path=self._yml_path)
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
    def yml(self):
        return self._yml

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
