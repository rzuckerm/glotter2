from concurrent.futures import ThreadPoolExecutor

from glotter.containerfactory import ContainerFactory
from glotter.settings import Settings
from glotter.source import filter_sources, get_sources


def download(args):
    sources_by_type = filter_sources(args, get_sources(Settings().source_root))
    containers = {
        f"{source.test_info.container_info.image}:{source.test_info.container_info.tag!s}": source.test_info.container_info
        for sources in sources_by_type.values()
        for source in sources
    }
    if args.parallel:
        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(
                lambda source: _download_image_from_source(source, True),
                containers.values(),
            )
    else:
        for container_info in containers:
            _download_image_from_source(container_info)

    return containers


def _download_image_from_source(container_info, parallel=False):
    ContainerFactory().get_image(container_info, parallel=parallel)


def remove_images(containers, parallel):
    if parallel:
        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(ContainerFactory().remove_image, containers.values())
    else:
        for container_info in containers:
            ContainerFactory().remove_image(container_info)
