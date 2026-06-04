# Build the Blender 4.5.10 template from the legacy 2.7 blend.

import os

import bpy

ROOT = os.getcwd()
SCRIPT_DIR = os.path.join(ROOT, "scripts", "4.5.10")
OUTPUT_BLEND = os.path.join(ROOT, "proportion_trick_4.5.10.blend")

TEXT_SOURCES = {
    "Proportion Trick": os.path.join(SCRIPT_DIR, "proportion_trick1.py"),
    "Proportion Trick 2": os.path.join(SCRIPT_DIR, "proportion_trick2.py"),
    "Proportion Trick Full": os.path.join(SCRIPT_DIR, "proportion_trick_full.py"),
    "QC": os.path.join(ROOT, "QC.txt"),
    "ValveBiped": os.path.join(ROOT, "ValveBiped.txt"),
}


def replace_text_block(name, path):
    text = bpy.data.texts.get(name) or bpy.data.texts.new(name)
    text.clear()
    with open(path, "r", encoding="utf-8") as handle:
        text.write(handle.read())
    text.use_fake_user = True


def iter_layer_collections(layer_collection):
    yield layer_collection
    for child in layer_collection.children:
        yield from iter_layer_collections(child)


for block_name, source_path in TEXT_SOURCES.items():
    replace_text_block(block_name, source_path)

for collection in bpy.data.collections:
    collection.hide_viewport = False

for layer_collection in iter_layer_collections(bpy.context.view_layer.layer_collection):
    layer_collection.exclude = False
    layer_collection.hide_viewport = False

for ob in bpy.data.objects:
    ob.hide_viewport = False
    ob.hide_set(False)
    ob.select_set(False)

prop = bpy.data.objects.get("proportions")
if prop:
    prop.hide_set(False)
    prop.hide_viewport = False
    prop.select_set(True)
    bpy.context.view_layer.objects.active = prop

bpy.ops.wm.save_as_mainfile(filepath=OUTPUT_BLEND)
print("Saved Blender 4.5.10 template:", OUTPUT_BLEND)
