# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause
"""Implements a global configuration system setup and readout."""

import collections.abc
import io
import json
import logging
import pathlib
import typing

import tomli
import tomli_w
import xdg


class UserDefaults(collections.abc.MutableMapping):
    """Contains user defaults read from the user TOML configuration file.

    Upon intialisation, an instance of this class will read the user
    configuration file defined by the first argument. If the input file is
    specified as a relative path, then it is considered relative to the
    environment variable ``${XDG_CONFIG_HOME}``, or its default setting (which is
    operating system dependent, c.f. `XDG defaults`_).

    This object may be used (with limited functionality) like a dictionary.  In
    this mode, objects of this class read and write values to the ``DEFAULT``
    section.  The ``len()`` method will also return the number of variables set
    at the ``DEFAULT`` section as well.

    Parameters
    ----------
    path
        The path, absolute or relative, to the file containing the user
        defaults to read.  If `path` is a relative path, then it is considered
        relative to the directory defined by the environment variable
        ``${XDG_CONFIG_HOME}`` (read `XDG defaults
        <https://specifications.freedesktop.org/basedir-spec/basedir-spec-latest.html>`_
        for details on the default location of this directory in the various
        operating systems).  The tilde (`~`) character may be used to represent
        the user home, and is automatically expanded.
    logger
        A logger to use for messaging operations.  If not set, use this
        module's logger.

    Attributes
    ----------
    path
        The current path to the user defaults base file.
    """

    def __init__(
        self,
        path: str | pathlib.Path,
        logger: logging.Logger | None = None,
    ) -> None:
        self.logger = logger or logging.getLogger(__name__)

        self.path = pathlib.Path(path).expanduser()

        if not self.path.is_absolute():
            self.path = xdg.xdg_config_home() / self.path

        self.logger.info(f"User configuration file set to `{str(self.path)}'")
        self.data: dict[str, typing.Any] = {}
        self.read()

    def read(self) -> None:
        """Read configuration file, replaces any internal values."""
        if self.path.exists():
            self.logger.debug("User configuration file exists, reading contents...")
            self.data.clear()

            with self.path.open("rb") as f:
                contents = f.read()

            # Support for legacy JSON file format.  Remove after sometime
            # FYI: today is September 16, 2022
            try:
                data = json.loads(contents)
                self.logger.warning(
                    f"Converting `{str(self.path)}' from (legacy) JSON "
                    f"to (new) TOML format"
                )
                self.update(data)
                self.write()
                self.clear()
                # reload contents
                with self.path.open("rb") as f:
                    contents = f.read()
            except ValueError:
                pass

            self.data.update(tomli.load(io.BytesIO(contents)))

        else:
            self.logger.debug("Initializing empty user configuration...")

    def write(self) -> None:
        """Store any modifications done on the user configuration."""
        if self.path.exists():
            backup = pathlib.Path(str(self.path) + "~")
            self.logger.debug(f"Backing-up {str(self.path)} -> {str(backup)}")
            self.path.rename(backup)

        with self.path.open("wb") as f:
            tomli_w.dump(self.data, f)

        self.logger.info(f"Wrote configuration at {str(self.path)}")

    def __str__(self) -> str:
        t = io.BytesIO()
        tomli_w.dump(self.data, t)
        return t.getvalue().decode(encoding="utf-8")

    def __getitem__(self, k: str) -> typing.Any:
        if k in self.data:
            return self.data[k]

        if "." in k:
            # search for a key with a matching name after the "."
            parts = k.split(".")
            base = self.data
            for n in range(len(parts)):
                if parts[n] in base:
                    base = base[parts[n]]
                    if (not isinstance(base, dict)) and (n < (len(parts) - 1)):
                        # this is an actual value, not another dict whereas it
                        # should not as we have more parts to go
                        break
                else:
                    break
                subkey = ".".join(parts[(n + 1) :])
                if subkey in base:
                    return base[subkey]

        # otherwise, defaults to the default behaviour
        return self.data.__getitem__(k)

    def __setitem__(self, k: str, v: typing.Any) -> None:
        assert isinstance(k, str)

        if "." in k:
            # sets nested subsections
            parts = k.split(".")
            base = self.data
            for n in range(len(parts) - 1):
                base = base.setdefault(parts[n], {})
                if not isinstance(base, dict):
                    raise KeyError(
                        f"You are trying to set configuration key "
                        f"{k}, but {'.'.join(parts[:(n + 1)])} is already a "
                        f"variable set in the file, and not a section"
                    )
            base[parts[-1]] = v
            return v

        # otherwise, defaults to the default behaviour
        return self.data.__setitem__(k, v)

    def __delitem__(self, k: str) -> None:
        assert isinstance(k, str)

        if "." in k:
            # search for a key with a matching name after the "."
            parts = k.split(".")
            base = self.data
            for n in range(len(parts) - 1):
                if parts[n] in base:
                    base = base[parts[n]]
                    if not isinstance(base, dict):
                        # this is an actual value, not another dict whereas it
                        # should not as we have more parts to go
                        break
                else:
                    break
                subkey = ".".join(parts[(n + 1) :])
                if subkey in base:
                    del base[subkey]
                    return None

        # otherwise, defaults to the default behaviour
        return self.data.__delitem__(k)

    def __iter__(self) -> typing.Iterator[str]:
        return self.data.__iter__()

    def __len__(self) -> int:
        return self.data.__len__()
