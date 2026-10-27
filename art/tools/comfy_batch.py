"""Lanza lotes de texto->imagen en ComfyUI y registra cada resultado en un manifiesto.

Uso:
  python comfy_batch.py --category tests --name vespera_style_a --prompt "..." -n 4
Opcional: --neg, --seed, --width, --height, --steps, --cfg, --ckpt, --sampler
"""
import argparse
import json
import random
import time
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

COMFY = "http://127.0.0.1:8188"
ART = Path(__file__).resolve().parents[1]
CONCEPTS = ART / "concepts"
MANIFEST = CONCEPTS / "_manifest.json"

DEFAULT_CKPT = "animagine-xl-4.0.safetensors"
DEFAULT_NEG = (
    "lowres, bad anatomy, bad hands, text, error, missing finger, extra digits, "
    "fewer digits, cropped, worst quality, low quality, low score, bad score, "
    "average score, signature, watermark, username, blurry"
)
QUALITY = "masterpiece, high score, great score, absurdres"


def http_json(path, data=None):
    req = urllib.request.Request(
        COMFY + path,
        data=json.dumps(data).encode() if data is not None else None,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def upload(path):
    import uuid
    b = uuid.uuid4().hex
    data = Path(path).read_bytes()
    crlf = chr(13) + chr(10)
    head = (f"--{b}{crlf}Content-Disposition: form-data; name=\"image\"; filename=\"{Path(path).name}\"{crlf}"
            f"Content-Type: image/png{crlf}{crlf}")
    body = head.encode() + data + f"{crlf}--{b}--{crlf}".encode()
    req = urllib.request.Request(COMFY + "/upload/image", data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())["name"]


def build_graph(a, seed):
    g = _build_graph(a, seed)
    if a.ref:
        g["20"] = {"class_type": "LoadImage", "inputs": {"image": upload(a.ref)}}
        g["21"] = {"class_type": "IPAdapterModelLoader", "inputs": {"ipadapter_file": "ip-adapter-plus_sdxl_vit-h.safetensors"}}
        g["22"] = {"class_type": "CLIPVisionLoader", "inputs": {"clip_name": "CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors"}}
        g["23"] = {"class_type": "IPAdapterAdvanced", "inputs": {
            "model": ["1", 0], "ipadapter": ["21", 0], "image": ["20", 0], "clip_vision": ["22", 0],
            "weight": a.ref_weight, "weight_type": a.ref_type, "combine_embeds": "concat",
            "start_at": 0.0, "end_at": 1.0, "embeds_scaling": "V only"}}
        g["5"]["inputs"]["model"] = ["23", 0]
    return g


def _build_graph(a, seed):
    return {
        "1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": a.ckpt}},
        "2": {"class_type": "CLIPTextEncode", "inputs": {"text": f"{a.prompt}, {QUALITY}", "clip": ["1", 1]}},
        "3": {"class_type": "CLIPTextEncode", "inputs": {"text": a.neg, "clip": ["1", 1]}},
        "4": {"class_type": "EmptyLatentImage", "inputs": {"width": a.width, "height": a.height, "batch_size": 1}},
        "5": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["4", 0],
                "seed": seed, "steps": a.steps, "cfg": a.cfg, "sampler_name": a.sampler,
                "scheduler": "normal", "denoise": 1.0,
            },
        },
        "6": {"class_type": "VAEDecode", "inputs": {"samples": ["5", 0], "vae": ["1", 2]}},
        "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": f"devils/{a.name}"}},
    }


def wait_for(pid):
    while True:
        h = http_json(f"/history/{pid}")
        if pid in h:
            return h[pid]
        time.sleep(1.5)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--category", required=True)
    p.add_argument("--name", required=True)
    p.add_argument("--prompt", required=True)
    p.add_argument("--neg", default=DEFAULT_NEG)
    p.add_argument("-n", type=int, default=1)
    p.add_argument("--seed", type=int, default=None)
    p.add_argument("--width", type=int, default=832)
    p.add_argument("--height", type=int, default=1216)
    p.add_argument("--steps", type=int, default=28)
    p.add_argument("--cfg", type=float, default=5.0)
    p.add_argument("--sampler", default="euler_ancestral")
    p.add_argument("--ckpt", default=DEFAULT_CKPT)
    p.add_argument("--ref", default=None, help="imagen de referencia (IP-Adapter)")
    p.add_argument("--ref-type", dest="ref_type", default="linear")
    p.add_argument("--ref-weight", dest="ref_weight", type=float, default=0.6)
    a = p.parse_args()

    out_dir = CONCEPTS / a.category
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text("utf-8")) if MANIFEST.exists() else []

    for i in range(a.n):
        seed = (a.seed if a.seed is not None else random.randint(0, 2**32 - 1)) + (i if a.seed is not None else 0)
        pid = http_json("/prompt", {"prompt": build_graph(a, seed)})["prompt_id"]
        hist = wait_for(pid)
        for img in hist["outputs"]["7"]["images"]:
            q = urllib.parse.urlencode({"filename": img["filename"], "subfolder": img["subfolder"], "type": img["type"]})
            dest = out_dir / f"{a.name}_s{seed}.png"
            with urllib.request.urlopen(f"{COMFY}/view?{q}", timeout=60) as r:
                dest.write_bytes(r.read())
            manifest.append({
                "file": str(dest.relative_to(ART)).replace("\\", "/"),
                "date": datetime.now().isoformat(timespec="seconds"),
                "ckpt": a.ckpt, "prompt": a.prompt, "negative": a.neg, "seed": seed,
                "size": [a.width, a.height], "steps": a.steps, "cfg": a.cfg, "sampler": a.sampler,
                "status": "candidato", "ref": a.ref, "ref_weight": a.ref_weight if a.ref else None,
            })
            print(dest)
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), "utf-8")


if __name__ == "__main__":
    main()
