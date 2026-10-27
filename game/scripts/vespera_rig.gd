class_name VesperaRig
extends Control
## Rig de busto de Vespera: expresion (imagen completa), parpadeo y habla por parches, respiracion.

const DIR := "res://assets/vespera/rig_v7/"

var rig: Dictionary
var base_rect := TextureRect.new()
var patch_rect := TextureRect.new()
var tex_cache: Dictionary = {}
var expression := "base"
var talk_time := 0.0
var blink_in := 2.0
var blink_left := 0.0
var t := 0.0
var scale_px := 1.0

func _ready() -> void:
	rig = JSON.parse_string(FileAccess.get_file_as_string(DIR + "rig.json"))
	base_rect.stretch_mode = TextureRect.STRETCH_SCALE
	base_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	base_rect.size = size
	add_child(base_rect)
	patch_rect.stretch_mode = TextureRect.STRETCH_SCALE
	patch_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	add_child(patch_rect)
	scale_px = size.x / float(rig["tam"])
	set_expression("base")

func _tex(path: String) -> Texture2D:
	if not tex_cache.has(path):
		tex_cache[path] = load(path)
	return tex_cache[path]

func set_expression(e: String) -> void:
	if not (e in rig["expresiones"]):
		e = "base"
	expression = e
	base_rect.texture = _tex(DIR + "cabeza_%s.png" % e)

func speak(seconds: float) -> void:
	talk_time = seconds

func _show_patch(name: String) -> void:
	var r: Array = rig["parches"][name]
	patch_rect.texture = _tex(DIR + "parche_%s.png" % name)
	patch_rect.position = Vector2(r[0], r[1]) * scale_px
	patch_rect.size = Vector2(r[2], r[3]) * scale_px
	patch_rect.visible = true

func _process(dt: float) -> void:
	t += dt
	pivot_offset = size * Vector2(0.5, 0.9)
	scale = Vector2.ONE * (1.0 + 0.006 * sin(t * 1.6))
	if talk_time > 0.0:
		talk_time -= dt
		var frames := ["talk_a", "talk_b", "talk_c", "talk_b"]
		_show_patch(frames[int(t * 8.0) % 4])
		return
	if blink_left > 0.0:
		blink_left -= dt
		_show_patch("blink")
		return
	patch_rect.visible = false
	blink_in -= dt
	if blink_in <= 0.0:
		blink_left = 0.14
		blink_in = randf_range(2.0, 5.5)
