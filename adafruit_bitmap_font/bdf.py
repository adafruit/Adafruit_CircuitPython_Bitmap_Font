import gc
from .glyph_cache import GlyphCache
from displayio import Glyph

class BDF(GlyphCache):
    def __init__(self, f, bitmap_class):
        super().__init__()
        self.file = f
        self.name = f
        self.file.seek(0)
        self.bitmap_class = bitmap_class
        line = self.file.readline()
        line = str(line, "utf-8")
        if not line or not line.startswith("STARTFONT 2.1"):
            raise ValueError("Unsupported file version")

    def get_bounding_box(self):
        self.file.seek(0)
        while True:
            line = self.file.readline()
            line = str(line, "utf-8")
            if not line:
                break

            if line.startswith("FONTBOUNDINGBOX "):
                _, x, y, dx, dy = line.split()
                return (int(x), int(y), int(dx), int(dy))
        return None

    def load_glyphs(self, code_points):
        metadata = True
        character = False
        code_point = None
        bytes_per_row = 1
        desired_character = False
        current_info = None
        current_y = 0
        rounded_x = 1
        total_remaining = len(code_points)

        x, _, _, _ = self.get_bounding_box()

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
                # print(lineno, line.strip())
                #_, character_name = line.split()
                character = True
            elif line.startswith(b"ENDCHAR"):
                character = False
                if desired_character:
                    bounds = current_info["bounds"]
                    shift = current_info["shift"]
                    self._glyphs[code_point] = Glyph(current_info["bitmap"],
                                                     0,
                                                     bounds[0],
                                                     bounds[1],
                                                     bounds[2],
                                                     bounds[3],
                                                     shift[0],
                                                     shift[1])
                    gc.collect()
                    if total_remaining == 0:
                        return
                desired_character = False
            elif line.startswith(b"BBX"):
                if desired_character:
                    _, x, y, dx, dy = line.split()
                    x = int(x)
                    y = int(y)
                    dx = int(dx)
                    dy = int(dy)
                    current_info["bounds"] = (x, y, dx, dy)
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
                if code_point == code_points or code_point in code_points:
                    total_remaining -= 1
                    if code_point not in self._glyphs or not self._glyphs[code_point]:
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
                        val = (bits >> ((rounded_x-i-1)*8)) & 0xFF
                        for j in range(7,-1,-1):
                            if x >= width:
                                break
                            bit = 0
                            if val & (1 << j) != 0:
                                bit = 1
                            current_info["bitmap"][start + x] = bit
                            x += 1
                    current_y += 1
            elif metadata:
                #print(lineno, line.strip())
                pass
