# Blackjack: Devil's Deal — Plan por fases

Juego de un jugador para Steam. Compra única, ES + EN, sin servidor.
Fuentes: `../../BLACKJACK_DEVILSDEAL/DISENO_COMPLETO.md` (diseño), `../../jb21/` (motor a portar).

Documentos hermanos: `arquitectura.md`, `reglas_y_mecanicas.md`, `biblia_de_arte.md`, `pipeline_arte.md`.

## Decisiones fijas

| Tema | Decisión |
| --- | --- |
| Estilo visual | Anime gótico pulido (novela visual premium) |
| Vista principal | Primera persona sobre la mesa (ref. `referencia_vista_jugador.png`) |
| Motor | Godot 4 + núcleo de reglas en Rust (godot-rust/gdext) |
| Plataforma | Steam (Windows primero; Linux/Steam Deck después) |
| Idiomas | ES + EN desde el día uno (claves de localización) |
| Monetización | Compra única; cosméticos/DLC después. Sin vender fichas, Pulso ni victorias |
| Arte | Concepto en ComfyUI → acabado profesional en Krita (vía MCP ampliado) |

## Fase 0 — Documentos maestros
**Entregables:** los 5 documentos de `docs/`.
**Hecho cuando:** cada sistema de `DISENO_COMPLETO.md` tiene su regla concreta en `reglas_y_mecanicas.md` y su lenguaje visual en `biblia_de_arte.md`.

## Fase 1 — Preparar ComfyUI
**Entregables:** ComfyUI-Manager, checkpoint anime SDXL de licencia comercial, IP-Adapter + CLIP-Vision, ControlNet SDXL, FaceDetailer, upscaler anime; script de lotes `art/tools/comfy_batch.py`; workflows en `art/comfy_workflows/`.
**Hecho cuando:** un prompt de prueba genera una imagen anime vía API (`/prompt` → `/history` → `/view`) y queda registrada en el manifiesto con semilla y prompt.
**Regla:** se verifica la licencia de cada modelo antes de descargarlo; se anota en `art/LICENCIAS_MODELOS.md`.

## Fase 2 — Exploración visual (ComfyUI)
Orden, con aprobación del usuario entre pasos:
1. Pruebas de estilo/checkpoint (3–4 direcciones). **El usuario elige una.**
2. Vespera: turnaround + hoja de 12 expresiones + poses de crupier + vestuarios.
3. Nox, La Contadora, almas visitantes, manos del protagonista.
4. Escena principal en primera persona + 5 fondos de acto.
5. Objetos/UI: naipes, fichas, zapato, contratos, Sellos, Pulso, Cartas de Memoria, ruleta, logo.
6. Escenas clave: accidente, revelación, duelo final, 5 finales.
7. (Opcional) Entrenar LoRA de Vespera con 25–40 imágenes curadas para consistencia a largo plazo.
**Hecho cuando:** la biblia de arte está actualizada con lo aprobado y Vespera es reconocible en 6+ imágenes distintas.

## Fase 3 — Ampliar el MCP de Krita
**Entregables:** capas (listar/crear/renombrar/orden/opacidad/fusión/grupos), importar imagen como capa, selección y máscaras, filtros, transformar/recortar, exportar capa/grupo/todas las capas, `run_script`.
**Hecho cuando:** ida y vuelta completa: importar un concepto → separar en capas → exportar PNGs por capa.

## Fase 4 — Arte final en Krita
Limpieza de línea, color por zonas, separación en capas animables (Vespera: cuerpo, cabello frontal/trasero, ojos, cejas, boca, rubor, manos, cuernos), exportación a `game/assets/`, arte de tienda Steam (cápsulas, cabecera, capturas).
**Hecho cuando:** todos los assets de la lista de `biblia_de_arte.md §10` existen con la nomenclatura definida.

## Fase 5 — Núcleo Rust
Porte de `jb21/backend/blackjack/` + sus tests (`jb21/backend/tests/`), corrigiendo `max_splits`, duplicación de `dealer_should_hit` y seguro. CLI `sim` Monte Carlo.
**Hecho cuando:** `cargo test` en verde con los casos portados; `sim` reproduce la ventaja de la casa esperada para las reglas base.

## Fase 6 — Slice jugable en Godot
Mesa en primera persona, Vespera por capas con expresiones, blackjack completo contra el núcleo Rust, Acto I (tutorial, 1 contrato, duelo de Sello).
**Hecho cuando:** un jugador nuevo completa el Acto I (~10–15 min) sin ayuda externa.

## Fase 7 — Sistemas del concepto
Contratos Vivos, trampas + Inspeccionar la Mesa, Fascinación/Desesperación/Desdén + memoria, Cartas de Memoria, eventos, Mesa de Confesiones, economía (Fondo de Retorno, Pulso, préstamo). Balance con `sim`.
**Hecho cuando:** cada regla de `reglas_y_mecanicas.md` tiene test y la economía de los 5 actos cierra en simulación (conservador y agresivo).

## Fase 8 — Campaña completa
5 actos, 5 finales, guardado entre actos, Casino Eterno, Desafío Diario (semilla), audio, accesibilidad (alto contraste, reducción de movimiento, subtítulos, velocidad de animación).
**Hecho cuando:** campaña de 60–90 min jugable de principio a fin en ES y EN.

## Fase 9 — Steam
GodotSteam (logros, Cloud), cuestionario de contenido generado por IA, clasificación (simulación de apuestas sin dinero real), página de tienda, demo/beta.
**Hecho cuando:** build subida a Steamworks y pasada la revisión.

## Riesgos
- **Consistencia del personaje con IA:** mitigado con IP-Adapter, ControlNet y LoRA propia.
- **Políticas de Steam (IA, apuestas):** declarar uso de IA; sin dinero real ni compras aleatorias.
- **Alcance de arte:** priorizar Vespera y la mesa; el resto en oleadas.
- **Balance:** ninguna cifra económica es definitiva hasta pasar por `sim`.

## Registro de avance
- 2026-10-25: Fase 0 (documentos), Fase 1 (ComfyUI: Animagine XL 4.0, IP-Adapter, upscaler), Fase 3 (MCP de Krita ampliado y verificado).
- 2026-10-26: Fase 2/4 parcial: diseno canon de Vespera aprobado; busto de juego v01 con 15 expresiones, rig por capas, movimiento con muelles y contornos. Lamina: `art/VESPERA_DISENO_FINAL_v01.png`.
- Pendiente de Fase 2/4: Nox, La Contadora, mesa/fondos de acto, naipes y fichas, UI, logo/portada; mejora manual en Krita del busto (manos, dorados, mechones del cuello).
- 2026-10-26 (tarde): cambio de metodo de arte: generacion con ComfyUI (ControlNet Union + IP-Adapter + inpaint de cara) en vez de separacion por color. Vespera v6_s604 aprobada; 15 expresiones (`art/VESPERA_EXPRESIONES_v02.png`); rig simplificado (`game/assets/vespera/rig_v6/`: cuerpo, cabeza por expresion, parches de parpadeo/habla, motion_spec.json); animacion `art/VESPERA_ANIMACION_v02.gif`; editable `art/source/vespera_rig_v6.kra`. Pendiente: cuerpo completo con mas curvas, Nox, Contadora, mesa/fondos, cartas/fichas/UI, LoRA de Vespera.
- 2026-10-27: Fase 5 en marcha: `core/devils_core` (reglas, zapato con semilla, mesa de un jugador con eventos, side bets, estrategia basica) + `core/devils_sim`; 37 tests; ventaja de la casa simulada 0,33% (S17) / 0,49% (H17). Arte: rig v7 de Vespera, poses de cuerpo, fondos de actos I-V y props de mesa listos.
