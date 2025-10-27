# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Amir Mohammadi  <amir.mohammadi@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

import difflib
import logging

import click

from click.testing import CliRunner

from clapper.click import (
    AliasedGroup,
    ConfigCommand,
    ResourceOption,
    log_parameters,
    verbosity_option,
)


def test_prefix_aliasing():
    @click.group(cls=AliasedGroup)
    def cli():
        pass

    @cli.command()
    def test():
        click.echo("OK")

    @cli.command(name="test-aaa")
    def test_aaa():
        click.echo("AAA")

    runner = CliRunner()
    result = runner.invoke(cli, ["te"], catch_exceptions=False)
    assert result.exit_code != 0

    result = runner.invoke(cli, ["test"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "OK" in result.output, (result.exit_code, result.output)

    result = runner.invoke(cli, ["test-a"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "AAA" in result.output, (result.exit_code, result.output)

    result = runner.invoke(cli, ["test-aaaa"], catch_exceptions=False)
    assert result.exit_code != 0


def test_commands_with_config_1():
    # random test
    @click.command(cls=ConfigCommand, entry_point_group="clapper.test.config")
    def cli(**_):
        pass

    runner = CliRunner()
    result = runner.invoke(cli, ["first"])
    assert result.exit_code == 0


def test_commands_with_config_2():
    # test option with valid default value
    @click.command(cls=ConfigCommand, entry_point_group="clapper.test.config")
    @click.option("-a", type=click.INT, cls=ResourceOption)
    def cli(a, **_):
        assert isinstance(a, int), (type(a), a)
        click.echo(f"{a}")

    runner = CliRunner()

    result = runner.invoke(cli, ["first"])
    assert result.exit_code == 0
    assert result.output.strip() == "1"

    result = runner.invoke(cli, ["-a", "2"])
    assert result.exit_code == 0
    assert result.output.strip() == "2"

    result = runner.invoke(cli, ["-a", "3", "first"])
    assert result.exit_code == 0
    assert result.output.strip() == "3"

    result = runner.invoke(cli, ["first", "-a", "3"])
    assert result.exit_code == 0
    assert result.output.strip() == "3"


def test_commands_with_config_3():
    # test required options
    @click.command(cls=ConfigCommand, entry_point_group="clapper.test.config")
    @click.option("-a", cls=ResourceOption, required=True)
    def cli(a, **_):
        click.echo(f"{a}")

    runner = CliRunner()

    result = runner.invoke(cli, [])
    assert result.exit_code == 2

    result = runner.invoke(cli, ["first"])
    assert result.exit_code == 0
    assert result.output.strip() == "1"

    result = runner.invoke(cli, ["-a", "2"])
    assert result.exit_code == 0
    assert result.output.strip() == "2"

    result = runner.invoke(cli, ["-a", "3", "first"])
    assert result.exit_code == 0
    assert result.output.strip() == "3"

    result = runner.invoke(cli, ["first", "-a", "3"])
    assert result.exit_code == 0
    assert result.output.strip() == "3"


def test_commands_with_config_4():
    # test required options
    @click.command(cls=ConfigCommand, entry_point_group="clapper.test.config")
    @click.option("-a/-A", cls=ResourceOption)
    def cli(a, **_):
        click.echo(f"{a}")

    runner = CliRunner()

    result = runner.invoke(cli, [])
    assert result.exit_code == 0


def test_commands_with_config_5():
    # test required options
    @click.command(cls=ConfigCommand, entry_point_group="clapper.test.config")
    @click.option("-a", default=42, required=True, cls=ResourceOption)
    def cli(a, **_):
        click.echo(f"{a}")

    runner = CliRunner()

    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert result.output.strip() == "42"


def test_commands_with_config_6():
    # test unprocessed options
    @click.command(cls=ConfigCommand, entry_point_group="clapper.test.config")
    @click.option("-a", type=click.UNPROCESSED, default=[], cls=ResourceOption)
    def cli(a, **_):
        click.echo(f"{a}")

    runner = CliRunner()

    result = runner.invoke(cli, [])
    assert result.exit_code == 0
    assert result.output.strip() == "[]"


def _assert_config_dump(output, ref, ref_date):
    with output.open("rt") as f, ref.open() as f2:
        diff = difflib.ndiff(f.readlines(), f2.readlines())
        important_diffs = [k for k in diff if k.startswith(("+", "-"))]

        # check and remove differences on the generation date
        if (
            len(important_diffs) >= 2
            and important_diffs[0].startswith(
                '- """Configuration file automatically generated at '
            )
            and important_diffs[1].startswith(
                '+ """Configuration file automatically generated at '
            )
        ):
            important_diffs = important_diffs[2:]

        important_diffs = "".join(important_diffs)

        assert len(important_diffs) == 0, (
            f"Differences between "
            f"{str(output)} and {str(ref)} files observed: "
            f"{important_diffs}"
        )


def test_config_dump(tmp_path, datadir):
    @click.command(cls=ConfigCommand, epilog="Examples!")
    @click.option(
        "-t",
        "--test",
        required=True,
        default="/my/path/test.txt",
        help="Path leading to test blablabla",
        cls=ResourceOption,
    )
    @verbosity_option(logging.getLogger(__name__), cls=ResourceOption)
    def test(**_):
        """Test command."""
        pass

    runner = CliRunner()
    output = tmp_path / "test_dump.py"
    result = runner.invoke(
        test,
        ["-H", str(output)],
        catch_exceptions=False,
    )
    ref = datadir / "test_dump_config.py"
    assert result.exit_code == 0
    _assert_config_dump(output, ref, "10/09/2022")


def test_config_dump2(tmp_path, datadir):
    @click.command(cls=ConfigCommand, entry_point_group="clapper.test.config")
    @click.option(
        "--database",
        "-d",
        required=True,
        cls=ResourceOption,
        entry_point_group="clapper.test.config",
        help="bla bla bla",
    )
    @click.option(
        "--annotator",
        "-a",
        required=True,
        cls=ResourceOption,
        entry_point_group="clapper.test.config",
        help="bli bli bli",
    )
    @click.option(
        "--output-dir",
        "-o",
        required=True,
        cls=ResourceOption,
        help="blo blo blo",
    )
    @click.option(
        "--force", "-f", is_flag=True, cls=ResourceOption, help="lalalalalala"
    )
    @click.option(
        "--array",
        type=click.INT,
        default=1,
        cls=ResourceOption,
        help="lililili",
    )
    @click.option(
        "--database-directories-file",
        cls=ResourceOption,
        default="~/databases.txt",
        help="lklklklk",
    )
    @verbosity_option(logging.getLogger(__name__), cls=ResourceOption)
    def test(**_):
        """Blablabla bli blo.

        Parameters
        ----------
        xxx : :any:`list`
            blabla blablo
        yyy : callable
            bli bla blo bla bla bla

        [CONFIG]...           BLA BLA BLA BLA
        """
        pass

    runner = CliRunner()
    output = tmp_path / "test_dump.py"
    result = runner.invoke(test, ["test", "-H", str(output)], catch_exceptions=False)

    ref = datadir / "test_dump_config2.py"
    assert result.exit_code == 0
    _assert_config_dump(output, ref, "10/09/2022")


def test_config_command_with_callback_options():
    @click.command(cls=ConfigCommand, entry_point_group="clapper.test.config")
    @verbosity_option(logging.getLogger(__name__), envvar="VERBOSE", cls=ResourceOption)
    @click.pass_context
    def cli(ctx, **_):
        verbose = ctx.meta["verbose"]
        assert verbose == 2

    runner = CliRunner()
    result = runner.invoke(cli, ["verbose-config"])
    assert result.exit_code == 0

    runner = CliRunner(env=dict(VERBOSE="1"))
    result = runner.invoke(cli, ["verbose-config"])
    assert result.exit_code == 0

    runner = CliRunner(env=dict(VERBOSE="2"))
    result = runner.invoke(cli)
    assert result.exit_code == 0


def test_resource_option():
    # test usage without ConfigCommand and with entry_point_group
    @click.command()
    @click.option(
        "-a", "--a", cls=ResourceOption, entry_point_group="clapper.test.config"
    )
    def cli1(a):
        assert a == 1

    runner = CliRunner()
    result = runner.invoke(cli1, ["-a", "tests.data.basic_config"])
    assert result.exit_code == 0

    # test usage without ConfigCommand and without entry_point_group
    # should raise a TypeError
    @click.command()
    @click.option("-a", "--a", cls=ResourceOption)
    def cli2(**_):
        raise ValueError("Should not have reached here!")

    runner = CliRunner()
    result = runner.invoke(cli2, ["-a", "1"], catch_exceptions=True)
    assert result.exit_code != 0
    assert isinstance(result.exception, TypeError)
    assert str(result.exception).startswith("The ResourceOption class is not")

    # test ResourceOption with string_exceptions
    @click.command()
    @click.option(
        "-a",
        "--a",
        cls=ResourceOption,
        string_exceptions=("tests.data.basic_config"),
        entry_point_group="clapper.test.config",
    )
    def cli3(a):
        assert a == "tests.data.basic_config"

    runner = CliRunner()
    result = runner.invoke(cli3, ["-a", "tests.data.basic_config"])
    assert result.exit_code == 0


def test_log_parameter():
    # Fake logger that checks if log_parameters accesses it
    class DummyLogger:
        def __init__(self):
            self.accessed = False

        def debug(self, s, k, v):
            self.accessed = True

    @click.command()
    @click.option(
        "-a",
        "--a",
    )
    def cli_log(a):
        dummy_logger = DummyLogger()
        log_parameters(dummy_logger)
        assert dummy_logger.accessed

    runner = CliRunner()
    result = runner.invoke(cli_log, ["-a", "aparam"])
    assert result.exit_code == 0


def test_log_parameter_with_ignore():
    # Fake logger that ensures that the parameter 'a' is ignored
    class DummyLogger:
        def debug(self, s, k, v):
            assert "a" not in k

    @click.command()
    @click.option("-a", "--a")
    @click.option(
        "-b",
        "--b",
    )
    def cli_log(a, b):
        log_parameters(DummyLogger(), ignore=("a"))

    runner = CliRunner()
    result = runner.invoke(cli_log, ["-a", "aparam", "-b", "bparam"])
    assert result.exit_code == 0
