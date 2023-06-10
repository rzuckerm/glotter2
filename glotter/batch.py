import argparse
import sys

from glotter.source import get_sources
from glotter.settings import Settings
from glotter.utils import error_and_exit
from glotter.download import download, remove_images
from glotter.test import test


def batch(args):
    # Validate arguments
    if args.num_batches < 1:
        error_and_exit("Number of batches must be at least 1")

    if args.batch is not None and (args.batch < 1 or args.batch > args.num_batches):
        error_and_exit(f"Batch number must be from 1 to {args.num_batches}")

    # Get all of the languages
    all_sources = get_sources(Settings().source_root)
    languages = sorted(
        {
            source.language.lower()
            for sources in all_sources.values()
            for source in sources
        }
    )
    num_languages = len(languages)
    num_batches = min(num_languages, args.num_batches)

    # Determine starting and ending batch
    if args.batch is None:
        first_batch = 0
        last_batch = num_batches
    elif args.batch <= num_batches:
        first_batch = args.batch - 1
        last_batch = args.batch
    else:
        sys.exit(0)

    # For each batch
    exit_code = 0
    for n in range(first_batch, last_batch):
        # Get languages for this batch
        batch_args = argparse.Namespace(
            source=None,
            project=None,
            language=set(
                languages[
                    (n * num_languages // num_batches) : (
                        (n + 1) * num_languages // num_batches
                    )
                ]
            ),
            parallel=args.parallel,
        )

        # Download images for this batch
        _display_batch("Downloading images", n, num_batches)
        containers = download(batch_args)

        # Run tests for this batch
        try:
            _display_batch("Testing", n, num_batches)
            test(batch_args)
        except SystemExit as e:
            exit_code = exit_code or int(e.code)

        # If removing images, remove images for this batch
        if args.remove:
            _display_batch("Removing images", n, num_batches)
            remove_images(containers, args.parallel)

    sys.exit(exit_code)


def _display_batch(prefix, n, num_batches):
    print(f"\n*** {prefix} for batch {n + 1} of {num_batches} ***", flush=True)
