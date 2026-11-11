import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import sort_qc_compile as qc


class ProportionGroundingTests(unittest.TestCase):
    def setUp(self):
        self.workspace = tempfile.TemporaryDirectory()
        self.addCleanup(self.workspace.cleanup)
        self.source = Path(self.workspace.name)
        (self.source / "anims").mkdir()
        (self.source / "anims" / "reference_male.smd").touch()
        self.plan = {
            "author": "test",
            "character_category": "characters",
            "model_name": "grounding",
            "bodygroups": [],
        }
        self.definebones = ['$definebone "ValveBiped.Bip01_Pelvis" "" 0 0 0 0 0 0 0 0 0 0 0 0\n']

    def test_gmod_body_keeps_proportion_height_for_both_animation_sets(self):
        # Missing game keys occur in saved plans from older importer versions.
        for game in (None, "gmod"):
            for gender in ("female", "male"):
                for player in (False, True):
                    with self.subTest(game=game, gender=gender, player=player):
                        plan = dict(self.plan, gender=gender)
                        if game is not None:
                            plan["game"] = game
                        text = "".join(qc.base_qc_lines(
                            plan, self.source, pm=player, include_definebones=self.definebones
                        ))
                        self.assertNotIn("$ikautoplaylock", text)
                        self.assertNotIn("$origin", text)
                        for side in ("r", "l"):
                            self.assertIn(f'$ikchain "{side}foot" "mci_foot_ik_target"', text)
                        self.assertIn('$ikchain "rhand" "ValveBiped.Bip01_R_Hand"', text)
                        self.assertIn('$ikchain "lhand" "ValveBiped.Bip01_L_Hand"', text)
                        self.assertIn('$definebone "mci_foot_ik_root" ""', text)
                        self.assertIn('$definebone "mci_foot_ik_knee" "mci_foot_ik_root"', text)
                        self.assertIn('$definebone "mci_foot_ik_target" "mci_foot_ik_knee"', text)
                        self.assertNotIn('ikrule "rfoot" release', text)
                        self.assertIn(f'$sequence reference "anims/reference_{gender}"', text)
                        self.assertIn('subtract reference 0', text)
                        self.assertIn('$sequence proportions a_proportions predelta autoplay', text)

    def test_gmod_capture_uses_only_the_real_skeleton(self):
        for defines in (None, self.definebones):
            text = "".join(qc.base_qc_lines(
                self.plan, self.source, include_definebones=defines, for_definebone_capture=True
            ))
            self.assertNotIn("mci_foot_ik_", text)
            self.assertIn('$ikchain "rfoot" "ValveBiped.Bip01_R_Foot"', text)
            self.assertIn('$ikchain "lfoot" "ValveBiped.Bip01_L_Foot"', text)

    def test_gmod_rejects_conflicting_helper_bones(self):
        for name in qc.GMOD_FOOT_IK_HELPERS:
            with self.subTest(name=name), self.assertRaisesRegex(RuntimeError, "reserved"):
                qc.base_qc_lines(self.plan, self.source, include_definebones=[f'$definebone "{name}" ""'])

    def test_l4d2_body_retains_survivor_locks_and_origin(self):
        plan = dict(self.plan, game="l4d2", survivor="producer")
        with patch.object(qc, "l4d2_survivor_skeleton_bones", return_value=set()):
            for capture in (False, True):
                with self.subTest(capture=capture):
                    text = "".join(qc.base_qc_lines(
                        plan, self.source, for_definebone_capture=capture,
                        include_definebones=self.definebones,
                    ))
                    self.assertNotIn("mci_foot_ik_", text)
                    self.assertIn('$origin 0 0 -2.50', text)
                    self.assertNotIn('ikrule "rfoot" release', text)
                    self.assertNotIn('ikrule "lfoot" release', text)
                    if capture:
                        self.assertNotIn("$ikautoplaylock", text)
                    else:
                        self.assertIn('$ikautoplaylock "rfoot" 1 0.1', text)
                        self.assertIn('$ikautoplaylock "lfoot" 1 0.1', text)

    def test_sfm_retains_static_idle(self):
        text = "".join(qc.base_qc_lines(dict(self.plan, game="sfm"), self.source))
        self.assertIn('$sequence "idle"', text)
        self.assertNotIn("$ikchain", text)
        self.assertNotIn("autoplay", text)
        self.assertNotIn("$origin", text)

    def test_gmod_first_person_arms_keep_their_existing_alignment(self):
        arms = self.source / "step10"
        arms.mkdir()
        (arms / "arms.smd").touch()
        plan = dict(self.plan, game="gmod", inputs={"step10_dir": str(arms)})
        path = qc.build_carms_qc(plan, self.source, [])
        self.assertIsNotNone(path)
        text = path.read_text(encoding="utf-8")
        self.assertIn('$ikautoplaylock "rfoot" 0.7 0.1', text)
        self.assertIn('$ikautoplaylock "lfoot" 0.7 0.1', text)
        self.assertIn('$origin 0 0 -2.40', text)
        self.assertNotIn('ikrule "rfoot" release', text)

    def test_gmod_material_uses_the_bundled_toon_lighting(self):
        path = self.source / "body.vmt"
        qc.write_vmt(path, "test", "grounding", "body", False)
        text = path.read_text(encoding="utf-8")
        self.assertIn('$bumpmap "models/test/shared/normal"', text)
        self.assertIn('$lightwarptexture "models/test/shared/lightwarptexture"', text)
        self.assertIn('$phongexponenttexture "models/test/shared/phong_exp"', text)
        self.assertIn('$phong "1"', text)
        self.assertIn('$rimlight "1"', text)

    def test_gmod_material_keeps_its_supplied_normal_and_exponent_maps(self):
        path = self.source / "body.vmt"
        qc.write_vmt(path, "test", "grounding", "body", True,
                     normal_name="shared_skin", phongexp_texture="models/test/grounding/skin_exp")
        text = path.read_text(encoding="utf-8")
        self.assertIn('$bumpmap "models/test/grounding/shared_skin_normal"', text)
        self.assertIn('$phongexponenttexture "models/test/grounding/skin_exp"', text)

    def test_other_games_keep_their_material_lighting(self):
        path = self.source / "body.vmt"
        for game in ("l4d2", "sfm"):
            with self.subTest(game=game):
                qc.write_vmt(path, "test", "grounding", "body", False, game=game)
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("$lightwarptexture", text)
                self.assertNotIn("$phong", text)
                self.assertNotIn("$rimlight", text)


if __name__ == "__main__":
    unittest.main()
