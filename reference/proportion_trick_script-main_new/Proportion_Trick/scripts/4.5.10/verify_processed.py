# Verify that a processed Proportion Trick scene can be reopened and exported.

import os
import sys

import bpy

ROOT = os.getcwd()
ADDON_DIR = os.path.join(ROOT, "blender-4.5.10-windows-x64", "4.5", "scripts", "addons")
PROP_ARMATURE_NAME = "proportions"
HELPER_MESH_NAMES = {"smd_bone_vis"}


def enable_source_tools():
    try:
        bpy.ops.preferences.addon_enable(module="io_scene_valvesource")
        return
    except Exception:
        pass

    if ADDON_DIR not in sys.path:
        sys.path.insert(0, ADDON_DIR)
    import io_scene_valvesource

    io_scene_valvesource.register()


def verify_scene():
    prop = bpy.data.objects.get(PROP_ARMATURE_NAME)
    if prop is None or prop.type != "ARMATURE":
        raise RuntimeError('Processed scene is missing armature "%s".' % PROP_ARMATURE_NAME)
    bone_count = len(prop.data.bones)
    if bone_count != 214:
        raise RuntimeError("Expected 214 proportions bones, found %d." % bone_count)

    remaining_pt_constraints = [
        "%s:%s" % (bone.name, constraint.name)
        for bone in prop.pose.bones
        for constraint in bone.constraints
        if constraint.name.startswith("PT_")
    ]
    if remaining_pt_constraints:
        raise RuntimeError("PT constraints remain: %s" % ", ".join(remaining_pt_constraints[:10]))

    bad_modifiers = []
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH" or ob.name in HELPER_MESH_NAMES or ob.name.startswith("VTA vertices"):
            continue
        armature_mod = next((mod for mod in ob.modifiers if mod.type == "ARMATURE"), None)
        if armature_mod is None or armature_mod.object != prop:
            bad_modifiers.append(ob.name)
    if bad_modifiers:
        raise RuntimeError("Meshes not retargeted to proportions: %s" % ", ".join(bad_modifiers))

    result = bpy.ops.export_scene.smd(export_scene=True)
    if result != {"FINISHED"}:
        raise RuntimeError("Source export failed after reopening: %s" % (result,))

    print("Reopen verification/export passed.")
    print("proportions bones:", bone_count)


enable_source_tools()
verify_scene()
