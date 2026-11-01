extends SceneTree

## Side diagnostic: render the raw KayKit Knight's 1H_Melee_Attack_Chop at
## 8 evenly spaced times from the right side (the same 74-degree view the
## mannequin renderer now uses), to see the ground-truth arm depth.

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var packed: PackedScene = load("res://assets/kaykit/Knight.glb")
	var inst := packed.instantiate()
	root.add_child(inst)
	var ap := _find(inst, "AnimationPlayer") as AnimationPlayer
	var clip := "1H_Melee_Attack_Chop"
	ap.play(clip)
	ap.pause()
	var vp := SubViewport.new()
	vp.size = Vector2i(320, 320)
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(vp)
	var cam := Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = 3.4
	cam.near = 0.1
	cam.far = 100.0
	vp.add_child(cam)
	var ang := deg_to_rad(74.0)
	cam.global_position = Vector3(-6.0 * sin(ang), 1.5, 6.0 * cos(ang))
	cam.look_at(Vector3(0.0, 1.3, 0.0), Vector3.UP)
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
	var length := ap.current_animation_length
	for i in 8:
		ap.seek(length * float(i) / 8.0, true)
		await process_frame
		await process_frame
		vp.get_texture().get_image().save_png("/tmp/opencode/kaykit_side_%02d.png" % i)
	quit()

func _find(node: Node, cls: String) -> Node:
	if node.is_class(cls):
		return node
	for c in node.get_children():
		var r := _find(c, cls)
		if r != null:
			return r
	return null
