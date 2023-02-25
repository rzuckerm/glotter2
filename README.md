# Glotter2

This is a fork of the original [Glotter](https://github.com/auroq/glotter) repository, which
appears to be unmaintained.

Glotter is an execution library for collections of single file scripts. It uses Docker to be able to build, run, and optionally test scripts in any language without having to install a local sdk or development environment.

## Contributing

If you'd like to contribute to Glotter, read our [contributing guidelines](./CONTRIBUTING.md).

## Changelog

### Glotter2 releases

* 0.3.0 Original release:
  * Fix crash when running tests for [sample-programs](https://github.com/TheRenegadeCoder/sample-programs)
    with glotter 0.2.x
  * Upgrade dependencies to latest version:
    * `docker >=6.0.1, <7`
    * `Jinja >=3.1.2, <4`
    * `pytest >=7.2.1, <8`
    * `PyYAML >=6.0, <7`
  * Upgrade python to 3.8 or above

### Original Glotter releases

* 0.2.x Add reporting verb to output discovered sources as a table in stdout or to a csv
* 0.1.x Initial release of working code.
