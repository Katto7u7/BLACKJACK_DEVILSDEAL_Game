import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import regen_cn as r

P = ("1girl, vespera, evil seductive demon dealer, very attractive anime waifu with a dominant, unhinged, manipulative aura, "
     "jet black hair with vivid red streaks, pure black hair, wide black horns with red stripes, "
     "glowing red eyes with narrow slit pupils, wide manic grin with sharp fangs, intense predatory stare, one eyebrow raised, slight blush, "
     "curvy hourglass figure, large breasts, cleavage, black corset bodice with gold trim, keyhole neckline, shoulders covered, "
     "sleeved arms from shoulders to hands, hands clasped on table, black gloves, red ruffled cuffs with gold trim and embroidered playing card suit symbols spade heart club diamond, "
     "flat color, cel shading, thick clean black lineart, vivid red and black, upper body, front view")
NEG = ", brown hair, dark brown hair, gray hair, cute, innocent, shy, soft smile, pastel"

if __name__ == "__main__":
    den = float(sys.argv[1])
    for s in sys.argv[2:]:
        print(r.regen(int(s), P, strength=0.7, ipw=0.45, free_y=1100, name=f"v6_d{int(den*100)}", denoise=den,
                      base="../concepts/vespera/bust/bust_v5_s502.png", neg_extra=NEG), flush=True)
