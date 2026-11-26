"""Persistent CMYK stage navigation and control-state helpers."""

import os
import sys
import unittest
from pathlib import Path


os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PySide6.QtWidgets import (  # noqa: E402
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from generator_tabs.cmyk_workflow import (  # noqa: E402
    CMYK_WORKFLOW_STAGES,
    CmykStageNavigator,
    control_state,
    restore_control_state,
)


class CmykWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_navigation_emits_stage_and_click_events(self):
        navigator = CmykStageNavigator(CMYK_WORKFLOW_STAGES)
        self.addCleanup(navigator.deleteLater)
        changed = []
        clicked = []
        navigator.stage_changed.connect(changed.append)
        navigator.stage_clicked.connect(clicked.append)

        self.assertEqual(navigator.current_stage, "composition")
        navigator.next_stage()
        self.assertEqual(navigator.current_stage, "prepare")
        self.assertEqual(changed, ["prepare"])
        navigator._buttons["direction"].click()
        self.assertEqual(navigator.current_stage, "direction")
        self.assertEqual(clicked, ["direction"])
        self.assertEqual(changed, ["prepare", "direction"])
        navigator.previous_stage()
        self.assertEqual(navigator.current_stage, "separation")
        for stage in CMYK_WORKFLOW_STAGES:
            self.assertTrue(stage.input_contract)
            self.assertTrue(stage.output_contract)
            self.assertTrue(stage.validation)
            self.assertTrue(stage.cache_dependencies)

    def test_lock_is_per_stage_and_signal_fires(self):
        navigator = CmykStageNavigator(CMYK_WORKFLOW_STAGES)
        self.addCleanup(navigator.deleteLater)
        updates = []
        navigator.lock_changed.connect(
            lambda key, value: updates.append((key, value))
        )
        navigator.set_stage("streamlines")
        navigator.lock_box.setChecked(True)
        self.assertTrue(navigator.is_locked("streamlines"))
        self.assertFalse(navigator.is_locked("direction"))
        navigator.set_stage("direction")
        self.assertFalse(navigator.lock_box.isChecked())
        navigator.set_stage("streamlines")
        self.assertTrue(navigator.lock_box.isChecked())
        self.assertEqual(updates, [("streamlines", True)])

    def test_control_snapshot_restores_structural_state(self):
        root = QWidget()
        self.addCleanup(root.deleteLater)
        QVBoxLayout(root)
        check = QCheckBox("Enabled")
        check.setChecked(True)
        combo = QComboBox()
        combo.addItem("First", "first")
        combo.addItem("Second", "second")
        number = QDoubleSpinBox()
        number.setValue(2.5)
        button = QPushButton("Preset")
        button.setCheckable(True)
        button.setChecked(True)
        for widget in (check, combo, number, button):
            root.layout().addWidget(widget)

        snapshot = control_state(root)
        check.setChecked(False)
        combo.setCurrentIndex(1)
        number.setValue(9.0)
        button.setChecked(False)
        restore_control_state(snapshot)

        self.assertTrue(check.isChecked())
        self.assertEqual(combo.currentData(), "first")
        self.assertEqual(number.value(), 2.5)
        self.assertTrue(button.isChecked())


if __name__ == "__main__":
    unittest.main()
