# Call this with the font file as the command line argument.

import os
import sys

# Add paths so this runs in CPython in-place.
sys.path.append(os.path.join(sys.path[0], ".."))
from adafruit_bitmap_font import bitmap_font  # pylint: disable=wrong-import-position

sys.path.append(os.path.join(sys.path[0], "../test"))
font = bitmap_font.load_font(sys.argv[1])

_, height, _, dy = font.get_bounding_box()
for y in range(height):
    for c in "Adafruit CircuitPython":
        glyph = font.get_glyph(ord(c))
        if not glyph:
            continue
        glyph_y = y + (glyph.height - (height + dy)) + glyph.dy
        pixels = []
        if 0 <= glyph_y < glyph.height:
            for i in range(glyph.width):
                value = glyph.bitmap[i, glyph_y]
                pixel = " "
                if value > 0:
                    pixel = "#"
                pixels.append(pixel)
        else:
            pixels = ""
        print("".join(pixels) + " " * (glyph.shift_x - len(pixels)), end="")
    print()
