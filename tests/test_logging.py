# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

import io
import logging

import click
import pytest

from click.testing import CliRunner

import clapper.logging

from clapper.click import ConfigCommand, ResourceOption, verbosity_option


def test_logger_setup():
    lo = io.StringIO()
    hi = io.StringIO()

    logger = clapper.logging.setup(
        "awesome.logger",
        format="%(message)s",
        low_level_stream=lo,
        high_level_stream=hi,
    )
    logger.setLevel(logging.DEBUG)

    logger.debug("debug message")
    logger.info("info message")

    logger.warning("warning message")
    logger.error("error message")

    assert lo.getvalue() == "debug message\ninfo message\n"
    assert hi.getvalue() == "warning message\nerror message\n"


def test_logger_setup_formatter():
    log_output = io.StringIO()

    custom_formatter = logging.Formatter(fmt="custom {message:s}", style="{")

    logger = clapper.logging.setup(
        "awesome.logger",
        low_level_stream=log_output,
        high_level_stream=log_output,
        formatter=custom_formatter,
    )
    logger.setLevel(logging.DEBUG)

    logger.debug("debug message")
    logger.info("info message")
    logger.warning("warning message")
    logger.error("error message")

    assert log_output.getvalue() == (
        "custom debug message\n"
        "custom info message\n"
        "custom warning message\n"
        "custom error message\n"
    )


def test_logger_click_no_v():
    lo = io.StringIO()
    hi = io.StringIO()

    logger = clapper.logging.setup(
        "awesome.logger",
        format="%(message)s",
        low_level_stream=lo,
        high_level_stream=hi,
    )

    @click.command()
    @verbosity_option(logger=logger)
    def cli(**_):
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")

    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0

    assert lo.getvalue() == ""

    assert hi.getvalue() == "error message\n"


def test_logger_click_v():
    lo = io.StringIO()
    hi = io.StringIO()

    logger = clapper.logging.setup(
        "awesome.logger",
        format="%(message)s",
        low_level_stream=lo,
        high_level_stream=hi,
    )

    @click.command()
    @verbosity_option(logger=logger)
    def cli(**_):
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")

    runner = CliRunner()
    result = runner.invoke(cli, ["-v"])
    assert result.exit_code == 0

    assert lo.getvalue() == ""
    assert hi.getvalue() == "warning message\nerror message\n"


def test_logger_click_vv():
    lo = io.StringIO()
    hi = io.StringIO()

    logger = clapper.logging.setup(
        "awesome.logger",
        format="%(message)s",
        low_level_stream=lo,
        high_level_stream=hi,
    )

    @click.command()
    @verbosity_option(logger=logger)
    def cli(**_):
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")

    runner = CliRunner()
    result = runner.invoke(cli, ["-vv"])
    assert result.exit_code == 0

    assert lo.getvalue() == "info message\n"
    assert hi.getvalue() == "warning message\nerror message\n"


def test_logger_click_vvv():
    lo = io.StringIO()
    hi = io.StringIO()

    logger = clapper.logging.setup(
        "awesome.logger",
        format="%(message)s",
        low_level_stream=lo,
        high_level_stream=hi,
    )

    @click.command()
    @verbosity_option(logger=logger)
    def cli(**_):
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")

    runner = CliRunner()
    result = runner.invoke(cli, ["-vvv"])
    assert result.exit_code == 0

    assert "debug message\ninfo message\n" in lo.getvalue()
    assert hi.getvalue() == "warning message\nerror message\n"


def test_logger_click_3x_verbose():
    lo = io.StringIO()
    hi = io.StringIO()

    logger = clapper.logging.setup(
        "awesome.logger",
        format="%(message)s",
        low_level_stream=lo,
        high_level_stream=hi,
    )

    @click.command()
    @verbosity_option(logger=logger)
    def cli(**_):
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")

    runner = CliRunner()
    result = runner.invoke(cli, 3 * ["--verbose"])
    assert result.exit_code == 0

    assert "debug message\ninfo message\n" in lo.getvalue()
    assert hi.getvalue() == "warning message\nerror message\n"


def test_logger_click_3x_verb():
    lo = io.StringIO()
    hi = io.StringIO()

    logger = clapper.logging.setup(
        "awesome.logger",
        format="%(message)s",
        low_level_stream=lo,
        high_level_stream=hi,
    )

    @click.command()
    @verbosity_option(logger=logger, name="verb")
    def cli(**_):
        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")

    runner = CliRunner()
    result = runner.invoke(cli, 3 * ["--verb"])
    assert result.exit_code == 0

    assert "debug message\ninfo message\n" in lo.getvalue()
    assert hi.getvalue() == "warning message\nerror message\n"


# Testing the logger is also set correctly during the loading of config files.


@pytest.fixture
def cli_config():
    messages = io.StringIO()
    logger = clapper.logging.setup(
        "clapper_test",
        format="[%(levelname)s] %(message)s",
        low_level_stream=messages,
        high_level_stream=messages,
    )
    logger.setLevel("ERROR")  # Enforce a default level

    @click.command(entry_point_group="clapper.test.config", cls=ConfigCommand)
    @click.option("--cmp", entry_point_group="clapper.test.config", cls=ResourceOption)
    @verbosity_option(logger, expose_value=False)
    def cli(**_):
        """This is the documentation provided by the user."""
        logger.debug("App Debug level message")
        logger.info("App Info level message")
        logger.warning("App Warning level message")
        logger.error("App Error level message")

    return (cli, messages)


# Loading configs using ResourceOption


def test_logger_click_option_config_q(cli_config):
    cli, log_output = cli_config
    runner = CliRunner()
    result = runner.invoke(cli, ["--cmp", "complex-var"])
    expected = "[ERROR] Error level message\n[ERROR] App Error level message\n"
    assert result.exit_code == 0, result.output
    assert log_output.getvalue() == expected


def test_logger_click_option_config_v(cli_config):
    cli, log_output = cli_config
    runner = CliRunner()
    result = runner.invoke(cli, ["--cmp", "complex-var", "-v"])
    expected = (
        "[WARNING] Warning level message\n"
        "[ERROR] Error level message\n"
        "[WARNING] App Warning level message\n"
        "[ERROR] App Error level message\n"
    )
    assert result.exit_code == 0, result.output
    assert log_output.getvalue() == expected


def test_logger_click_option_config_vv(cli_config):
    cli, log_output = cli_config
    runner = CliRunner()
    result = runner.invoke(cli, ["--cmp", "complex-var", "-vv"])
    expected = (
        "[INFO] Info level message\n"
        "[WARNING] Warning level message\n"
        "[ERROR] Error level message\n"
        "[INFO] App Info level message\n"
        "[WARNING] App Warning level message\n"
        "[ERROR] App Error level message\n"
    )
    assert result.exit_code == 0, result.output
    assert log_output.getvalue() == expected


def test_logger_click_option_config_vvv(cli_config):
    cli, log_output = cli_config
    runner = CliRunner()
    result = runner.invoke(cli, ["--cmp", "complex-var", "-vvv"])
    expected = (
        "[DEBUG] Debug level message\n"
        "[INFO] Info level message\n"
        "[WARNING] Warning level message\n"
        "[ERROR] Error level message\n"
        "[DEBUG] App Debug level message\n"
        "[INFO] App Info level message\n"
        "[WARNING] App Warning level message\n"
        "[ERROR] App Error level message\n"
    )
    assert result.exit_code == 0, result.output
    assert log_output.getvalue().endswith(expected)


# Loading configs using ConfigCommand


def test_logger_click_command_config_q(cli_config):
    cli, log_output = cli_config
    runner = CliRunner()
    result = runner.invoke(cli, ["complex"])
    expected = "[ERROR] Error level message\n[ERROR] App Error level message\n"
    assert result.exit_code == 0, result.output
    assert log_output.getvalue() == expected


def test_logger_click_command_config_v(cli_config):
    cli, log_output = cli_config
    runner = CliRunner()
    result = runner.invoke(cli, ["complex", "-v"])
    expected = (
        "[WARNING] Warning level message\n"
        "[ERROR] Error level message\n"
        "[WARNING] App Warning level message\n"
        "[ERROR] App Error level message\n"
    )
    assert result.exit_code == 0, result.output
    assert log_output.getvalue() == expected


def test_logger_click_command_config_vv(cli_config):
    cli, log_output = cli_config
    runner = CliRunner()
    result = runner.invoke(cli, ["complex", "-vv"])
    expected = (
        "[INFO] Info level message\n"
        "[WARNING] Warning level message\n"
        "[ERROR] Error level message\n"
        "[INFO] App Info level message\n"
        "[WARNING] App Warning level message\n"
        "[ERROR] App Error level message\n"
    )
    assert result.exit_code == 0, result.output
    assert log_output.getvalue() == expected


def test_logger_click_command_config_vvv(cli_config):
    cli, log_output = cli_config
    runner = CliRunner()
    result = runner.invoke(cli, ["complex", "-vvv"])
    expected = (
        "[DEBUG] Debug level message\n"
        "[INFO] Info level message\n"
        "[WARNING] Warning level message\n"
        "[ERROR] Error level message\n"
        "[DEBUG] App Debug level message\n"
        "[INFO] App Info level message\n"
        "[WARNING] App Warning level message\n"
        "[ERROR] App Error level message\n"
    )
    assert result.exit_code == 0, result.output
    assert log_output.getvalue().endswith(expected)


# Verbosity option set in config file is ignored (not a ResourceOption)


def test_logger_click_command_config_q_plus_config(cli_config):
    cli, log_output = cli_config
    runner = CliRunner()
    result = runner.invoke(cli, ["verbose-config", "complex"])
    expected = "[ERROR] Error level message\n[ERROR] App Error level message\n"
    assert result.exit_code == 0, result.output
    assert log_output.getvalue() == expected


def test_logger_click_command_config_v_plus_config(cli_config):
    cli, log_output = cli_config
    runner = CliRunner()
    result = runner.invoke(cli, ["verbose-config", "complex", "-v"])
    expected = (
        "[WARNING] Warning level message\n"
        "[ERROR] Error level message\n"
        "[WARNING] App Warning level message\n"
        "[ERROR] App Error level message\n"
    )
    assert result.exit_code == 0, result.output
    assert log_output.getvalue() == expected


# Testing verbosity option as config option (legacy mode)
# The logging level will not be correct in the config files, but can be set as a config.


@pytest.fixture
def cli_verbosity_config():
    messages = io.StringIO()
    logger = clapper.logging.setup(
        "clapper_test",
        format="[%(levelname)s] %(message)s",
        low_level_stream=messages,
        high_level_stream=messages,
    )
    logger.setLevel("ERROR")  # Enforce a default level

    @click.command(entry_point_group="clapper.test.config", cls=ConfigCommand)
    @click.option("--cmp", entry_point_group="clapper.test.config", cls=ResourceOption)
    @verbosity_option(logger, expose_value=False, cls=ResourceOption)
    def cli(**_):
        """This is the documentation provided by the user."""
        logger.debug("App Debug level message")
        logger.info("App Info level message")
        logger.warning("App Warning level message")
        logger.error("App Error level message")

    return (cli, messages)


def test_logger_click_option_config_verbose_as_config_q(cli_verbosity_config):
    cli, log_output = cli_verbosity_config
    runner = CliRunner()
    result = runner.invoke(cli, ["--cmp", "complex-var"])
    expected = "[ERROR] Error level message\n[ERROR] App Error level message\n"
    assert result.exit_code == 0, result.output
    assert log_output.getvalue() == expected


def test_logger_click_option_config_verbose_as_config_v(cli_verbosity_config):
    cli, log_output = cli_verbosity_config
    runner = CliRunner()
    result = runner.invoke(cli, ["--cmp", "complex-var", "-v"])
    expected = (
        "[ERROR] Error level message\n"
        "[WARNING] App Warning level message\n"
        "[ERROR] App Error level message\n"
    )
    assert result.exit_code == 0, result.output
    assert log_output.getvalue() == expected


def test_logger_click_option_config_verbose_as_config_vv(cli_verbosity_config):
    cli, log_output = cli_verbosity_config
    runner = CliRunner()
    result = runner.invoke(cli, ["--cmp", "complex-var", "-vv"])
    expected = (
        "[ERROR] Error level message\n"
        "[INFO] App Info level message\n"
        "[WARNING] App Warning level message\n"
        "[ERROR] App Error level message\n"
    )
    assert result.exit_code == 0, result.output
    assert log_output.getvalue() == expected


def test_logger_click_option_config_verbose_as_config_vvv(cli_verbosity_config):
    cli, log_output = cli_verbosity_config
    runner = CliRunner()
    result = runner.invoke(cli, ["--cmp", "complex-var", "-vvv"])
    expected_start = "[ERROR] Error level message\n"
    expected_end = (
        "[DEBUG] App Debug level message\n"
        "[INFO] App Info level message\n"
        "[WARNING] App Warning level message\n"
        "[ERROR] App Error level message\n"
    )
    assert result.exit_code == 0, result.output
    output = log_output.getvalue()
    assert output.startswith(expected_start)
    assert output.endswith(expected_end)


# Verbosity option set in config file is handled (verbosity_option is a ResourceOption)


def test_logger_option_config_verbose_as_config_q_plus_config(cli_verbosity_config):
    cli, log_output = cli_verbosity_config
    runner = CliRunner()
    result = runner.invoke(cli, ["verbose-config", "complex"])
    expected = (
        "[ERROR] Error level message\n"
        "[INFO] App Info level message\n"
        "[WARNING] App Warning level message\n"
        "[ERROR] App Error level message\n"
    )
    assert result.exit_code == 0, result.output
    assert log_output.getvalue() == expected


# specifying the verbosity option in the CLI overrides the option


def test_logger_option_config_verbose_as_config_v_plus_config(cli_verbosity_config):
    cli, log_output = cli_verbosity_config
    runner = CliRunner()
    result = runner.invoke(cli, ["verbose-config", "complex", "-v"])
    expected = (
        "[ERROR] Error level message\n"
        "[WARNING] App Warning level message\n"
        "[ERROR] App Error level message\n"
    )
    assert result.exit_code == 0, result.output
    assert log_output.getvalue() == expected
