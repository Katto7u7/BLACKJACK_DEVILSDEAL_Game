"""Poses de Nox y La Contadora con klein (ref = canon). Uso: klein_chars_poses.py <semilla> [nox|cont]"""
import sys, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
FIN = "../concepts/personajes/final"
KEEP = {"nox": "Image 2 is a close-up of her face and hair: copy that exact face, eye shape, round glasses and hair (black hair with green streaks only on the front bangs and left side) EXACTLY. Keep exactly the same character as image 1: same face, short black hair with sulfur-green streaks, small black horns, pointy ears, round glasses, green eyes, bat wings and tail, black vest with gold buttons, white blouse, black bow tie, black skirt with green trim, black tights, same proportions and height, flat cel anime style, thick outlines, vivid colors with strong shadows, plain dark burgundy background, full body head to toe. ",
        "cont": "Keep exactly the same character as image 1: same face, silver-white hair with side braid, thin gold halo, rectangular glasses, grey eyes, white tuxedo jacket with gold lapels and gold bow tie, fully closed jacket with NO cleavage, same large bust, white skirt, grey stockings, white heels, white gloves, same proportions and height, flat cel anime style, thick outlines, vivid colors with strong shadows, plain dark burgundy background, full body head to toe. "}
P = {"nox": {
  "lado": "New pose: three-quarter side view turned to the right, hugging the ledger, glancing nervously at the viewer over her shoulder.",
  "espalda": "New pose: seen from behind, looking back over her shoulder nervously, wings and tail visible.",
  "oferta": "New pose: holding out three glowing sulfur-green tickets fanned in one hand toward the viewer with a nervous sly smile, the ledger under the other arm.",
  "susto": "New pose: terrified, both hands pressed against her cheeks, wide eyes with tiny pupils, sweat drops, mouth open in a scream, wings spread in panic.",
  "acida": "New pose: arms crossed, hip cocked, a sarcastic acid smirk with one eyebrow raised and fangs showing, the ledger tucked under her arm.",
  "risa": "New pose: laughing nervously with one hand behind her head, eyes closed, sweat drop, blushing.",
  "escribe": "New pose: writing in the ledger with the quill, looking at the viewer over her glasses with a suspicious squint."},
 "cont": {
  "lado": "New pose: three-quarter side view turned to the right, holding the ledger against her chest, looking at the viewer with a cold calm gaze.",
  "espalda": "New pose: seen from behind, looking back over her shoulder with a cold calm gaze, braid and halo visible.",
  "sello": "New pose: standing with both feet planted on the ground, holding the open ledger flat in her left hand at chest height and pressing the round gold seal stamp firmly down onto the open page with her right hand, looking down at the ledger, severe impartial expression.",
  "juicio": "New pose: one arm extended pointing a gloved finger firmly at the viewer, the ledger held open in the other hand, stern expression, a slight frown.",
  "brazos": "New pose: standing with arms crossed under the bust, ledger tucked under one arm, chin slightly raised, expressionless cold stare.",
  "sonrisa": "New pose: a rare faint small smile, eyes slightly softened, holding the ledger to her chest with both hands."}}
who = sys.argv[2:] or ["nox", "cont"]
seed = sys.argv[1]
for w in who:
    ref = {"nox": f"{FIN}/nox_canon.png", "cont": f"{FIN}/contadora_canon.png"}[w]
    h = {"nox": "1280", "cont": "1376"}[w]
    for k, v in P[w].items():
        if os.environ.get("POSE") and k != os.environ["POSE"]: continue
        env = dict(os.environ, REF=ref, REF2=(f"{FIN}/nox_canon_cabeza.png" if w=="nox" else ""), TAG=f"{w}_pose2_", PROMPT=KEEP[w] + v)
        subprocess.run([sys.executable, os.path.join(HERE, "klein_chars.py"), seed, k], env=env, check=True, cwd=HERE)
