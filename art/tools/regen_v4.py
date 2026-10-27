import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import regen_cn as r

BASE_P = ("1girl, vespera, beautiful seductive demon waitress, very attractive anime waifu, long jet black hair with vivid red streaks, wide black horns, "
          "glowing red eyes with long lashes, alluring smirk with small fangs, slight blush, "
          "curvy hourglass figure, large breasts, cleavage, slim waist, wide hips, "
          "black fitted corset bodice with gold trim and gold lacing, keyhole neckline, shoulders covered by black sleeves, "
          "forearms resting on the table leading to hands clasped together, black gloves, ruffled red cuffs with gold trim, "
          "sleeved arms coming down from the shoulders to the table, forearms clearly visible, arms connected naturally to the body, one continuous drawing, sitting at a table, flat color, cel shading, thick clean black lineart, vivid red and black, upper body, front view")

if __name__ == "__main__":
    free_y = int(sys.argv[1])
    for s in sys.argv[2:]:
        print(r.regen(int(s), BASE_P, strength=0.75, ipw=0.45, free_y=free_y, name=f"v5_y{free_y}"), flush=True)
