.. SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
..
.. SPDX-License-Identifier: BSD-3-Clause

.. _clapper.logging:

============================
 Logging Helpers and Policy
============================

We advise the use of the Python :py:mod:`logging` module to log messages from
your library.  If you are unfamiliar with the design and use of that standard
Python module, we suggest you read our :ref:`clapper.logging.rationale`.

We provide a single a method in this library to help setup a particular
:py:class:`logging.Logger` to output to a (text-based) stream.  The
documentation of :py:func:`clapper.logging.setup` explains in details what it
does.  To use it in an application, follow this pattern:

.. code-block:: python

   import logging
   from clapper.logging import setup
   logger = setup("mypackage", format="%(levelname)s: %(message)s")
   logger.setLevel(logging.INFO)  # set log-level as you wish
   logger.info("test message")  # use at application level, normally
   INFO: test message


To help with setting the base logger level via the CLI, we provide a
:py:mod:`click` :ref:`clapper.click.verbosity`.  A full example can be seen at
:ref:`clapper.click.configcommand` and :ref:`clapper.click.rc_helpers`.


.. _clapper.logging.rationale:

Logging Setup Rationale
-----------------------

In essence, each library may be composed of a hierarchical tree of loggers
attached to a base root logger.  The tree resembles the Python module system
where module hierarchies are defined by ``.`` (dots).  It is common practice
that each module in a library or application logs *exclusively* to its own
private logger, as such:

.. code-block:: python

   # in library.module1
   import logging
   logger = logging.getLogger(__name__)  # __name__ == library.module1

   # now log normally through this module
   logger.info(f"info test from module {__name__}")

   # in library.module2
   import logging
   logger = logging.getLogger(__name__)  # __name__ == library.module2

   # now log normally through this module
   logger.info(f"info test from module {__name__}")


By the way the logging module is set up by default, no messages should be seen
on your console by virtue of the above code.  To actually be able to see
messages, one needs to associate the various loggers to an output (e.g. by
connecting these loggers to a console output handler).

If you start Python, import your library, and inspect the logging system
hierarchy (e.g., use the `logging-tree module`_), the logging system should
have these instantiated loggers:

.. code-block::

   + RootLogger

       + Logger("library")

           + Logger("library.module1")

           + Logger("library.module2")


The logger for your ``library`` is instantiated because the loggers for the
submodules ``library.module1`` and ``library.module2`` were created (when you
called :py:func:`logging.getLogger`, and imported those modules).  The loggers
are arranged in a hierarchy as you would expect, with a default ``RootLogger``
in the very top.

Messages generated at a lower-level logger (e.g. ``library.module2``) will be
handled by handlers attached to:

* ``Logger("library.module2")``
* ``Logger("library")``
* ``RootLogger``

in this order. If any of these levels have a handler attached and properly
configured to output informational messages, then you will be able to see
printouts on your screen (or log file).

Because of this structure and functioning, affecting the ``RootLogger`` is
seldomly advisable, since it may affect logging of **all libraries loaded by
your application**.  For example, if your application imports ``scipy``, and
that library uses the logging module, changing the ``RootLogger`` may imply in
logging messages showing up at your console also for ``scipy``. This is rarely
useful, unless you want to debug those other modules.

In this context, these are our recommendations:

* If you are designing a library without applications, we recommend you **do
  not setup any logging handlers** anywhere in your modules, and log as
  explained above.  If you do this, then users of your library will not have
  unwanted logging messages from your library on their screens or output files.
* If you provide an application with your library, e.g. a CLI application, then
  configure the package "base" logger (``Logger("library")`` in the example
  above), so all messages from your package are visible upon user
  configuration.


.. include:: links.rst
