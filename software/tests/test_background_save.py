"""Exact G-code generation must not block the Qt event loop."""

import importlib.util
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    from PySide6.QtWidgets import QApplication

    HAVE_QT = True
except Exception:  # pragma: no cover - the app needs Qt, the core does not
    HAVE_QT = False


def _load_app_module():
    path = Path(__file__).resolve().parents[1] / "qt_svg_to_gcode.pyw"
    spec = importlib.util.spec_from_file_location(
        "qt_svg_to_gcode_background_save_test", path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@unittest.skipUnless(HAVE_QT, "PySide6 is not installed")
class BackgroundSaveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.module = _load_app_module()

    def setUp(self):
        self.window = self.module.MainWindow()
        self.temp_dir = tempfile.TemporaryDirectory(
            prefix="background-save-test-"
        )
        root = Path(self.temp_dir.name)
        self.svg_path = root / "small.svg"
        self.gcode_path = root / "small.gcode"
        self.svg_path.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10">'
            '<path d="M0 0 L10 0"/></svg>',
            encoding="utf-8",
        )
        self.window.svg_path.setText(str(self.svg_path))
        self.window.gcode_path.setText(str(self.gcode_path))
        self.window.fields["bed_compensation_path"].setText(
            str(self.module.converter.DEFAULT_BED_COMPENSATION_PATH)
        )
        self.profile_fingerprint = self.module.converter.load_bed_compensation(
            str(self.module.converter.DEFAULT_BED_COMPENSATION_PATH)
        ).fingerprint

    def _wait_for_save(self, timeout=5.0):
        deadline = time.monotonic() + timeout
        while (
            self.window.save_thread is not None
            and time.monotonic() < deadline
        ):
            self.app.processEvents()
            time.sleep(0.01)
        return self.window.save_thread is None

    def tearDown(self):
        if self.window.save_thread is not None:
            self.window.cancel_save()
            self._wait_for_save()
        self.window.close()
        self.app.processEvents()
        self.temp_dir.cleanup()

    def test_convert_returns_before_exact_gcode_generation_finishes(self):
        def slow_gcode(*_args, **_kwargs):
            time.sleep(0.35)
            return "(background-save test)\nG1 X0 Y0 A0 F700\nM2\n"

        with patch.object(
            self.module.converter,
            "contours_to_gcode",
            side_effect=slow_gcode,
        ), patch.object(
            self.module.QMessageBox, "critical", return_value=None
        ):
            started = time.monotonic()
            self.window.convert()
            convert_elapsed = time.monotonic() - started
            self.assertLess(
                convert_elapsed,
                0.15,
                "convert() must return immediately while the save worker runs",
            )
            self.assertIsNotNone(
                self.window.save_thread,
                "convert() did not start a background save worker",
            )
            self.assertTrue(
                self._wait_for_save(),
                "the background save worker did not finish",
            )

        self.assertTrue(self.gcode_path.exists())
        self.assertIn("G1", self.gcode_path.read_text(encoding="utf-8"))

    def test_save_worker_writes_the_exact_compensated_program(self):
        with patch.object(
            self.module.QMessageBox, "critical", return_value=None
        ):
            self.window.convert()
            self.assertTrue(
                self._wait_for_save(),
                "the background save worker did not finish",
            )

        gcode = self.gcode_path.read_text(encoding="utf-8")
        self.assertIn(
            f"(bed compensation {self.profile_fingerprint},",
            gcode,
        )
        self.assertIn("M2", gcode)


if __name__ == "__main__":
    unittest.main()
