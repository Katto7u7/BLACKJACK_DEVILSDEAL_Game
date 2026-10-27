"""Propuestas de personajes nuevos (Nox, Contadora) con klein; Vespera solo como referencia de estilo. Uso: klein_chars.py <semilla> [clave ...]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import comfy_tools as ct
OUT = Path("../concepts/personajes"); OUT.mkdir(parents=True, exist_ok=True)
REF = Path(os.environ.get("REF","../concepts/vespera/body/body_canon_v3.png"))
STYLE = ("Use image 1 ONLY as the art style reference (flat cel-shaded anime, thick black outlines, vivid saturated colors with strong dark shadows, plain dark burgundy background). "
         "Draw a COMPLETELY DIFFERENT NEW character, NOT the girl from image 1: different face, different hair, different body, different outfit. Full body, head to toe, standing, one character only. ")
C = {
 "nox_a": "A small round chubby imp demon, about 4 heads tall, casino employee. Sulfur-green skin, tiny curved horns, big round glasses, pointy ears, a small bat tail, wearing a tiny black vest with gold buttons and a bow tie, holding a thick ledger notebook and a quill, nervous sweaty acid expression.",
 "nox_b": "A small skinny nervous imp demon, about 5 heads tall, casino bellhop clerk. Dark charcoal skin with glowing sulfur-green eyes and green markings, bat wings folded, a pair of round monocle glasses, uniform jacket with gold trim and a clipboard full of papers, messy hair, sarcastic smirk.",
 "nox_c": "A small cute fluffy demon creature, about 3.5 heads tall, round body like a plump bat-cat, sulfur-green fur and cream belly, little horns, round glasses on its nose, tiny waistcoat, carrying a record book almost bigger than itself, anxious wide eyes and a sharp grumpy mouth.",
 "cont_a": "A tall severe adult woman, 8 heads tall, impartial arbiter of hell. White and grey formal tailcoat suit with gold trim, long straight silver-white hair in a tight low bun, pale skin, cold grey eyes, rectangular glasses, small white halo-like gold ring behind her head, holding a large ledger book in one arm and a gold seal stamp in the other hand, calm expressionless face.",
 "cont_b": "A tall elegant ghostly woman, 8 heads tall, hell's neutral accountant. Long pale grey robes with gold accounting symbols, white hair in a long braid, blindfold-free calm closed eyes with gold eyelid marks, floating gold coins and a pen around her, holding an open ledger and a gold seal, serene cold expression.",
 "cont_c": "A tall stern androgynous judge-like arbiter, 8 heads tall, neutral. White judicial coat with grey high collar and gold buttons, short silver hair, sharp amber eyes, a gold monocle, white gloves holding a heavy ledger with a gold seal stamp, strict neutral face, no warmth.",
}
C.update({
 "nox_w": "A petite adult demon woman (clearly an adult, mature face, adult proportions, short stature, about 6 heads tall), casino employee, very cute waifu anime style. Dark hair with sulfur-green streaks in a messy short bob, small curved black horns, pointy ears, round glasses over big nervous green eyes, a blush, a small fanged sarcastic smirk, a thin bat tail and tiny bat wings. Modest cute uniform: black vest with gold buttons over a white blouse, a short black skirt with sulfur-green trim, black tights, a bow tie. Hugging a thick ledger notebook with a quill, anxious and acid expression.",
 "cont_w": "A tall elegant adult woman, 8 heads tall, waifu anime style, impartial arbiter of hell. Long silver-white hair in a low side braid, pale skin, cold grey eyes with gold eyelashes, rectangular glasses, a thin gold ring halo behind her head, a calm composed expressionless face with a subtle beauty mark. White and grey tailored high-collar dress-coat with gold trim and a fitted waist, keyhole-free modest neckline, white gloves, long legs in grey stockings and white heels. Holding a large ledger in one arm and a gold seal stamp in the other hand. Elegant, sophisticated, cold, no warmth.",
})
def gen(name, seed, w=1024, h=1024):
    if name not in C: C[name] = ""
    g = {"1": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux-2-klein-4b-fp8.safetensors", "weight_dtype": "default"}},
         "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "flux2"}},
         "3": {"class_type": "VAELoader", "inputs": {"vae_name": "flux2-vae.safetensors"}},
         "4": {"class_type": "CLIPTextEncode", "inputs": {"text": (os.environ["PROMPT"] if os.environ.get("PROMPT") else STYLE + C[name]), "clip": ["2", 0]}},
         "9": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}},
         "50": {"class_type": "LoadImage", "inputs": {"image": ct.upload(str(REF))}},
         "60": {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["50", 0], "upscale_method": "lanczos", "megapixels": 1.0, "resolution_steps": 16}},
         "70": {"class_type": "VAEEncode", "inputs": {"pixels": ["60", 0], "vae": ["3", 0]}},
         "80": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["4", 0], "latent": ["70", 0]}},
         "90": {"class_type": "ReferenceLatent", "inputs": {"conditioning": ["9", 0], "latent": ["70", 0]}}}
    pos, neg = ["80", 0], ["90", 0]
    if os.environ.get("REF2"):
        g.update({"51": {"class_type": "LoadImage", "inputs": {"image": ct.upload(os.environ["REF2"])}},
         "61": {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": ["51", 0], "upscale_method": "lanczos", "megapixels": 1.0, "resolution_steps": 16}},
         "71": {"class_type": "VAEEncode", "inputs": {"pixels": ["61", 0], "vae": ["3", 0]}},
         "81": {"class_type": "ReferenceLatent", "inputs": {"conditioning": pos, "latent": ["71", 0]}},
         "91": {"class_type": "ReferenceLatent", "inputs": {"conditioning": neg, "latent": ["71", 0]}}})
        pos, neg = ["81", 0], ["91", 0]
    g.update({
         "11": {"class_type": "CFGGuider", "inputs": {"model": ["1", 0], "positive": pos, "negative": neg, "cfg": 1.0}},
         "12": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
         "13": {"class_type": "Flux2Scheduler", "inputs": {"steps": 4, "width": w, "height": h}},
         "14": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
         "15": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
         "16": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["14", 0], "guider": ["11", 0], "sampler": ["12", 0], "sigmas": ["13", 0], "latent_image": ["15", 0]}},
         "17": {"class_type": "VAEDecode", "inputs": {"samples": ["16", 0], "vae": ["3", 0]}},
         "18": {"class_type": "SaveImage", "inputs": {"images": ["17", 0], "filename_prefix": "devils/_char"}}})
    dest = OUT / f"{os.environ.get('TAG', '')}{name}_s{seed}.png"; ct.run(g, "18", str(dest)); return dest
if __name__ == "__main__":
    seed = int(sys.argv[1])
    for n in (sys.argv[2:] or list(C)): print(gen(n, seed), flush=True)
