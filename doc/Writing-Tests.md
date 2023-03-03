# Writing Tests

<< [Directory Level Configuration](Directory-Level-Configuration.md) |

Glotter2 uses [pytest] behind the scenes for running tests.
If you are not familiar with [pytest], it may be helpful to learn the basics from their [documentation][pytest].

## Creating a Project Fixture.<a name="project-fixture">

A project fixture follows the same basic idea as a [fixture in pytest][pytest-fixture].
It is used to "provide a fixed baseline upon which tests can... execute." (from [pytest fixture documentation][pytest-fixture])
Fixtures in [pytest] can also be parametrized (see [Parametrizing fixtures](pytest-fixture-parametrize]).
In the case of a project fixture, the "fixed baseline" of the tests is a set of sources that implement a project specified by a ]project key][project-key].

All of this is handled automatically using the `project_fixture` decorator provided by Glotter2.

Start by importing the decorator: `from glotter import project_test`.
Then create a fixture function and decorate it with the decorator.
The decorator takes a [project key][project-key] as a parameter. See [Project Keys below][project-key] for more information.
The function can be named whatever you like, but I recommend naming it something related to the [project key][project-key].
The function must also take a parameter called `request`.
This is due to the way [pytest] works with parametrizing fixtures. (See [pytest documentation][pytest-fixture-parametrize] for more information.)

The body of the function should be three commands:
- `request.param.build()` - Build the source file. (See [Directory Level Configuration][directory-config-build])
- `yield request.param` - Provide the source to the test.
- `request.param.cleanup()` - Cleanup after all tests have run.

Altogether, this should look like the following:
```python
@project_fixture('my_project_key')
def my_project_key(request):
    request.param.build()
    yield request.param
    request.param.cleanup()
```

> Note, while you may have multiple tests for a given project key, only one fixture is required per project key.

## Writing a Project Test

As per [pytest] standards, any functions named starting with `test_` will considered tests.
Start by creating such a function.
The function must take a parameter with the same name as the `project_fixture` function you defined for the test (see [Creating a Project Fixture][project-fixture] above).

Next decorate the function with the `project_test` decorator provided by Glotter2.
Don't forget to import it from glotter. `from glotter import project_test`
This decorator also takes [project key][project-key] as a parameter.
This project key should must match the project key for the project fixture. See [Project Keys below][project-key] for more information.

Any other decorators—from pytest or otherwise—can be added as needed after the `project_test` decorator.

How to implement the body of the function is up to you.
The parameter of the test function named after the project fixture will be of type `source`.
It has the following methods available.
- `build(params='')` - build the source with optional parameters
- `run(params=None)` - run the source with optional parameters
- `exec(command)` - run a command inside of the container where the source exists
- `cleanup()` - cleanup the container where the source exists

In most cases only `run()` should be used in the test. `build` and `cleanup are called by the project fixture as described [above][project-fixture]. However, I can imagine a corner case where `exec` could be useful.

Both `run` and `exec` return the standard output response from the container.
In other words `exec` will return the response of the command as a string.
`run` will return as a string the output of the source when run with the provided parameters (if necessary).
This can be saved off and used for assertions. (See [pytest assertion documentation][pytest-assertions] for more information.)

Putting this all together a sample test might looks something like the following:
```python
@project_test('my_project_key')
def test_my_script(my_project_key):
    actual = my_project_key.run()
    assert actual.strip() == 'script was run'
```

## Project Keys<a name="project-key">

A project key is just a string that refers to a single project that can have multiple source files and/or tests.
Project keys are defined in the [global Glotter2 configuration][Glotter2-config-projects].
In order for tests to run properly the project key used here must refer to a project key specified in the [global Glotter2 configuration][Glotter2-config-projects].
It is case sensitive.

In order to make things easier and prevent confusing typos, I recommend saving these strings as constants somewhere in your project or using an enum with a "key" method as seen below:

```python
class ProjectKeys(Enum):
    Baklava = auto()
    BubbleSort = auto()
    EvenOdd = auto()
    FileIO = auto()
    Factorial = auto()

    @property
    def key(self):
        return self.name.lower()
```

> Note for this example to work, the project keys in your [global Glotter2 configuration][Glotter2-config-projects], must match the names of the enum values letter for letter.


## Example

If we bring this all together, here is an example of a set of tests for a factorial project:

```python
import pytest

from enum import Enum, auto
from glotter import project_test, project_fixture


class ProjectKeys(Enum):
    Factorial = auto()

    @property
    def key(self):
        return self.name.lower()


error_permutations = (
    'description, cli_args, expected', [
        (
            'no input',
            None,
            'Please enter an integer'
        ), (
            'invalid input: not a number',
            '"asdf"',
            'Please enter an integer'
        ), (
            'invalid input: negative',
            '"-1"',
            'Integer must be positive'
        )
    ]
)

working_permutations = (
    'description, cli_args, expected', [
        (
            'sample input: zero',
            '"0"',
            '1'
        ), (
            'sample input: one',
            '1',
            '1'
        ), (
            'sample input: ten',
            '10',
            '3628800'
        )
    ]
)


@project_fixture(ProjectKeys.Factorial.key)
def factorial(request):
    request.param.build()
    yield request.param
    request.param.cleanup()


@project_test(ProjectKeys.Factorial.key)
@pytest.mark.parametrize(working_permutations[0], working_permutations[1],
                         ids=[p[0] for p in working_permutations[1]])
def test_factorial(description, cli_args, expected, factorial):
    actual = factorial.run(params=cli_args)
    assert actual.strip() == expected



@project_test(ProjectType.Factorial.key)
@pytest.mark.parametrize(description, error_permutations[0], error_permutations[1],
                         ids=[p[0] for p in error_permutations[1]])
def test_factorial_errors(cli_args, expected, factorial):
    actual = factorial.run(params=cli_args)
    assert actual.strip() == expected
```

[pytest]:https://docs.pytest.org/en/latest/
[pytest-fixture]:https://docs.pytest.org/en/latest/fixture.html
[pytest-fixture-parametrize]:https://docs.pytest.org/en/latest/fixture.html#parametrizing-fixtures
[pytest-assertions]:http://doc.pytest.org/en/latest/assert.html

[project-key]:#project-key
[project-fixture]:#project-fixture

[directory-config-build]:Directory-Level-Configuration#build
[Glotter2-config-projects]:Global-Glotter2-Configuration#projects

[sample-programs]:https://github.com/TheRenegadeCoder/sample-programs

<< [Directory Level Configuration](Directory-Level-Configuration.md) |
