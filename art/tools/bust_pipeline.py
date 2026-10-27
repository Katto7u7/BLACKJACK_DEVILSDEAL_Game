"""Pipeline del busto de Vespera.

Trabaja a 4x (4096) con paleta fija y reduce cada capa a 2048 promediando
(bordes suaves). Genera capas por parte y grupo (linea / color / sombra_propia).

Uso (desde art/tools):  python bust_pipeline.py base      -> capas del busto base
Funciones reutilizables: classify(), part_masks(), save_layers()
"""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ART = Path(__file__).resolve().parents[1]
WORK = ART / "work" / "vespera" / "bust"
OUT = WORK / "layers"
S = 4            # factor de trabajo respecto a 1024
FINAL = 2048     # tamano de salida de capas

# nombre, colores origen (RGB del concepto), color final, grupo
ANCH = [
    ("linea", [(1, 1, 1), (26, 16, 13)], (10, 8, 10), "linea"),
    ("sombra", [(54, 37, 33)], (26, 18, 24), "sombra_propia"),
    ("ropa", [(76, 63, 59)], (52, 40, 48), "color"),
    ("pelo", [(106, 72, 73)], (36, 26, 34), "color"),
    ("rojo", [(223, 57, 47), (238, 62, 59)], (232, 38, 46), "color"),
    ("rojo_oscuro", [(151, 46, 41)], (150, 28, 40), "sombra_propia"),
    ("dorado", [(223, 168, 113)], (214, 160, 70), "color"),
    ("dorado_oscuro", [(156, 112, 82)], (160, 110, 52), "sombra_propia"),
    ("piel", [(247, 242, 236)], (250, 244, 238), "color"),
    ("gris", [(150, 133, 132), (113, 104, 101)], (52, 40, 48), "color"),
    ("rosa", [(240, 150, 150), (232, 120, 125), (246, 185, 180)], (236, 98, 118), "color"),
    ("fondo", [(205, 196, 193), (176, 169, 167)], None, None),
    ("mesa", [(179, 141, 129)], None, None),
]
NAMES = [a[0] for a in ANCH]
SRC = np.array([c for a in ANCH for c in a[1]], np.float32)
SRC_IDX = np.array([i for i, a in enumerate(ANCH) for _ in a[1]])
IDX = {n: i for i, n in enumerate(NAMES)}

# Zonas en coordenadas de 1024 (prioridad de arriba a abajo; lo demas = pelo_trasero / torso por regla)
RECTS = {
    "ojos": (375, 280, 660, 385),
    "boca": (435, 400, 590, 470),
}
POLYS = [
    ("cabeza", [(310, 95), (380, 60), (520, 55), (650, 80), (715, 170), (730, 330), (715, 400), (640, 450),
                (590, 490), (450, 490), (400, 450), (335, 400), (300, 300), (295, 180)]),
    ("cuerno_izq", [(135, 180), (190, 105), (300, 95), (350, 50), (372, 0), (420, 0), (410, 60), (380, 130),
                    (350, 170), (330, 230), (380, 300), (400, 350), (300, 340), (215, 290), (140, 215)]),
    ("cuerno_der", [(640, 0), (760, 0), (800, 70), (860, 130), (915, 220), (905, 275), (840, 345), (720, 350),
                    (700, 300), (720, 240), (700, 130)]),
    ("mano_izq", [(215, 820), (470, 820), (470, 1010), (215, 1010)]),
    ("mano_der", [(520, 820), (795, 820), (795, 1010), (520, 1010)]),
]
TORSO = [(240, 520), (300, 488), (440, 488), (590, 488), (720, 488), (790, 520), (840, 700), (890, 830),
         (915, 1010), (110, 1010), (130, 860), (190, 700)]
ORDER = ["cuerno_izq", "cuerno_der", "pelo_trasero", "torso", "pelo_frente", "mano_izq", "mano_der",
         "cabeza"]


def classify(rgb):
    """rgb uint8 (H,W,3) -> indice de clase por pixel (en bloques para ahorrar memoria)."""
    h, w, _ = rgb.shape
    out = np.empty((h, w), np.int8)
    step = 256
    for y in range(0, h, step):
        blk = rgb[y:y + step].astype(np.float32)
        d = ((blk[:, :, None, :] - SRC[None, None]) ** 2).sum(-1)
        out[y:y + step] = SRC_IDX[d.argmin(-1)]
    return out


def poly_mask(poly, size):
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).polygon([(x * S, y * S) for x, y in poly], fill=255)
    return np.asarray(m) > 0


def rect_mask(box, size, r=24):
    m = Image.new("L", (size, size), 0)
    x0, y0, x1, y1 = [v * S for v in box]
    ImageDraw.Draw(m).rounded_rectangle((x0, y0, x1, y1), radius=r * S, fill=255)
    return np.asarray(m) > 0


def alpha_and_cls(rgb4):
    """Clasifica y devuelve (cls, alpha bool). Quita fondo y mesa; fuerza linea en el borde exterior."""
    cls = classify(rgb4)
    bgc = (cls == IDX["fondo"]) | (cls == IDX["mesa"])
    lab, n = ndi.label(bgc)
    sizes = ndi.sum(bgc, lab, index=np.arange(1, n + 1))
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    big = {i + 1 for i, v in enumerate(sizes) if v > 150 * S * S / 4}
    remove = np.isin(lab, list(edge | big)) | (cls == IDX["mesa"])
    ring = ndi.binary_dilation(remove, iterations=6 * S // 2) & ~remove
    cls = np.where(ring, IDX["linea"], cls)
    cls = np.where((cls == IDX["fondo"]) & ~remove, IDX["piel"], cls)
    yy = np.arange(cls.shape[0])[:, None] / S
    xx = np.arange(cls.shape[1])[None, :] / S
    corner = (yy > 895) & ((xx < 100) | (xx > 925))
    remove = remove | corner
    return cls, ~remove


def save_layer(cls_mask, cls, dest):
    """Capa RGBA a 4x con los colores finales -> reducida a FINAL (promedio premultiplicado)."""
    h = cls.shape[0]
    rgba = np.zeros((h, h, 4), np.float32)
    for i, (n, _, tgt, g) in enumerate(ANCH):
        if tgt is None:
            continue
        m = cls_mask & (cls == i)
        rgba[m, :3] = tgt
        rgba[m, 3] = 255
    pre = rgba.copy(); pre[..., :3] *= pre[..., 3:4] / 255
    f = h // FINAL
    pre = pre.reshape(FINAL, f, FINAL, f, 4).mean(axis=(1, 3))
    a = pre[..., 3:4]
    rgb = np.where(a > 0, pre[..., :3] / np.maximum(a, 1e-6) * 255, 0)
    img = np.concatenate([np.clip(rgb, 0, 255), a], -1).astype(np.uint8)
    Image.fromarray(img, "RGBA").save(dest)
    return int((a > 0).sum())


def group_masks(cls):
    return {g: np.isin(cls, [i for i, a in enumerate(ANCH) if a[3] == g]) for g in ("color", "sombra_propia", "linea")}


def build_parts(cls, alpha):
    size = cls.shape[0]
    taken = np.zeros_like(alpha)
    parts = {}
    for n, poly in POLYS:
        m = poly_mask(poly, size) & alpha & ~taken
        parts[n] = m; taken |= m
    torso = poly_mask(TORSO, size) & alpha & ~taken
    x = np.arange(size)[None, :] / S
    hair_c = (cls == IDX["pelo"]) | ((cls == IDX["rojo"]) & ((x < 330) | (x > 700)))
    y = np.arange(size)[:, None] / S
    hair_c = hair_c & (y < 900)
    parts["pelo_frente"] = torso & hair_c
    parts["torso"] = torso & ~hair_c
    taken |= torso
    parts["pelo_trasero"] = alpha & ~taken
    # solapamiento minimo entre partes vecinas: evita costuras de antialias
    for k in list(parts):
        parts[k] = ndi.binary_dilation(parts[k], iterations=3) & alpha
    return parts


def majority(cls, n, size):
    """Filtro de mayoria sobre el mapa de clases (quita grano en bordes de color)."""
    best = np.zeros(cls.shape, np.float32); out = cls.copy()
    for k in range(n):
        f = ndi.uniform_filter((cls == k).astype(np.float32), size)
        m = f > best
        out[m] = k; best[m] = f[m]
    return out


def build_base():
    OUT.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("*.png"):
        f.unlink()
    rgb4 = np.asarray(Image.open(WORK / "base_4x.png").convert("RGB"))
    cls, alpha = alpha_and_cls(rgb4)
    cls = majority(cls, len(ANCH), 5)
    np.save(WORK / "cls4.npy", cls); np.save(WORK / "alpha4.npy", alpha)
    parts = build_parts(cls, alpha)
    gm = group_masks(cls)
    manifest = []
    for p in ORDER:
        for g, gmask in gm.items():
            cnt = save_layer(parts[p] & gmask, cls, OUT / f"{p}__{g}.png")
            if cnt:
                manifest.append({"part": p, "group": g, "file": f"{p}__{g}.png"})
            else:
                (OUT / f"{p}__{g}.png").unlink()
    json.dump(manifest, open(OUT / "manifest.json", "w"), indent=1)
    print(len(manifest), "capas")


if __name__ == "__main__":
    if sys.argv[1] == "base":
        build_base()


# ---------------------------------------------------------------------------
# Variantes de expresion (ojos / boca): recortes escalados a 4x, mismas reglas
# ---------------------------------------------------------------------------
CROPS = {"ojos": (360, 265, 676, 401), "boca": (420, 385, 604, 485)}  # coords 1024 (multiplos de 4)


def save_crop_layer(mask, cls, origin1024, dest):
    h, w = cls.shape
    rgba = np.zeros((h, w, 4), np.float32)
    for i, (n, _, tgt, g) in enumerate(ANCH):
        if tgt is None:
            continue
        m = mask & (cls == i)
        rgba[m, :3] = tgt; rgba[m, 3] = 255
    pre = rgba.copy(); pre[..., :3] *= pre[..., 3:4] / 255
    f = S // 2  # 4x -> 2x
    pre = pre.reshape(h // f, f, w // f, f, 4).mean(axis=(1, 3))
    a = pre[..., 3:4]
    rgb = np.where(a > 0, pre[..., :3] / np.maximum(a, 1e-6) * 255, 0)
    img = np.concatenate([np.clip(rgb, 0, 255), a], -1).astype(np.uint8)
    if not (a > 0).any():
        return 0
    Image.fromarray(img, "RGBA").save(dest)
    return int((a > 0).sum())


def build_variants(only=None):
    import comfy_tools as ct
    OUTV = WORK / "layers_expr"; OUTV.mkdir(exist_ok=True)
    states = {"ojos": {}, "boca": {}}
    VAR = WORK / "variants"
    items = {"ojos": ["base", "e_shock", "e_angry", "e_smug", "e_sad", "e_blink", "e_happy", "e_heart", "e_spiral"],
             "boca": ["base", "m_shout", "m_o", "m_smirk", "m_frown", "m_tongue", "m_laugh", "m_soft", "m_pout"]}
    for part, names in items.items():
        x0, y0, x1, y1 = CROPS[part]
        for nm in names:
            if only and nm not in only:
                continue
            src = Image.open(VAR / f"{nm}.png").convert("RGB").crop((x0, y0, x1, y1))
            tmp = WORK / "_crop_in.png"; src.save(tmp)
            up = WORK / "_crop_up.png"
            ct.upscale4x(str(tmp), str(up))
            big = Image.open(up).convert("RGB")
            cw, ch = (x1 - x0) * S, (y1 - y0) * S
            big = big.resize((cw, ch), Image.LANCZOS)
            cls = classify(np.asarray(big))
            # mascara del rect redondeado en coordenadas del recorte
            rx0, ry0, rx1, ry1 = [v * S for v in RECTS[part]]
            m = Image.new("L", (cw, ch), 0)
            ImageDraw.Draw(m).rounded_rectangle((rx0 - x0 * S, ry0 - y0 * S, rx1 - x0 * S, ry1 - y0 * S), radius=24 * S, fill=255)
            rm = np.asarray(m) > 0
            keep = rm & ~np.isin(cls, [IDX["fondo"], IDX["mesa"]])
            files = []
            for g, gm in group_masks(cls).items():
                fn = f"{part}_{nm}__{g}.png"
                if save_crop_layer(keep & gm, cls, (x0, y0), OUTV / fn):
                    files.append({"group": g, "file": fn})
            states[part][nm] = {"x": x0 * S // 2, "y": y0 * S // 2, "layers": files}
            print(part, nm, flush=True)
    json.dump(states, open(OUTV / "states.json", "w"), indent=1)


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "variants":
    build_variants()
