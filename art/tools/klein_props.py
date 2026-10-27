"""Props y fondo de mesa (sin personajes) con klein, estilo de ref = busto v7. Uso: klein_props.py <semilla> [clave ...]"""
import os, sys, subprocess
HERE=os.path.dirname(os.path.abspath(__file__))
ST=("Use image 1 ONLY as the art style reference (flat cel-shaded anime, thick black outlines, vivid saturated colors, strong dark shadows, burgundy and black palette with gold accents). Do NOT draw any person or character from image 1. ")
P={
 "fondo_acto1":(1536,864,"A first-person view of an elegant gothic casino blackjack table in an empty hall, NO people: a wide curved table with dark green felt and an ornate gold-trimmed black edge in the lower half, a card shoe at the right, small candelabras with candle flames on both sides, tall dark red velvet curtains and glowing shelves with bottles in the background, warm candlelight with crimson rim light, empty center of the table left free for cards, no text."),
 "fichas":(1024,1024,"A sheet of 5 casino chips in a row, each seen from a three-quarter view with a thin gold edge and an engraved horn emblem, in 5 colors: white-ivory, red crimson, black, gold, deep purple, plus one extra glowing spectral blue memory chip on a second row; plain dark burgundy background, no numbers, no text."),
 "dorso":(768,1152,"A single playing card BACK design, portrait, ruby red with an ornate gold border and a central gold devil-horn emblem with spade, heart, diamond and club symbols in the corners, symmetrical, ivory outer margin, flat cel style, on a plain dark burgundy background, no text."),
 "zapato":(1024,1024,"A casino card dealing shoe: a black and gold gothic box with a slanted opening holding a stack of cards with ruby backs, subtle red glow, three-quarter view, on a plain dark burgundy background, no text."),
 "contrato":(1024,1024,"A rolled open parchment contract, black-red aged paper with gold ornate border, blank lines of faint glowing fire-orange script without readable letters, sealed with a red wax seal at the bottom, flat on a plain dark burgundy background, no readable text."),
 "sellos":(1024,1024,"A sheet of 5 wax seals in a row of different designs, each a round red-and-gold seal: horns, heart, eye, key, crown; plain dark burgundy background, no text."),
 "manos_jugador":(1536,864,"First-person view of the PLAYER's own two bare hands (neutral skin tone, no gloves, no gender cues) resting on dark green casino felt in the foreground, seen from above and from behind the hands, fingers relaxed, with two playing cards between them, bottom of the frame, dark burgundy blurred background, five fingers each hand, no text."),
}

for i,(n,d) in enumerate({"cuernos":"two small devil horns","corazon":"a heart with a crack","ojo":"an open eye","llave":"an ornate key","corona":"a crown"}.items()):
    P["sello_"+n]=(768,768,"A single round red wax seal with a gold rim stamped with "+d+" in gold relief, centered, one object only, plain dark burgundy background, no text.")
for i,(n,d) in enumerate({"acto2":"more intimate and jewel-toned: a smaller room, deep wine-red velvet, gold jewelry boxes and mirrors on the walls, many candles, soft warm light",
  "acto3":"shadows and mirrors: tall dark mirrors reflecting nothing, thick smoke on the floor, flickering cold candles, high contrast, deep shadow",
  "acto4":"red-dominant and cracked: the walls and floor have glowing red cracks, crimson light everywhere, dark silhouettes of furniture, a hostile mood",
  "acto5":"almost total void: black emptiness all around, only the green table lit by a single crimson spotlight, one candle, nothing else"}.items()):
    P["fondo_"+n]=(1536,864,"Edit image 2 into a different version: the same empty first-person casino table view with NO people but "+d+". Keep the same flat cel anime style, curved table with dark green felt and gold trim at the bottom, empty center of the table, no text.")
seed=sys.argv[1]
for k in (sys.argv[2:] or list(P)):
    w,h,t=P[k]
    code=f"import klein_chars as K;print(K.gen('{k}',{seed},{w},{h}))"
    env=dict(os.environ,REF="../concepts/vespera/v7/busto_canon_v7.png",TAG="prop_",PROMPT=ST+t); env.pop("REF2",None)
    if k.startswith("fondo_acto") and k!="fondo_acto1": env["REF2"]="../concepts/mesa/fondo_acto1.png"
    subprocess.run([sys.executable,"-c",code],env=env,check=True,cwd=HERE)
