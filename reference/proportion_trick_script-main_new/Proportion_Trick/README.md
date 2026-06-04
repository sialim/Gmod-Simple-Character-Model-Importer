# Blender 4.5.10 Proportion Trick Automation Handoff

This workspace contains a Blender 4.5.10-compatible conversion of the legacy
`proportion_trick_2.7_new.blend` workflow, plus automation scripts that import,
process, verify, and export a Source Engine model using Blender Source Tools.

The intended reader is another Codex session. Prefer the automated scripts below
instead of rediscovering the old Blender 2.79 tutorial workflow.

## Current State

Important artifacts:

- `proportion_trick_4.5.10.blend`
  - Blender 4.5.10-ready template converted from `proportion_trick_2.7_new.blend`.
  - Contains text blocks:
    - `Proportion Trick`
    - `Proportion Trick 2`
    - `Proportion Trick Full`
    - `QC`
    - `ValveBiped`
- `scripts/4.5.10/proportion_trick1.py`
  - Aligns the template `proportions` armature to the imported model armature named `gg`.
- `scripts/4.5.10/proportion_trick2.py`
  - Merges non-ValveBiped custom bones from `gg` into `proportions` and retargets mesh armature modifiers.
- `scripts/4.5.10/proportion_trick_full.py`
  - One-click workflow: align, apply pose as rest, clear generated constraints, merge extra bones, retarget meshes, configure Source export.
- `scripts/4.5.10/build_template.py`
  - Rebuilds `proportion_trick_4.5.10.blend` from the legacy 2.7 blend and current script files.
- `scripts/4.5.10/build_sample.py`
  - Imports `4_export`, runs the full workflow, verifies the processed scene, saves the processed blend, and exports Source files.
- `scripts/4.5.10/verify_processed.py`
  - Reopens a processed scene, validates the final armature/modifiers, and reruns Source export from a fresh Blender process.
- `4_export/`
  - Input test model files, SMD/VTA.
- `4_export_processed/proportion_trick_4_export_4.5.10.blend`
  - Processed sample scene.
- `4_export_processed/source_export/`
  - Exported Source files from the processed sample.

Legacy files such as `proportion_trick_2.7_new.blend`, `proportion_trick_2.9.blend`,
and `proportion_trick_4.3_new.blend` are preserved and should not be overwritten.

## Required Runtime

Use the bundled Blender 4.5.10 runtime:

```powershell
.\blender-4.5.10-windows-x64\blender.exe --version
```

Expected version:

```text
Blender 4.5.10 LTS
```

Do not use Blender 5.0 for final acceptance. It was useful during exploration, but the deliverable is specifically Blender 4.5.10.

Blender Source Tools 3.4.3 is required for SMD/VTA import/export:

- Archive in workspace: `blender_source_tools_3.4.3_for_blender_4.5.zip`
- Installed for Blender 4.5 user scripts at:
  - `%APPDATA%\Blender Foundation\Blender\4.5\scripts\addons\io_scene_valvesource`
- Also unpacked into the portable Blender tree under:
  - `blender-4.5.10-windows-x64\4.5\scripts\addons\io_scene_valvesource`

If Source Tools is missing, use `tar`, not PowerShell `Expand-Archive`, because the Source Tools ZIP uses BZip2-compressed entries:

```powershell
$addonDir = "$env:APPDATA\Blender Foundation\Blender\4.5\scripts\addons"
New-Item -ItemType Directory -Force -Path $addonDir | Out-Null
tar -xf blender_source_tools_3.4.3_for_blender_4.5.zip -C $addonDir
```

Validate the add-on:

```powershell
.\blender-4.5.10-windows-x64\blender.exe --factory-startup --background --python-expr "import bpy; bpy.ops.preferences.addon_enable(module='io_scene_valvesource'); import io_scene_valvesource; print(io_scene_valvesource.bl_info['version'])"
```

Expected output includes:

```text
(3, 4, 3)
```

## Fast Path: Rebuild and Process the Sample

Run these commands from the workspace root:

```powershell
.\blender-4.5.10-windows-x64\blender.exe --factory-startup --background proportion_trick_2.7_new.blend --python scripts\4.5.10\build_template.py
```

This updates `proportion_trick_4.5.10.blend` with the current `scripts/4.5.10/*.py`
text blocks.

Then process the provided test model:

```powershell
.\blender-4.5.10-windows-x64\blender.exe --factory-startup --background proportion_trick_4.5.10.blend --python scripts\4.5.10\build_sample.py
```

Expected results:

- `4_export_processed/proportion_trick_4_export_4.5.10.blend`
- `4_export_processed/source_export/*.smd`
- `4_export_processed/source_export/*.vta`
- `4_export_processed/source_export/anims/*.smd`

The current known export count is 21 `.smd`/`.vta` files.

## Critical A-Pose Regression Fix

The first Blender 4.5.10 conversion had a serious regression: the generated
`4_export_processed` output could export the default/A-posed `proportions`
armature instead of the human 2.79-style proportional result in `5_propo`.

Root cause:

- The legacy blend stores `proportions` in a hidden collection.
- The converted scripts cleared object and view-layer visibility, but did not clear `Collection.hide_viewport`.
- In Blender 4.5.10, constraints on an owner armature inside a hidden collection can remain valid but unevaluated.
- `Apply Pose as Rest Pose` then baked the unchanged template pose, producing the bad A-pose export.

Fixes now in the 4.5.10 scripts:

- `unhide_for_viewlayer()` in all Proportion Trick scripts clears both collection-level and view-layer visibility.
- `build_template.py` saves the converted template with legacy hidden collections revealed.
- `build_sample.py` reveals converted template collections before import.
- `proportion_trick_full.py` verifies alignment after adding `PT_*` constraints and before applying rest pose. If important bones have not moved to `gg`, it raises instead of exporting.

Validation against `5_propo` after this fix:

- `proportions` exports with 214 bones.
- `Body.smd`/other mesh SMD global ValveBiped positions match the human output within about `0.00004` units.
- The large previous A-pose deltas are gone; comparing fixed output to `4_export/Body.smd` shows the expected proportional rest-pose changes.

## Toe/Foot Local Basis Correction

The old manual workflow also produces a small foot/toe local-basis correction
that is easy to miss when only checking global joint positions. The Blender
4.5.10 scripts now reproduce it after applying the aligned pose as rest pose.

Behavior:

- Compute the left/right `ValveBiped.Bip01_*_Toe0` vectors in world space.
- For each toe, compute `atan2(vector.y, vector.z)` and normalize it to the nearest small rotation in `[-90, 90]` degrees.
- Apply the arithmetic average as a global-X rotation to the tails of both toe bones and both foot bones.
- Keep every corrected bone head fixed; only edit-bone tails move.
- `Proportion Trick Full` applies this automatically.
- `Proportion Trick 2` also applies it for the manual two-step workflow after the user has applied pose as rest pose.

Expected comparison against `5_propo/Body.smd` after this correction:

- Global ValveBiped position delta remains about `0.00005` units or better.
- Foot local Euler delta drops from about `0.0673` radians to about `0.001` radians or better.
- Toe local translation delta drops from about `0.354` units to about `0.005` units or better.

## What `build_sample.py` Automates

The old manual workflow required importing the model, renaming the skeleton to
`gg`, running Proportion Trick, applying pose as rest pose, clearing constraints,
and running Proportion Trick 2. The automation performs those steps in order.

Import sequence:

1. Import `4_export/Body.smd` with Source Tools `append='NEW_ARMATURE'`.
2. Rename the imported armature to `gg`.
3. Import all remaining `.smd` files from `4_export` with `append='VALIDATE'` against `gg`.
4. Import VTA shapekeys by selecting the matching mesh before each VTA import:
   - `Body.vta` -> `Body`
   - `Face.vta` -> `Face`
   - `Feet.vta` -> `Feet`
5. Save the imported scene once to `4_export_processed/proportion_trick_4_export_4.5.10.blend`.
6. Execute the embedded `Proportion Trick Full` text block.
7. Verify the processed scene.
8. Save again.
9. Export Source files with Blender Source Tools.
10. Save again with export settings retained.

## Full Workflow Behavior

`proportion_trick_full.py` expects:

- Template armature: `proportions`
- Imported model armature: `gg`
- Optional reference armatures: `reference_male`, `reference_female`

The script:

- Adds named generated constraints with `PT_*` prefixes.
- Repairs collection and view-layer visibility before posing armatures.
- Verifies the constrained pose evaluated before applying it as rest pose.
- Applies the aligned pose as the new rest pose.
- Explicitly removes generated constraints after pose application.
- Applies the toe/foot local-basis correction in Edit Mode.
- Copies custom non-ValveBiped bones from `gg` into `proportions`.
- Reparents copied custom bones to match the original `gg` hierarchy.
- Retargets mesh Armature modifiers to `proportions`.
- Excludes helper meshes from retarget/export:
  - `smd_bone_vis`
  - Source Tools diagnostic meshes named `VTA vertices*`
- Configures Source Tools export:
  - `scene.vs.export_format = 'SMD'`
  - `scene.vs.smd_format = 'SOURCE'`
  - `scene.vs.qc_compile = False`
  - processed sample export root: `//source_export`, relative to the processed blend

The old two-step text blocks are still available for manual use:

- Run `Proportion Trick` after importing a model armature named `gg`.
- Apply pose as rest pose and clear constraints manually.
- Run `Proportion Trick 2` to apply toe/foot local-basis correction, merge custom bones, and retarget modifiers.

For automation, prefer `Proportion Trick Full`.

## Verification Checklist

After processing `4_export`, verify in Blender 4.5.10:

- `proportions` has 214 bones.
- No `PT_*` constraints remain on `proportions` pose bones.
- All non-helper meshes have an Armature modifier targeting `proportions`.
- Shapekey counts are present:
  - `Body`: 8 key blocks
  - `Face`: 86 key blocks
  - `Feet`: 8 key blocks
- Source export writes 21 `.smd`/`.vta` files.
- Reopening the processed `.blend` and exporting again succeeds from a fresh Blender session.

The saved scene was verified with this fresh-session pattern:

```powershell
.\blender-4.5.10-windows-x64\blender.exe --factory-startup --background 4_export_processed\proportion_trick_4_export_4.5.10.blend --python scripts\4.5.10\verify_processed.py
```

Expected key lines:

```text
21 files exported in 9.7 seconds with 0 Errors and 19 Warnings
Reopen verification/export passed.
proportions bones: 214
```

## Expected Warnings

The sample model has 214 bones. Blender Source Tools warns:

```text
SMD only supports 128 bones
Exported 214 bones, but SMD only supports 128
```

These warnings are expected for this sample and are not treated as automation failure.
The successful reference run exported with:

```text
0 Errors and 19 Warnings
21 files exported
```

Source Tools also logs VTA import warnings for unmatched vertices:

```text
52 VTA vertices were not matched
12 VTA vertices were not matched
```

Those diagnostic helper meshes are intentionally excluded from export.

Observed export note:

- `Feet.vta` is written and contains 7 flex shapes, but Source Tools logged `0 verts` for that VTA in the sample. Do not silently treat that as a script failure unless the downstream compiler/use case requires non-empty Feet flex deltas.

## Output File Inventory

Expected exported Source files:

```text
4_export_processed/source_export/Arms.smd
4_export_processed/source_export/Body.smd
4_export_processed/source_export/Body.vta
4_export_processed/source_export/Bra.smd
4_export_processed/source_export/Clothes.smd
4_export_processed/source_export/Face.smd
4_export_processed/source_export/Face.vta
4_export_processed/source_export/Feet.smd
4_export_processed/source_export/Feet.vta
4_export_processed/source_export/FeetConstruct.smd
4_export_processed/source_export/Glove.smd
4_export_processed/source_export/Hair.smd
4_export_processed/source_export/Hairpin.smd
4_export_processed/source_export/Kamikazari.smd
4_export_processed/source_export/Pants.smd
4_export_processed/source_export/Physics.smd
4_export_processed/source_export/Shoes.smd
4_export_processed/source_export/Sleeves.smd
4_export_processed/source_export/anims/proportions.smd
4_export_processed/source_export/anims/reference_female.smd
4_export_processed/source_export/anims/reference_male.smd
```

## Maintenance Notes for Future Codex Sessions

- Use `apply_patch` for tracked script/doc edits.
- Do not overwrite legacy `.blend` files.
- Rebuild `proportion_trick_4.5.10.blend` after changing any script that should be embedded as a text block.
- Run `build_sample.py` after changing workflow behavior; it is the main regression test.
- Run `verify_processed.py` after saving a processed blend to prove export is not dependent on transient session state.
- Use `--factory-startup` for headless validation to avoid user add-ons influencing results.
- If Source Tools cannot be enabled through `bpy.ops.preferences.addon_enable`, add the Blender 4.5 user add-on path to `sys.path` or reinstall the add-on from the bundled ZIP with `tar`.
- Avoid relying on Blender UI state. The scripts should set active objects, selected objects, and modes explicitly.
- Do not remove the collection visibility repair or the post-constraint alignment guard; those prevent the A-pose regression.
- Keep helper meshes out of export. Diagnostic VTA helper objects have no polygons and will produce Source Tools export errors if included.

## Manual In-Blender Use

For a user running the converted template interactively:

1. Open `proportion_trick_4.5.10.blend` in Blender 4.5.10.
2. Enable Blender Source Tools 3.4.3.
3. Import the model SMDs with the same order used by `build_sample.py`.
4. Rename the imported model armature to `gg`.
5. Import VTA files with their matching mesh selected.
6. Run the `Proportion Trick Full` text block.
7. Save the processed blend.
8. Export from Source Tools using the configured SMD/Source settings.

Automation should use `build_sample.py`; manual use is included only as a fallback.
