"""Pasada de unificacion del cuerpo completo: img2img suave con lineart fuerte, para igualar trazo/color/sombreado entre busto y cuerpo."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import regen_cn as r
r.CANON = Path("../concepts/vespera/bust/bust_v6_s604.png"); r.OUT = Path("../concepts/vespera/body")
P = ("1girl, solo, vespera, demon girl, jet black hair with vivid red streaks, wide black horns with red stripes, red eyes, wide grin with sharp fangs, "
     "black high-collar jacket with gold trim, grey corset bodice with gold buttons, red ruffled cuffs, black gloves, short black skirt with red ruffle, black stockings, black boots with gold, "
     "full body, standing, flat color, cel shading, thick clean black lineart, vivid red and black, dark burgundy background")
if __name__ == "__main__":
    den = float(sys.argv[1])
    for s in sys.argv[2:]:
        print(r.regen(int(s), P, strength=0.9, ipw=0.5, free_y=3000, name=f"unif_d{int(den*100)}", denoise=den,
                      base="../concepts/vespera/body/out2_d100_s7101.png", neg_extra=", pink background, brown hair, gray hair"), flush=True)
