"""Expresiones de La Contadora sobre su busto canon. Uso: klein_cont_expr.py <semilla> [expr ...]"""
import sys, os, subprocess
HERE=os.path.dirname(os.path.abspath(__file__)); FIN="../concepts/personajes/final"
KEEP=("Edit image 1: keep the character, hair, halo, glasses, outfit, ledger, seal, hands, pose, framing, table and background EXACTLY identical, same position and size. Keep the small beauty mark under her left eye. Keep her forehead smooth with no wrinkles and a young face. Change ONLY the facial expression (eyes, eyebrows, mouth): ")
E={"evalua":"evaluating: one eyebrow slightly raised, eyes narrowed and looking down her nose through the glasses at the viewer, lips pressed in a thin line, a judging look.",
   "sello":"firm and decisive: eyes looking down toward the ledger, eyebrows lowered with authority, mouth a firm straight line, severe stern face.",
   "sonrisa_sutil":"a rare faint small smile: the corners of her lips slightly raised, eyes softened and slightly closed, eyebrows relaxed, very subtle warmth.",
   "enfado_frio":"cold anger: eyebrows lowered and slanted, eyes icy and narrowed with a piercing glare, lips pressed tight, no shouting, controlled fury.",
   "blink":"eyes fully closed peacefully as in a blink, eyelids shut with eyelashes, neutral calm mouth.",
   "talk_a":"mouth slightly open as if speaking, small open mouth, calm cold expression, eyes unchanged.",
   "talk_b":"mouth open in a round 'o' shape as if speaking, calm cold expression, eyes unchanged.",
   "talk_c":"mouth open wide as if saying 'a', showing teeth and tongue slightly, calm cold expression, eyes unchanged.",
   "sorpresa":"rare surprise: eyes opened wide, eyebrows raised high, lips slightly parted, still composed."}
seed=sys.argv[1]
for k in (sys.argv[2:] or [x for x in E if not x.startswith(("blink","talk"))]):
    env=dict(os.environ,REF=f"{FIN}/contadora_busto_canon.png",TAG=f"cont_expr_{k}_",PROMPT=KEEP+E[k])
    env.pop("REF2",None)
    subprocess.run([sys.executable,os.path.join(HERE,"klein_chars.py"),seed,"b"],env=env,check=True,cwd=HERE)
