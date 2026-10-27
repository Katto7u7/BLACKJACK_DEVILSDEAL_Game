"""Rig simplificado de Vespera v6: fondo, cuerpo (con cabeza retirada y relleno LaMa), cabeza por expresion, parches de parpadeo y habla.
Uso: python rig_v6.py up | build"""
import sys, os, json, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage as ndi
import comfy_tools as ct

ART = Path(__file__).resolve().parent.parent
EXPR = ART / "concepts/vespera/expr_v6"
FINAL = EXPR / "final"
PARTS = EXPR / "parts"
WORK = ART / "work/vespera/rig_v6"; UP = WORK / "up"
GAME = ART.parent / "game/assets/vespera/rig_v6"
S = 2                                  # 1024 -> 2048
PATCHES = {"blink": PARTS / "blink_812.png", "talk_a": PARTS / "talk_a_802.png",
           "talk_b": PARTS / "talk_b_801.png", "talk_c": PARTS / "talk_c_801.png"}
EYES = (385, 290, 655, 392); MOUTH = (440, 400, 590, 482)   # coords 1024

def sources():
    d = {p.stem.replace("vespera_", ""): p for p in FINAL.glob("vespera_*.png")}
    d.update({k: v for k, v in PATCHES.items()}); return d

def up():
    UP.mkdir(parents=True, exist_ok=True)
    for n, p in sources().items():
        dst = UP / f"{n}.png"
        if dst.exists(): continue
        tmp = WORK / f"_{n}_4x.png"; ct.upscale4x(str(p), str(tmp))
        Image.open(tmp).convert("RGB").resize((1024 * S, 1024 * S), Image.LANCZOS).save(dst); tmp.unlink(); print("up", n, flush=True)

def fg_mask(rgb):
    h, w, _ = rgb.shape
    edge = np.concatenate([rgb[:200, :40].reshape(-1, 3), rgb[:200, -40:].reshape(-1, 3)])
    bg = np.median(edge, axis=0)
    dist = np.sqrt(((rgb.astype(np.float32) - bg) ** 2).sum(-1))
    fg = dist > 26
    fg[int(852 * S):, :] = True        # la mesa forma parte del busto
    fg = ndi.binary_closing(fg, iterations=2)
    holes = ndi.binary_fill_holes(fg) & ~fg                  # huecos de fondo entre mechones se quedan transparentes
    lab, n = ndi.label(holes)
    if n:
        sizes = ndi.sum(holes, lab, range(1, n + 1))
        for i, sz in enumerate(sizes, 1):
            if sz < 600: fg |= lab == i                      # solo se rellenan los huecos pequenos
    lab, n = ndi.label(fg)
    if n > 1:
        sizes = ndi.sum(fg, lab, range(1, n + 1)); fg = lab == (1 + int(np.argmax(sizes)))
    return ndi.binary_erosion(fg, iterations=1)

def build():
    GAME.mkdir(parents=True, exist_ok=True)
    base = np.asarray(Image.open(UP / "base.png").convert("RGB"))
    fg = fg_mask(base)
    core = ndi.binary_erosion(fg, iterations=2)
    idx = ndi.distance_transform_edt(~core, return_distances=False, return_indices=True)
    def clean(img):                                   # pixeles fuera del nucleo copian el color interior mas cercano
        return img[idx[0], idx[1]]
    base = clean(base); fg = ndi.binary_dilation(core, iterations=1)
    h, w = fg.shape
    yy, xx = np.mgrid[0:h, 0:w]
    chin = (xx > 440 * S) & (xx < 590 * S)
    cut_y = np.where(chin, 1000, 940)                 # corte del cuello en coords 2048 (barbilla mas baja)
    reg = (yy < 700) | ((xx >= 300 * S) & (xx <= 740 * S) & (yy < cut_y)) | ((yy < 760) & ((xx < 330 * S) | (xx > 720 * S)))
    head = fg & reg
    ha = Image.fromarray((head * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.6))
    ha = np.asarray(ha).astype(np.float32) / 255
    ha = np.clip((ha - 0.5) * 2.2 + 0.5, 0, 1)
    # degradado en el corte del cuello y de los costados: la cabeza se funde con el cuerpo
    FD = 56
    zone = yy >= 700
    fx = np.where(yy >= 760, np.minimum(np.clip((xx - 300 * S) / FD, 0, 1), np.clip((740 * S - xx) / FD, 0, 1)), 1.0)
    fade = np.where(zone, np.minimum(np.clip((cut_y - yy) / FD, 0, 1), fx), 1.0)
    ha = ha * fade
    head_a = (ha * 255).astype(np.uint8)
    # cuerpo: quitar la cabeza y rellenar con LaMa (a 1024), solo donde hay cuerpo detras
    hole = ndi.binary_dilation(head, iterations=10 * S)
    small = Image.fromarray(base).resize((1024, 1024), Image.LANCZOS)
    mk = Image.fromarray((hole * 255).astype(np.uint8)).resize((1024, 1024), Image.NEAREST)
    small.save(WORK / "_body_in.png"); mk.save(WORK / "_body_mask.png")
    g = {"1": {"class_type": "LoadImage", "inputs": {"image": ct.upload(str(WORK / "_body_in.png"))}},
         "2": {"class_type": "LoadImage", "inputs": {"image": ct.upload(str(WORK / "_body_mask.png"))}},
         "3": {"class_type": "ImageToMask", "inputs": {"image": ["2", 0], "channel": "red"}},
         "4": {"class_type": "INPAINT_LoadInpaintModel", "inputs": {"model_name": "big-lama.pt"}},
         "5": {"class_type": "INPAINT_InpaintWithModel", "inputs": {"inpaint_model": ["4", 0], "image": ["1", 0], "mask": ["3", 0], "seed": 1}},
         "6": {"class_type": "SaveImage", "inputs": {"images": ["5", 0], "filename_prefix": "devils/_lama"}}}
    ct.run(g, "6", str(WORK / "_body_filled.png"))
    filled = Image.open(WORK / "_body_filled.png").convert("RGB").resize((w, h), Image.LANCZOS)
    fillzone = hole & (fade > 0.999)                                      # rellenar solo bajo la parte opaca de la cabeza
    body = np.where(fillzone[..., None], np.asarray(filled), base)
    keep = fg & ~(head & (yy < 700))                   # sobre el hombro no hay cuerpo
    keep = keep | (hole & fg & (yy >= 700))
    ba = Image.fromarray((keep * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))
    Image.fromarray(np.dstack([body, np.asarray(ba)]), "RGBA").save(GAME / "cuerpo.png")
    # cabezas por expresion
    names = []
    for n in sorted(p.stem for p in UP.glob("*.png")):
        if n in PATCHES: continue
        im = clean(np.asarray(Image.open(UP / f"{n}.png").convert("RGB")))
        Image.fromarray(np.dstack([im, head_a]), "RGBA").save(GAME / f"cabeza_{n}.png"); names.append(n)
    # parches (parpadeo / habla): recorte del rect con borde suave
    pm = {}
    for n, rect in (("blink", EYES), ("talk_a", MOUTH), ("talk_b", MOUTH), ("talk_c", MOUTH)):
        x0, y0, x1, y1 = [v * S for v in rect]
        im = Image.open(UP / f"{n}.png").convert("RGB").crop((x0, y0, x1, y1))
        m = Image.new("L", im.size, 0); m.paste(255, (14, 14, im.size[0] - 14, im.size[1] - 14)); m = m.filter(ImageFilter.GaussianBlur(7))
        im.putalpha(m); im.save(GAME / f"parche_{n}.png"); pm[n] = [x0, y0, x1 - x0, y1 - y0]
    json.dump({"tam": 1024 * S, "expresiones": names, "parches": pm, "pivote_cabeza": [512 * S, 500 * S]},
              open(GAME / "rig.json", "w"), indent=1)
    print("rig ok", len(names), "expresiones")

if __name__ == "__main__":
    {"up": up, "build": build}[sys.argv[1]]()
