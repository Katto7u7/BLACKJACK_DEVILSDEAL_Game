"""Falda larga (arriba de la rodilla) por guia dibujada: se pinta la silueta en la base, Canny la convierte en lineart y se regenera con ControlNet."""
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
from PIL import Image, ImageDraw
import regen_cn as r
r.CANON = Path("../concepts/vespera/bust/bust_v6_s604.png"); r.OUT = Path("../concepts/vespera/body")
SRC = Path("../concepts/vespera/body/out2_d100_s7101.png")
def paint():
    im = Image.open(SRC).convert("RGB"); W, H = im.size; d = ImageDraw.Draw(im)
    top, hem = .40 * H, .60 * H
    pts = [(.30 * W, top), (.70 * W, top)]
    n = 10
    for i in range(n + 1):                      # dobladillo ondulado de derecha a izquierda
        x = .84 * W - i * (.68 * W / n); pts.append((x, hem + (14 if i % 2 else -6)))
    d.polygon(pts, fill=(26, 20, 24), outline=(0, 0, 0))
    band = [(x, y - 26) for x, y in pts[2:]] ; 
    d.polygon(pts[2:] + [(p[0], p[1] - 34) for p in reversed(pts[2:])], fill=(205, 30, 40))
    d.line([(.26 * W, top + 6), (.74 * W, top + 6)], fill=(222, 168, 113), width=5)
    p = Path("../concepts/vespera/body/_skirt_base.png"); im.save(p); return p
P = ("1girl, solo, vespera, demon girl, black high-collar jacket with gold trim, grey corset bodice, red ruffled cuffs, black gloves, "
     "black layered knee-length dress skirt with gold trim and red ruffle hem ending just above the knees, covers the thighs, opaque black stockings, black boots with gold, "
     "full body, standing, flat color, cel shading with strong dark shadows, thick clean black lineart, extremely vivid saturated red and black, high contrast, dark burgundy background")
if __name__ == "__main__":
    base = paint(); den = float(sys.argv[1])
    for s in sys.argv[2:]:
        print(r.regen(int(s), P, strength=0.85, ipw=0.5, free_y=3000, name=f"sk2_d{int(den*100)}", denoise=den, base=str(base),
                      neg_extra=", mini skirt, short skirt, bare thighs, bare skin, pale colors, washed out, pink background, panties"), flush=True)
