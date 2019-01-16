from .glyph_cache import GlyphCache

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

    def _get_glyph(self, input_code_point):
        self.file.seek(0)
        self.characters = {}

        metadata = True
        character = False
        bounds = None
        bitmap = None
        code_point = None
        character_name = None
        lineno = 0
        count = 0
        current_y = 0
        rounded_x = 1
        desired_character = False
        while True:
            line = self.file.readline()
            line = str(line, "utf-8")
            if not line:
                break
            if line.startswith("CHARS "):
                metadata = False
            elif line.startswith("SIZE"):
                _, self.point_size, self.x_resolution, self.y_resolution = line.split()
            elif line.startswith("COMMENT"):
                pass
                #token, comment = line.split(" ", 1)
                # print(comment.strip("\n\""))
            elif line.startswith("STARTCHAR"):
                # print(lineno, line.strip())
                #_, character_name = line.split()
                character = True
            elif line.startswith("ENDCHAR"):
                character = False
                count += 1
                if desired_character:
                    #print(lineno, character_name, bounds)
                    return {"bitmap": bitmap, "bounds": bounds, "shift": (shift_x, shift_y)}
            elif line.startswith("BBX"):
                if desired_character:
                    _, x, y, dx, dy = line.split()
                    x = int(x)
                    y = int(y)
                    dx = int(dx)
                    dy = int(dy)
                    bounds = (x, y, dx, dy)
            elif line.startswith("BITMAP"):
                if desired_character:
                    rounded_x = x // 8
                    if x % 8 > 0:
                        rounded_x += 1
                    bitmap = bytearray(rounded_x * y)
                    current_y = 0
                pass
            elif line.startswith("ENCODING"):
                _, code_point = line.split()
                code_point = int(code_point)
                if code_point == input_code_point:
                    desired_character = True
            elif line.startswith("DWIDTH"):
                _, shift_x, shift_y = line.split()
                shift_x = int(shift_x)
                shift_y = int(shift_y)
            elif line.startswith("SWIDTH"):
                pass
            elif character:
                if desired_character:
                    bits = int(line.strip(), 16)
                    #print(hex(bits))
                    shift = 8 - bounds[0]
                    #bits >>= shift
                    for i in range(rounded_x):
                        idx = current_y * rounded_x + i
                        val = (bits >> ((rounded_x-i-1)*8)) & 0xFF
                        #print("idx:", idx, "val:", hex(val))
                        bitmap[idx] = val
                    #pixels = ("{0:0" + str(bounds[0]) +"b}").format(bits).replace("0", " ").replace("1", "*")
                    #print(pixels)
                    #bitmap.append(pixels)
                    current_y += 1

            elif metadata:
                #print(lineno, line.strip())
                pass
            lineno += 1
