class_name I18n
extends RefCounted
## Textos ES/EN por clave. (Se migrara a .po; nada de texto literal en las escenas.)

static var lang := "es"

const T := {
	"es": {
		"ui.deal": "Repartir", "ui.hit": "Pedir", "ui.stand": "Plantarse", "ui.double": "Doblar", "ui.split": "Separar",
		"ui.surrender": "Rendirse", "ui.insure": "Asegurar", "ui.no_insure": "Sin seguro", "ui.bet": "Apuesta",
		"ui.chips": "Fichas", "ui.next": "Siguiente mano", "ui.lang": "EN", "ui.broke": "Sin fichas. Vespera sonrie.",
		"out.Win": "Ganas", "out.Loss": "Pierdes", "out.Push": "Empate", "out.Bust": "Te pasas", "out.DealerBust": "Ganas (crupier se pasa)", "out.Blackjack": "¡Blackjack!", "out.Surrender": "Rendición",
		"cam.hand": "Mano %d/%d", "cam.duel": "DUELO DE SELLO  Tú %d – %d Vespera", "cam.act": "Acto %d",
		"mem.title": "Memorias", "mem.SecondChance": "Segunda Oportunidad", "mem.EyeOfDestiny": "Ojo del Destino", "mem.ContractBreaker": "Rompe-Contratos",
		"mem.LastHeartbeat": "Último Latido", "mem.InfernalSilence": "Silencio Infernal", "mem.TruthHurts": "La Verdad Duele", "mem.TwinChips": "Fichas Gemelas",
		"mem.next": "La siguiente carta es: %s", "mem.cheat_yes": "Hay trampa en esta ronda.", "mem.cheat_no": "No hay trampa en esta ronda.", "mem.replaced": "Cambias tu última carta por %s.",
		"mem.used": "Memoria usada.", "mem.fail": "No se puede usar ahora.",
		"cam.duel_start": ["Ahora sí, cariño. El Sello se juega a tres manos.", "Un duelo. Al mejor de tres. Me tiemblan los cuernos."],
		"cam.seal": ["El Sello es tuyo... por ahora.", "Tsk. Lo ganaste. Qué aburrido."], "cam.duel_lost": ["Perdiste el duelo. Tu pulso lo sintió.", "Un latido menos, querido."],
		"end.title": "FINAL", "end.ReturnToLife": "Regreso a la Vida", "end.EternityWithYou": "Una Eternidad Contigo", "end.HouseWins": "La Casa Gana",
		"end.BrokenPact": "El Pacto Roto", "end.NewDealer": "El Nuevo Crupier", "end.again": "Nueva partida",
		"ins.btn": "Inspeccionar", "ins.title": "¿Qué crees que hizo?", "ins.cancel": "Cancelar", "ins.correct": "¡Lo descubriste! Compensación: %d", "ins.wrong": "Nada que ver. Vespera se ríe.", "ins.clean": "La mesa está limpia.", "ins.none": "No te quedan inspecciones este acto.",
		"cheat.swapped": "Carta cambiada", "cheat.cursed": "Baraja maldita", "cheat.gaze": "Mirada prohibida", "cheat.contract": "Contrato adulterado", "cheat.ghost": "Carta fantasma", "cheat.bet": "Apuesta alterada",
		"line.inspect_fail": ["Jajaja... ¿acusándome? Qué lindo.", "Tu desconfianza me excita."], "line.inspect_ok": ["...¿Cómo lo supiste?", "Tsk. Eres más listo de lo que pareces."],
		"con.title": "Vespera te ofrece un contrato", "con.reject": "Rechazar todos (-5)", "con.hands": "manos", "con.active": "Contrato",
		"con.BrokenHeart": "Corazón Roto", "con.BrokenHeart.d": "Tu próxima victoria paga doble. Si pierdes, un recuerdo se sella.",
		"con.Mirror": "Espejo", "con.Mirror.d": "Ves una carta futura una vez. Vespera verá una carta oculta más adelante.",
		"con.Chains": "Cadenas", "con.Chains.d": "2 victorias seguidas: bono al Fondo de Retorno. Si rompes la racha, ella gana iniciativa.",
		"con.BlazingBet": "Apuesta Ardiente", "con.BlazingBet.d": "Ganancias +50%, pero el límite de apuesta sube +50%.",
		"con.HouseListens": "La Casa Escucha", "con.HouseListens.d": "Al ganar, haces una pregunta. Si pierdes, respondes una personal.",
		"con.SealedTable": "Mesa Sellada", "con.SealedTable.d": "Nadie usa poderes ni memorias. Renuncias a tus recursos.",
		"con.HonorDebt": "Deuda de Honor", "con.HonorDebt.d": "Victoria limpia: inspección extra. Derrota: un requisito para cobrar.",
		"con.DoubleOrNothing": "Doble o Nada", "con.DoubleOrNothing.d": "Premio doble si ganas; si fallas, pierdes un latido.",
		"line.deal": ["Veamos qué te trae la suerte, cariño.", "Siéntate cerca. No muerdo... todavía.", "Apuesta, apuesta. Me encanta verte dudar."],
		"line.hit": ["¿Otra? Qué valiente.", "Sí, pide. Sigue pidiendo.", "Ay, qué ansia."],
		"line.stand": ["¿Te plantas? Qué prudente.", "Cobarde... o muy listo. No sé cuál me gusta más.", "Muy bien. Mi turno."],
		"line.double": ["¡Doblar! Ahora sí hablamos.", "Mmm, me gusta cuando arriesgas."],
		"line.split": ["Dos manos... dos formas de perder.", "Separas. Qué codicioso."],
		"line.surrender": ["¿Te rindes? Qué lástima, me divertía.", "Huye, huye. Yo me quedo con la mitad."],
		"line.insurance": ["¿Seguro? Qué desconfiado.", "Un As... ¿tienes miedo, cariño?"],
		"line.win_player": ["Suerte de principiante. Solo eso.", "Tsk. Disfrútalo mientras dure.", "No... no es justo."],
		"line.lose_player": ["Ay, pobrecito. Otra vez será.", "La casa siempre gana. Y yo soy la casa.", "Qué dulce se siente tu derrota."],
		"line.bust": ["¡Te pasaste! Ja, ja, ja.", "Pasarse de 21... el pecado favorito de los humanos."],
		"line.dealer_bust": ["¡Imposible! ¿Qué le hiciste al zapato?", "Mi... mi propia mano me traiciona."],
		"line.blackjack_player": ["¡Blackjack! ...No lo vi venir.", "Eso es... sospechoso."],
		"line.blackjack_dealer": ["Blackjack. Mío. Siempre mío.", "Ay, ay, ay. Mala suerte."],
		"line.push": ["Empate. Qué aburrido... y qué tenso.", "Nadie gana. Qué delicioso suspenso."],
		"line.contract": ["Tengo algo para ti, cariño. Firma aquí.", "Un pequeño trato. Solo leerás la letra grande."],
	},
	"en": {
		"ui.deal": "Deal", "ui.hit": "Hit", "ui.stand": "Stand", "ui.double": "Double", "ui.split": "Split",
		"ui.surrender": "Surrender", "ui.insure": "Insure", "ui.no_insure": "No insurance", "ui.bet": "Bet",
		"ui.chips": "Chips", "ui.next": "Next hand", "ui.lang": "ES", "ui.broke": "Out of chips. Vespera smiles.",
		"out.Win": "You win", "out.Loss": "You lose", "out.Push": "Push", "out.Bust": "Bust", "out.DealerBust": "You win (dealer busts)", "out.Blackjack": "Blackjack!", "out.Surrender": "Surrender",
		"cam.hand": "Hand %d/%d", "cam.duel": "SEAL DUEL  You %d – %d Vespera", "cam.act": "Act %d",
		"mem.title": "Memories", "mem.SecondChance": "Second Chance", "mem.EyeOfDestiny": "Eye of Destiny", "mem.ContractBreaker": "Contract Breaker",
		"mem.LastHeartbeat": "Last Heartbeat", "mem.InfernalSilence": "Infernal Silence", "mem.TruthHurts": "Truth Hurts", "mem.TwinChips": "Twin Chips",
		"mem.next": "The next card is: %s", "mem.cheat_yes": "She is cheating this round.", "mem.cheat_no": "No cheating this round.", "mem.replaced": "You swap your last card for %s.",
		"mem.used": "Memory used.", "mem.fail": "Cannot use it now.",
		"cam.duel_start": ["Now we're talking, darling. The Seal is played in three hands.", "A duel. Best of three. My horns tremble."],
		"cam.seal": ["The Seal is yours... for now.", "Tsk. You won it. How dull."], "cam.duel_lost": ["You lost the duel. Your pulse felt it.", "One heartbeat less, dear."],
		"end.title": "ENDING", "end.ReturnToLife": "Return to Life", "end.EternityWithYou": "An Eternity With You", "end.HouseWins": "The House Wins",
		"end.BrokenPact": "The Broken Pact", "end.NewDealer": "The New Dealer", "end.again": "New game",
		"ins.btn": "Inspect", "ins.title": "What do you think she did?", "ins.cancel": "Cancel", "ins.correct": "You caught her! Compensation: %d", "ins.wrong": "Nothing of the sort. Vespera laughs.", "ins.clean": "The table is clean.", "ins.none": "No inspections left this act.",
		"cheat.swapped": "Swapped card", "cheat.cursed": "Cursed deck", "cheat.gaze": "Forbidden gaze", "cheat.contract": "Altered contract", "cheat.ghost": "Ghost card", "cheat.bet": "Altered bet",
		"line.inspect_fail": ["Hahaha... accusing me? How cute.", "Your distrust excites me."], "line.inspect_ok": ["...How did you know?", "Tsk. You are smarter than you look."],
		"con.title": "Vespera offers you a contract", "con.reject": "Reject all (-5)", "con.hands": "hands", "con.active": "Contract",
		"con.BrokenHeart": "Broken Heart", "con.BrokenHeart.d": "Your next win pays double. If you lose, a memory is sealed.",
		"con.Mirror": "Mirror", "con.Mirror.d": "See one future card once. Vespera will see a hidden card later.",
		"con.Chains": "Chains", "con.Chains.d": "2 wins in a row: bonus to the Return Fund. Break the streak and she gains initiative.",
		"con.BlazingBet": "Blazing Bet", "con.BlazingBet.d": "Winnings +50%, but the bet limit rises +50%.",
		"con.HouseListens": "The House Listens", "con.HouseListens.d": "When you win, ask a question. If you lose, answer a personal one.",
		"con.SealedTable": "Sealed Table", "con.SealedTable.d": "Nobody uses powers or memories. You give up your resources.",
		"con.HonorDebt": "Debt of Honor", "con.HonorDebt.d": "Clean win: extra inspection. Defeat: a requirement to collect.",
		"con.DoubleOrNothing": "Double or Nothing", "con.DoubleOrNothing.d": "Double prize if you win; if you fail, you lose a heartbeat.",
		"line.deal": ["Let's see what luck brings you, darling.", "Sit close. I don't bite... yet.", "Place your bet. I love watching you hesitate."],
		"line.hit": ["Another one? How brave.", "Yes, draw. Keep drawing.", "Oh, so eager."],
		"line.stand": ["You stand? How prudent.", "Coward... or very clever. I can't tell which I like more.", "Very well. My turn."],
		"line.double": ["Double! Now we're talking.", "Mmm, I like it when you gamble."],
		"line.split": ["Two hands... two ways to lose.", "You split. How greedy."],
		"line.surrender": ["You surrender? Shame, I was having fun.", "Run, run. I keep half."],
		"line.insurance": ["Insurance? How distrustful.", "An Ace... are you scared, darling?"],
		"line.win_player": ["Beginner's luck. That's all.", "Tsk. Enjoy it while it lasts.", "No... that's not fair."],
		"line.lose_player": ["Oh, poor thing. Next time.", "The house always wins. And I am the house.", "Your defeat tastes so sweet."],
		"line.bust": ["You bust! Ha ha ha.", "Going over 21... humanity's favorite sin."],
		"line.dealer_bust": ["Impossible! What did you do to the shoe?", "My... my own hand betrays me."],
		"line.blackjack_player": ["Blackjack! ...I didn't see that coming.", "That's... suspicious."],
		"line.blackjack_dealer": ["Blackjack. Mine. Always mine.", "Oh dear. Bad luck."],
		"line.push": ["A push. How dull... and how tense.", "Nobody wins. Delicious suspense."],
		"line.contract": ["I have something for you, darling. Sign here.", "A little deal. You'll only read the big print."],
	},
}

static var _last := {}

static func s(key: String) -> String:
	return str(T[lang].get(key, key))

## Linea aleatoria que evita repetir la ultima de la misma clave.
static func line(key: String) -> String:
	var arr: Array = T[lang].get(key, [key])
	if arr.size() == 1:
		return arr[0]
	var i := randi() % arr.size()
	if _last.get(key, -1) == i:
		i = (i + 1) % arr.size()
	_last[key] = i
	return arr[i]
