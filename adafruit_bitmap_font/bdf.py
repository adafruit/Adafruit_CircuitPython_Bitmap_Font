# SPDX-FileCopyrightText: 2019 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

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

try:
    from io import FileIO
    from typing import Iterable, Optional, Tuple, Union

    from displayio import Bitmap
except ImportError:
    pass

import gc

from fontio import Glyph

from .glyph_cache import GlyphCache

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Bitmap_Font.git"


class BDF(GlyphCache):
    """Loads glyphs from a BDF file in the given bitmap_class."""

    def __init__(self, f: FileIO, bitmap_class: Bitmap) -> None:
        super().__init__()
        self.file = f
        self.name = f
        self.file.seek(0)
        self.bitmap_class = bitmap_class
        line = self._readline_file()
        if not line or not line.startswith("STARTFONT 2.1"):
            raise ValueError("Unsupported file version")
        self._verify_bounding_box()
        self.point_size = None
        self.x_resolution = None
        self.y_resolution = None
        self._ascent = None
        self._descent = None

    @property
    def descent(self) -> Optional[int]:
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
    def ascent(self) -> Optional[int]:
        """The number of pixels above the baseline of a typical ascender"""
        if self._ascent is None:
            self.file.seek(0)
            while True:
                line = self._readline_file()
                if not line:
                    break

                if line.startswith("FONT_ASCENT "):
                    self._ascent = int(line.split()[1])
                    break

        return self._ascent

    def _verify_bounding_box(self) -> None:
        """Private function to verify FOUNTBOUNDINGBOX parameter
        This function will parse the first 10 lines of the font source
        file to verify the value or raise an exception in case is not found
        """
        self.file.seek(0)
        # Normally information about the FONT is in the first four lines.
        # Exception is when font file have a comment. Comments are three lines
        # 10 lines is a safe bet
        for _ in range(11):
            line = self._readline_file()
            while line.startswith("COMMENT "):
                line = self._readline_file()
            if line.startswith("FONTBOUNDINGBOX "):
                _, x, y, x_offset, y_offset = line.split()
                self._boundingbox = (int(x), int(y), int(x_offset), int(y_offset))

        try:
            self._boundingbox
        except AttributeError as error:
            raise RuntimeError(
                "Source file does not have the FOUNTBOUNDINGBOX parameter"
            ) from error

    def _readline_file(self) -> str:
        line = self.file.readline()
        return str(line, "utf-8")

    def get_bounding_box(self) -> Tuple[int, int, int, int]:
        """Return the maximum glyph size as a 4-tuple of: width, height, x_offset, y_offset"""
        return self._boundingbox

    def load_glyphs(self, code_points: Union[int, str, Iterable[int]]) -> None:
        metadata = True
        character = False
        code_point = None
        bytes_per_row = 1
        desired_character = False
        current_info = {}
        current_y = 0
        rounded_x = 1
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

        x, _, _, _ = self._boundingbox

        self.file.seek(0)
        while True:
            line = self.file.readline()
            if not line:
                break
            if line.startswith(b"CHARS "):
                metadata = False
            elif line.startswith(b"SIZE"):
                _, self.point_size, self.x_resolution, self.y_resolution = line.split()
            elif line.startswith(b"COMMENT"):
                pass
            elif line.startswith(b"STARTCHAR"):
                character = True
            elif line.startswith(b"ENDCHAR"):
                character = False
                if desired_character:
                    bounds = current_info["bounds"]
                    shift = current_info["shift"]
                    gc.collect()
                    self._glyphs[code_point] = Glyph(
                        current_info["bitmap"],
                        0,
                        bounds[0],
                        bounds[1],
                        bounds[2],
                        bounds[3],
                        shift[0],
                        shift[1],
                    )
                    remaining.remove(code_point)
                    if not remaining:
                        return
                desired_character = False
            elif line.startswith(b"BBX"):
                if desired_character:
                    _, x, y, x_offset, y_offset = line.split()
                    x = int(x)
                    y = int(y)
                    x_offset = int(x_offset)
                    y_offset = int(y_offset)
                    current_info["bounds"] = (x, y, x_offset, y_offset)
                    current_info["bitmap"] = self.bitmap_class(x, y, 2)
            elif line.startswith(b"BITMAP"):
                if desired_character:
                    rounded_x = x // 8
                    if x % 8 > 0:
                        rounded_x += 1
                    bytes_per_row = rounded_x
                    if bytes_per_row % 4 > 0:
                        bytes_per_row += 4 - bytes_per_row % 4
                    current_y = 0
            elif line.startswith(b"ENCODING"):
                _, code_point = line.split()
                code_point = int(code_point)
                if code_point in remaining:
                    desired_character = True
                    current_info = {"bitmap": None, "bounds": None, "shift": None}
            elif line.startswith(b"DWIDTH"):
                if desired_character:
                    _, shift_x, shift_y = line.split()
                    shift_x = int(shift_x)
                    shift_y = int(shift_y)
                    current_info["shift"] = (shift_x, shift_y)
            elif line.startswith(b"SWIDTH"):
                pass
            elif character:
                if desired_character:
                    bits = int(line.strip(), 16)
                    width = current_info["bounds"][0]
                    start = current_y * width
                    x = 0
                    for i in range(rounded_x):
                        val = (bits >> ((rounded_x - i - 1) * 8)) & 0xFF
                        for j in range(7, -1, -1):
                            if x >= width:
                                break
                            bit = 0
                            if val & (1 << j) != 0:
                                bit = 1
                            current_info["bitmap"][start + x] = bit
                            x += 1
                    current_y += 1
            elif metadata:
                pass
