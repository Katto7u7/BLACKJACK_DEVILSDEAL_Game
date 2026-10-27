# Biblia de arte — Blackjack: Devil's Deal

Fuente de verdad visual. Todo asset debe poder justificarse con esta página. Se actualiza con lo aprobado en Fase 2.

## 1. Estilo
**Anime gótico pulido / novela visual premium.** Línea limpia de grosor variable (más fina en rostro, más gruesa en siluetas), sombreado cel de 2–3 tonos con gradiente suave en piel y cabello, brillos especulares duros en oro, terciopelo y vidrio.
Referencias del usuario: `vespera.png` (diseño de personaje, vestuario, tono elegante) y `referencia_vista_jugador.png` (composición en primera persona, mano del jugador, mesa con mantel ornamentado, estantes con luz de neón).
Evitar: realismo fotográfico, 3D plástico, texturas ruidosas de IA, manos deformes, texto generado por IA dentro de la imagen (el texto se compone en el motor).

### Estilo aprobado (2026-10-25): dirección B — "cel plano"
Línea negra gruesa y uniforme, colores planos por zonas con sombra cel de 1–2 tonos, paleta limitada, fondo simple. Elegido por su facilidad de limpiar y separar en capas en Krita y de animar en motor. Referencia aprobada: `art/concepts/tests/styleB_vespera_cel_s2000.png`. Las escenas (fondos, CG) usan el mismo grosor de línea y paleta, con más detalle de fondo pero sin degradados fotográficos.
Los estilos A (elegante/cálido) y C (pintura oscura) quedan descartados salvo como inspiración de iluminación.

### Vespera — diseño canon v01 (aprobado 2026-10-25)
Referencia: `art/concepts/vespera/ref/vespera_canon_v01.png` (origen `sheet/vespera_v4_s8001.png`).
Rasgos: pelo negro azabache larguísimo con mechones rojo vivo, cuernos negros anchos con brillo rojo, ojos rojos, sonrisa desquiciada con dientes afilados (aspecto dominante/yandere), vestido de cuello alto con escote ojo de cerradura y hombros cubiertos, mangas largas con puños de volante rojo, corsé negro con cordones dorados, falda corta en capas con volante rojo, medias negras y botines con detalles dorados. Colores vivos e intensos (rojo carmesí saturado, negro profundo, oro brillante).
Vistas: lado y espalda en `sheet/vespera_side2_s9301.png` y `sheet/vespera_back2_s9202.png`; 12 expresiones en `expr/`.
Skin DLC reservada: pelo corto (de la propuesta 2 de la primera ronda).
Receta de consistencia: IP-Adapter `style transfer`, peso 0.45–0.5, con la referencia canon (peso mayor o `linear` degrada la imagen y fuerza la vista frontal).

## 2. Paleta
| Rol | Color | Uso |
| --- | --- | --- |
| Negro carbón | `#130D0F` | fondos, sombras |
| Vino profundo | `#651E2A` | terciopelo, vestido, mantel |
| Rojo rubí | `#B23339` | acentos, ojos, peligro |
| Oro envejecido | `#A87B39` | marcos, índices, UI |
| Marfil cálido | `#F9F4EC` | cartas, texto, highlights |
| Azul espectral (acento) | `#6FA8C9` | recuerdos, almas, **pistas de trampa de baja intensidad** |
| Verde azufre (acento) | `#8FB04A` | Nox |
Regla 60/30/10: 60% oscuros, 30% vino/rubí, 10% oro/marfil. El azul/verde solo como acento semántico.

## 3. Iluminación
Cálida de velas/candelabros como luz clave; rim light carmesí desde ventanales; luz puntual dorada sobre la mesa. Cada acto sube el contraste y la saturación roja (I cálido y elegante → V casi monocromo rojo/negro). Las trampas rompen la paleta con un destello controlado.

## 4. Vespera
- Demonio adulta, cabello largo negro con reflejos rubí/caoba, **ojos rojos luminosos**, **cuernos negros curvos**, expresión que oscila entre encanto y vulnerabilidad. Atractiva por carisma y presencia, no caricaturizada.
- Vestuario base: vestido borgoña y negro con bordados dorados, escote moderado, cuello alto de encaje, guantes opcionales. (Ref. `vespera.png`: capas, volantes rojos y negros, lazos.)
- Siluetas: base crupier clásico, gótico, gala infernal, blanco-dorado "ángel irónico", temporada (skins DLC).
- **12 expresiones:** encanto, malicia, arrogancia, celos, culpa, vulnerabilidad, desesperación, sorpresa, enfado, burla, ternura, miedo.
- Debe poder seccionarse en capas animables (§9).

## 5. Otros personajes
- **Nox:** demonio pequeño, empleado del casino, nervioso y ácido. Silueta redonda, gafas/libreta de registros, acento verde azufre.
- **La Contadora:** árbitra neutral, alta, sobria, blanco/gris/oro, sin la calidez de Vespera. Libro mayor y sello.
- **Almas visitantes:** semitransparentes en azul espectral, cada una con silueta y época distintas.
- **Protagonista:** solo se ven **sus manos/brazos** en primera persona (género sin definir). Recuerdos como siluetas o fragmentos.

## 6. Escenario: Casino del Último Suspiro
Mármol negro, terciopelo burdeos, candelabros barrocos, oro envejecido, vitrales rojos, ciudad infernal tras ventanales, clientes espectrales al fondo. Art déco infernal.
**Vista principal (gameplay):** primera persona; Vespera centrada detrás de la mesa, zapato a la derecha, mantel ornamentado en primer plano, estantes/vitrinas iluminados al fondo. Zona de cartas libre de elementos para legibilidad.
**5 fondos de acto:** I elegante y cálido · II más íntimo, más joyas · III sombras y espejos, humo · IV rojo dominante, grietas · V vacío casi total, solo la mesa.

## 7. Objetos y UI
- **Naipes:** marfil, borde dorado fino, índices grandes (accesibilidad); palos distinguibles por forma además de color (modo alto contraste: palos rojos con patrón). Dorso: rubí y oro con emblema del casino. Carta fantasma: dorso con **marca extraña**.
- **Fichas:** 5 denominaciones (colores de la paleta), borde dorado, emblema; ficha especial de memoria (azul espectral).
- **Zapato, mantel, candelabros, copas.**
- **Contratos:** pergamino negro-rojizo con texto de fuego; cambios de tinta (rojo→dorado) para "contrato adulterado".
- **Sellos del Pacto (×5), Pulso (corazón/ECG), Fondo de Retorno, Cartas de Memoria (10 iconos), Ruleta de los Condenados, Prueba de fraude.**
- **Tipografía:** display art déco para títulos (licencia comercial verificada); serif legible para diálogo; numerales de cartas muy legibles.
- **UI:** marcos dorados finos, esquinas ornamentadas, fondos vino translúcidos; prioridad visual: cartas, valor de manos, acciones, apuesta, saldo, contrato activo. Los indicadores emocionales **no** aparecen como barras; se transmiten con la actuación de Vespera.

## 8. Lenguaje visual de las trampas
| Trampa | Pista visual | Pista sonora |
| --- | --- | --- |
| Carta sustituida | Dedos con movimiento irregular (frame extra) | roce seco |
| Baraja maldita | Brillo rojo anómalo en el zapato | zumbido grave breve |
| Mirada prohibida | Ojos de Vespera brillan un instante | susurro |
| Contrato adulterado | Tinta/sello parpadea de color | tinta chisporroteando |
| Carta fantasma | Marca inexistente en el dorso | campanilla apagada |
| Apuesta alterada | Ficha emite humo/cambia de color | siseo |
Intensidad escalable por acto y por dificultad; siempre perceptible con atención, nunca invisible.

## 9. Especificaciones técnicas
- **Resolución base 1920×1080**; assets de personaje a 2× (altura ~2160 px) para escalar a 4K.
- Personajes en **capas separadas** (PSD/KRA): línea, color, sombra, brillo; piezas independientes para ojos, cejas, boca, rubor, cabello frontal/trasero, manos, cuernos, accesorios.
- Fondo sin personajes; elementos de mesa en capas propias (mantel, zapato, fichas, candelabros).
- PNG con alpha, sRGB, sin compresión con pérdida. Atlas de iconos 256×256 y 512×512.
- Nomenclatura: `categoria_nombre_variante_vNN.png` (ej. `char_vespera_expr_smirk_v01.png`, `bg_casino_act3_v02.png`, `ui_card_back_v01.png`).
- Animación en motor: respiración, parpadeo, balanceo de cabello, humo, parpadeo de velas; swap de expresiones por capa.

## 10. Lista de assets objetivo (para Fase 4)
Vespera (cuerpo + 12 expresiones + 5 vestuarios), Nox (+6 expresiones), La Contadora, 3 almas visitantes, manos del protagonista (acciones: pedir, plantarse, doblar, separar), mesa principal, 5 fondos de acto, 52 cartas + dorso + carta fantasma, 5 fichas + ficha de memoria, zapato, contrato (3 estados), 5 sellos, icono Pulso, 10 cartas de memoria, ruleta, logo, 6–8 CG de escenas clave, portada y arte de tienda Steam.

## 11. Consistencia (checklist de aprobación)
Antes de aceptar un asset: ¿misma paleta? ¿rasgos de Vespera reconocibles (ojos, cuernos, cabello)? ¿grosor de línea coherente? ¿iluminación según el acto? ¿sin texto de IA? ¿manos correctas? ¿nomenclatura y capas?
