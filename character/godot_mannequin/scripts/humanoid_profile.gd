extends RefCounted
## Godot 4 `SkeletonProfileHumanoid` bridge for the parametric rig.
##
## The PLAN calls for a mannequin bound to the standard humanoid profile so
## generic animation libraries can be retargeted onto it.  We instantiate the
## built-in profile, map its semantic bone names onto the rig's short bone
## names, and validate the mapping at render time.  A copy of the profile is
## written to `res://assets/humanoid_profile.tres` for use with Godot's own
## retargeting tools.

const HUMANOID_TO_RIG := {
	"Root": "root",
	"Hips": "hips",
	"Spine": "spine",
	"Chest": "chest",
	"Neck": "neck",
	"Head": "head",
	"LeftShoulder": "shoulder_l",
	"LeftUpperArm": "upper_arm_l",
	"LeftLowerArm": "lower_arm_l",
	"LeftHand": "hand_l",
	"RightShoulder": "shoulder_r",
	"RightUpperArm": "upper_arm_r",
	"RightLowerArm": "lower_arm_r",
	"RightHand": "hand_r",
	"LeftUpperLeg": "upper_leg_l",
	"LeftLowerLeg": "lower_leg_l",
	"LeftFoot": "foot_l",
	"RightUpperLeg": "upper_leg_r",
	"RightLowerLeg": "lower_leg_r",
	"RightFoot": "foot_r",
}


static func make_profile() -> SkeletonProfileHumanoid:
	return SkeletonProfileHumanoid.new()


static func _normalize(bone_name: String) -> String:
	return bone_name.replace(" ", "").replace("-", "").replace("_", "")


static func validate(skeleton: Skeleton3D) -> Dictionary:
	"""Return {mapped, missing} for the humanoid semantic bones on *skeleton*."""
	var profile := make_profile()
	var mapped := 0
	var missing: Array[String] = []
	for i in profile.bone_size:
		var hname := profile.get_bone_name(i)
		if hname == "":
			continue
		var key := _normalize(hname)
		var rig_name := ""
		for candidate in HUMANOID_TO_RIG.keys():
			if _normalize(candidate) == key:
				rig_name = HUMANOID_TO_RIG[candidate]
				break
		if rig_name == "":
			continue
		if skeleton.find_bone(rig_name) >= 0:
			mapped += 1
		else:
			missing.append(hname)
	return {"mapped": mapped, "missing": missing}


const REFERENCE_BONES := {
	"hips": "hips", "spine": "spine", "chest": "chest", "head": "head",
	"upper_arm_l": "upperarm.l", "lower_arm_l": "lowerarm.l", "hand_l": "hand.l",
	"upper_arm_r": "upperarm.r", "lower_arm_r": "lowerarm.r", "hand_r": "hand.r",
	"upper_leg_l": "upperleg.l", "lower_leg_l": "lowerleg.l", "foot_l": "foot.l",
	"upper_leg_r": "upperleg.r", "lower_leg_r": "lowerleg.r", "foot_r": "foot.r",
}


static func _humanoid_for(rig_bone: String) -> String:
	for humanoid_name in HUMANOID_TO_RIG.keys():
		if HUMANOID_TO_RIG[humanoid_name] == rig_bone:
			return humanoid_name
	return ""


static func make_reference_bone_map() -> BoneMap:
	"""BoneMap for the KayKit reference using the same humanoid profile."""
	var bm := BoneMap.new()
	bm.set_profile(make_profile())
	for rig_bone in REFERENCE_BONES.keys():
		var humanoid_name := _humanoid_for(rig_bone)
		if humanoid_name != "":
			bm.set_skeleton_bone_name(humanoid_name, REFERENCE_BONES[rig_bone])
	return bm


static func make_bone_map() -> BoneMap:
	"""Genuine Godot retargeting resource: profile bone <-> rig bone."""
	var bm := BoneMap.new()
	bm.set_profile(make_profile())
	for humanoid_name in HUMANOID_TO_RIG.keys():
		bm.set_skeleton_bone_name(humanoid_name, HUMANOID_TO_RIG[humanoid_name])
	return bm


static func save_bone_map(path: String = "res://assets/humanoid_bonemap.tres") -> void:
	var bm := make_bone_map()
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path("res://assets"))
	ResourceSaver.save(bm, path)


static func save_profile(path: String = "res://assets/humanoid_profile.tres") -> void:
	var profile := make_profile()
	DirAccess.make_dir_recursive_absolute(path.get_base_dir().replace("res://", ProjectSettings.globalize_path("res://")))
	ResourceSaver.save(profile, path)
