"""
This example uses addfruit_display_text.label to display text using a custom font
loaded by adafruit_bitmap_font
"""

import board
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font

display = board.DISPLAY

# Set text, font, and color
text = "HELLO WORLD"
font = bitmap_font.load_font("fonts/Arial-16.bdf")
color = 0xFF00FF

# Create the tet label
text_area = label.Label(font, text=text, color=color)

# Set the location
text_area.x = 20
text_area.y = 20

# Show it
display.show(text_area)

while True:
    pass
