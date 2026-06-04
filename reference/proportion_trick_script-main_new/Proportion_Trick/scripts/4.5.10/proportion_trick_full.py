# One-click Proportion Trick workflow for Blender 4.5.10.
# Run after importing Source model parts and renaming the imported armature to "gg".

import math
import os
import sys
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

VALVEBIPED_BONE_SET = set(VALVEBIPED_BONES)

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

ALIGNMENT_EVALUATION_BONES = [
    "ValveBiped.Bip01_Pelvis",
    "ValveBiped.Bip01_Spine",
    "ValveBiped.Bip01_Spine1",
    "ValveBiped.Bip01_L_UpperArm",
    "ValveBiped.Bip01_R_UpperArm",
    "ValveBiped.Bip01_L_Thigh",
    "ValveBiped.Bip01_R_Thigh",
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


def align_proportions(src, prop):
    ensure_pose_mode(prop)
    for bone_name in VALVEBIPED_BONES:
        prop_bone = prop.pose.bones.get(bone_name)
        if prop_bone:
            remove_pt_constraints(prop_bone)

    for bone_name in VALVEBIPED_BONES:
        prop_bone = prop.pose.bones.get(bone_name)
        if prop_bone and src.pose.bones.get(bone_name):
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


def assert_alignment_evaluated(src, prop):
    bpy.context.view_layer.update()
    mismatches = []
    checked = 0
    for bone_name in ALIGNMENT_EVALUATION_BONES:
        src_bone = src.pose.bones.get(bone_name)
        prop_bone = prop.pose.bones.get(bone_name)
        if not src_bone or not prop_bone:
            continue
        checked += 1
        src_pos = (src.matrix_world @ src_bone.matrix).to_translation()
        prop_pos = (prop.matrix_world @ prop_bone.matrix).to_translation()
        delta = (prop_pos - src_pos).length
        if delta > 0.05:
            mismatches.append("%s %.4f" % (bone_name, delta))

    if checked == 0:
        raise RuntimeError("No shared ValveBiped bones were available to verify alignment.")
    if mismatches:
        raise RuntimeError(
            "Proportion constraints did not evaluate before applying rest pose. "
            "Check armature and collection visibility. Largest deltas: %s"
            % ", ".join(mismatches[:5])
        )


def apply_pose_as_rest_and_clear(prop):
    ensure_pose_mode(prop)
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.armature_apply(selected=False)
    if bpy.context.mode != "POSE":
        ensure_pose_mode(prop)
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.constraints_clear()
    for pose_bone in prop.pose.bones:
        for constraint in list(pose_bone.constraints):
            pose_bone.constraints.remove(constraint)


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


def link_object_like(source, new_object):
    if source.users_collection:
        source.users_collection[0].objects.link(new_object)
    else:
        bpy.context.collection.objects.link(new_object)


def merge_extra_bones(src, prop):
    source_extra_names = [bone.name for bone in src.data.bones if bone.name not in VALVEBIPED_BONE_SET]
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
            if bone_name in VALVEBIPED_BONE_SET or bone_name in existing_prop_names:
                bone = edit_bones.get(bone_name)
                if bone:
                    edit_bones.remove(bone)
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
        if bone.name in VALVEBIPED_BONE_SET:
            continue
        child = edit_bones.get(bone.name)
        parent_name = bone.parent.name if bone.parent else "ValveBiped.Bip01_Pelvis"
        parent = edit_bones.get(parent_name) or edit_bones.get("ValveBiped.Bip01_Pelvis")
        if child and parent and child != parent:
            child.parent = parent
    bpy.ops.object.mode_set(mode="OBJECT")


def retarget_mesh_modifiers(prop):
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH" or ob.name in HELPER_MESH_NAMES or ob.name.startswith("VTA vertices"):
            continue
        armature_mod = next((mod for mod in ob.modifiers if mod.type == "ARMATURE"), None)
        if armature_mod is None:
            armature_mod = ob.modifiers.new(name="Armature", type="ARMATURE")
        armature_mod.object = prop


def default_export_path():
    if bpy.data.filepath:
        blend_dir = os.path.dirname(bpy.data.filepath)
        if os.path.basename(blend_dir).lower() == "4_export_processed":
            return "//source_export"
    return "//4_export_processed/source_export"


def enable_source_tools_if_available():
    try:
        bpy.ops.preferences.addon_enable(module="io_scene_valvesource")
        return True
    except Exception:
        pass

    blender_root = os.path.dirname(bpy.app.binary_path)
    addon_dirs = [
        os.path.join(blender_root, "4.5", "scripts", "addons"),
        bpy.utils.user_resource("SCRIPTS", path="addons", create=False),
    ]
    for addon_dir in addon_dirs:
        if addon_dir and addon_dir not in sys.path and os.path.isdir(addon_dir):
            sys.path.insert(0, addon_dir)
    try:
        import io_scene_valvesource

        io_scene_valvesource.register()
        return True
    except Exception as exc:
        print("Source Tools could not be enabled: %s" % exc)
        return False


def configure_source_export(prop):
    if not enable_source_tools_if_available():
        return False

    scene = bpy.context.scene
    scene.vs.export_format = "SMD"
    scene.vs.smd_format = "SOURCE"
    scene.vs.qc_compile = False
    scene.vs.export_path = default_export_path()

    for collection in bpy.data.collections:
        collection.vs.mute = True

    for ob in scene.objects:
        if ob.type == "MESH":
            ob.vs.export = ob.name not in HELPER_MESH_NAMES and not ob.name.startswith("VTA vertices")
            ob.vs.subdir = "."
        elif ob.type == "ARMATURE":
            ob.vs.export = ob.name in {PROP_ARMATURE_NAME, "reference_male", "reference_female"}
            ob.vs.subdir = "anims"
            if hasattr(ob.data, "vs"):
                ob.data.vs.action_selection = "CURRENT"
        else:
            ob.vs.export = False

    try:
        from io_scene_valvesource.utils import State

        State.update_scene(scene)
    except Exception as exc:
        print("Source Tools export list refresh failed: %s" % exc)

    return True


def run():
    src = get_armature(SRC_ARMATURE_NAME)
    prop = get_armature(PROP_ARMATURE_NAME)
    unhide_for_viewlayer(src)
    unhide_for_viewlayer(prop)

    align_proportions(src, prop)
    assert_alignment_evaluated(src, prop)
    apply_pose_as_rest_and_clear(prop)
    apply_toe_foot_basis_correction(prop)
    merge_extra_bones(src, prop)
    retarget_mesh_modifiers(prop)
    configure_source_export(prop)

    set_active_only(prop)
    bpy.context.view_layer.update()
    print("One-click Proportion Trick workflow for Blender 4.5.10 done.")


run()
