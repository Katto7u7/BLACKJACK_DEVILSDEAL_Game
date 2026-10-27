"""Busto de Vespera v7 (canon cuerpo v4 ondulada). Uso: klein_vesp_bust.py <semilla...>"""
import sys, os, subprocess
HERE=os.path.dirname(os.path.abspath(__file__)); V="../concepts/vespera/v7"
P=("Image 1 is the full-body character and image 2 is a close-up of her face: keep EXACTLY the same face, big crimson eyes, long wavy curly black hair with crimson red streaks, large black horns, fanged mischievous smile, high collar, keyhole chest opening, covered shoulders, long sleeves with red ruffled cuffs, black gloves, black corset with gold lacing. "
   "New framing: a close-up bust portrait, chest-up, seen from the front like a first-person view across a casino table, centered and facing the viewer, leaning slightly toward the viewer with her gloved hands clasped together on the dark green felt table in front of her, two playing cards lying on the table, a mad seductive confident grin. "
   "Flat cel anime, thick outlines, vivid saturated colors, strong dark shadows, plain dark burgundy background, 1:1 composition with the horns and hair filling the frame.")
for s in sys.argv[1:]:
    env=dict(os.environ,REF=f"{V}/body_canon_v4.png",REF2=f"{V}/head_ref.png",TAG="v7_bust_",PROMPT=P)
    subprocess.run([sys.executable,os.path.join(HERE,"klein_chars.py"),s,"b"],env=env,check=True,cwd=HERE)
