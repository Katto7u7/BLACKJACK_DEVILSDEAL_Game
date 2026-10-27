# Tabla de reacciones (evento de juego → expresión y movimiento)

El juego **no es una novela visual**: el jugador juega blackjack frente a Vespera y ella reacciona en vivo a cada mano. La vista principal es el **busto sobre la mesa** (rig por capas en Godot). Esta tabla fija qué expresión y movimiento dispara cada evento, y de ahí sale la lista de expresiones que hay que dibujar para cada personaje.

## 1. Principios
1. **Reacciona a lo que pasa, no a lo que viene.** La expresión se dispara *después* de que la carta o la resolución sea visible, nunca antes (salvo la pista de trampa, ver §5).
2. **Todo evento tiene reacción**, aunque sea pequeña. Si no ocurre nada, hay microanimación ociosa (parpadeo, respiración, mirada a la mesa, mirada al jugador).
3. **Intensidad en 3 niveles** (1 leve, 2 normal, 3 extrema) según la apuesta y el estado emocional (Fascinación, Desesperación, Desdén). Mismo evento ⇒ misma familia de expresiones, distinta intensidad.
4. **Duración**: 0,6–1,2 s la reacción, 1–3 s si está en mitad de una línea de diálogo; después vuelve a `base` con transición corta (0,2 s).
5. **Cola de prioridades**: una reacción importante (blackjack, trampa, duelo de Sello) interrumpe a una menor; las leves se descartan si hay otra pendiente.
6. **Nunca delata una trampa** salvo con la pista de baja intensidad definida en `biblia_de_arte.md §8`.
7. Cada personaje usa **su subconjunto**; los nombres de expresión son los mismos para facilitar el código (`expr_<nombre>`).

## 2. Eventos de blackjack → Vespera
Expresiones existentes (15): `base, encanto, malicia, arrogancia, burla, celos, culpa, vulnerable, desesperacion, sorpresa, enfado, miedo, ternura, locura, obsesion`.

| Evento | Intensidad 1 | Intensidad 2 | Intensidad 3 | Movimiento |
| --- | --- | --- | --- | --- |
| Reparto inicial | `base` | `malicia` (mano fuerte del jugador: 20/21) | `sorpresa` | mirada a las cartas, leve inclinación |
| El jugador pide carta | `base` | `malicia` | `locura` (si se arriesga con 17+) | se inclina hacia la mesa |
| El jugador se planta | `arrogancia` | `malicia` | `encanto` (si planta con 20/21) | se recuesta |
| El jugador dobla | `malicia` | `encanto` | `locura` | sonrisa, acerca el busto |
| El jugador separa | `sorpresa` | `malicia` | `obsesion` | cabeza ladeada |
| El jugador se rinde | `burla` | `arrogancia` | `culpa` (si Fascinación alta) | mira hacia otro lado |
| El jugador se pasa (>21) | `burla` | `arrogancia` | `locura` (risa) | cuerpo hacia atrás, risa |
| Vespera se pasa | `sorpresa` | `enfado` | `desesperacion` | golpe de cámara, temblor |
| Vespera gana la mano | `arrogancia` | `burla` | `locura` | sonrisa, brazos cruzados |
| Vespera pierde la mano | `enfado` | `celos` (jugador gana mucho) | `desesperacion` | golpe de mesa, pelo agitado |
| Empate | `base` | `malicia` | `obsesion` | inclinación de cabeza |
| Blackjack del jugador | `sorpresa` | `celos` | `enfado` | salta atrás, cuernos tiemblan |
| Blackjack de Vespera | `encanto` | `arrogancia` | `locura` | carcajada |
| Seguro aceptado / acertado | `malicia` | `sorpresa` | `desesperacion` | — |
| Racha ganadora del jugador (3+) | `obsesion` | `celos` | `desesperacion` | mira fijamente |
| Racha perdedora del jugador (3+) | `ternura` | `culpa` | `vulnerable` | desvía la mirada |
| Jugador con pocas fichas | `ternura` | `vulnerable` | `culpa` | voz suave |
| Jugador gana el duelo de Sello | `vulnerable` | `desesperacion` | `miedo` | cabeza baja |
| Jugador pierde el duelo de Sello | `arrogancia` | `burla` | `locura` | — |
| Contrato ofrecido | `encanto` | `malicia` | `obsesion` | extiende el contrato |
| Contrato aceptado | `malicia` | `locura` | `obsesion` | — |
| Contrato rechazado | `enfado` | `celos` | `desesperacion` | — |
| Jugador inspecciona la mesa: acierta | `sorpresa` | `enfado` | `miedo` | retrocede |
| Jugador inspecciona la mesa: falla | `burla` | `arrogancia` | `locura` | señala |
| Jugador descubre trampa confirmada | `miedo` | `desesperacion` | `vulnerable` | desvía la mirada |
| Evento de Nox | `enfado` (hacia Nox) | `celos` | `miedo` | gira la cabeza hacia Nox |
| La Contadora supervisa | `arrogancia` (forzada) | `miedo` | `enfado` | rigidez, sin movimiento |
| Pregunta personal / Confesión | `vulnerable` | `culpa` | `desesperacion` | voz baja |
| Desdén sube (autoboicot) | `arrogancia` | `enfado` | `locura` | cruza los brazos |

## 3. Nox (reacciona al jugador y a Vespera)
Subconjunto base: `base, nervioso, susto, acida, risa, escribe, alivio`.

| Evento | Expresión | Movimiento |
| --- | --- | --- |
| Aparece (evento de Nox) | `nervioso` | mira por encima del hombro |
| Ofrece 3 opciones | `nervioso` → `alivio` si el jugador elige bien | extiende los boletos |
| Jugador elige mal | `susto` | se tapa la cara |
| Vespera ruge o se enfurece | `susto` | se encoge, alas pegadas |
| Jugador gana mucho | `risa` (nerviosa) | se frota la nuca |
| Jugador pierde | `acida` | cruza los brazos, comentario sarcástico |
| Anota en el libro | `escribe` | mueve la pluma |

## 4. La Contadora
Subconjunto base: `base, neutral_severa, evalua, sello, sonrisa_sutil`.

| Evento | Expresión | Movimiento |
| --- | --- | --- |
| Supervisa la mano | `neutral_severa` | sin movimiento |
| Revisa contrato | `evalua` | gafas arriba, pasa páginas |
| Veredicto de fraude | `sello` | estampa |
| Jugador gana limpiamente | `sonrisa_sutil` (rara) | leve cabeceo |

## 5. Pistas de trampa
Las reacciones de baja intensidad de Vespera (microexpresión de `malicia` fuera de contexto, parpadeo asimétrico) pueden ser pistas **si el jugador no lo ve venir**, siempre alineadas con `biblia_de_arte.md §8`. Nunca se sincronizan con la resolución.

## 6. Resultado para el arte
**Vespera (ya hecho, 15):** cubre todo lo anterior. Falta quizá `risa` (carcajada, boca abierta) como expresión propia.
**Nox (pendiente, 7):** `base, nervioso, susto, acida, risa, escribe, alivio`, con parche de parpadeo y de habla.
**La Contadora (pendiente, 5):** `base/neutral_severa, evalua, sello, sonrisa_sutil, enfado_frio`, con parche de parpadeo y de habla.

Cada personaje necesita además: busto aprobado, `cuerpo.png`, `cabeza_<expr>.png`, parches de parpadeo/habla, `rig.json` y `motion_spec.json`, como `rig_v6` de Vespera.
