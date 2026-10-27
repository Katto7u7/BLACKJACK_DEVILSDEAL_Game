"""Previsualizacion del rig v6 de Vespera: muelles (cabeza/cuerpo/pelo), parpadeo, habla, reacciones y cambio de expresion."""
import sys, os, json, math, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter, ImageDraw

ART = Path(__file__).resolve().parent.parent
G = ART.parent / "game/assets/vespera/rig_v6"
OUT = ART / "work/vespera/anim_v6"; OUT.mkdir(parents=True, exist_ok=True)
R, FPS = 1024, 24
DT = 1 / FPS
rig = json.load(open(G / "rig.json"))
K = R / rig["tam"]
HEAD_PIVOT = (512, 470)
BODY_PIVOT = (512, 1000)

def load(p): return Image.open(p).convert("RGBA").resize((R, R), Image.LANCZOS)
BODY = load(G / "cuerpo.png")
HEADS = {n: load(G / f"cabeza_{n}.png") for n in rig["expresiones"]}
PATCH = {}
for n, (x, y, w, h) in rig["parches"].items():
    im = Image.open(G / f"parche_{n}.png").convert("RGBA")
    PATCH[n] = (im.resize((max(1, int(w * K)), max(1, int(h * K))), Image.LANCZOS), (int(x * K), int(y * K)))

def backdrop():
    rr = random.Random(3)
    px = np.zeros((R, R, 3), np.float32); yy = np.linspace(0, 1, R)[:, None]
    px[..., 0] = 34 + 40 * (1 - yy); px[..., 1] = 8 + 10 * (1 - yy); px[..., 2] = 20 + 18 * (1 - yy)
    bg = Image.fromarray(px.astype(np.uint8), "RGB").convert("RGBA")
    glow = Image.new("RGBA", (R, R), (0, 0, 0, 0)); d = ImageDraw.Draw(glow)
    for _ in range(26):
        x, y, r = rr.randint(0, R), rr.randint(20, 640), rr.randint(14, 46)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, rr.randint(140, 190), 70, rr.randint(26, 70)))
    bg.alpha_composite(glow.filter(ImageFilter.GaussianBlur(6))); return bg
BACK = backdrop()

class Spring:
    def __init__(self, k, c): self.k, self.c, self.x, self.v = k, c, 0.0, 0.0
    def step(self, target, sub=4):
        h = DT / sub
        for _ in range(sub):
            self.v += (self.k * (target - self.x) - self.c * self.v) * h; self.x += self.v * h
        return self.x
    def kick(self, dv): self.v += dv

def xform(im, dx=0.0, dy=0.0, rot=0.0, pivot=HEAD_PIVOT, scale=1.0):
    c, s = math.cos(math.radians(-rot)), math.sin(math.radians(-rot)); px, py = pivot
    a, b, d, e = c / scale, -s / scale, s / scale, c / scale
    cx = px - a * (px + dx) - b * (py + dy); cy = py - d * (px + dx) - e * (py + dy)
    return im.transform(im.size, Image.AFFINE, (a, b, cx, d, e, cy), resample=Image.BICUBIC)

TIMELINE = [(0.0, "base"), (1.4, "encanto"), (3.0, "arrogancia"), (4.8, "sorpresa"), (5.8, "enfado"),
            (7.0, "burla"), (8.4, "locura"), (9.4, "base")]
EVENTS = [(1.4, "lean_in"), (4.8, "recoil"), (5.8, "anger"), (7.0, "laugh"), (8.4, "laugh")]
TALK = [(3.1, 4.6), (5.9, 6.9)]
DURATION = 10.5
TALKSEQ = ["talk_b", "talk_a", "talk_c", "talk_a", "talk_b", "talk_c"]

def expr_at(t):
    cur = TIMELINE[0][1]
    for ts, n in TIMELINE:
        if t >= ts: cur = n
    return cur

def main():
    random.seed(11)
    hx, hy, hr = Spring(60, 9), Spring(60, 9), Spring(50, 7)
    by, lean, hair = Spring(40, 8), Spring(30, 6), Spring(26, 2.5)
    next_blink, blink_t = 1.0, -1.0
    frames = []
    for i in range(int(DURATION * FPS)):
        t = i * DT
        for et, name in EVENTS:
            if abs(t - et) < DT / 2:
                if name == "lean_in": lean.kick(40); hr.kick(-14)
                elif name == "recoil": lean.kick(-110); hy.kick(-90); hair.kick(160)
                elif name == "anger": hx.kick(30); hy.kick(60); lean.kick(60)
                elif name == "laugh": hy.kick(-50); hair.kick(-120)
        cur = 28 * math.sin(t * 0.9)
        tx = hx.step(cur * 0.4)
        ty = hy.step(0.0)
        tr = hr.step(cur * 0.025)
        ln = lean.step(8 if 1.4 <= t < 3.0 else 0)
        breath = math.sin(t * 2 * math.pi / 3.2)
        bb = by.step(breath * 3)
        hs = hair.step(-hx.v * 0.04 + breath * 1.5)
        if t >= next_blink: blink_t, next_blink = t, t + random.uniform(2.0, 4.5)
        expr = expr_at(t)
        patches = []
        if 0 <= t - blink_t < 0.14 and expr not in ("burla", "locura", "sorpresa", "enfado"): patches.append("blink")
        talking = False
        for a, b in TALK:
            if a <= t < b:
                talking = True
                if expr not in ("enfado", "burla", "locura", "sorpresa"):   # esas ya tienen la boca abierta
                    patches.append(TALKSEQ[int((t - a) * 9) % 6])
        if talking: ty = ty + 3 * math.sin(t * 2 * math.pi * 9)             # pequeño rebote de mandibula
        head = HEADS[expr].copy()
        for p in patches:                       # parches dentro de la cabeza, antes de moverla
            im, pos = PATCH[p]; head.alpha_composite(im, pos)
        c = BACK.copy()
        body = xform(BODY, tx * 0.08, bb + ln * 0.5, 0, BODY_PIVOT, 1 + 0.003 * breath)
        c.alpha_composite(body)
        c.alpha_composite(xform(head, tx * 0.3, ty * 0.3 + bb * 0.5 + ln * 0.5, tr, HEAD_PIVOT))
        frames.append(c.convert("RGB"))
    box = (0, 0, 1024, 940)
    gif = [f.crop(box).resize((512, 470), Image.LANCZOS) for f in frames]
    gif[0].save(OUT / "vespera_rig_v6.gif", save_all=True, append_images=gif[1:], duration=int(1000 / FPS), loop=0)
    for tt in (0.5, 2.0, 3.6, 5.1, 6.2, 7.6, 8.9):
        frames[int(tt * FPS)].crop(box).save(OUT / f"f_{int(tt*10):03d}.png")
    json.dump({"fps": FPS, "pivote_cabeza": HEAD_PIVOT, "pivote_cuerpo": BODY_PIVOT,
               "muelles": {"cabeza_xy": [60, 9], "cabeza_rot": [50, 7], "cuerpo": [40, 8], "inclinacion": [30, 6], "pelo": [26, 2.5]},
               "parpadeo": {"intervalo_s": [2.0, 4.5], "duracion_s": 0.14}, "habla": {"secuencia": TALKSEQ, "hz": 9},
               "factores": {"cabeza_seguir": 0.3, "cuerpo_seguir": 0.08, "rotacion": 0.025},
               "linea_tiempo_demo": TIMELINE}, open(G / "motion_spec.json", "w"), indent=1)
    print("ok", len(frames))

if __name__ == "__main__":
    main()
