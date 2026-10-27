"""Alarga la falda del cuerpo completo (hasta arriba de la rodilla) por inpaint de la zona cadera-muslo. Uso: fullbody_skirt.py <den> <semillas>"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
import comfy_tools as ct
OUT = Path("../concepts/vespera/body"); SRC = OUT / "out2_d100_s7101.png"
P = ("1girl, solo, vespera, full body, standing, black layered dress skirt with gold trim and a red ruffle hem, skirt covers the thighs and ends just above the knees, "
     "opaque black stockings below, black boots, flat color, cel shading with strong dark shadows, thick clean black lineart, extremely vivid saturated red and black, high contrast")
NEG = ", mini skirt, short skirt, bare thighs, bare skin, long skirt to the floor, cape, tassels, pale colors, washed out, extra legs"
def mask():
    im = Image.open(SRC); W, H = im.size
    m = np.zeros((H, W), np.uint8); m[int(H*0.36):int(H*0.66), int(W*0.10):int(W*0.90)] = 255
    Image.fromarray(m).filter(ImageFilter.GaussianBlur(6)).save(OUT / "_sk_mask.png")
def gen(seed, den):
    g = {"1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ct.CKPT}},
         "2": {"class_type": "CLIPTextEncode", "inputs": {"text": f"{P}, {ct.QUALITY}", "clip": ["1", 1]}},
         "3": {"class_type": "CLIPTextEncode", "inputs": {"text": ct.NEG + NEG, "clip": ["1", 1]}},
         "30": {"class_type": "LoadImage", "inputs": {"image": ct.upload(str(SRC))}},
         "31": {"class_type": "LoadImage", "inputs": {"image": ct.upload(str(OUT / "_sk_mask.png"))}},
         "32": {"class_type": "ImageToMask", "inputs": {"image": ["31", 0], "channel": "red"}},
         "4": {"class_type": "VAEEncode", "inputs": {"pixels": ["30", 0], "vae": ["1", 2]}},
         "33": {"class_type": "SetLatentNoiseMask", "inputs": {"samples": ["4", 0], "mask": ["32", 0]}},
         "5": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["33", 0],
               "seed": seed, "steps": 30, "cfg": 6.0, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": den}},
         "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
         "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": "devils/_sk"}}}
    dest = OUT / f"skirt_d{int(den*100)}_s{seed}.png"; ct.run(g, "7", str(dest))
    res = Image.open(dest).convert("RGB"); orig = Image.open(SRC).convert("RGB")
    Image.composite(res, orig, Image.open(OUT / "_sk_mask.png").convert("L")).save(dest); return dest
if __name__ == "__main__":
    mask()
    for s in sys.argv[2:]: print(gen(int(s), float(sys.argv[1])), flush=True)
