extends SceneTree

## Weapon-relative orientation diagnostic: how is KayKit's 1H_Sword oriented
## relative to the hand.r bone?  This is the orientation our mannequin's
## weapon holder must inherit (instead of forcing the blade to world-up).

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var packed: PackedScene = load("res://assets/kaykit/Knight.glb")
	var inst := packed.instantiate()
	root.add_child(inst)
	var sk := _find(inst, "Skeleton3D") as Skeleton3D
	print("skeleton xform ", sk.global_transform)
	var hi := sk.find_bone("hand.r")
	var hrest := sk.get_bone_global_rest(hi)
	print("hand.r rest global ", hrest)
	var sword := _find_named(inst, "1H_Sword")
	if sword == null:
		print("no 1H_Sword node")
		quit()
		return
	print("sword node parent ", sword.get_parent().name)
	var s_world: Transform3D = sword.global_transform
	print("sword world ", s_world)
	var s_skel: Transform3D = sk.global_transform.affine_inverse() * s_world
	print("sword skeleton-space ", s_skel)
	var rel: Basis = hrest.basis.orthonormalized().inverse() * s_skel.basis.orthonormalized()
	print("REL basis (hand->sword) x=", rel.x, " y=", rel.y, " z=", rel.z)
	print("REL quat ", rel.get_rotation_quaternion())
	if sword is MeshInstance3D:
		print("sword AABB ", sword.get_aabb())
	var sib := _find_named(inst, "1H_Sword_Offhand")
	if sib != null:
		var sw2: Transform3D = sk.global_transform.affine_inverse() * sib.global_transform
		print("offhand sword skeleton-space ", sw2)
	quit()

func _find(node: Node, cls: String) -> Node:
	if node.is_class(cls):
		return node
	for c in node.get_children():
		var r := _find(c, cls)
		if r != null:
			return r
	return null

func _find_named(node: Node, n: String) -> Node:
	if node.name == n:
		return node
	for c in node.get_children():
		var r := _find_named(c, n)
		if r != null:
			return r
	return null
