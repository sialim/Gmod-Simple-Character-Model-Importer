# Proportion Trick 2 script for Blender 4.5.10
# Merges non-ValveBiped bones from "gg" into "proportions" and retargets meshes.

import math
import bpy
from mathutils import Matrix

SRC_ARMATURE_NAME = "gg"
PROP_ARMATURE_NAME = "proportions"
HELPER_MESH_NAMES = {"smd_bone_vis"}

TOE_BASIS_SOURCE_BONES = (
    "ValveBiped.Bip01_L_Toe0",
    "ValveBiped.Bip01_R_Toe0",
)

TOE_BASIS_CORRECTION_BONES = (
    "ValveBiped.Bip01_L_Toe0",
    "ValveBiped.Bip01_R_Toe0",
    "ValveBiped.Bip01_L_Foot",
    "ValveBiped.Bip01_R_Foot",
)

VALVEBIPED_BONES = {
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
}


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


def link_object_like(source, new_object):
    if source.users_collection:
        source.users_collection[0].objects.link(new_object)
    else:
        bpy.context.collection.objects.link(new_object)


def remove_edit_bone_if_present(edit_bones, name):
    bone = edit_bones.get(name)
    if bone:
        edit_bones.remove(bone)


def normalize_toe_basis_angle(angle):
    while angle > math.pi / 2.0:
        angle -= math.pi
    while angle < -math.pi / 2.0:
        angle += math.pi
    return angle


def apply_toe_foot_basis_correction(prop):
    unhide_for_viewlayer(prop)
    set_active_only(prop)
    bpy.ops.object.mode_set(mode="EDIT")
    try:
        edit_bones = prop.data.edit_bones
        required = set(TOE_BASIS_SOURCE_BONES) | set(TOE_BASIS_CORRECTION_BONES)
        missing = sorted(name for name in required if name not in edit_bones)
        if missing:
            raise RuntimeError("Toe/foot local basis correction missing bones: %s" % ", ".join(missing))

        angles = []
        for bone_name in TOE_BASIS_SOURCE_BONES:
            bone = edit_bones[bone_name]
            head_world = prop.matrix_world @ bone.head
            tail_world = prop.matrix_world @ bone.tail
            vector = tail_world - head_world
            if abs(vector.y) < 1e-8 and abs(vector.z) < 1e-8:
                raise RuntimeError("Cannot compute toe basis angle for zero-length YZ vector: %s" % bone_name)
            angles.append(normalize_toe_basis_angle(math.atan2(vector.y, vector.z)))

        average_angle = sum(angles) / len(angles)
        if abs(average_angle) > 1e-8:
            rotation = Matrix.Rotation(average_angle, 4, "X")
            inverse_world = prop.matrix_world.inverted()
            for bone_name in TOE_BASIS_CORRECTION_BONES:
                bone = edit_bones[bone_name]
                head_world = prop.matrix_world @ bone.head
                tail_world = prop.matrix_world @ bone.tail
                bone.tail = inverse_world @ (head_world + (rotation @ (tail_world - head_world)))
    finally:
        bpy.ops.object.mode_set(mode="OBJECT")

    print(
        "Toe/foot local basis correction: left %.6f deg, right %.6f deg, applied %.6f deg."
        % (math.degrees(angles[0]), math.degrees(angles[1]), math.degrees(average_angle))
    )


def retarget_mesh_modifiers(prop):
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH" or ob.name in HELPER_MESH_NAMES or ob.name.startswith("VTA vertices"):
            continue
        armature_mod = next((mod for mod in ob.modifiers if mod.type == "ARMATURE"), None)
        if armature_mod is None:
            armature_mod = ob.modifiers.new(name="Armature", type="ARMATURE")
        armature_mod.object = prop


def run():
    src = get_armature(SRC_ARMATURE_NAME)
    prop = get_armature(PROP_ARMATURE_NAME)
    unhide_for_viewlayer(src)
    unhide_for_viewlayer(prop)

    apply_toe_foot_basis_correction(prop)

    source_extra_names = [bone.name for bone in src.data.bones if bone.name not in VALVEBIPED_BONES]
    existing_prop_names = {bone.name for bone in prop.data.bones}
    new_extra_names = [name for name in source_extra_names if name not in existing_prop_names]

    if new_extra_names:
        duplicate = src.copy()
        duplicate.data = src.data.copy()
        duplicate.animation_data_clear()
        duplicate.name = "%s_extra_tmp" % SRC_ARMATURE_NAME
        link_object_like(src, duplicate)
        unhide_for_viewlayer(duplicate)

        set_active_only(duplicate)
        bpy.ops.object.mode_set(mode="EDIT")
        edit_bones = duplicate.data.edit_bones
        for bone_name in list(edit_bones.keys()):
            if bone_name in VALVEBIPED_BONES or bone_name in existing_prop_names:
                remove_edit_bone_if_present(edit_bones, bone_name)
        bpy.ops.object.mode_set(mode="OBJECT")

        if len(duplicate.data.bones) > 0:
            duplicate_name = duplicate.name
            unhide_for_viewlayer(prop)
            unhide_for_viewlayer(duplicate)
            bpy.ops.object.select_all(action="DESELECT")
            prop.select_set(True)
            duplicate.select_set(True)
            bpy.context.view_layer.objects.active = prop
            bpy.context.view_layer.update()
            with bpy.context.temp_override(
                active_object=prop,
                selected_objects=[prop, duplicate],
                selected_editable_objects=[prop, duplicate],
            ):
                result = bpy.ops.object.join()
            if result != {"FINISHED"} or duplicate_name in bpy.data.objects:
                raise RuntimeError("Failed to merge extra bones into proportions.")
        else:
            bpy.data.objects.remove(duplicate, do_unlink=True)

    set_active_only(prop)
    bpy.ops.object.mode_set(mode="EDIT")
    edit_bones = prop.data.edit_bones
    for bone in src.data.bones:
        if bone.name in VALVEBIPED_BONES:
            continue
        child = edit_bones.get(bone.name)
        parent_name = bone.parent.name if bone.parent else "ValveBiped.Bip01_Pelvis"
        parent = edit_bones.get(parent_name) or edit_bones.get("ValveBiped.Bip01_Pelvis")
        if child and parent and child != parent:
            child.parent = parent
    bpy.ops.object.mode_set(mode="OBJECT")

    retarget_mesh_modifiers(prop)
    bpy.context.view_layer.update()
    print("Proportion Trick 2 for Blender 4.5.10 done.")


run()
