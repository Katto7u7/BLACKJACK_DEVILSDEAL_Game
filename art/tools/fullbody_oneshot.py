"""Cuerpo completo de una sola generacion: txt2img + 2 IP-Adapter (cara y atuendo del busto s604) + ControlNet openpose (pose de 7101).
Uso: fullbody_oneshot.py <ip_cara> <ip_ropa> <semillas...>"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
from PIL import Image
import comfy_tools as ct
OUT = Path("../concepts/vespera/body"); BUST = Path("../concepts/vespera/bust/bust_v6_s604.png")
POSE = OUT / "out2_d100_s7101.png"
P = ("1girl, solo, vespera, demon girl, very attractive anime waifu, dominant unhinged manipulative smirk, "
     "jet black hair with vivid red streaks, wide black horns with red stripes, glowing red eyes with slit pupils, wide grin with sharp fangs, "
     "black high-collar jacket with gold trim and gold epaulettes, red toggle at the collar, keyhole cleavage window, grey corset bodice with gold buttons, shoulders covered, long black sleeves, "
     "red ruffled cuffs with gold trim, black gloves, hands clasped at the waist, "
     "curvy hourglass figure, narrow waist, wide hips, "
     "black layered dress skirt with red ruffle hem, skirt ends just above the knees, covers the thighs, opaque black stockings, black ankle boots with gold, "
     "full body, standing, flat color, cel shading with strong dark shadows, thick clean black lineart, extremely vivid saturated red and black, high contrast, dark burgundy background")
NEG = ", mini skirt, bare thighs, bare shoulders, white blouse, epaulettes missing, striped stockings, garter belt, cape, wings, hat, pale colors, washed out, pink background, brown hair, panties, extra limbs"
def crops():
    b = Image.open(BUST).convert("RGB")
    b.crop((150, 20, 874, 560)).save(OUT / "_ref_cara.png"); b.crop((60, 330, 964, 830)).save(OUT / "_ref_ropa.png")
def gen(seed, ipf, ipr):
    def ip(i, model, img, w, wt):
        return {str(i): {"class_type": "IPAdapterAdvanced", "inputs": {"model": model, "ipadapter": ["21", 0], "image": [img, 0], "clip_vision": ["22", 0],
                "weight": w, "weight_type": wt, "combine_embeds": "concat", "start_at": 0.0, "end_at": 1.0, "embeds_scaling": "V only"}}}
    g = {"1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ct.CKPT}},
         "2": {"class_type": "CLIPTextEncode", "inputs": {"text": f"{P}, {ct.QUALITY}", "clip": ["1", 1]}},
         "3": {"class_type": "CLIPTextEncode", "inputs": {"text": ct.NEG + NEG, "clip": ["1", 1]}},
         "4": {"class_type": "EmptyLatentImage", "inputs": {"width": 832, "height": 1536, "batch_size": 1}},
         "21": {"class_type": "IPAdapterModelLoader", "inputs": {"ipadapter_file": "ip-adapter-plus_sdxl_vit-h.safetensors"}},
         "22": {"class_type": "CLIPVisionLoader", "inputs": {"clip_name": "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"}},
         "20": {"class_type": "LoadImage", "inputs": {"image": ct.upload(str(OUT / "_ref_cara.png"))}},
         "24": {"class_type": "LoadImage", "inputs": {"image": ct.upload(str(OUT / "_ref_ropa.png"))}},
         "40": {"class_type": "LoadImage", "inputs": {"image": ct.upload(str(POSE))}},
         "41": {"class_type": "OpenposePreprocessor", "inputs": {"image": ["40", 0], "detect_hand": "enable", "detect_body": "enable", "detect_face": "disable", "resolution": 1024}},
         "10": {"class_type": "ControlNetLoader", "inputs": {"control_net_name": "controlnet-union-sdxl-promax.safetensors"}},
         "11": {"class_type": "SetUnionControlNetType", "inputs": {"control_net": ["10", 0], "type": "openpose"}},
         "13": {"class_type": "ControlNetApplyAdvanced", "inputs": {"positive": ["2", 0], "negative": ["3", 0], "control_net": ["11", 0],
                "image": ["41", 0], "strength": 0.8, "start_percent": 0.0, "end_percent": 0.8}},
         "5": {"class_type": "KSampler", "inputs": {"model": ["51", 0], "positive": ["13", 0], "negative": ["13", 1], "latent_image": ["4", 0],
               "seed": seed, "steps": 30, "cfg": 6.0, "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": 1.0}},
         "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
         "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": "devils/_one"}},
         "42": {"class_type": "PreviewImage", "inputs": {"images": ["41", 0]}}}
    g.update(ip(50, ["1", 0], "20", ipf, "style transfer")); g.update(ip(51, ["50", 0], "24", ipr, "style transfer"))
    dest = OUT / f"one_f{int(ipf*100)}_r{int(ipr*100)}_s{seed}.png"; ct.run(g, "7", str(dest)); return dest
if __name__ == "__main__":
    crops()
    for s in sys.argv[3:]: print(gen(int(s), float(sys.argv[1]), float(sys.argv[2])), flush=True)
