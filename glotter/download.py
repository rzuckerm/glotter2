from glotter.source import get_sources, filter_sources
from glotter.settings import Settings
from glotter.containerfactory import ContainerFactory


def download(args):
    sources_by_type = filter_sources(args, get_sources(Settings().source_root))
    languages = set()
    for sources in sources_by_type.values():
        for source in sources:
            if source.language not in languages:
                _download_image_from_source(source)
                languages.add(source.language)


def _download_image_from_source(source):
    ContainerFactory().get_image(source.test_info.container_info)
