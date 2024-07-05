# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

from clapper.click import user_defaults_group
from clapper.logging import setup
from clapper.rc import UserDefaults

logger = setup(__name__.split(".", 1)[0])
rc = UserDefaults("myapp.toml", logger=logger)


@user_defaults_group(logger=logger, config=rc)
def main(**kwargs):
    """Use this command to affect the global user defaults."""
    pass


if __name__ == "__main__":
    main()
