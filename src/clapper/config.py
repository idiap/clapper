# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Amir Mohammadi  <amir.mohammadi@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

"""Functionality to implement python-based config file parsing and loading."""

import importlib.util
import logging
import pathlib
import types
import typing

from importlib.metadata import EntryPoint, entry_points

logger = logging.getLogger(__name__)

_LOADED_CONFIGS = []
"""Small gambiarra (https://www.urbandictionary.com/define.php?term=Gambiarra)
to avoid the garbage collector to collect some already imported modules."""


def _load_context(path: str, mod: types.ModuleType) -> types.ModuleType:
    """Load the Python file as module, returns a resolved context.

    This function is implemented in a way that is both Python 2 and Python 3
    compatible. It does not directly load the python file, but reads its
    contents in memory before Python-compiling it. It leaves no traces on the
    file system.

    Arguments:

        path: The full path of the Python file to load the module contents from

        mod: A preloaded module to use as a default context for the next module
            loading. You can create a new module using :py:mod:`types` as in:

            .. code-block:: python

               ctxt: dict[str, typing.Any] = {}
               m = types.ModuleType("name")
               m.__dict__.update(ctxt)

            ``ctxt`` is a python dictionary mapping strings to object values
            representing the contents of the module to be created.


    Returns
    -------
        A python module with the fully resolved context
    """
    # executes the module code on the context of previously imported modules
    with pathlib.Path(path).open("rb") as f:
        exec(compile(f.read(), path, "exec"), mod.__dict__)

    return mod


def _get_module_filename(module_name: str) -> str | None:
    """Resolve a module name to an actual Python file.

    This function will return the path to the file containing the module named
    at ``module_name``.  Values for this parameter are dot-separated module
    names such as ``expose.config``.


    Arguments:

        module_name: The name of the module to search


    Returns
    -------
        The path that corresponds to file implementing the provided module name
    """
    try:
        module_spec = importlib.util.find_spec(module_name)
        if module_spec is None:
            return None
        return module_spec.origin
    except (ModuleNotFoundError,):
        return None


def _object_name(
    path: str | pathlib.Path, common_name: str | None
) -> tuple[str, str | None]:
    if isinstance(path, pathlib.Path):
        path = str(path)

    r = path.rsplit(":", 1)
    return r[0], (common_name if len(r) < 2 else r[1])


def _resolve_entry_point_or_modules(
    paths: list[str | pathlib.Path],
    entry_point_group: str | None = None,
    common_name: str | None = None,
) -> tuple[list[str], list[str], list[str]]:
    """Resolve a mixture of paths, entry point names, and module names to
    path.

    This function can resolve actual file system paths, ``setup.py``
    entry-point names and module names to a set of file system paths.

    Examples of things that can be resolved by this function are:
    ``["/tmp/config.py", "my-config", "expose.config"]`` (an actualy filesystem
    path, an entry-point described in a ``setup.py`` file, or the name of a
    python module.

    Parameters
    ----------
    paths
        An iterable strings that either point to actual files, are entry point
        names, or are module names.
    entry_point_group
        The entry point group name to search in entry points.
    common_name
        It will be used as a default name for object names. See the
        ``attribute_name`` parameter from :py:func:`load`.


    Returns
    -------
        A tuple containing three lists of strings with:

        * The resolved paths pointing to existing files
        * The valid python module names to bind each of the files to, and
          finally,
        * The name of objects that are supposed to be picked from paths


    Raises
    ------
    ValueError
        If one of the paths cannot be resolved to an actual path to a file.
    """

    if entry_point_group is not None:
        entry_point_dict: dict[str, EntryPoint] = {
            e.name: e for e in entry_points(group=entry_point_group)
        }
    else:
        entry_point_dict = {}

    files = []
    module_names = []
    object_names = []

    for path in paths:
        module_name = "user_config"  # fixed module name for files with full paths
        resolved_path, object_name = _object_name(path, common_name)

        # if it already points to a file, then do nothing
        if pathlib.Path(resolved_path).is_file():
            pass

        # If it is an entry point name, collect path and module name
        elif resolved_path in entry_point_dict:
            entry = entry_point_dict[resolved_path]
            module_name = entry.module
            object_name = entry.attr if entry.attr else common_name

            resolved_path = _get_module_filename(module_name)
            if resolved_path is None or not pathlib.Path(resolved_path).is_file():
                raise ValueError(
                    f"The specified entry point `{path}' pointing to module "
                    f"`{module_name}' and resolved to `{resolved_path}' does "
                    f"not point to an existing file."
                )

        # If it is not a path nor an entry point name, it is a module name then?
        else:
            # if we have gotten here so far then path must resolve as a module
            resolved_path = _get_module_filename(resolved_path)
            if resolved_path is None or not pathlib.Path(resolved_path).is_file():
                raise ValueError(
                    f"The specified path `{path}' is not a file, a entry "
                    f"point name, or a known-module name"
                )

        files.append(resolved_path)
        module_names.append(module_name)
        object_names.append(object_name)

    return files, module_names, object_names


def load(
    paths: list[str | pathlib.Path],
    context: dict[str, typing.Any] | None = None,
    entry_point_group: str | None = None,
    attribute_name: str | None = None,
) -> types.ModuleType | typing.Any:
    """Load a set of configuration files, in sequence.

    This method will load one or more configuration files. Every time a
    configuration file is loaded, the context (variables) loaded from the
    previous file is made available, so the new configuration file can override
    or modify this context.

    Parameters
    ----------
    paths
        A list or iterable containing paths (relative or absolute) of
        configuration files that need to be loaded in sequence. Each
        configuration file is loaded by creating/modifying the context
        generated after each file readout.
    context
        If provided, start the readout of the first configuration file with the
        given context. Otherwise, create a new internal context.
    entry_point_group
        If provided, it will treat non-existing file paths as entry point names
        under the ``entry_point_group`` name.
    attribute_name
        If provided, will look for the ``attribute_name`` variable inside the
        loaded files. Paths ending with ``some_path:variable_name`` can
        override the ``attribute_name``. The ``entry_point_group`` must
        provided as well ``attribute_name`` is not ``None``.


    Returns
    -------
        A module representing the resolved context, after loading the provided
        modules and resolving all variables. If ``attribute_name`` is given,
        the object with the given ``attribute_name`` name (or the name provided
        by user) is returned instead of the module.


    Raises
    ------
    ImportError
        If attribute_name is given but the object does not exist in the paths.
    ValueError
        If attribute_name is given but entry_point_group is not given.
    """

    # resolve entry points to paths
    resolved_paths, names, object_names = _resolve_entry_point_or_modules(
        paths, entry_point_group, attribute_name
    )

    ctxt = types.ModuleType("initial_context")
    if context is not None:
        ctxt.__dict__.update(context)

    # Small gambiarra (https://www.urbandictionary.com/define.php?term=Gambiarra)
    # to avoid the garbage collector to collect some already imported modules.
    _LOADED_CONFIGS.append(ctxt)

    # if no paths are provided, return context
    if not resolved_paths:
        return ctxt

    mod = None
    for k, n in zip(resolved_paths, names):
        logger.debug("Loading configuration file `%s'...", k)
        mod = types.ModuleType(n)
        # remove the keys that might break the loading of the next config file.
        ctxt.__dict__.pop("__name__", None)
        ctxt.__dict__.pop("__package__", None)
        # do not propogate __ variables
        context = {k: v for k, v in ctxt.__dict__.items() if not k.startswith("__")}
        mod.__dict__.update(context)
        _LOADED_CONFIGS.append(mod)
        ctxt = _load_context(k, mod)

    if not attribute_name:
        return mod

    # We pick the last object_name here. Normally users should provide just one
    # path when enabling the attribute_name parameter.
    attribute_name = object_names[-1]
    if attribute_name is not None and not hasattr(mod, attribute_name):
        raise ImportError(
            f"The desired variable `{attribute_name}' does not exist in any of "
            f"your configuration files: {', '.join(resolved_paths)}"
        )

    return getattr(mod, attribute_name)


def mod_to_context(mod: types.ModuleType) -> dict[str, typing.Any]:
    """Convert the loaded module of :py:func:`load` to a dictionary context.

    This function removes all the variables that start and end with ``__``.

    Parameters
    ----------
    mod
        a Python module, e.g., as returned by :py:func:`load`.

    Returns
    -------
        The context that was in ``mod``, as a dictionary mapping strings to
        objects.
    """
    return {
        k: v
        for k, v in mod.__dict__.items()
        if not (k.startswith("__") and k.endswith("__"))
    }


def resource_keys(
    entry_point_group: str,
    exclude_packages: tuple[str, ...] = tuple(),
    strip: tuple[str, ...] = ("dummy",),
) -> list[str]:
    """Read and returns all resources that are registered on a entry-point
    group.

    Entry points from the given ``exclude_packages`` list are ignored.  Notice
    we are using :py:mod:`importlib.metadata` to load entry-points, and that
    that entry point distribution (``.dist`` attribute) was only added to
    Python in version 3.10.  We therefore currently only verify if the named
    resource does not start with any of the strings provided in
    `exclude_package``.

    Parameters
    ----------
    entry_point_group
        The entry point group name.
    exclude_packages
        List of packages to exclude when finding resources.
    strip
        Entrypoint names that start with any value in ``strip`` will be
        ignored.


    Returns
    -------
        Alphabetically sorted list of resources matching your query
    """

    ret_list = [
        k.name
        for k in entry_points(group=entry_point_group)
        if (
            (not k.name.strip().startswith(exclude_packages))
            and (not k.name.startswith(strip))
        )
    ]
    ret_list = list(dict.fromkeys(ret_list))  # order-preserving uniq
    return sorted(ret_list)
