"""Genera ojos cerrados y una animacion idle de previsualizacion (GIF + fotogramas) desde layers_parts."""
import json, math
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1] / "work" / "vespera"
L = ROOT / "layers_parts"
OUTD = ROOT / "anim"; OUTD.mkdir(exist_ok=True)
W, H = 832, 1216
SKIN = (252, 248, 246, 255)

def ld(fn): return Image.open(L / fn).convert("RGBA")

# --- ojos cerrados ---
for side in ("izq", "der"):
    col = np.asarray(ld(f"ojo_{side}__color.png"))[..., 3] > 0
    sh = np.asarray(ld(f"ojo_{side}__sombra_propia.png"))[..., 3] > 0
    ln = np.asarray(ld(f"ojo_{side}__linea.png"))[..., 3] > 0
    from scipy import ndimage as ndi
    m = ndi.binary_dilation(col | sh, iterations=3) & (ln | col | sh)
    ys, xs = np.nonzero(m)
    cx, cy = int(xs.mean()), int(ys.mean())
    x0, x1 = xs.min(), xs.max()
    lay = np.zeros((H, W, 4), np.uint8)
    lay[m] = SKIN
    im = Image.fromarray(lay, "RGBA")
    d = ImageDraw.Draw(im)
    pts = [(x0 + (x1 - x0) * t / 12, cy + 3 + 5 * math.sin(math.pi * t / 12)) for t in range(13)]
    d.line(pts, fill=(14, 11, 13, 255), width=3)
    im.save(L / f"ojo_{side}__cerrado.png")

# --- partes ---
PARTS = ["cuerno_izq", "cuerno_der", "pelo_trasero", "piernas", "falda", "torso", "brazo_der", "brazo_izq", "cabeza"]
def part_img(p):
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    for g in ("color", "sombra_propia", "linea"):
        f = L / f"{p}__{g}.png"
        if f.exists(): out.alpha_composite(Image.open(f).convert("RGBA"))
    return out
imgs = {p: part_img(p) for p in PARTS}
eyes = {s: {g: ld(f"ojo_{s}__{g}.png") for g in ("color", "sombra_propia", "linea", "cerrado")} for s in ("izq", "der")}
mouth = part_img("boca")
shadows = [(json.load(open(L / "order.json")))]
shad = [ld(o["file"]) for o in json.load(open(L / "order.json")) if o["group"] == "sombras"]

def shift(im, dx=0.0, dy=0.0, shear=0.0, scale_y=1.0, pivot_y=470):
    # transformacion afin inversa: salida(x,y) <- entrada
    a = 1; b = -shear / H * 0; 
    dx, dy = round(dx), round(dy)
    coeffs = (1, 0, -dx, 0, 1 / scale_y, -dy + pivot_y * (1 - 1 / scale_y))
    return im.transform(im.size, Image.AFFINE, coeffs, resample=Image.NEAREST)

def sway(im, t, amp=5.0):
    # el pelo se balancea mas abajo: cizalla horizontal dependiente de y
    arr = np.asarray(im); out = np.zeros_like(arr)
    for y in range(H):
        s = int(round(amp * math.sin(t) * max(0, (y - 150)) / 900))
        row = arr[y]
        out[y] = np.roll(row, s, axis=0) if s else row
    return Image.fromarray(out, "RGBA")

def frame(i, n=48):
    t = 2 * math.pi * i / n
    br = math.sin(t)
    blink = i in (30, 31, 32)
    c = Image.new("RGBA", (W, H), (19, 13, 15, 255))
    c.alpha_composite(shift(imgs["cuerno_izq"], dy=1.2 * br)); c.alpha_composite(shift(imgs["cuerno_der"], dy=1.2 * br))
    c.alpha_composite(sway(imgs["pelo_trasero"], t))
    c.alpha_composite(imgs["piernas"]); c.alpha_composite(imgs["falda"])
    body = shift(imgs["torso"], dy=0.8 * br, scale_y=1 + 0.006 * br, pivot_y=470)
    c.alpha_composite(body)
    c.alpha_composite(shift(imgs["brazo_der"], dy=0.8 * br)); c.alpha_composite(shift(imgs["brazo_izq"], dy=1.0 * br))
    hd = 2.0 * br
    c.alpha_composite(shift(imgs["cabeza"], dy=hd))
    for s in ("izq", "der"):
        e = eyes[s]
        if blink:
            c.alpha_composite(shift(e["linea"], dy=hd)); c.alpha_composite(shift(e["cerrado"], dy=hd))
        else:
            for g in ("color", "sombra_propia", "linea"): c.alpha_composite(shift(e[g], dy=hd))
    c.alpha_composite(shift(mouth, dy=hd))
    for s in shad: c.alpha_composite(s) if False else None
    return c

frames = [frame(i) for i in range(48)]
for i in (0, 12, 31, 36):
    frames[i].convert("RGB").crop((60, 0, 772, 760)).save(OUTD / f"idle_f{i:02d}.png")
frames[0].convert("RGB")
gif = [f.convert("RGB").crop((60, 0, 772, 780)).resize((356, 390)) for f in frames]
gif[0].save(OUTD / "vespera_idle_preview.gif", save_all=True, append_images=gif[1:], duration=50, loop=0)
print("ok", len(frames))
