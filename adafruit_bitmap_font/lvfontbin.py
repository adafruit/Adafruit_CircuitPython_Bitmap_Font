# SPDX-FileCopyrightText: 2025 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_bitmap_font.lvfontbin`
====================================================

Loads binary LVGL format fonts.

* Author(s): Scott Shawcroft

Implementation Notes
--------------------

**Hardware:**

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://github.com/adafruit/circuitpython/releases

"""

import struct

try:
    from io import FileIO
    from typing import Iterable, Union
except ImportError:
    pass

from fontio import Glyph

from .glyph_cache import GlyphCache


class LVGLFont(GlyphCache):
    """Loads glyphs from a LVGL binary font file in the given bitmap_class.

    There is an in-browser converter here: https://lvgl.io/tools/fontconverter

    The format is documented here: https://github.com/lvgl/lv_font_conv/tree/master/doc

    """

    def __init__(self, f: FileIO, bitmap_class=None):
        super().__init__()
        f.seek(0)
        self.file = f
        self.bitmap_class = bitmap_class
        # Initialize default values for bounding box
        self._width = None
        self._height = None
        self._x_offset = 0
        self._y_offset = 0

        # For reading bits
        self._byte = 0
        self._remaining_bits = 0

        while True:
            buffer = f.read(4)
            if len(buffer) < 4:
                break
            section_size = struct.unpack("<I", buffer)[0]
            if section_size == 0:
                break
            table_marker = f.read(4)
            section_start = f.tell()
            remaining_section = f.read(section_size - 8)
            if table_marker == b"head":
                self._load_head(remaining_section)
                # Set bounding box based on font metrics from head section
                self._width = self._default_advance_width
                self._height = self._font_size
                self._x_offset = 0
                self._y_offset = self._descent
            elif table_marker == b"cmap":
                self._load_cmap(remaining_section)
            elif table_marker == b"loca":
                self._max_cid = struct.unpack("<I", remaining_section[0:4])[0]
                self._loca_start = section_start + 4
            elif table_marker == b"glyf":
                self._glyf_start = section_start - 8

    def _load_head(self, data):
        self._version = struct.unpack("<I", data[0:4])[0]
        (
            self._font_size,
            self._ascent,
            self._descent,
            self._typo_ascent,
            self._typo_descent,
            self._line_gap,
            self._min_y,
            self._max_y,
            self._default_advance_width,
            self._kerning_scale,
        ) = struct.unpack("<HHhHhHHHHH", data[6:26])
        self._index_to_loc_format = data[26]
        self._glyph_id_format = data[27]
        self._advance_format = data[28]
        self._bits_per_pixel = data[29]
        self._glyph_bbox_xy_bits = data[30]
        self._glyph_bbox_wh_bits = data[31]
        self._glyph_advance_bits = data[32]
        self._glyph_header_bits = (
            self._glyph_advance_bits + 2 * self._glyph_bbox_xy_bits + 2 * self._glyph_bbox_wh_bits
        )
        self._glyph_header_bytes = (self._glyph_header_bits + 7) // 8
        self._compression_alg = data[33]
        self._subpixel_rendering = data[34]

    def _load_cmap(self, data):
        data = memoryview(data)
        subtable_count = struct.unpack("<I", data[0:4])[0]
        self._cmap_tiny = []
        for i in range(subtable_count):
            subtable_header = data[4 + 16 * i : 4 + 16 * (i + 1)]
            (_, range_start, range_length, glyph_offset, _) = struct.unpack(
                "<IIHHH", subtable_header[:14]
            )
            format_type = subtable_header[14]

            if format_type != 2:
                raise RuntimeError(f"Unsupported cmap format {format_type}")

            self._cmap_tiny.append((range_start, range_start + range_length, glyph_offset))

    @property
    def ascent(self) -> int:
        """The number of pixels above the baseline of a typical ascender"""
        return self._ascent

    @property
    def descent(self) -> int:
        """The number of pixels below the baseline of a typical descender"""
        return self._descent

    def get_bounding_box(self) -> tuple[int, int, int, int]:
        """Return the maximum glyph size as a 4-tuple of: width, height, x_offset, y_offset"""
        return (self._width, self._height, self._x_offset, self._y_offset)

    def _seek(self, offset):
        self.file.seek(offset)
        self._byte = 0
        self._remaining_bits = 0

    def _read_bits(self, num_bits):
        result = 0
        needed_bits = num_bits
        while needed_bits > 0:
            if self._remaining_bits == 0:
                self._byte = self.file.read(1)[0]
                self._remaining_bits = 8
            available_bits = min(needed_bits, self._remaining_bits)
            result = (result << available_bits) | (self._byte >> (8 - available_bits))
            self._byte <<= available_bits
            self._byte &= 0xFF
            self._remaining_bits -= available_bits
            needed_bits -= available_bits
        return result

    def load_glyphs(self, code_points: Union[int, str, Iterable[int]]) -> None:
        # pylint: disable=too-many-statements,too-many-branches,too-many-nested-blocks,too-many-locals
        if isinstance(code_points, int):
            code_points = (code_points,)
        elif isinstance(code_points, str):
            code_points = [ord(c) for c in code_points]

        # Only load glyphs that aren't already cached
        code_points = sorted(c for c in code_points if self._glyphs.get(c, None) is None)
        if not code_points:
            return

        for code_point in code_points:
            # Find character ID in the cmap table
            cid = None
            for start, end, offset in self._cmap_tiny:
                if start <= code_point < end:
                    cid = offset + (code_point - start)
                    break

            if cid is None or cid >= self._max_cid:
                self._glyphs[code_point] = None
                continue

            offset_length = 4 if self._index_to_loc_format == 1 else 2

            # Get the glyph offset from the location table
            self._seek(self._loca_start + cid * offset_length)
            glyph_offset = struct.unpack(
                "<I" if offset_length == 4 else "<H", self.file.read(offset_length)
            )[0]

            # Read glyph header data
            self._seek(self._glyf_start + glyph_offset)
            glyph_advance = self._read_bits(self._glyph_advance_bits)

            # Read and convert signed bbox_x and bbox_y
            bbox_x = self._read_bits(self._glyph_bbox_xy_bits)
            # Convert to signed value if needed (using two's complement)
            if bbox_x & (1 << (self._glyph_bbox_xy_bits - 1)):
                bbox_x = bbox_x - (1 << self._glyph_bbox_xy_bits)

            bbox_y = self._read_bits(self._glyph_bbox_xy_bits)
            # Convert to signed value if needed (using two's complement)
            if bbox_y & (1 << (self._glyph_bbox_xy_bits - 1)):
                bbox_y = bbox_y - (1 << self._glyph_bbox_xy_bits)

            bbox_w = self._read_bits(self._glyph_bbox_wh_bits)
            bbox_h = self._read_bits(self._glyph_bbox_wh_bits)

            # Create bitmap for the glyph
            bitmap = self.bitmap_class(bbox_w, bbox_h, 2)

            # Read bitmap data (starting from the current bit position)
            for y in range(bbox_h):
                for x in range(bbox_w):
                    pixel_value = self._read_bits(self._bits_per_pixel)
                    if pixel_value > 0:  # Convert any non-zero value to 1
                        bitmap[x, y] = 1

            # Create and cache the glyph
            self._glyphs[code_point] = Glyph(
                bitmap, 0, bbox_w, bbox_h, bbox_x, bbox_y, glyph_advance, 0
            )
