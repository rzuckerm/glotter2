import os
import sys
from functools import lru_cache

import yaml

from glotter import testinfo
from glotter.settings import Settings
from glotter.containerfactory import ContainerFactory


class Source:
    """Metadata about a source file"""

    def __init__(self, name, language, path, test_info_string):
        """Initialize source

        :param name: filename including extension
        :param path: path to the file excluding name
        :param language: the language of the source
        :param test_info_string: a string in yaml format containing testinfo for a directory
        """
        self._name = name
        self._language = language
        self._path = path

        self._test_info = testinfo.TestInfo.from_string(test_info_string, self)

    @property
    def full_path(self):
        """Returns the full path to the source including filename and extension"""
        return os.path.join(self._path, self._name)

    @property
    def path(self):
        """Returns the path to the source excluding name"""
        return self._path

    @property
    def name(self):
        """Returns the name of the source excluding the extension"""
        return os.path.splitext(self._name)[0]

    @property
    def language(self):
        """Returns the language of the source"""
        return self._language

    @property
    def extension(self):
        """Returns the extension of the source"""
        return os.path.splitext(self._name)[1]

    @property
    def test_info(self):
        """Returns parsed TestInfo object"""
        return self._test_info

    def __repr__(self):
        return f"Source(name: {self.name}, path: {self.path})"

    def build(self, params=""):
        if self.test_info.container_info.build is not None:
            command = f"{self.test_info.container_info.build} {params}"
            result = self._container_exec(command)
            if result[0] != 0:
                raise RuntimeError(
                    f'unable to build using cmd "{self.test_info.container_info.build} {params}":\n'
                    f'{result[1].decode("utf-8")}'
                )

    def run(self, params=None):
        """
        Run the source and return the output

        :param params: input passed to the source as it's run
        :return: the output of running the source
        """
        params = params or ""
        command = f"{self.test_info.container_info.cmd} {params}"
        result = self._container_exec(command)
        return result[1].decode("utf-8")

    def exec(self, command):
        """
        Run a command inside the container for a source

        :param command: command to run
        :return:  the output of the command as a string
        """
        result = self._container_exec(command)
        return result[1].decode("utf-8")

    def _container_exec(self, command):
        """
        Run a command inside the container for a source

        :param command: command to run
        :return:  the exit code and output of the command
        """
        container = ContainerFactory().get_container(self)
        return container.exec_run(
            cmd=command,
            detach=False,
            workdir="/src",
        )

    def cleanup(self):
        ContainerFactory().cleanup(self)


@lru_cache
def get_sources(path):
    """
    Walk through a directory and create Source objects

    :param path: path to the directory through which to walk
    :return: a dict where the key is the ProjectType and the value is a list of all the Source objects of that project
    """
    sources = {k: [] for k in Settings().projects}
    for root, _, files in os.walk(path):
        path = os.path.abspath(root)
        if "testinfo.yml" in files:
            with open(
                os.path.join(path, "testinfo.yml"), "r", encoding="utf-8"
            ) as file:
                test_info_string = file.read()
            folder_info = testinfo.FolderInfo.from_dict(
                yaml.safe_load(test_info_string)["folder"]
            )
            folder_project_names = folder_info.get_project_mappings(
                include_extension=True
            )
            for project_type, project_name in folder_project_names.items():
                if project_name in files:
                    source = Source(
                        project_name, os.path.basename(path), path, test_info_string
                    )
                    sources[project_type].append(source)
    return sources


def filter_sources(args, sources):
    """
    Filter sources based language, project, and/or source

    :param args: Arguments indicating what to filter on
    :param sources: a dict where the key is the ProjectType and the value is a list of all the Source objects of that project
    :return: a dict where the key is the ProjectType and the value is a list of all the Source objects of that project
        that match the filter
    """

    if args.project:
        if args.project not in sources:
            _error_and_exit(f'No valid sources found for project: "{args.project}"')

        sources = {args.project: sources[args.project]}

    filtered_sources_by_type = {}
    for project_type, sources_by_type in sources.items():
        filtered_sources = [
            source for source in sources_by_type if _matches_source(args, source)
        ]
        if filtered_sources:
            filtered_sources_by_type[project_type] = filtered_sources

    if not filtered_sources_by_type:
        errors = []
        if args.project:
            errors.append(f'project "{args.project}"')

        if args.language:
            errors.append(f'language "{args.language}"')

        if args.source:
            errors.append(f'source "{args.source}"')

        if errors:
            error_msg = ", ".join(errors)
            _error_and_exit(
                f"No valid sources found for the following combination: {error_msg}"
            )

    return filtered_sources_by_type


def _matches_source(args, source):
    if args.language and source.language.lower() != args.language.lower():
        return False

    return (
        not args.source
        or f"{source.name}{source.extension}".lower() == args.source.lower()
    )


def _error_and_exit(msg):
    print(msg)
    sys.exit(1)
