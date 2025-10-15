.. SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
..
.. SPDX-License-Identifier: BSD-3-Clause

.. _clapper:

====================================================
 Configuration Support for Python Packages and CLIs
====================================================

.. todolist::

This package provides a way to define command-line-interface (CLI) applications such
that user options can be stored in Python-based configuration files and read-out
automatically.  It also provides a rather simple RC file support, based on TOML_ that
can be used by modules to read application-wide default values.

The project depends on an external Python package for CLI development, called click_,
the tomli_ TOML_ parser, and the standard :py:mod:`logging` modules.  As a framework, no
messages are directly printed to the screen.


Documentation
-------------

.. toctree::
   :maxdepth: 2

   install
   rc
   config
   logging
   click
   api


Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


.. include:: links.rst
