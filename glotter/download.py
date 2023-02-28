import os

from glotter.source import get_sources
from glotter.settings import Settings
from glotter.containerfactory import ContainerFactory
from glotter.utils import error_and_exit


def download(args):
    if args.language:
        _download_language(args.language)
    elif args.project:
        _download_project(args.project)
    elif args.source:
        _download_source(args.source)
    else:
        _download_all()


def _download_image_from_source(source):
    ContainerFactory().get_image(source.test_info.container_info)


def _download_all():
    sources_by_type = get_sources(Settings().source_root)
    for sources in sources_by_type.values():
        for source in sources:
            _download_image_from_source(source)


def _download_language(language):
    sources_by_type = get_sources(
        path=os.path.join(Settings().source_root, language[0], language)
    )
    if not any(sources_by_type.values()):
        error_and_exit(f'No valid sources found for language: "{language}"')
    for sources in sources_by_type.values():
        for source in sources:
            _download_image_from_source(source)


def _download_project(project):
    sources_by_type = get_sources(Settings().source_root)
    try:
        Settings().verify_project_type(project)
        sources = sources_by_type[project]
        for source in sources:
            _download_image_from_source(source)
    except KeyError:
        error_and_exit(f'No valid sources found for project: "{project}"')


def _download_source(source):
    sources_by_type = get_sources(Settings.source_root)
    for sources in sources_by_type.values():
        for src in sources:
            if f"{src.name}{src.extension}".lower() == source.lower():
                _download_image_from_source(src)
                return

    error_and_exit(f'Source "{source}" could not be found')
