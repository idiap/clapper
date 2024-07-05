# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

import contextlib
import io
import pathlib
import warnings

import pytest

from click.testing import CliRunner
from pytest import fixture

"""

In your tests:

  @cli_runner
  def test_foo(cli_runner):
    r = cli_runner.invoke(mycli, ["mycommand"])
    assert r.exit_code == 0

In `some_command()`, add:

  @cli.command()
  def mycommand():
    import pytest; pytest.set_trace()

Then run via:

  $ pytest --pdb-trace ...

Note any tests checking CliRunner stdout/stderr values will fail when
--pdb-trace is set.

"""


def pytest_addoption(parser) -> None:
    parser.addoption(
        "--pdb-trace",
        action="store_true",
        default=False,
        help="Allow calling pytest.set_trace() in Click's CliRunner",
    )


class MyCliRunner(CliRunner):
    def __init__(self, *args, in_pdb=False, **kwargs) -> None:
        self._in_pdb = in_pdb
        super().__init__(*args, **kwargs)

    def invoke(self, cli, args=None, **kwargs):
        params = kwargs.copy()
        if self._in_pdb:
            params["catch_exceptions"] = False

        return super().invoke(cli, args=args, **params)

    def isolation(self, input_=None, env=None, color=False):
        if self._in_pdb:
            if input_ or env or color:
                warnings.warn(
                    "CliRunner PDB un-isolation doesn't work if input/env/color are passed"
                )
            else:
                return self.isolation_pdb()

        return super().isolation(input=input_, env=env, color=color)

    @contextlib.contextmanager
    def isolation_pdb(self):
        s = io.BytesIO(b"{stdout not captured because --pdb-trace}")
        yield (s, not self.mix_stderr and s)


@pytest.fixture
def cli_runner(request) -> MyCliRunner:
    """A wrapper round Click's test CliRunner to improve usefulness."""
    return MyCliRunner(
        # workaround Click's environment isolation so debugging works.
        in_pdb=request.config.getoption("--pdb-trace")
    )


@fixture
def datadir(request) -> pathlib.Path:
    """Returns the directory in which the test is sitting."""
    return pathlib.Path(request.module.__file__).parents[0] / "data"
