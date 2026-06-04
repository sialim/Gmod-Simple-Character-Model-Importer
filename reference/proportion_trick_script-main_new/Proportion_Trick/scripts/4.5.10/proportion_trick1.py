# Proportion Trick script for Blender 4.5.10
# Aligns the "proportions" armature to an imported skeleton named "gg".

import bpy

SRC_ARMATURE_NAME = "gg"
PROP_ARMATURE_NAME = "proportions"

VALVEBIPED_BONES = [
    "ValveBiped.Bip01_Pelvis",
    "ValveBiped.Bip01_Spine",
    "ValveBiped.Bip01_Spine1",
    "ValveBiped.Bip01_Spine2",
    "ValveBiped.Bip01_Spine4",
    "ValveBiped.Bip01_Neck1",
    "ValveBiped.Bip01_Head1",
    "ValveBiped.Bip01_R_Clavicle",
    "ValveBiped.Bip01_R_UpperArm",
    "ValveBiped.Bip01_R_Forearm",
    "ValveBiped.Bip01_R_Hand",
    "ValveBiped.Bip01_R_Finger0",
    "ValveBiped.Bip01_R_Finger01",
    "ValveBiped.Bip01_R_Finger02",
    "ValveBiped.Bip01_R_Finger1",
    "ValveBiped.Bip01_R_Finger11",
    "ValveBiped.Bip01_R_Finger12",
    "ValveBiped.Bip01_R_Finger2",
    "ValveBiped.Bip01_R_Finger21",
    "ValveBiped.Bip01_R_Finger22",
    "ValveBiped.Bip01_R_Finger3",
    "ValveBiped.Bip01_R_Finger31",
    "ValveBiped.Bip01_R_Finger32",
    "ValveBiped.Bip01_R_Finger4",
    "ValveBiped.Bip01_R_Finger41",
    "ValveBiped.Bip01_R_Finger42",
    "ValveBiped.Bip01_L_Clavicle",
    "ValveBiped.Bip01_L_UpperArm",
    "ValveBiped.Bip01_L_Forearm",
    "ValveBiped.Bip01_L_Hand",
    "ValveBiped.Bip01_L_Finger0",
    "ValveBiped.Bip01_L_Finger01",
    "ValveBiped.Bip01_L_Finger02",
    "ValveBiped.Bip01_L_Finger1",
    "ValveBiped.Bip01_L_Finger11",
    "ValveBiped.Bip01_L_Finger12",
    "ValveBiped.Bip01_L_Finger2",
    "ValveBiped.Bip01_L_Finger21",
    "ValveBiped.Bip01_L_Finger22",
    "ValveBiped.Bip01_L_Finger3",
    "ValveBiped.Bip01_L_Finger31",
    "ValveBiped.Bip01_L_Finger32",
    "ValveBiped.Bip01_L_Finger4",
    "ValveBiped.Bip01_L_Finger41",
    "ValveBiped.Bip01_L_Finger42",
    "ValveBiped.Bip01_R_Thigh",
    "ValveBiped.Bip01_R_Calf",
    "ValveBiped.Bip01_R_Foot",
    "ValveBiped.Bip01_R_Toe0",
    "ValveBiped.Bip01_L_Thigh",
    "ValveBiped.Bip01_L_Calf",
    "ValveBiped.Bip01_L_Foot",
    "ValveBiped.Bip01_L_Toe0",
]

TRACK_PAIRS = [
    ("ValveBiped.Bip01_L_Thigh", "ValveBiped.Bip01_L_Calf"),
    ("ValveBiped.Bip01_L_Calf", "ValveBiped.Bip01_L_Foot"),
    ("ValveBiped.Bip01_R_Thigh", "ValveBiped.Bip01_R_Calf"),
    ("ValveBiped.Bip01_R_Calf", "ValveBiped.Bip01_R_Foot"),
    ("ValveBiped.Bip01_L_UpperArm", "ValveBiped.Bip01_L_Forearm"),
    ("ValveBiped.Bip01_L_Forearm", "ValveBiped.Bip01_L_Hand"),
    ("ValveBiped.Bip01_R_UpperArm", "ValveBiped.Bip01_R_Forearm"),
    ("ValveBiped.Bip01_R_Forearm", "ValveBiped.Bip01_R_Hand"),
    ("ValveBiped.Bip01_L_Finger0", "ValveBiped.Bip01_L_Finger01"),
    ("ValveBiped.Bip01_L_Finger01", "ValveBiped.Bip01_L_Finger02"),
    ("ValveBiped.Bip01_L_Finger1", "ValveBiped.Bip01_L_Finger11"),
    ("ValveBiped.Bip01_L_Finger11", "ValveBiped.Bip01_L_Finger12"),
    ("ValveBiped.Bip01_L_Finger2", "ValveBiped.Bip01_L_Finger21"),
    ("ValveBiped.Bip01_L_Finger21", "ValveBiped.Bip01_L_Finger22"),
    ("ValveBiped.Bip01_L_Finger3", "ValveBiped.Bip01_L_Finger31"),
    ("ValveBiped.Bip01_L_Finger31", "ValveBiped.Bip01_L_Finger32"),
    ("ValveBiped.Bip01_L_Finger4", "ValveBiped.Bip01_L_Finger41"),
    ("ValveBiped.Bip01_L_Finger41", "ValveBiped.Bip01_L_Finger42"),
    ("ValveBiped.Bip01_R_Finger0", "ValveBiped.Bip01_R_Finger01"),
    ("ValveBiped.Bip01_R_Finger01", "ValveBiped.Bip01_R_Finger02"),
    ("ValveBiped.Bip01_R_Finger1", "ValveBiped.Bip01_R_Finger11"),
    ("ValveBiped.Bip01_R_Finger11", "ValveBiped.Bip01_R_Finger12"),
    ("ValveBiped.Bip01_R_Finger2", "ValveBiped.Bip01_R_Finger21"),
    ("ValveBiped.Bip01_R_Finger21", "ValveBiped.Bip01_R_Finger22"),
    ("ValveBiped.Bip01_R_Finger3", "ValveBiped.Bip01_R_Finger31"),
    ("ValveBiped.Bip01_R_Finger31", "ValveBiped.Bip01_R_Finger32"),
    ("ValveBiped.Bip01_R_Finger4", "ValveBiped.Bip01_R_Finger41"),
    ("ValveBiped.Bip01_R_Finger41", "ValveBiped.Bip01_R_Finger42"),
]


def get_armature(name):
    ob = bpy.data.objects.get(name)
    if ob is None:
        raise RuntimeError('Armature "%s" was not found.' % name)
    if ob.type != "ARMATURE":
        raise RuntimeError('Object "%s" must be an ARMATURE, not %s.' % (name, ob.type))
    return ob


def iter_layer_collections(layer_collection):
    yield layer_collection
    for child in layer_collection.children:
        yield from iter_layer_collections(child)


def ensure_collection_visible(collection, view_layer):
    collection.hide_viewport = False
    for layer_collection in iter_layer_collections(view_layer.layer_collection):
        if layer_collection.collection == collection:
            layer_collection.exclude = False
            layer_collection.hide_viewport = False


def unhide_for_viewlayer(ob):
    view_layer = bpy.context.view_layer
    for collection in ob.users_collection:
        ensure_collection_visible(collection, view_layer)
    ob.hide_set(False)
    ob.hide_viewport = False
    bpy.context.view_layer.update()
    if not ob.visible_get():
        raise RuntimeError('Object "%s" is still hidden after visibility repair.' % ob.name)


def set_active_only(ob):
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def ensure_pose_mode(ob):
    unhide_for_viewlayer(ob)
    set_active_only(ob)
    bpy.ops.object.mode_set(mode="POSE")


def remove_pt_constraints(pose_bone):
    for constraint in list(pose_bone.constraints):
        if constraint.name.startswith("PT_"):
            pose_bone.constraints.remove(constraint)


def run():
    src = get_armature(SRC_ARMATURE_NAME)
    prop = get_armature(PROP_ARMATURE_NAME)
    unhide_for_viewlayer(src)
    unhide_for_viewlayer(prop)
    ensure_pose_mode(prop)

    for bone_name in VALVEBIPED_BONES:
        prop_bone = prop.pose.bones.get(bone_name)
        if prop_bone:
            remove_pt_constraints(prop_bone)

    for bone_name in VALVEBIPED_BONES:
        prop_bone = prop.pose.bones.get(bone_name)
        src_bone = src.pose.bones.get(bone_name)
        if prop_bone and src_bone:
            constraint = prop_bone.constraints.new("COPY_LOCATION")
            constraint.name = "PT_CopyLoc"
            constraint.target = src
            constraint.subtarget = bone_name

    for target_name, subtarget_name in TRACK_PAIRS:
        prop_bone = prop.pose.bones.get(target_name)
        if not prop_bone:
            continue
        if not src.pose.bones.get(target_name) or not src.pose.bones.get(subtarget_name):
            continue

        constraint = prop_bone.constraints.new("LOCKED_TRACK")
        constraint.name = "PT_LockedTrack_Z"
        constraint.target = src
        constraint.subtarget = subtarget_name
        constraint.track_axis = "TRACK_X"
        constraint.lock_axis = "LOCK_Z"

        constraint = prop_bone.constraints.new("LOCKED_TRACK")
        constraint.name = "PT_LockedTrack_Y"
        constraint.target = src
        constraint.subtarget = subtarget_name
        constraint.track_axis = "TRACK_X"
        constraint.lock_axis = "LOCK_Y"

    for parent_name in VALVEBIPED_BONES:
        parent = prop.pose.bones.get(parent_name)
        if not parent:
            continue
        for child in parent.children:
            if len(child.constraints) == 0 and parent.parent is not None:
                for constraint in list(parent.constraints):
                    if constraint.name.startswith("PT_") and constraint.name != "PT_CopyLoc":
                        parent.constraints.remove(constraint)
                print("%s is a parent of %s but child has no constraints; cleaned PT locked tracks." % (parent_name, child.name))

    ensure_pose_mode(prop)
    bpy.context.view_layer.update()
    print("Proportion Trick 1 for Blender 4.5.10 done.")


run()
