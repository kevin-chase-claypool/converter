"""Postcard layout generator tab.

Layout concept re-implemented from the Unlicense-licensed
cadin/plotter-postcard (https://github.com/cadin/plotter-postcard): a
plottable postcard back with border, divider, stamp box, address guide lines,
and optional caption/address text drawn with the shared monoline font.
"""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLineEdit,
    QPlainTextEdit,
)

from ._hershey import text_polylines
from ._tab_common import GeneratorTab, double_spin, int_spin, scale_polylines


TITLE = "Postcard"
ORDER = 90

PAGE_PRESETS = (
    ("5x7 in (127 x 178 mm)", 127.0, 177.8),
    ("A6 (105 x 148 mm)", 105.0, 148.0),
    ("A5 (148 x 210 mm)", 148.0, 210.0),
    ("Square 140 mm", 140.0, 140.0),
)


def postcard_polylines(
    width_mm=127.0,
    height_mm=177.8,
    margin_mm=8.0,
    line_spacing_mm=9.0,
    address_lines=4,
    stamp_width_mm=25.0,
    stamp_height_mm=30.0,
    divider=True,
    caption="",
    message="",
    address="",
    text_size_mm=5.0,
    tracking_mm=0.2,
    scale_pct=100.0,
):
    """Return the postcard layout as plotter polylines."""
    width_mm = max(40.0, float(width_mm))
    height_mm = max(40.0, float(height_mm))
    margin = max(2.0, min(float(margin_mm), min(width_mm, height_mm) / 4.0))
    spacing = max(3.0, float(line_spacing_mm))
    stamp_w = max(5.0, float(stamp_width_mm))
    stamp_h = max(5.0, float(stamp_height_mm))
    paths = [
        [
            (margin, margin),
            (width_mm - margin, margin),
            (width_mm - margin, height_mm - margin),
            (margin, height_mm - margin),
            (margin, margin),
        ]
    ]
    divider_x = width_mm * 0.52
    if divider:
        paths.append([(divider_x, margin), (divider_x, height_mm - margin)])
    stamp_x = width_mm - margin - stamp_w
    paths.append(
        [
            (stamp_x, margin),
            (stamp_x + stamp_w, margin),
            (stamp_x + stamp_w, margin + stamp_h),
            (stamp_x, margin + stamp_h),
            (stamp_x, margin),
        ]
    )
    address_x0 = divider_x + 4.0
    address_x1 = width_mm - margin - 3.0
    first_line_y = margin + stamp_h + spacing
    lines = max(1, int(address_lines))
    for index in range(lines):
        y = first_line_y + index * spacing
        if y > height_mm - margin - 2.0:
            break
        paths.append([(address_x0, y), (address_x1, y)])
    address_text = [line for line in address.split("\n") if line.strip()][:lines]
    for index, line in enumerate(address_text):
        y = first_line_y + index * spacing - 1.5
        paths.extend(
            text_polylines(
                line,
                address_x0,
                y,
                text_size_mm,
                tracking_mm=tracking_mm,
                align="left",
            )
        )
    if caption.strip():
        paths.extend(
            text_polylines(
                caption.strip(),
                margin + 3.0,
                height_mm - margin - 3.0,
                text_size_mm,
                tracking_mm=tracking_mm,
                align="left",
            )
        )
    message_lines = [line for line in message.split("\n") if line.strip()]
    if message_lines:
        message_y = margin + 10.0
        for line in message_lines:
            if message_y > height_mm - margin - 6.0:
                break
            paths.extend(
                text_polylines(
                    line,
                    margin + 3.0,
                    message_y,
                    text_size_mm,
                    tracking_mm=tracking_mm,
                    align="left",
                )
            )
            message_y += spacing
    return scale_polylines(
        paths, float(scale_pct) / 100.0, width_mm, height_mm
    )


class PostcardTab(GeneratorTab):
    NAME = "postcard"

    def __init__(self, host):
        super().__init__(host)
        layout = self.add_group("Layout")
        self.preset = QComboBox()
        for label, width, height in PAGE_PRESETS:
            self.preset.addItem(label, (width, height))
        layout.addRow("Page preset", self.preset)
        self.divider = QCheckBox("Centre divider")
        self.divider.setChecked(True)
        layout.addRow("", self.divider)
        self.address_lines = int_spin(4, 1, 8)
        layout.addRow("Address lines", self.address_lines)
        self.line_spacing = double_spin(9.0, 4.0, 20.0, 0.5, 1, " mm")
        layout.addRow("Line spacing", self.line_spacing)
        self.stamp_w = double_spin(25, 10, 60, 1, 0, " mm")
        layout.addRow("Stamp width", self.stamp_w)
        self.stamp_h = double_spin(30, 10, 60, 1, 0, " mm")
        layout.addRow("Stamp height", self.stamp_h)

        text = self.add_group("Text")
        self.caption = QLineEdit()
        text.addRow("Caption", self.caption)
        self.message = QPlainTextEdit()
        self.message.setFixedHeight(60)
        text.addRow("Message", self.message)
        self.address = QPlainTextEdit()
        self.address.setFixedHeight(60)
        text.addRow("Address", self.address)
        self.text_size = double_spin(5.0, 3.0, 12.0, 0.5, 1, " mm")
        text.addRow("Text size", self.text_size)
        self.tracking = double_spin(0.2, -1.0, 4.0, 0.1, 2, " mm")
        text.addRow("Tracking", self.tracking)

        page = self.add_group("Page")
        self.page_w = double_spin(127, 40, 1000, 5, 1, " mm")
        page.addRow("Width", self.page_w)
        self.page_h = double_spin(177.8, 40, 1000, 5, 1, " mm")
        page.addRow("Height", self.page_h)
        self.margin = double_spin(8, 2, 40, 1, 0, " mm")
        page.addRow("Margin", self.margin)
        self.line_width = double_spin(0.3, 0.1, 1.2, 0.05, 2, " mm")
        page.addRow("Line width", self.line_width)
        self.scale_pct = double_spin(100, 10, 1000, 5, 0, " %")
        page.addRow("Artwork scale", self.scale_pct)

        self.preset.currentIndexChanged.connect(self._apply_preset)
        self.finish_controls()

    def _apply_preset(self):
        size = self.preset.currentData()
        if size:
            self.page_w.setValue(size[0])
            self.page_h.setValue(size[1])

    def build_svg(self):
        polylines = postcard_polylines(
            width_mm=self.page_w.value(),
            height_mm=self.page_h.value(),
            margin_mm=self.margin.value(),
            line_spacing_mm=self.line_spacing.value(),
            address_lines=self.address_lines.value(),
            stamp_width_mm=self.stamp_w.value(),
            stamp_height_mm=self.stamp_h.value(),
            divider=self.divider.isChecked(),
            caption=self.caption.text(),
            message=self.message.toPlainText(),
            address=self.address.toPlainText(),
            text_size_mm=self.text_size.value(),
            tracking_mm=self.tracking.value(),
            scale_pct=self.scale_pct.value(),
        )
        return self.write_result(
            polylines,
            self.page_w.value(),
            self.page_h.value(),
            self.line_width.value(),
            f"Postcard layout, {len(polylines)} paths.",
        )


def create_tab(host):
    return PostcardTab(host)
