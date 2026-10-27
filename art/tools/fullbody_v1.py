"""Cuerpo completo de Vespera: txt2img SDXL + IP-Adapter (busto aprobado s604). Uso: fullbody_v1.py <ipw> <semillas...>"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import comfy_tools as ct

REF = Path("../concepts/vespera/bust/bust_v6_s604.png")
OUT = Path("../concepts/vespera/body"); OUT.mkdir(parents=True, exist_ok=True)
P = ("1girl, solo, vespera, evil seductive demon dealer, very attractive anime waifu, dominant unhinged manipulative aura, "
     "jet black hair with vivid red streaks, pure black hair, long hair, wide black horns with red stripes, glowing red eyes, slit pupils, "
     "wide smug grin with sharp fangs, slight blush, "
     "curvy hourglass figure, medium-large breasts, proportionate bust, narrow waist, wide hips, thick thighs, "
     "black corset bodice with gold trim, keyhole neckline, shoulders covered, long sleeves, short black skirt with red lining, red ruffled cuffs with gold card suit embroidery, black gloves, "
     "thigh-high stockings, high heels, standing, hand on hip, other hand holding a playing card, full body, head to toe, "
     "flat color, cel shading, thick clean black lineart, vivid red and black, dark crimson and black background, vivid saturated colors")
NEG = ", huge breasts, gigantic breasts, oversized breasts, bursting cleavage, hat, witch hat, wings, cape, orange hair, pale pastel background, lavender background, brown hair, gray hair, cute, innocent, shy, pastel, cropped, out of frame, cut off feet, extra fingers, fused fingers, deformed hands, extra limbs, gray skin"

def gen(seed, ipw, base=None, den=1.0, tag="v1"):
    g = {"1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ct.CKPT}},
         "2": {"class_type": "CLIPTextEncode", "inputs": {"text": f"{P}, {ct.QUALITY}", "clip": ["1", 1]}},
         "3": {"class_type": "CLIPTextEncode", "inputs": {"text": ct.NEG + NEG, "clip": ["1", 1]}},
         "4": ({"class_type": "EmptyLatentImage", "inputs": {"width": 832, "height": 1216, "batch_size": 1}} if base is None else {"class_type": "VAEEncode", "inputs": {"pixels": ["30", 0], "vae": ["1", 2]}}),
         "30": {"class_type": "LoadImage", "inputs": {"image": ct.upload(str(base or REF))}},
         "20": {"class_type": "LoadImage", "inputs": {"image": ct.upload(str(REF))}},
         "21": {"class_type": "IPAdapterModelLoader", "inputs": {"ipadapter_file": "ip-adapter-plus_sdxl_vit-h.safetensors"}},
         "22": {"class_type": "CLIPVisionLoader", "inputs": {"clip_name": "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"}},
         "23": {"class_type": "IPAdapterAdvanced", "inputs": {"model": ["1", 0], "ipadapter": ["21", 0], "image": ["20", 0], "clip_vision": ["22", 0],
                "weight": ipw, "weight_type": "style transfer", "combine_embeds": "concat", "start_at": 0.0, "end_at": 1.0, "embeds_scaling": "V only"}},
         "5": {"class_type": "KSampler", "inputs": {"model": ["23", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["4", 0],
               "seed": seed, "steps": 30, "cfg": 6.0, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": den}},
         "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
         "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": "devils/_body"}}}
    dest = OUT / f"body_{tag}_w{int(ipw*100)}_s{seed}.png"
    ct.run(g, "7", str(dest)); return dest

P2 = P.replace("jet black hair with vivid red streaks, pure black hair,", "jet black hair, solid black hair, a few vivid red streaks,").replace("short black skirt with red lining", "short solid black skirt with red lining").replace("dark crimson and black background", "very dark near-black burgundy casino background, dark room")
if __name__ == "__main__" and sys.argv[1] == "new":
    P = P2; NEG += ", gray skirt, pink background, beige floor, brown hair, gray stockings, lavender background"
    for s in sys.argv[3:]:
        print(gen(int(s), float(sys.argv[2]), tag="v3"), flush=True)
    sys.exit()
if __name__ == "__main__" and sys.argv[1] == "ref":
    P = P2; NEG += ", gray skirt, pink background, beige floor, brown hair"
    base = "../concepts/vespera/body/body_v1_w80_s1005.png"
    for s in sys.argv[3:]:
        print(gen(int(s), 0.7, base=base, den=float(sys.argv[2]), tag="v2"), flush=True)
    sys.exit()
if __name__ == "__main__":
    ipw = float(sys.argv[1])
    for s in sys.argv[2:]:
        print(gen(int(s), ipw), flush=True)
