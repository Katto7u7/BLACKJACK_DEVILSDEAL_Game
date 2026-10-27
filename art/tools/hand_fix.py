"""Prueba: FaceDetailer con detector de manos (o cara) sobre una imagen."""
import sys
import comfy_tools as ct

def detail(src, dest, det, prompt, seed=1, denoise=0.5, guide=512, crop=3.0, thr=0.3):
    g = {"1": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ct.CKPT}},
         "2": {"class_type": "CLIPTextEncode", "inputs": {"text": f"{prompt}, {ct.QUALITY}", "clip": ["1", 1]}},
         "3": {"class_type": "CLIPTextEncode", "inputs": {"text": ct.NEG + ", extra fingers, fused fingers, mutated hands", "clip": ["1", 1]}},
         "4": {"class_type": "LoadImage", "inputs": {"image": ct.upload(src)}},
         "5": {"class_type": "UltralyticsDetectorProvider", "inputs": {"model_name": det}},
         "6": {"class_type": "FaceDetailer", "inputs": {
             "image": ["4", 0], "model": ["1", 0], "clip": ["1", 1], "vae": ["1", 2], "guide_size": guide,
             "guide_size_for": True, "max_size": 1024, "seed": seed, "steps": 28, "cfg": 6.0,
             "sampler_name": "euler_ancestral", "scheduler": "normal", "positive": ["2", 0], "negative": ["3", 0],
             "denoise": denoise, "feather": 8, "noise_mask": True, "force_inpaint": True, "bbox_threshold": thr,
             "bbox_dilation": 10, "bbox_crop_factor": crop, "sam_detection_hint": "center-1", "sam_dilation": 0,
             "sam_threshold": 0.93, "sam_bbox_expansion": 0, "sam_mask_hint_threshold": 0.7,
             "sam_mask_hint_use_negative": "False", "drop_size": 10, "bbox_detector": ["5", 0],
             "wildcard": "", "cycle": 1}},
         "7": {"class_type": "SaveImage", "inputs": {"images": ["6", 0], "filename_prefix": "devils/_det"}}}
    return ct.run(g, "7", dest)

if __name__ == "__main__":
    src, dest, det, den = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
    p = sys.argv[5] if len(sys.argv) > 5 else "gloved hands clasped on table, black gloves, red ruffled cuffs, gold trim, clearly drawn fingers, flat color, cel shading, thick clean black lineart"
    detail(src, dest, det, p, denoise=den)
    print("ok", dest)
