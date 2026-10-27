"""Genera capas por parte (linea / color / sombra_propia) y capas de sombras proyectadas.
Salida: work/vespera/layers_parts/*.png y order.json (de atras hacia delante).
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import parts

ROOT = Path(__file__).resolve().parents[1] / "work" / "vespera"
OUT = ROOT / "layers_parts"
OUT.mkdir(parents=True, exist_ok=True)
for f in OUT.glob("*.png"):
    f.unlink()

cut = np.asarray(Image.open(ROOT / "cutouts" / "body_canon.png").convert("RGBA"))
alpha = cut[..., 3] > 0
H, W = alpha.shape
idx = parts.partition((W, H))
names = [n for n, _ in parts.PARTS] + [parts.REST]
LAYERS = ROOT / "layers_body"
read = lambda n: np.asarray(Image.open(LAYERS / f"{n}.png").convert("RGBA"))
cl = {k: read(k) for k in ["negro_linea", "rojo", "rojo_oscuro", "dorado", "piel_blanco", "gris_sombra"]}
GROUPS = {"linea": ["negro_linea"], "color": ["rojo", "dorado", "piel_blanco"], "sombra_propia": ["rojo_oscuro", "gris_sombra"]}

# atras -> delante
ORDER = ["cuerno_izq", "cuerno_der", "pelo_trasero", "piernas", "falda", "torso", "brazo_der", "brazo_izq",
         "cabeza", "ojo_izq", "ojo_der", "boca"]
order = []
for part in ORDER:
    pi = names.index(part)
    for g, srcs in GROUPS.items():
        layer = np.zeros((H, W, 4), np.uint8)
        for s in srcs:
            m = (idx == pi) & (cl[s][..., 3] > 0)
            layer[m] = cl[s][m]
        if layer[..., 3].any():
            fn = f"{part}__{g}.png"
            Image.fromarray(layer, "RGBA").save(OUT / fn)
            order.append({"file": fn, "name": f"{part}_{g}", "group": part, "blend": "normal", "opacity": 255})

# ---- sombras proyectadas (multiply), sin tocar la linea negra ----
not_line = cl["negro_linea"][..., 3] == 0
def shadow(name, polys, blur=2.0, strength=150, color=(70, 8, 30)):
    m = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(m)
    for p in polys:
        d.polygon(p, fill=255)
    m = m.filter(ImageFilter.GaussianBlur(blur))
    a = (np.asarray(m).astype(np.float32) / 255 * strength) * (alpha & not_line)
    layer = np.zeros((H, W, 4), np.uint8)
    layer[..., :3] = color
    layer[..., 3] = a.astype(np.uint8)
    fn = f"sombra__{name}.png"
    Image.fromarray(layer, "RGBA").save(OUT / fn)
    order.append({"file": fn, "name": f"sombra_{name}", "group": "sombras", "blend": "multiply", "opacity": 255})

shadow("cuello_menton", [[(380, 236), (452, 236), (448, 262), (386, 262)]], blur=3)
shadow("pelo_sobre_pecho", [[(318, 262), (352, 262), (356, 360), (330, 400), (318, 330)],
                            [(470, 262), (505, 262), (518, 330), (505, 400), (480, 380)]], blur=3, strength=130)
shadow("bajo_pecho", [[(360, 345), (470, 345), (462, 372), (368, 372)]], blur=3, strength=110)
shadow("brazo_izq_sobre_torso", [[(335, 360), (372, 360), (372, 470), (340, 470)]], blur=3)
shadow("cintura_falda", [[(335, 468), (520, 468), (560, 510), (330, 515)]], blur=4, strength=140)
shadow("bajo_falda_piernas", [[(330, 690), (500, 690), (500, 735), (330, 735)]], blur=4, strength=150)
shadow("cabeza_sobre_cuernos", [[(318, 75), (505, 75), (505, 110), (318, 110)]], blur=4, strength=90)

json.dump(order, open(OUT / "order.json", "w"), indent=1)
print(len(order), "capas")
