"""Reparte un recorte en partes por poligonos (prioridad de arriba a abajo; el resto = pelo_trasero)
y guarda un mapa de partes. Uso: python parts.py recorte.png carpeta_salida
Coordenadas en pixeles del recorte de Vespera de cuerpo completo (832x1216).
"""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

PARTS = [  # (nombre, poligono)
    ("ojo_izq", [(366, 162), (400, 162), (400, 196), (366, 196)]),
    ("ojo_der", [(426, 168), (472, 168), (472, 206), (426, 206)]),
    ("boca", [(383, 203), (454, 203), (454, 238), (383, 238)]),
    ("cuerno_izq", [(265, 0), (405, 0), (405, 85), (335, 100), (320, 170), (290, 168), (265, 110)]),
    ("cuerno_der", [(440, 0), (560, 0), (560, 178), (520, 180), (495, 125), (470, 85), (440, 85)]),
    ("cabeza", [(322, 80), (500, 80), (505, 190), (490, 250), (470, 264), (400, 264), (335, 252), (318, 180)]),
    ("brazo_izq", [(225, 335), (335, 335), (345, 400), (335, 480), (235, 470), (225, 400)]),
    ("brazo_der", [(495, 415), (560, 415), (560, 478), (495, 478)]),
    ("torso", [(310, 255), (500, 255), (520, 330), (505, 470), (335, 470), (318, 330)]),
    ("falda", [(335, 468), (520, 468), (600, 520), (690, 565), (738, 640), (722, 718), (190, 728), (174, 665), (215, 600), (282, 520)]),
    ("piernas", [(228, 690), (565, 690), (565, 1195), (228, 1195)]),
]
REST = "pelo_trasero"
COLORS = {"ojo_izq": (255, 255, 0), "ojo_der": (255, 200, 0), "boca": (255, 0, 255), "cuerno_izq": (0, 120, 255),
          "cuerno_der": (0, 200, 255), "cabeza": (255, 255, 255), "brazo_izq": (120, 255, 120),
          "brazo_der": (60, 200, 60), "torso": (255, 130, 0), "falda": (200, 80, 200), "piernas": (150, 150, 255),
          REST: (90, 40, 40)}


def partition(size):
    w, h = size
    idx = np.full((h, w), len(PARTS), dtype=np.int16)
    for i, (_, poly) in enumerate(PARTS):
        m = Image.new("L", size, 0)
        ImageDraw.Draw(m).polygon(poly, fill=255)
        idx = np.where((np.asarray(m) > 0) & (idx == len(PARTS)), i, idx)
    return idx


def main(src, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    im = Image.open(src).convert("RGBA")
    idx = partition(im.size)
    names = [n for n, _ in PARTS] + [REST]
    a = np.asarray(im)[..., 3] > 0
    vis = np.zeros((*idx.shape, 3), np.uint8)
    for i, n in enumerate(names):
        vis[(idx == i) & a] = COLORS[n]
    Image.fromarray(vis).save(out / "_mapa_partes.png")
    np.save(out / "partes_idx.npy", idx)
    json.dump(names, open(out / "partes.json", "w"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
