extends Node3D
## Parametric humanoid mannequin used as the motion/pose truth source.
##
## The rig is built procedurally so proportions can be changed at render time
## without shear: bone REST transforms are recomputed from the requested
## parameters (not runtime scale on rotating chain bones), and the only runtime
## scale (head_scale) is applied on a leaf bone whose attachment nodes are
## inverse-compensated. That keeps every child mesh axis-aligned and rigid.

const PART_COLORS := {
	"head": Color(1.0, 0.0, 0.0, 1.0),
	"torso": Color(0.0, 1.0, 0.0, 1.0),
	"arm_l": Color(0.0, 0.0, 1.0, 1.0),
	"arm_r": Color(1.0, 1.0, 0.0, 1.0),
	"leg_l": Color(1.0, 0.0, 0.5019608, 1.0),
	"leg_r": Color(0.5333333, 0.0, 1.0, 1.0),
	"weapon": Color(0.0, 1.0, 1.0, 1.0),
	"katana": Color(0.0, 1.0, 1.0, 1.0),
	"scabbard": Color(0.65, 0.0, 1.0, 1.0),
	"pistol": Color(1.0, 0.55, 0.0, 1.0),
	"holster": Color(0.9, 0.9, 0.9, 1.0),
	"shield": Color(1.0, 1.0, 1.0, 1.0),
}

# Unique debug colour per rigid attachment.  Used only to derive per-pixel
# motion truth; it is not part of the delivered 8-part sheet.
const BONE_COLORS := {
	"hips": Color(1.0, 0.0, 0.0, 1.0),
	"chest": Color(0.0, 1.0, 0.0, 1.0),
	"head": Color(0.0, 0.0, 1.0, 1.0),
	"upper_arm_l": Color(1.0, 1.0, 0.0, 1.0),
	"lower_arm_l": Color(1.0, 0.0, 0.5, 1.0),
	"hand_l": Color(0.5, 0.0, 1.0, 1.0),
	"upper_arm_r": Color(0.0, 1.0, 1.0, 1.0),
	"lower_arm_r": Color(1.0, 0.5, 0.0, 1.0),
	"hand_r": Color(0.5, 1.0, 0.0, 1.0),
	"upper_leg_l": Color(0.75, 0.0, 0.75, 1.0),
	"lower_leg_l": Color(0.0, 1.0, 0.5, 1.0),
	"foot_l": Color(1.0, 0.25, 0.25, 1.0),
	"upper_leg_r": Color(0.25, 0.25, 1.0, 1.0),
	"lower_leg_r": Color(0.25, 1.0, 0.25, 1.0),
	"foot_r": Color(1.0, 1.0, 0.25, 1.0),
	"weapon": Color(0.0, 0.5, 1.0, 1.0),
	"shield": Color(0.8, 0.2, 0.8, 1.0),
	"pistol": Color(0.1, 0.9, 0.9, 1.0),
	"katana_back": Color(0.9, 0.1, 0.9, 1.0),
	"pistol_hip": Color(0.9, 0.9, 0.1, 1.0),
}

const SHADED_COLORS := {
	"head": Color(0.86, 0.66, 0.50),
	"torso": Color(0.56, 0.22, 0.20),
	"arm_l": Color(0.62, 0.66, 0.74),
	"arm_r": Color(0.62, 0.66, 0.74),
	"leg_l": Color(0.30, 0.26, 0.34),
	"leg_r": Color(0.30, 0.26, 0.34),
	"weapon": Color(0.78, 0.82, 0.90),
	"shield": Color(0.44, 0.30, 0.18),
}

var skeleton: Skeleton3D
var anim_player: AnimationPlayer
var params: Dictionary = {}
var character: String = "knight"
var gear_mode: Dictionary = {"katana": "back", "pistol": "hip"}
var attachments: Dictionary = {}   # bone key -> BoneAttachment3D
var hips_rest_y := 26.0
var meshes: Array[MeshInstance3D] = []
var mesh_keys: Array[String] = []  # parallel: bone key for each mesh
var shaded_mats: Dictionary = {}
var part_mats: Dictionary = {}
var bone_mats: Dictionary = {}
var clay_mat: StandardMaterial3D = null


func _ready() -> void:
	pass


func build(p: Dictionary) -> void:
	params = p.duplicate()
	character = String(params.get("character", "knight"))
	_build_skeleton()
	_build_parts()
	_build_animations()
	set_gear(gear_mode)
	set_pass("shaded")


func _bone_layout() -> Dictionary:
	var head_scale: float = float(params.get("head_scale", 1.0))
	var torso_len: float = float(params.get("torso_len", 1.0))
	var limb_len: float = float(params.get("limb_len", 1.0))
	var shoulder_width: float = float(params.get("shoulder_width", 1.0))

	var foot_y := 2.5
	var lower_leg_len := 11.5 * limb_len
	var upper_leg_len := 12.0 * limb_len
	var hips_y := foot_y + lower_leg_len + upper_leg_len
	var neck_y := hips_y + 16.0 * torso_len
	var head_y := neck_y + 3.0
	var shoulder_y := neck_y - 1.0
	var elbow_y := shoulder_y - 9.0 * limb_len
	var hand_y := elbow_y - 8.0 * limb_len
	var knee_y := hips_y - upper_leg_len
	var sx := 10.0 * shoulder_width

	return {
		"root": Vector3.ZERO,
		"hips": Vector3(0, hips_y, 0),
		"spine": Vector3(0, hips_y + 3.0 * torso_len, 0),
		"chest": Vector3(0, neck_y - 6.0 * torso_len, 0),
		"neck": Vector3(0, neck_y - 2.0, 0),
		"head": Vector3(0, head_y, 0),
		"shoulder_l": Vector3(sx * 0.45, shoulder_y, 0),
		"upper_arm_l": Vector3(sx, shoulder_y, 0),
		"lower_arm_l": Vector3(sx + 9.0 * limb_len, shoulder_y, 0),
		"hand_l": Vector3(sx + 17.0 * limb_len, shoulder_y, 0),
		"shoulder_r": Vector3(-sx * 0.45, shoulder_y, 0),
		"upper_arm_r": Vector3(-sx, shoulder_y, 0),
		"lower_arm_r": Vector3(-(sx + 9.0 * limb_len), shoulder_y, 0),
		"hand_r": Vector3(-(sx + 17.0 * limb_len), shoulder_y, 0),
		"upper_leg_l": Vector3(sx * 0.42, hips_y, 0),
		"lower_leg_l": Vector3(sx * 0.42, knee_y, 0),
		"foot_l": Vector3(sx * 0.42, foot_y, 0),
		"upper_leg_r": Vector3(-sx * 0.42, hips_y, 0),
		"lower_leg_r": Vector3(-sx * 0.42, knee_y, 0),
		"foot_r": Vector3(-sx * 0.42, foot_y, 0),
		"head_scale": head_scale,
		"torso_len": torso_len,
		"limb_len": limb_len,
		"shoulder_width": shoulder_width,
	}


const BONE_TREE := {
	"root": "",
	"hips": "root",
	"spine": "hips",
	"chest": "spine",
	"neck": "chest",
	"head": "neck",
	"shoulder_l": "chest",
	"upper_arm_l": "shoulder_l",
	"lower_arm_l": "upper_arm_l",
	"hand_l": "lower_arm_l",
	"shoulder_r": "chest",
	"upper_arm_r": "shoulder_r",
	"lower_arm_r": "upper_arm_r",
	"hand_r": "lower_arm_r",
	"upper_leg_l": "hips",
	"lower_leg_l": "upper_leg_l",
	"foot_l": "lower_leg_l",
	"upper_leg_r": "hips",
	"lower_leg_r": "upper_leg_r",
	"foot_r": "lower_leg_r",
}


func _build_skeleton() -> void:
	var layout := _bone_layout()
	skeleton = Skeleton3D.new()
	skeleton.name = "Skeleton3D"
	add_child(skeleton)
	hips_rest_y = (layout["hips"] as Vector3).y
	for bone_name in BONE_TREE.keys():
		skeleton.add_bone(bone_name)
	for bone_name in BONE_TREE.keys():
		var parent_name: String = BONE_TREE[bone_name]
		var idx := skeleton.find_bone(bone_name)
		var abs_pos: Vector3 = layout[bone_name]
		var rel := abs_pos
		if parent_name != "":
			skeleton.set_bone_parent(idx, skeleton.find_bone(parent_name))
			rel = abs_pos - (layout[parent_name] as Vector3)
		skeleton.set_bone_rest(idx, Transform3D(Basis.IDENTITY, rel))
	skeleton.reset_bone_poses()
	# PLAN 1.1: parameterise the head via set_bone_pose_scale on the leaf bone.
	# The head attachment inherits the scale; no child bone needs inverse
	# compensation (leaf), so no shear can occur.
	var head_idx := skeleton.find_bone("head")
	var hs: float = float(params.get("head_scale", 1.0))
	if head_idx >= 0 and not is_equal_approx(hs, 1.0):
		skeleton.set_bone_pose_scale(head_idx, Vector3(hs, hs, hs))


func _mat_shaded(key: String) -> StandardMaterial3D:
	if not shaded_mats.has(key):
		var m := StandardMaterial3D.new()
		if character == "agent":
			var agent_colors := {
				"skin": Color(0.86, 0.68, 0.54),
				"hair": Color(0.78, 0.80, 0.88),
				"eye": Color(0.45, 0.29, 0.62),
				"torso": Color(0.16, 0.19, 0.28),
				"sleeve": Color(0.22, 0.25, 0.36),
				"shorts": Color(0.12, 0.14, 0.21),
				"boot": Color(0.10, 0.11, 0.16),
				"weapon": Color(0.72, 0.76, 0.86),
				"shield": Color(0.44, 0.30, 0.18),
				"arm_l": Color(0.86, 0.68, 0.54),
				"arm_r": Color(0.86, 0.68, 0.54),
				"leg_l": Color(0.86, 0.68, 0.54),
				"leg_r": Color(0.86, 0.68, 0.54),
				"head": Color(0.86, 0.68, 0.54),
			}
			m.albedo_color = agent_colors.get(key, Color(0.5, 0.5, 0.5))
		else:
			m.albedo_color = SHADED_COLORS.get(key, SHADED_COLORS.get("torso", Color(0.5, 0.5, 0.5)))
		m.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
		m.specular_mode = BaseMaterial3D.SPECULAR_TOON
		m.roughness = 0.9
		shaded_mats[key] = m
	return shaded_mats[key]


func _mat_clay() -> StandardMaterial3D:
	# Neutral clay pass: one light material for every body part, so the edit
	# model can read a tumbling silhouette instead of a pile of near-black
	# outfit boxes.  Colours always come from the reference panel.
	if clay_mat == null:
		clay_mat = StandardMaterial3D.new()
		clay_mat.albedo_color = Color(0.80, 0.80, 0.82)
		clay_mat.diffuse_mode = BaseMaterial3D.DIFFUSE_TOON
		clay_mat.specular_mode = BaseMaterial3D.SPECULAR_TOON
		clay_mat.roughness = 0.85
	return clay_mat


func _mat_part(part: String) -> StandardMaterial3D:
	if not part_mats.has(part):
		var m := StandardMaterial3D.new()
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.albedo_color = PART_COLORS[part]
		m.disable_receive_shadows = true
		part_mats[part] = m
	return part_mats[part]


func _mat_bone(bone_key: String) -> StandardMaterial3D:
	if not bone_mats.has(bone_key):
		var m := StandardMaterial3D.new()
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.albedo_color = BONE_COLORS[bone_key]
		m.disable_receive_shadows = true
		bone_mats[bone_key] = m
	return bone_mats[bone_key]


func _attachment(bone_key: String, source_bone: String = "") -> BoneAttachment3D:
	if attachments.has(bone_key):
		return attachments[bone_key]
	var att := BoneAttachment3D.new()
	att.name = "att_" + bone_key
	skeleton.add_child(att)
	var bone_name := source_bone if source_bone != "" else bone_key
	att.bone_idx = skeleton.find_bone(bone_name)
	attachments[bone_key] = att
	return att


func _add_box(parent: Node3D, size: Vector3, pos: Vector3, part: String, bone_key: String, rot: Vector3 = Vector3.ZERO, shade_key: String = "") -> MeshInstance3D:
	var mesh := BoxMesh.new()
	mesh.size = size
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.position = pos
	mi.rotation_degrees = rot
	parent.add_child(mi)
	meshes.append(mi)
	mesh_keys.append(bone_key)
	mi.set_meta("part", part)
	mi.set_meta("bone_key", bone_key)
	mi.set_meta("shade_key", shade_key if shade_key != "" else part)
	return mi


func _build_parts() -> void:
	var layout := _bone_layout()
	var tl: float = float(params.get("torso_len", 1.0))
	var limb: float = float(params.get("limb_len", 1.0))
	var sw: float = float(params.get("shoulder_width", 1.0))
	var is_agent := character == "agent"

	# --- torso / pelvis -----------------------------------------------------
	var chest_att := _attachment("chest")
	if is_agent:
		# Narrow waist, fitted top, subtle hips: enough silhouette for the
		# image model to read a female agent instead of the knight.
		_add_box(chest_att, Vector3(11.0 * sw, 14.0 * tl, 7.2), Vector3(0, -4.0 * tl, 0), "torso", "chest", Vector3.ZERO, "torso")
		_add_box(chest_att, Vector3(9.0 * sw, 5.2 * tl, 6.8), Vector3(0, -12.2 * tl, 0), "torso", "chest", Vector3.ZERO, "torso")
		_add_box(chest_att, Vector3(8.0 * sw, 3.0, 2.0), Vector3(0, -2.0 * tl, 3.5), "torso", "chest", Vector3.ZERO, "torso")
	else:
		_add_box(chest_att, Vector3(13.0 * sw, 15.0 * tl, 8.0), Vector3(0, -4.0 * tl, 0), "torso", "chest")
	var hips_att := _attachment("hips")
	if is_agent:
		_add_box(hips_att, Vector3(12.8 * sw, 6.4, 8.8), Vector3(0, -1.0, 0), "torso", "hips", Vector3.ZERO, "shorts")
		_add_box(hips_att, Vector3(13.6 * sw, 1.8, 9.2), Vector3(0, 1.4, 0), "torso", "hips", Vector3.ZERO, "boot")
	else:
		_add_box(hips_att, Vector3(12.0 * sw, 6.0, 8.5), Vector3(0, -1.0, 0), "torso", "hips")
		_add_box(hips_att, Vector3(13.4 * sw, 2.0, 9.0), Vector3(0, 1.5, 0), "torso", "hips")  # belt
	# neck column closes the gap between the cuirass and the head
	_add_box(chest_att, Vector3(4.2, 4.6 * tl, 4.2), Vector3(0, 4.0 * tl, 0), "torso", "chest",
		Vector3.ZERO, "skin" if is_agent else "")

	# --- head / hair / helmet ----------------------------------------------
	var head_att := _attachment("head")
	var head_mesh := SphereMesh.new()
	if is_agent:
		head_mesh.radius = 5.0
		head_mesh.height = 10.4
	else:
		head_mesh.radius = 5.4
		head_mesh.height = 11.0
	var head_mi := MeshInstance3D.new()
	head_mi.mesh = head_mesh
	head_mi.position = Vector3(0, 4.2, 0)
	head_mi.scale = Vector3(1.0, 1.05, 0.98)
	head_att.add_child(head_mi)
	meshes.append(head_mi)
	mesh_keys.append("head")
	head_mi.set_meta("part", "head")
	head_mi.set_meta("bone_key", "head")
	head_mi.set_meta("shade_key", "skin" if is_agent else "head")
	if is_agent:
		# face plane + violet eye pixels + silver hair mass.
		_add_box(head_att, Vector3(6.2, 4.6, 1.1), Vector3(0, 3.4, 4.2), "head", "head", Vector3.ZERO, "skin")
		_add_box(head_att, Vector3(1.6, 1.1, 0.7), Vector3(-1.7, 4.6, 4.9), "head", "head", Vector3.ZERO, "eye")
		_add_box(head_att, Vector3(1.6, 1.1, 0.7), Vector3(1.7, 4.6, 4.9), "head", "head", Vector3.ZERO, "eye")
		_add_box(head_att, Vector3(11.2, 5.8, 6.2), Vector3(0, 7.2, -1.4), "head", "head", Vector3.ZERO, "hair")
		_add_box(head_att, Vector3(8.2, 21.0, 4.2), Vector3(1.8, -2.8, -4.2), "head", "head", Vector3.ZERO, "hair")
		_add_box(head_att, Vector3(3.6, 13.0, 3.0), Vector3(6.0, -0.8, -2.4), "head", "head", Vector3(0, 0, 8), "hair")
		_add_box(head_att, Vector3(3.0, 10.0, 3.0), Vector3(-3.4, -0.2, -2.4), "head", "head", Vector3(0, 0, -8), "hair")
	else:
		# helmet crest for a readable silhouette
		_add_box(head_att, Vector3(2.2, 4.2, 7.4), Vector3(0, 9.8, -0.6), "head", "head", Vector3(-14, 0, 0))
		_add_box(head_att, Vector3(1.0, 2.6, 1.2), Vector3(0, 11.2, 2.6), "head", "head", Vector3(24, 0, 0))
		# visor / face plate: protrudes past the head sphere so the generative model
		# can tell the front of the character from the back
		_add_box(head_att, Vector3(6.4, 1.5, 2.6), Vector3(0, 3.9, 4.4), "head", "head")
		_add_box(head_att, Vector3(3.4, 2.2, 1.8), Vector3(0, 1.9, 4.5), "head", "head")

	# --- arms ---------------------------------------------------------------
	var arm_w := 4.4
	var fore_w := 3.9
	var hand_w := 4.2
	var sleeve_w := 4.9
	var fore_sleeve_w := 4.4
	if is_agent:
		# Slimmer blocky limbs: the run pose must not read as a muscle-bound
		# variant of the idle reference.
		arm_w = 3.6
		fore_w = 3.2
		hand_w = 3.5
		sleeve_w = 4.0
		fore_sleeve_w = 3.6
	for side in ["l", "r"]:
		var sign := 1.0 if side == "l" else -1.0
		var upper := _attachment("upper_arm_" + side)
		_add_box(upper, Vector3(9.4 * limb, arm_w * sw, 4.8), Vector3(sign * 4.3 * limb, 0, 0), "arm_" + side, "upper_arm_" + side,
			Vector3.ZERO, "skin" if is_agent else "")
		if is_agent:
			# short sleeve at the shoulder
			_add_box(upper, Vector3(4.8 * limb, sleeve_w * sw, 5.2), Vector3(sign * 1.6 * limb, 0, 0), "arm_" + side, "upper_arm_" + side,
				Vector3.ZERO, "sleeve")
		var lower := _attachment("lower_arm_" + side)
		_add_box(lower, Vector3(8.4 * limb, fore_w * sw, 4.2), Vector3(sign * 3.9 * limb, 0, 0), "arm_" + side, "lower_arm_" + side,
			Vector3.ZERO, "skin" if is_agent else "")
		if is_agent:
			# detached forearm sleeve (套袖)
			_add_box(lower, Vector3(7.8 * limb, fore_sleeve_w * sw, 4.6), Vector3(sign * 3.6 * limb, 0, 0), "arm_" + side, "lower_arm_" + side,
				Vector3.ZERO, "sleeve")
		var hand := _attachment("hand_" + side)
		_add_box(hand, Vector3(3.4 * limb, hand_w, 4.4), Vector3(sign * 1.5 * limb, 0, 0), "arm_" + side, "hand_" + side,
			Vector3.ZERO, "skin" if is_agent else "")

	# --- legs ---------------------------------------------------------------
	var thigh_w := 5.4
	var calf_w := 4.7
	var foot_w := 5.2
	var shorts_w := 6.0
	if is_agent:
		thigh_w = 4.0
		calf_w = 3.4
		foot_w = 4.6
		shorts_w = 4.6
	for side in ["l", "r"]:
		var upper_leg := _attachment("upper_leg_" + side)
		_add_box(upper_leg, Vector3(thigh_w * sw, 12.4 * limb, 5.6), Vector3(0, -6.0 * limb, 0), "leg_" + side, "upper_leg_" + side,
			Vector3.ZERO, "skin" if is_agent else "")
		if is_agent:
			# shorts cover the upper thigh only
			_add_box(upper_leg, Vector3(shorts_w * sw, 6.2, 6.0), Vector3(0, -2.8, 0), "leg_" + side, "upper_leg_" + side,
				Vector3.ZERO, "shorts")
		var lower_leg := _attachment("lower_leg_" + side)
		_add_box(lower_leg, Vector3(calf_w * sw, 11.4 * limb, 5.0), Vector3(0, -5.5 * limb, 0), "leg_" + side, "lower_leg_" + side,
			Vector3.ZERO, "skin" if is_agent else "")
		if is_agent:
			_add_box(lower_leg, Vector3((calf_w + 0.3) * sw, 3.4, 5.4), Vector3(0, -9.2, 0), "leg_" + side, "lower_leg_" + side,
				Vector3.ZERO, "boot")
		var foot := _attachment("foot_" + side)
		_add_box(foot, Vector3(foot_w * sw, 3.0, 8.4), Vector3(0, -1.0, 1.8), "leg_" + side, "foot_" + side,
			Vector3.ZERO, "boot" if is_agent else "")

	# --- weapons ------------------------------------------------------------
	if is_agent:
		_build_agent_weapons(limb, sw)
	else:
		# --- greatsword (right hand) -------------------------------------
		# A plain holder under the hand attachment (not a BoneAttachment3D) so its
		# local orientation can be re-aligned at runtime without being overwritten.
		var weapon := Node3D.new()
		weapon.name = "weapon_holder"
		attachments["weapon"] = weapon
		_attachment("hand_r").add_child(weapon)
		_add_box(weapon, Vector3(1.7, 20.0 * limb, 0.7), Vector3(0, 9.5 * limb, 0), "weapon", "weapon")
		_add_box(weapon, Vector3(7.2, 1.5, 1.8), Vector3(0, -0.6, 0), "weapon", "weapon")
		_add_box(weapon, Vector3(1.6, 4.6, 1.6), Vector3(0, -3.2, 0), "weapon", "weapon")

		# --- shield (left hand) -------------------------------------------
		var shield := Node3D.new()
		shield.name = "shield_holder"
		attachments["shield"] = shield
		_attachment("hand_l").add_child(shield)
		_add_box(shield, Vector3(13.0, 16.0, 1.6), Vector3(0, 3.0, 3.4), "shield", "shield", Vector3(0, 0, 0))
		_add_box(shield, Vector3(4.0, 4.0, 2.2), Vector3(0, 3.0, 4.6), "shield", "shield")


func _build_agent_weapons(limb: float, sw: float) -> void:
	# Active katana: thin blade + guard + grip, held in the right hand.
	var weapon := Node3D.new()
	weapon.name = "weapon_holder"
	attachments["weapon"] = weapon
	_attachment("hand_r").add_child(weapon)
	_add_box(weapon, Vector3(1.2, 19.0 * limb, 0.55), Vector3(0, 9.0 * limb, 0), "katana", "weapon", Vector3.ZERO, "weapon")
	_add_box(weapon, Vector3(4.8, 1.0, 1.2), Vector3(0, -0.4, 0), "katana", "weapon", Vector3.ZERO, "weapon")
	_add_box(weapon, Vector3(1.5, 4.2, 1.4), Vector3(0, -2.7, 0), "katana", "weapon", Vector3.ZERO, "scabbard")

	# Sheathed katana: diagonal across the back, hilt above the right shoulder.
	var kback := Node3D.new()
	kback.name = "katana_back_holder"
	_attachment("katana_back", "chest").add_child(kback)
	kback.position = Vector3(-4.0, -1.0, 0.0)
	kback.rotation_degrees = Vector3(0, 0, 35)
	# The scabbard stays on the back even when the katana is drawn.  The hilt
	# and blade are a separate child so set_gear() can hide them, leaving an
	# empty straight scabbard (no duplicate hilt sticking over the shoulder).
	_add_box(kback, Vector3(1.2, 23.0, 1.2), Vector3(0, -0.5, 0), "scabbard", "katana_back", Vector3.ZERO, "scabbard")
	var hilt := Node3D.new()
	hilt.name = "hilt"
	kback.add_child(hilt)
	# The blade must sit fully INSIDE the scabbard shell: an offset blade pokes
	# through the side and the edit model then paints a second silver rod next
	# to the scabbard (the "duplicate stowed katana" defect).  Only the hilt
	# box and the tsuba should be visible above the scabbard.
	_add_box(hilt, Vector3(0.5, 21.0, 0.5), Vector3(0, -0.8, 0), "katana", "katana_back", Vector3.ZERO, "weapon")
	_add_box(hilt, Vector3(1.0, 4.8, 1.0), Vector3(0, 14.5, 0), "katana", "katana_back", Vector3.ZERO, "weapon")
	_add_box(hilt, Vector3(3.6, 1.0, 1.2), Vector3(0, 12.1, 0), "katana", "katana_back", Vector3.ZERO, "weapon")
	# Empty mouth of the scabbard, shown only while the katana is drawn: a
	# plain closed box reads as a sheathed sword and the edit model adds a
	# second hilt to it.  A dark opening reads as an empty sheath.
	var mouth := Node3D.new()
	mouth.name = "scabbard_mouth"
	kback.add_child(mouth)
	_add_box(mouth, Vector3(0.9, 1.1, 0.9), Vector3(0, 11.2, 0), "scabbard", "katana_back", Vector3.ZERO, "boot")
	mouth.visible = false

	# Active pistol: barrel follows the hand's -X (arm) axis.
	var pistol := Node3D.new()
	pistol.name = "pistol_holder"
	_attachment("pistol", "hand_r").add_child(pistol)
	_add_box(pistol, Vector3(6.0, 2.2, 1.8), Vector3(-3.0, 0.2, 0), "pistol", "pistol", Vector3.ZERO, "weapon")
	_add_box(pistol, Vector3(1.8, 4.2, 2.0), Vector3(0.4, -2.2, 0), "pistol", "pistol", Vector3.ZERO, "scabbard")
	_add_box(pistol, Vector3(1.2, 1.0, 1.0), Vector3(-5.8, 0.7, 0), "pistol", "pistol", Vector3.ZERO, "weapon")

	# Empty holster on the right hip (near camera).  The holster itself is
	# always visible: when the pistol is drawn the hip must keep the same
	# silhouette instead of losing the whole gear block from frame to frame.
	var holster := Node3D.new()
	holster.name = "holster_holder"
	_attachment("holster", "hips").add_child(holster)
	holster.position = Vector3(-7.2, -4.6, 2.2)
	holster.rotation_degrees = Vector3(0, 0, -12)
	_add_box(holster, Vector3(4.4, 10.0, 2.8), Vector3(-0.6, -3.4, 0.4), "holster", "holster", Vector3.ZERO, "scabbard")
	# A light metal clip on the outer face keeps the empty holster readable
	# against the dark shorts when the pistol is in hand.
	_add_box(holster, Vector3(1.4, 1.6, 1.0), Vector3(0, 0.9, 1.5), "holster", "holster", Vector3.ZERO, "weapon")

	# The pistol that sits in that holster; hidden while the pistol is in hand.
	var phip := Node3D.new()
	phip.name = "pistol_hip_holder"
	_attachment("pistol_hip", "hips").add_child(phip)
	phip.position = Vector3(-7.2, -4.6, 2.2)
	phip.rotation_degrees = Vector3(0, 0, -12)
	_add_box(phip, Vector3(1.8, 3.4, 1.9), Vector3(0, 1.9, 0), "pistol", "pistol_hip", Vector3.ZERO, "scabbard")
	# Slide/barrel sticking forward out of the holster: without it the stowed
	# pistol reads as a featureless pouch.
	_add_box(phip, Vector3(2.8, 1.1, 2.0), Vector3(0, 3.2, 1.1), "pistol", "pistol_hip", Vector3.ZERO, "weapon")
	_add_box(phip, Vector3(1.6, 1.0, 1.4), Vector3(0, 3.9, 0), "pistol", "pistol_hip", Vector3.ZERO, "weapon")

	# Keep the shield key present (empty) so shared truth/audit code can ask
	# for it without branching on the character.
	var shield := Node3D.new()
	shield.name = "shield_holder"
	attachments["shield"] = shield
	_attachment("hand_l").add_child(shield)


func set_gear(mode: Dictionary) -> void:
	gear_mode = mode.duplicate()
	for key in ["weapon", "katana_back", "pistol", "pistol_hip", "shield"]:
		if attachments.has(key):
			attachments[key].visible = false
	if character == "knight":
		if attachments.has("weapon"):
			attachments["weapon"].visible = true
		if attachments.has("shield"):
			attachments["shield"].visible = true
		return
	var katana := String(mode.get("katana", "back"))
	var pistol_mode := String(mode.get("pistol", "hip"))
	if katana == "hand" and attachments.has("weapon"):
		attachments["weapon"].visible = true
		if attachments.has("katana_back"):
			attachments["katana_back"].visible = true
			var h = attachments["katana_back"].get_node_or_null("hilt")
			if h:
				h.visible = false
			var mouth_open = attachments["katana_back"].get_node_or_null("scabbard_mouth")
			if mouth_open:
				mouth_open.visible = true
	elif katana == "back" and attachments.has("katana_back"):
		attachments["katana_back"].visible = true
		var h2 = attachments["katana_back"].get_node_or_null("hilt")
		if h2:
			h2.visible = true
		var mouth_shut = attachments["katana_back"].get_node_or_null("scabbard_mouth")
		if mouth_shut:
			mouth_shut.visible = false
	if pistol_mode == "hand" and attachments.has("pistol"):
		attachments["pistol"].visible = true
	elif pistol_mode == "hip" and attachments.has("pistol_hip"):
		attachments["pistol_hip"].visible = true


func set_simple(on: bool) -> void:
	for mi in meshes:
		var shade: String = mi.get_meta("shade_key", "")
		if shade == "hair":
			mi.visible = not on


func set_pass(pass_name: String) -> void:
	for mi in meshes:
		var part: String = mi.get_meta("part")
		var bone_key: String = mi.get_meta("bone_key")
		if pass_name == "shaded":
			var shade_key: String = mi.get_meta("shade_key", part)
			mi.material_override = _mat_shaded(shade_key)
		elif pass_name == "clay":
			mi.material_override = _mat_clay()
		elif pass_name == "part_id":
			mi.material_override = _mat_part(part)
		else:
			mi.material_override = _mat_bone(bone_key)


# ---------------------------------------------------------------------------
# Animation construction
# ---------------------------------------------------------------------------
func _mirror(v: float, side: String) -> float:
	return v if side == "l" else -v


func _build_animations() -> void:
	anim_player = AnimationPlayer.new()
	anim_player.name = "AnimationPlayer"
	add_child(anim_player)
	var lib := AnimationLibrary.new()
	lib.add_animation("idle", _anim_idle())
	lib.add_animation("sword_block", _anim_sword_block())
	lib.add_animation("run", _anim_run())
	lib.add_animation("attack_combo", _anim_attack())
	lib.add_animation("roll_tuck", _anim_roll_tuck())
	anim_player.add_animation_library("actions", lib)
	anim_player.play("actions/idle")
	anim_player.pause()


func _new_anim() -> Animation:
	var a := Animation.new()
	a.length = 1.0
	a.loop_mode = Animation.LOOP_LINEAR
	return a


func _rot_track(a: Animation, bone: String, keys: Array) -> void:
	var t := a.add_track(Animation.TYPE_ROTATION_3D)
	a.track_set_path(t, "Skeleton3D:" + bone)
	a.track_set_interpolation_type(t, Animation.INTERPOLATION_LINEAR)
	var n := keys.size()
	for i in n:
		var e: Vector3 = keys[i]
		var time := float(i) / float(n - 1)
		var q := Quaternion.from_euler(Vector3(deg_to_rad(e.x), deg_to_rad(e.y), deg_to_rad(e.z)))
		# Rest pose is a T-pose (needed for KayKit retargeting); procedural clips
		# are authored with "arms hanging down", so offset the upper arm here.
		if bone == "upper_arm_l":
			q = q * Quaternion(Vector3(0, 0, 1), deg_to_rad(-90))
		elif bone == "upper_arm_r":
			q = q * Quaternion(Vector3(0, 0, 1), deg_to_rad(90))
		a.rotation_track_insert_key(t, time, q)


func _pos_track(a: Animation, bone: String, keys: Array) -> void:
	# Pose positions are ABSOLUTE in bone space, so the rest translation has to
	# be re-added; otherwise the whole chain collapses onto its parent origin.
	var rest := skeleton.get_bone_rest(skeleton.find_bone(bone)).origin
	var t := a.add_track(Animation.TYPE_POSITION_3D)
	a.track_set_path(t, "Skeleton3D:" + bone)
	a.track_set_interpolation_type(t, Animation.INTERPOLATION_LINEAR)
	var n := keys.size()
	for i in n:
		a.position_track_insert_key(t, float(i) / float(n - 1), rest + keys[i])


func _anim_idle() -> Animation:
	var a := _new_anim()
	var breath := [0, -1.2, -2.2, -1.4, 0, 1.0, 2.0, 1.2, 0]
	var head := [0, 1.0, 1.8, 1.2, 0, -0.8, -1.6, -1.0, 0]
	_rot_track(a, "chest", breath.map(func(v): return Vector3(v, 0, 0)))
	_rot_track(a, "head", head.map(func(v): return Vector3(v, 0, 0)))
	_rot_track(a, "upper_arm_l", [Vector3(0, 0, 3), Vector3(1, 0, 4), Vector3(2, 0, 5), Vector3(1, 0, 4), Vector3(0, 0, 3), Vector3(-1, 0, 2), Vector3(-2, 0, 1), Vector3(-1, 0, 2), Vector3(0, 0, 3)])
	_rot_track(a, "upper_arm_r", [Vector3(0, 0, -3), Vector3(1, 0, -4), Vector3(2, 0, -5), Vector3(1, 0, -4), Vector3(0, 0, -3), Vector3(-1, 0, -2), Vector3(-2, 0, -1), Vector3(-1, 0, -2), Vector3(0, 0, -3)])
	_pos_track(a, "hips", [Vector3(0, 0, 0), Vector3(0, -0.12, 0), Vector3(0, -0.2, 0), Vector3(0, -0.12, 0), Vector3(0, 0, 0), Vector3(0, 0.1, 0), Vector3(0, 0.16, 0), Vector3(0, 0.1, 0), Vector3(0, 0, 0)])
	return a


func _anim_sword_block() -> Animation:
	var a := _new_anim()
	# right arm brings the greatsword up across the chest
	_rot_track(a, "upper_arm_r", [
		Vector3(0, 0, -4), Vector3(-38, 0, -16), Vector3(-66, 0, -24), Vector3(-80, 0, -26),
		Vector3(-82, 0, -26), Vector3(-80, 0, -24), Vector3(-76, 0, -22), Vector3(-70, 0, -18), Vector3(-62, 0, -14),
	])
	_rot_track(a, "lower_arm_r", [
		Vector3(0, 0, 0), Vector3(-25, 8, 8), Vector3(-48, 16, 16), Vector3(-58, 20, 20),
		Vector3(-60, 20, 20), Vector3(-56, 18, 18), Vector3(-52, 15, 14), Vector3(-46, 12, 10), Vector3(-38, 8, 6),
	])
	_rot_track(a, "upper_arm_l", [
		Vector3(-12, 0, 8), Vector3(-24, 0, 14), Vector3(-32, 0, 18), Vector3(-34, 0, 20),
		Vector3(-34, 0, 20), Vector3(-33, 0, 19), Vector3(-31, 0, 18), Vector3(-29, 0, 17), Vector3(-26, 0, 15),
	])
	_rot_track(a, "lower_arm_l", [
		Vector3(-28, 0, 0), Vector3(-38, 0, 2), Vector3(-46, 0, 4), Vector3(-50, 0, 4),
		Vector3(-50, 0, 4), Vector3(-49, 0, 4), Vector3(-47, 0, 3), Vector3(-45, 0, 3), Vector3(-42, 0, 2),
	])
	_rot_track(a, "chest", [Vector3(0, 0, 0), Vector3(-2, -3, 0), Vector3(-4, -5, 0), Vector3(-4, -6, 0), Vector3(-4, -6, 0), Vector3(-3, -5, 0), Vector3(-3, -4, 0), Vector3(-2, -3, 0), Vector3(-1, -2, 0)])
	_rot_track(a, "head", [Vector3(0, 0, 0), Vector3(1, 2, 0), Vector3(2, 4, 0), Vector3(2, 4, 0), Vector3(2, 4, 0), Vector3(2, 3, 0), Vector3(1, 3, 0), Vector3(1, 2, 0), Vector3(0, 1, 0)])
	_rot_track(a, "upper_leg_l", [Vector3(0, 0, 0), Vector3(-4, 0, 2), Vector3(-7, 0, 3), Vector3(-8, 0, 3), Vector3(-8, 0, 3), Vector3(-8, 0, 3), Vector3(-7, 0, 3), Vector3(-6, 0, 2), Vector3(-5, 0, 2)])
	_rot_track(a, "upper_leg_r", [Vector3(0, 0, 0), Vector3(5, 0, -2), Vector3(9, 0, -3), Vector3(10, 0, -3), Vector3(10, 0, -3), Vector3(10, 0, -3), Vector3(9, 0, -3), Vector3(8, 0, -2), Vector3(7, 0, -2)])
	_rot_track(a, "lower_leg_l", [Vector3(0, 0, 0), Vector3(4, 0, 0), Vector3(7, 0, 0), Vector3(8, 0, 0), Vector3(8, 0, 0), Vector3(8, 0, 0), Vector3(7, 0, 0), Vector3(6, 0, 0), Vector3(5, 0, 0)])
	_pos_track(a, "hips", [Vector3(0, 0, 0), Vector3(0, -0.8, -0.4), Vector3(0, -1.4, -0.7), Vector3(0, -1.5, -0.8), Vector3(0, -1.5, -0.8), Vector3(0, -1.4, -0.8), Vector3(0, -1.3, -0.7), Vector3(0, -1.2, -0.6), Vector3(0, -1.0, -0.5)])
	return a


func _anim_run() -> Animation:
	var a := _new_anim()
	var leg_l := [-38, -12, 12, 34, 20, -2, -24, -40, -38]
	var leg_r := [34, 12, -12, -38, -40, -24, -2, 20, 34]
	var knee_l := [5, 26, 12, 4, 34, 52, 30, 8, 5]
	var knee_r := [4, 34, 52, 30, 8, 5, 26, 12, 4]
	var arm_l := [26, 12, -8, -26, -18, -2, 16, 28, 26]
	var arm_r := [-26, -12, 8, 26, 18, 2, -16, -28, -26]
	_rot_track(a, "upper_leg_l", leg_l.map(func(v): return Vector3(v, 0, 1.5)))
	_rot_track(a, "upper_leg_r", leg_r.map(func(v): return Vector3(v, 0, -1.5)))
	_rot_track(a, "lower_leg_l", knee_l.map(func(v): return Vector3(v, 0, 0)))
	_rot_track(a, "lower_leg_r", knee_r.map(func(v): return Vector3(v, 0, 0)))
	_rot_track(a, "upper_arm_l", arm_l.map(func(v): return Vector3(v, 0, 6)))
	_rot_track(a, "upper_arm_r", arm_r.map(func(v): return Vector3(v, 0, -6)))
	_rot_track(a, "lower_arm_l", [Vector3(-20, 0, 0), Vector3(-26, 0, 0), Vector3(-32, 0, 0), Vector3(-40, 0, 0), Vector3(-38, 0, 0), Vector3(-32, 0, 0), Vector3(-26, 0, 0), Vector3(-20, 0, 0), Vector3(-20, 0, 0)])
	_rot_track(a, "lower_arm_r", [Vector3(-40, 0, 0), Vector3(-38, 0, 0), Vector3(-32, 0, 0), Vector3(-26, 0, 0), Vector3(-20, 0, 0), Vector3(-20, 0, 0), Vector3(-26, 0, 0), Vector3(-32, 0, 0), Vector3(-40, 0, 0)])
	_rot_track(a, "chest", [Vector3(8, -4, 0), Vector3(9, -2, 0), Vector3(8, 2, 0), Vector3(8, 4, 0), Vector3(8, 2, 0), Vector3(9, -2, 0), Vector3(8, -4, 0), Vector3(8, -3, 0), Vector3(8, -4, 0)])
	_rot_track(a, "head", [Vector3(-6, 3, 0), Vector3(-6, 1, 0), Vector3(-6, -2, 0), Vector3(-6, -3, 0), Vector3(-6, -1, 0), Vector3(-6, 2, 0), Vector3(-6, 3, 0), Vector3(-6, 2, 0), Vector3(-6, 3, 0)])
	_pos_track(a, "hips", [Vector3(0, 1.6, 0), Vector3(0, 0.6, 0), Vector3(0, 1.8, 0), Vector3(0, 0.5, 0), Vector3(0, 1.6, 0), Vector3(0, 0.6, 0), Vector3(0, 1.8, 0), Vector3(0, 0.5, 0), Vector3(0, 1.6, 0)])
	return a


func _anim_attack() -> Animation:
	var a := _new_anim()
	# 0 guard -> 1 windup -> 2-3 horizontal slash -> 4 recover -> 5 raise -> 6 chop -> 7 settle
	_rot_track(a, "chest", [Vector3(0, 0, 0), Vector3(-4, -30, 0), Vector3(0, 10, 0), Vector3(4, 34, 0), Vector3(2, 12, 0), Vector3(-6, -6, 0), Vector3(6, -2, 0), Vector3(2, 0, 0), Vector3(0, 0, 0)])
	_rot_track(a, "head", [Vector3(0, 0, 0), Vector3(0, -12, 0), Vector3(0, 6, 0), Vector3(0, 14, 0), Vector3(0, 6, 0), Vector3(-2, -2, 0), Vector3(4, 0, 0), Vector3(2, 0, 0), Vector3(0, 0, 0)])
	_rot_track(a, "upper_arm_r", [Vector3(0, 0, -4), Vector3(44, 0, -38), Vector3(-40, 0, -10), Vector3(-96, 0, 22), Vector3(-70, 0, 12), Vector3(-150, 0, 10), Vector3(-30, 0, 0), Vector3(-10, 0, -2), Vector3(0, 0, -4)])
	_rot_track(a, "lower_arm_r", [Vector3(0, 0, 0), Vector3(-70, 0, 0), Vector3(-20, 0, 0), Vector3(-6, 0, 0), Vector3(-24, 0, 0), Vector3(-40, 0, 0), Vector3(-8, 0, 0), Vector3(-4, 0, 0), Vector3(0, 0, 0)])
	_rot_track(a, "upper_arm_l", [Vector3(-14, 0, 10), Vector3(-30, 0, 20), Vector3(-20, 0, 14), Vector3(-10, 0, 8), Vector3(-16, 0, 10), Vector3(-28, 0, 18), Vector3(-24, 0, 16), Vector3(-18, 0, 12), Vector3(-14, 0, 10)])
	_rot_track(a, "lower_arm_l", [Vector3(-30, 0, 0), Vector3(-50, 0, 0), Vector3(-44, 0, 0), Vector3(-34, 0, 0), Vector3(-38, 0, 0), Vector3(-52, 0, 0), Vector3(-46, 0, 0), Vector3(-38, 0, 0), Vector3(-30, 0, 0)])
	_rot_track(a, "upper_leg_l", [Vector3(0, 0, 2), Vector3(-14, 0, 4), Vector3(-18, 0, 5), Vector3(-10, 0, 4), Vector3(-6, 0, 3), Vector3(-8, 0, 3), Vector3(-12, 0, 4), Vector3(-8, 0, 3), Vector3(0, 0, 2)])
	_rot_track(a, "upper_leg_r", [Vector3(0, 0, -2), Vector3(12, 0, -5), Vector3(16, 0, -6), Vector3(10, 0, -5), Vector3(6, 0, -4), Vector3(8, 0, -4), Vector3(12, 0, -5), Vector3(8, 0, -4), Vector3(0, 0, -2)])
	_rot_track(a, "lower_leg_l", [Vector3(0, 0, 0), Vector3(10, 0, 0), Vector3(16, 0, 0), Vector3(12, 0, 0), Vector3(8, 0, 0), Vector3(10, 0, 0), Vector3(14, 0, 0), Vector3(8, 0, 0), Vector3(0, 0, 0)])
	_rot_track(a, "lower_leg_r", [Vector3(0, 0, 0), Vector3(6, 0, 0), Vector3(8, 0, 0), Vector3(14, 0, 0), Vector3(10, 0, 0), Vector3(8, 0, 0), Vector3(10, 0, 0), Vector3(6, 0, 0), Vector3(0, 0, 0)])
	_pos_track(a, "hips", [Vector3(0, 0, 0), Vector3(0, -0.6, -0.8), Vector3(0, -1.4, 0.6), Vector3(0, -1.6, 1.4), Vector3(0, -1.0, 0.8), Vector3(0, 0.2, -0.4), Vector3(0, -1.8, 1.2), Vector3(0, -0.8, 0.4), Vector3(0, 0, 0)])
	return a


func _anim_roll_tuck() -> Animation:
	# A real forward-roll silhouette: frames 0 and 7 are the standing
	# transition, frames 1-6 hold a tight tuck (chin down, knees to chest,
	# elbows folded).  render_actor.gd adds the 360-degree skeleton pitch.
	var a := _new_anim()
	var stand := [0, 0, 0, 0, 0, 0, 0, 0]
	var chest := [0, 58, 64, 64, 62, 60, 30, 0]
	var spine := [0, 24, 28, 28, 26, 24, 12, 0]
	var head := [0, 40, 44, 44, 42, 40, 16, 0]
	var hip_tilt := [0, 10, 12, 12, 11, 10, 5, 0]
	var upper_arm := [0, -74, -86, -86, -84, -80, -38, 0]
	var elbow := [0, -108, -124, -124, -120, -114, -64, 0]
	var thigh := [0, -112, -124, -124, -120, -114, -60, 0]
	var knee := [0, 128, 142, 142, 138, 132, 88, 0]
	_rot_track(a, "hips", hip_tilt.map(func(v): return Vector3(v, 0, 0)))
	_rot_track(a, "spine", spine.map(func(v): return Vector3(v, 0, 0)))
	_rot_track(a, "chest", chest.map(func(v): return Vector3(v, 0, 0)))
	_rot_track(a, "head", head.map(func(v): return Vector3(v, 0, 0)))
	_rot_track(a, "upper_arm_l", upper_arm.map(func(v): return Vector3(v, 0, 10)))
	_rot_track(a, "upper_arm_r", upper_arm.map(func(v): return Vector3(v, 0, -10)))
	_rot_track(a, "lower_arm_l", elbow.map(func(v): return Vector3(v, 0, 0)))
	_rot_track(a, "lower_arm_r", elbow.map(func(v): return Vector3(v, 0, 0)))
	_rot_track(a, "upper_leg_l", thigh.map(func(v): return Vector3(v, 0, 1.5)))
	_rot_track(a, "upper_leg_r", thigh.map(func(v): return Vector3(v, 0, -1.5)))
	_rot_track(a, "lower_leg_l", knee.map(func(v): return Vector3(v, 0, 0)))
	_rot_track(a, "lower_leg_r", knee.map(func(v): return Vector3(v, 0, 0)))
	_pos_track(a, "hips", [
		Vector3(0, 0, 0), Vector3(0, -7.0, 2.0), Vector3(0, -8.0, 2.5),
		Vector3(0, -8.0, 2.5), Vector3(0, -8.0, 2.5), Vector3(0, -7.5, 2.0),
		Vector3(0, -4.5, 0.6), Vector3(0, 0, 0),
	])
	return a


func stop_animation() -> void:
	anim_player.stop()


func play_action(action: String) -> void:
	if action == "rest":
		return
	var clip := "roll_tuck" if action == "roll" else action
	anim_player.play("actions/" + clip)
	anim_player.pause()


func seek_time(t: float) -> void:
	anim_player.seek(t, true)
