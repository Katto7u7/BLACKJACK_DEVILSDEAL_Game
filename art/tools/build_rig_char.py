"""Construye rig_v1 (expresiones completas + parches de parpadeo/habla) de Nox o la Contadora. Python embebido de ComfyUI (cv2).
Uso: build_rig_char.py nox|contadora"""
import sys, os, json, shutil
import cv2, numpy as np
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
P = ROOT + "/concepts/personajes/"; FIN = P + "final/"
who = sys.argv[1]
if who == "nox":
    base = FIN + "nox_busto_canon.png"
    ex = {"base": base, **{k: P + f"nox_expr_{k}_b_s7.png" for k in ("nervioso", "susto", "acida", "risa", "escribe", "alivio", "enfado")}}
    fr = {k: P + f"nox_expr_{k}_b_s7.png" for k in ("blink", "talk_a", "talk_b", "talk_c")}
elif who == "vespera":
    V7 = ROOT + "/concepts/vespera/v7/expr/"; base = V7 + "base.png"
    ex = {"base": base, **{k[:-4]: V7 + k for k in os.listdir(V7) if k[:-4] not in ("base", "blink", "talk_a", "talk_b", "talk_c")}}
    fr = {k: V7 + k + ".png" for k in ("blink", "talk_a", "talk_b", "talk_c")}
else:
    base = FIN + "contadora_busto_canon.png"
    ex = {"base": base, "evalua": P + "cont_expr_evalua_b_s8.png", **{k: P + f"cont_expr_{k}_m_s8.png" for k in ("sello", "sonrisa_sutil", "enfado_frio", "sorpresa")}}
    fr = {k: P + f"cont_expr_{k}_b_s7.png" for k in ("blink", "talk_a", "talk_b", "talk_c")}
OUT = ROOT + f"/../game/assets/{who}/" + ("rig_v7/" if who == "vespera" else "rig_v1/"); os.makedirs(OUT, exist_ok=True)
B = cv2.imread(base)
for k, f in ex.items(): shutil.copy(f, OUT + f"cabeza_{k}.png")
def diffmask(f, ylim):
    im = cv2.imread(f).astype(np.int16); d = np.abs(im - B.astype(np.int16)).sum(2)
    m = (d > 60).astype(np.uint8); m[:ylim[0]] = 0; m[ylim[1]:] = 0; m[:, :XL] = 0; m[:, XR:] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return im.astype(np.uint8), m
def bbox(m, pad=14):
    ys, xs = np.nonzero(m); H, W = m.shape
    return int(max(xs.min() - pad, 0)), int(max(ys.min() - pad, 0)), int(min(xs.max() + pad, W)), int(min(ys.max() + pad, H))
# regiones: ojos (y<EY) y boca (y>EY)
EY = {"nox": 368, "vespera": 372}.get(who, 352)
XL, XR = (330, 700) if who == "vespera" else (380, 650)
TH = 90 if who == "vespera" else 110
info = {}
ims = {}; ms = {}
for k, f in fr.items():
    ylim = (150, EY) if k == "blink" else (EY, EY + TH)
    ims[k], ms[k] = diffmask(f, ylim)
bb = bbox(ms["blink"]); info["blink"] = list(bb)
um = np.maximum.reduce([ms[k] for k in ("talk_a", "talk_b", "talk_c")]); tb = bbox(um)
for k in ("talk_a", "talk_b", "talk_c"): info[k] = list(tb)
for k in fr:
    x0, y0, x1, y1 = info[k][0], info[k][1], info[k][2], info[k][3]
    m = cv2.dilate(ms[k], np.ones((9, 9), np.uint8)).astype(np.float32); m = cv2.GaussianBlur(m, (0, 0), 4); m = np.clip(m * 1.4, 0, 1)
    rgba = np.dstack([ims[k], (m * 255).astype(np.uint8)])[y0:y1, x0:x1]
    cv2.imwrite(OUT + f"parche_{k}.png", rgba)
    info[k] = [x0, y0, x1 - x0, y1 - y0]
rig = {"tam": B.shape[1], "expresiones": sorted(ex), "parches": info, "pivote_cabeza": [B.shape[1] // 2, 420]}
json.dump(rig, open(OUT + "rig.json", "w"), indent=1, ensure_ascii=False)
V = json.load(open(ROOT + "/../game/assets/vespera/rig_v6/motion_spec.json", encoding="utf-8"))
V["pivote_cabeza"] = rig["pivote_cabeza"]; V["pivote_cuerpo"] = [B.shape[1] // 2, 900]
if who == "vespera": pass
elif who == "nox":
    V["parpadeo"] = {"intervalo_s": [1.2, 3.0], "duracion_s": 0.12}; V["muelles"]["cabeza_xy"] = [70, 7]; V["habla"]["hz"] = 11
else:
    V["parpadeo"] = {"intervalo_s": [3.5, 7.0], "duracion_s": 0.16}; V["muelles"]["cabeza_xy"] = [45, 11]; V["habla"]["hz"] = 6; V["factores"]["rotacion"] = 0.01
V["linea_tiempo_demo"] = [[0.0, "base"]] + [[1.2 * (i + 1), e] for i, e in enumerate(e for e in sorted(ex) if e != "base")] + [[1.2 * (len(ex) + 1), "base"]]
json.dump(V, open(OUT + "motion_spec.json", "w"), indent=1, ensure_ascii=False)
print(who, info)
