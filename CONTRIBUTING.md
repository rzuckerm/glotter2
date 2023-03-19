# Contributing

Thank you for your desire to contribute to Glotter2!

If you haven't already, please first take a look through our [README], [Code of Conduct],
and [docs]. Specifically, make sure you have a grasp on [general usage][docs-general-usage]
of glotter and [how glotter2 integrates with clients][docs-integrating].

Once you are familiar with the basics, see the sections below for how to contribute.

## Creating Issues

Before creating an issue, please use the search function to see if a related Bug or Feature
Request exists.

If you are unable to find a relevant issue, please create a new one using either the Bug Request
template or the Feature Request template as applicable.

## Glotter2 Development Environment

### Dependencies

Before you can build Glotter2, there a few things you will need.

- [docker]: Glotter2 makes extensive use of docker. You will need to have docker installed on your
  machine.
- [python], [pip], and [virtualenv]: Glotter2 is written in python and uses `pip` to install
  dependencies in a virtual environment that isolates the dependencies for this project
  from the dependencies on your host system.
- [make]: Everything in Glotter2 is built and run using `make`. See the following installation
  guides:
  - [Installing make on Linux]
  - [Installing make on MacOS]
  - [Installing make on Windows]

### Structure

The file structure of Glotter2 looks like the following (with omissions):

- `glotter`
- `doc`
- `test`
  - `integration`
  - `unit`
- `Makefile`
- `pyproject.toml`
- `poetry.lock`

The `glotter` directory contains all source code for the project.

The `doc` directory contains all the documentation for the project.
[Sphinx] is used to convert the
[reStructuredText](https://www.sphinx-doc.org/en/master/usage/restructuredtext/basics.html)
to HTML.

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

The project used [black] to do code formatting and format linting and [pylint] for linting.

This project uses [pytest] as its testing library, but it is also a wrapper around [pytest].

### Local Development

Everything associated with this project is done through `make` targets:

* `clean` - Delete output file
* `doc` - Make documentation
* `format` - Format the code using `black`
* `lint` - Lint the code using `black` and `pylint`

## Running Tests

Test can be run with `make test`. If you want to pass arguments to [pytest], use the
`PYTEST_ARGS`. Here are some common arguments:

* `-v` - Verbose output
* `-vv` - Very verbose output
* `-vvl` - Very verbose, long output
* `-k "<pattern>"` - Only run tests that match a specific pattern. The match can be
  done on test filename or test function name
* `-x` - Stop on the first failure
* `-s` - Show test output
* `--pdb` - Open python debugger when a failure occurs

For example, this will run tests that match `test_generator`, stop on the first
failure, and open the python debugger on that failure:

`make test PYTEST_ARGS="-vvl -x --pdb -k test_generator"`

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
- After creating the pull request, ensure that all the test passed on [GitHub Actions]. No pull
  requests will be merged without failing tests.
- If your changes are related to an existing issue, please reference that issue in your pull
  request.
- If your changes are not related to an existing issue, please either create a new issue and
  link to it.

[README]: https://github.com/rzuckerm/glotter2#glotter2
[Code of Conduct]: https://github.com/rzuckerm/glotter2/blob/main/CODE_OF_CONDUCT.md
[GitHub Actions]: https://github.com/rzuckerm/glotter2/actions/workflows/makefile.yml

[docs]: https://rzuckerm.github.io/glotter2/
[docs-general-usage]: https://rzuckerm.github.io/glotter2/general-usage.html
[docs-integrating]: https://rzuckerm.github.io/glotter2/index.html#integrating-with-glotter2

[Sphinx]: https://pypi.org/project/sphinx
[black]: https://pypi.org/project/black
[pylint]: https://pypi.org/project/pylint
[python-poetry]: https://pypi.org/project/poetry
[pytest]: https://pypi.org/project/pytest

[reStructuredText]: https://www.sphinx-doc.org/en/master/usage/restructuredtext/

[docker]: https://docs.docker.com/get-docker/
[python]: https://www.python.org/downloads/
[pip]: https://pip.pypa.io/en/stable/installation/
[virtualenv]: https://virtualenv.pypa.io/en/latest/installation.html
[make]: https://www.gnu.org/software/make/
[Installing make on Linux]: https://www.incredibuild.com/integrations/gnu-make#:~:text=If%20you're%20on%20Linux,Fedora%2FRHEL%20%E2%80%93%20yum%20install%20make
[Installing make on MacOS]: https://formulae.brew.sh/formula/make
[Installing make on Windows]: https://gnuwin32.sourceforge.net/packages/make.htm
