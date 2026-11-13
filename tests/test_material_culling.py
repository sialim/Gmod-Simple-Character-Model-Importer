import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import sort_param_textures as textures
import sort_qc_compile as qc


class MaterialCullingTests(unittest.TestCase):
    def test_older_workspaces_render_dress_and_baked_cloth_backfaces(self):
        with tempfile.TemporaryDirectory() as directory:
            vmt = Path(directory) / "test.vmt"
            for name in ("cloth", "clothatlas", "clothdith", "Dress_Lace", "Outfit00", "hair", "cf_m_sk_00"):
                with self.subTest(material=name):
                    qc.write_vmt(vmt, "test", "model", name, False)
                    text = vmt.read_text()
                    self.assertIn("$nocull 1", text)
                    self.assertIn("$alphatest 1", text)
                    self.assertNotIn("$translucent", text)
            qc.write_vmt(vmt, "test", "model", "body", False)
            self.assertNotIn("$nocull", vmt.read_text())

    def test_source_culling_setting_takes_precedence_over_the_material_name(self):
        with tempfile.TemporaryDirectory() as directory:
            vmt = Path(directory) / "test.vmt"
            qc.write_vmt(vmt, "test", "model", "mat_group_001", False, two_sided=True)
            self.assertIn("$nocull 1", vmt.read_text())
            qc.write_vmt(vmt, "test", "model", "dress", False, two_sided=False)
            self.assertNotIn("$nocull", vmt.read_text())

    def test_culling_survives_texture_processing_and_shared_texture_export(self):
        with tempfile.TemporaryDirectory() as directory, contextlib.redirect_stdout(io.StringIO()):
            workspace = Path(directory)
            step5 = workspace / "5_sort_materials"
            step5.mkdir()
            base = workspace / "base.png"
            Image.new("RGBA", (8, 8), (180, 140, 200, 255)).save(base)
            mapping = step5 / "materials.json"
            mapping.write_text(json.dumps({"final_materials": [
                {"material_name": "mat_group_001", "base_color_path": str(base), "two_sided": True},
                {"material_name": "dress_shell", "base_color_path": str(base), "two_sided": False},
            ]}))
            step12 = workspace / "12_param_texture_render_materials"
            step12.mkdir()
            plan_path = step12 / "plan.json"
            manifest = step12 / "textures_manifest.json"
            textures.analyze_textures(workspace, step12 / "analysis.json", plan_path)
            textures.process_textures(workspace, plan_path, step12 / "report.json", manifest)
            rows = qc.material_plan_rows(manifest)
            self.assertEqual([row["two_sided"] for row in rows], [True, False])
            plan = {"author": "test", "model_name": "model", "material_rows": rows}
            addon = workspace / "addon"
            with patch.object(qc, "find_vtfcmd", return_value=None):
                qc.compose_materials(plan, addon)
            output = addon / "materials/models/test/model"
            inner = (output / "mat_group_001.vmt").read_text()
            shell = (output / "dress_shell.vmt").read_text()
            self.assertIn("$nocull 1", inner)
            self.assertNotIn("$nocull", shell)
            # Identical textures can share a VTF without sharing culling settings.
            self.assertIn('$basetexture "models/test/model/mat_group_001"', shell)

    def test_legacy_texture_manifest_without_culling_metadata_uses_name_fallback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "textures_manifest.json"
            path.write_text(json.dumps({"textures": [{"material_name": "cloth atlas"}]}))
            row = qc.material_plan_rows(path)[0]
            self.assertIsNone(row["two_sided"])
            vmt = Path(directory) / "clothatlas.vmt"
            qc.write_vmt(vmt, "test", "model", row["output_name"], False, two_sided=row["two_sided"])
            self.assertIn("$nocull 1", vmt.read_text())


if __name__ == "__main__":
    unittest.main()
