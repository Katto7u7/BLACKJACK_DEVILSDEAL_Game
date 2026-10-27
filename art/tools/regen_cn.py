"""Regenera el busto guiado por lineart (ControlNet Union) + IP-Adapter de Vespera.
Zona libre: donde se borra el lineart, el modelo dibuja segun el prompt (manos, etc.)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import cv2
from pathlib import Path
from PIL import Image
import comfy_tools as ct

BASE = Path("../concepts/vespera/bust/bust_base_v2.png")
CANON = Path("../concepts/vespera/ref/vespera_canon_v01.png")
OUT = Path("../work/vespera/polish")

def lineart(free_y=780, dest=OUT / "cn_lineart.png"):
    im = cv2.imread(str(BASE), cv2.IMREAD_GRAYSCALE)
    edges = cv2.Canny(cv2.GaussianBlur(im, (3, 3), 0), 60, 140)
    edges = cv2.dilate(edges, np.ones((2, 2), np.uint8))
    fade0 = free_y - 140
    ys = np.arange(edges.shape[0])[:, None]
    keep = np.clip((free_y - ys) / float(free_y - fade0), 0, 1)
    rnd = np.random.default_rng(5).random(edges.shape)
    edges = (edges * (rnd < keep)).astype(np.uint8)  # degradado: menos lineas hacia abajo, sin corte duro
    cv2.imwrite(str(dest), edges); return dest

def regen(seed, prompt, strength=0.8, ipw=0.45, free_y=780, name="cn", denoise=1.0, base=None, neg_extra=""):
    global BASE
    if base is not None:
        BASE = Path(base)
    lp = lineart(free_y)
    g = {"1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ct.CKPT}},
         "2": {"class_type": "CLIPTextEncode", "inputs": {"text": f"{prompt}, {ct.QUALITY}", "clip": ["1", 1]}},
         "3": {"class_type": "CLIPTextEncode", "inputs": {"text": ct.NEG + ", extra fingers, fused fingers, mutated hands, deformed breasts" + neg_extra, "clip": ["1", 1]}},
         "4": ({"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024, "batch_size": 1}} if denoise >= 1.0 else {"class_type": "VAEEncode", "inputs": {"pixels": ["30", 0], "vae": ["1", 2]}}),
         "30": {"class_type": "LoadImage", "inputs": {"image": ct.upload(str(BASE))}},
         "10": {"class_type": "ControlNetLoader", "inputs": {"control_net_name": "controlnet-union-sdxl-promax.safetensors"}},
         "11": {"class_type": "SetUnionControlNetType", "inputs": {"control_net": ["10", 0], "type": "canny/lineart/anime_lineart/mlsd"}},
         "12": {"class_type": "LoadImage", "inputs": {"image": ct.upload(str(lp))}},
         "13": {"class_type": "ControlNetApplyAdvanced", "inputs": {"positive": ["2", 0], "negative": ["3", 0], "control_net": ["11", 0],
                "image": ["12", 0], "strength": strength, "start_percent": 0.0, "end_percent": 0.85}},
         "20": {"class_type": "LoadImage", "inputs": {"image": ct.upload(str(CANON))}},
         "21": {"class_type": "IPAdapterModelLoader", "inputs": {"ipadapter_file": "ip-adapter-plus_sdxl_vit-h.safetensors"}},
         "22": {"class_type": "CLIPVisionLoader", "inputs": {"clip_name": "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"}},
         "23": {"class_type": "IPAdapterAdvanced", "inputs": {"model": ["1", 0], "ipadapter": ["21", 0], "image": ["20", 0], "clip_vision": ["22", 0],
                "weight": ipw, "weight_type": "style transfer", "combine_embeds": "concat", "start_at": 0.0, "end_at": 1.0, "embeds_scaling": "V only"}},
         "5": {"class_type": "KSampler", "inputs": {"model": ["23", 0], "positive": ["13", 0], "negative": ["13", 1], "latent_image": ["4", 0],
               "seed": seed, "steps": 30, "cfg": 6.0, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": denoise}},
         "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
         "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": "devils/_cn"}}}
    dest = OUT / f"{name}_s{seed}.png"
    ct.run(g, "7", str(dest)); return dest

PROMPT = ("1girl, vespera, demon girl, long jet black hair with red streaks, wide black horns, red eyes, crazed sharp-toothed grin, "
          "black corset bodice with gold trim, keyhole neckline, ruffled red cuffs, leaning on a table with hands clasped together in front, "
          "gloved hands with clearly drawn fingers, flat color, cel shading, thick clean black lineart, vivid red and black, upper body")

if __name__ == "__main__":
    for s in sys.argv[1:]:
        print(regen(int(s), PROMPT, name="cn"), flush=True)
