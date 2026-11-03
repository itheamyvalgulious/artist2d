extends SceneTree
## Batch renderer for the parametric mannequin.
##
## Usage:
##   godot --path . --script res://scripts/render_actor.gd -- \
##       --action idle --out <dir> --params '{"head_scale":1.0,...}' --frames 8 \
##       [--source kaykit|procedural]
##
## Emits (mirroring PLAN module 1.1):
##   sheet_shaded.png    frames * 512 x 512   (toon shaded, magenta key)
##   sheet_part_id.png   frames * 64  x 64    (8 documented part IDs)
##   sheet_bone_id.png   frames * 64  x 64    (unique rigid-attachment IDs)
##   sheet_motion.json   projected screen anchors for pixel-level motion truth
##
## Two pose sources are supported:
##   procedural : hand-authored AnimationLibrary shipped with this project
##   kaykit     : CC0 KayKit Adventurers clip retargeted rotation-wise onto the
##                parametric rig (professional animation library, 76 clips).

const Mannequin := preload("res://scripts/mannequin.gd")
const HumanoidProfile := preload("res://scripts/humanoid_profile.gd")
const FRAME_HI := 512
const FRAME_LO := 64
const RIG_SCALE := 0.82

# action name -> KayKit clip
const ACTION_CLIPS := {
	"idle": "Idle",
	"running": "Running_A",
	"attack": "1H_Melee_Attack_Chop",
	"defend": "Blocking",
	"jump": "Jump_Start",
	"in_air": "Jump_Full_Short",
	"sword_block": "Blocking",
	"run": "Running_A",
	"attack_combo": "1H_Melee_Attack_Chop",
	"shoot1": "1H_Ranged_Shoot",
	"shoot2": "1H_Ranged_Shoot",
	"shoot3": "1H_Ranged_Shoot",
	"slash1": "1H_Melee_Attack_Slice_Horizontal",
	"slash2": "1H_Melee_Attack_Slice_Horizontal",
	"slash3": "1H_Melee_Attack_Slice_Horizontal",
	"block": "Blocking",
	"roll": "Dodge_Forward",
}

# our bone -> reference bone (KayKit humanoid)
const RETARGET_MAP := {
	"hips": "hips",
	"spine": "spine",
	"chest": "chest",
	"neck": "chest",
	"head": "head",
	"shoulder_l": "chest",
	"shoulder_r": "chest",
	"upper_arm_l": "upperarm.l",
	"lower_arm_l": "lowerarm.l",
	"hand_l": "hand.l",
	"upper_arm_r": "upperarm.r",
	"lower_arm_r": "lowerarm.r",
	"hand_r": "hand.r",
	"upper_leg_l": "upperleg.l",
	"lower_leg_l": "lowerleg.l",
	"foot_l": "foot.l",
	"upper_leg_r": "upperleg.r",
	"lower_leg_r": "lowerleg.r",
	"foot_r": "foot.r",
}

# Clips whose action is only one phase of a longer animation use a normalized
# sub-range (start, end).  in_air is the apex of the full jump, not the whole
# take-off/land cycle.
const ACTION_RANGES := {
	"in_air": [0.35, 0.68],
}

const BONE_PARENT := {
	"hips": "", "spine": "hips", "chest": "spine", "neck": "chest", "head": "neck",
	"shoulder_l": "chest", "upper_arm_l": "shoulder_l", "lower_arm_l": "upper_arm_l", "hand_l": "lower_arm_l",
	"shoulder_r": "chest", "upper_arm_r": "shoulder_r", "lower_arm_r": "upper_arm_r", "hand_r": "lower_arm_r",
	"upper_leg_l": "hips", "lower_leg_l": "upper_leg_l", "foot_l": "lower_leg_l",
	"upper_leg_r": "hips", "lower_leg_r": "upper_leg_r", "foot_r": "lower_leg_r",
}

var vp: Window
var cam: Camera3D
var rig: Node3D
var requested_params: Dictionary = {}
var ref_root: Node3D
var ref_skel: Skeleton3D
var ref_ap: AnimationPlayer
var retarget_pairs: Dictionary = {}
var weapon_rel := Basis.IDENTITY
var requested_cam := Vector3(-70.0, 37.0, 20.0)
var use_kaykit := false
var current_action := "idle"
var current_frames := 8


func _initialize() -> void:
	_run.call_deferred()


func _args() -> Dictionary:
	var out := {}
	var argv := OS.get_cmdline_user_args()
	var i := 0
	while i < argv.size():
		var a: String = argv[i]
		if a.begins_with("--") and i + 1 < argv.size():
			out[a.substr(2)] = argv[i + 1]
			i += 2
		else:
			i += 1
	return out


func _run() -> void:
	var args := _args()
	var action: String = args.get("action", "idle")
	current_action = action
	var outdir: String = args.get("out", "user://out")
	var frames: int = int(args.get("frames", "8"))
	current_frames = frames
	var source: String = args.get("source", "kaykit")
	var gear_mode: Dictionary = {"katana": "back", "pistol": "hip"}
	if args.has("gear"):
		var parsed_gear = JSON.parse_string(args["gear"])
		if parsed_gear is Dictionary:
			for k in parsed_gear.keys():
				gear_mode[k] = parsed_gear[k]
	var p := {
		"head_scale": 1.0,
		"torso_len": 1.0,
		"limb_len": 1.0,
		"shoulder_width": 1.0,
	}
	if args.has("params"):
		var parsed = JSON.parse_string(args["params"])
		if parsed is Dictionary:
			for k in parsed.keys():
				p[k] = parsed[k]
	requested_params = p
	if args.has("cam"):
		var cv := String(args["cam"]).split_floats(",")
		if cv.size() == 3:
			requested_cam = Vector3(cv[0], cv[1], cv[2])
	DirAccess.make_dir_recursive_absolute(outdir)
	_build_scene()
	rig.set_gear(gear_mode)

	var poses: Array = []
	var clip := ""
	use_kaykit = source == "kaykit" and _setup_reference()
	if use_kaykit:
		rig.stop_animation()
		clip = args.get("clip", ACTION_CLIPS.get(action, "Idle"))
		var rng: Array = ACTION_RANGES.get(action, [0.0, 1.0])
		var start: float = float(args.get("start", str(rng[0])))
		var end: float = float(args.get("end", str(rng[1])))
		if action == "roll" and not args.has("base-clip"):
			# KayKit has no somersault clip.  Build the roll from a held crouch
			# (Dodge_Forward) plus a deterministic 360-degree pitch of the whole
			# skeleton in _apply_roll(); frames 0/7 use the idle pose so the
			# idle -> roll -> idle transition is honest on both ends.
			var crouch: Array = await _precompute_poses("Dodge_Forward", frames, 0.32, 0.40)
			var idle_pose: Array = await _precompute_poses("Idle", frames, 0.0, 0.0)
			poses = []
			for fi in frames:
				if fi == 0 or fi == frames - 1:
					poses.append(idle_pose[fi])
				else:
					poses.append(crouch[fi])
			clip = "Dodge_Forward_crouch+360pitch"
		elif args.has("base-clip"):
			var base_clip: String = args.get("base-clip", "Running_A")
			var upper_clip: String = args.get("upper-clip", clip)
			var brng: Array = ACTION_RANGES.get("base", [0.0, 1.0])
			var bs: float = float(args.get("base-start", str(brng[0])))
			var be: float = float(args.get("base-end", str(brng[1])))
			var us: float = float(args.get("upper-start", "0.0"))
			var ue: float = float(args.get("upper-end", "1.0"))
			var base_poses: Array = await _precompute_poses(base_clip, frames, bs, be)
			var upper_poses: Array = await _precompute_poses(upper_clip, frames, us, ue)
			poses = []
			for fi in frames:
				poses.append(_merge_upper(base_poses[fi], upper_poses[fi]))
			clip = base_clip + "+" + upper_clip
		else:
			poses = await _precompute_poses(clip, frames, start, end)
	else:
		rig.play_action(action)

	if use_kaykit and not poses.is_empty():
		_apply_pose(poses[0])
		await process_frame
		var holder: Node3D = rig.attachments["weapon"]
		if holder.visible:
			holder.quaternion = weapon_rel.get_rotation_quaternion()

	if args.has("trace"):
		await _write_trace(outdir, clip, poses, frames)
		quit()
		return

	if args.has("views"):
		await _write_views(outdir, poses, int(args.get("view_frame", "4")))
		quit()
		return

	var sheet_hi := Image.create(FRAME_HI * frames, FRAME_HI, false, Image.FORMAT_RGBA8)
	var sheet_part := Image.create(FRAME_LO * frames, FRAME_LO, false, Image.FORMAT_RGBA8)
	var sheet_bone := Image.create(FRAME_LO * frames, FRAME_LO, false, Image.FORMAT_RGBA8)

	# ---------------- shaded pass (512 px per frame) -----------------------
	vp.size = Vector2i(FRAME_HI, FRAME_HI)
	await process_frame
	rig.set_simple(true)
	rig.set_pass("shaded")
	for i in frames:
		await _pose(i, frames, poses)
		var img := await _capture()
		img.convert(Image.FORMAT_RGBA8)
		sheet_hi.blit_rect(img, Rect2i(0, 0, FRAME_HI, FRAME_HI), Vector2i(i * FRAME_HI, 0))
		if i == 0:
			img.save_png(outdir.path_join("frame_preview.png"))

	rig.set_simple(false)
	# ---------------- clay pass (512 px per frame) ------------------------
	# Same poses with one neutral material: the edit model reads the true
	# silhouette instead of confusing near-black outfit boxes with weapons.
	rig.set_pass("clay")
	var sheet_clay := Image.create(FRAME_HI * frames, FRAME_HI, false, Image.FORMAT_RGBA8)
	for i in frames:
		await _pose(i, frames, poses)
		var clay_img := await _capture()
		clay_img.convert(Image.FORMAT_RGBA8)
		sheet_clay.blit_rect(clay_img, Rect2i(0, 0, FRAME_HI, FRAME_HI), Vector2i(i * FRAME_HI, 0))

	# ---------------- part-colour pass (512 px per frame) -----------------
	# A flat, colour-coded pose proxy: each part is a distinct flat colour
	# (legend supplied to the edit model).  Hair is hidden so the proxy shows
	# the pose and the weapons only; the character's hair/appearance comes
	# from the reference.
	vp.size = Vector2i(FRAME_HI, FRAME_HI)
	await process_frame
	rig.set_simple(true)
	rig.set_pass("part_id")
	var sheet_parts := Image.create(FRAME_HI * frames, FRAME_HI, false, Image.FORMAT_RGBA8)
	for i in frames:
		await _pose(i, frames, poses)
		var part_img := await _capture()
		part_img.convert(Image.FORMAT_RGBA8)
		sheet_parts.blit_rect(part_img, Rect2i(0, 0, FRAME_HI, FRAME_HI), Vector2i(i * FRAME_HI, 0))
	rig.set_simple(false)

	# ---------------- part-ID pass (64 px per frame) ----------------------
	vp.size = Vector2i(FRAME_LO, FRAME_LO)
	await process_frame
	rig.set_pass("part_id")
	for i in frames:
		await _pose(i, frames, poses)
		var img := await _capture()
		img.convert(Image.FORMAT_RGBA8)
		sheet_part.blit_rect(img, Rect2i(0, 0, FRAME_LO, FRAME_LO), Vector2i(i * FRAME_LO, 0))

	# ---------------- bone-ID pass + projection truth ---------------------
	rig.set_pass("bone_id")
	var frames_data: Array = []
	for i in frames:
		await _pose(i, frames, poses)
		var img := await _capture()
		img.convert(Image.FORMAT_RGBA8)
		sheet_bone.blit_rect(img, Rect2i(0, 0, FRAME_LO, FRAME_LO), Vector2i(i * FRAME_LO, 0))
		var bones := {}
		for key in rig.attachments.keys():
			var att: Node3D = rig.attachments[key]
			if not att.is_inside_tree():
				continue
			var o: Vector2 = cam.unproject_position(att.global_transform.origin)
			var px: Vector2 = cam.unproject_position(att.global_transform * Vector3(1.0, 0.0, 0.0))
			var py: Vector2 = cam.unproject_position(att.global_transform * Vector3(0.0, 1.0, 0.0))
			bones[key] = [[o.x, o.y], [px.x, px.y], [py.x, py.y]]
		frames_data.append({"frame": i, "bones": bones})

	sheet_hi.save_png(outdir.path_join("sheet_shaded.png"))
	sheet_parts.save_png(outdir.path_join("sheet_parts.png"))
	sheet_clay.save_png(outdir.path_join("sheet_clay.png"))
	sheet_part.save_png(outdir.path_join("sheet_part_id.png"))
	sheet_bone.save_png(outdir.path_join("sheet_bone_id.png"))

	var payload := {
		"schema": "pixel-mannequin-truth/1",
		"action": action,
		"pose_source": "kaykit" if use_kaykit else "procedural",
		"clip": ACTION_CLIPS.get(action, "") if use_kaykit else "",
		"frames": frames,
		"frame_size": [FRAME_LO, FRAME_LO],
		"hi_frame_size": [FRAME_HI, FRAME_HI],
		"rig_scale": RIG_SCALE,
		"params": p,
		"camera": {
			"position": [cam.global_position.x, cam.global_position.y, cam.global_position.z],
			"size": cam.size,
			"orthogonal": true,
		},
		"part_colors": _colors_to_array(Mannequin.PART_COLORS),
		"bone_colors": _colors_to_array(Mannequin.BONE_COLORS),
		"attachments": rig.attachments.keys(),
		"frames_data": frames_data,
	}
	var f := FileAccess.open(outdir.path_join("sheet_motion.json"), FileAccess.WRITE)
	f.store_string(JSON.stringify(payload, "  "))
	f.close()
	print("MANNEQUIN_DONE ", action, " source=", "kaykit" if use_kaykit else "procedural", " -> ", outdir)
	quit()


func _colors_to_array(d: Dictionary) -> Dictionary:
	var out := {}
	for k in d.keys():
		var c: Color = d[k]
		out[k] = [c.r8, c.g8, c.b8]
	return out


func _capture() -> Image:
	RenderingServer.force_draw(false)
	await RenderingServer.frame_post_draw
	return vp.get_texture().get_image()


func _write_views(outdir: String, poses: Array, frame: int) -> void:
	_apply_pose(poses[clampi(frame, 0, poses.size() - 1)])
	await process_frame
	for angle in [0, 90, 180, 270]:
		var rad := deg_to_rad(float(angle))
		cam.global_position = Vector3(-70.0 * sin(rad), 37.0, 70.0 * cos(rad))
		cam.look_at(Vector3(0.0, 29.0, 0.0), Vector3.UP)
		await process_frame
		await process_frame
		var img := await _capture()
		img.save_png(outdir + "/view_%03d.png" % angle)
		print("VIEW ", angle)
	print("VIEWS_DONE ", outdir)


func _write_trace(outdir: String, clip: String, poses: Array, frames: int) -> void:
	var limb: float = float(requested_params.get("limb_len", 1.0))
	var samples: Array = []
	for i in frames:
		_apply_pose(poses[i])
		_apply_roll(i, frames)
		await process_frame
		var weapon: Node3D = rig.attachments["weapon"]
		var hand_r: Node3D = rig.attachments["hand_r"]
		var hand_l: Node3D = rig.attachments["hand_l"]
		var shield: Node3D = rig.attachments["shield"]
		var hips: Node3D = rig.attachments["hips"]
		var tip: Vector3 = weapon.global_transform * Vector3(0.0, 19.5 * limb, 0.0)
		samples.append({
			"i": i,
			"t": float(i) / float(frames),
			"tip": [tip.x, tip.y, tip.z],
			"hand_r": [hand_r.global_transform.origin.x, hand_r.global_transform.origin.y, hand_r.global_transform.origin.z],
			"hand_l": [hand_l.global_transform.origin.x, hand_l.global_transform.origin.y, hand_l.global_transform.origin.z],
			"shield": [shield.global_transform.origin.x, shield.global_transform.origin.y, shield.global_transform.origin.z],
			"hips": [hips.global_transform.origin.x, hips.global_transform.origin.y, hips.global_transform.origin.z],
		})
	var out := {
		"clip": clip,
		"samples": frames,
		"forward_axis": [0.0, 0.0, 1.0],
		"camera": [cam.global_position.x, cam.global_position.y, cam.global_position.z],
		"samples_data": samples,
	}
	var f := FileAccess.open(outdir + "/motion_trace.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(out, "  "))
	f.close()
	print("MOTION_TRACE ", outdir + "/motion_trace.json")


func _pose(i: int, frames: int, poses: Array) -> void:
	if use_kaykit and not poses.is_empty():
		_apply_pose(poses[i])
	else:
		var denom: float = float(max(1, frames - 1)) if current_action == "roll" else float(frames)
		rig.seek_time(float(i) / denom)
	_apply_roll(i, frames)
	await process_frame
	await RenderingServer.frame_post_draw


func _apply_roll(i: int, frames: int) -> void:
	# Rotate the whole skeleton around the body centre for the forward roll.
	# The bone poses themselves stay a held crouch, so the 3D truth sheet
	# shows a real somersault instead of eight near-identical crouches.
	if current_action != "roll" or frames < 4:
		rig.skeleton.transform = Transform3D.IDENTITY
		return
	var angle := 0.0
	if i >= 1 and i <= frames - 2:
		# Full 360: frame 1 is the tuck at 0deg and frame 6 is a distinct
		# landing crouch at 360deg, so the roll completes and stands up.
		angle = 360.0 * float(i - 1) / float(frames - 3)
	var b := Basis(Vector3(1.0, 0.0, 0.0), deg_to_rad(angle))
	var pivot := Vector3(0.0, rig.hips_rest_y * 0.86, 0.0)
	rig.skeleton.transform = Transform3D(b, pivot - b * pivot)


# ---------------------------------------------------------------------------
# KayKit retargeting
# ---------------------------------------------------------------------------
func _setup_reference() -> bool:
	var path := "res://assets/kaykit/Knight.glb"
	if not ResourceLoader.exists(path):
		push_warning("KayKit reference not found, falling back to procedural")
		return false
	var packed: PackedScene = load(path)
	if packed == null:
		return false
	ref_root = packed.instantiate()
	ref_root.visible = false
	root.add_child(ref_root)
	ref_skel = _find_first(ref_root, "Skeleton3D") as Skeleton3D
	ref_ap = _find_first(ref_root, "AnimationPlayer") as AnimationPlayer
	if ref_skel == null or ref_ap == null:
		push_warning("KayKit scene missing skeleton or AnimationPlayer")
		return false
	# Derive the retarget pairs from the profile BoneMaps (not a separate
	# hand-written rig map): rig bone -> humanoid -> reference bone.
	var bm_rig := HumanoidProfile.make_bone_map()
	var bm_ref := HumanoidProfile.make_reference_bone_map()
	retarget_pairs.clear()
	for i in rig.skeleton.get_bone_count():
		var rig_bone: String = String(rig.skeleton.get_bone_name(i))
		var humanoid_name: StringName = bm_rig.find_profile_bone_name(rig_bone)
		if String(humanoid_name) == "":
			continue
		var ref_bone: StringName = bm_ref.get_skeleton_bone_name(humanoid_name)
		if String(ref_bone) == "":
			continue
		if ref_bone != "" and ref_skel.find_bone(ref_bone) >= 0:
			retarget_pairs[rig_bone] = ref_bone
	# KayKit's 1H_Sword node is a child of handslot.r.  Its orientation
	# relative to hand.r is the true grip orientation; our weapon box must
	# inherit that, not a hard-coded world-up.
	var hand_i := ref_skel.find_bone("hand.r")
	var sword_node := _find_named(ref_root, "1H_Sword")
	if hand_i >= 0 and sword_node != null:
		var hrest := ref_skel.get_bone_global_rest(hand_i)
		var sword_skel: Transform3D = ref_skel.global_transform.affine_inverse() * sword_node.global_transform
		weapon_rel = sword_skel.basis.orthonormalized()
		print("WEAPON_REL ", weapon_rel)
	print("RETARGET_PAIRS ", retarget_pairs.size(), " from BoneMap")
	return true


func _find_named(node: Node, target: String) -> Node:
	if node.name == target:
		return node
	for c in node.get_children():
		var r := _find_named(c, target)
		if r != null:
			return r
	return null


func _find_first(node: Node, cls: String) -> Node:
	if node.is_class(cls):
		return node
	for c in node.get_children():
		var r := _find_first(c, cls)
		if r != null:
			return r
	return null


func _precompute_poses(clip: String, frames: int, start: float = 0.0, end: float = 1.0) -> Array:
	var anim := ref_ap.get_animation(clip)
	if anim == null:
		push_warning("clip not found: " + clip)
		return []
	var length := anim.length
	ref_ap.play(clip)
	ref_ap.pause()
	var out: Array = []
	var ref_bones := {}
	for b in retarget_pairs.keys():
		ref_bones[b] = ref_skel.find_bone(retarget_pairs[b])
	for i in frames:
		var phase: float = lerpf(start, end, float(i) / float(frames))
		ref_ap.seek(length * phase, true)
		await process_frame
		# World-space rotation delta of every mapped bone vs. its rest pose.
		var delta := {}
		for b in ref_bones.keys():
			var ri: int = ref_bones[b]
			var g := ref_skel.get_bone_global_pose(ri)
			var r := ref_skel.get_bone_global_rest(ri)
			delta[b] = g.basis.orthonormalized() * r.basis.orthonormalized().inverse()
		var rots := {}
		for b in delta.keys():
			var parent: String = BONE_PARENT[b]
			var local: Basis = delta[b]
			if parent != "" and delta.has(parent):
				local = (delta[parent] as Basis).inverse() * (delta[b] as Basis)
			# KayKit's rest bone bases are NOT the rig's rest bases.  The
			# world-space delta must be conjugated into the rig bone's rest
			# frame, otherwise the arms/legs swing around the wrong axis
			# (the right arm went backwards in the chop).
			var ri_rig: int = rig.skeleton.find_bone(b)
			var m: Basis = rig.skeleton.get_bone_global_rest(ri_rig).basis.orthonormalized()
			var q: Quaternion = (m.inverse() * local * m).get_rotation_quaternion()
			rots[b] = q
		# hips vertical motion (kept in-place: horizontal root motion removed)
		var hi: int = ref_skel.find_bone("hips")
		var hp := ref_skel.get_bone_global_pose(hi)
		var hr := ref_skel.get_bone_global_rest(hi)
		var k: float = rig.hips_rest_y / maxf(hr.origin.y, 0.001)
		var hips_pos := Vector3(0.0, rig.hips_rest_y + (hp.origin.y - hr.origin.y) * k, 0.0)
		out.append({"rot": rots, "hips": hips_pos})

	return out


func _merge_upper(base_pose: Dictionary, upper_pose: Dictionary) -> Dictionary:
	# Run-and-gun / airborne variants: keep the base clip's legs and hips,
	# take the upper clip's torso, head and arms.  Both clips are retargeted
	# into the same rig space, so the bone rotations can be combined directly.
	var upper_bones := {
		"spine": true, "chest": true, "neck": true, "head": true,
		"shoulder_l": true, "upper_arm_l": true, "lower_arm_l": true, "hand_l": true,
		"shoulder_r": true, "upper_arm_r": true, "lower_arm_r": true, "hand_r": true,
	}
	var merged_rot: Dictionary = (base_pose["rot"] as Dictionary).duplicate()
	var upper_rot: Dictionary = upper_pose["rot"]
	for b in upper_rot.keys():
		if upper_bones.has(b):
			merged_rot[b] = upper_rot[b]
	return {"rot": merged_rot, "hips": base_pose["hips"]}


func _apply_pose(pose: Dictionary) -> void:
	var rots: Dictionary = pose["rot"]
	for b in rots.keys():
		rig.skeleton.set_bone_pose_rotation(rig.skeleton.find_bone(b), rots[b])
	rig.skeleton.set_bone_pose_position(rig.skeleton.find_bone("hips"), pose["hips"])


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------
func _build_scene() -> void:
	vp = root
	vp.size = Vector2i(FRAME_HI, FRAME_HI)
	vp.msaa_3d = Viewport.MSAA_DISABLED
	vp.screen_space_aa = Viewport.SCREEN_SPACE_AA_DISABLED
	vp.use_taa = false
	vp.world_3d.environment = null

	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(1.0, 0.0, 1.0, 1.0)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.55, 0.55, 0.62)
	env.ambient_light_energy = 0.45
	var we := WorldEnvironment.new()
	we.name = "WorldEnvironment"
	we.environment = env
	vp.add_child(we)

	cam = Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	cam.size = 64.0
	cam.near = 1.0
	cam.far = 400.0
	cam.keep_aspect = Camera3D.KEEP_HEIGHT
	vp.add_child(cam)
	cam.global_position = requested_cam
	cam.look_at(Vector3(0.0, 29.0, 0.0), Vector3.UP)
	cam.current = true

	var sun := DirectionalLight3D.new()
	sun.name = "Sun"
	sun.rotation_degrees = Vector3(-40, -35, 0)
	sun.light_energy = 1.15
	vp.add_child(sun)

	rig = Mannequin.new()
	rig.name = "Mannequin"
	rig.scale = Vector3(RIG_SCALE, RIG_SCALE, RIG_SCALE)
	vp.add_child(rig)
	rig.build(requested_params)
	var hp := HumanoidProfile.validate(rig.skeleton)
	print("HUMANOID_PROFILE mapped=", hp["mapped"], " missing=", hp["missing"])
	HumanoidProfile.save_profile()
	var bm := HumanoidProfile.make_bone_map()
	HumanoidProfile.save_bone_map()
	print("BONEMAP hips=", bm.find_profile_bone_name("hips"),
		" head=", bm.find_profile_bone_name("head"),
		" hand_r=", bm.find_profile_bone_name("hand_r"))
