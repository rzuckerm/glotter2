import sys

from glotter.settings import Settings
from glotter.source import BAD_SOURCES, get_sources


def check(_args):
    # Get all sources
    all_sources = get_sources(Settings().source_root, check_bad_sources=True)

    # If no bad sources, exit with zero status
    bad_sources = all_sources[BAD_SOURCES]
    if not bad_sources:
        print("All filenames correspond to valid projects")
        sys.exit(0)

    # Show bad sources and exit with non-zero status
    print("The following filenames do not correspond to a valid project:")
    for source in sorted(bad_sources):
        print(f"- {source}")

    sys.exit(1)
