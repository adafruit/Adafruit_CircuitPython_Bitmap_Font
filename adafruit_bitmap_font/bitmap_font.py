import sys

def load_font(filename, bitmap=None):
    if not bitmap:
        import displayio
        bitmap = displayio.Bitmap
    f = open(filename, "rb")
    first_four = f.read(4)
    #print(first_four)
    if filename.endswith("bdf") and first_four == b"STAR":
        from . import bdf
        return bdf.BDF(f, bitmap)
    elif filename.endswith("pcf") and first_four == b"\x01fcp":
        import pcf
        return pcf.PCF(f)
    elif filename.endswith("ttf") and first_four == b"\x00\x01\x00\x00":
        import ttf
        return ttf.TTF(f)



if __name__ == "__main__":
    f = load_font(sys.argv[1])
    # print(f.characters)
    for c in "Adafruit CircuitPython":
        o = ord(c)
        if o not in f.characters:
            continue
        glyph = f.characters[o]
        print(glyph)
    for i in range(10):
        for c in "Adafruit CircuitPython":
            o = ord(c)
            if o not in f.characters:
                continue
            glyph = f.characters[o]
            # print(glyph)
            shifted_i = i + (glyph["bounds"][1] - 8) + glyph["bounds"][3]
            if 0 <= shifted_i < len(glyph["bitmap"]):
                pixels = glyph["bitmap"][shifted_i]
            else:
                pixels = ""
            print(pixels + " " * (glyph["shift"][0] - len(pixels)), end="")
        print()
