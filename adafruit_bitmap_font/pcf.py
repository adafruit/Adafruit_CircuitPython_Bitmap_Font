from collections import namedtuple
import gc

from .glyph_cache import GlyphCache
from fontio import Glyph
import displayio
import struct

_PCF_PROPERTIES = 1 << 0
_PCF_ACCELERATORS = 1 << 1
_PCF_METRICS = 1 << 2
_PCF_BITMAPS = 1 << 3
_PCF_INK_METRICS = 1 << 4
_PCF_BDF_ENCODINGS = 1 << 5
_PCF_SWIDTHS = 1 << 6
_PCF_GLYPH_NAMES = 1 << 7
_PCF_BDF_ACCELERATORS = 1 << 8

_PCF_DEFAULT_FORMAT = 0x00000000
_PCF_INKBOUNDS = 0x00000200
_PCF_ACCEL_W_INKBOUNDS = 0x00000100
_PCF_COMPRESSED_METRICS = 0x00000100

_PCF_GLYPH_PAD_MASK = 3 << 0  # See the bitmap table for explanation */
_PCF_BYTE_MASK = 1 << 2  # If set then Most Sig Byte First */
_PCF_BIT_MASK = 1 << 3  # If set then Most Sig Bit First */
_PCF_SCAN_UNIT_MASK = 3 << 4

# https://fontforge.org/docs/techref/pcf-format.html

Table = namedtuple("Table", ("format", "size", "offset"))
Metrics = namedtuple("Metrics", ("left_side_bearing", "right_side_bearing", "character_width", "character_ascent", "character_descent", "character_attributes"))
Accelerators = namedtuple("Accelerators", (
    "no_overlap", "constant_metrics", "terminal_font", "constant_width",
    "ink_inside", "ink_metrics", "draw_direction", "font_ascent", "font_descent", "max_overlap", "minbounds", "maxbounds", "ink_minbounds", "ink_maxbounds"))
Encoding = namedtuple("Encoding", (
    "min_byte2", "max_byte2", "min_byte1", "max_byte1", "default_char"))
Bitmap = namedtuple("Bitmap", ("glyph_count", "bitmap_sizes"))

class PCF(GlyphCache):
    def __init__(self, f, bitmap_class):
        super().__init__()
        self.file = f
        self.name = f
        f.seek(0)
        self.bitmap_class = bitmap_class
        header, table_count = self.read("<4sI")
        self.tables = {}
        for _ in range(table_count):
            type, format, size, offset = self.read("<IIII")
            self.tables[type] = Table(format, size, offset)

        bitmap_format = self.tables[_PCF_BITMAPS].format
        if bitmap_format != 0xe:
            raise NotImplementedError(f"Unsupported format {bitmap_format:x}")

        self._accel = self.read_accelerator_tables()
        self._encoding = self.read_encoding_table()
        self._bitmaps = self.read_bitmap_table()

        self.ascent = self._accel.font_ascent
        self.descent = self._accel.font_descent

        minbounds = self._accel.ink_minbounds
        maxbounds = self._accel.ink_maxbounds
        width = maxbounds.right_side_bearing - minbounds.left_side_bearing
        height = maxbounds.character_ascent + maxbounds.character_descent

        self._bounding_box = width, height, minbounds.left_side_bearing, -maxbounds.character_descent

    def get_bounding_box(self):
        return self._bounding_box

    def read(self, format):
        s = struct.calcsize(format)
        return struct.unpack_from(format, self.file.read(s))

    def seek_table(self, table):
        self.file.seek(table.offset)
        (format,) = self.read("<I")

        if format & _PCF_BYTE_MASK == 0:
            raise RuntimeError("Only big endian supported")
        
        return format

    def seek_glyph(self, idx):
        encoding = self.tables[_PCF_BDF_ENCODINGS]
        self.seek_table(encoding)

    def read_encoding_table(self):
        encoding = self.tables[_PCF_BDF_ENCODINGS]
        self.seek_table(encoding)

        return Encoding(*self.read(">hhhhh"))

    def read_bitmap_table(self):
        bitmaps = self.tables[_PCF_BITMAPS]
        format = self.seek_table(bitmaps)

        glyph_count, = self.read(">I")
        self.file.seek(bitmaps.offset + 8 + 4 * glyph_count)
        bitmap_sizes = self.read(">4I")
        return Bitmap(glyph_count, bitmap_sizes[format & 3])

    def read_metrics(self, compressed_metrics):
        if compressed_metrics:
            left_side_bearing, right_side_bearing, character_width, character_ascent, character_descent = self.read("5B")
            left_side_bearing -= 0x80
            right_side_bearing -= 0x80
            character_width -= 0x80
            character_ascent -= 0x80
            character_descent -= 0x80
            attributes = 0
        else:
            left_side_bearing, right_side_bearing, character_width, character_ascent, character_descent, attributes = self.read(">5hH")
        return Metrics(left_side_bearing, right_side_bearing, character_width, character_ascent, character_descent, attributes)

    def read_accelerator_tables(self):
        accelerators = self.tables.get(_PCF_BDF_ACCELERATORS)
        if not accelerators:
            accelerators = self.tables.get(_PCF_ACCELERATORS)
        if not accelerators:
            raise RuntimeError("Accelerator table missing")

        format = self.seek_table(accelerators)

        has_inkbounds = format & _PCF_ACCEL_W_INKBOUNDS
        compressed_metrics = False # format & _PCF_COMPRESSED_METRICS

        (no_overlap, constant_metrics, terminal_font, constant_width, ink_inside, ink_metrics, draw_direction, _, font_ascent, font_descent, max_overlap) = self.read(">BBBBBBBBIII")
        minbounds = self.read_metrics(compressed_metrics)
        maxbounds = self.read_metrics(compressed_metrics)
        if has_inkbounds:
            ink_minbounds = self.read_metrics(compressed_metrics)
            ink_maxbounds = self.read_metrics(compressed_metrics)
        else:
            ink_minbounds = minbounds    
            ink_maxbounds = maxbounds    

        return Accelerators(
            no_overlap, constant_metrics, terminal_font, constant_width, ink_inside, ink_metrics, draw_direction, font_ascent, font_descent, max_overlap, minbounds, maxbounds, ink_minbounds, ink_maxbounds)
        
    def read_properties(self):
        property_table_offset = self.tables[_PCF_PROPERTIES]["offset"]
        self.file.seek(property_table_offset)
        (format,) = self.read("<I")

        if format & _PCF_BYTE_MASK == 0:
            raise RuntimeError("Only big endian supported")
        (nprops,) = self.read(">I")
        self.file.seek(property_table_offset + 8 + 9 * nprops)

        pos = self.file.tell()
        if pos % 4 > 0:
            self.file.read(4 - pos % 4)
        (string_size,) = self.read(">I")

        strings = self.file.read(string_size)
        string_map = {}
        i = 0
        for s in strings.split(b"\x00"):
            string_map[i] = s
            i += len(s) + 1

        self.file.seek(property_table_offset + 8)
        for _ in range(nprops):
            name_offset, isStringProp, value = self.read(">IBI")

            if isStringProp:
                yield (string_map[name_offset], string_map[value])
            else:
                yield (string_map[name_offset], value)



    def load_glyphs(self, code_points):
        # pylint: disable=too-many-statements,too-many-branches,too-many-nested-blocks,too-many-locals
        if isinstance(code_points, int):
            code_points = (code_points,)
        elif isinstance(code_points, str):
            code_points = [ord(c) for c in code_points]

        code_points = sorted(c for c in code_points if self._glyphs.get(c, None) is None)

        if not code_points:
            return

        indices_offset = self.tables[_PCF_BDF_ENCODINGS].offset + 14
        bitmap_offset_offsets = self.tables[_PCF_BITMAPS].offset + 8
        first_bitmap_offset = self.tables[_PCF_BITMAPS].offset + 4 * (6 + self._bitmaps.glyph_count)
        metrics_compressed = self.tables[_PCF_METRICS].format & _PCF_COMPRESSED_METRICS
        first_metric_offset = self.tables[_PCF_METRICS].offset + 6 if metrics_compressed else 8
        metrics_size = 5 if metrics_compressed else 12

        # These will each _tend to be_ forward reads in the file, at least
        # sometimes we'll benefit from oofatfs's 512 byte cache and avoid
        # excess reads
        indices = [None] * len(code_points)
        for i, code_point in enumerate(code_points):
            enc1 = (code_point >> 8) & 0xff
            enc2 = code_point & 0xff
            
            if enc1 < self._encoding.min_byte1 or enc1 >= self._encoding.max_byte1:
                continue
            if enc2 < self._encoding.min_byte2 or enc2 >= self._encoding.max_byte2:
                continue

            encoding_idx = (enc1 - self._encoding.min_byte1) * (self._encoding.max_byte2 - self._encoding.min_byte2 + 1) + enc2 - self._encoding.min_byte2
            self.file.seek(indices_offset + 2 * encoding_idx)
            glyph_idx, = self.read(">H")
            indices[i] = glyph_idx

        all_metrics = [None] * len(code_points)
        for i, code_point in enumerate(code_points):
            index = indices[i]
            if index is None: continue
            self.file.seek(first_metric_offset + metrics_size * index)
            all_metrics[i] = self.read_metrics(metrics_compressed)
        bitmap_offsets = [None] * len(code_points)
        for i, code_point in enumerate(code_points):
            index = indices[i]
            if index is None: continue
            self.file.seek(bitmap_offset_offsets + 4 * index)
            bitmap_offset, = self.read(">I")
            bitmap_offsets[i] = bitmap_offset

        for i, code_point in enumerate(code_points):
            metrics = all_metrics[i]
            if metrics is None: continue
            self.file.seek(first_bitmap_offset + bitmap_offsets[i])
            shift = metrics.character_width
            width = metrics.right_side_bearing - metrics.left_side_bearing
            height = metrics.character_ascent + metrics.character_descent

            gc.collect()
            bitmap = self.bitmap_class(width, height , 2)
            self._glyphs[code_point] = Glyph(bitmap, 0, 
                        width,
                        height,
                        metrics.left_side_bearing,
                        -metrics.character_descent,
                        metrics.character_width,
                        0)
            words_per_row = ((width + 31) // 32)
            buf = bytearray(4 * words_per_row)
            start = 0
            for i in range(height):
                self.file.readinto(buf)
                for j in range(width):
                    bitmap[start] = not not (buf[j // 8] & (128 >> (j % 8)))
                    start += 1
