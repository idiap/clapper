# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

from clapper.click import config_group
from clapper.logging import setup

logger = setup(__name__.split(".", 1)[0])


@config_group(logger=logger, entry_point_group="clapper.test.config")
def main(**kwargs):
    """Use this command to list/describe/copy package config resources."""
    pass


if __name__ == "__main__":
    main()
