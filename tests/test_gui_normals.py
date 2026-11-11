import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
try:
    from PySide6 import QtCore, QtWidgets
except ImportError:
    raise unittest.SkipTest("GUI checks require the PySide6 build dependency")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import mmd_character_importer_gui as gui


class NormalSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        settings_class = QtCore.QSettings
        settings_path = str(Path(self.folder.name) / "settings.ini")
        self.settings = settings_class(settings_path, settings_class.Format.IniFormat)
        factory = lambda *args: settings_class(settings_path, settings_class.Format.IniFormat)
        self.settings_patch = patch.object(QtCore, "QSettings", factory)
        self.settings_patch.start()
        self.addCleanup(self.settings_patch.stop)

    def make_window(self):
        window = gui.ImporterWindow()
        self.addCleanup(window.close)
        self.assertEqual(Path(window.settings_store.fileName()), Path(self.settings.fileName()))
        return window

    def test_fresh_settings_preserve_custom_normals_in_both_entry_points(self):
        window = self.make_window()
        self.assertFalse(window.main_clear_custom_normals_enabled())
        self.assertFalse(window.fix_clear_custom_normals_enabled())

    def test_startup_honors_the_saved_clearing_preference(self):
        self.settings.setValue("main_clear_custom_normals", True)
        self.settings.sync()
        window = self.make_window()
        self.assertTrue(window.main_clear_custom_normals_enabled())


if __name__ == "__main__":
    unittest.main()
