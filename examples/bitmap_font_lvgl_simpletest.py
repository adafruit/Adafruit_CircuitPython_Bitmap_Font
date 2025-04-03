# SPDX-FileCopyrightText: 2025 Scott Shawcroft for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
This example demonstrates loading and using an LVGL format font.
You can convert fonts to LVGL format using the online converter:
https://lvgl.io/tools/fontconverter
"""

from adafruit_bitmap_font import bitmap_font

# Use the Japanese font file
font_file = "fonts/unifont-16.0.02-ja.bin"

font = bitmap_font.load_font(font_file)
print("Successfully loaded LVGL font")
print("Font metrics:")
print(f"  Ascent: {font.ascent}")
print(f"  Descent: {font.descent}")
bbox = font.get_bounding_box()
print(f"  Bounding box: width={bbox[0]}, height={bbox[1]}, x_offset={bbox[2]}, y_offset={bbox[3]}")

# Test characters
test_japanese = "a こんにちは世界🎉"  # Hello World in Japanese (according to Claude)
print(f"\nTesting characters: {test_japanese}")
font.load_glyphs(test_japanese)
for c in test_japanese:
    glyph = font.get_glyph(ord(c))
    if glyph:
        print(f"  Character '{c}' (U+{ord(c):04X}):")  # Print ASCII art representation of the glyph
        for y in range(glyph.height):
            pixels = []
            for x in range(glyph.width):
                value = glyph.bitmap[x, y]
                pixel = "#" if value > 0 else " "
                pixels.append(pixel)
            print("    " + "".join(pixels))
    else:
        print(f"  Character '{c}' (U+{ord(c):04X}) not found in font")
