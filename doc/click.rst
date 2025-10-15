.. SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
.. SPDX-FileContributor: Amir Mohammadi  <amir.mohammadi@idiap.ch>
..
.. SPDX-License-Identifier: BSD-3-Clause

.. _clapper.click:

======================
 Command-Line Helpers
======================

This package provides a few handy additions to the click_ command-line
interface (CLI) library, allowing one to build even more powerful CLIs.


.. _clapper.click.verbosity:

Verbosity Option
----------------

The :py:func:`clapper.click.verbosity_option` click_ decorator allows
one to control the logging-level of a pre-defined :py:class:logging.Logger.
Here is an example usage.

.. code-block:: python

   import clapper.click
   import logging

   # retrieve the base-package logger
   logger = logging.getLogger(__name__.split(".", 1)[0])


   @clapper.click.verbosity_option(logger)
   def cli(verbose):
       pass

The verbosity option binds the command-line (``-v``) flag usage to setting the
:py:class:`logging.Logger` level by calling :py:meth:`logging.Logger.setLevel`
with the appropriate logging level, mapped as such:

* 0 (the user has provide no ``-v`` option on the command-line):
  ``logger.setLevel(logging.ERROR)``
* 1 (the user provided a single ``-v``): ``logger.setLevel(logging.WARNING)``
* 2 (the user provided the flag twice, ``-vv``):
  ``logger.setLevel(logging.INFO)``
* 3 (the user provide the flag thrice or more, ``-vvv``):
  ``logger.setLevel(logging.DEBUG)``

.. note::
   If you do not care about the ``verbose`` parameter in your command and only
   rely on the decorator to set the logging level, you can set ``expose_value``
   to ``False``:

   .. code-block:: python

      @clapper.click.verbosity_option(logger, expose_value=False)
      def cli():
          pass



.. _clapper.click.configcommand:

Config Command
--------------

The :py:class:`clapper.click.ConfigCommand` is a type of
:py:class:`click.Command` in which declared CLI options may be either passed
via the command-line, or loaded from a :ref:`clapper.config`.  It works by
reading the Python configuration file and filling up option values pretty much
as click_ would do, with one exception: CLI options can now be of any
Pythonic type.

To implement this, a CLI implemented via :py:class:`clapper.click.ConfigCommand`
may not declare any arguments, only options.  All arguments are interpreted as
configuration files, from where option values will be set, in order.  Any type
of configuration resource can be provided (file paths, python modules or
entry-points).  Command-line options take precedence over values set in
configuration files.  The order of configuration files matters, and the final
values for CLI options follow the same rules as in
:ref:`clapper.config.chain-loading`.

Options that may be read from configuration files must also be marked with the
custom click-type :py:class:`clapper.click.ResourceOption`.

Here is an example usage of this class:

.. literalinclude:: example_cli.py
   :caption: Example CLI with config-file support
   :language: python


If a configuration file is setup like this:

.. literalinclude:: example_options.py
   :caption: Example configuration file for the CLI above
   :language: python


Then end result would be this:

.. command-output:: python example_cli.py example_options.py


Notice that configuration options on the command-line take precedence:

.. command-output:: python example_cli.py --str=baz example_options.py


Configuration options can also be loaded from `package entry-points`_ named
``test.app``.  To do this, a package setup would have to contain a group named
``test.app``, and list entry-point names which point to modules containing
variables that can be loaded by the CLI application.  For example, would a
package declare this entry-point:

.. code-block:: python

    entry_points={
        # some test entry_points
        'test.app': [
            'my-config = path.to.module.config',
            ...
        ],
    },

Then, the application shown above would also be able to work like this:

.. code-block:: shell

   python example_cli.py my-config


Options with type :py:class:`clapper.click.ResourceOption` may also point to
individual resources (specific variables on python modules). This may be,
however, a more seldomly used feature.  Read the class documentation for
details.


.. _clapper.click.aliasedgroups:

Aliased Command Groups
----------------------

When designing an CLI with multiple subcommands, it is sometimes useful to be
able to shorten command names.  For example, being able to use ``git ci``
instead of ``git commit``, is a form of aliasing.  To do so in click_
CLIs, it suffices to subclass all command group instances with
:py:class:`clapper.click.AliasedGroup`.  This should include groups and
subgroups of any depth in your CLI.  Here is an example usage:


.. literalinclude:: example_alias.py
   :caption: Example CLI with group aliasing support
   :language: python

You may then shorten the command to be called such as this:

.. command-output:: python example_alias.py pu


.. _clapper.click.config_helpers:

Experiment Options (Config) Command-Group
-----------------------------------------

When building complex CLIs in which support for `configuration
<:ref:clapper.config>`_ is required, it may be convenient to provide users with
CLI subcommands to display configuration resources (examples) shipped with the
package.  To this end, we provide an easy to plug :py:class:`click.Group`
decorator that attaches a few useful subcommands to a predefined CLI command,
from your package.  Here is an example on how to build a CLI to do this:


.. literalinclude:: example_config.py
   :caption: Implementation a command group to affect the RC file of an application.
   :language: python


Here is the generated command-line:

.. command-output:: python example_config.py --help


You may try to use that example application like this:

.. code-block:: shell

   # lists all installed resources in the entry-point-group
   # "clapper.test.config"
   $ python doc/example_config.py list
   module: tests.data
       complex
       complex-var
       first
       first-a
       first-b
       second
       second-b
       second-c
       verbose-config

   # describes a particular resource configuration
   # Adding one or more "-v" (verbosity) options affects
   # what is printed.
   $ python doc/example_config.py describe "complex" -vv
   Configuration: complex
   Python Module: tests.data.complex

   Contents:
   cplx = dict(
       a="test",
       b=42,
       c=3.14,
       d=[1, 2, 37],
   )

   # copies the module pointed by "complex" locally (to "local.py")
   # for modification and testing
   $ python doc/example_config.py copy complex local.py
   $ cat local.py
   cplx = dict(
       a="test",
       b=42,
       c=3.14,
       d=[1, 2, 37],
   )

.. _clapper.click.rc_helpers:

Global Configuration (RC) Command-Group
---------------------------------------

When building complex CLIs in which support for `global configuration
<:ref:clapper.rc>`_ is required, it may be convenient to provide users with CLI
subcommands to display current values, set or get the value of specific
configuration variables.  For example, the ``git`` CLI provides the ``git
config`` command that fulfills this task.  Here is an example on how to build a
CLI to affect your application's global RC file:


.. literalinclude:: example_defaults.py
   :caption: Implementation a command group to affect the RC file of an application.
   :language: python


Here is the generated command-line:

.. command-output:: python example_defaults.py --help


You may try to use that example application like this:

.. code-block:: shell

   $ python example_defaults.py set foo 42
   $ python example_defaults.py set bla.float 3.14
   $ python example_defaults.py get bla
   {'float': 3.14}
   $ python example_defaults.py show
   foo = 42

   [bla]
   float = 3.14
   $ python example_defaults.py rm bla
   $ python example_defaults.py show
   foo = 42
   $


.. _clapper.click.entrypoins:

Multi-package Command Groups
----------------------------

You may have to write parts of your CLI in different software packages.  We
recommend you look into the `Click-Plugins extension module <click-plugins_>`_
as means to implement this in a Python-oriented way, using the `package
entry-points`_ (plugin) mechanism.

.. _clapper.click.log_parameters:

Log Parameters
--------------

The :py:func:`clapper.click.log_parameters` click_ method allows one to log the
parameters used within the current click context and their value for debuging purposes.
Here is an example usage.

.. code-block:: python

   import clapper.click
   import logging

   # retrieve the base-package logger
   logger = logging.getLogger(__name__)


   @clapper.click.verbosity_option(logger, short_name="vvv")
   def cli(verbose):
      clapper.click.log_parameters(logger)

A pre-defined :py:class:`logging.Logger` have to be provided and, optionally,
a list of parameters to ignore can be provided as well, as a Tuple.


.. include:: links.rst
