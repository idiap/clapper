# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
# SPDX-FileContributor: Amir Mohammadi  <amir.mohammadi@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

import filecmp
import logging
import os
import pathlib
import shutil

import pytest

from click.testing import CliRunner

from clapper.click import user_defaults_group
from clapper.rc import UserDefaults


def _check_userdefaults_ex1_contents(rc):
    # checks that it matches the contents of that file

    assert rc["string"] == "this is a string"
    assert rc["integer"] == 42
    assert rc["float"] == 3.14
    assert rc["boolean"] is True
    assert rc["array"] == ["abc", 2, 2.78]
    assert rc["bar"]["boolean"] is False
    assert rc["bar.boolean"] is False


def test_rc_basic_loading(datadir):
    # tests if we can simply read an RC file
    rc = UserDefaults(datadir / "userdefaults_ex1.cfg")
    _check_userdefaults_ex1_contents(rc)

    with pytest.raises(KeyError):
        assert rc["float.error"] == 3.14


def test_rc_loading_from_xdg_config_home(datadir):
    # tests if we can simply read an RC file from the XDG_CONFIG_HOME
    _environ = dict(os.environ)  # or os.environ.copy()
    try:
        os.environ["XDG_CONFIG_HOME"] = str(datadir)
        rc = UserDefaults("userdefaults_ex1.cfg")
        _check_userdefaults_ex1_contents(rc)

        with pytest.raises(KeyError):
            assert rc["float.error"] == 3.14
    finally:
        os.environ.clear()
        os.environ.update(_environ)


def test_rc_init_empty(tmp_path):
    rc = UserDefaults(tmp_path / "new-rc")
    assert not rc


def _check_tree(d, sect, var, val):
    assert sect in d
    assert var in d[sect]
    assert d[sect][var] == val


def test_rc_write(tmp_path):
    rc = UserDefaults(tmp_path / "new-rc")
    assert not rc

    rc["section1.an_int"] = 15
    rc["section1.a_bool"] = True
    rc["section1.a_float"] = 3.1415
    rc["section1.baz"] = "fun"
    rc["section1.bar"] = "Python"

    # checks contents before writing
    assert rc["section1"]["an_int"] == 15
    assert rc["section1"]["a_bool"] is True
    assert rc["section1"]["a_float"] == 3.1415
    assert rc["section1"]["baz"] == "fun"
    assert rc["section1"]["bar"] == "Python"

    # checks contents before writing - different way
    assert rc["section1.an_int"] == 15
    assert rc["section1.a_bool"] is True
    assert rc["section1.a_float"] == 3.1415
    assert rc["section1.baz"] == "fun"
    assert rc["section1.bar"] == "Python"

    rc.write()

    assert (tmp_path / "new-rc").exists()

    rc2 = UserDefaults(tmp_path / "new-rc")
    assert len(rc2) == 1
    assert rc["section1"]["an_int"] == 15
    assert rc["section1.an_int"] == 15
    assert rc["section1"]["a_bool"] is True
    assert rc["section1.a_bool"] is True
    assert rc["section1"]["a_float"] == 3.1415
    assert rc["section1.a_float"] == 3.1415
    assert rc["section1"]["baz"] == "fun"
    assert rc["section1.baz"] == "fun"
    assert rc["section1"]["bar"] == "Python"
    assert rc["section1.bar"] == "Python"


def test_rc_delete(tmp_path):
    rc = UserDefaults(tmp_path / "new-rc")
    assert not rc

    rc["an_int"] = 15
    rc["a_bool"] = True
    rc["a_float"] = 3.1415
    rc["section1.baz"] = "fun"
    rc["section1.bar"] = "Python"

    assert rc["an_int"] == 15
    assert rc["a_bool"] is True
    assert rc["a_float"] == 3.1415
    assert rc["section1.baz"] == "fun"
    assert rc["section1.bar"] == "Python"

    # delete something that exists
    del rc["an_int"]
    assert "an_int" not in rc

    with pytest.raises(KeyError):
        del rc["error"]

    with pytest.raises(KeyError):
        del rc["section1.baz.error"]

    with pytest.raises(KeyError):
        del rc["section2.baz.error"]


def test_rc_backup_on_write(tmp_path):
    rc = UserDefaults(tmp_path / "new-rc")
    assert not rc

    rc["section1.an_int"] = 15
    rc.write()
    assert (tmp_path / "new-rc").exists()

    rc.write()
    assert (tmp_path / "new-rc").exists()
    assert (tmp_path / "new-rc~").exists()

    assert filecmp.cmp(tmp_path / "new-rc", tmp_path / "new-rc~")


def test_rc_clear():
    rc = UserDefaults("does-not-exist")
    assert not rc

    rc["section2.another_int"] = 42
    rc.clear()

    assert not rc
    assert not pathlib.Path("does-not-exist").exists()


def test_rc_reload(tmp_path):
    rc = UserDefaults(tmp_path / "new-rc")
    rc["section1.foo"] = "bar"
    rc["section1.an_int"] = 15
    rc.write()
    assert len(rc) == 1

    rc2 = UserDefaults(tmp_path / "new-rc")  # change that and reload first
    rc2["section2.another_int"] = 42
    rc2.write()

    # now reload and see what happened
    rc.read()
    assert len(rc) == 2
    assert rc["section1"]["foo"] == "bar"
    assert rc["section1"]["an_int"] == 15
    assert rc2["section2"]["another_int"] == 42


def test_rc_str(tmp_path):
    rc = UserDefaults(tmp_path / "new-rc")
    rc["foo"] = "bar"
    rc["section1.an_int"] = 15
    rc.write()

    assert (tmp_path / "new-rc").open().read() == str(rc)


def test_rc_json_legacy(datadir, tmp_path):
    shutil.copy(datadir / "oldjson.cfg", tmp_path)
    rc = UserDefaults(tmp_path / "oldjson.cfg")

    assert rc["string"] == "this is a string"
    assert rc["integer"] == 42
    assert rc["bar"] == {"boolean": False, "int": 15}
    assert rc["baz.foo"] == {"int": 35, "float": 2.78}
    assert rc["baz"]["foo"]["int"] == 35


def test_rc_click_loading(datadir):
    # tests if we can simply read an RC file
    rc = UserDefaults(datadir / "userdefaults_ex1.cfg")
    logger = logging.getLogger("test-click-loading")

    @user_defaults_group(logger=logger, config=rc)
    def cli(**_):
        """This is the documentation provided by the user."""
        pass

    runner = CliRunner()

    # test "show"
    result = runner.invoke(cli, ["show"])
    assert result.exit_code == 0
    assert result.output.strip() == str(rc).strip()

    # test "get"
    result = runner.invoke(cli, ["get", "string"])
    assert result.exit_code == 0
    assert result.output.strip() == "this is a string"

    result = runner.invoke(cli, ["get", "bar.boolean"])
    assert result.exit_code == 0
    assert result.output.strip() == "False"

    result = runner.invoke(cli, ["get", "bar"])
    assert result.exit_code == 0
    assert result.output.strip() == "{'boolean': False}"

    result = runner.invoke(cli, ["get", "wrong.wrong"])
    assert result.exit_code != 0
    assert "Error: Cannot find object named `wrong.wrong'" in result.output

    result = runner.invoke(cli, ["get", "bar.wrong"])
    assert result.exit_code != 0
    assert "Error: Cannot find object named `bar.wrong'" in result.output


def test_rc_click_writing(datadir, tmp_path):
    # let's copy the user defaults to a temporary file so we can change it
    shutil.copy(datadir / "userdefaults_ex1.cfg", tmp_path)

    rc = UserDefaults(tmp_path / "userdefaults_ex1.cfg")
    logger = logging.getLogger("test-click-writing")

    @user_defaults_group(logger=logger, config=rc)
    def cli(**_):
        """This is the documentation provided by the user."""
        pass

    runner = CliRunner()

    result = runner.invoke(cli, ["set", "string", "a different string"])
    result = runner.invoke(cli, ["get", "bar.boolean"])
    assert result.exit_code == 0
    assert result.output.strip() == "False"

    result = runner.invoke(cli, ["set", "bar.boolean", "true"])
    result = runner.invoke(cli, ["get", "bar.boolean"])
    assert result.exit_code == 0
    assert result.output.strip() == "True"

    result = runner.invoke(cli, ["set", "new-section.date", "2022-02-02"])
    result = runner.invoke(cli, ["get", "new-section.date"])
    assert result.exit_code == 0
    assert result.output.strip() == "2022-02-02"

    result = runner.invoke(cli, ["rm", "new-section.date"])
    result = runner.invoke(cli, ["get", "new-section.date"])
    assert result.exit_code != 0
    assert "Error: Cannot find object named `new-section.date'" in result.output

    result = runner.invoke(cli, ["rm", "new-section"])
    result = runner.invoke(cli, ["get", "new-section"])
    assert result.exit_code != 0
    assert "Error: Cannot find object named `new-section'" in result.output

    result = runner.invoke(cli, ["rm", "bar"])
    assert result.exit_code == 0
    result = runner.invoke(cli, ["get", "bar"])
    assert result.exit_code != 0
    assert "Error: Cannot find object named `bar'" in result.output


def test_rc_click_no_directory(datadir, tmp_path):
    # artificially removes surrounding directory to create an error
    shutil.copy(datadir / "userdefaults_ex1.cfg", tmp_path)

    rc = UserDefaults(tmp_path / "userdefaults_ex1.cfg")
    logger = logging.getLogger("test-click-writing")

    @user_defaults_group(logger=logger, config=rc)
    def cli(**_):
        """This is the documentation provided by the user."""
        pass

    runner = CliRunner()

    shutil.rmtree(tmp_path)
    result = runner.invoke(cli, ["set", "color", "purple"])
    assert result.exit_code != 0
    assert isinstance(result.exception, FileNotFoundError)


def test_rc_click_cannot_set(tmp_path):
    rc = UserDefaults(tmp_path / "test.toml")
    logger = logging.getLogger("test-click-cannot-set")

    @user_defaults_group(logger=logger, config=rc)
    def cli(**_):
        """This is the documentation provided by the user."""
        pass

    runner = CliRunner()

    result = runner.invoke(cli, ["set", "string", "a different string"])
    result = runner.invoke(cli, ["set", "bar.boolean", "true"])
    assert result.exit_code == 0

    assert (tmp_path / "test.toml").exists()

    result = runner.invoke(cli, ["set", "bar.boolean.error", "50"])
    assert result.exit_code != 0
    assert "Error: Cannot set object named `bar.boolean.error'" in result.output


def test_rc_click_cannot_delete(tmp_path):
    rc = UserDefaults(tmp_path / "test.toml")
    logger = logging.getLogger("test-click-cannot-delete")

    @user_defaults_group(logger=logger, config=rc)
    def cli(**_):
        """This is the documentation provided by the user."""
        pass

    runner = CliRunner()

    result = runner.invoke(cli, ["set", "string", "a different string"])
    result = runner.invoke(cli, ["set", "bar.boolean", "true"])
    assert result.exit_code == 0

    assert (tmp_path / "test.toml").exists()

    result = runner.invoke(cli, ["rm", "new-section"])
    assert result.exit_code != 0
    assert "Error: Cannot delete object named `new-section'" in result.output

    # the existing section should still work
    result = runner.invoke(cli, ["rm", "bar"])
    assert result.exit_code == 0
