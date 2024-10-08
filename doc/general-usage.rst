=============
General Usage
=============

Glotter2 is an execution library for collections of single file scripts.
It uses Docker to be able to build and run scripts in any language without having
to install a local sdk or development environment.

Before Glotter2 can be used, your project must be configured.
See :ref:`integrating-with-glotter2` for more information

The Glotter2 CLI has these main commands:

- `download`_
- `run`_
- `test`_
- `report`_
- `batch`_
- `check`_

All of these commands have this optional argument:

==========  ==========  ===========
Flag        Short Flag  Description
==========  ==========  ===========
``--help``  ``-h``      Print help text and exit
==========  ==========  ===========

While the `download`, `run`, and `test` commands serve different functions
(described below), each has the following optional arguments:

==============  ==========  ===========
Flag            Short Flag  Description
==============  ==========  ===========
``--source``    ``-s``      Perform action using a single source file
``--project``   ``-p``      Perform action using all sources relevant to a certain project key
``--language``  ``-l``      Perform action using all sources of a given language
==============  ==========  ===========

These optional arguments can be used together in the event that multiple languages
have the same filename and extension. For example, suppose that there are two programs
called ``hello_world.e``, one in Eiffel and one in Euphoria. If you want to force the
action on the Eiffel one, you would use one of the following:

- ``-l eiffel -p helloworld``
- ``-l eiffel -s hello_world.e``

--------
Download
--------

The ``download`` command is used to download any required docker images.
It is invoked using ``glotter download`` with any of the flags described above.

It is not necessary to invoke download manually before run or test.
It will be invoked automatically.
This command is exposed for convenience in cases where you want to have
everything you will need downloaded ahead of time.

The ``download`` command also has the following optional argument:

==============  ==========  ===========
Flag            Short Flag  Description
==============  ==========  ===========
``--parallel``              Download images in parallel
==============  ==========  ===========

---
Run
---

The ``run`` command is used to execute scripts.
It is invoked using ``glotter run`` with any of the flags described above.
If a script requires input, it will prompt for that information.

----
Test
----

The ``test`` command is used to execute tests for scripts.
It is invoked using ``glotter test`` with any of the flags described above.

The `test` command also has the following optional argument:

==============  ==========  ===========
Flag            Short Flag  Description
==============  ==========  ===========
``--parallel``              Run tests in parallel
==============  ==========  ===========

------
Report
------

The ``report`` command is used to output a report of discovered sources for configured
projects and languages.
It is invoked using ``glotter report``.

The ``report`` command has the following optional argument:

+--------------+------------+--------------------------------------------------------------------------------------+
| Flag         | Short Flag | Description                                                                          |
+==============+============+======================================================================================+
| ``--output`` | ``-o``     | Output the report as a `CSV <https://en.wikipedia.org/wiki/Comma-separated_values>`_ |
|              |            | at the specified report path instead of to stdout                                    |
+--------------+------------+--------------------------------------------------------------------------------------+

If ``-o`` is not specified, the report is output as `Markdown <https://www.markdownguide.org/basic-syntax/>`_ to stdout.

-----
Batch
-----

The ``batch`` command is only used in a Continuous Integration (CI) pipeline to limit the
amount of disk space used. It breaks up the image download, testing, and optional image removal
into individual batches.

The ``batch`` command has a required argument that specifies the number of batches to use (``<n>``).

The ``batch`` command also has the following optional arguments:

==============  ==========  ===========
Flag            Short Flag  Description
==============  ==========  ===========
``--batch``     ``-b``      Indicate the batch number (1 through ``<n>``). If not specified, all batches are run
``--parallel``              Download images, run tests, and optionally remove images in parallel
``--remove``                Indicates if the images should be removed after each batch is finished
==============  ==========  ===========

There are two modes in which ``batch`` can be used:

1. Serial
2. Parallel

Serial Mode
-----------

In this mode all batches are run one after another. It is highly recommended that ``--remove`` be used
with this mode in order to save disk space by removing images that are only used for the current batch.
For example, break the download, test, and removal into 3 batches and parallelize:

.. code-block:: text

    glotter batch 3 --remove --parallel

Parallel Mode
-------------

In this mode each batch is run on a different build server. This has the potential benefit of reducing
build time if a sufficient number of build servers are available. For this mode, it is not necessary to
specified ``--remove`` since the build server will clean itself up as soon as the current job is finished.
As with the previous example, break the download and test into 3 batches and parallelize for each
build server:

.. code-block:: text

    glotter batch 3 --batch <m> --parallel

where: ``<m>`` is ``1`` for the first build server, ``2`` for the second, and ``3`` for the third.

-----
Check
-----

The ``check`` command makes sure that the sample program files are named properly. If they are
not, a list of improperly named files are output, and this command exits with an non-zero return code.
Otherwise, this command exits with a zero return code.
