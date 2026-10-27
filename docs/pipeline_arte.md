# Pipeline de arte

```
Brief (biblia_de_arte) → ComfyUI (conceptos) → selección → Krita (acabado, capas) → export → game/assets
```

## 1. Generación (ComfyUI, `http://127.0.0.1:8188`)
- Hardware: RTX 3060 12 GB → SDXL con resolución base ~832×1216 / 1216×832 / 1024×1024 y upscale posterior.
- **Un solo checkpoint anime** para todo el proyecto (se elige en Fase 2.1). Cambiarlo rompe la consistencia.
- Consistencia:
  1. **Prompt maestro** de Vespera fijo (rasgos + paleta) en `art/comfy_workflows/prompts.md`.
  2. **IP-Adapter** con 2–3 imágenes de referencia aprobadas de Vespera.
  3. **ControlNet** (pose/lineart/depth) para poses y composiciones repetibles.
  4. **FaceDetailer** para caras/manos.
  5. **LoRA de Vespera** entrenada con 25–40 imágenes curadas (cuando exista el set).
- Cada imagen registra en `art/concepts/_manifest.json`: archivo, workflow, checkpoint, LoRAs, prompt, negativo, semilla, parámetros, estado (`candidato|aprobado|descartado`).
- Salida a `art/concepts/<categoria>/` con nomenclatura de la biblia.
- Lotes con `art/tools/comfy_batch.py` (cola vía API; reproducible por semilla).
- Licencias de modelos en `art/LICENCIAS_MODELOS.md` (uso comercial verificado).

## 2. Revisión
Tandas pequeñas (4–8) → presentación al usuario → aprobar/pedir cambios → se actualiza la biblia. Nada se produce en serie hasta aprobar la dirección.

## 3. Acabado (Krita vía MCP en `127.0.0.1:5678`)
Flujo por asset aprobado:
1. `import_image_as_layer` del concepto (upscalado).
2. Limpieza de línea y corrección de anatomía/manos (trazos/filtros/`run_script`).
3. Color plano por zonas + sombreado según biblia.
4. Separación en capas animables (personajes) y grupos nombrados.
5. Guardar `.kra` en `art/source/`.
6. Exportar PNGs por capa/grupo a `game/assets/<categoria>/`.
Herramientas dependen de la Fase 3 (capas, importación, selección, filtros, exportación, `run_script`).

## 4. Integración al juego
`game/assets/` importado por Godot; atlas y recorte automáticos; el texto (títulos, cartas, UI) se compone en el motor, nunca viene horneado desde IA.

## 5. Cumplimiento
- Declarar contenido generado por IA en el cuestionario de Steam (el acabado y rediseño en Krita no exime de declararlo).
- Guardar el manifiesto de generación como registro de procedencia.
- Fuentes, música y SFX con licencia comercial documentada.

## 6. Estado real del pipeline (2026-10-26) — busto de Vespera v01
Flujo probado de punta a punta (scripts en `art/tools/`):
1. **Base:** `comfy_batch.py` con IP-Adapter (style transfer 0.5) -> `art/concepts/vespera/bust/bust_base_s12003.png`.
2. **Escalado:** `comfy_tools.upscale4x` (Real-ESRGAN anime) a 4096 px.
3. **Capas:** `bust_pipeline.py base` -> paleta fija (clasificacion por color mas cercano), partes por poligonos (`cuerno_izq/der, pelo_trasero, torso, pelo_frente, mano_izq/der, cabeza`), cada una con `color / sombra_propia / linea`; reducidas a 2048 promediando (bordes con antialias).
4. **Expresiones:** `comfy_tools.inpaint` sobre la zona de ojos o boca (mascara rectangular) -> `bust_pipeline.py variants` genera parches `ojos_*` y `boca_*` (9 y 9 estados) que se intercambian sobre la cabeza.
5. **Rig y movimiento:** `vespera_rig.py` (compositor, 15 expresiones) y `anim_bust.py` (muelles, parpadeo, labios, reacciones; escribe `motion_spec.json`).
6. **Edicion:** `art/source/vespera_bust_v01.kra` (grupos por parte, estados de ojos/boca como grupos conmutables) y exportacion a `game/assets/vespera/bust/`.
Lecciones: IP-Adapter `linear` o peso alto degrada; el inpainting de ojos puede cambiar el color del iris (forzar "red eyes" y prohibir otros colores en el negativo); los contornos claros por parte son necesarios sobre fondos oscuros; las partes deben solaparse unos pixeles para evitar costuras.

## 7. Pipeline v2 (2026-10-26) — ComfyUI-first
1. Guia: Canny del busto aprobado (borrando la zona a rehacer, con degradado) -> `tools/regen_cn.py` / `regen_v4.py` / `regen_v6.py` (ControlNet Union promax + IP-Adapter style transfer 0.45 + img2img). Ejecutar con `python_embeded` de ComfyUI (tiene OpenCV).
2. Expresiones: `tools/expr_v6.py` (zona de cara poligonal + mezcla suave) y `tools/expr_parts_v6.py` (ojos cerrados y bocas). Semilla 701 deriva a piel gris.
3. Rig: `tools/rig_v6.py up|build` (ESRGAN 4x -> 2048, fondo fuera sin rellenar huecos grandes, cabeza cortada con degradado de 56 px en cuello/costados, relleno LaMa bajo la cabeza, bordes descontaminados).
4. Animacion de prueba: `tools/anim_rig_v6.py` (muelles, parpadeo, habla, reacciones). En el juego la anima Godot con `motion_spec.json`.
5. Editable en Krita: `art/source/vespera_rig_v6.kra`.

## 8. Pipeline v3 (2026-10-27) — FLUX.2 klein 4B (Apache-2.0)
- Edicion por referencia en ComfyUI (`UNETLoader` + `CLIPLoader type=flux2` + `ReferenceLatent`, 4 pasos, cfg 1). Mantiene cara, atuendo y colores; segundos por imagen. Se usa canon de cuerpo + recorte de cabeza como 2 referencias.
- Vespera canon v7 (pelo ondulado, off-shoulder con volantes): busto `art/concepts/vespera/v7/busto_canon_v7.png`, 19 expresiones + parpadeo/habla, 10 acciones de manos en la mesa, 9 poses de cuerpo. Rig: `game/assets/vespera/rig_v7/` (`tools/build_rig_char.py vespera`, entorno python_embeded).
- Nox y La Contadora: `game/assets/{nox,contadora}/rig_v1/`.
- Mesa: `tools/klein_props.py` (fondos actos I-V, fichas, zapato, contrato, dorso, sellos, manos del jugador); recortes con `tools/cutout2.py` en `art/concepts/mesa/recortes/`. El texto/numeros de cartas se componen en Godot.
- Reacciones del juego: `docs/tabla_reacciones.md`.
- Licencias a registrar: FLUX.2 klein 4B Apache-2.0; MAT (CC-BY-NC) NO usado.
