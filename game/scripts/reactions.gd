class_name Reactions
extends RefCounted
## Tabla de reacciones (docs/tabla_reacciones.md): evento -> [expresion int.1, int.2, int.3] y clave de linea.

const TABLE := {
	"deal": [["base", "base", "malicia"], "line.deal"],
	"hit": [["base", "malicia", "locura"], "line.hit"],
	"stand": [["arrogancia", "malicia", "encanto"], "line.stand"],
	"double": [["malicia", "encanto", "locura"], "line.double"],
	"split": [["sorpresa", "malicia", "obsesion"], "line.split"],
	"surrender": [["burla", "arrogancia", "culpa"], "line.surrender"],
	"insurance": [["malicia", "sorpresa", "desesperacion"], "line.insurance"],
	"bust": [["burla", "arrogancia", "locura"], "line.bust"],
	"dealer_bust": [["sorpresa", "enfado", "desesperacion"], "line.dealer_bust"],
	"win_player": [["enfado", "celos", "desesperacion"], "line.win_player"],
	"lose_player": [["arrogancia", "burla", "locura"], "line.lose_player"],
	"blackjack_player": [["sorpresa", "celos", "enfado"], "line.blackjack_player"],
	"blackjack_dealer": [["encanto", "arrogancia", "locura"], "line.blackjack_dealer"],
	"inspect_fail": [["burla", "arrogancia", "locura"], "line.inspect_fail"],
	"inspect_ok": [["sorpresa", "enfado", "miedo"], "line.inspect_ok"],
	"contract": [["encanto", "malicia", "obsesion"], "line.contract"],
	"push": [["base", "malicia", "obsesion"], "line.push"],
}

## Intensidad 1..3 segun la apuesta respecto a la apuesta minima.
static func intensity(bet: int, min_bet: int) -> int:
	if bet >= min_bet * 10:
		return 3
	if bet >= min_bet * 4:
		return 2
	return 1

static func expression(kind: String, level: int) -> String:
	return TABLE[kind][0][clampi(level, 1, 3) - 1]

static func line_key(kind: String) -> String:
	return TABLE[kind][1]

## Resuelve el tipo de reaccion principal de un lote de eventos del nucleo.
static func kind_from_events(events: Array, fallback: String) -> String:
	var kind := fallback
	var worst := ""
	for e in events:
		if e is Dictionary:
			if e.has("DealerPeek") and e["DealerPeek"].get("blackjack", false):
				return "blackjack_dealer"
			if e.has("HandResolved"):
				match str(e["HandResolved"]["outcome"]):
					"Blackjack": return "blackjack_player"
					"Bust": worst = "bust"
					"DealerBust": worst = "dealer_bust" if worst == "" else worst
					"Win": worst = "win_player" if worst == "" else worst
					"Loss": worst = "lose_player" if worst == "" else worst
					"Push": worst = "push" if worst == "" else worst
					"Surrender": worst = "surrender"
	return worst if worst != "" else kind
