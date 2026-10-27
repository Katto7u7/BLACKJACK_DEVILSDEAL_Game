extends SceneTree
# Prueba sin interfaz: godot --headless --path game -s res://scripts/smoke_test.gd

func _init() -> void:
	var t := DevilsTable.new()
	var r: Dictionary = JSON.parse_string(t.new_game("{}", 1000, 42))
	assert(not r.has("error"))
	var ev: Dictionary = JSON.parse_string(t.start_round(50, "{}"))
	print("eventos: ", ev["events"].size())
	var s: Dictionary = JSON.parse_string(t.state())
	print("fase=", s["phase"], " crupier=", s["dealer"], " mano=", s["hands"][0]["cards"], " legal=", s["legal"])
	if s["phase"] == "insurance":
		t.insurance(0)
	s = JSON.parse_string(t.state())
	var guard := 0
	while s["phase"] == "player" and guard < 20:
		t.act("stand")
		s = JSON.parse_string(t.state())
		guard += 1
	print("final fase=", s["phase"], " fichas=", s["chips"], " resultado=", s["hands"][0]["outcome"])
	var saved := t.save_json()
	var t2 := DevilsTable.new()
	assert(not JSON.parse_string(t2.load_json(saved)).has("error"))
	print("OK guardado/carga, bytes=", saved.length())
	quit(0)
