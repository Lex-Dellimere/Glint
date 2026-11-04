#!/usr/bin/env python3
"""Make src/assets/glint_font.bin: ASCII 32..126 as 8x16 one-bit glyphs, for the
preview's error and status text. Rendered from DejaVu Sans Mono (Bitstream Vera
license, see NOTICE). Needs Pillow. The output is committed; run only to change it.
Layout: 95 glyphs, 16 rows each, one byte per row, bit 7 = leftmost pixel."""
import os, sys
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT = sys.argv[1] if len(sys.argv) > 1 else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
f = ImageFont.truetype(FONT, 13)
out = bytearray()
for c in range(32, 127):
    im = Image.new("L", (8, 16), 0)
    ImageDraw.Draw(im).text((0, 0), chr(c), font=f, fill=255)
    for y in range(16):
        b = 0
        for x in range(8):
            if im.getpixel((x, y)) >= 110:
                b |= 0x80 >> x
        out.append(b)
open(os.path.join(ROOT, "src", "assets", "glint_font.bin"), "wb").write(out)
print("fontgen: %d bytes" % len(out))
