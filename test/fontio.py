# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""Implementation of minimal fontio subset for testing"""

import collections

Glyph = collections.namedtuple(
    "Glyph",
    ["bitmap", "tile_index", "width", "height", "dx", "dy", "shift_x", "shift_y"],
)
