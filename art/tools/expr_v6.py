"""Expresiones de Vespera v6: reinpaint de la zona de cara (cejas+ojos+boca) con mezcla suave sobre bust_v6_s604."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import comfy_tools as ct

BASE = Path("../concepts/vespera/bust/bust_v6_s604.png")
OUT = Path("../concepts/vespera/expr_v6"); OUT.mkdir(parents=True, exist_ok=True)
FACE = [(372, 262), (672, 262), (690, 330), (668, 440), (610, 500), (440, 500), (385, 440), (362, 330)]
HEAD = ("1girl, vespera, demon girl, jet black hair with red streaks, glowing red eyes with slit pupils, sharp fangs, pale skin, "
        "flat color, cel shading, thick clean black lineart, vivid colors, close up face")
EXPR = {
  "encanto":      "seductive half-lidded eyes, soft alluring smirk, blush, lips slightly parted",
  "malicia":      "evil grin, narrowed menacing eyes, wide sharp-toothed smile, scheming look",
  "arrogancia":   "smug look, one eyebrow raised, eyes half closed looking down, closed mouth smirk",
  "celos":        "yandere jealousy, dark shadowed eyes with tiny pupils, cold glare, one twitching eyebrow, tight forced smile with fangs, menacing",
  "culpa":        "guilty, averted eyes, worried eyebrows, small frown, biting lip",
  "vulnerable":   "sad teary eyes, trembling lips, worried eyebrows, blush, tears",
  "desesperacion":"desperate, wide eyes with tiny pupils, tears, screaming mouth open, panicking",
  "sorpresa":     "surprised, wide open eyes, raised eyebrows, small round open mouth",
  "enfado":       "extremely furious, deeply furrowed angry eyebrows, glaring murderous eyes, shadow over eyes, snarling with gritted sharp teeth, rage, vein popping",
  "burla":        "mocking laughter, eyes closed happy, wide open laughing mouth showing tongue and fangs",
  "ternura":      "gentle warm smile, soft eyes, blush, small genuine smile",
  "miedo":        "scared, shrinking pupils, trembling, pale, mouth open in fear, sweat drop",
  "obsesion":     "yandere, heart-shaped pupils, wide eyes, unhinged adoring smile, blush",
  "locura":       "insane grin, wide bloodshot eyes with tiny pupils, manic laughter, maniacal expression",
}
NEG = ct.NEG + ", gray skin, dark skin, brown hair, extra eyes, deformed face, blue eyes, green eyes"

def mask():
    m = Image.new("L", (1024, 1024), 0); ImageDraw.Draw(m).polygon(FACE, fill=255)
    p = OUT / "_mask.png"; m.save(p); return p, m.filter(ImageFilter.GaussianBlur(4))

if __name__ == "__main__":
    mp, soft = mask(); base = Image.open(BASE).convert("RGB")
    names = sys.argv[2:] or list(EXPR)
    for n in names:
        for s in range(int(sys.argv[1]), int(sys.argv[1]) + 2):
            raw = OUT / f"_raw_{n}_{s}.png"
            ct.inpaint(str(BASE), str(mp), str(raw), f"{HEAD}, {EXPR[n]}", neg=NEG, seed=s, denoise=0.72, steps=30, cfg=6.5)
            Image.composite(Image.open(raw).convert("RGB"), base, soft).save(OUT / f"{n}_{s}.png")
            print(n, s, flush=True)
