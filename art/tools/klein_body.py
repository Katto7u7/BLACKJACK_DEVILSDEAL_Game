"""FLUX.2 klein 4B (edicion por referencia, Apache-2.0). Uso: klein_body.py <nombre> <semillas...>  (prompt en PROMPTS)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import comfy_tools as ct
OUT = Path("../concepts/vespera/body")
BUST = Path("../concepts/vespera/bust/bust_v6_s604.png")
BODY = ("Draw the full body of the character in image 1, standing front view, head to toe, hands clasped together at the waist. "
        "Keep exactly the same character, face, black hair with red streaks, black horns, red eyes, fanged grin, black high-collar jacket with gold trim, "
        "keyhole cleavage, grey corset bodice with gold buttons, red ruffled cuffs and black gloves. "
        "Replace the skirt with a more elegant, beautiful gothic dress cut: the corset bodice continues into a form-fitting black skirt that hugs the waist and hips and shows the hourglass figure, "
        "with gold embroidery and a gold waist belt, a slightly flared hem with layered red ruffles and a red lace trim, ending just above the knees. "
        "Very narrow waist, wide rounded hips, full thighs, long legs, 8-head fashion proportions, sheer black stockings with a subtle gold-trimmed top and black ankle boots with gold trim; keep the bust the same size as in image 1. "
        "Same flat cel-shaded anime style, thick black outlines, vivid saturated red and black colors with strong dark shadows, plain dark burgundy background.")
def gen(name, seed, prompt=BODY, ref=BUST, w=832, h=1536, steps=4):
    g = {"1": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux-2-klein-4b-fp8.safetensors", "weight_dtype": "default"}},
         "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "flux2"}},
         "3": {"class_type": "VAELoader", "inputs": {"vae_name": "flux2-vae.safetensors"}},
         "4": {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": ["2", 0]}},
         "5": {"class_type": "LoadImage", "inputs": {"image": ct.upload(str(ref))}},
         "6": {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["5", 0], "upscale_method": "lanczos", "megapixels": 1.0, "resolution_steps": 16}},
         "7": {"class_type": "VAEEncode", "inputs": {"pixels": ["6", 0], "vae": ["3", 0]}},
         "8": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["4", 0], "latent": ["7", 0]}},
         "9": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
         "10": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["9", 0], "latent": ["7", 0]}},
         "11": {"class_type": "CFGGuider", "inputs": {"model": ["1", 0], "positive": ["8", 0], "negative": ["10", 0], "cfg": 1.0}},
         "12": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
         "13": {"class_type": "Flux2Scheduler", "inputs": {"steps": steps, "width": w, "height": h}},
         "14": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
         "15": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
         "16": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["14", 0], "guider": ["11", 0], "sampler": ["12", 0], "sigmas": ["13", 0], "latent_image": ["15", 0]}},
         "17": {"class_type": "VAEDecode", "inputs": {"samples": ["16", 0], "vae": ["3", 0]}},
         "18": {"class_type": "SaveImage", "inputs": {"images": ["17", 0], "filename_prefix": "devils/_klein"}}}
    dest = OUT / f"klein_{name}_s{seed}.png"; ct.run(g, "18", str(dest)); return dest
if __name__ == "__main__":
    for s in sys.argv[2:]: print(gen(sys.argv[1], int(s)), flush=True)
