# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

import io
import logging

import clapper.logging
import click
import pytest

from clapper.click import ConfigCommand, ResourceOption, verbosity_option
from click.testing import CliRunner


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
        pass

    return (cli, messages)


# Loading configs using ResourceOption


def test_logger_click_option_config_q(cli_config):
    cli, log_output = cli_config
    runner = CliRunner()
    result = runner.invoke(cli, ["--cmp", "complex-var"])
    expected = "[ERROR] Error level message\n"
    assert result.exit_code == 0, result.output
    assert log_output.getvalue() == expected


def test_logger_click_option_config_v(cli_config):
    cli, log_output = cli_config
    runner = CliRunner()
    result = runner.invoke(cli, ["--cmp", "complex-var", "-v"])
    expected = "[WARNING] Warning level message\n" "[ERROR] Error level message\n"
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
    )
    assert result.exit_code == 0, result.output
    assert log_output.getvalue().endswith(expected)


# Loading configs using ConfigCommand
def test_logger_click_command_config_q(cli_config):
    cli, log_output = cli_config
    runner = CliRunner()
    result = runner.invoke(cli, ["complex"])
    expected = "[ERROR] Error level message\n"
    assert result.exit_code == 0, result.output
    assert log_output.getvalue() == expected


def test_logger_click_command_config_v(cli_config):
    cli, log_output = cli_config
    runner = CliRunner()
    result = runner.invoke(cli, ["complex", "-v"])
    expected = "[WARNING] Warning level message\n" "[ERROR] Error level message\n"
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
    )
    assert result.exit_code == 0, result.output
    assert log_output.getvalue().endswith(expected)
