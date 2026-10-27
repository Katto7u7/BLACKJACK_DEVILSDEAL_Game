"""Redibuja el pecho de Vespera (vectorial, supersampling 4x) sobre el busto base."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import numpy as np

SRC = Path("../concepts/vespera/bust/bust_base_s12003.png")
OUT = Path("../concepts/vespera/bust/bust_base_v2.png")
SS = 4
def P(cx, cy):                       # coords del recorte (x1.5, offset 260,430) -> 1024
    return (260 + cx / 1.5, 430 + cy / 1.5)

base = Image.open(SRC).convert("RGB")
a = np.asarray(base)
def samp(cx, cy):
    x, y = map(int, P(cx, cy)); return tuple(int(v) for v in np.median(a[y-2:y+3, x-2:x+3].reshape(-1, 3), axis=0))
SKIN, GOLD, CLOTH = (247, 242, 236), (223, 168, 113), (76, 63, 59)
LINE = (20, 10, 14); RED = (226, 52, 44)
SHADE = SKIN
print("colors", SKIN, GOLD, CLOTH)

W = 1024 * SS
lay = Image.new("RGBA", (W, W), (0, 0, 0, 0))
d = ImageDraw.Draw(lay)
def S(pts): return [(x * SS, y * SS) for x, y in (P(*p) for p in pts)]
def smooth(pts, n=14):               # curva Catmull-Rom suave
    pts = [pts[0]] + pts + [pts[-1]]; out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i-1], pts[i], pts[i+1], pts[i+2]
        for k in range(n):
            t = k / n
            out.append(tuple(0.5 * ((2*p1[j]) + (-p0[j]+p2[j])*t + (2*p0[j]-5*p1[j]+4*p2[j]-p3[j])*t*t + (-p0[j]+3*p1[j]-3*p2[j]+p3[j])*t**3) for j in (0, 1)))
    out.append(pts[-2]); return out

# 1) piel limpia bajo el borde dorado del escote
skin = [(112, 408), (200, 336), (282, 296), (350, 268), (420, 292), (520, 335), (606, 392), (652, 440), (660, 500), (80, 505)]
d.polygon(S(skin), fill=SKIN + (255,))
# sombra bajo el borde del escote
sh = smooth([(120, 412), (205, 345), (285, 306), (352, 280), (420, 303), (518, 346), (600, 402)], 10)
pass

LC = smooth([(82, 505), (118, 466), (172, 445), (232, 450), (288, 480), (332, 522), (352, 552)])
RC = smooth([(652, 488), (612, 452), (556, 436), (496, 443), (442, 472), (398, 516), (378, 552)])
# 2) volumen de los montículos: sombra interior junto al canalillo + curvas de contorno
for pts in ([(176, 438), (236, 424), (296, 446), (346, 492)], [(556, 436), (496, 424), (436, 444), (390, 490)],
            [(358, 430), (361, 470), (362, 508)], [(372, 430), (369, 470), (368, 508)]):
    seg = smooth(pts, 10); n = len(seg)
    for i in range(n - 1):                      # trazo cónico: más fino hacia el final
        w = max(1, int((3.2 - 2.2 * i / n) * SS))
        d.line(S(seg[i:i + 2]), fill=LINE + (255,), width=w)
# 3) copas (tela) con borde dorado
for edge, side in ((LC, "L"), (RC, "R")):
    poly = edge + (smooth([(352, 552), (305, 574), (200, 578), (112, 556), (82, 505)], 8) if side == "L" else smooth([(378, 552), (425, 574), (530, 578), (622, 556), (652, 488)], 8))
    d.polygon(S(poly), fill=CLOTH + (255,))
    d.line(S(edge), fill=LINE + (255,), width=17 * SS // 2, joint="curve")
    d.line(S(edge), fill=GOLD + (255,), width=10 * SS // 2, joint="curve")
    # brillo de tela
    hl = [(x, y + 26) for x, y in edge[2:-4]]
    d.line(S(hl[::2]), fill=(104, 88, 84) + (255,), width=3 * SS // 2, joint="curve")
# 4) colgante de cerradura pequeno
d.polygon(S([(365, 300), (386, 332), (365, 388), (344, 332)]), fill=LINE + (255,))
cx_, cy_ = P(365, 328)
d.ellipse([(cx_-6)*SS, (cy_-6)*SS, (cx_+6)*SS, (cy_+6)*SS], fill=RED + (255,))
d.polygon(S([(361, 336), (369, 336), (371, 368), (359, 368)]), fill=RED + (255,))

lay = lay.resize((1024, 1024), Image.LANCZOS)
out = base.convert("RGBA"); out.alpha_composite(lay)
out.convert("RGB").save(OUT)
out.crop((260, 430, 780, 900)).resize((780, 705)).convert("RGB").save("../work/vespera/polish/chest_v2_crop.png")
