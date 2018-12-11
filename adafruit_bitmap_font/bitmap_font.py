import sys

def load_font(filename):
    f = open(filename, "r")
    first_four = f.read(4)
    if filename.endswith("bdf") and first_four == "STAR":
        import bdf
        return bdf.BDF(f)
    elif filename.endswith("pcf") and first_four == "\x01fcp":
        import pcf
        return pcf.PCF(f)



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
