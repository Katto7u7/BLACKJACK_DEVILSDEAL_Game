"""Pulido de busto: reinpaint de pecho y manos con varias semillas; compone con mascara suavizada."""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import comfy_tools as ct

BASE = Path("../concepts/vespera/bust/bust_base_s12003.png")
OUT = Path("../work/vespera/polish"); OUT.mkdir(parents=True, exist_ok=True)
ZONAS = {
    "pecho": ([(330, 590), (690, 590), (740, 700), (730, 830), (300, 830), (290, 700)],
              "1girl, bust, large breasts, fitted black corset bodice with gold trim and gold lacing, "
              "clear natural breast shape under the corset, keyhole neckline opening showing pale skin, "
              "red ribbon lacing, flat color, cel shading, thick clean black lineart, vivid red and black, upper body"),
    "manos": ([(200, 800), (480, 800), (480, 1000), (200, 1000)],
              "gloved hands resting clasped on a table, black gloves, ruffled red cuffs with gold trim, "
              "clearly drawn fingers, flat color, cel shading, thick clean black lineart"),
}
NEGP = ct.NEG + ", extra fingers, fused fingers, deformed breasts, asymmetrical breasts, floating shapes, diamond shape on chest, nipples"

def mask_for(poly, name):
    m = Image.new("L", (1024, 1024), 0)
    ImageDraw.Draw(m).polygon(poly, fill=255)
    p = OUT / f"mask_{name}.png"; m.save(p); return p, m

def run(zona, seeds, denoise):
    poly, prompt = ZONAS[zona]
    mp, m = mask_for(poly, zona)
    soft = m.filter(ImageFilter.GaussianBlur(5))
    base = Image.open(BASE).convert("RGB")
    for s in seeds:
        raw = OUT / f"{zona}_s{s}_raw.png"
        ct.inpaint(str(BASE), str(mp), str(raw), prompt, neg=NEGP, seed=s, denoise=denoise)
        comp = Image.composite(Image.open(raw).convert("RGB"), base, soft)
        comp.save(OUT / f"{zona}_s{s}.png")
        print("ok", zona, s, flush=True)

if __name__ == "__main__":
    zona, den = sys.argv[1], float(sys.argv[2])
    run(zona, [int(x) for x in sys.argv[3:]], den)
