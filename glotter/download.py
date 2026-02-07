from concurrent.futures import ThreadPoolExecutor

from glotter.containerfactory import get_container_factory
from glotter.settings import get_settings
from glotter.source import filter_sources, get_sources


def download(args):
    def get_key(source):
        return f"{source.test_info.container_info.image}:{source.test_info.container_info.tag}"

    sources_by_type = filter_sources(args, get_sources(get_settings().source_root))
    containers = {
        get_key(source): source.test_info.container_info
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
        for container_info in containers.values():
            _download_image_from_source(container_info)

    return containers


def _download_image_from_source(container_info, parallel=False):
    get_container_factory().get_image(container_info, parallel=parallel)


def remove_images(containers, parallel):
    if parallel:
        with ThreadPoolExecutor(max_workers=4) as executor:
            executor.map(get_container_factory().remove_image, containers.values())
    else:
        for container_info in containers.values():
            get_container_factory().remove_image(container_info)
