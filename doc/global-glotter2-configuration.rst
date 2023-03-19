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

Tests
-----

- **Optional**
- **Format**

  .. code-block:: yaml

    tests:
      test_name1:
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

``tests`` is a dictionary that describes auto-generated tests. Each auto-generate test
has a name that is a key. Each of these tests have is a list of parameter dictionaries,
``params``. This is required. Each list has the following item:

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
- ``input`` is a string. It is required if ``requires_parameters`` is ``true``.
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

- `"strip"`: Remove leading and trailing whitespace from the actual value.
- `"splitlines"`: Split actual value at each newline character -- e.g., ``"1\n2\n3"`` is
  converted to the list ``["1", "2", "3"]``.
- `"lower"`: Convert the actual value to lowercase.
- `"any_order"`: Convert the actual and expected value into a sorted list of unique
  values -- e.g., a list of ``["7", "3", "1", "7"]`` is converted to ``["1", "3", "7"]``.
- ``strip_expected``: Remove leading a trailing whitespace from the expected value.

The following transformations are dictionaries:

- "remove": Remove all listed characters from the actual value:

  .. code-block:: yaml

    - "remove":
      - "char1"
      - "char2"
      - ...

- "strip": Remove leading and trailing characters from the actual value.

  .. code-block:: yaml

    - "strip":
      - "char1"
      - "char2"
      - ...

Format
------

The format for a project is as follows:

.. code-block:: yaml

    projectkey:
      words:
        - "words"
        - "in"
        - "project"
      acronyms:
        - "acronyms"
        - "in"
        - "project"
      requires_parameters: true

So for example. Let's say I have three projects named FileIO, Factorial, and HelloWorld.
FileIO contains an acronym.
Factorial requires parameters.
My ``projects`` section would look like this:

.. code-block:: yaml

    projects:
      fileio:
        words:
          - "file"
          - "io"
        acronyms:
          - "io"
      factorial:
        words:
          - "factorial"
        requires_parameters: true
      helloworld:
        words:
          - "hello"
          - "world"

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
      factorial:
        words:
          - "factorial"
        requires_parameters: true
      helloworld:
        words:
          - "hello"
          - "world"
