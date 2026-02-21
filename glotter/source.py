from functools import lru_cache

from glotter_core.source import CoreSource, categorize_sources

from glotter.containerfactory import get_container_factory
from glotter.settings import get_settings
from glotter.utils import error_and_exit

BAD_SOURCES = "__bad_sources__"


class Source(CoreSource):
    """Metadata about a source file"""

    def __repr__(self):
        return f"Source(name: {self.name}, path: {self.path})"

    def build(self, params=""):
        if self.test_info.container_info.build is not None:
            command = f"{self.test_info.container_info.build} {params}"
            result = self._container_exec(command)
            if result[0] != 0:
                raise RuntimeError(
                    f'unable to build using cmd "{self.test_info.container_info.build} {params}":\n'
                    f"{result[1].decode('utf-8')}"
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
        container = get_container_factory().get_container(self)
        return container.exec_run(
            cmd=command,
            detach=False,
            workdir="/src",
        )

    def cleanup(self):
        get_container_factory().cleanup(self)


@lru_cache
def get_sources(path, check_bad_sources=False):
    """
    Walk through a directory and create Source objects

    :param path: path to the directory through which to walk
    :param check_bad_source: if True, check for bad source filenames. Default is False
    :return: a dict where the key is the ProjectType and the value is a list of all the
        Source objects of that project. If check_bad_source is True,
        the BAD_SOURCES key contains a list of invalid paths relative to the current
        working directory
    """

    categories = categorize_sources(path, get_settings().projects, Source)
    sources = categories.testable_by_project
    if check_bad_sources:
        sources[BAD_SOURCES] = categories.bad_sources

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
            error_and_exit(f'No valid sources found for project: "{args.project}"')

        sources = {args.project: sources[args.project]}

    filtered_sources_by_type = {}
    for project_type, sources_by_type in sources.items():
        filtered_sources = [source for source in sources_by_type if _matches_source(args, source)]
        if filtered_sources:
            filtered_sources_by_type[project_type] = filtered_sources

    if not filtered_sources_by_type:
        errors = []
        if args.project:
            errors.append(f'project "{args.project}"')

        if args.language:
            if isinstance(args.language, set):
                errors.append(
                    "languages " + ", ".join(f'"{language}"' for language in sorted(args.language))
                )
            else:
                errors.append(f'language "{args.language}"')

        if args.source:
            errors.append(f'source "{args.source}"')

        if errors:
            error_msg = ", ".join(errors)
            error_and_exit(f"No valid sources found for the following combination: {error_msg}")

    return filtered_sources_by_type


def _matches_source(args, source):
    if args.language:
        if isinstance(args.language, set):
            if source.language.lower() not in args.language:
                return False
        elif source.language.lower() != args.language.lower():
            return False

    return not args.source or f"{source.name}{source.extension}".lower() == args.source.lower()
