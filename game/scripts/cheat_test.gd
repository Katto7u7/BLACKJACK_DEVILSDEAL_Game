extends SceneTree
# godot --headless --path game -s res://scripts/cheat_test.gd : juega rondas con trampas al maximo y verifica la inspeccion

func _init() -> void:
	var t := DevilsTable.new()
	t.new_game("{}", 100, 7)
	t.set_cheats(true)
	for i in 6:
		t.advance_act()
	var hints := 0
	var correct := 0
	for n in 400:
		t.advance_act() if false else null
		var r: Dictionary = JSON.parse_string(t.start_round(10, "{}"))
		if r.has("error"):
			break
		var found := false
		for e in r["events"]:
			if e is Dictionary and e.has("CheatHint"):
				found = true
				hints += 1
		var s: Dictionary = JSON.parse_string(t.state())
		if found and (s["phase"] == "player" or s["phase"] == "insurance"):
			var res: Dictionary = JSON.parse_string(t.inspect("swapped"))
			if res.get("result", "") == "correct":
				correct += 1
		s = JSON.parse_string(t.state())
		if s["phase"] == "insurance":
			t.insurance(0)
		s = JSON.parse_string(t.state())
		while s["phase"] == "player":
			t.act("stand")
			s = JSON.parse_string(t.state())
		if int(s["chips"]) < 10:
			break
	print("pistas=", hints, " aciertos_swapped=", correct)
	assert(hints > 0)
	quit(0)
