"""Piezas sueltas para el rig: ojos cerrados (parpadeo) y bocas (habla) sobre bust_v6_s604."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import comfy_tools as ct

BASE = Path("../concepts/vespera/bust/bust_v6_s604.png")
OUT = Path("../concepts/vespera/expr_v6/parts"); OUT.mkdir(parents=True, exist_ok=True)
EYES = [(385, 290), (655, 290), (655, 392), (385, 392)]
MOUTH = [(440, 400), (590, 400), (590, 482), (440, 482)]
HEAD = ("1girl, vespera, demon girl, jet black hair with red streaks, pale white skin, sharp fangs, "
        "flat color, cel shading, thick clean black lineart, vivid colors, close up face")
JOBS = {
  "blink":  (EYES,  "closed eyes, both eyes shut, curved closed eyelid lines, long eyelashes, no pupils, no irises, sleepy happy closed eyes"),
  "talk_a": (MOUTH, "mouth open wide talking, showing sharp fangs and tongue, red inside"),
  "talk_b": (MOUTH, "mouth open small round shape like saying O, fangs"),
  "talk_c": (MOUTH, "mouth slightly open, smirking talking, fangs visible"),
}
NEG = ct.NEG + ", open eyes, visible pupils, visible irises, red eyes, yellow eyes, orange eyes, gray skin, dark skin, brown hair, blue eyes"

if __name__ == "__main__":
    base = Image.open(BASE).convert("RGB")
    for name in (sys.argv[2:] or JOBS):
        poly, p = JOBS[name]
        m = Image.new("L", (1024, 1024), 0); ImageDraw.Draw(m).polygon(poly, fill=255)
        mp = OUT / f"_m_{name}.png"; m.save(mp); soft = m.filter(ImageFilter.GaussianBlur(3))
        for s in range(int(sys.argv[1]), int(sys.argv[1]) + 3):
            raw = OUT / f"_raw_{name}_{s}.png"
            ct.inpaint(str(BASE), str(mp), str(raw), f"{HEAD}, {p}", neg=NEG, seed=s, denoise=(0.97 if name == "blink" else 0.8), steps=30, cfg=6.5)
            Image.composite(Image.open(raw).convert("RGB"), base, soft).save(OUT / f"{name}_{s}.png"); print(name, s, flush=True)
