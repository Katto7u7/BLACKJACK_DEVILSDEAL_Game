"""Busto de Nox con klein. Uso: klein_nox_bust.py <semilla> [semilla...]"""
import sys, os, subprocess
HERE=os.path.dirname(os.path.abspath(__file__)); FIN="../concepts/personajes/final"
P=("Image 1 is the full-body character and image 2 is a close-up of her face: keep EXACTLY the same face, eye shape, round glasses, hair (black with green streaks on the front bangs and left side), small black horns, pointy ears, bat wings, black vest with gold buttons, white blouse, black bow tie. "
   "New framing: a chest-up bust portrait seen from the front at a casino table, front-facing, centered, torso cropped at the waist, facing the viewer with a small nervous smile, her hands holding the ledger in front of her chest, the black bat wings visible behind her shoulders. Flat cel anime, thick outlines, vivid colors, strong shadows, plain dark burgundy background.")
for s in sys.argv[1:]:
    env=dict(os.environ,REF=f"{FIN}/nox_canon.png",REF2=f"{FIN}/nox_canon_cabeza.png",TAG="nox_bust_",PROMPT=P)
    subprocess.run([sys.executable,os.path.join(HERE,"klein_chars.py"),s,"b"],env=env,check=True,cwd=HERE)
