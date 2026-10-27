"""Utilidades ComfyUI: subir imagen, ejecutar grafo, descargar resultado, escalar con ESRGAN, inpaint de region."""
import json, time, uuid, urllib.parse, urllib.request
from pathlib import Path

COMFY = "http://127.0.0.1:8188"
CKPT = "animagine-xl-4.0.safetensors"
QUALITY = "masterpiece, high score, great score, absurdres"
NEG = ("lowres, bad anatomy, bad hands, text, error, cropped, worst quality, low quality, signature, "
       "watermark, blurry, gray hair, pastel, muted colors")


def _json(path, data=None):
    req = urllib.request.Request(COMFY + path, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())


def upload(path):
    b = uuid.uuid4().hex
    crlf = chr(13) + chr(10)
    head = (f"--{b}{crlf}Content-Disposition: form-data; name=\"image\"; filename=\"{Path(path).name}\"{crlf}"
            f"Content-Type: image/png{crlf}{crlf}")
    body = head.encode() + Path(path).read_bytes() + f"{crlf}--{b}--{crlf}".encode()
    req = urllib.request.Request(COMFY + "/upload/image", data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={b}"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())["name"]


def run(graph, save_node, dest):
    pid = _json("/prompt", {"prompt": graph})["prompt_id"]
    while True:
        h = _json(f"/history/{pid}")
        if pid in h:
            break
        time.sleep(1.5)
    img = h[pid]["outputs"][save_node]["images"][0]
    q = urllib.parse.urlencode({"filename": img["filename"], "subfolder": img["subfolder"], "type": img["type"]})
    with urllib.request.urlopen(f"{COMFY}/view?{q}", timeout=120) as r:
        Path(dest).write_bytes(r.read())
    return dest


def upscale4x(src, dest):
    g = {"1": {"class_type": "LoadImage", "inputs": {"image": upload(src)}},
         "2": {"class_type": "UpscaleModelLoader", "inputs": {"model_name": "RealESRGAN_x4plus_anime_6B.pth"}},
         "3": {"class_type": "ImageUpscaleWithModel", "inputs": {"upscale_model": ["2", 0], "image": ["1", 0]}},
         "4": {"class_type": "SaveImage", "inputs": {"images": ["3", 0], "filename_prefix": "devils/_up"}}}
    return run(g, "4", dest)


def inpaint(src, mask, dest, prompt, neg=NEG, seed=1, denoise=0.8, steps=28, cfg=6.0):
    """mask: PNG en escala de grises, blanco = zona a repintar."""
    g = {"1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": CKPT}},
         "2": {"class_type": "CLIPTextEncode", "inputs": {"text": f"{prompt}, {QUALITY}", "clip": ["1", 1]}},
         "3": {"class_type": "CLIPTextEncode", "inputs": {"text": neg, "clip": ["1", 1]}},
         "4": {"class_type": "LoadImage", "inputs": {"image": upload(src)}},
         "5": {"class_type": "LoadImage", "inputs": {"image": upload(mask)}},
         "6": {"class_type": "ImageToMask", "inputs": {"image": ["5", 0], "channel": "red"}},
         "7": {"class_type": "VAEEncode", "inputs": {"pixels": ["4", 0], "vae": ["1", 2]}},
         "8": {"class_type": "SetLatentNoiseMask", "inputs": {"samples": ["7", 0], "mask": ["6", 0]}},
         "9": {"class_type": "KSampler", "inputs": {"model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0],
               "latent_image": ["8", 0], "seed": seed, "steps": steps, "cfg": cfg,
               "sampler_name": "euler_ancestral", "scheduler": "normal", "denoise": denoise}},
         "10": {"class_type": "VAEDecode", "inputs": {"samples": ["9", 0], "vae": ["1", 2]}},
         "11": {"class_type": "SaveImage", "inputs": {"images": ["10", 0], "filename_prefix": "devils/_inp"}}}
    return run(g, "11", dest)
