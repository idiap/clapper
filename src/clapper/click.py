# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause
"""Helpers to build command-line interfaces (CLI) via :py:mod:`click`."""

import functools
import inspect
import logging
import pathlib
import pprint
import shutil
import time
import typing

from importlib.metadata import EntryPoint

import click
import tomli

from click.core import ParameterSource

from .config import load, mod_to_context, resource_keys
from .rc import UserDefaults

module_logger = logging.getLogger(__name__)
"""Module logger."""

_COMMON_CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
"""Common click context settings."""


def verbosity_option(
    logger: logging.Logger,
    short_name: str = "v",
    name: str = "verbose",
    dflt: int = 0,
    **kwargs: typing.Any,
) -> typing.Callable[..., typing.Any]:
    """Click-option decorator that adds a ``-v``/``--verbose`` option to a cli.

    This decorator adds a click option to your CLI to set the log-level on a
    provided :py:class:`logging.Logger`.  You must specifically determine the
    logger that will be affected by this CLI option, via the ``logger`` option.

    .. code-block:: python

       @verbosity_option(logger=logger)

    The verbosity option has the "count" type, and has a default value of 0.
    At each time you provide ``-v`` options on the command-line, this value is
    increased by one.  For example, a CLI setting of ``-vvv`` will set the
    value of this option to 3.  This is the mapping between the value of this
    option (count of ``-v`` CLI options passed) and the log-level set at the
    provided logger:

    * 0 (no ``-v`` option provided): ``logger.setLevel(logging.ERROR)``
    * 1 (``-v``): ``logger.setLevel(logging.WARNING)``
    * 2 (``-vv``): ``logger.setLevel(logging.INFO)``
    * 3 (``-vvv`` or more): ``logger.setLevel(logging.DEBUG)``


    Arguments:

        logger: The :py:class:`logging.Logger` to be set.

        short_name: Short name of the option.  If not set, then use ``v``

        name: Long name of the option.  If not set, then use ``verbose`` --
            this will also become the name of the contextual parameter for click.

        dlft: The default verbosity level to use (defaults to 0).

        **kwargs: Further keyword-arguments to be forwarded to the underlying
            :py:func:`click.option`


    Returns
    -------
        A callable, that follows the :py:mod:`click`-framework policy for
        option decorators.  Use it accordingly.
    """

    def custom_verbosity_option(f):
        def callback(ctx, param, value):
            ctx.meta[name] = value
            log_level: int = {  # type: ignore
                0: logging.ERROR,
                1: logging.WARNING,
                2: logging.INFO,
                3: logging.DEBUG,
            }[value]

            logger.setLevel(log_level)
            logger.debug(f'Level of Logger("{logger.name}") was set to {log_level}')
            return value

        return click.option(
            f"-{short_name}",
            f"--{name}",
            count=True,
            type=click.IntRange(min=0, max=3, clamp=True),
            default=dflt,
            show_default=True,
            help=(
                f"Increase the verbosity level from 0 (only error and "
                f"critical) messages will be displayed, to 1 (like 0, but adds "
                f"warnings), 2 (like 1, but adds info messags), and 3 (like 2, "
                f"but also adds debugging messages) by adding the --{name} "
                f"option as often as desired (e.g. '-vvv' for debug)."
            ),
            callback=callback,
            is_eager=kwargs.get("cls", None) is not ResourceOption,
            **kwargs,
        )(f)

    return custom_verbosity_option


class ConfigCommand(click.Command):
    """A :py:class:`click.Command` that can read options from config files.

    .. warning::

       In order to use this class, you **have to** use the
       :py:class:`ResourceOption` class also.


    Arguments:

        name: The name to be used for the configuration argument

        *args: Unnamed parameters passed to :py:class:`click.Command`

        help: Help message associated with this command

        entry_point_group: Name of the entry point group from which
            entry-points will be searched

        **kwargs: Named parameters passed to :py:class:`click.Command`
    """

    config_argument_name: str
    """The name of the config argument."""

    entry_point_group: str
    """The name of entry point that will be used to load the config files."""

    def __init__(
        self,
        name: str,
        *args: tuple,
        help: str | None = None,  # noqa: A002
        entry_point_group: str | None = None,
        **kwargs: typing.Any,
    ) -> None:
        self.entry_point_group = entry_point_group
        configs_argument_name = "CONFIG"

        # Augment help for the config file argument
        self.extra_help = f"""\n\nIt is possible to pass one or several Python
files (or names of ``{entry_point_group}`` entry points or module names) as
{configs_argument_name} arguments to the command line which contain the parameters listed below as Python variables. The options through the command-line (see below)
will override the values of configuration files. You can run this command with
``<COMMAND> -H example_config.py`` to create a template config file."""
        help = (help or "").rstrip() + self.extra_help  # noqa: A001
        super().__init__(name, *args, help=help, **kwargs)

        # Add the config argument to the command
        def configs_argument_callback(ctx, param, value):
            config_context = load(value, entry_point_group=self.entry_point_group)

            config_context = mod_to_context(config_context)
            ctx.config_context = config_context
            module_logger.debug("Augmenting click context with config context")
            return value

        click.argument(
            configs_argument_name,
            nargs=-1,
            callback=configs_argument_callback,
            is_eager=True,  # runs first and unconditionally
        )(self)

        # Option for config file generation
        click.option(
            "-H",
            "--dump-config",
            type=click.File(mode="wt"),
            help="Name of the config file to be generated",
            is_eager=True,
            callback=self.dump_config,
        )(self)

    def dump_config(
        self,
        ctx: typing.Any,
        param: typing.Any,
        value: typing.TextIO | None,
    ) -> None:
        """Generate configuration file from parameters and context.

        Using this function will conclude the command-line execution.


        Arguments:

            ctx: Click context
        """

        config_file = value
        if config_file is None:
            return

        module_logger.debug(f"Generating configuration file `{config_file}'...")
        config_file.write('"""')
        config_file.write(
            f"Configuration file automatically generated at "
            f"{time.strftime('%d/%m/%Y')}.\n\n{ctx.command_path}\n"
        )

        if self.help:
            h = self.help.replace(self.extra_help, "").replace("\b\n", "")
            config_file.write(f"\n{h.rstrip()}")

        if self.epilog:
            config_file.write("\n\n{}".format(self.epilog.replace("\b\n", "")))

        config_file.write('\n"""\n')

        for param in self.params:
            if not isinstance(param, ResourceOption):
                # we can only handle ResourceOptions
                continue

            config_file.write(f"\n# {param.name} = {str(param.default)}\n")
            config_file.write('"""')

            if param.required:
                begin, dflt = "Required parameter", ""
            else:
                begin, dflt = (
                    "Optional parameter",
                    f" [default: {param.default}]",
                )

            config_file.write(f"{begin}: {param.name} ({', '.join(param.opts)}){dflt}")

            if param.help is not None:
                config_file.write(f"\n{param.help}")

            if (
                isinstance(param, ResourceOption)
                and param.entry_point_group is not None
            ):
                config_file.write(
                    f"\nRegistered entries are: "
                    f"{resource_keys(param.entry_point_group)}"
                )

            config_file.write('"""\n')

        click.echo(f"Configuration file `{config_file.name}' was written; exiting")

        config_file.close()
        ctx.exit()


class CustomParamType(click.ParamType):
    """Custom parameter class allowing click to receive complex Python types as
    parameters.
    """

    name = "custom"


class ResourceOption(click.Option):
    """An extended :py:class:`click.Option` that automatically loads resources
    from config files.

    This class comes with two different functionalities that are independent and
    could be combined:

    1. If used in commands that are inherited from :py:class:`ConfigCommand`,
       it will lookup inside the config files (that are provided as argument to
       the command) to resolve its value. Values given explicitly in the
       command line take precedence.

    2. If ``entry_point_group`` is provided, it will treat values given to it
       (by any means) as resources to be loaded. Loading is done using
       :py:func:`.config.load`. Check :ref:`clapper.config.resource` for more
       details on this topic. The final value cannot be a string.

    You may use this class in three ways:

    1. Using this class (without using :py:class:`ConfigCommand`) AND
       (providing ``entry_point_group``).
    2. Using this class (with :py:class:`ConfigCommand`) AND (providing
       `entry_point_group`).
    3. Using this class (with :py:class:`ConfigCommand`) AND (without providing
       `entry_point_group`).

    Using this class without :py:class:`ConfigCommand` and without providing
    `entry_point_group` does nothing and is not allowed.
    """

    entry_point_group: str | None
    """If provided, the strings values to this option are assumed to be entry
    points from ``entry_point_group`` that need to be loaded.

    This may be different than the wrapping :py:class:`ConfigCommand`.
    """

    string_exceptions: list[str] | None
    """If provided and ``entry_point_group`` is provided, the code will not
    treat strings in ``string_exceptions`` as entry points and does not try to
    load them."""

    def __init__(
        self,
        param_decls=None,
        show_default=False,
        prompt=False,
        confirmation_prompt=False,
        hide_input=False,
        is_flag=None,
        flag_value=None,
        multiple=False,
        count=False,
        allow_from_autoenv=True,
        type=None,  # noqa: A002
        help=None,  # noqa: A002
        entry_point_group=None,
        required=False,
        string_exceptions=None,
        **kwargs,
    ) -> None:
        # By default, if unspecified, click options are converted to strings.
        # By using ResourceOption's, however, we allow for complex user types
        # to be set into options. So, if no specific ``type``, a ``default``,
        # the ``count`` flag, or ``is_flag`` is given, we assume this is a
        # "custom" parameter type, and do not convert values to strings.
        if (
            (type is None)
            and (kwargs.get("default") is None)
            and (count is False)
            and (is_flag is None)
        ):
            type = CustomParamType()  # noqa: A001

        self.entry_point_group = entry_point_group
        if entry_point_group is not None:
            name, _, _ = self._parse_decls(param_decls, kwargs.get("expose_value"))
            help = help or ""  # noqa: A001
            help += (  # noqa: A001
                f" Can be a `{entry_point_group}' entry point, a module name, or "
                f"a path to a Python file which contains a variable named `{name}'."
            )
            help = help.format(entry_point_group=entry_point_group, name=name)  # noqa: A001

        super().__init__(
            param_decls=param_decls,
            show_default=show_default,
            prompt=prompt,
            confirmation_prompt=confirmation_prompt,
            hide_input=hide_input,
            is_flag=is_flag,
            flag_value=flag_value,
            multiple=multiple,
            count=count,
            allow_from_autoenv=allow_from_autoenv,
            type=type,
            help=help,
            required=required,
            **kwargs,
        )
        self.string_exceptions = string_exceptions or []

    def consume_value(
        self, ctx: click.Context, opts: dict
    ) -> tuple[typing.Any, ParameterSource]:
        """Retrieve value for parameter from appropriate context.

        This method will retrive the value of its own parameter from the
        appropriate context, by trying various sources.

        Parameters
        ----------
        ctx
            The click context to retrieve the value from
        opts
            command-line options, eventually passed by the user


        Returns
        -------
            A tuple containing the parameter value (of any type) and the source
            it used to retrieve it.
        """

        if (not hasattr(ctx, "config_context")) and self.entry_point_group is None:
            raise TypeError(
                "The ResourceOption class is not meant to be used this way. "
                "See package documentation for details."
            )

        module_logger.debug(f"consuming resource option for {self.name}")
        value = opts.get(self.name)
        source = ParameterSource.COMMANDLINE

        # if value is not given from command line, lookup the config files given as
        # arguments (not options).
        if value is None:
            # if this class is used with the ConfigCommand class. This is not always
            # true.
            if hasattr(ctx, "config_context"):
                value = ctx.config_context.get(self.name)

        # if not from config files, lookup the environment variables
        if value is None:
            value = self.value_from_envvar(ctx)
            source = ParameterSource.ENVIRONMENT

        # if not from environment variables, lookup the default value
        if value is None:
            value = ctx.lookup_default(self.name)
            source = ParameterSource.DEFAULT_MAP

        if value is None:
            value = self.get_default(ctx)
            source = ParameterSource.DEFAULT

        return value, source

    def type_cast_value(self, ctx: click.Context, value: typing.Any) -> typing.Any:
        """Convert and validate a value against the option's type.

        This method considers the option's ``type``, ``multiple``, and ``nargs``.
        Furthermore, if the an ``entry_point_group`` is provided, it will load
        it.

        Arguments:

            ctx: The click context to be used for casting the value

            value: The actual value, that needs to be cast


        Returns
        -------
            The cast value
        """
        value = super().type_cast_value(ctx, value)

        # if the value is a string and an entry_point_group is provided, load it
        if self.entry_point_group is not None:
            while isinstance(value, str) and value not in self.string_exceptions:
                value = load(
                    [value],
                    entry_point_group=self.entry_point_group,
                    attribute_name=self.name,
                )

        return value


class AliasedGroup(click.Group):
    """Class that handles prefix aliasing for commands.

    Basically just implements get_command that is used by click to choose the
    command based on the name.

    Example
    -------
    To enable prefix aliasing of commands for a given group,
    just set ``cls=AliasedGroup`` parameter in click.group decorator.
    """

    def get_command(self, ctx, cmd_name):
        """get_command with prefix aliasing."""
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        matches = [x for x in self.list_commands(ctx) if x.startswith(cmd_name)]
        if not matches:
            return None

        if len(matches) == 1:
            return click.Group.get_command(self, ctx, matches[0])

        ctx.fail(f"Too many matches: {', '.join(sorted(matches))}")  # noqa: RET503


def user_defaults_group(
    logger: logging.Logger,
    config: UserDefaults,
) -> typing.Callable[..., typing.Any]:
    """Add a command group to read/write RC configuration.

    This decorator adds a whole command group to a user predefined function
    which is part of the user's CLI.  The command group allows the user to get
    and set options through the command-line interface:

    .. code-block:: python

       import logging
       from expose.rc import UserDefaults
       from expose.click import user_defaults_group

       logger = logging.getLogger(__name__)
       user_defaults = UserDefaults("~/.myapprc")
       ...


       @user_defaults_group(logger=logger, config=user_defaults)
       def rc(**kwargs):
           '''Use this command to affect the global user configuration.'''
           pass


    Then use it like this:

    .. code-block:: shell

       $ user-cli rc --help
       usage: ...
    """

    def group_decorator(
        func: typing.Callable[..., typing.Any],
    ) -> typing.Callable[..., typing.Any]:
        @click.group(
            cls=AliasedGroup,
            no_args_is_help=True,
            context_settings=_COMMON_CONTEXT_SETTINGS,
        )
        @verbosity_option(logger=logger)
        @functools.wraps(func)
        def group_wrapper(**kwargs):
            return func(**kwargs)

        @group_wrapper.command(context_settings=_COMMON_CONTEXT_SETTINGS)
        @verbosity_option(logger=logger)
        def show(**_: typing.Any) -> None:
            """Show the user-defaults file contents."""
            click.echo(str(config).strip())

        @group_wrapper.command(
            no_args_is_help=True,
            context_settings=_COMMON_CONTEXT_SETTINGS,
        )
        @click.argument("key")
        @verbosity_option(logger=logger)
        def get(key: str, **_: typing.Any) -> None:
            """Print a key from the user-defaults file.

            Retrieves the value of the requested KEY and displays it. The KEY
            may contain dots (``.``) to access values from subsections in the
            TOML_ document.
            """
            try:
                click.echo(config[key])
            except KeyError:
                raise click.ClickException(
                    f"Cannot find object named `{key}' at `{config.path}'",
                )

        @group_wrapper.command(
            name="set",
            no_args_is_help=True,
            context_settings=_COMMON_CONTEXT_SETTINGS,
        )
        @click.argument("key")
        @click.argument("value")
        @verbosity_option(logger=logger)
        def set_(key: str, value: str, **_: typing.Any) -> None:
            """Set the value for a key on the user-defaults file.

            If ``key`` contains dots (``.``), then this sets nested subsection
            variables on the configuration file.  Values are parsed and
            translated following the rules of TOML_.

            .. warning::

               This command will override the current configuration file and my
               erase any user comments added by hand.  To avoid this, simply
               edit your configuration file by hand.
            """
            try:
                tmp = tomli.loads(f"v = {value}")
                value = tmp["v"]
            except tomli.TOMLDecodeError:
                pass

            try:
                config[key] = value
                config.write()
            except KeyError:
                logger.error(
                    f"Cannot set object named `{key}' at `{config.path}'",
                    exc_info=True,
                )
                raise click.ClickException(
                    f"Cannot set object named `{key}' at `{config.path}'",
                )

        @group_wrapper.command(
            no_args_is_help=True, context_settings=_COMMON_CONTEXT_SETTINGS
        )
        @click.argument("key")
        @verbosity_option(logger=logger)
        def rm(key: str, **_: typing.Any) -> None:
            """Remove the given key from the configuration file.

            This command will remove the KEY from the configuration file.  If
            the input key corresponds to a section in the configuration file,
            then the whole configuration section will be removed.

            .. warning::

               This command will override the current configuration file and my
               erase any user comments added by hand.  To avoid this, simply
               edit your configuration file by hand.
            """
            try:
                del config[key]
                config.write()
            except KeyError:
                logger.error(
                    f"Cannot delete object named `{key}' at `{config.path}'",
                    exc_info=True,
                )
                raise click.ClickException(
                    f"Cannot delete object named `{key}' at `{config.path}'",
                )

        return group_wrapper

    return group_decorator


def config_group(
    logger: logging.Logger,
    entry_point_group: str,
) -> typing.Callable[..., typing.Any]:
    """Add a command group to list/describe/copy job configurations.

    This decorator adds a whole command group to a user predefined function
    which is part of the user's CLI.  The command group provdes an interface to
    list, fully describe or locally copy configuration files distributed with
    the package.  Commands accept both entry-point or module names to be
    provided as input.

    .. code-block:: python

       import logging
       from expose.click import config_group

       logger = logging.getLogger(__name__)
       ...


       @config_group(logger=logger, entry_point_group="mypackage.config")
       def config(**kwargs):
           '''Use this command to list/describe/copy config files.'''
           pass


    Then use it like this:

    .. code-block:: shell

       $ user-cli config --help
       usage: ...
    """

    def group_decorator(
        func: typing.Callable[..., typing.Any],
    ) -> typing.Callable[..., typing.Any]:
        @click.group(cls=AliasedGroup, context_settings=_COMMON_CONTEXT_SETTINGS)
        @verbosity_option(logger=logger)
        @functools.wraps(func)
        def group_wrapper(**kwargs):
            return func(**kwargs)

        @group_wrapper.command(
            name="list",
            context_settings=_COMMON_CONTEXT_SETTINGS,
        )
        @click.pass_context
        @verbosity_option(logger=logger)
        def list_(ctx, **_: typing.Any):
            """List installed configuration resources."""
            from importlib.metadata import entry_points  # type: ignore

            entry_points: dict[str, EntryPoint] = {  # type: ignore
                e.name: e for e in entry_points(group=entry_point_group)
            }

            # all modules with configuration resources
            modules: set[str] = {
                # note: k.module does not exist on Python < 3.9
                k.value.split(":")[0].rsplit(".", 1)[0]
                for k in entry_points.values()  # type: ignore
            }
            keep_modules: set[str] = set()
            for k in sorted(modules):
                if k not in keep_modules and not any(
                    k.startswith(to_keep) for to_keep in keep_modules
                ):
                    keep_modules.add(k)
            modules = keep_modules

            # sort data entries by originating module
            entry_points_by_module: dict[str, dict[str, EntryPoint]] = {}
            for k in modules:
                entry_points_by_module[k] = {}
                for name, ep in entry_points.items():  # type: ignore
                    # note: ep.module does not exist on Python < 3.9
                    module = ep.value.split(":", 1)[0]  # works on Python 3.8
                    if module.startswith(k):
                        entry_points_by_module[k][name] = ep

            for config_type in sorted(entry_points_by_module):
                # calculates the longest config name so we offset the printing
                longest_name_length = max(
                    len(k) for k in entry_points_by_module[config_type].keys()
                )

                # set-up printing options
                print_string = "    %%-%ds   %%s" % (longest_name_length,)
                # 79 - 4 spaces = 75 (see string above)
                description_leftover = 75 - longest_name_length

                click.echo(f"module: {config_type}")
                for name in sorted(entry_points_by_module[config_type]):
                    ep = entry_points[name]  # type: ignore

                    if (ctx.parent.params["verbose"] >= 1) or (
                        ctx.params["verbose"] >= 1
                    ):
                        try:
                            obj = ep.load()

                            if ":" in ep.value:  # it's an object
                                summary = (
                                    f"[{type(obj).__name__}] {pprint.pformat(obj)}"
                                )
                                summary = summary.replace("\n", " ")
                            else:  # it's a whole module
                                summary = "[module] "
                                doc = inspect.getdoc(obj)
                                if doc is not None:
                                    summary += doc.split("\n\n")[0]
                                    summary = summary.replace("\n", " ")
                                else:
                                    summary += "[undocumented]"

                        except Exception as ex:
                            summary = "(cannot be loaded; add another -v for details)"
                            if (ctx.parent.params["verbose"] >= 2) or (
                                ctx.params["verbose"] >= 2
                            ):
                                logger.exception(ex)

                    else:
                        summary = ""

                    summary = (
                        (summary[: (description_leftover - 3)] + "...")
                        if len(summary) > (description_leftover - 3)
                        else summary
                    )

                    click.echo(print_string % (name, summary))

        @group_wrapper.command(
            no_args_is_help=True, context_settings=_COMMON_CONTEXT_SETTINGS
        )
        @click.pass_context
        @click.argument(
            "name",
            required=True,
            nargs=-1,
        )
        @verbosity_option(logger=logger)
        def describe(ctx, name, **_: typing.Any):
            """Describe a specific configuration resource."""
            from importlib.metadata import entry_points  # type: ignore

            entry_points: dict[str, EntryPoint] = {  # type: ignore
                e.name: e for e in entry_points(group=entry_point_group)
            }

            for k in name:
                if k not in entry_points:  # type: ignore
                    logger.error(f"Cannot find configuration resource `{k}'")
                    continue
                ep = entry_points[k]  # type: ignore
                click.echo(f"Configuration: {ep.name}")
                click.echo(f"Python object: {ep.value}")
                click.echo("")
                mod = ep.load()

                if ":" not in ep.value:
                    if (ctx.parent.params["verbose"] >= 1) or (
                        ctx.params["verbose"] >= 1
                    ):
                        fname = inspect.getfile(mod)
                        click.echo("Contents:")
                        with pathlib.Path(fname).open() as f:
                            click.echo(f.read())
                    else:  # only output documentation, if module
                        doc = inspect.getdoc(mod)
                        if doc and doc.strip():
                            click.echo("Documentation:")
                            click.echo(doc)

        @group_wrapper.command(
            no_args_is_help=True, context_settings=_COMMON_CONTEXT_SETTINGS
        )
        @click.argument(
            "source",
            required=True,
            nargs=1,
        )
        @click.argument(
            "destination",
            required=True,
            nargs=1,
        )
        @verbosity_option(logger=logger)
        def copy(source, destination, **_: typing.Any):
            """Copy a specific configuration resource so it can be modified
            locally.
            """
            from importlib.metadata import entry_points  # type: ignore

            entry_points: dict[str, EntryPoint] = {  # type: ignore
                e.name: e for e in entry_points(group=entry_point_group)
            }

            if source not in entry_points:  # type: ignore
                logger.error(f"Cannot find configuration resource `{source}'")
                return 1
            ep = entry_points[source]  # type: ignore
            mod = ep.load()
            src_name = inspect.getfile(mod)
            logger.info(f"cp {src_name} -> {destination}")
            shutil.copyfile(src_name, destination)

            return None

        return group_wrapper

    return group_decorator


def log_parameters(logger_handle: logging.Logger, ignore: tuple[str] | None = None):
    """Log the click parameters with the logging module.

    Parameters
    ----------
    logger
        The :py:class:`logging.Logger` handle to write debug information into.
    ignore
        List of the parameters to ignore when logging. (Tuple)
    """
    ignore = ignore or tuple()
    ctx = click.get_current_context()
    # do not sort the ctx.params dict. The insertion order is kept in Python 3
    # and is useful (but not necessary so works on Python 2 too).
    for k, v in ctx.params.items():
        if k in ignore:
            continue
        logger_handle.debug("%s: %s", k, v)
