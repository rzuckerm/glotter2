# Contributing

Thank you for your desire to contribute to Glotter2!

If you haven't already, please first take a look through our [docs].
Specifically, make sure you have a grasp on [general usage][docs-general-usage] of glotter
and [how glotter2 integrates with clients][docs-integrating].

Once you are familiar with the basics, see the sections below for how to contribute.

## Creating Issues

Before creating an issue, please use the search function to see if a related Bug or Feature
Request exists.

If you are unable to find a relevant issue, please create a new one using either the Bug Request
template or the Feature Request template as applicable.

## Glotter2 Development Environment

### Dependencies

Before you can build Glotter2, there a few things you will need.

- `docker`: Glotter2 makes extensive use of docker. You will need to have docker installed on your
  machine
- `python`, `pip`, and `virtualenv`: Glotter2 is written in python and uses `pip` to install
  `virtualenv`, which is used to create a virtual environment where dependencies can be installed.
- `make`: Everything in Glotter2 is built and run using `make`

### Structure

The file structure of Glotter2 looks like the following (with omissions):

- `glotter`
- `test`
  - `integration`
  - `unit`
- `Makefile`
- `pyproject.toml`
- `poetry.lock`

The `glotter` directory contains all source code for the project.

The `test` directory contains all tests for the project. It is split into two types: `unit` and
`integration`. The difference for the sake of this project is that the unit tests are written in
such a way to abstract our all external dependencies (docker, the filesystem, etc...). The
integration tests test the integration between the code and external dependencies (docker,
the filesystem, etc...).

`Makefile` contains all the rules for building and running the projects.

The `pyproject.toml` contains all the dependenies of Glotter2 and all of the development
dependencies as well as configuration. The `poetry.lock` locks down the exact version
dependencies for build reproducibility. The project is based on
[python-poetry](https://python-poetry.org/docs/).

The project used `black` to do code formatting and format linting and `pylint` for linting.

This project uses `pytest` as its testing library, but it is also a wrapper around `pytest`.

### Local Development

Everything associated with this project is done through `make` targets:

* `clean` - Delete output file
* `format` - Format the code using `black`
* `lint` - Lint the code using `black` and `pylint`

## Running Tests

Test can be run with `make test`. If you want to pass arguments to `pytest`, use the
`PYTEST_ARGS`. Some common arguments:

* `-k "<pattern>"` - Only run tests that match a specific pattern. The match can be
  done on test filename or test function name
* `-x` - Stop on the first failure
* `-s` - Show test output
* `--pdb` - Open python debugger when a failure occurs

## Final Requirements for Contributing

- Run `make format` and `make lint` before committing your changes.
- Fix any linting errors, or add a "disable" rule to the `disable` item in the
  `tool.pylint.message` section of `pyproject.toml`. If you disable the linting, please
  be prepared to explain why this is being done. Alternatively, you can disable
  the linting error by adding something like this to the line in question:

  ```
  # pylint: disable=<error-code>
  ```

  For example:

  ```
  # pylint: disable=too-few-methods
  ```
- Please write tests for new functionality. No pull requests will be accepted without applicable
  new or existing unit or integration tests.
- After creating the pull request, ensure that all the test passed on GitHub Actions. No pull
  requests will be merged without failing tests.
- If your changes are related to an existing issue, please reference that issue in your pull
  request.
- If your changes are not related to an existing issue, please either create a new issue and
  link to it.

[docs]:https://github.com/rzuckerm/glotter2/README.md
[docs-general-usage]:https://github.com/rzuckerm/glotter2/General-Usage.md
[docs-integrating]:https://github.com/rzuckerm/glotter2/Integrating-With-Glotter.md
