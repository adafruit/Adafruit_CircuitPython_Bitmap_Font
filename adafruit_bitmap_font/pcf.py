
class BDF:
    def __init__(self, f):
        self.file = f

        f.seek(0)

        self.characters = {}

        metadata = True
        character = False
        bitmap_lines_left = 0
        bounds = None
        bitmap = None
        code_point = None
        character_name = None
        for lineno, line in enumerate(self.file.readlines()):
            if lineno == 0 and not line.startswith("STARTFONT 2.1"):
                raise ValueError("Unsupported file version")
            if line.startswith("CHARS "):
                metadata = False
            if line.startswith("SIZE"):
                _, self.point_size, self.x_resolution, self.y_resolution = line.split()
            elif line.startswith("COMMENT"):
                token, comment = line.split(" ", 1)
                print(comment.strip("\n\""))
            elif line.startswith("STARTCHAR"):
                print(lineno, line.strip())
                _, character_name = line.split()
                character = True
            elif line.startswith("ENDCHAR"):
                character = False
            elif line.startswith("BBX"):
                _, x, y, dx, dy = line.split()
                x = int(x)
                y = int(y)
                dx = int(dx)
                dy = int(dy)
                bounds = (x, y, dx, dy)
                character = False
            elif line.startswith("BITMAP"):
                character = False
                bitmap_lines_left = bounds[1]
                bitmap = []
            elif line.startswith("ENCODING"):
                _, code_point = line.split()
                code_point = int(code_point)
                print(hex(code_point))
            elif bitmap_lines_left > 0:
                bits = int(line.strip(), 16)
                shift = 8 - bounds[0]
                bits >>= shift
                pixels = ("{0:0" + str(bounds[0]) +"b}").format(bits).replace("0", " ")
                bitmap.append(pixels)
                bitmap_lines_left -= 1

                if bitmap_lines_left == 0:
                    self.characters[code_point] = {"name": character_name, "bitmap": bitmap}
            elif metadata:
                print(lineno, line.strip())
