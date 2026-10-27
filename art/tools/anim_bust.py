"""Simulacion de movimiento del busto de Vespera (muelles, parpadeo, labios, reacciones).

Genera un GIF de previsualizacion y escribe motion_spec.json con los parametros que
usara Godot. Las transformaciones se calculan sobre las capas del rig (vespera_rig).
"""
import json
import math
import random
from pathlib import Path
import numpy as np
from PIL import Image
import vespera_rig as rig

OUT = rig.WORK.parent / "anim"
OUT.mkdir(exist_ok=True)
R = 1024                      # resolucion de simulacion
FPS = 24
DT = 1.0 / FPS
HEAD_PIVOT = (512, 500)       # cuello
BODY_PIVOT = (512, 1000)


def small(im):
    return im.resize((R, R), Image.LANCZOS)


PARTS = {p: small(rig.part_image(p)) for p in rig.ORDER}
STATES = {}
for part, names in rig._states.items():
    for nm in names:
        s = rig._states[part][nm]
        layer = Image.new("RGBA", (rig.SIZE, rig.SIZE), (0, 0, 0, 0))
        for l in sorted(s["layers"], key=lambda l: rig.RANK[l["group"]]):
            layer.alpha_composite(rig.img(rig.WORK / "layers_expr" / l["file"]), (s["x"], s["y"]))
        STATES[(part, nm)] = small(layer)


from PIL import ImageFilter, ImageChops, ImageDraw


def make_ring(im, grow=7, color=(168, 34, 58), thin_open=0):
    a = im.split()[3]
    if thin_open:  # quita lineas finas (mechones sueltos) antes de calcular el contorno
        a = a.filter(ImageFilter.MinFilter(thin_open)).filter(ImageFilter.MaxFilter(thin_open))
    big = a.filter(ImageFilter.MaxFilter(grow))
    ring = ImageChops.subtract(big, a).filter(ImageFilter.GaussianBlur(1.2))
    out = Image.new("RGBA", im.size, color + (0,))
    out.putalpha(ring.point(lambda v: min(255, int(v * 1.6))))
    return out


RINGS = {p: make_ring(PARTS[p], thin_open=(17 if p.startswith('pelo') else 0)) for p in PARTS}


def _hide_covered(rings, parts):
    """Quita el contorno de cada parte donde otra parte (pose de reposo) ya lo tapa: evita lineas en las costuras."""
    for p in rings:
        others = None
        for q in parts:
            if q == p:
                continue
            al = parts[q].split()[3]
            others = al if others is None else ImageChops.lighter(others, al)
        cover = others.filter(ImageFilter.MaxFilter(11)).point(lambda v: 255 if v > 200 else 0)
        r = rings[p]; ra = r.split()[3]
        r.putalpha(ImageChops.subtract(ra, cover))
    return rings


RINGS = _hide_covered(RINGS, PARTS)


def backdrop():
    """Fondo de casino procedural: degradado vino, bokeh calido y mesa oscura con borde dorado."""
    import random as _r
    rr = _r.Random(3)
    bg = Image.new("RGBA", (R, R), (24, 8, 16, 255))
    px = np.zeros((R, R, 3), np.float32)
    yy = np.linspace(0, 1, R)[:, None]
    px[..., 0] = 34 + 40 * (1 - yy); px[..., 1] = 8 + 10 * (1 - yy); px[..., 2] = 20 + 18 * (1 - yy)
    bg = Image.fromarray(px.astype(np.uint8), "RGB").convert("RGBA")
    glow = Image.new("RGBA", (R, R), (0, 0, 0, 0))
    d = ImageDraw.Draw(glow)
    for _ in range(26):
        x, y, r = rr.randint(0, R), rr.randint(20, 520), rr.randint(14, 46)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(255, rr.randint(140, 190), 70, rr.randint(26, 70)))
    bg.alpha_composite(glow.filter(ImageFilter.GaussianBlur(6)))
    return bg


def table():
    t = Image.new("RGBA", (R, R), (0, 0, 0, 0))
    d = ImageDraw.Draw(t)
    d.polygon([(0, 862), (R, 862), (R, R), (0, R)], fill=(26, 8, 14, 255))
    d.line([(0, 862), (R, 862)], fill=(196, 150, 70, 255), width=5)
    d.line([(0, 882), (R, 882)], fill=(120, 24, 40, 255), width=3)
    return t


BACK, TABLE = backdrop(), table()


class Spring:
    def __init__(self, k, c, x=0.0):
        self.k, self.c, self.x, self.v = k, c, x, 0.0

    def step(self, target, dt=DT, sub=4):
        h = dt / sub
        for _ in range(sub):
            a = self.k * (target - self.x) - self.c * self.v
            self.v += a * h
            self.x += self.v * h
        return self.x

    def kick(self, dv):
        self.v += dv


def xform(im, dx=0.0, dy=0.0, rot=0.0, pivot=HEAD_PIVOT, scale=1.0):
    if rot == 0 and scale == 1.0:
        return im.transform(im.size, Image.AFFINE, (1, 0, -dx, 0, 1, -dy), resample=Image.BILINEAR)
    # escala + rotacion alrededor del pivote, luego traslacion
    c, s = math.cos(math.radians(-rot)), math.sin(math.radians(-rot))
    px, py = pivot
    a, b, d, e = c / scale, -s / scale, s / scale, c / scale
    cx = px - a * (px + dx) - b * (py + dy)
    cy = py - d * (px + dx) - e * (py + dy)
    return im.transform(im.size, Image.AFFINE, (a, b, cx, d, e, cy), resample=Image.BILINEAR)


def sway_rows(im, amp):
    if abs(amp) < 0.05:
        return im
    arr = np.asarray(im)
    out = np.empty_like(arr)
    for y in range(R):
        k = max(0.0, min(1.0, (y - 250) / 600.0))
        s = int(round(amp * k))
        out[y] = np.roll(arr[y], s, axis=0) if s else arr[y]
    return Image.fromarray(out, "RGBA")


# ---- linea de tiempo de la escena (segundos) ----
# expresion: (t_inicio, ojos, boca)
TIMELINE = [
    (0.0, "base", "base"),
    (2.0, "e_smug", "m_smirk"),      # encanto / se inclina
    (4.4, "e_shock", "m_o"),         # sorpresa
    (5.6, "e_angry", "m_pout"),      # celos
    (7.0, "e_happy", "m_laugh"),     # burla / risa
    (9.0, "base", "base"),
]
EVENTS = [  # (tiempo, nombre)
    (2.0, "lean_in"), (4.4, "recoil"), (7.0, "laugh"),
]
TALK = [(2.6, 4.2)]               # intervalos de habla (sincronia labial)
DURATION = 10.0


def expr_at(t):
    cur = TIMELINE[0]
    for e in TIMELINE:
        if t >= e[0]:
            cur = e
    return cur[1], cur[2]


def talking(t):
    return any(a <= t < b for a, b in TALK)


def main():
    random.seed(7)
    head_x, head_y, head_r = Spring(60, 9), Spring(60, 9), Spring(50, 7)
    body_y = Spring(40, 8)
    hair = Spring(26, 2.2)
    lean = Spring(30, 6)
    n = int(DURATION * FPS)
    next_blink = 1.2
    blink_t = -1.0
    frames, log = [], []
    for i in range(n):
        t = i * DT
        for et, name in EVENTS:
            if abs(t - et) < DT / 2:
                if name == "lean_in":
                    lean.kick(40); head_r.kick(-18)
                elif name == "recoil":
                    lean.kick(-110); head_y.kick(-120); hair.kick(240)
                elif name == "laugh":
                    head_y.kick(-60); hair.kick(-160)
        # objetivo de mirada: cursor oscilando de izquierda a derecha
        cur = 40 * math.sin(t * 0.9)
        tx = head_x.step(cur * 0.5)
        ty = head_y.step(0.0 + (-10 if 7.0 <= t < 8.6 and int(t * 10) % 2 else 0))
        tr = head_r.step(cur * 0.03)
        ln = lean.step(10 if 2.0 <= t < 4.4 else 0)
        breath = math.sin(t * 2 * math.pi / 3.2)
        by = body_y.step(breath * 5)
        # el pelo se mueve por la aceleracion de la cabeza
        hs = hair.step(-head_x.v * 0.05 + breath * 2)
        # parpadeo aleatorio
        if t >= next_blink:
            blink_t = t; next_blink = t + random.uniform(2.0, 5.0)
        blinking = 0 <= t - blink_t < 0.16
        ojos, boca = expr_at(t)
        if blinking and ojos in ("base", "e_smug", "e_shock", "e_angry", "e_sad"):
            ojos = "e_blink"
        if talking(t):
            boca = ["m_soft", "m_o", "m_shout", "m_o", "m_soft", "m_smirk"][int((t - 2.6) * 9) % 6]
        # ---- composicion ----
        c = BACK.copy()
        hx, hy = tx * 0.3, ty * 0.3 + by * 0.4 + ln
        # (clave, transformacion) de cada parte, de atras hacia delante
        def T_head6(im): return xform(im, tx * 0.3, ty * 0.3 + ln * 0.4, tr, HEAD_PIVOT)
        def T_hair_b(im): return sway_rows(xform(im, tx * 0.2, by * 0.5, 0, BODY_PIVOT), hs)
        def T_torso(im): return xform(im, tx * 0.1, by + ln * 0.6, 0, BODY_PIVOT, 1 + 0.004 * breath)
        def T_hair_f(im): return sway_rows(xform(im, tx * 0.1, by + ln * 0.6, 0, BODY_PIVOT), hs * 0.5)
        def T_hand(im): return xform(im, 0, by * 0.5 + ln * 0.3)
        def T_head(im): return xform(im, hx, hy, tr, HEAD_PIVOT)
        stack = [("cuerno_izq", T_head6), ("cuerno_der", T_head6), ("pelo_trasero", T_hair_b), ("torso", T_torso),
                 ("pelo_frente", T_hair_f), ("mano_izq", T_hand), ("mano_der", T_hand), ("cabeza", T_head)]
        for key, T in stack:                      # contornos primero (quedan detras de todo)
            c.alpha_composite(T(RINGS[key]))
        for key, T in stack:
            c.alpha_composite(T(PARTS[key]))
        for im in (STATES[("ojos", ojos)], STATES[("boca", boca)]):
            c.alpha_composite(T_head(im))
        c.alpha_composite(TABLE)
        frames.append(c.convert("RGB"))
        log.append({"t": round(t, 3), "eyes": ojos, "mouth": boca})
    gif = [f.crop((40, 0, 984, 900)).resize((472, 450), Image.LANCZOS) for f in frames]
    gif[0].save(OUT / "vespera_bust_reactions.gif", save_all=True, append_images=gif[1:], duration=int(1000 / FPS), loop=0)
    for t in (1.0, 3.2, 4.6, 5.8, 7.4, 8.0):
        frames[int(t * FPS)].crop((40, 0, 984, 900)).save(OUT / f"bust_f{int(t*10):03d}.png")
    json.dump({
        "fps": FPS, "resolucion_sim": R, "pivote_cabeza": HEAD_PIVOT, "pivote_cuerpo": BODY_PIVOT,
        "muelles": {"cabeza_xy": {"k": 60, "c": 9}, "cabeza_rot": {"k": 50, "c": 7}, "cuerpo_resp": {"k": 40, "c": 8},
                    "pelo": {"k": 26, "c": 2.2}, "inclinacion": {"k": 30, "c": 6}},
        "parpadeo": {"intervalo_s": [2.0, 5.0], "duracion_s": 0.16},
        "labios": {"secuencia": ["m_soft", "m_o", "m_shout", "m_o", "m_soft", "m_smirk"], "hz": 9},
        "reacciones": {"lean_in": "kick inclinacion +40, rot -18", "recoil": "inclinacion -110, cabeza_y -120, pelo +240",
                       "laugh": "cabeza_y -60, pelo -160"},
        "linea_tiempo_demo": TIMELINE,
    }, open(OUT / "motion_spec.json", "w"), indent=1)
    print("ok", len(frames))


if __name__ == "__main__":
    main()
