# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

import filecmp
import io

import pytest

from clapper.click import config_group
from clapper.config import load, mod_to_context
from clapper.logging import setup as logger_setup
from click.testing import CliRunner


def test_basic(datadir):
    c = load([datadir / "basic_config.py"])
    assert hasattr(c, "a") and c.a == 1
    assert hasattr(c, "b") and c.b == 3

    ctx = mod_to_context(c)
    assert ctx == {"a": 1, "b": 3}


def test_empty():
    c = load([])
    ctx = mod_to_context(c)
    assert len(ctx) == 0


def test_basic_with_context(datadir):
    c = load([datadir / "basic_config.py"], {"d": 35, "a": 0})
    assert hasattr(c, "a") and c.a == 1
    assert hasattr(c, "b") and c.b == 3
    assert hasattr(c, "d") and c.d == 35


def test_chain_loading(datadir):
    file1 = datadir / "basic_config.py"
    file2 = datadir / "second_config.py"
    c = load([file1, file2])
    assert hasattr(c, "a") and c.a == 1
    assert hasattr(c, "b") and c.b == 6


def test_config_with_module():
    c = load(
        [
            "tests.data.basic_config",
            "tests.data.second_config",
            "tests.data.complex",
        ]
    )
    assert hasattr(c, "a") and c.a == 1
    assert hasattr(c, "b") and c.b == 6
    assert hasattr(c, "cplx") and isinstance(c.cplx, dict)


def test_config_with_entry_point():
    c = load(["first", "second", "complex"], entry_point_group="clapper.test.config")
    assert hasattr(c, "a") and c.a == 1
    assert hasattr(c, "b") and c.b == 6
    assert hasattr(c, "cplx") and isinstance(c.cplx, dict)


def test_config_with_entry_point_file_missing():
    with pytest.raises(ValueError):
        load(["error-config"], entry_point_group="clapper.test.config")


def test_config_with_mixture(datadir):
    c = load(
        [
            datadir / "basic_config.py",
            "tests.data.second_config",
            "complex",
        ],
        entry_point_group="clapper.test.config",
    )
    assert hasattr(c, "a") and c.a == 1
    assert hasattr(c, "b") and c.b == 6
    assert hasattr(c, "cplx") and isinstance(c.cplx, dict)


def test_config_not_found(datadir):
    with pytest.raises(ValueError):
        load([datadir / "basic_config.pz"])


def test_config_load_attribute():
    a = load(["tests.data.basic_config"], attribute_name="a")
    assert a == 1


def test_config_load_no_attribute():
    with pytest.raises(ImportError):
        _ = load(["tests.data.basic_config"], attribute_name="wrong")


@pytest.fixture
def cli_messages():
    messages = io.StringIO()
    logger = logger_setup(
        "test-click-loading",
        format="[%(levelname)s] %(message)s",
        low_level_stream=messages,
        high_level_stream=messages,
    )

    @config_group(logger=logger, entry_point_group="clapper.test.config")
    def cli(**_):
        """This is the documentation provided by the user."""
        pass

    return (cli, messages)


def test_config_click_config_list(cli_messages):
    cli = cli_messages[0]
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert result.output.startswith("module: tests.data")
    assert "(cannot be loaded; add another -v for details)" not in result.output


def test_config_click_config_list_v(cli_messages):
    cli = cli_messages[0]
    runner = CliRunner()
    result = runner.invoke(cli, ["list", "-v"])
    assert result.exit_code == 0
    assert result.output.startswith("module: tests.data")
    assert "(cannot be loaded; add another -v for details)" in result.output
    assert "[module] Example configuration module" in result.output


def test_config_click_config_list_vv(cli_messages):
    cli, messages = cli_messages
    runner = CliRunner()
    result = runner.invoke(cli, ["list", "-vv"])
    assert result.exit_code == 0
    assert result.output.startswith("module: tests.data")
    assert "(cannot be loaded; add another -v for details)" in result.output
    assert "[module] Example configuration module" in result.output
    assert "NameError" in messages.getvalue()


def test_config_click_config_describe(cli_messages):
    cli = cli_messages[0]
    runner = CliRunner()
    result = runner.invoke(cli, ["describe", "first"])
    assert result.exit_code == 0
    assert result.output.startswith("Configuration: first")
    assert "Example configuration module" in result.output
    assert "a = 1" not in result.output
    assert "b = a + 2" not in result.output


def test_config_click_config_describe_v(cli_messages):
    cli = cli_messages[0]
    runner = CliRunner()
    result = runner.invoke(cli, ["describe", "first", "-v"])
    assert result.exit_code == 0
    assert result.output.startswith("Configuration: first")
    assert "a = 1" in result.output
    assert "b = a + 2" in result.output


def test_config_click_describe_error(cli_messages):
    cli, messages = cli_messages
    runner = CliRunner()
    result = runner.invoke(cli, ["describe", "not-found"])
    assert result.exit_code == 0
    assert "Cannot find configuration resource `not-found'" in messages.getvalue()


def test_config_click_copy(cli_messages, datadir, tmp_path):
    cli = cli_messages[0]
    runner = CliRunner()
    dest = tmp_path / "file.py"
    result = runner.invoke(cli, ["copy", "first", str(dest)])
    assert result.exit_code == 0
    assert filecmp.cmp(datadir / "basic_config.py", dest)


def test_config_click_copy_error(cli_messages, datadir, tmp_path):
    cli, messages = cli_messages
    runner = CliRunner()
    dest = tmp_path / "file.py"
    result = runner.invoke(cli, ["copy", "firstx", str(dest)])
    assert result.exit_code == 0
    assert "[ERROR] Cannot find configuration resource `firstx'" in messages.getvalue()
