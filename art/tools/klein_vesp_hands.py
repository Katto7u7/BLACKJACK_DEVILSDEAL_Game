"""Acciones de manos de Vespera en la mesa (gameplay). Uso: klein_vesp_hands.py <semilla> [accion ...]"""
import sys, os, subprocess
HERE=os.path.dirname(os.path.abspath(__file__)); V="../concepts/vespera/v7"
KEEP=("Edit image 1: keep her face, expression, wavy hair, horns, outfit, framing, table and background identical, same position and size, same chest-up front view over the casino table. Change ONLY what her hands and arms are doing, with five correct fingers on each hand and well-formed gloved hands: ")
A={
 "reparte":"she is dealing: her right gloved hand slides a single face-down playing card across the green felt toward the viewer, the card in motion near the front edge of the table, her left hand rests flat on the table.",
 "baraja":"she is shuffling a deck of cards: both gloved hands hold a deck at chest height and bend it in a riffle shuffle, cards fanning between her hands.",
 "voltea":"she is flipping a card: one gloved index finger and thumb lift the corner of a face-down card on the table to reveal it, the other hand flat on the table.",
 "fichas":"she is pushing a small stack of gold casino chips across the felt toward the viewer with the fingertips of one gloved hand, the other hand resting on the table.",
 "tamborilea":"one gloved hand is flat on the table with the fingers drumming impatiently on the felt, the other hand rests under her chin holding up her head.",
 "barbilla":"both elbows rest on the table and her gloved hands are interlaced under her chin, supporting it, leaning toward the viewer.",
 "senala":"she leans forward over the table and aims her gloved index finger straight at the viewer, the pointing hand horizontal and very close to the camera, finger tip toward us; the other hand flat on the table.",
 "palma":"her right forearm lies on the green felt of the table, stretched forward, and the gloved hand lies on the felt with the PALM FACING UP and fingers slightly curled, open and waiting for coins; the hand is low, resting on the table, not raised; the other hand flat on the table.",
 "palma2":"she holds her right forearm horizontally in front of her chest pointing toward the viewer, the gloved hand open with the palm turned UP like a cupped hand waiting to be paid, fingers pointing at the camera and seen foreshortened from the side, the back of the hand toward the floor; she smirks greedily; the other hand flat on the table.",
 "palma3":"she cups one open gloved hand palm-up in the air above the table, as if holding an invisible coin: the thumb side faces the viewer, fingers curled upward, a gesture of asking for money; the other hand flat on the table.",
 "contrato":"she holds up a rolled parchment contract sealed with a red wax seal between two fingers in one gloved hand, the other hand flat on the table.",
 "cruza":"she sits upright and crosses her arms over her chest, the left forearm over the right, each gloved hand tucked under the opposite upper arm, haughty pose, hands not clasped and not on the table."}
seed=sys.argv[1]
for k in (sys.argv[2:] or list(A)):
    env=dict(os.environ,REF=f"{V}/busto_canon_v7.png",TAG=f"v7_mano_{k}_",PROMPT=KEEP+A[k]); env.pop("REF2",None)
    subprocess.run([sys.executable,os.path.join(HERE,"klein_chars.py"),seed,"b"],env=env,check=True,cwd=HERE)
