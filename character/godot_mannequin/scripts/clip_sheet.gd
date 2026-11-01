extends SceneTree
func _initialize(): _run.call_deferred()
func _run():
	root.size = Vector2i(512, 512)
	var env := Environment.new(); env.background_mode = Environment.BG_COLOR; env.background_color = Color(1,0,1)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR; env.ambient_light_color = Color(1,1,1); env.ambient_light_energy=0.6
	var we := WorldEnvironment.new(); we.environment = env; root.add_child(we)
	var cam := Camera3D.new(); cam.projection = Camera3D.PROJECTION_ORTHOGONAL; cam.size=2.3; cam.keep_aspect=Camera3D.KEEP_HEIGHT; cam.near=0.1; cam.far=100
	root.add_child(cam); cam.global_position=Vector3(-2.0,1.6,2.8); cam.look_at(Vector3(0,1.0,0),Vector3.UP); cam.current=true
	var n = load("res://assets/kaykit/Knight.glb").instantiate(); root.add_child(n)
	var sk: Skeleton3D = null; var ap: AnimationPlayer = null
	var stack = [n]
	while stack.size() > 0:
		var x = stack.pop_back()
		if x is Skeleton3D: sk = x
		if x is AnimationPlayer: ap = x
		for c in x.get_children(): stack.append(c)
	var clips = ["Idle","Blocking","Block","Running_A","Running_B","1H_Melee_Attack_Slice_Horizontal","1H_Melee_Attack_Chop","1H_Melee_Attack_Stab","2H_Melee_Attack_Slice","Spellcast_Raise","Jump_Start","Dodge_Forward"]
	var img := Image.create(2048,1536,false,Image.FORMAT_RGBA8)
	var i := 0
	for clip in clips:
		ap.play(clip); ap.pause()
		var L = ap.get_animation(clip).length
		ap.seek(L*0.35, true)
		await process_frame
		await RenderingServer.frame_post_draw
		var cap := root.get_texture().get_image()
		var col = i % 4; var row = i / 4
		img.blit_rect(cap, Rect2i(0,0,512,512), Vector2i(col*512,row*512))
		i += 1
	img.save_png("/home/ithea/projects/artist2d/output/_rigtest/clips.png")
	print("CLIPS_DONE")
	quit()
