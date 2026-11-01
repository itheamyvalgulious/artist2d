extends SceneTree

## Rest-pose diagnostic: compare the rig's and KayKit's global rest bone axes.

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var Mannequin := load("res://scripts/mannequin.gd")
	var rig = Mannequin.new()
	root.add_child(rig)
	rig.build({})
	var rs: Skeleton3D = rig.skeleton
	print("--- RIG rest ---")
	for n in ["upper_arm_r", "lower_arm_r", "hand_r", "upper_arm_l", "hand_l", "hips", "chest"]:
		var i := rs.find_bone(n)
		if i < 0:
			print(n, " missing")
			continue
		var t := rs.get_bone_global_rest(i)
		print(n, " origin=", t.origin, " Yaxis=", t.basis.y.normalized(),
			" Xaxis=", t.basis.x.normalized(), " Zaxis=", t.basis.z.normalized())

	var packed: PackedScene = load("res://assets/kaykit/Knight.glb")
	var inst := packed.instantiate()
	root.add_child(inst)
	var sk := _find(inst, "Skeleton3D") as Skeleton3D
	print("KAYKIT NODE CHAIN")
	var node_iter: Node = sk
	while node_iter != null:
		print("  ", node_iter.name, " xform=", node_iter.transform, " global=", node_iter.global_transform)
		node_iter = node_iter.get_parent()
	print("RIG skeleton global=", rs.global_transform)
	print("--- KAYKIT rest ---")
	for n in ["upperarm.r", "lowerarm.r", "hand.r", "upperarm.l", "hand.l", "hips", "chest", "spine"]:
		var i := sk.find_bone(n)
		if i < 0:
			print(n, " missing")
			continue
		var t := sk.get_bone_global_rest(i)
		print(n, " origin=", t.origin, " Yaxis=", t.basis.y.normalized(),
			" Xaxis=", t.basis.x.normalized(), " Zaxis=", t.basis.z.normalized())

	# bone direction of the arm at the 50% chop pose
	var ap := _find(inst, "AnimationPlayer") as AnimationPlayer
	ap.play("1H_Melee_Attack_Chop")
	ap.seek(ap.current_animation_length * 0.5, true)
	ap.pause()
	await process_frame
	await process_frame
	print("--- KAYKIT posed 50% global pose ---")
	for n in ["upperarm.r", "lowerarm.r", "hand.r", "upperarm.l", "hand.l"]:
		var i := sk.find_bone(n)
		var t := sk.get_bone_global_pose(i)
		print(n, " origin=", t.origin, " Yaxis=", t.basis.y.normalized())
	quit()

func _find(node: Node, cls: String) -> Node:
	if node.is_class(cls):
		return node
	for c in node.get_children():
		var r := _find(c, cls)
		if r != null:
			return r
	return null
