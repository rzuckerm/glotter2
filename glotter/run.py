from glotter.source import get_sources, filter_sources
from glotter.settings import Settings


def run(args):
    sources_by_type = filter_sources(args, get_sources(Settings().source_root))
    for project_type, sources in sources_by_type.items():
        params = _prompt_params(project_type)
        for source in sources:
            _build_and_run(source, params)


def _prompt_params(project_type):
    if not Settings().projects[project_type].requires_parameters:
        return ""
    return input(f'input parameters for "{project_type}": ')


def _build_and_run(source, params):
    print()
    print(f'Running "{source.name}{source.extension}"...')
    source.build()
    print(source.run(params))
    source.cleanup()
