# Build and export the provided 4_export sample using the Blender 4.5.10 template.

import os
import sys

import bpy

ROOT = os.getcwd()
SAMPLE_DIR = os.path.join(ROOT, "4_export")
OUTPUT_DIR = os.path.join(ROOT, "4_export_processed")
OUTPUT_BLEND = os.path.join(OUTPUT_DIR, "proportion_trick_4_export_4.5.10.blend")
EXPORT_DIR = os.path.join(OUTPUT_DIR, "source_export")
ADDON_DIR = os.path.join(ROOT, "blender-4.5.10-windows-x64", "4.5", "scripts", "addons")


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


def reveal_converted_template_collections():
    def iter_layer_collections(layer_collection):
        yield layer_collection
        for child in layer_collection.children:
            yield from iter_layer_collections(child)

    for collection in bpy.data.collections:
        collection.hide_viewport = False
    for layer_collection in iter_layer_collections(bpy.context.view_layer.layer_collection):
        layer_collection.exclude = False
        layer_collection.hide_viewport = False
    for ob in bpy.data.objects:
        ob.hide_viewport = False
        ob.hide_set(False)
    bpy.context.view_layer.update()


def set_active_only(ob):
    if bpy.context.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def import_smd_parts():
    body_path = os.path.join(SAMPLE_DIR, "Body.smd")
    bpy.ops.import_scene.smd(filepath=body_path, append="NEW_ARMATURE", upAxis="Z")

    imported_armatures = [
        ob
        for ob in bpy.data.objects
        if ob.type == "ARMATURE" and ob.name not in {"proportions", "reference_female", "reference_male"}
    ]
    if not imported_armatures:
        raise RuntimeError("Body.smd did not create an imported armature.")

    gg = imported_armatures[0]
    gg.name = "gg"
    gg.data.name = "gg"

    for filename in sorted(os.listdir(SAMPLE_DIR)):
        if not filename.lower().endswith(".smd") or filename == "Body.smd":
            continue
        set_active_only(gg)
        bpy.ops.import_scene.smd(filepath=os.path.join(SAMPLE_DIR, filename), append="VALIDATE", upAxis="Z")


def import_vta_shapes():
    for filename, target_name in (("Body.vta", "Body"), ("Face.vta", "Face"), ("Feet.vta", "Feet")):
        target = bpy.data.objects.get(target_name)
        if target is None:
            raise RuntimeError("Cannot import %s because mesh %s was not found." % (filename, target_name))
        set_active_only(target)
        bpy.ops.import_scene.smd(filepath=os.path.join(SAMPLE_DIR, filename), append="VALIDATE", upAxis="Z")


def run_full_workflow():
    text = bpy.data.texts.get("Proportion Trick Full")
    if text is None:
        raise RuntimeError('Text block "Proportion Trick Full" was not found.')
    exec(text.as_string(), {"__name__": "__main__"})


def verify_processed_scene():
    prop = bpy.data.objects.get("proportions")
    if prop is None:
        raise RuntimeError('Processed scene is missing "proportions".')
    if len(prop.data.bones) != 214:
        raise RuntimeError("Expected 214 proportions bones, found %d." % len(prop.data.bones))

    bad_modifiers = []
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH" or ob.name == "smd_bone_vis" or ob.name.startswith("VTA vertices"):
            continue
        arm_mod = next((mod for mod in ob.modifiers if mod.type == "ARMATURE"), None)
        if arm_mod is None or arm_mod.object != prop:
            bad_modifiers.append(ob.name)
    if bad_modifiers:
        raise RuntimeError("Meshes not retargeted to proportions: %s" % ", ".join(bad_modifiers))

    remaining_pt_constraints = [
        "%s:%s" % (bone.name, constraint.name)
        for bone in prop.pose.bones
        for constraint in bone.constraints
        if constraint.name.startswith("PT_")
    ]
    if remaining_pt_constraints:
        raise RuntimeError("PT constraints were not cleared: %s" % ", ".join(remaining_pt_constraints[:10]))

    shape_counts = {}
    for name in ("Body", "Face", "Feet"):
        ob = bpy.data.objects.get(name)
        shape_counts[name] = len(ob.data.shape_keys.key_blocks) if ob and ob.data.shape_keys else 0
    if shape_counts["Body"] < 2 or shape_counts["Face"] < 2 or shape_counts["Feet"] < 2:
        raise RuntimeError("Expected Body, Face, and Feet shapekeys; found %s." % shape_counts)

    print("Processed scene verification passed.")
    print("proportions bones:", len(prop.data.bones))
    print("shape key counts:", shape_counts)


def export_source_files():
    os.makedirs(EXPORT_DIR, exist_ok=True)
    result = bpy.ops.export_scene.smd(export_scene=True)
    if result != {"FINISHED"}:
        raise RuntimeError("Source export failed: %s" % (result,))

    exported = []
    for dirpath, _, filenames in os.walk(EXPORT_DIR):
        for filename in filenames:
            if filename.lower().endswith((".smd", ".vta")):
                exported.append(os.path.join(dirpath, filename))
    if not exported:
        raise RuntimeError("Source export did not write any .smd or .vta files.")

    print("Source export file count:", len(exported))
    print("Source export root:", EXPORT_DIR)


os.makedirs(OUTPUT_DIR, exist_ok=True)
enable_source_tools()
reveal_converted_template_collections()
import_smd_parts()
import_vta_shapes()

bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
run_full_workflow()
verify_processed_scene()
bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
export_source_files()
bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
print("Saved processed sample:", OUTPUT_BLEND)
