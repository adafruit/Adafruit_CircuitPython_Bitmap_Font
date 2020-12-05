# The MIT License (MIT)
#
# Copyright (c) 2019 Scott Shawcroft for Adafruit Industries LLC
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`adafruit_bitmap_font.bdf`
====================================================

Loads BDF format fonts.

* Author(s): Scott Shawcroft

Implementation Notes
--------------------

**Hardware:**

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import gc
from fontio import Glyph
from .glyph_cache import GlyphCache

__version__ = "0.0.0-auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Bitmap_Font.git"


class BDF(GlyphCache):
    """Loads glyphs from a BDF file in the given bitmap_class."""

    def __init__(self, f, bitmap_class):
        super().__init__()
        self.file = f
        self.name = f
        self.file.seek(0)
        self.bitmap_class = bitmap_class
        line = self.file.readline()
        if not line or not line.startswith(b"STARTFONT 2.1"):
            raise ValueError("Unsupported file version")
        self.point_size = None
        self.x_resolution = None
        self.y_resolution = None
        self._ascent = None
        self._descent = None

    @property
    def descent(self):
        """The number of pixels below the baseline of a typical descender"""
        if self._descent is None:
            self.file.seek(0)
            while True:
                line = self.file.readline()
                if not line:
                    break

                if line.startswith(b"FONT_DESCENT "):
                    self._descent = int(line.split()[1])
                    break

        return self._descent

    @property
    def ascent(self):
        """The number of pixels above the baseline of a typical ascender"""
        if self._ascent is None:
            self.file.seek(0)
            while True:
                line = self.file.readline()
                if not line:
                    break

                if line.startswith(b"FONT_ASCENT "):
                    self._ascent = int(line.split()[1])
                    break

        return self._ascent

    def get_bounding_box(self):
        """Return the maximum glyph size as a 4-tuple of: width, height, x_offset, y_offset"""
        self.file.seek(0)
        while True:
            line = self.file.readline()
            if not line:
                break

            if line.startswith(b"FONTBOUNDINGBOX "):
                _, x, y, x_offset, y_offset = line.split()
                return (int(x), int(y), int(x_offset), int(y_offset))
        return None

    def _read_to(self, prefix):
        _readline = self.file.readline
        while True:
            line = _readline()
            if not line or line.startswith(prefix):
                return line

    def load_glyphs(self, code_points):
        # pylint: disable=too-many-statements,too-many-branches,too-many-nested-blocks,too-many-locals
        if isinstance(code_points, int):
            remaining = set()
            remaining.add(code_points)
        elif isinstance(code_points, str):
            remaining = set(ord(c) for c in code_points)
        elif isinstance(code_points, set):
            remaining = code_points
        else:
            remaining = set(code_points)
        for code_point in remaining.copy():
            if code_point in self._glyphs and self._glyphs[code_point]:
                remaining.remove(code_point)
        if not remaining:
            return

        _readline = self.file.readline
        _read = self.file.read

        self.file.seek(0)
        _, point_size, x_resolution, y_resolution = self._read_to(b"SIZE ").split()
        self.point_size = int(point_size)
        self.x_resolution = int(x_resolution)
        self.y_resolution = int(y_resolution)

        while remaining:
            line = self._read_to(b"ENCODING ")
            if not line:
                break

            _, code_point = line.split()
            code_point = int(code_point)
            if code_point not in remaining:
                continue

            line = self._read_to(b"DWIDTH ")
            _, shift_x, shift_y = line.split()
            shift_x = int(shift_x)
            shift_y = int(shift_y)

            line = self._read_to(b"BBX ")
            _, x, y, x_offset, y_offset = line.split()
            x = int(x)
            y = int(y)
            x_offset = int(x_offset)
            y_offset = int(y_offset)

            line = self._read_to(b"BITMAP")

            bitmap = self.bitmap_class(x, y, 2)
            start = 0
            for _ in range(y):
                idx = 0
                for idx in range(x):
                    if idx % 4 == 0:
                        value = int(_read(1), 16)
                    if value & 8:
                        bitmap[start + idx] = 1
                    value <<= 1
                _readline()
                start += x

            gc.collect()
            self._glyphs[code_point] = Glyph(
                bitmap, 0, x, y, x_offset, y_offset, shift_x, shift_y
            )

            remaining.remove(code_point)
