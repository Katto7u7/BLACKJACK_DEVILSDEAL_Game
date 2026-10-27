extends Control
## Mesa de blackjack contra Vespera. Godot no calcula reglas: todo viene del nucleo Rust (DevilsTable).
## Composicion: Vespera al centro; las cartas se reparten sobre la mesa (centro) y, al decidir, se agrandan y
## el resto se atenua para remarcarlas.

const W := 1920.0
const CX := 960.0
const SPAWN := Vector2(1650, 260)   # zapato

var table := DevilsTable.new()
var vespera: VesperaRig
var dialog: Label
var dialog_box: ColorRect
var info: Label
var bet_label: Label
var stage := Control.new()
var labels_layer := Control.new()
var dim := ColorRect.new()
var buttons := HBoxContainer.new()
var buttons_by_name := {}
var card_nodes := {}
var bet := 50
var min_bet := 10
var last_action := "deal"
var react_timer := 0.0
var focus := false
var offers_panel: Control
var offers_open := false
var inspect_panel: Control
var mem_box := VBoxContainer.new()
var bg: TextureRect
var bg_act := 1
var ending_shown := false

func _ready() -> void:
	randomize()
	table.new_game("{}", 100, randi())
	table.set_cheats(true)
	for c in ["EyeOfDestiny", "SecondChance", "TwinChips"]:
		table.unlock_memory(c)
		table.equip_memory(c)
	_build_ui()
	_refresh()
	_say("deal", "deal")
	var args := OS.get_cmdline_user_args()
	if "--shot" in args:
		_autoshot()
	elif "--contract" in args:
		_autocontract()
	elif "--demo" in args:
		_autodemo()

func _build_ui() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	bg = TextureRect.new()
	bg.texture = load("res://assets/mesa/fondo_acto1.png")
	bg.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	bg.stretch_mode = TextureRect.STRETCH_SCALE
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(bg)
	var frame := Panel.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(0.075, 0.05, 0.06)
	sb.border_color = Color("A87B39")
	sb.set_border_width_all(5)
	sb.set_corner_radius_all(14)
	frame.add_theme_stylebox_override("panel", sb)
	frame.position = Vector2(410, 0)
	frame.size = Vector2(1100, 1080)
	add_child(frame)
	vespera = VesperaRig.new()
	vespera.position = Vector2(420, 0)
	vespera.size = Vector2(1080, 1080)
	add_child(vespera)
	# paneles laterales
	var left := ColorRect.new()
	left.color = Color(0.075, 0.05, 0.06, 0.8)
	left.position = Vector2(20, 20)
	left.size = Vector2(370, 360)
	add_child(left)
	info = _label(Vector2(40, 34), 26)
	info.size = Vector2(330, 330)
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var right := ColorRect.new()
	right.color = Color(0.075, 0.05, 0.06, 0.8)
	right.position = Vector2(1530, 700)
	right.size = Vector2(370, 360)
	add_child(right)
	bet_label = _label(Vector2(1555, 715), 30)
	mem_box.position = Vector2(1530, 120)
	mem_box.size = Vector2(370, 400)
	mem_box.add_theme_constant_override("separation", 10)
	add_child(mem_box)
	var chips := TextureRect.new()
	chips.texture = load("res://assets/mesa/fichas.png")
	chips.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	chips.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	chips.position = Vector2(1555, 760)
	chips.size = Vector2(320, 120)
	add_child(chips)
	var i := 0
	for d in [-50, -10, 10, 50]:
		var b := Button.new()
		b.text = "%+d" % d
		b.position = Vector2(1555 + i * 85, 900)
		b.size = Vector2(78, 50)
		b.add_theme_font_size_override("font_size", 22)
		b.pressed.connect(_on_bet.bind(d))
		add_child(b)
		i += 1
	# dialogo (arriba, sobre el busto)
	dialog_box = ColorRect.new()
	dialog_box.color = Color(0.05, 0.02, 0.03, 0.62)
	dialog_box.position = Vector2(450, 18)
	dialog_box.size = Vector2(1020, 70)
	add_child(dialog_box)
	dialog = _label(Vector2(470, 26), 28)
	dialog.z_index = 5
	dialog_box.z_index = 4
	dialog.size = Vector2(980, 60)
	dialog.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	# atenuacion para remarcar las cartas
	dim.color = Color(0.03, 0.01, 0.02, 0.0)
	dim.position = Vector2(410, 0)
	dim.size = Vector2(1100, 1080)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(dim)
	stage.set_anchors_preset(Control.PRESET_FULL_RECT)
	stage.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(stage)
	labels_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	labels_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(labels_layer)
	var bar := ColorRect.new()
	bar.color = Color(0.05, 0.02, 0.03, 0.7)
	bar.position = Vector2(412, 975)
	bar.size = Vector2(1096, 105)
	add_child(bar)
	buttons.position = Vector2(560, 985)
	buttons.size = Vector2(800, 70)
	buttons.alignment = BoxContainer.ALIGNMENT_CENTER
	buttons.add_theme_constant_override("separation", 12)
	add_child(buttons)
	for n in ["deal", "hit", "stand", "double", "split", "surrender", "yes_ins", "no_ins", "inspect", "lang"]:
		var b := Button.new()
		b.custom_minimum_size = Vector2(140, 64)
		b.add_theme_font_size_override("font_size", 24)
		b.pressed.connect(_on_button.bind(n))
		buttons.add_child(b)
		buttons_by_name[n] = b

func _label(pos: Vector2, fs: int) -> Label:
	var l := Label.new()
	l.position = pos
	l.add_theme_font_size_override("font_size", fs)
	l.add_theme_color_override("font_outline_color", Color.BLACK)
	l.add_theme_constant_override("outline_size", 6)
	add_child(l)
	return l

func _on_bet(d: int) -> void:
	bet = clampi(bet + d, min_bet, 500)
	_refresh()

func _st() -> Dictionary:
	return JSON.parse_string(table.state())

func _on_button(n: String) -> void:
	var res := ""
	last_action = n
	match n:
		"deal": res = table.start_round(bet, "{}")
		"yes_ins":
			res = table.insurance(int(bet / 2))
			last_action = "insurance"
		"no_ins": res = table.insurance(0)
		"inspect":
			_show_inspect()
			return
		"lang":
			I18n.lang = "en" if I18n.lang == "es" else "es"
			_refresh()
			return
		_: res = table.act(n)
	var data: Dictionary = JSON.parse_string(res)
	if data.has("error"):
		push_warning(data["error"])
		return
	var kind := last_action
	if kind == "no_ins":
		kind = "insurance"
	for e in data["events"]:
		if e is Dictionary and e.has("CheatHint"):
			_cheat_hint(str(e["CheatHint"]["hint"]))
	var rk := Reactions.kind_from_events(data["events"], kind)
	_refresh()
	_say(rk, rk)
	_campaign_events(data.get("campaign_events", []))

func _say(kind: String, _tag: String) -> void:
	var level := Reactions.intensity(bet, min_bet)
	vespera.set_expression(Reactions.expression(kind, level))
	dialog.text = I18n.line(Reactions.line_key(kind))
	vespera.speak(clampf(dialog.text.length() * 0.045, 1.0, 3.5))
	react_timer = 3.0

func _process(dt: float) -> void:
	if react_timer > 0.0:
		react_timer -= dt
		if react_timer <= 0.0:
			vespera.set_expression("base")

# ---------------------------------------------------------------- cartas

## Coloca una fila de cartas centrada en `center`. Las nuevas salen del zapato; las existentes se animan a su sitio.
func _layout_row(prefix: String, items: Array, center: Vector2, sc: float, seen: Dictionary) -> void:
	var step := CardView.SIZE.x * sc * 0.66
	var total := step * (items.size() - 1) + CardView.SIZE.x * sc
	var x0 := center.x - total * 0.5
	var y := center.y - CardView.SIZE.y * sc * 0.5
	for j in items.size():
		var key := "%s%d" % [prefix, j]
		seen[key] = true
		var code: String = items[j][0]
		var up: bool = items[j][1]
		var node: CardView = card_nodes.get(key)
		var target := Vector2(x0 + step * j, y)
		if node == null:
			node = CardView.new(code, up)
			node.position = SPAWN
			node.scale = Vector2.ONE * 0.4
			node.rotation = 0.5
			node.mouse_filter = Control.MOUSE_FILTER_IGNORE
			stage.add_child(node)
			card_nodes[key] = node
		elif node.code != code or node.face_up != up:
			node.code = code
			node.face_up = up
			node.queue_redraw()
		node.z_index = j
		var tw := create_tween().set_parallel(true).set_trans(Tween.TRANS_QUART).set_ease(Tween.EASE_OUT)
		tw.tween_property(node, "position", target, 0.38)
		tw.tween_property(node, "scale", Vector2.ONE * sc, 0.38)
		tw.tween_property(node, "rotation", 0.0, 0.38)

func _place_cards(s: Dictionary, in_focus: bool) -> void:
	var seen := {}
	var sc_d := 1.1 if in_focus else 0.72
	var sc_p := 1.7 if in_focus else 0.9
	var y_d := 195.0 if in_focus else 560.0
	var y_p := 590.0 if in_focus else 800.0
	var dealer_items: Array = []
	for c in s["dealer"]:
		dealer_items.append([c, true])
	if s["dealer_hidden"]:
		dealer_items.append(["", false])
	if not dealer_items.is_empty():
		_layout_row("d", dealer_items, Vector2(CX, y_d), sc_d, seen)
	var hands: Array = s["hands"]
	var n := hands.size()
	var gap := (560.0 if in_focus else 300.0)
	if n > 2 and in_focus:
		sc_p = 1.25
		gap = 430.0
	for i in n:
		var items: Array = []
		for c in hands[i]["cards"]:
			items.append([c, true])
		var cx := CX + (i - (n - 1) * 0.5) * gap
		_layout_row("h%d_" % i, items, Vector2(cx, y_p), sc_p, seen)
	for k in card_nodes.keys():
		if not seen.has(k):
			card_nodes[k].queue_free()
			card_nodes.erase(k)
	# etiquetas de valor / resultado
	for c in labels_layer.get_children():
		c.queue_free()
	for i in n:
		var h: Dictionary = hands[i]
		var l := Label.new()
		l.text = "%d" % int(h["value"])
		if h["outcome"] != "Pending":
			l.text += "  ·  " + I18n.s("out." + str(h["outcome"])) + "  (%+d)" % (int(h["payout"]) - int(h["bet"]))
		if i == s["active"] and s["phase"] == "player":
			l.text = "▶ " + l.text
		l.add_theme_font_size_override("font_size", 40 if in_focus else 30)
		l.add_theme_color_override("font_outline_color", Color.BLACK)
		l.add_theme_constant_override("outline_size", 8)
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		l.size = Vector2(520, 60)
		var cx := CX + (i - (n - 1) * 0.5) * gap
		l.position = Vector2(cx - 260, y_p + CardView.SIZE.y * sc_p * 0.5 + 6)
		labels_layer.add_child(l)

func _set_focus(on: bool) -> void:
	focus = on
	var tw := create_tween()
	tw.tween_property(dim, "color:a", 0.62 if on else 0.0, 0.3)

# ---------------------------------------------------------------- refresco

func _refresh() -> void:
	var s := _st()
	var phase: String = s["phase"]
	info.text = "%s: %d\n♥ %d    Fondo: %d\n%s" % [I18n.s("ui.chips"), int(s["chips"]), int(s["pulse"]), int(s["fund"]), _campaign_line(s)]
	var act_n := int(s["campaign"]["act"])
	if act_n != bg_act:
		bg_act = act_n
		bg.texture = load("res://assets/mesa/fondo_acto%d.png" % clampi(act_n, 1, 5))
	_build_memory(s, phase)
	if s["campaign"]["ending"] != null and not ending_shown:
		_show_ending(str(s["campaign"]["ending"]))
	for c in s["contracts"]:
		info.text += "\n\n%s: %s\n(%d %s)" % [I18n.s("con.active"), I18n.s("con." + str(c["kind"])), int(c["remaining"]), I18n.s("con.hands")]
	bet_label.text = "%s: %d" % [I18n.s("ui.bet"), bet]
	var want_focus := phase == "player" or phase == "insurance"
	if want_focus != focus:
		_set_focus(want_focus)
	_place_cards(s, want_focus)
	var legal: Array = s["legal"]
	var texts := {"deal": "ui.deal", "hit": "ui.hit", "stand": "ui.stand", "double": "ui.double", "split": "ui.split",
		"surrender": "ui.surrender", "yes_ins": "ui.insure", "no_ins": "ui.no_insure", "inspect": "ins.btn", "lang": "ui.lang"}
	for n in buttons_by_name:
		var b: Button = buttons_by_name[n]
		b.text = I18n.s(texts[n])
		match n:
			"deal": b.visible = phase == "idle" or phase == "finished"
			"yes_ins", "no_ins": b.visible = phase == "insurance"
			"inspect": b.visible = (phase == "player" or phase == "insurance") and int(s["inspect_charges"]) > 0
			"lang": b.visible = true
			_: b.visible = phase == "player" and n in legal
	if (phase == "idle" or phase == "finished") and int(s["chips"]) < min_bet:
		dialog.text = I18n.s("ui.broke")
	min_bet = int(s["min_bet"])
	bet = mini(bet, maxi(min_bet, int(s["chips"])))
	if s["contract_due"] and (phase == "idle" or phase == "finished") and not offers_open:
		_show_offers()

# ---------------------------------------------------------------- modales

func _modal(title_text: String) -> ColorRect:
	var p := ColorRect.new()
	p.color = Color(0.05, 0.02, 0.03, 0.98)
	p.position = Vector2(560, 60)
	p.size = Vector2(800, 960)
	p.z_index = 50
	add_child(p)
	var t := Label.new()
	t.text = title_text
	t.position = Vector2(30, 24)
	t.add_theme_font_size_override("font_size", 34)
	p.add_child(t)
	return p

func _show_offers() -> void:
	offers_open = true
	var o: Dictionary = JSON.parse_string(table.offer_contracts())
	offers_panel = _modal(I18n.s("con.title"))
	var y := 100
	var i := 0
	for c in o["offers"]:
		var b := Button.new()
		b.position = Vector2(30, y)
		b.size = Vector2(740, 200)
		b.alignment = HORIZONTAL_ALIGNMENT_LEFT
		b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		b.add_theme_font_size_override("font_size", 24)
		b.text = "%s  [%d %s]\n%s" % [I18n.s("con." + str(c["kind"])), int(c["duration"]), I18n.s("con.hands"), I18n.s("con." + str(c["kind"]) + ".d")]
		b.pressed.connect(_pick_offer.bind(i))
		offers_panel.add_child(b)
		y += 220
		i += 1
	var r := Button.new()
	r.position = Vector2(30, y)
	r.size = Vector2(740, 70)
	r.text = I18n.s("con.reject")
	r.add_theme_font_size_override("font_size", 24)
	r.pressed.connect(_pick_offer.bind(-1))
	offers_panel.add_child(r)
	_say("contract", "contract")

func _pick_offer(i: int) -> void:
	var res: String = table.reject_contracts() if i < 0 else table.accept_contract(i)
	if JSON.parse_string(res).has("error"):
		push_warning(res)
	offers_panel.queue_free()
	offers_open = false
	_refresh()

func _show_inspect() -> void:
	if inspect_panel != null:
		return
	inspect_panel = _modal(I18n.s("ins.title"))
	var y := 100
	for k in ["swapped", "cursed", "gaze", "contract", "ghost", "bet"]:
		var b := Button.new()
		b.position = Vector2(30, y)
		b.size = Vector2(740, 90)
		b.text = I18n.s("cheat." + k)
		b.add_theme_font_size_override("font_size", 26)
		b.pressed.connect(_do_inspect.bind(k))
		inspect_panel.add_child(b)
		y += 105
	var c := Button.new()
	c.position = Vector2(30, y + 20)
	c.size = Vector2(740, 70)
	c.text = I18n.s("ins.cancel")
	c.pressed.connect(_close_inspect)
	inspect_panel.add_child(c)

func _close_inspect() -> void:
	if inspect_panel:
		inspect_panel.queue_free()
		inspect_panel = null

func _do_inspect(kind: String) -> void:
	var r: Dictionary = JSON.parse_string(table.inspect(kind))
	_close_inspect()
	if r.has("error"):
		return
	match r["result"]:
		"correct":
			vespera.set_expression(Reactions.expression("inspect_ok", 2))
			dialog.text = I18n.s("ins.correct") % int(r["compensation"]) + "  " + I18n.line("line.inspect_ok")
		"wrong":
			vespera.set_expression(Reactions.expression("inspect_fail", 2))
			dialog.text = I18n.s("ins.wrong") + "  " + I18n.line("line.inspect_fail")
		"clean":
			vespera.set_expression(Reactions.expression("inspect_fail", 1))
			dialog.text = I18n.s("ins.clean")
		_:
			dialog.text = I18n.s("ins.none")
	vespera.speak(2.0)
	react_timer = 3.5
	_refresh()

## Pistas sutiles (biblia de arte §8). Nunca indican el tipo exacto ni la resolucion.
func _cheat_hint(h: String) -> void:
	var tw := create_tween()
	match h:
		"ShoeGlow":
			modulate = Color(1.0, 0.8, 0.8)
			tw.tween_property(self, "modulate", Color.WHITE, 1.2)
		"EyesGlow":
			vespera.modulate = Color(1.3, 0.8, 0.8)
			tw.tween_property(vespera, "modulate", Color.WHITE, 1.0)
		"IrregularFingers":
			var p := vespera.position
			tw.tween_property(vespera, "position", p + Vector2(7, 0), 0.05)
			tw.tween_property(vespera, "position", p - Vector2(5, 0), 0.07)
			tw.tween_property(vespera, "position", p, 0.05)
		"ExtraSmoke":
			bet_label.modulate = Color(0.7, 0.7, 0.7)
			tw.tween_property(bet_label, "modulate", Color.WHITE, 1.4)
		"InkFlicker":
			info.modulate = Color(1.0, 0.5, 0.3)
			tw.tween_property(info, "modulate", Color.WHITE, 1.2)
		"MarkedBack":
			stage.modulate = Color(1.0, 0.85, 0.85)
			tw.tween_property(stage, "modulate", Color.WHITE, 1.4)

# ---------------------------------------------------------------- capturas automaticas

func _shot(name: String) -> void:
	get_viewport().get_texture().get_image().save_png(ProjectSettings.globalize_path("res://../art/%s.png" % name))

func _autoshot() -> void:
	await get_tree().create_timer(0.6).timeout
	_on_button("deal")
	await get_tree().create_timer(1.6).timeout
	if _st()["phase"] == "insurance":
		_on_button("no_ins")
		await get_tree().create_timer(1.2).timeout
	_shot("JUEGO_slice_decision")
	if _st()["phase"] == "player":
		_on_button("stand")
		await get_tree().create_timer(1.8).timeout
	_shot("JUEGO_slice_resultado")
	get_tree().quit()

func _autocontract() -> void:
	for i in 3:
		table.start_round(10, "{}")
		if _st()["phase"] == "insurance":
			table.insurance(0)
		while _st()["phase"] == "player":
			table.act("stand")
	_refresh()
	await get_tree().create_timer(1.2).timeout
	_shot("JUEGO_slice_contrato")
	get_tree().quit()

## Demo para grabar video: juega manos solas con una estrategia simple.
func _autodemo() -> void:
	var t := get_tree()
	await t.create_timer(1.0).timeout
	bet = 50
	while true:
		_on_button("deal")
		await t.create_timer(1.8).timeout
		if _st()["phase"] == "insurance":
			_on_button("no_ins")
			await t.create_timer(1.2).timeout
		while _st()["phase"] == "player":
			await t.create_timer(1.6).timeout
			var s := _st()
			var h: Dictionary = s["hands"][int(s.get("active", 0))]
			_on_button("hit" if int(h["value"]) < 17 else "stand")
			await t.create_timer(1.2).timeout
		await t.create_timer(3.2).timeout
		if _st()["chips"] < bet:
			bet = min_bet

# ---------------------------------------------------------------- campana y memorias

func _campaign_line(s: Dictionary) -> String:
	var c: Dictionary = s["campaign"]
	var head: String = I18n.s("cam.act") % int(c["act"])
	if str(c["phase"]) == "Duel":
		return head + "\n" + I18n.s("cam.duel") % [int(c["duel_player"]), int(c["duel_dealer"])]
	if str(c["phase"]) == "DuelDue":
		return head + "\n" + I18n.s("cam.duel").split("  ")[0]
	return head + " · " + I18n.s("cam.hand") % [mini(int(c["normal_hands"]) + 1, int(c["hands_per_act"])), int(c["hands_per_act"])]

func _campaign_events(evs: Array) -> void:
	for e in evs:
		if not (e is Dictionary):
			continue
		if e.has("DuelStarted"):
			_speak_line("cam.duel_start", "arrogancia")
		elif e.has("SealWon"):
			_speak_line("cam.seal", "sorpresa")
		elif e.has("DuelLost"):
			_speak_line("cam.duel_lost", "burla")

func _speak_line(key: String, expr: String) -> void:
	vespera.set_expression(expr)
	dialog.text = I18n.line(key)
	vespera.speak(2.5)
	react_timer = 3.5

func _build_memory(s: Dictionary, phase: String) -> void:
	for ch in mem_box.get_children():
		ch.queue_free()
	var m: Dictionary = s["memory"]
	if m["equipped"].is_empty():
		return
	var t := Label.new()
	t.text = I18n.s("mem.title")
	t.add_theme_font_size_override("font_size", 24)
	mem_box.add_child(t)
	for c in m["equipped"]:
		var b := Button.new()
		b.custom_minimum_size = Vector2(350, 70)
		b.add_theme_font_size_override("font_size", 22)
		b.text = "%s  (%d)" % [I18n.s("mem." + str(c["id"])), int(c["left"])]
		var live: bool = phase == "player" or phase == "insurance"
		var ready: bool = (phase == "idle" or phase == "finished") if bool(c["before_deal"]) else live
		b.disabled = not ready or int(c["left"]) == 0 or bool(m["sealed"])
		b.pressed.connect(_use_memory.bind(str(c["id"])))
		mem_box.add_child(b)

func _use_memory(id: String) -> void:
	var r: Dictionary = JSON.parse_string(table.use_memory(id))
	if r.has("error"):
		dialog.text = I18n.s("mem.fail") + " (" + str(r["error"]) + ")"
		return
	var rv: Dictionary = r["reveal"]
	match str(rv["kind"]):
		"next_card": dialog.text = I18n.s("mem.next") % str(rv["card"])
		"cheating": dialog.text = I18n.s("mem.cheat_yes") if rv["value"] else I18n.s("mem.cheat_no")
		"replaced": dialog.text = I18n.s("mem.replaced") % str(rv["card"])
		_: dialog.text = I18n.s("mem.used")
	react_timer = 4.0
	_refresh()

func _show_ending(id: String) -> void:
	ending_shown = true
	var p := _modal(I18n.s("end.title"))
	var l := Label.new()
	l.text = I18n.s("end." + id)
	l.position = Vector2(30, 300)
	l.add_theme_font_size_override("font_size", 56)
	p.add_child(l)
	var b := Button.new()
	b.position = Vector2(30, 700)
	b.size = Vector2(740, 80)
	b.text = I18n.s("end.again")
	b.add_theme_font_size_override("font_size", 28)
	b.pressed.connect(func(): get_tree().reload_current_scene())
	p.add_child(b)
