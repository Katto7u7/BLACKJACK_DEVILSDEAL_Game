"""Expresiones de Vespera v7 sobre el busto canon. Uso: klein_vesp_expr.py <semilla> [expr ...]"""
import sys, os, subprocess
HERE=os.path.dirname(os.path.abspath(__file__)); V="../concepts/vespera/v7"
KEEP=("Edit image 1: keep the character, wavy hair, horns, outfit, gloved hands clasped on the table, the cards, framing, table and background EXACTLY identical, same position and size. The irises MUST stay vivid crimson red (never blue, grey or amber), also when wide open or crying. Change ONLY the facial expression (eyes, eyebrows, mouth, blush): ")
E={
 "encanto":"charming and flirty: soft half-lidded crimson eyes, eyebrows relaxed, a sweet seductive smile with a small fang showing, strong blush.",
 "malicia":"wicked scheming: one eyebrow raised, eyes narrowed with tiny slit pupils, a sly crooked grin with sharp fangs.",
 "arrogancia":"arrogant and smug: chin slightly raised, eyes half-closed looking down at the viewer, a confident smirk with one fang.",
 "burla":"mocking: eyes closed in a teasing curve, tongue stuck out slightly with a fanged grin, one eyebrow raised.",
 "celos":"jealous: a pout, eyebrows slanted, eyes narrowed and glaring sideways, cheeks puffed slightly, a flushed face.",
 "culpa":"guilty: eyebrows raised and worried, eyes looking down and away, lips pressed in a small wobbly line, a faint blush.",
 "vulnerable":"vulnerable: big shiny watery eyes, eyebrows tilted up in the middle, a small trembling mouth, a deep blush, a tear at the corner of the eye.",
 "desesperacion":"desperate: wide shaking eyes with tiny pupils, eyebrows pulled up, mouth open in a strained cry, sweat drops, messy hair strands.",
 "sorpresa":"shocked: eyes wide open with tiny pupils, eyebrows high, mouth open in a surprised 'o' showing fangs.",
 "enfado":"furious: eyebrows slanted sharply down, glaring narrow crimson eyes with tiny pupils, teeth bared showing sharp fangs, an anger vein mark on the forehead.",
 "miedo":"scared: pale face, huge trembling eyes with tiny pupils, eyebrows raised, a wobbly mouth, sweat drops.",
 "ternura":"tender: soft warm eyes, gently raised eyebrows, a gentle small smile without fangs, a sweet blush.",
 "locura":"insane: wide manic eyes with shrunken pupils and a glint, an enormous stretched grin full of sharp fangs, eyebrows uneven, a deranged laugh.",
 "obsesion":"obsessed yandere: unblinking wide crimson eyes with dark shadow over the eyes, a fixed small smile, head slightly tilted, an intense stare.",
 "risa":"laughing: eyes closed in happy arcs, mouth wide open laughing with fangs, a strong blush, head tilted slightly back.",
 "blink":"eyes fully closed peacefully as in a blink, eyelids shut with long eyelashes, the same mischievous smile.",
 "talk_a":"mouth slightly open as if speaking, small open mouth with fangs, eyes unchanged, same smile.",
 "talk_b":"mouth open in a round 'o' shape as if speaking, eyes unchanged.",
 "talk_c":"mouth open wide as if saying 'a', showing fangs and tongue, eyes unchanged."}
seed=sys.argv[1]
for k in (sys.argv[2:] or list(E)):
    env=dict(os.environ,REF=f"{V}/busto_canon_v7.png",TAG=f"v7_expr_{k}_",PROMPT=KEEP+E[k]); env.pop("REF2",None)
    subprocess.run([sys.executable,os.path.join(HERE,"klein_chars.py"),seed,"b"],env=env,check=True,cwd=HERE)
