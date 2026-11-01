extends SceneTree

## Quick diagnostic: render the raw KayKit Knight from +Z and -Z with the
## 1H_Melee_Attack_Chop clip at its mid pose, to see which way it faces.

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var packed: PackedScene = load("res://assets/kaykit/Knight.glb")
	var inst := packed.instantiate()
	root.add_child(inst)
	var skel := _find(inst, "Skeleton3D") as Skeleton3D
	var ap := _find(inst, "AnimationPlayer") as AnimationPlayer
	ap.play("1H_Melee_Attack_Chop")
	ap.seek(ap.current_animation_length * 0.5, true)
	ap.pause()
	await process_frame
	await process_frame

	var aabb := _aabb(inst)
	print("AABB ", aabb)

	for side in [1, -1]:
		var vp := SubViewport.new()
		vp.size = Vector2i(512, 512)
		vp.transparent_bg = false
		vp.render_target_update_mode = SubViewport.UPDATE_ONCE
		root.add_child(vp)
		var cam := Camera3D.new()
		cam.projection = Camera3D.PROJECTION_ORTHOGONAL
		cam.size = 2.6
		cam.near = 0.1
		cam.far = 100.0
		vp.add_child(cam)
		cam.global_position = Vector3(0.0, 1.2, side * 6.0)
		cam.look_at(Vector3(0.0, 1.0, 0.0), Vector3.UP)
		cam.current = true
		var we := WorldEnvironment.new()
		var env := Environment.new()
		env.background_mode = Environment.BG_COLOR
		env.background_color = Color(0.1, 0.1, 0.12)
		env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
		env.ambient_light_color = Color(1, 1, 1)
		env.ambient_light_energy = 0.8
		we.environment = env
		vp.add_child(we)
		var sun := DirectionalLight3D.new()
		sun.rotation_degrees = Vector3(-40, -35, 0)
		sun.light_energy = 1.2
		vp.add_child(sun)
		await process_frame
		await process_frame
		var img := vp.get_texture().get_image()
		img.save_png("/tmp/opencode/kaykit_%s.png" % ("plusZ" if side == 1 else "minusZ"))
		vp.queue_free()
	quit()

func _find(node: Node, cls: String) -> Node:
	if node.is_class(cls):
		return node
	for c in node.get_children():
		var r := _find(c, cls)
		if r != null:
			return r
	return null

func _aabb(node: Node) -> AABB:
	var out := AABB()
	var first := true
	if node is MeshInstance3D and node.mesh != null:
		var box: AABB = node.global_transform * node.mesh.get_aabb()
		if first:
			out = box
			first = false
		else:
			out = out.merge(box)
	if node is Skeleton3D:
		for i in node.get_bone_count():
			var p: Vector3 = node.global_transform * node.get_bone_global_pose(i).origin
			if first:
				out = AABB(p, Vector3.ZERO)
				first = false
			else:
				out = out.expand(p)
	for c in node.get_children():
		var sub := _aabb(c)
		if sub.size != Vector3.ZERO:
			if first:
				out = sub
				first = false
			else:
				out = out.merge(sub)
	return out
