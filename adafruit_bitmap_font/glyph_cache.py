# SPDX-FileCopyrightText: 2019 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_bitmap_font.glyph_cache`
====================================================

Displays text using CircuitPython's displayio.

* Author(s): Scott Shawcroft

Implementation Notes
--------------------

**Hardware:**

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

try:
    from typing import Union, Iterable
    from fontio import Glyph
except ImportError:
    pass

import gc

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Bitmap_Font.git"


class GlyphCache:
    """Caches glyphs loaded by a subclass."""

    def __init__(self) -> None:
        self._glyphs = {}

    def load_glyphs(self, code_points: Union[int, str, Iterable[int]]) -> None:
        """Loads displayio.Glyph objects into the GlyphCache from the font."""

    def get_glyph(self, code_point: int) -> Glyph:
        """Returns a displayio.Glyph for the given code point or None is unsupported."""
        if code_point in self._glyphs:
            return self._glyphs[code_point]

        code_points = set()
        code_points.add(code_point)
        self._glyphs[code_point] = None
        self.load_glyphs(code_points)
        gc.collect()
        return self._glyphs[code_point]
