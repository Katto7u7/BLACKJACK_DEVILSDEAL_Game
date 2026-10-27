# Arquitectura técnica

## Stack
- **Godot 4.x** (GDScript para UI/escenas/diálogo) — presentación, animación, input, audio, localización, exportación.
- **Rust** (crate `devils_core`, vía `godot-rust/gdext`) — toda la lógica de reglas y estado del juego.
- **GodotSteam** — logros, Steam Cloud, overlay.
- **Herramientas de arte:** ComfyUI (conceptos), Krita (acabado) — ver `pipeline_arte.md`.

Principio: **Godot nunca calcula reglas.** Envía comandos al núcleo y renderiza los eventos que este devuelve.

## Estructura de carpetas
```
BLACKJACK_DEVILSDEAL_Game/
  docs/                 documentos maestros
  art/
    concepts/<cat>/     salidas de ComfyUI + _manifest.json
    comfy_workflows/    workflows JSON versionados
    tools/              scripts (comfy_batch.py, ...)
    source/             .kra de trabajo
    LICENCIAS_MODELOS.md
  core/                 workspace Rust
    devils_core/        lógica pura (sin Godot)
    devils_bridge/      gdext: expone el núcleo a Godot
    devils_sim/         CLI de simulación Monte Carlo
  game/                 proyecto Godot
    assets/ scenes/ scripts/ locale/ dialogue/ data/
```

## Núcleo Rust — módulos
Origen: porte de `jb21/backend/blackjack/`.

| Módulo | Contenido | Origen |
| --- | --- | --- |
| `cards` | Suit, Rank, Card (+ código "10H") | `cards.py` |
| `shoe` | Zapato N barajas, penetración, RNG con semilla (ChaCha) | `deck.py` |
| `hand` | Valor, soft, bust, blackjack natural, split | `hand.py` |
| `rules` | `TableRules` validadas (decks 1–8, pagos, doblar/separar/rendir, `max_hands`) | `rules.py` |
| `round` | Máquina de estados de una mano | `engine.py` |
| `side_bets` | TriBlack, BlackSeven | `side_bets.py` |
| `insurance` | Seguro (opcional por regla) | `insurance.py` |
| `contracts` | Contratos Vivos como modificadores declarativos con duración | nuevo |
| `cheats` | Trampas como eventos explícitos + registro previo | nuevo |
| `emotion` | Fascinación, Desesperación, Desdén, memoria de estilo | nuevo |
| `economy` | Fichas, Fondo de Retorno, Sellos, Pulso, préstamo | nuevo |
| `memory_cards` | Comodines (3 equipables, 1 por mano) | nuevo |
| `events` | Selección ponderada + hitos garantizados | nuevo |
| `campaign` | Actos, duelos al mejor de 3, finales | nuevo |
| `save` | Serialización versionada (serde) | nuevo |

**Correcciones al portar:** aplicar `max_splits` (hoy solo se usa `max_hands`); una sola implementación de `dealer_should_hit`; seguro como regla configurable (el 10:1 con carta de valor 10 era peculiar de jb21); pagos por fracción entera para evitar redondeos.

## Comunicación Godot ↔ Núcleo
Comandos (Godot → núcleo) y eventos (núcleo → Godot), todo serializable:

- Comandos: `PlaceBet`, `SetSideBets`, `Deal`, `Action(hit|stand|double|split|surrender)`, `Insurance`, `ChooseContract(i|reject|negotiate)`, `InspectTable`, `UseMemoryCard`, `ChooseEventOption`, `DepositReturnFund`, `Save/Load`.
- Eventos: `CardDealt{to,card,face_up}`, `HandResolved{outcome,payout}`, `ContractOffered[3]`, `CheatCommitted/Hint/Resolved`, `EmotionChanged`, `DialogueTrigger{id,vars}`, `EventTriggered`, `ActAdvanced`, `EndingReached`.
- El núcleo devuelve eventos con **tiempo lógico**, no con tiempos de animación; Godot decide el ritmo.

## Trampas verificables (regla de oro del diseño)
Antes de cada resolución el núcleo **compromete** (hash) el estado: orden del zapato restante, apuestas, contratos y cartas. Una trampa es un evento explícito sobre ese estado con su pista. `InspectTable` compara estado comprometido vs. mostrado: si difiere, la acusación es correcta. Nada cambia el resultado sin dejar rastro.

## Narrativa y localización
- Diálogo en `game/dialogue/*.json` (o Yarn/Dialogic): nodos con condiciones sobre variables del núcleo (`fascination>60`, `evidence>=3`, etiquetas de memoria).
- Todo texto visible sale de claves (`locale/es.po`, `en.po`). Prohibido texto literal en escenas.
- Líneas de reacción de Vespera etiquetadas por situación + estado emocional; el selector evita repetir las últimas N.

## Guardado
JSON versionado (`save_version`), un slot por partida, autoguardado entre actos (el concepto lo exige) + Steam Cloud. Semilla de RNG guardada: recargar no permite "re-tirar" cartas.

## Audio
Buses: música, SFX, voz, UI (volumen independiente — accesibilidad). Música adaptable por capas (calma/tensión/duelo); corte de música en recuerdos del accidente.

## Testing
- `cargo test`: portar casos de `jb21/backend/tests/` (engine, double face-down, insurance, side bets, integridad de mesa) + propiedades (el zapato conserva 52·N cartas, pagos cuadran).
- `devils_sim`: millones de manos → ventaja de la casa, RTP de side bets, duración de actos, solvencia de economía.
- Godot: GUT para escenas críticas; prueba manual de accesibilidad.

## Rendimiento / plataforma
2D, 1920×1080 base escalable; objetivo 60 fps en equipos modestos y Steam Deck. Capas animables con tweens/shaders ligeros (respiración, parpadeo, humo).
