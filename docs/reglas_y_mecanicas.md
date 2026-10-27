# Reglas y mecánicas (especificación)

Cifras marcadas **[sim]** son provisionales hasta validarlas con `devils_sim`.

## 1. Blackjack base
| Regla | Valor | Nota vs jb21 |
| --- | --- | --- |
| Zapato | 6 barajas, remezcla al 75% de penetración | igual (`SHOE_PENETRATION`) |
| Crupier | Se planta en todo 17 (incl. suave) | igual (`dealer_hits_soft_17=false`) |
| Natural | 3:2 | igual |
| Victoria / empate | 1:1 / devuelve apuesta | igual |
| Doblar | Con 2 cartas; una sola carta; permitido tras separar | igual |
| Separar | Hasta 3 manos totales (concepto) | jb21 permite 4 → **cambiar a 3** y aplicar `max_splits` |
| Ases separados | 1 carta c/u, sin volver a separar; 21 ≠ natural | igual |
| Rendición | Tardía, solo 2 primeras cartas, devuelve la mitad | igual |
| Seguro | Opcional; solo con As visible; paga 2:1 | jb21 también ofrecía con carta 10 (10:1) → **eliminar** |

El mazo revela solo la carta visible del crupier; la oculta es el índice 1.

## 2. Apuestas secundarias
Idénticas al concepto y a `jb21/backend/blackjack/side_bets.py`.
- **TriBlack** (2 cartas jugador + visible crupier): Escalera real Q-K-A mismo palo 100:1 · Escalera de color 35:1 · Tercia 30:1 · Escalera 10:1 · Color 5:1. Solo la mayor. K-A-2 no cuenta.
- **BlackSeven** (2 cartas jugador): 7♠+7♠ 50:1 · 7 perfecto otro palo 35:1 · par perfecto 25:1 · par mismo color 10:1 · par 5:1.
- Pago neto X:1 = ganancia X veces la apuesta + devolución. Se resuelven tras el reparto, independientes de la mano.

## 3. Estructura de sesión
Apuesta → cartas iniciales (+ side bets) → decisiones → resolución → economía/relación → ¿evento? → siguiente mano.
Cada acto: 5–7 manos normales, 1–2 eventos, 1 Contrato Vivo, 1 oportunidad de memoria, duelo de Sello (**mejor de 3**, empates se repiten).
Evento cada 3–4 manos, con prioridad a momentos significativos; sin encadenar interrupciones; hitos argumentales garantizados si el azar no los dio.

## 4. Contratos Vivos
Propuestos por Vespera tras 3–4 manos o un suceso. Se ofrecen **3**; el jugador: acepta uno · rechaza todos pagando coste pequeño conocido · negocia (consume un Favor limitado).
Cada oferta muestra duración (1–2 manos, raro 3), beneficio, riesgo y restricciones **antes** de aceptar. Un contrato altera **una sola** cosa.

| Contrato | Efecto | Contrapartida |
| --- | --- | --- |
| Corazón Roto | Próxima victoria: pista + recompensa doble | Si pierdes, un recuerdo se sella temporalmente |
| Espejo | Ver una carta futura en ventana concreta | Vespera ve una carta oculta en un duelo posterior |
| Cadenas | 2 victorias seguidas → bono al Fondo de Retorno | Romper racha: Vespera gana iniciativa en el siguiente contrato |
| Apuesta Ardiente | Ganancias ↑ durante 2 manos | Exposición permitida ↑ proporcional |
| La Casa Escucha | Tras ganar, una pregunta narrativa | Si pierdes, respondes una personal |
| Mesa Sellada | Nadie usa poderes/memorias | Renuncias a tus recursos |
| Deuda de Honor | Victoria limpia → inspección extra | Derrota: requisito para cobrar la ventaja |
| Doble o Nada | Arriesgar premio de contrato por uno mayor | Se pierde si falla la condición |

Generación: pesos según estado (fichas, racha, acto, emociones). Negociación: cambiar una condición (p. ej. menos recompensa a cambio de no perder memoria). **Trampa contractual:** Vespera puede alterar una cláusula; el original lo guarda La Contadora; si se detecta se restaura y puede haber sanción.

## 5. Vespera — emociones
- **Fascinación (0–100):** ↑ remontadas, manos tensas, victorias inesperadas, negociación inteligente; ↓ duelo sin significado o desprecio.
- **Desesperación (0–100):** ↑ Sellos, depósitos al Fondo, verdades descubiertas, intención clara de irse.
- Ambas pueden estar altas a la vez. Afectan diálogo, tipo de contratos, frecuencia/agresividad de trampas — **nunca** las cartas repartidas sin trampa explícita.
- Reacciones orientativas (tabla del concepto §7) implementadas como reglas de selección de líneas.

### Desdén (oculto)
Sube con **patrones reiterados y extraordinarios** de autoboicot evidente (p. ej. pedir carta con 20 repetidamente, apuestas máximas sin sentido seguidas de abandono de manos). **No** sube por: perder, apostar poco, ser principiante, rendirse estratégicamente, decisiones subóptimas válidas. Umbral → Vespera pausa y exige **Mano de Honor** (sin contratos, una mano). Es evento dramático, no castigo financiero. El juego nunca afirma conocer la intención.

### Memoria de decisiones
Registra: estilo de apuesta (conservador/arriesgado), trampas descubiertas, regalos rechazados, respuestas personales, amabilidad, confrontaciones. Alimenta variantes de diálogo y ofertas.

## 6. Trampas e inspección
Tipos: Carta sustituida · Baraja maldita · Mirada prohibida · Contrato adulterado · Carta fantasma · Apuesta alterada (pistas en `biblia_de_arte.md §8`).
- Frecuencia ↑ con el acto; **nunca** hacen imposible ganar.
- Estado comprometido antes de cada resolución (ver `arquitectura.md`).
- **Inspeccionar la Mesa:** acción limitada (cargas por acto **[sim]**). Acierto → se corrige/anula la mano, compensación proporcionada y 1 Prueba de fraude. Fallo → se consume la carga, Vespera se burla, **sin deuda ruinosa**. Con Pruebas suficientes → exigir mano supervisada por La Contadora.

## 7. Eventos entre rondas
Siempre ofrecen una decisión relevante (arriesgar/obtener/investigar). Lista: Ruleta de los Condenados · Oferta de Nox (elegir 1 de 3) · Pregunta personal · Recuerdo fragmentado · Visitante · Propina del Diablo · Teléfono de los Vivos · Apuesta de una Carta · Vino Infernal · Hora de la Bruja · Interrupción arbitral · Carta Sellada · Celos de Vespera · Mesa de Confesiones · Llamada del Hospital.
El azar decide **qué oportunidad aparece**, no fuerza una decisión desventajosa. Ruleta: probabilidades visibles, boletos solo ganados jugando.

## 8. Cartas de Memoria (comodines)
3 espacios equipables por capítulo, **1 activación por mano**, usos limitados en las potentes, ventanas de activación claras (nunca retroceden un resultado ya aceptado). Ninguna convierte automáticamente una derrota importante en victoria. Nunca obligatorias para superar un capítulo.
Lista: Segunda Oportunidad · Ojo del Destino · Rompecontratos · Último Latido · Mano Bendita · Memoria Prestada · Pacto de Cenizas · Silencio Infernal · La Verdad Duele · Fichas Gemelas.

## 9. Mesa de las Confesiones
Mano real de blackjack; se apuesta información/obligación (no fichas). Condición mostrada antes de repartir. Empate = repetir sin intercambio. Preguntas escalan del acto I (nombre, tiempo, por qué me conoces) al IV (quién ordenó, cómo sabías dónde estaba, cámaras, ¿fuiste tú?). Vespera responde con medias verdades, pero no puede contradecir pruebas verificables.

## 10. Economía **[sim]**
| Recurso | Regla |
| --- | --- |
| Fichas | Inicio 100; límites de mesa por acto |
| Fondo de Retorno | Cuenta aparte, protegida de pérdidas ordinarias; depósito voluntario |
| Sellos | 0–5, uno por acto (mejor de 3) |
| Pulso | 3 iniciales; se pierde 1 por fracaso crítico (duelo de Sello perdido, contrato de alto riesgo perdido) |
| Fragmentos de memoria | Desbloquean recuerdos/comodines |
| Pruebas de fraude | Para arbitraje |
Sin fichas: **Préstamo Infernal** (condiciones claras, sin espiral) + vía gratuita (desafío de habilidad / misión de Nox / mano de bajo riesgo con capital prestado). Estilo conservador siempre puede completar la historia.
Precio de libertad, límites por acto y probabilidades se fijan con simulación (perfil conservador vs. agresivo vs. estrategia básica).

## 11. Progresión y finales
5 actos / 5 Sellos (ver diseño). Finales: 1 Regreso a la Vida · 2 Una Eternidad Contigo · 3 La Casa Gana (Pulso=0) · 4 El Pacto Roto (secreto: pruebas + retorno) · 5 El Nuevo Crupier (cláusula). No dependen de un único medidor romántico; ninguno detrás de compras.

## 12. Modos
Historia · Casino Eterno (tras campaña) · Desafío Diario (misma semilla para todos; sin ventajas compradas) · desafíos personales + logros.

## 13. Reglas de diseño inviolables
1. Nunca cambiar una regla sin avisar (salvo trampa con pista inspeccionable).
2. Mala suerte ≠ falta de habilidad: derrotas ordinarias sin castigo irreversible.
3. No exigir apuestas temerarias.
4. No vender la libertad ni victorias.
5. El romance no borra la responsabilidad de Vespera.
6. La sorpresa nace de decisiones, no de arbitrariedad.
7. Vespera es el corazón: comenta, recuerda, miente, se desespera, cambia.
