"""Stage navigation and reusable state handling for the CMYK workspace."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)


@dataclass(frozen=True)
class CmykWorkflowStage:
    """One operator-facing stage over the existing conversion pipeline."""

    key: str
    title: str
    short_title: str
    description: str
    group_titles: tuple[str, ...]
    diagnostic_label: str
    input_contract: str
    output_contract: str
    validation: str
    cache_dependencies: tuple[str, ...]


CMYK_WORKFLOW_STAGES = (
    CmykWorkflowStage(
        "composition",
        "Composition and placement",
        "Compose",
        "Choose the artwork and place its physical page on the registered bed "
        "frame. All four inks inherit this page and registration setup.",
        ("Image", "Page"),
        "Show source",
        "Source artwork; page dimensions; artwork placement; registration mode.",
        "One common paper-space frame and physical page placement.",
        "Artwork exists, page is positive, and placement is finite.",
        ("artwork path", "page", "placement", "registration"),
    ),
    CmykWorkflowStage(
        "prepare",
        "Color-managed image preparation",
        "Prepare",
        "Set levels, exposure, color strength, and sharpening before process "
        "ink separation. Automatic adjustments can be locked at this stage.",
        ("Image options",),
        "Show adjusted source",
        "Source RGB image and color-management controls.",
        "Prepared scene tones and edge-preserving source guide.",
        "Image dimensions, orientation, channel range, and alpha compositing.",
        ("artwork path", "levels", "exposure", "contrast", "saturation",
         "sharpening"),
    ),
    CmykWorkflowStage(
        "separation",
        "Calibrated CMYK separation",
        "Separate",
        "Resolve process-ink coverage against the loaded ink profile. Keep "
        "ink gamma, black generation, resolution, and per-ink weights together.",
        ("Ink separation",),
        "Show ink channels",
        "Prepared RGB guide, measured or default ink response, GCR and weights.",
        "C/M/Y/K coverage fields plus common scene-depth support.",
        "Finite [0,1] channel fields and one calibration identity.",
        ("prepared image", "ink profile", "gamma", "GCR", "weights",
         "resolution"),
    ),
    CmykWorkflowStage(
        "direction",
        "Structure-tensor direction field",
        "Direction",
        "Smooth the multichannel image field before tracing. This controls "
        "contour scale, edge confidence, and how quickly weak texture falls "
        "back to fixed screen angles, plus where additional shadow layers "
        "activate for streamline styles.",
        ("Flow geometry",),
        "Show flow field",
        "Multichannel image guide, page geometry, and smoothing radius.",
        "Undirected tangent field, guidance confidence, and keyline confidence.",
        "Finite normalized vectors, repeatable tensor components, and stable "
        "opposite-direction colours.",
        ("flow guide", "page geometry", "smoothing", "shadow thresholds",
         "tensor constants"),
    ),
    CmykWorkflowStage(
        "streamlines",
        "Screen geometry and spacing",
        "Geometry",
        "Choose the complete geometry style, base pitch, and density behavior. "
        "Adaptive styles trace streamlines; the precision process screen uses "
        "pen-footprint area cells.",
        ("Screening",),
        "Show paths",
        "Direction field, coverage support, pitch, layers, and compression.",
        "Deterministic screen marks or shared streamline candidates and their "
        "occupancy spacing.",
        "Bounds, pen-safe pitch, deterministic seeds, and mark cap.",
        ("direction field", "style", "pitch", "layers", "compression", "seed"),
    ),
    CmykWorkflowStage(
        "ink",
        "Ink assignment and local coverage",
        "Ink planes",
        "Review how coverage becomes process-ink cells or local ink planes: "
        "keyline policy, edge separation, ink-plane hold and secondary mix, "
        "dot size, overdraw, pen width, and density levels.",
        ("Ink assignment",),
        "Show ink simulation",
        "Streamline geometry, local channel coverage, keyline and pen policy.",
        "Independent tagged polylines for Yellow, Magenta, Cyan, and Black.",
        "Ink planes are continuous where supported and deterministic phase "
        "gates remain bounded.",
        ("streamline paths", "coverage fields", "keylines", "edge separation",
         "ink-plane hold", "secondary mix", "pen width", "overdraw"),
    ),
    CmykWorkflowStage(
        "paths",
        "Path simplification, chaining, and order",
        "Paths",
        "Control path fidelity, local tone-gap bridging, adjacent pen-down "
        "joining, deterministic limits, and the row/chaining policy that "
        "changes M3/M5 count and visible bridges.",
        ("Path and continuity",),
        "Show path plan",
        "Per-ink marks, path tolerance, deterministic limit, and chain policy.",
        "Simplified, ordered contours and visible connector decisions.",
        "Tolerance, mark cap, and chain gap are respected before planning.",
        ("marks", "path tolerance", "tone bridge", "chain gap", "row order",
         "seed", "maximum marks"),
    ),
    CmykWorkflowStage(
        "motion",
        "Machine motion and alignment",
        "Motion",
        "Select XY-only or XY-Theta planning, centre handling, and per-pen "
        "alignment. Motion preflight remains mandatory before publication.",
        ("Kinematics", "Pen alignment"),
        "Motion preflight",
        "Ordered contours, page frame, XY-only/XTheta contract, and pen offsets.",
        "One planned G-code program per ink with machine-compensation applied "
        "once.",
        "Bed step, A rate, bare rapids, reach, and common set identity.",
        ("ordered contours", "theta mode", "center hold", "pen offsets",
         "feed limits", "compensation"),
    ),
    CmykWorkflowStage(
        "review",
        "Review, validation, and export",
        "Review",
        "Choose preview inks, calibration behavior, and the coordinated "
        "four-file export. A successful save publishes programs and manifest "
        "together.",
        ("Recommended", "Layers", "Calibration", "G-code (4 files)"),
        "Print simulation",
        "Four verified programs plus the complete recipe and calibration "
        "identity.",
        "One published program-and-manifest set in Y/M/C/K order.",
        "Complete channels, shared program identity, hashes, and transactional "
        "publication.",
        ("program bytes", "preflight", "set identity", "manifest",
         "destination"),
    ),
)

CMYK_RECIPE_PRESETS = (
    ("Recommended coherent portrait", "recommended"),
    ("Precision process-color screen", "process_area"),
    ("Per-ink Edge-flow comparison", "edge_flow_per_ink"),
    ("Stochastic shared flow experiment", "edge_flow_shared"),
    ("Line-screen speed comparison", "line_screen"),
)


def _widget_state(widget):
    if isinstance(widget, QCheckBox):
        return ("checked", bool(widget.isChecked()))
    if isinstance(widget, QPushButton) and widget.isCheckable():
        return ("button_checked", bool(widget.isChecked()))
    if isinstance(widget, QComboBox):
        return ("combo", widget.currentData())
    if isinstance(widget, (QSpinBox, QDoubleSpinBox)):
        return ("number", widget.value())
    if isinstance(widget, QLineEdit):
        return ("text", widget.text())
    if hasattr(widget, "value") and hasattr(widget, "set_value"):
        return ("choice", widget.value())
    return None


def _set_widget_state(widget, state):
    kind, value = state
    if kind == "checked":
        widget.setChecked(bool(value))
    elif kind == "button_checked":
        widget.setChecked(bool(value))
    elif kind == "combo":
        index = widget.findData(value)
        if index >= 0:
            widget.setCurrentIndex(index)
    elif kind == "number":
        widget.setValue(value)
    elif kind == "text":
        widget.setText(str(value))
    elif kind == "choice":
        widget.set_value(value)


def control_state(root):
    """Capture resettable control state beneath one widget."""
    states = {}
    for widget in root.findChildren(QWidget):
        state = _widget_state(widget)
        if state is not None:
            states[widget] = state
    return states


def restore_control_state(states):
    """Restore a prior ``control_state`` snapshot."""
    for widget, state in states.items():
        try:
            _set_widget_state(widget, state)
        except (RuntimeError, TypeError, ValueError):
            continue


class CmykStageNavigator(QWidget):
    """Compact persistent stage rail, lock, reset, and next/previous controls."""

    stage_changed = Signal(str)
    stage_clicked = Signal(str)
    reset_requested = Signal(str)
    lock_changed = Signal(str, bool)
    diagnostic_requested = Signal(str)
    recipe_applied = Signal(str)

    def __init__(self, stages, recipes=(), parent=None):
        super().__init__(parent)
        self.stages = tuple(stages)
        self._stage_by_key = {
            stage.key: stage
            for stage in self.stages
        }
        self._buttons = {}
        self._locked = set()
        self._current_key = self.stages[0].key if self.stages else ""

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(6)

        frame = QFrame()
        frame.setObjectName("cmykWorkflowRail")
        frame.setStyleSheet(
            "QFrame#cmykWorkflowRail {"
            "  background: palette(base);"
            "  border: 1px solid palette(mid);"
            "  border-radius: 8px;"
            "}"
            "QPushButton[cmykStage='true'] {"
            "  text-align: left;"
            "  padding: 6px 8px;"
            "  border-radius: 5px;"
            "}"
            "QPushButton[cmykStage='true']:checked {"
            "  background: palette(highlight);"
            "  color: palette(highlighted-text);"
            "  font-weight: 600;"
            "}"
        )
        body = QVBoxLayout(frame)
        body.setContentsMargins(9, 8, 9, 8)
        body.setSpacing(6)

        heading = QLabel("Adaptive CMYK workflow")
        heading.setStyleSheet("font-weight: 700;")
        body.addWidget(heading)

        recipe_row = QHBoxLayout()
        recipe_row.setSpacing(4)
        self.recipe_combo = QComboBox()
        for label, key in recipes:
            self.recipe_combo.addItem(label, key)
        self.recipe_combo.setToolTip(
            "Apply a complete starting recipe. Locked stages keep their "
            "current manual values."
        )
        self.recipe_button = QPushButton("Apply recipe")
        recipe_row.addWidget(self.recipe_combo, 1)
        recipe_row.addWidget(self.recipe_button)
        body.addLayout(recipe_row)
        self.recipe_button.clicked.connect(
            lambda: self.recipe_applied.emit(
                str(self.recipe_combo.currentData() or "")
            )
        )

        grid = QGridLayout()
        grid.setHorizontalSpacing(4)
        grid.setVerticalSpacing(4)
        for index, stage in enumerate(self.stages):
            button = QPushButton(
                f"{index + 1}. {stage.short_title}"
            )
            button.setCheckable(True)
            button.setAutoExclusive(True)
            button.setProperty("cmykStage", True)
            button.setToolTip(stage.title)
            button.clicked.connect(
                lambda _checked=False, key=stage.key: self._on_stage_button(key)
            )
            grid.addWidget(button, index // 3, index % 3)
            self._buttons[stage.key] = button
        body.addLayout(grid)

        self.stage_title = QLabel()
        self.stage_title.setStyleSheet("font-weight: 600;")
        self.stage_title.setWordWrap(True)
        body.addWidget(self.stage_title)
        self.stage_description = QLabel()
        self.stage_description.setWordWrap(True)
        self.stage_description.setStyleSheet("color: palette(mid);")
        body.addWidget(self.stage_description)

        actions = QHBoxLayout()
        actions.setSpacing(4)
        self.previous_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.reset_button = QPushButton("Reset stage")
        self.lock_box = QCheckBox("Lock auto")
        self.lock_box.setToolTip(
            "Keep this stage's manual values when a recommended preset or "
            "automatic image adjustment is applied."
        )
        self.diagnostic_button = QPushButton()
        actions.addWidget(self.previous_button)
        actions.addWidget(self.next_button)
        actions.addWidget(self.reset_button)
        actions.addWidget(self.lock_box)
        actions.addWidget(self.diagnostic_button, 1)
        body.addLayout(actions)

        self.previous_button.clicked.connect(self.previous_stage)
        self.next_button.clicked.connect(self.next_stage)
        self.reset_button.clicked.connect(
            lambda: self.reset_requested.emit(self._current_key)
        )
        self.lock_box.toggled.connect(self._on_lock_changed)
        self.diagnostic_button.clicked.connect(
            lambda: self.diagnostic_requested.emit(self._current_key)
        )
        outer.addWidget(frame)
        self.set_stage(self._current_key, emit=False)

    @property
    def current_stage(self):
        return self._current_key

    @property
    def locked_stages(self):
        return tuple(
            stage.key
            for stage in self.stages
            if stage.key in self._locked
        )

    def set_stage(self, key, emit=True):
        if key not in self._stage_by_key:
            return False
        changed = key != self._current_key
        self._current_key = key
        stage = self._stage_by_key[key]
        button = self._buttons[key]
        if not button.isChecked():
            button.setChecked(True)
        self.stage_title.setText(stage.title)
        self.stage_description.setText(stage.description)
        self.diagnostic_button.setText(stage.diagnostic_label)
        index = self.stages.index(stage)
        self.previous_button.setEnabled(index > 0)
        self.next_button.setEnabled(index + 1 < len(self.stages))
        self.lock_box.blockSignals(True)
        self.lock_box.setChecked(key in self._locked)
        self.lock_box.blockSignals(False)
        if emit and changed:
            self.stage_changed.emit(key)
        return True

    def previous_stage(self):
        index = next(
            (
                index
                for index, stage in enumerate(self.stages)
                if stage.key == self._current_key
            ),
            0,
        )
        if index > 0:
            self.set_stage(self.stages[index - 1].key)

    def _on_stage_button(self, key):
        self.set_stage(key)
        self.stage_clicked.emit(key)

    def next_stage(self):
        index = next(
            (
                index
                for index, stage in enumerate(self.stages)
                if stage.key == self._current_key
            ),
            len(self.stages) - 1,
        )
        if index + 1 < len(self.stages):
            self.set_stage(self.stages[index + 1].key)

    def set_locked(self, key, locked):
        if key not in self._stage_by_key:
            return
        if locked:
            self._locked.add(key)
        else:
            self._locked.discard(key)
        if key == self._current_key:
            self.lock_box.blockSignals(True)
            self.lock_box.setChecked(bool(locked))
            self.lock_box.blockSignals(False)

    def is_locked(self, key):
        return key in self._locked

    def _on_lock_changed(self, checked):
        if not self._current_key:
            return
        if checked:
            self._locked.add(self._current_key)
        else:
            self._locked.discard(self._current_key)
        self.lock_changed.emit(self._current_key, bool(checked))
