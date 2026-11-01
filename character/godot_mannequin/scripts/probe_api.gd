extends SceneTree
func _initialize():
	for cls in ["BoneMap","SkeletonProfileHumanoid","SkeletonProfile"]:
		print("== ", cls)
		for m in ClassDB.class_get_method_list(cls, true):
			if m.name.begins_with("_"): continue
			print("  M ", m.name)
		for p in ClassDB.class_get_property_list(cls, true):
			print("  P ", p.name)
	quit()
