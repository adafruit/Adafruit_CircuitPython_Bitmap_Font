from .glyph_cache import GlyphCache
import displayio

class BDF(GlyphCache):
    def __init__(self, f):
        super().__init__()
        self.file = f
        self.name = f
        self.file.seek(0)
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
        rounded_x = 1
        bytes_per_row = 1
        desired_character = False
        current_info = None
        current_y = 0
        total_remaining = len(code_points)

        x, _, _, _ = self.get_bounding_box()
        # create a scratch bytearray to load pixels into
        scratch_row = memoryview(bytearray((((x-1)//32)+1) * 4))

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
                    self._glyphs[code_point] = current_info
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
                    current_info["bitmap"] = displayio.Bitmap(x, y, 2)
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
                    if code_point not in self._glyphs:
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
                    for i in range(rounded_x):
                        val = (bits >> ((rounded_x-i-1)*8)) & 0xFF
                        scratch_row[i] = val
                    current_info["bitmap"]._load_row(current_y, scratch_row[:bytes_per_row])
                    current_y += 1
            elif metadata:
                #print(lineno, line.strip())
                pass
