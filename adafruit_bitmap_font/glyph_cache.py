import gc
import collections

class GlyphCache:
    def __init__(self):
        self._glyphs = {}

    def get_glyph(self, code_point):
        if code_point in self._glyphs:
            return self._glyphs[code_point]

        s = set()
        s.add(code_point)
        self._glyphs[code_point] = None
        self.load_glyphs(s)
        gc.collect()
        return self._glyphs[code_point]
