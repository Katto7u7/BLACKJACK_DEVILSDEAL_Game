"""Texto a imagen con klein, sin referencias. Uso: klein_txt.py <variante a|b> <semilla...>"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import comfy_tools as ct
OUT = Path("../concepts/vespera/experimento"); OUT.mkdir(parents=True, exist_ok=True)
BASE = ("Flat cel-shaded anime character design, thick black outlines, vivid saturated intense colors, strong dark shadows, plain dark background, full body, head to toe, one character. "
        "An adult female demon casino dealer named Vespera: a beautiful, seductive, dominant and slightly mad demon woman. Her palette is only crimson red and black. "
        "Long wavy black hair with crimson red streaks, large curved black horns, glowing crimson red eyes with slit pupils, a wicked fanged smirk with a flushed face, "
        "a manic seductive expression like she always gets her way, hungry provocative gaze. Voluptuous curvy figure with a full bust, a narrow waist and wide hips. ")
BASE2 = ("High-quality anime key visual of a hyper-waifu gacha game character, flat cel-shaded, clean thick black outlines, vivid saturated intense colors, soft strong shadows, plain dark background, full body, head to toe, one character. "
         "An adult female demon casino dealer named Vespera: an EXTREMELY beautiful, cute-pretty anime waifu with a gorgeous delicate face, very large detailed sparkling crimson red eyes with long eyelashes and slit pupils, small nose, flushed cheeks, a charming mischievous fanged smile, a slightly mad seductive dominant look. "
         "Palette only crimson red and black. Long silky black hair with crimson red streaks, large curved black horns. Curvy voluptuous figure with a large bust, narrow waist and wide hips, but a modest high neckline, shoulders covered. ")
V = {"c": "She wears an elegant black and crimson red gothic dealer dress: a high collar, a small keyhole opening at the chest, long sleeves with crimson ruffled cuffs, a fitted corset with gold laces, a short layered skirt with a crimson ruffle, black stockings and gold-trimmed boots. Confident dominant pose, one hand on her hip, the other holding a playing card.",
     "d": "She wears a luxurious black and crimson red tailored outfit: a closed high-neck fitted bodice with a gold heart-shaped cutout detail, long black sleeves with red cuffs with poker suit symbols, a crimson satin skirt with black lace layers, black thigh-high stockings and red heels. Teasing playful pose leaning forward with a hand extended toward the viewer.",
     "a": "She wears an elegant gothic casino dealer dress in black and crimson red with gold trim, tasteful and classy but provocative: a fitted corset bodice, a daring neckline, long gloves, a short flared skirt with a crimson ruffle, black stockings and high heels. Confident dominant pose, one hand on her hip, holding a playing card between two fingers.",
     "b": "She wears a luxurious black and crimson red tailored dealer outfit with a short cropped jacket, a lace-up corset, a crimson satin skirt, black thigh-high stockings, red-soled heels and black gloves, with poker-suit symbols embroidered in gold. Dominant, teasing pose, leaning forward with a hand extended toward the viewer, a devilish tail curling behind her."}
def gen(var, seed, w=832, h=1376):
    g = {"1": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux-2-klein-4b-fp8.safetensors", "weight_dtype": "default"}},
         "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "flux2"}},
         "3": {"class_type": "VAELoader", "inputs": {"vae_name": "flux2-vae.safetensors"}},
         "4": {"class_type": "CLIPTextEncode", "inputs": {"text": (BASE2 if var in "cd" else BASE) + V[var], "clip": ["2", 0]}},
         "9": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
         "11": {"class_type": "CFGGuider", "inputs": {"model": ["1", 0], "positive": ["4", 0], "negative": ["9", 0], "cfg": 1.0}},
         "12": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
         "13": {"class_type": "Flux2Scheduler", "inputs": {"steps": 4, "width": w, "height": h}},
         "14": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
         "15": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
         "16": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["14", 0], "guider": ["11", 0], "sampler": ["12", 0], "sigmas": ["13", 0], "latent_image": ["15", 0]}},
         "17": {"class_type": "VAEDecode", "inputs": {"samples": ["16", 0], "vae": ["3", 0]}},
         "18": {"class_type": "SaveImage", "inputs": {"images": ["17", 0], "filename_prefix": "devils/_exp"}}}
    dest = OUT / f"vespera_{var}_s{seed}.png"; ct.run(g, "18", str(dest)); return dest
if __name__ == "__main__":
    for s in sys.argv[2:]: print(gen(sys.argv[1], int(s)), flush=True)
