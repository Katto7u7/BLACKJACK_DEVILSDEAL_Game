"""Compositor del rig de Vespera (busto): partes base + estados de ojos/boca."""
import json
from pathlib import Path
from PIL import Image

WORK = Path(__file__).resolve().parents[1] / "work" / "vespera" / "bust"
SIZE = 2048
RANK = {"color": 0, "sombra_propia": 1, "linea": 2}
ORDER = ["cuerno_izq", "cuerno_der", "pelo_trasero", "torso", "pelo_frente", "mano_izq", "mano_der", "cabeza"]
_base = json.load(open(WORK / "layers" / "manifest.json"))
_states = json.load(open(WORK / "layers_expr" / "states.json"))
_cache = {}


def img(path):
    if path not in _cache:
        _cache[path] = Image.open(path).convert("RGBA")
    return _cache[path]


def part_image(p):
    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    for x in sorted([x for x in _base if x["part"] == p], key=lambda x: RANK[x["group"]]):
        out.alpha_composite(img(WORK / "layers" / x["file"]))
    return out


def state_image(part, name):
    s = _states[part][name]
    out = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    for l in sorted(s["layers"], key=lambda l: RANK[l["group"]]):
        out.alpha_composite(img(WORK / "layers_expr" / l["file"]), (s["x"], s["y"]))
    return out


def compose(eyes="base", mouth="base", bg=(19, 13, 15, 255), with_parts=None):
    c = Image.new("RGBA", (SIZE, SIZE), bg)
    for p in ORDER:
        c.alpha_composite(part_image(p))
    c.alpha_composite(state_image("ojos", eyes))
    c.alpha_composite(state_image("boca", mouth))
    return c


EXPRESSIONS = {
    "base": ("base", "base"), "encanto": ("e_smug", "m_smirk"), "malicia": ("base", "m_tongue"),
    "arrogancia": ("e_smug", "m_smirk"), "celos": ("e_angry", "m_pout"), "culpa": ("e_sad", "m_frown"),
    "vulnerable": ("e_sad", "m_soft"), "desesperacion": ("e_shock", "m_shout"), "sorpresa": ("e_shock", "m_o"),
    "enfado": ("e_angry", "m_shout"), "burla": ("e_happy", "m_laugh"), "ternura": ("e_happy", "m_soft"),
    "miedo": ("e_shock", "m_frown"), "obsesion": ("e_heart", "m_soft"), "locura": ("e_spiral", "m_laugh"),
}

if __name__ == "__main__":
    names = list(EXPRESSIONS)
    box = (500, 150, 1540, 1060)
    cols = 5
    tiles = [compose(*EXPRESSIONS[n]).crop(box).resize((416, 364), Image.LANCZOS) for n in names]
    sheet = Image.new("RGB", (416 * cols, 364 * ((len(tiles) + cols - 1) // cols)))
    for i, t in enumerate(tiles):
        sheet.paste(t.convert("RGB"), ((i % cols) * 416, (i // cols) * 364))
    sheet.save(WORK / "_expresiones.png")
    print("ok")
