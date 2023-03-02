Glotter2 is an execution library for collections of single file scripts.
It uses Docker to be able to build and run scripts in any language without having to install a local sdk or development environment.

Before Glotter2 can be used, your project must be configured.
See [Integrating with Glotter2](Integrating-with-Glotter2.md) for more information

The Glotter2 CLI has four main commands:
- [download](#download)
- [run](#run)
- [test](#test)
- [report](#report)

All of these commands have this optional argument:

| Flag | Short Flag | Description |
| --- | --- | --- |
| `--help` | `-h` | Print help text and exit |

While the `download`, `run`, and `test` commands serve different functions
(described below), each has the following optional arguments:

| Flag | Short Flag | Description |
| --- | --- | --- |
| `--source` | `-s` | Perform action using a single source file |
| `--project` | `-p` | Perform action using all sources relevant to a certain project key |
| `--language` | `-l` | Perform action using all sources of a given language |

These optional arguments can be used together in the event that multiple languages
have the same filename and extension. For example, suppose that there are two programs
called `hello_world.e`, one in Eiffel and one in Euphoria. If you want to perforce the
action on the Eiffel one, you do one of the following:

- `-l eiffel -p helloworld`
- `-l eiffel -s hello_world.e`

## Download

The `download` command is used to download any required docker images.
It is invoked using `glotter download` with any of the flags described above.

It is not necessary to invoke download manually before run or test.
It will be invoked automatically.
This command is exposed for convenience in cases where you want to have everything you will need downloaded ahead of time.

The `download` command also has the following optional argument:

| Flag | Short Flag | Description |
| --- | --- | --- |
| `--parallel` | | Download images in parallel |

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
|  `--parallel` | | Run tests in parallel |

# Report

The `report` command is used to output a report of discovered sources for configured
projects and languages.

The `report` command has the following optional argument:

| Flag | Short Flag | Description |
| --- | --- | --- |
| `-o` | `--output` | Output the report as a [CSV](https://en.wikipedia.org/wiki/Comma-separated_values) at the specified report path instead of to stdout |

If `-o` is not specified, the report is output as [Markdown](https://www.markdownguide.org/basic-syntax/) to stdout.
