"""Run with Blender --background --factory-startup --python tests/blender_spine_repair.py."""

import copy
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import bpy


root = Path(__file__).resolve().parents[1]
module_path = Path(os.environ.get("SPINE_REPAIR_MODULE", root / "tools/blender_fix_spine_bones.py"))
spec = importlib.util.spec_from_file_location("spine_repair", module_path)
spine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(spine)


class SpineRepairTests(unittest.TestCase):
    def make_rig(self, canonical=False):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        data = bpy.data.armatures.new("test_rig")
        rig = bpy.data.objects.new("test_rig", data)
        bpy.context.collection.objects.link(rig)
        bpy.context.view_layer.objects.active = rig
        rig.select_set(True)
        bpy.ops.object.mode_set(mode="EDIT")

        def bone(name, z, parent=None, x=0):
            b = data.edit_bones.new(name)
            b.head = (x, 0, z)
            b.tail = (x, 0, z + 0.04)
            b.parent = data.edit_bones.get(parent) if parent else None

        bone(spine.PELVIS, 1)
        if canonical:
            bone(spine.SPINE, 1.1, spine.PELVIS)
            bone(spine.SPINE1, 1.2, spine.SPINE)
            bone(spine.SPINE2, 1.3, spine.SPINE1)
            bone(spine.SPINE4, 1.4, spine.SPINE2)
            chest = spine.SPINE4
        else:
            # The parent helper prevents the two-bone collapsed-spine shortcut.
            # The chest claims the existing Spine1 name, leaving no lower candidate.
            bone("Offset_helper", 1.06, spine.PELVIS, x=0.6)
            bone(spine.SPINE, 1.1, "Offset_helper")
            bone(spine.SPINE1, 1.4, spine.SPINE)
            chest = spine.SPINE1
        bone(spine.NECK, 1.5, chest)
        bone(spine.L_CLAVICLE, 1.43, chest, x=0.14)
        bone(spine.R_CLAVICLE, 1.43, chest, x=-0.14)
        bpy.ops.object.mode_set(mode="OBJECT")
        mesh = bpy.data.meshes.new("weighted_torso")
        mesh.from_pydata([(0, 0, 1.1), (0, 0, 1.3), (0.1, 0, 1.2)], [], [(0, 1, 2)])
        obj = bpy.data.objects.new("weighted_torso", mesh)
        bpy.context.collection.objects.link(obj)
        obj.parent = rig
        obj.modifiers.new("Armature", "ARMATURE").object = rig
        for index, name in enumerate((spine.PELVIS, spine.SPINE, chest)):
            obj.vertex_groups.new(name=name).add([index], 1, "REPLACE")
        return rig, obj

    def assert_repaired(self, rig, obj, plan):
        result = spine.apply_plan(rig, plan)
        self.assertTrue(result["validation"]["ok"], result["validation"])
        heights = [rig.data.bones[name].head_local.z for name in spine.CHAIN_TARGETS]
        self.assertEqual(heights, sorted(heights))
        for name, parent in spine.TARGET_PARENTS.items():
            if parent:
                self.assertEqual(rig.data.bones[name].parent.name, parent)
        for index, name in enumerate((spine.PELVIS, spine.SPINE, spine.SPINE4)):
            self.assertAlmostEqual(obj.vertex_groups[name].weight(index), 1)
        self.assertNotIn(spine.SPINE1, obj.vertex_groups)
        return result

    def test_sparse_torso_gets_an_unweighted_intermediate(self):
        rig, obj = self.make_rig()
        plan = spine.proposal_for_armature(rig, spine.weighted_bone_names())
        self.assertEqual(plan["targets"][spine.SPINE1]["action"], "add")
        self.assert_repaired(rig, obj, plan)

    def test_saved_incomplete_plan_is_recovered_without_modifying_it(self):
        rig, obj = self.make_rig()
        plan = spine.proposal_for_armature(rig, spine.weighted_bone_names())
        plan["targets"][spine.SPINE1] = spine.make_entry(spine.SPINE1, None, "missing", spine.SPINE, 0)
        original = copy.deepcopy(plan)
        result = self.assert_repaired(rig, obj, plan)
        self.assertIn(spine.SPINE1, result["resolved_targets"])
        self.assertEqual(plan, original)

    def test_missing_chest_stops_before_renaming_or_merging(self):
        rig, obj = self.make_rig()
        plan = spine.proposal_for_armature(rig, spine.weighted_bone_names())
        plan["targets"][spine.SPINE4] = spine.make_entry(spine.SPINE4, None, "missing", spine.SPINE2, 0)
        names = [b.name for b in rig.data.bones]
        with self.assertRaisesRegex(RuntimeError, "unresolved source bones"):
            spine.apply_plan(rig, plan)
        self.assertEqual([b.name for b in rig.data.bones], names)

    def test_canonical_torso_keeps_its_existing_bones_and_positions(self):
        rig, obj = self.make_rig(canonical=True)
        before = {b.name: tuple(b.head_local) for b in rig.data.bones}
        plan = spine.proposal_for_armature(rig, spine.weighted_bone_names())
        result = spine.apply_plan(rig, plan)
        self.assertTrue(result["validation"]["ok"], result["validation"])
        self.assertEqual(result["added"], [])
        self.assertEqual({b.name: tuple(b.head_local) for b in rig.data.bones}, before)

    def run_cli(self, folder, plan):
        input_path = folder / "fixed.blend"
        plan_path = folder / "plan.json"
        output_path = folder / "spine_fixed.blend"
        report_path = folder / "report.json"
        bpy.ops.wm.save_as_mainfile(filepath=str(input_path))
        plan_path.write_text(json.dumps(plan), encoding="utf-8")
        args = ["blender", "--", "--mode", "apply", "--input-blend", str(input_path),
                "--plan-json", str(plan_path), "--output-blend", str(output_path),
                "--report-json", str(report_path)]
        with patch.object(sys, "argv", args):
            spine.main()
        return output_path, report_path

    def test_cli_saves_and_reopens_a_valid_repaired_rig(self):
        rig, obj = self.make_rig()
        plan = spine.proposal_for_armature(rig, spine.weighted_bone_names())
        with tempfile.TemporaryDirectory() as folder:
            output_path, report_path = self.run_cli(Path(folder), plan)
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertTrue(report["applied"]["validation"]["ok"])
            bpy.ops.wm.open_mainfile(filepath=str(output_path))
            self.assertTrue(spine.validation_for_armature(spine.active_armature())["ok"])

    def test_cli_writes_a_report_when_the_plan_is_unresolved(self):
        rig, obj = self.make_rig()
        plan = spine.proposal_for_armature(rig, spine.weighted_bone_names())
        plan["targets"][spine.SPINE4] = spine.make_entry(spine.SPINE4, None, "missing", spine.SPINE2, 0)
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(RuntimeError, "unresolved source bones"):
                self.run_cli(Path(folder), plan)
            report = json.loads((Path(folder) / "report.json").read_text(encoding="utf-8"))
            self.assertFalse(report["validation"]["ok"])
            self.assertIn(spine.SPINE4, report["validation"]["errors"][0])
            self.assertFalse((Path(folder) / "spine_fixed.blend").exists())


unittest.main(argv=[sys.argv[0]])
