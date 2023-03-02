Glotter2 is an execution library for collections of single file scripts.
It uses Docker to be able to build and run scripts in any language without having to install a local sdk or development environment.

Before Glotter2 can be used, your project must be configured.
See [Integrating with Glotter2](Integrating-with-Glotter2.md) for more information

The Glotter2 CLI has four main commands:
- [download](#download)
- [run](#run)
- [test](#test)
- [report](#report)

All of these has a commands optional argument:

| Flag | Short Flag | Description |
| --- | --- | --- |
| --help | -h | print help text and exit |

While these each perform a different function (described below), the `download`, `run`,
and `test` has the following optional arguments:

| Flag | Short Flag | Description |
| --- | --- | --- |
| --source | -s | perform action using a single source file |
| --project | -p | perform action using all sources relevant to a certain project key |
| --language | -l | perform action using all sources of a given language |

The Glotter2 CLI has this part:

- Report

## Download

The `download` command is used to download any required docker images.
It is invoked using `glotter download` with any of the flags described above.

It is not necessary to invoke download manually before run or test.
It will be invoked automatically.
This command is exposed for convenience in cases where you want to have everything you will need downloaded ahead of time.

The `download` command also has the following optional argument:

| Flag | Short Flag | Description |
| --- | --- | --- |
| --parallel | | Download images in parallel |

## Run

The `run` command is used to execute scripts.
It is invoked using `glotter run` with any of the flags described above.
If a script requires input, it will prompt for that information.

## Test

The `test` command is used to execute tests for scripts.
It is invoked using `glotter test` with any of the flags described above.

The `test` command also has the following optional argument:

| Flag | Short Flag | Description |
| --- | --- | --- |
| --parallel | | Run tests in parallel |

# Report

The `report` command is used to output a report of discovered sources for configured
projects and languages.

The `report` command has the following optional argument:

| Flag | Short Flag | Description |
| --- | --- | --- |
| -o <REPORT_PATH> | | Output the report as a [CSV](https://en.wikipedia.org/wiki/Comma-separated_values) at <REPORT_PATH> instead of to stdout |

If `-o` is not specified, the report is output as [Markdown](https://www.markdownguide.org/basic-syntax/) to stdout.
