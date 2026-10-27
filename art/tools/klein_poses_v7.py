"""Poses de Vespera con FLUX.2 klein usando body_canon_v1 + busto s604 como referencias. Uso: klein_poses.py <semilla> [pose ...]"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import comfy_tools as ct
OUT = Path("../concepts/vespera/body/poses4"); OUT.mkdir(parents=True, exist_ok=True)
CANON = Path("../concepts/vespera/v7/body_canon_v4.png"); BUST = Path("../concepts/vespera/v7/head_ref.png")
KEEP = ("Keep exactly the same character, outfit and proportions as image 1 (same 7-head body, wide rounded hips, same bust size, same dress length) and the same face as image 2: wavy black hair with red streaks, black horns, vivid crimson eyes, fanged grin, black off-shoulder bodice with red ruffles, black gloves with red poker-suit cuffs. "
        "Same flat cel-shaded anime style, thick black outlines, vivid saturated colors with strong dark shadows, plain dark burgundy background, full body, head to toe, well-formed hands with five fingers. ")
POSES = {
 "_canon2": "Redraw her with chibi-leaning anime proportions about 6 heads tall: a LARGE head and face exactly like image 2 (wide face, big eyes with the red marks beside the eye, round cheeks), short neck, shoulders and body compact, wide rounded hips, normal-length legs, not tall and not elongated. Standing, hands clasped at the waist, smug fanged grin.",
 "_canon3": "Redraw her SLIGHTLY TALLER than image 1: about 7 heads tall, same face and head size as image 1, a slightly longer neck, longer torso and noticeably longer legs, keeping the wide rounded hips and the same bust size. Graceful elegant standing pose, hands clasped at the waist, smug fanged grin. Same dress length above the knees.",
 "_canon4": "Redraw her a bit TALLER than image 1: about 7.5 heads tall, same face and head size as image 1, a longer neck, a longer torso with a slim waist, and clearly longer legs, keeping the wide rounded hips and the same bust size. Graceful elegant standing pose, hands clasped at the waist, smug fanged grin. Same dress length above the knees.",
 "lado": "New pose: three-quarter side view, turned to the right, one hand on her hip, looking at the viewer over her shoulder with a smug fanged smirk.",
 "espalda": "New pose: seen from behind, looking back over her shoulder at the viewer with a wicked grin, long hair down her back, dress and ruffled hem visible from behind.",
 "mesa": "New pose: WAIST-UP framing only. She leans forward over a casino table with both gloved hands flat on the green felt, a dark wooden table edge hides everything below her waist, intense predatory stare, manic fanged grin. Nothing is visible below the table.",
 "carta": "New pose: standing, one arm extended toward the viewer holding a single playing card between two gloved fingers, offering it with a seductive manipulative smile.",
 "brazos": "New pose: standing with arms crossed under the bust, chin raised, arrogant dominant expression, one eyebrow raised.",
 "sentada": "New pose: sitting elegantly on a high stool with legs crossed, hands on her knee, smug seductive smile.",
 "risa": "New pose: head thrown back laughing maniacally with a wide fanged grin, one hand covering her cheek, hair flying.",
 "furia": "New pose: FURIOUS. Leaning toward the viewer, pointing an accusing finger straight at the viewer with one arm extended, the other hand clenched into a fist at her side. Her face is enraged: eyebrows furrowed and slanted down, narrowed glaring red eyes with tiny slit pupils, mouth open shouting with bared sharp fangs, a pulsing anger vein mark on her forehead, no smile.",
}
def gen(name, seed, w=832, h=1376):
    if name == "_canon2": w, h = 832, 1280
    if name == "_canon3": w, h = 832, 1376
    if name == "_canon4": w, h = 832, 1440
    g = {"1": {"class_type": "UNETLoader", "inputs": {"unet_name": "flux-2-klein-4b-fp8.safetensors", "weight_dtype": "default"}},
         "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen_3_4b.safetensors", "type": "flux2"}},
         "3": {"class_type": "VAELoader", "inputs": {"vae_name": "flux2-vae.safetensors"}},
         "4": {"class_type": "CLIPTextEncode", "inputs": {"text": KEEP + POSES[name], "clip": ["2", 0]}},
         "9": {"class_type": "ConditioningZeroOut", "inputs": {"conditioning": ["4", 0]}}}
    pos, neg = ["4", 0], ["9", 0]
    for i, ref in enumerate((Path(os.environ["CANON"]) if os.environ.get("CANON") else CANON, BUST)):
        g[f"5{i}"] = {"class_type": "LoadImage", "inputs": {"image": ct.upload(str(ref))}}
        g[f"6{i}"] = {"class_type": "ImageScaleToTotalPixels", "inputs": {"image": [f"5{i}", 0], "upscale_method": "lanczos", "megapixels": 1.0, "resolution_steps": 16}}
        g[f"7{i}"] = {"class_type": "VAEEncode", "inputs": {"pixels": [f"6{i}", 0], "vae": ["3", 0]}}
        g[f"8{i}"] = {"class_type": "ReferenceLatent", "inputs": {"conditioning": pos, "latent": [f"7{i}", 0]}}
        g[f"9{i}"] = {"class_type": "ReferenceLatent", "inputs": {"conditioning": neg, "latent": [f"7{i}", 0]}}
        pos, neg = [f"8{i}", 0], [f"9{i}", 0]
    g.update({"11": {"class_type": "CFGGuider", "inputs": {"model": ["1", 0], "positive": pos, "negative": neg, "cfg": 1.0}},
         "12": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "euler"}},
         "13": {"class_type": "Flux2Scheduler", "inputs": {"steps": 4, "width": w, "height": h}},
         "14": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed}},
         "15": {"class_type": "EmptyFlux2LatentImage", "inputs": {"width": w, "height": h, "batch_size": 1}},
         "16": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["14", 0], "guider": ["11", 0], "sampler": ["12", 0], "sigmas": ["13", 0], "latent_image": ["15", 0]}},
         "17": {"class_type": "VAEDecode", "inputs": {"samples": ["16", 0], "vae": ["3", 0]}},
         "18": {"class_type": "SaveImage", "inputs": {"images": ["17", 0], "filename_prefix": "devils/_pose"}}})
    dest = OUT / f"pose_{name}_s{seed}.png"; ct.run(g, "18", str(dest)); return dest
if __name__ == "__main__":
    seed = int(sys.argv[1])
    for n in (sys.argv[2:] or list(POSES)): print(gen(n, seed), flush=True)
