"""Expresiones de Nox sobre su busto canon. Uso: klein_nox_expr.py <semilla> [expr ...]"""
import sys, os, subprocess
HERE=os.path.dirname(os.path.abspath(__file__)); FIN="../concepts/personajes/final"
KEEP=("Edit image 1: keep the character, hair, horns, glasses, outfit, wings, ledger, hands, pose, framing, table and background EXACTLY identical, same position and size. Change ONLY the facial expression and eyes/mouth/eyebrows: ")
E={"nervioso":"nervous and worried: eyebrows raised and tilted up in the middle, a small tight wobbly mouth, a sweat drop, a blush.",
   "susto":"terrified: eyes wide with tiny pupils, mouth wide open screaming, sweat drops flying, pale face.",
   "acida":"sarcastic and acid: one eyebrow raised, eyes half-closed looking down at the viewer, a crooked smirk showing one small fang.",
   "risa":"nervous laughter: eyes closed in a happy curve, wide open smiling mouth, a big sweat drop, a heavy blush.",
   "escribe":"concentrated: eyes looking down toward the ledger, eyebrows slightly furrowed, mouth a small flat line, calm focused expression.",
   "alivio":"relieved: eyes closed softly, a gentle exhale with a small relieved smile, eyebrows relaxed, a sweat drop sliding down.",
   "blink":"eyes fully closed peacefully as in a blink, eyelids shut with eyelashes, the same small smile.",
   "talk_a":"mouth slightly open as if speaking, small open mouth, eyes unchanged, same nervous smile.",
   "talk_b":"mouth open in a round 'o' shape as if speaking, eyes unchanged.",
   "talk_c":"mouth open wide as if saying 'a' showing small fangs, eyes unchanged.",
   "enfado":"angry: eyebrows slanted down sharply, narrowed glaring green eyes, teeth clenched showing small fangs, a cheek blush."}
seed=sys.argv[1]
for k in (sys.argv[2:] or [x for x in E if not x.startswith(("blink","talk"))]):
    env=dict(os.environ,REF=f"{FIN}/nox_busto_canon.png",TAG=f"nox_expr_{k}_",PROMPT=KEEP+E[k])
    env.pop("REF2",None)
    subprocess.run([sys.executable,os.path.join(HERE,"klein_chars.py"),seed,"b"],env=env,check=True,cwd=HERE)
