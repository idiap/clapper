# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

import io
import logging

import clapper.logging
import click

from clapper.click import verbosity_option
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
