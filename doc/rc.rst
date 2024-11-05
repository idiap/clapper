.. SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
.. SPDX-FileContributor: Amir Mohammadi  <amir.mohammadi@idiap.ch>
..
.. SPDX-License-Identifier: BSD-3-Clause

.. _clapper.rc:

==============================
 Global Configuration Options
==============================

In this section, we deal with configuration values that must typically be
provided by the user on a per-machine or per-system basis.  Example values that
are local to a system or machine can be, for example, access credentials to a
database, or the root location of files used in a Machine Learning (ML)
pipeline.  Typically, in these cases, developers want to allow users to
configure such values once and have a programmatic way to access such values at
run time.  Module :py:mod:`clapper.rc` provides code to facilitate the
implementation and setup of this functionality.


Storage
-------

Global configuration options are stored in TOML_ format, in a file whose
location is specified by you.  The class :py:class:`clapper.rc.UserDefaults` can
load such a file and provide access to values set therein:

.. code-block:: python

   >>> from clapper import rc
   >>> defaults = rc.UserDefaults("myapprc.toml")

.. note::

   If the input filename given upon the construction of
   :py:class:`clapper.rc.UserDefaults` is not absolute, it is considered
   relative to the value of the environment variable ``$XDG_CONFIG_HOME``. In
   UNIX-style operating systems, the above example would typically resolve to
   ``${HOME}/.config/myapprc.toml``. Check the `XDG defaults <xdg-defaults_>`_
   for specifics.


Reading and writing values
--------------------------

You may use dictionary methods to get and set variables on any
:py:class:`clapper.rc.UserDefaults`, besides all other methods related to
mapping types (such as ``len()`` or ``setdefault()``).


Writing changes back
--------------------

To write changes back to the configuration file, use the
:py:meth:`clapper.rc.UserDefaults.write` method, which requires no parameters,
writing directly to the "default" location set during construction:

.. code-block:: python

   >>> defaults.write()


.. warning::

   This command will override the current configuration file and my erase any
   user comments added by the user.  To avoid this, simply edit your
   configuration file by hand.


Adding a global RC functionality to your module
-----------------------------------------------

To add a global object that reads user defaults into your application, we
recommend you create a module containing a configured instance of
:py:class:`clapper.rc.UserDefaults`.  Then, within your command-line interface,
import that module to trigger reading out the necessary variables.  For
example:


.. code-block:: python

   # module "config"
   from clapper.rc import UserDefaults
   rc = UserDefaults("~/.myapprc.toml", "MYAPPRC")

   # module "cli"
   from .config import rc
   value = rc["section"]["value-of-interest"]


Defining a command-line interface to the RC functionality
---------------------------------------------------------

We provide command plugins for you to define CLI-based get/set operations on
your configuration file.  This is discussed at :ref:`clapper.click`.


.. include:: links.rst
