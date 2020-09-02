"""
This example runs on PyPortal, or any Circuit Python device
with a built-in screen that is at least 320x240 pixels.

It will use adafruit_bitmap_font to load a font and fill a
bitmap with pixels matching glyphs from a given String
"""


import board
import displayio
from adafruit_bitmap_font import bitmap_font

font = bitmap_font.load_font("fonts/Arial-16.bdf")

bitmap = displayio.Bitmap(320, 240, 2)

palette = displayio.Palette(2)

palette[0] = 0x000000
palette[1] = 0xFFFFFF

_, height, _, dy = font.get_bounding_box()
for y in range(height):
    pixels = []
    for c in "Adafruit CircuitPython":
        glyph = font.get_glyph(ord(c))
        if not glyph:
            continue
        glyph_y = y + (glyph.height - (height + dy)) + glyph.dy

        if 0 <= glyph_y < glyph.height:
            for i in range(glyph.width):
                value = glyph.bitmap[i, glyph_y]
                pixel = 0
                if value > 0:
                    pixel = 1
                pixels.append(pixel)
        else:
            # empty section for this glyph
            for i in range(glyph.width):
                pixels.append(0)

        # one space between glyph
        pixels.append(0)

    if pixels:
        for x, pixel in enumerate(pixels):
            bitmap[x, y] = pixel

# Create a TileGrid to hold the bitmap
tile_grid = displayio.TileGrid(bitmap, pixel_shader=palette)

# Create a Group to hold the TileGrid
group = displayio.Group()

group.x = 20
# Add the TileGrid to the Group
group.append(tile_grid)

# Add the Group to the Display
board.DISPLAY.show(group)

while True:
    pass
