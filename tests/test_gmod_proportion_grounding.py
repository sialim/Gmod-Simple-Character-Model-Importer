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

    def test_gmod_body_keeps_proportion_height_for_both_animation_sets(self):
        # Missing game keys occur in saved plans from older importer versions.
        for game in (None, "gmod"):
            for gender in ("female", "male"):
                for player in (False, True):
                    with self.subTest(game=game, gender=gender, player=player):
                        plan = dict(self.plan, gender=gender)
                        if game is not None:
                            plan["game"] = game
                        text = "".join(qc.base_qc_lines(plan, self.source, pm=player))
                        self.assertNotIn("$ikautoplaylock", text)
                        self.assertNotIn("$origin", text)
                        for side in ("r", "l"):
                            self.assertIn(f'$ikchain "{side}foot"', text)
                        self.assertIn(f'$sequence reference "anims/reference_{gender}"', text)
                        self.assertIn('subtract reference 0', text)
                        self.assertIn('$sequence proportions a_proportions predelta autoplay', text)

    def test_l4d2_body_retains_survivor_locks_and_origin(self):
        plan = dict(self.plan, game="l4d2", survivor="producer")
        with patch.object(qc, "l4d2_survivor_skeleton_bones", return_value=set()):
            for capture in (False, True):
                with self.subTest(capture=capture):
                    text = "".join(qc.base_qc_lines(
                        plan, self.source, for_definebone_capture=capture
                    ))
                    self.assertIn('$origin 0 0 -2.50', text)
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


if __name__ == "__main__":
    unittest.main()
