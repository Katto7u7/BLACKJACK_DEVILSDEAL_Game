class_name CardView
extends Control
## Naipe dibujado en codigo (el texto y los palos se componen en el motor, no vienen de la IA).

const IVORY := Color("F9F4EC")
const GOLD := Color("A87B39")
const RED := Color("B23339")
const INK := Color("130D0F")
const SIZE := Vector2(110, 154)

var code := ""
var face_up := true
var back_tex: Texture2D = load("res://assets/mesa/dorso.png")

func _init(c: String = "", up: bool = true) -> void:
	code = c
	face_up = up
	custom_minimum_size = SIZE
	size = SIZE

func _draw() -> void:
	if not face_up or code == "":
		draw_texture_rect(back_tex, Rect2(Vector2.ZERO, SIZE), false)
		return
	draw_rect(Rect2(Vector2.ZERO, SIZE), IVORY)
	draw_rect(Rect2(Vector2.ZERO, SIZE), GOLD, false, 3.0)
	var suit := code.substr(code.length() - 1)
	var rank := code.substr(0, code.length() - 1)
	var col := RED if suit == "H" or suit == "D" else INK
	var font := ThemeDB.fallback_font
	draw_string(font, Vector2(8, 28), rank, HORIZONTAL_ALIGNMENT_LEFT, -1, 24, col)
	_suit(suit, Vector2(19, 42), 7.0, col)
	_suit(suit, SIZE * 0.5 + Vector2(0, 4), 22.0, col)
	draw_set_transform(SIZE, PI, Vector2.ONE)
	draw_string(font, Vector2(8, 28), rank, HORIZONTAL_ALIGNMENT_LEFT, -1, 24, col)
	_suit(suit, Vector2(19, 42), 7.0, col)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)

func _suit(s: String, c: Vector2, r: float, col: Color) -> void:
	match s:
		"D":
			draw_colored_polygon(PackedVector2Array([c + Vector2(0, -r * 1.3), c + Vector2(r, 0), c + Vector2(0, r * 1.3), c + Vector2(-r, 0)]), col)
		"H":
			_heart(c, r, col, false)
		"S":
			_heart(c, r, col, true)
			draw_colored_polygon(PackedVector2Array([c + Vector2(0, r * 0.2), c + Vector2(-r * 0.45, r * 1.5), c + Vector2(r * 0.45, r * 1.5)]), col)
		"C":
			draw_circle(c + Vector2(0, -r * 0.55), r * 0.5, col)
			draw_circle(c + Vector2(-r * 0.55, r * 0.3), r * 0.5, col)
			draw_circle(c + Vector2(r * 0.55, r * 0.3), r * 0.5, col)
			draw_colored_polygon(PackedVector2Array([c + Vector2(0, 0), c + Vector2(-r * 0.4, r * 1.4), c + Vector2(r * 0.4, r * 1.4)]), col)

func _heart(c: Vector2, r: float, col: Color, up: bool) -> void:
	var k := -1.0 if up else 1.0
	draw_circle(c + Vector2(-r * 0.5, -r * 0.35 * k), r * 0.55, col)
	draw_circle(c + Vector2(r * 0.5, -r * 0.35 * k), r * 0.55, col)
	draw_colored_polygon(PackedVector2Array([c + Vector2(-r * 1.02, -r * 0.1 * k), c + Vector2(r * 1.02, -r * 0.1 * k), c + Vector2(0, r * 1.1 * k)]), col)
