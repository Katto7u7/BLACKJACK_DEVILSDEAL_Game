"""Quita el fondo liso de un concepto (flood desde el borde) y guarda PNG con alpha.
Uso: python cutout.py entrada.png salida.png [tolerancia]
"""
import sys
import numpy as np
from PIL import Image
from scipy import ndimage as ndi


def cutout(src, dst, tol=34):
    im = Image.open(src).convert("RGB")
    a = np.asarray(im).astype(np.int16)
    border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
    bg = np.median(border, axis=0)
    close = np.abs(a - bg).sum(axis=2) < tol * 3 / 2
    lab, n = ndi.label(close)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    sizes = ndi.sum(close, lab, index=np.arange(1, n + 1))
    big = {i + 1 for i, v in enumerate(sizes) if v > 120}
    bgmask = np.isin(lab, list(edge | big))
    # suaviza 1 px el borde para evitar halo
    bgmask = ndi.binary_dilation(bgmask, iterations=1) & close | bgmask
    alpha = np.where(bgmask, 0, 255).astype(np.uint8)
    alpha = ndi.binary_opening(alpha > 0, iterations=1).astype(np.uint8) * 255
    # rellena huecos pequenos dentro del personaje
    solid = alpha > 0
    out = np.dstack([np.asarray(im), np.where(solid, 255, 0).astype(np.uint8)])
    Image.fromarray(out, "RGBA").save(dst)
    return bg


if __name__ == "__main__":
    print(cutout(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 34))
