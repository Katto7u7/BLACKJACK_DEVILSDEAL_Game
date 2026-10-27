"""Cuerpo completo por outpaint: el busto aprobado (s604) queda INTACTO arriba y se dibuja solo lo de abajo.
Uso: fullbody_out.py <denoise> <semillas...>"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter
import comfy_tools as ct

BUST = Path("../concepts/vespera/bust/bust_v6_s604.png")
OUT = Path("../concepts/vespera/body"); W, H = 832, 1536
CUT, SC = 830, 0.52                       # corte del busto (justo bajo las manos) y escala

def prep():
    b = Image.open(BUST).convert("RGB").crop((0, 0, 1024, CUT))
    b = b.resize((int(1024 * SC), int(CUT * SC)), Image.LANCZOS)
    bg = Image.new("RGB", (W, H), tuple(np.array(b)[2, 2]))      # color del fondo del busto
    x0 = (W - b.width) // 2; bg.paste(b, (x0, 0))
    m = np.zeros((H, W), np.uint8); m[b.height - 10:, :] = 255
    m[:b.height - 10, :] = 0
    mask = Image.fromarray(m).filter(ImageFilter.GaussianBlur(3))
    bg.save(OUT / "_out_in.png"); mask.save(OUT / "_out_mask.png"); return b.height

P = ("1girl, solo, vespera, full body, standing, hands clasped together at the waist, "
     "black high-collar jacket with gold trim, black corset with gold lacing and gold buttons, red ruffled cuffs, black gloves, "
     "wide hips, narrow waist, thick thighs, layered black dress skirt with red ruffle hem, skirt length ends just above the knees, covers the thighs, opaque plain black thigh-high stockings, black ankle boots with gold details, "
     "flat color, cel shading with strong dark shadows, thick clean black lineart, extremely vivid saturated red and black, high contrast, plain background")
NEG = ", mini skirt, short skirt, bare thighs, pale colors, washed out, long skirt, cape, tassels, flared skirt, wide panniers, white blouse, epaulettes, garter belt, striped stockings, red stockings, nude, bare legs, mesh, see-through, cropped, out of frame, extra limbs, extra legs"

def gen(seed, den):
    g = {"1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ct.CKPT}},
         "2": {"class_type": "CLIPTextEncode", "inputs": {"text": f"{P}, {ct.QUALITY}", "clip": ["1", 1]}},
         "3": {"class_type": "CLIPTextEncode", "inputs": {"text": ct.NEG + NEG, "clip": ["1", 1]}},
         "30": {"class_type": "LoadImage", "inputs": {"image": ct.upload(str(OUT / "_out_in.png"))}},
         "31": {"class_type": "LoadImage", "inputs": {"image": ct.upload(str(OUT / "_out_mask.png"))}},
         "32": {"class_type": "ImageToMask", "inputs": {"image": ["31", 0], "channel": "red"}},
         "4": {"class_type": "VAEEncode", "inputs": {"pixels": ["30", 0], "vae": ["1", 2]}},
         "33": {"class_type": "SetLatentNoiseMask", "inputs": {"samples": ["4", 0], "mask": ["32", 0]}},
         "20": {"class_type": "LoadImage", "inputs": {"image": ct.upload(str(BUST))}},
         "21": {"class_type": "IPAdapterModelLoader", "inputs": {"ipadapter_file": "ip-adapter-plus_sdxl_vit-h.safetensors"}},
         "22": {"class_type": "CLIPVisionLoader", "inputs": {"clip_name": "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"}},
         "23": {"class_type": "IPAdapterAdvanced", "inputs": {"model": ["1", 0], "ipadapter": ["21", 0], "image": ["20", 0], "clip_vision": ["22", 0],
                "weight": 0.5, "weight_type": "style transfer", "combine_embeds": "concat", "start_at": 0.0, "end_at": 1.0, "embeds_scaling": "V only"}},
         "5": {"class_type": "KSampler", "inputs": {"model": ["23", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["33", 0],
               "seed": seed, "steps": 30, "cfg": 6.0, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": den}},
         "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
         "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": "devils/_out"}}}
    dest = OUT / f"out3_d{int(den*100)}_s{seed}.png"
    ct.run(g, "7", str(dest))
    # el busto original se restituye intacto (el VAE lo altera un poco)
    res = Image.open(dest).convert("RGB"); orig = Image.open(OUT / "_out_in.png").convert("RGB")
    m = Image.open(OUT / "_out_mask.png").convert("L")
    Image.composite(res, orig, m).save(dest); return dest

if __name__ == "__main__":
    prep()
    for s in sys.argv[2:]:
        print(gen(int(s), float(sys.argv[1])), flush=True)
