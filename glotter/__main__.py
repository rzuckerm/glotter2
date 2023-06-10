import sys
import argparse

from glotter.run import run
from glotter.test import test
from glotter.download import download
from glotter.report import report
from glotter.batch import batch


def main():
    parser = argparse.ArgumentParser(
        prog="glotter",
        usage="""usage: glotter [-h] COMMAND

Commands:
  run         Run sources or group of sources. Use `glotter run --help` for more information.
  test        Run tests for sources or a group of sources. Use `glotter test --help` for more information.
  download    Download all the docker images required to run the tests
  report      Output a report of discovered sources for configured projects and languages
  batch       Download docker images, run tests, and optionally remove images for each batch
""",
    )
    parser.add_argument(
        "command",
        type=str,
        help="Subcommand to run",
        choices=["run", "test", "download", "report", "batch"],
    )
    args = parser.parse_args(sys.argv[1:2])
    commands = {
        "download": parse_download,
        "run": parse_run,
        "test": parse_test,
        "report": parse_report,
        "batch": parse_batch,
    }
    commands[args.command]()


def parse_download():
    parser = argparse.ArgumentParser(
        prog="glotter",
        description="Download images for a source or a group of sources. This command can be filtered by language, "
        "project, or a single source. Only one option may be specified.",
    )
    _add_parallel_arg(parser, "Download images in parallel")
    args = _parse_args_for_verb(parser)
    download(args)


def parse_run():
    parser = argparse.ArgumentParser(
        prog="glotter",
        description="Run a source or a group of sources. This command can be filtered by language, project"
        "or a single source. Only one option may be specified.",
    )
    args = _parse_args_for_verb(parser)
    run(args)


def parse_test():
    parser = argparse.ArgumentParser(
        prog="glotter",
        description="Test a source or a group of sources. This command can be filtered by language, project"
        "or a single source. Only one option may be specified.",
    )
    _add_parallel_arg(parser, "Run tests in parallel")
    args = _parse_args_for_verb(parser)
    test(args)


def _add_parallel_arg(parser, help_msg):
    parser.add_argument("--parallel", action="store_true", help=help_msg)


def _parse_args_for_verb(parser):
    parser.add_argument(
        "-s",
        "--source",
        metavar="SOURCE.EXT",
        type=str,
        help="source filename (not path) to run",
    )
    parser.add_argument(
        "-p",
        "--project",
        metavar="PROJECT",
        type=str,
        help="project to run",
    )
    parser.add_argument(
        "-l",
        "--language",
        metavar="LANGUAGE",
        type=str,
        help="language to run",
    )
    args = parser.parse_args(sys.argv[2:])
    return args


def parse_report():
    parser = argparse.ArgumentParser(
        prog="glotter",
        description="Output a report of discovered sources for configured projects and languages",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="REPORT_PATH",
        type=str,
        help="output the report as a csv at REPORT_PATH instead of to stdout",
    )
    args = parser.parse_args(sys.argv[2:])
    report(args)


def parse_batch():
    parser = argparse.ArgumentParser(
        prog="glotter",
        description="Download images, run tests, and optionally remove image in batches"
        "project, or a single source. Only one option may be specified.",
    )
    parser.add_argument(
        "num_batches", metavar="NUM_BATCHES", type=int, help="number of batches"
    )
    _add_parallel_arg(
        parser,
        "Download images, run tests, and optionally remove images in parallel for each batch",
    )
    parser.add_argument(
        "--batch", type=int, metavar="BATCH", help="batch number (1 to NUM_BATCHES)"
    )
    parser.add_argument(
        "--remove",
        action="store_true",
        help="remove docker images are each batch is finished",
    )
    args = parser.parse_args(sys.argv[2:])
    batch(args)


if __name__ == "__main__":
    main()
