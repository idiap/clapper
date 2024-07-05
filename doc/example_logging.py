# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

import logging

from clapper.logging import setup

logger = setup(__name__.split(".", 1)[0], format="%(levelname)s: %(message)s")
logger.setLevel(logging.INFO)
logger.info("test message")
