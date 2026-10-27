"""Busto de La Contadora. Uso: klein_cont_bust.py <semilla> [...]"""
import sys, os, subprocess
HERE=os.path.dirname(os.path.abspath(__file__)); FIN="../concepts/personajes/final"
P=("Image 1 is the full-body character and image 2 is a close-up of her face: keep EXACTLY the same face, grey eyes, rectangular glasses, silver-white hair with the side braid, thin gold halo, beauty mark, white tuxedo jacket with gold lapels and gold bow tie, fully closed jacket with NO cleavage, large bust, white gloves. "
   "New framing: a chest-up bust portrait seen from the front at a casino table, front-facing, centered, torso cropped at the waist, cold calm expressionless face looking at the viewer, holding the open ledger in front of her chest with one hand and the gold seal stamp in the other, the edge of a table in front of her. Flat cel anime, thick outlines, vivid colors, strong shadows, plain dark burgundy background.")
for s in sys.argv[1:]:
    env=dict(os.environ,REF=f"{FIN}/contadora_canon.png",REF2=f"{FIN}/contadora_canon_cabeza.png",TAG="cont_bust_",PROMPT=P)
    subprocess.run([sys.executable,os.path.join(HERE,"klein_chars.py"),s,"b"],env=env,check=True,cwd=HERE)
