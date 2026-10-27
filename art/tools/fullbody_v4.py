"""Corrige el atuendo del cuerpo completo (3005) al canon del busto: img2img + lineart ControlNet + IP-Adapter busto s604."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import regen_cn as r
r.CANON = Path("../concepts/vespera/bust/bust_v6_s604.png")
r.OUT = Path("../concepts/vespera/body")
P = ("1girl, solo, vespera, evil seductive demon dealer, anime waifu, dominant unhinged manipulative smirk, "
     "jet black hair, solid pure black hair with a few vivid red streaks, wide black horns with red stripes, glowing red eyes with slit pupils, wide grin with sharp fangs, "
     "medium-large breasts, narrow waist, wide hips, thick thighs, "
     "black high-collar jacket with gold trim and gold buttons, keyhole cleavage window showing skin, black corset with gold lacing, shoulders covered, long black sleeves, "
     "red ruffled cuffs with gold trim and card suit embroidery, black gloves, short layered black skirt with red ruffle hem, opaque solid black thigh-high stockings, no straps, no garter belt, opaque black tights, black ankle boots with gold details, "
     "standing, hand on hip, full body, flat color, cel shading, thick clean black lineart, vivid red and black, very dark burgundy background")
NEG = ", see-through, mesh, navel, midriff, stockings with red stripes, brown hair, gray hair, gray skirt, white blouse, white top, epaulettes, shoulder pads, striped stockings, red stockings, garter, pink background, beige floor, red scribbles on face, extra limbs"
if __name__ == "__main__":
    st, den = float(sys.argv[1]), float(sys.argv[2])
    for s in sys.argv[3:]:
        print(r.regen(int(s), P, strength=st, ipw=0.7, free_y=int(os.environ.get("FREEY","2000")), name=f"v4c_d{int(den*100)}", denoise=den,
                      base=os.environ.get("BASE","../concepts/vespera/body/body_v3_w70_s3005.png"), neg_extra=NEG), flush=True)
