# Glotter2

[![Makefile CI](https://github.com/rzuckerm/glotter2/actions/workflows/makefile.yml/badge.svg)](https://github.com/rzuckerm/glotter2/actions/workflows/makefile.yml)
[![Coverage](https://rzuckerm.github.io/glotter2/badge.svg)](https://rzuckerm.github.io/glotter2/html_cov)
[![PyPI version](https://img.shields.io/pypi/v/glotter2)](https://pypi.org/project/glotter2)
[![Python versions](https://img.shields.io/pypi/pyversions/glotter2)](https://pypi.org/project/glotter2)
[![Python wheel](https://img.shields.io/pypi/wheel/glotter2)](https://pypi.org/project/glotter2)

[![Glotter2 logo](https://rzuckerm.github.io/glotter2/_static/glotter2_small.png)](https://rzuckerm.github.io/glotter2/)

*The programming language icons were downloaded from [pngegg.com](https://www.pngegg.com/)*

This is a fork of the original [Glotter](https://github.com/auroq/glotter) repository, which
appears to be unmaintained.

Glotter2 is an execution library for collections of single file scripts. It uses Docker to be able to build, run, and optionally test scripts in any language without having to install a local sdk or development environment.

For getting started with Glotter2, refer to our [documentation](https://rzuckerm.github.io/glotter2/).

## Contributing

If you'd like to contribute to Glotter2, read our [contributing guidelines](./CONTRIBUTING.md).

## Changelog

### Glotter2 releases

* 0.7.2:
  * Make sure temporary directory used for docker is world accessible
* 0.7.1:
  * Remove work-in-progress from changelog
* 0.7.0:
  * Add `try/finally` to auto-generated project fixture to make sure docker
    container is cleaned up
  * Add `try/finally` to `run` command to make sure docker container is
    cleaned up
  * Add `batch` command
* 0.6.1:
  * Update `docker` dependency to 6.1.0 to support `urllib3` 2.x
* 0.6.0:
  * Add test documentation generation
* 0.5.0:
  * Add test generation
  * Add `pydantic` dependency
* 0.4.5:
  * Add link to documentation
* 0.4.4:
  * Fix bug that would indicate "No tests were found" when filtering tests
* 0.4.2:
  * Remove call to `time.sleep` when pulling image
* 0.4.1:
  * Bump version since wrong version pushed to pypi
* 0.4.0:
  * Change test ID from `<filename>` to `<language>/<filename>`
  * Speed up test collection by about 1 min and total test time by about
    5 min in [sample-programs][sample-programs] by caching list of sources
  * Modify `download`, `run`, and `test` commands so that `-p`, `-l`, and
    `-s` are no longer mutually exclusive
  * Add `--parallel` to `download` command to parallelize image downloads
  * Add `--parallel` to `test` command to parallelize tests
* 0.3.0:
  * Fix crash when running tests for [sample-programs][sample-programs]
    with glotter 0.2.x
  * Upgrade dependencies to latest version:
    * `docker >=6.0.1, <7`
    * `Jinja >=3.1.2, <4`
    * `pytest >=7.2.1, <8`
    * `PyYAML >=6.0, <7`
  * Upgrade python to 3.8 or above

### Original Glotter releases

* 0.2.x: Add reporting verb to output discovered sources as a table in stdout or to a csv
* 0.1.x: Initial release of working code.

[sample-programs]: https://github.com/TheRenegadeCoder/sample-programs
