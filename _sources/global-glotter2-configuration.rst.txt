=============================
Global Glotter2 Configuration
=============================

All of Glotter2's global settings are set in a file called ``.glotter.yml`` using `YAML syntax <https://yaml.org/>`_
This file can be placed anywhere in the filesystem of your project, but it is recommended to place it at the root.

There are two root level sections.

Settings
========

Settings are generic global settings. The following shows what settings are available and their purpose.
These settings are all optional. If this section is omitted, all of its values are default.

Acronym Scheme
--------------

- **Optional**
- **Format**: ``acronym_scheme: "value"``
- **Default**: ``two_letter_limit``

Description
^^^^^^^^^^^

``acronym_scheme`` determines how the Glotter2 should handle file names that contain acronyms.

Values
^^^^^^

- ``upper`` - All acronyms are expected to be uppercase
- ``lower`` - All acronyms are expected to be lowercase
- ``two_letter_limit`` - If an acronym is two letters or less and the project naming scheme is
  ``pascal`` or ``camel``, the the acronym is expected to be upper case. Otherwise, it is expected
  to be lowercase

Source Root
-----------

- **Optional**
- **Format**: ``source_root: "path/to/root"``
- **Default**: the current directory

Description
^^^^^^^^^^^

Source root is the path to the directory containing all of the scripts to run execute with Glotter2.
It can be absolute or relative from the current directory.

.. _projects:

Projects
========

The projects section contains all of the information about each "project" that is implemented in your project.
Each project has a project key and a set of value.


Words
-----

- **Required**
- **Format**:

  .. code-block:: yaml

    words:
      - "word1"
      - "word2"
      - ...

Description
^^^^^^^^^^^

``words`` is a list of words that make up the name of the project depending on naming scheme.

Acronyms
--------

- **Optional**
- **Format**:

  .. code-block:: yaml

    acronyms:
      - "acronym1"
      - "acronym2"
      - ...

Description
^^^^^^^^^^^

``acronyms`` is a list of the words in the word list that are acronyms.

Requires Parameters
-------------------

- **Optional**
- **Format**: ``requires_parameters: boolean``
- **Default**: ``false``

Description
^^^^^^^^^^^

``requires_parameters`` is a flag of whether the project will require command line arguments.

Values
^^^^^^

- ``true`` - A project requires command line arguments
- ``false`` - A project does not require command line arguments

.. _tests:

Tests
-----

- **Optional**
- **Format**

  .. code-block:: yaml

    tests:
      test_name1:
        inputs:
          - "Input 1"
          ...
        params:
          - name: param_name1
            input: input_value1
            expected: expected_value1
        ...
        transformations:
          - transformation1
          ...
      ...

Description
^^^^^^^^^^^

``tests`` is a dictionary that describes auto-generated tests. Each
auto-generated test has a name that is a key.

Each of these tests may have a list of input names, ``inputs``. This is optional,
and it is ignored if ``requires_parameters`` is ``false``. Each item gives a
name to each value in the ``input`` field. This field is used for
auto-generated test documentation. If not specified, a single input called
``"Input"`` is assumed. When ``requires_parameters`` is ``false``, the
test documentation just refers to the requirements section.

Each of these tests have is a list of parameter dictionaries, ``params``. This
is required. Each list has the following item:

- ``name`` is a name of the parameter.
- ``input`` is an input value to the test for this parameter.
- ``expected`` is a expected value or values for this parameter.

Each of these tests can have a list of ``transformations`` that can be applied to the
actual value and/or the expected value before comparing the actual and expected values.

Values
^^^^^^

- The test key must be at least one character that starts with an alphabetic character
  or an underscore. All subsequent characters must be alphanumeric or an underscore.

Params
~~~~~~

- **Required**

- ``name`` is a string. It is required if ``requires_parameters`` is ``true``.
- ``input`` is required if ``requires_parameters`` is ``true``. It is either ``null``
  or a string:

  .. code-block:: yaml

    input: null

  .. code-block:: yaml

    input: "string_value"

- ``expected`` is required. It is either a string, a list of strings, or a dictionary
  contain a key and a string value:

  .. code-block:: yaml

      expected: "string_value"

  .. code-block:: yaml

      expected:
        - "list_value1"
        - "list_value2"
        - ...

  .. code-block:: yaml

      expected:
        key: "string"

  As a dictionary may be one of the following:

  - ``exec: "command"`` - Execute a command in the language-specific docker container.
  - ``self: ""`` - The expect value is the project code (i.e., a 
    `quine <https://en.wikipedia.org/wiki/Quine_(computing)>`_)

Transformations
~~~~~~~~~~~~~~~

- **Optional**

The following transformations are string values:

- ``"strip"``: Remove leading and trailing whitespace from the actual value.
- ``"splitlines"``: Split actual value at line boundaries -- e.g., ``"1\n2\n3"`` is
  converted to the list ``["1", "2", "3"]``.
- ``"lower"``: Convert the actual value to lowercase.
- ``"any_order"``: Convert the actual and expected value into a sorted list of unique
  values -- e.g., a list of ``["7", "3", "1", "7"]`` is converted to ``["1", "3", "7"]``.
- ``"strip_expected"``: Remove leading a trailing whitespace from the expected value.
- ``"splitlines_expected"``: Split expected value at line boundaries -- e.g.,
  ``"1\r2\r\3"`` is converted to a list ``["1", "2", "3"]``.

The following transformations are dictionaries:

- ``"remove"``: Remove all listed characters from the actual value:

  .. code-block:: yaml

    - "remove":
      - "char1"
      - "char2"
      - ...

- ``"strip"``: Remove leading and trailing characters from the actual value.

  .. code-block:: yaml

    - "strip":
      - "char1"
      - "char2"
      - ...

.. _use_tests:

Use Tests
---------

- **Optional**
- **Format**:

  .. code-block:: yaml

    use_tests:
    - name: "project_name"
      search: "search_string"
      replace: "replace_string"

Description
^^^^^^^^^^^

``use_tests`` allows tests to be reused from another project. It is mutually exclusive with
``tests``.

Values
^^^^^^

- ``name`` is a string that indicates the project for which to reuse tests. It is required.
- ``search`` is a string to use a string to search for in the test name.
- ``replace`` is a string to use a string to replace in the tests.

Both ``search`` and ``replace`` is optional, but it one is specified, then other must also
be specified.

Format
------

The format for a project is as follows:

.. code-block:: yaml

    projectkey1:
      words:
        - "words"
        - "in"
        - "project"
      acronyms:
        - "acronyms"
        - "in"
        - "project"
      requires_parameters: true
      tests:
        testkey1:
          params:
            - name: "param name1"
              input: "input value1"
              expected: expected value or values 1
            - name: "param name2"
              input: "input value2"
              expected: expected value or values 2
            - ...
        testkey2:
          params:
            - name: "param name1"
              input: "input value1"
              expected: expected value or values 1
            - name: "param name2"
              input: "input value2"
              expected: expected value or values 2
            - ...
    projectkey2:
      words:
        - "words"
        - "in"
        - "project"
      acronyms:
        - "acronyms"
        - "in"
        - "project"
      use_tests:
        - name: "projectkey"
          search: "search_value"
          replace: "replace_value"

So for example. Let's say I have three projects named FileIO, Factorial, HelloWorld,
Quine, BubbleSort, and MergeSort.

FileIO contains an acronym. Both Factorial and BubbleSort requires parameters.
MergeSort uses tests from BubbleSort.

The ``projects`` section would look like this:

.. code-block:: yaml

    projects:
      fileio:
        words:
          - "file"
          - "io"
        acronyms:
          - "io"
        tests:
          fileio:
            - expected:
              exec: "cat output.txt"
      factorial:
        words:
          - "factorial"
        requires_parameters: true
        tests:
          factorial_valid:
            params:
              - name: "value 1"
                input: "1"
                expected: "1"
              - name: "value 5"
                input: "5"
                expected: "120"
            transformations:
              - "strip"
          factorial_invalid:
            params:
              - name: "no input"
                input: null
                expected: "Some error message"
              - name: "empty input"
                input: '""'
                expected: "Some error message"
            transformations:
              - "strip"
      helloworld:
        words:
          - "hello"
          - "world"
        tests:
            hello_world:
                params:
                  - expected: "Hello, world!"
                transformations:
                  - "strip"
      quine:
        words:
          - "quine"
        tests:
            quine:
                params:
                  - expected:
                    - self: ""
                transformations:
                  - "strip"
                  - "strip_expected"
      bubblesort:
        words:
          - "bubble"
          - "sort"
        requires_parameters: true
        bubble_sort_valid:
          params:
            - name: "not sorted"
              input: '"4, 5, 1, 3, 2"'
              expected: "1, 2, 3, 4, 5"
            - name: "already sorted"
              input: '"1, 2, 3, 4"'
              expected: "1, 2, 3, 4"
          transformations:
            -   remove:
                - "["
                - "]"
            -   "strip"
        bubble_sort_invalid:
          params:
            - name: "no input"
              input: null
              expected: "Some error"
            - name: "empty input"
              input: '""'
              expected: "Some error"
          transformations:
            - "strip"
      mergesort:
        words:
          - "merge"
          - "sort"
        use_tests:
          - name: "bubblesort"
            search: "bubble_sort"
            replace: "merge_sort"

Example
=======

The following is an example of a full ``.glotter.yml``

.. code-block:: yaml

    settings:
      acronym_scheme: "two_letter_limit"
      source_root: "./sources"

    projects:
      fileio:
        words:
          - "file"
          - "io"
        acronyms:
          - "io"
        tests:
          fileio:
            - expected:
              exec: "cat output.txt"
      factorial:
        words:
          - "factorial"
        requires_parameters: true
        tests:
          factorial_valid:
            params:
              - name: "value 1"
                input: "1"
                expected: "1"
              - name: "value 5"
                input: "5"
                expected: "120"
            transformations:
              - "strip"
          factorial_invalid:
            params:
              - name: "no input"
                input: null
                expected: "Some error message"
              - name: "empty input"
                input: '""'
                expected: "Some error message"
            transformations:
              - "strip"
      helloworld:
        words:
          - "hello"
          - "world"
        tests:
            hello_world:
                params:
                  - expected: "Hello, world!"
                transformations:
                  - "strip"
      quine:
        words:
          - "quine"
        tests:
            quine:
                params:
                  - expected:
                    - self: ""
                transformations:
                  - "strip"
                  - "strip_expected"
      bubblesort:
        words:
          - "bubble"
          - "sort"
        requires_parameters: true
        bubble_sort_valid:
          inputs:
            - "List Input"
          params:
            - name: "not sorted"
              input: '"4, 5, 1, 3, 2"'
              expected: "1, 2, 3, 4, 5"
            - name: "already sorted"
              input: '"1, 2, 3, 4"'
              expected: "1, 2, 3, 4"
          transformations:
            -   remove:
                - "["
                - "]"
            -   "strip"
        bubble_sort_invalid:
          inputs:
            - "List Input"
          params:
            - name: "no input"
              input: null
              expected: "Some error"
            - name: "empty input"
              input: '""'
              expected: "Some error"
          transformations:
            - "strip"
      mergesort:
        words:
          - "merge"
          - "sort"
        use_tests:
          - name: "bubblesort"
            search: "bubble_sort"
            replace: "merge_sort"

If you'd like to see a full working example of a ``.glotter.yml``, see the
one in `sample-programs <https://github.com/TheRenegadeCoder/sample-programs/blob/main/.glotter.yml>`_.
To see what the auto-generated code looks like, see the `sample-programs-auto-gen-tests 
<https://github.com/rzuckerm/sample-programs-auto-gen-tests/tree/main/test/generated>`_ repository.
