"""Layers tab: split an imported SVG by paint colour.

Concept ported from the MIT-licensed jdbrande/Svg-Layer-Painter
(https://github.com/jdbrande/Svg-Layer-Painter): drawable elements are grouped
by stroke (or fill) colour and each group is written as its own SVG, so a
multi-pen artwork can be plotted one colour at a time. The tab's layer combo
selects which layer the shared preview loads; "All colours" uses the original
file.
"""

from __future__ import annotations

import copy
import os
import xml.etree.ElementTree as ET

from PySide6.QtWidgets import QComboBox, QLabel, QPushButton

from ._tab_common import GeneratorTab, write_svg_document


TITLE = "Layers"
ORDER = 160

DRAWABLE = {"path", "line", "polyline", "polygon", "rect", "circle", "ellipse"}


def _drawable_elements(root):
    return [
        element
        for element in root.iter()
        if element.tag.split("}")[-1] in DRAWABLE
    ]


def _paint_key(element):
    stroke = element.get("stroke")
    fill = element.get("fill")
    if stroke and stroke.strip().lower() != "none":
        return stroke.strip()
    if fill and fill.strip().lower() != "none":
        return fill.strip()
    return "default"


def svg_layer_groups(svg_path):
    """Return ``[(paint, [drawable indices])]`` in document order."""
    root = ET.parse(svg_path).getroot()
    groups = {}
    for index, element in enumerate(_drawable_elements(root)):
        groups.setdefault(_paint_key(element), []).append(index)
    return list(groups.items())


def write_layer_svg(tree, indices, name="layer"):
    """Write a copy of *tree* containing only the given drawable indices."""
    root = copy.deepcopy(tree.getroot())
    elements = _drawable_elements(root)
    parents = {child: parent for parent in root.iter() for child in parent}
    keep = set(indices)
    for index in range(len(elements) - 1, -1, -1):
        if index in keep:
            continue
        parent = parents.get(elements[index])
        if parent is not None:
            parent.remove(elements[index])
    document = ET.tostring(root, encoding="unicode")
    if not document.startswith("<?xml"):
        document = '<?xml version="1.0" encoding="UTF-8"?>\n' + document
    return str(write_svg_document(name, document))


class LayersTab(GeneratorTab):
    NAME = "layers"
    GROUP = "Photo-based"
    DESCRIPTION = "Split an imported SVG into one file per pen colour."

    def __init__(self, host):
        super().__init__(host)
        layers = self.add_group("Layers")
        self.artwork_label = QLabel()
        self.artwork_label.setWordWrap(True)
        layers.addRow("Artwork", self.artwork_label)
        self.layer = QComboBox()
        layers.addRow("Layer", self.layer)
        self.use_button = QPushButton("Use layer in Convert")
        self.use_button.clicked.connect(self._use_layer)
        layers.addRow("", self.use_button)

        self._tree = None
        self._layers = []
        self._paths = []
        self.finish_controls()

    def showEvent(self, event):
        super().showEvent(event)
        self._refresh_artwork()

    def _refresh_artwork(self):
        path = ""
        if self.host is not None and hasattr(self.host, "artwork_path"):
            path = self.host.artwork_path()
        self._artwork = path
        self.artwork_label.setText(
            os.path.basename(path) if path else "(use File > Open Artwork)"
        )

    def _build_layers(self):
        self._refresh_artwork()
        if not self._artwork or not os.path.exists(self._artwork):
            raise ValueError("Open an SVG with File > Open Artwork first.")
        tree = ET.parse(self._artwork)
        groups = svg_layer_groups(self._artwork)
        self._tree = tree
        self._layers = groups
        self._paths = [
            write_layer_svg(tree, indices, f"layer-{index}")
            for index, (_paint, indices) in enumerate(groups)
        ]
        current = self.layer.currentIndex()
        self.layer.blockSignals(True)
        self.layer.clear()
        self.layer.addItem("All colours (original)", self._artwork)
        for paint, indices in groups:
            self.layer.addItem(
                f"{paint} ({len(indices)} elements)",
                None,
            )
        self.layer.setCurrentIndex(min(max(current, 0), self.layer.count() - 1))
        self.layer.blockSignals(False)

    def _selected_path(self):
        index = self.layer.currentIndex()
        if index <= 0:
            return self._artwork
        return self._paths[index - 1]

    def _use_layer(self):
        try:
            path = self._selected_path()
        except Exception as exc:  # noqa: BLE001
            self.report_error(str(exc))
            return
        if self.host is not None:
            self.host.adopt_artwork(path)

    def build_svg(self):
        self._build_layers()
        return self._selected_path()


def create_tab(host):
    return LayersTab(host)
