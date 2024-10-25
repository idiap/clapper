.. SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
.. SPDX-FileContributor: Amir Mohammadi  <amir.mohammadi@idiap.ch>
..
.. SPDX-License-Identifier: BSD-3-Clause

.. _clapper.config:

====================================
 Experimental Configuration Options
====================================

In this section, we deal with configuration values that must typically be
provided by the user on a per-job basis.  That is, every time the user executes
an application, the options may change.  Global defaults are not very good for
these type of options, that are typically stored in configuration files read by
command-line options.

Instead of yet-another-configuration-file format, we propose to use Python
itself to define configuration options.  Variables set on the file act as
options themselves, and can assume any format or type.  A mechanism of chain
loading allows an overwriting behaviour to take place.

Because configuration files are Python files, they can be distributed with your
application, within the module itself, and are easy to find.  Using `package
entry-points`_, it is possible to create shortcuts to important configuration
files provided with the package, for easy access.


Loading configuration options
-----------------------------

There is only one single function that matters in this module:
:py:func:`clapper.config.load`.  You should use it to load Python configuration
options:

To load a configuration file, containing options into a dictionary mapping
variable names to values (of any Python type), use
:py:func:`clapper.config.load`:

.. doctest::

   >>> import os.path
   >>> from clapper.config import load
   >>> options = load([os.path.join(data, "basic_config.py")])


If the function :py:func:`clapper.config.load` succeeds, it returns a
python module containing variables which represent the configuration resource.
For example, if the file ``basic_config.py`` contained:

.. literalinclude:: data/basic_config.py
   :language: python
   :linenos:
   :caption: "basic_config.py"


Then, the object ``options`` would look like this:

.. doctest::

   >>> print(f"a = {options.a}\nb = {options.b}")
   a = 1
   b = 3


.. _clapper.config.chain-loading:

Chain Loading
-------------

It is possible to implement chain configuration loading and overriding by
passing iterables with more than one filename to
:py:func:`clapper.config.load`. Suppose we have two configuration files
which must be loaded in sequence:

.. literalinclude:: data/basic_config.py
   :caption: "basic_config.py" (first to be loaded)
   :language: python
   :linenos:

.. literalinclude:: data/second_config.py
   :caption: "second_config.py" (loaded after basic_config.py)
   :language: python
   :linenos:


Then, one can chain-load them like this:

.. doctest::

   >>> import os.path
   >>> from clapper.config import load
   >>> file1 = os.path.join(data, "basic_config.py")
   >>> file2 = os.path.join(data, "second_config.py")
   >>> configuration = load([file1, file2])
   >>> print(f"a = {configuration.a} \nb = {configuration.b} \nc = {configuration.c}") # doctest: +NORMALIZE_WHITESPACE
   a = 1
   b = 6
   c = 4


The user wanting to override the values needs to manage the overriding and the
order in which the override happens.


.. _clapper.config.entry_points:

Entry Points and Python Modules
-------------------------------

The function :py:func:`clapper.config.load` can also load config files through
module entry-points, or Python module names.  Entry-points are simply aliases
to Python modules and objects.  To load entry-points via
:py:func:`clapper.config.load`, you must provide the group name of the entry
points.  For example, if in your package setup, you defined the following
entry-points to 2 python modules such as the examples above:

.. code-block:: python

    entry_points={
        ...
        'mypackage.config': [
            'basic = mypackage.config.basic',
            'second = mypackage.config.second',
        ],
        ...

You could do the same as such:

.. code-block:: python

   >>> from clapper.config import load
   >>> configuration = load(["basic", "second"], entry_point_group="mypackage.config")
   >>> print(f"a = {configuration.a} \nb = {configuration.b} \nc = {configuration.c}")
   a = 1
   b = 6
   c = 4

Or even refer to the module names themselves (instead of the entry-point names):

.. code-block:: python

   >>> from clapper.config import load
   >>> configuration = load(["mypackage.config.basic", "mypackage.config.second"])
   >>> print(f"a = {configuration.a} \nb = {configuration.b} \nc = {configuration.c}")
   a = 1
   b = 6
   c = 4

Of course, mixture of entry-point names, paths and module names are also acceptable:

.. code-block:: python

   >>> configuration = load(["basic", "mypackage.config.second"], entry_point_group="mypackage.config")
   >>> print(f"a = {configuration.a} \nb = {configuration.b} \nc = {configuration.c}")
   a = 1
   b = 6
   c = 4


.. _clapper.config.resource:

Loading Single Objects
----------------------

The function :py:func:`clapper.config.load` can also be used to load the
contents of specific variables within configuration files. To do this, you need
provide the name of an attribute to load.

.. doctest::

   >>> import os.path
   >>> from clapper.config import load
   >>> load([os.path.join(data, "basic_config.py")], attribute_name="b")
   3


.. include:: links.rst
