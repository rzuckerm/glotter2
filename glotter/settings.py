# pylint hates pydantic
# pylint: disable=E0213,E0611
from typing import Optional
import os
from warnings import warn

import yaml
from pydantic import BaseModel, validator

from glotter.project import Project, AcronymScheme
from glotter.containerfactory import Singleton


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
    acronym_scheme: AcronymScheme
    yml_path: str
    source_root: Optional[str] = None

    @validator("acronym_scheme", pre=True)
    def get_acronym_scheme(cls, value):
        if not isinstance(value, str):
            return value

        return value.lower()

    @validator("source_root")
    def get_source_root(cls, value, values):
        if os.path.isabs(value):
            return value

        yml_dir = os.path.dirname(values["yml_path"])
        return os.path.abspath(os.path.join(yml_dir, value))


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
            self.parse_settings_section()
            self.parse_projects_section()
        else:
            warn(f'.glotter.yml not found in directory "{project_root}"')

    def parse_settings_section(self):
        if self._yml is not None and "settings" in self._yml:
            settings_config = SettingsConfigSettings(
                **self._yml["settings"], yml_path=self._yml_path
            )
            self._acronym_scheme = settings_config.acronym_scheme
            self._source_root = settings_config.source_root

    def parse_projects_section(self):
        if self.yml is not None:
            self._projects = self._parse_projects()

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

    def _parse_projects(self):
        projects = {}
        if "projects" in self._yml:
            projects, use_tests_projects = self._parse_projects_without_use_tests()
            self._update_products_with_use_tests(projects, use_tests_projects)

        return projects

    def _parse_projects_without_use_tests(self):
        projects = {}
        use_tests_projects = {}
        for k, v in self._yml["projects"].items():
            project_name = k.lower()
            if "use_tests" in v:
                use_tests_projects[k] = v
                continue

            acronym_scheme = v.get("acronym_scheme") or self._acronym_scheme
            project = Project(**v, acronym_scheme=acronym_scheme)
            projects[project_name] = project

        return projects, use_tests_projects

    def _update_products_with_use_tests(self, projects, use_tests_projects):
        projects_yml = self._yml["projects"]
        for k, v in use_tests_projects.items():
            project_name = k.lower()
            use_tests = v["use_tests"]
            use_tests_name = use_tests.get("name")
            if not use_tests_name:
                warn(f'Project {project} has a "use_tests" item without a "name" item')
                continue

            if use_tests_name in use_tests_projects:
                warn(
                    f'Project {project_name} has a "use_tests" item that refers to '
                    f'another "use_test" item "{use_tests_name}"'
                )
                continue

            if use_tests_name not in projects:
                warn(
                    f'Project {project_name} has a "use_tests" item that refers to a '
                    f'non-existent project "{use_tests_name}"'
                )
                continue

            tests = projects_yml[use_tests_name].get("tests")
            if not tests:
                warn(
                    f'Project {project_name} has a "use_tests" item that refers to project '
                    f'{use_tests_name}, which has no "tests" item'
                )
                continue

            acronym_scheme = v.get("acronym_scheme") or self._acronym_scheme
            project = Project(
                **v,
                acronym_scheme=acronym_scheme,
                tests=tests,
            )
            projects[project_name] = project

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
