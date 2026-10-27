extends SceneTree

func _init() -> void:
	var t := DevilsTable.new()
	t.new_game("{}", 100, 12345)
	for c in ["EyeOfDestiny", "SecondChance", "TwinChips"]:
		t.unlock_memory(c)
		print("equip ", c, " -> ", t.equip_memory(c))
	var hands := 0
	var seals := 0
	var duels_started := 0
	var mem_used := 0
	var ending := ""
	while hands < 5000 and ending == "":
		var s: Dictionary = JSON.parse_string(t.state())
		if s["campaign"]["ending"] != null:
			ending = str(s["campaign"]["ending"])
			break
		var r: Dictionary = JSON.parse_string(t.start_round(10, "{}"))
		if r.has("error"):
			print("ERR ", r)
			break
		var evs: Array = r["campaign_events"]
		while true:
			for e in evs:
				if e is Dictionary and e.has("DuelStarted"):
					duels_started += 1
				if e is Dictionary and e.has("SealWon"):
					seals += 1
			s = JSON.parse_string(t.state())
			if s["phase"] == "insurance":
				evs = JSON.parse_string(t.insurance(0))["campaign_events"]
			elif s["phase"] == "player":
				if mem_used < 3 and not JSON.parse_string(t.use_memory("EyeOfDestiny")).has("error"):
					mem_used += 1
				var h: Dictionary = s["hands"][int(s["active"])]
				var a := "hit" if int(h["value"]) < 17 else "stand"
				evs = JSON.parse_string(t.act(a))["campaign_events"]
			else:
				break
		hands += 1
	var f: Dictionary = JSON.parse_string(t.state())
	print("hands=", hands, " duels=", duels_started, " seals=", seals, " ending=", ending, " pulse=", f["pulse"], " act=", f["campaign"]["act"], " mem_used=", mem_used)
	quit()
