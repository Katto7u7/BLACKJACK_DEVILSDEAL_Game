"""Separa un recorte plano en capas por color (cada pixel va a la paleta mas cercana).
Uso: python split_colors.py recorte.png carpeta_salida
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

PALETTE = {
    "negro_linea": (14, 11, 13),
    "rojo": (225, 22, 28),
    "rojo_oscuro": (140, 14, 24),
    "dorado": (196, 156, 78),
    "piel_blanco": (252, 248, 246),
    "gris_sombra": (130, 125, 130),
}


def split(src, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    im = np.asarray(Image.open(src).convert("RGBA"))
    rgb = im[..., :3].astype(np.float32); alpha = im[..., 3]
    names = list(PALETTE)
    cols = np.array([PALETTE[n] for n in names], dtype=np.float32)
    d = ((rgb[:, :, None, :] - cols[None, None]) ** 2).sum(-1)
    idx = d.argmin(-1)
    recomposed = np.zeros_like(im)
    for i, n in enumerate(names):
        m = (idx == i) & (alpha > 0)
        layer = np.zeros_like(im)
        layer[m] = np.concatenate([cols[i].astype(np.uint8), [255]])
        Image.fromarray(layer, "RGBA").save(out / f"{n}.png")
        recomposed[m] = layer[m]
        print(n, int(m.sum()))
    Image.fromarray(recomposed, "RGBA").save(out / "_recompuesto.png")


if __name__ == "__main__":
    split(sys.argv[1], sys.argv[2])
