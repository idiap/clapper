# SPDX-FileCopyrightText: Copyright © 2022 Idiap Research Institute <contact@idiap.ch>
#
# SPDX-License-Identifier: BSD-3-Clause

# the b variable from the last config file is available here
c = b + 1  # noqa: F821
b = b + 3  # noqa: F821
