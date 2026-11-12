import math
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import gmod_wrist_twist as twist
import sort_qc_compile as qc


class WristTwistTests(unittest.TestCase):
    def setUp(self):
        self.poses = {}
        for side in ("L", "R"):
            forearm = f"ValveBiped.Bip01_{side}_Forearm"
            self.poses[forearm] = twist.BonePose("", (0, 0, 0), (0, 0, 0))
            self.poses[f"ValveBiped.Bip01_{side}_Hand"] = twist.BonePose(
                forearm, (9, 0, 0), (1.57 if side == "L" else -1.57, -0.1, 0.13)
            )
            self.poses[f"ZHandTwist_{side}"] = twist.BonePose(forearm, (5.4, 0, 0), (0, -0.59, -1.57))
        self.declared = set(self.poses)

    def assert_same_rotation(self, a, b):
        self.assertAlmostEqual(abs(sum(x*y for x, y in zip(a, b))), 1.0, places=6)

    def test_neutral_pose_preserves_helper_position_and_its_own_bind_rotation(self):
        text, helpers = twist.build_vrd(self.poses, self.declared)
        self.assertEqual(helpers, ["ZHandTwist_L", "ZHandTwist_R"])
        blocks = text.split("<helper> ")[1:]
        for side, block in zip(("L", "R"), blocks):
            rows = [line.split()[1:] for line in block.splitlines() if line.startswith("<trigger>")]
            self.assertEqual(len(rows), 25)
            self.assertLessEqual(len(rows), 32)  # DoQuatInterpBone uses weight[32].
            neutral = [float(v) for v in rows[0]]
            self.assert_same_rotation(twist.from_euler(tuple(math.radians(v) for v in neutral[1:4])),
                                      twist.from_euler(self.poses[f"ValveBiped.Bip01_{side}_Hand"].rotation))
            self.assert_same_rotation(twist.from_euler(tuple(math.radians(v) for v in neutral[4:7])),
                                      twist.from_euler(self.poses[f"ZHandTwist_{side}"].rotation))
            self.assertIn("<basepos> 5.400000 0.000000 0.000000", block)
            self.assertTrue(all(row[-3:] == ["0", "0", "0"] for row in rows))

    def test_helper_follows_half_of_hand_roll_in_the_parent_frame(self):
        text, _ = twist.build_vrd(self.poses, self.declared)
        rows = [line.split()[1:] for line in text.splitlines() if line.startswith("<trigger>")]
        sixty = [float(v) for v in rows[2]]
        hand = twist.from_euler(self.poses["ValveBiped.Bip01_L_Hand"].rotation)
        helper = twist.from_euler(self.poses["ZHandTwist_L"].rotation)
        self.assert_same_rotation(twist.from_euler(tuple(math.radians(v) for v in sixty[1:4])),
                                  twist.multiply(twist.axis_rotation((1, 0, 0), 60), hand))
        self.assert_same_rotation(twist.from_euler(tuple(math.radians(v) for v in sixty[4:7])),
                                  twist.multiply(twist.axis_rotation((1, 0, 0), 30), helper))

    def test_authored_wrist_helper_takes_precedence(self):
        authored = "\ufeff<helper> ValveBiped.ZHandTwist_L Bip01_L_Forearm Bip01_L_Forearm Bip01_L_Hand\n"
        text, helpers = twist.build_vrd(self.poses, self.declared, authored)
        self.assertEqual(helpers, ["ZHandTwist_R"])
        self.assertNotIn("<helper> ZHandTwist_L ", text)

    def test_nonstandard_hierarchy_is_not_reparented_or_driven(self):
        self.poses["ValveBiped.Bip01_L_Hand"] = twist.BonePose("ZHandTwist_L", (9, 0, 0), (0, 0, 0))
        _, helpers = twist.build_vrd(self.poses, self.declared)
        self.assertEqual(helpers, ["ZHandTwist_R"])

    def test_missing_or_unrelated_helper_bones_are_not_synthesized(self):
        _, helpers = twist.build_vrd(self.poses, self.declared - {"ZHandTwist_L", "ZHandTwist_R"})
        self.assertEqual(helpers, [])
        self.poses["ZHandTwist_L"] = twist.BonePose("ValveBiped.Bip01_L_Forearm", (50, 3, 0), (0, 0, 0))
        _, helpers = twist.build_vrd(self.poses, self.declared)
        self.assertEqual(helpers, ["ZHandTwist_R"])

    def make_source(self, source):
        (source / "anims").mkdir()
        items = list(self.poses.items())
        indexes = {name: i for i, (name, _) in enumerate(items)}
        lines = ["version 1\nnodes\n"]
        for name, pose in items:
            lines.append(f'{indexes[name]} "{name}" {indexes.get(pose.parent, -1)}\n')
        lines.append("end\nskeleton\ntime 0\n")
        for name, pose in items:
            lines.append(f'{indexes[name]} ' + ' '.join(str(v) for v in (*pose.position, *pose.rotation)) + '\n')
        lines.append("end\n")
        (source / "anims/proportions.smd").write_text("".join(lines))
        return [f'$definebone "{name}" "{pose.parent}" 0 0 0 0 0 0\n' for name, pose in items]

    def test_compile_preparation_preserves_authored_vrd_and_removes_stale_generated_data(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            defines = self.make_source(source)
            authored = "// authored thigh helper\n<helper> skirt thigh thigh calf\n"
            (source / "vrd.vrd").write_text(authored)
            report = qc.prepare_gmod_wrist_twist(source, defines)
            output = source / twist.GENERATED_FILENAME
            self.assertEqual(report["helpers"], ["ZHandTwist_L", "ZHandTwist_R"])
            self.assertIn(authored.rstrip(), output.read_text())
            before = output.read_text()
            qc.prepare_gmod_wrist_twist(source, defines)
            self.assertEqual(output.read_text(), before)
            self.assertEqual((source / "vrd.vrd").read_text(), authored)
            qc.prepare_gmod_wrist_twist(source, [])
            self.assertFalse(output.exists())
            self.assertEqual((source / "vrd.vrd").read_text(), authored)

    def test_other_games_do_not_generate_wrist_drivers(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            defines = self.make_source(source)
            for game in ("l4d2", "sfm"):
                report = qc.prepare_gmod_wrist_twist(source, defines, game)
                self.assertFalse(report["enabled"])
                self.assertFalse((source / twist.GENERATED_FILENAME).exists())

    def test_final_gmod_qc_uses_merged_drivers_and_capture_uses_authored_vrd(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            defines = self.make_source(source)
            authored = "<helper> ZHandTwist_L Bip01_L_Forearm Bip01_L_Forearm Bip01_L_Hand\n"
            original = b"\xef\xbb\xbf" + authored.encode("utf-8")
            (source / "vrd.vrd").write_bytes(original)
            report = qc.prepare_gmod_wrist_twist(source, defines)
            self.assertEqual(report["helpers"], ["ZHandTwist_R"])
            merged = (source / twist.GENERATED_FILENAME).read_text(encoding="utf-8")
            self.assertNotIn("\ufeff", merged)
            self.assertIn(authored, merged)
            self.assertEqual((source / "vrd.vrd").read_bytes(), original)
            plan = {"author": "test", "character_category": "characters", "model_name": "wrist", "bodygroups": []}
            for capture in (False, True):
                text = "".join(qc.base_qc_lines(
                    plan, source, include_definebones=defines, for_definebone_capture=capture,
                ))
                name = "vrd.vrd" if capture else twist.GENERATED_FILENAME
                self.assertIn(f'$proceduralbones "{name}"', text)

    def test_generated_output_cannot_replace_an_authored_file(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)
            defines = self.make_source(source)
            output = source / twist.GENERATED_FILENAME
            output.write_text("// user file\n")
            with self.assertRaisesRegex(RuntimeError, "overwrite"):
                qc.prepare_gmod_wrist_twist(source, defines)
            self.assertEqual(output.read_text(), "// user file\n")


if __name__ == "__main__":
    unittest.main()
