"""Split Plotterfun Extended CMYK artwork into registered SVG layers.

The upstream page keeps all four process inks in one SVG and paints each ink
inside a group named ``cyan``, ``magenta``, ``yellow``, or ``black``.  A plot
needs four independent files, but each file must retain the shared page frame
or the converter will auto-fit every layer to its own ink bounds.  This module
therefore keeps the source document attributes and adds the same registration
crosses to every layer.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


SVG_NS = "http://www.w3.org/2000/svg"


@dataclass(frozen=True)
class InkLayer:
    ink: str
    label: str
    order: int

    @property
    def filename_part(self) -> str:
        return f"{self.order:02d}-{self.ink}"


# Physical print order requested by the project owner.  The upstream bundle
# builds channels in C/M/Y/K order; file order is deliberately different.
PRINT_ORDER = (
    InkLayer("yellow", "Yellow", 1),
    InkLayer("magenta", "Magenta", 2),
    InkLayer("cyan", "Cyan", 3),
    InkLayer("black", "Black", 4),
)
CHANNEL_IDS = frozenset(layer.ink for layer in PRINT_ORDER)


class CmykSplitError(ValueError):
    """The captured SVG does not contain a usable CMYK page."""


@dataclass(frozen=True)
class LayerFile:
    ink: str
    label: str
    order: int
    path: Path
    sha256: str
    drawing_elements: int
    registration_elements: int

    @property
    def has_artwork(self) -> bool:
        return self.drawing_elements > 0


@dataclass(frozen=True)
class CmykExport:
    folder: Path
    base_name: str
    manifest_path: Path
    layers: tuple[LayerFile, ...]

    @property
    def missing_inks(self) -> tuple[str, ...]:
        return tuple(
            layer.label for layer in self.layers if not layer.has_artwork
        )


def sanitize_base_name(value: str) -> str:
    """Return a Windows-safe base name without an artwork extension."""
    text = str(value or "").strip()
    if text:
        text = Path(text).stem
    text = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", text)
    text = re.sub(r"\s+", " ", text).strip(" .")
    return text or "plotterfun-extended"


def layer_filename(base_name: str, layer: InkLayer) -> str:
    return f"{sanitize_base_name(base_name)}-{layer.filename_part}.svg"


def manifest_filename(base_name: str) -> str:
    return f"{sanitize_base_name(base_name)}-cmyk-set.json"


def planned_paths(folder: Path, base_name: str) -> tuple[Path, ...]:
    """Return every destination path, in Y/M/C/K order plus the manifest."""
    folder = Path(folder)
    paths = [
        folder / layer_filename(base_name, layer) for layer in PRINT_ORDER
    ]
    paths.append(folder / manifest_filename(base_name))
    return tuple(paths)


def _local_tag(node) -> str:
    return str(node.tag).rsplit("}", 1)[-1]


def _channel_id(node) -> str:
    if _local_tag(node) != "g":
        return ""
    return str(node.get("id") or "").strip().lower()


def _number(value: str | None) -> float | None:
    if not value:
        return None
    match = re.match(
        r"^\s*([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)",
        str(value),
    )
    if not match:
        return None
    try:
        number = float(match.group(1))
    except ValueError:
        return None
    return number if number > 0.0 else None


def _page_box(root) -> tuple[float, float, float, float]:
    view_box = root.get("viewBox")
    if view_box:
        values = re.findall(
            r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?",
            view_box,
        )
        if len(values) == 4:
            try:
                x, y, width, height = (float(item) for item in values)
            except ValueError:
                pass
            else:
                if width > 0.0 and height > 0.0:
                    return x, y, width, height
    width = _number(root.get("width"))
    height = _number(root.get("height"))
    if width is None or height is None:
        raise CmykSplitError(
            "The captured SVG has no usable width, height, and viewBox."
        )
    return 0.0, 0.0, width, height


def _remove_other_channels(node, keep_ink: str) -> None:
    for child in list(node):
        channel = _channel_id(child)
        if channel in CHANNEL_IDS:
            if channel == keep_ink:
                continue
            node.remove(child)
        else:
            _remove_other_channels(child, keep_ink)


def _own_style(node, name: str) -> str | None:
    value = node.get(name)
    if value is not None:
        return str(value)
    for part in str(node.get("style") or "").split(";"):
        if ":" not in part:
            continue
        key, value = part.split(":", 1)
        if key.strip() == name:
            return value.strip()
    return None


def _normalise_layer_paints(node, inherited=None) -> None:
    """Make isolated channel geometry visible to the single-pen parser.

    Plotterfun paints cyan and yellow with the light process colours. The
    converter correctly treats those as near-white ink when the same SVG is
    loaded as ordinary artwork. In a split CMYK set, however, the group name
    already owns the colour decision; every visible mark therefore becomes
    black for geometry parsing so no channel is lost.
    """
    style = dict(inherited or {})
    for name in ("fill", "stroke", "stroke-width"):
        value = _own_style(node, name)
        if value is not None:
            style[name] = value
    if _local_tag(node) in {
        "path",
        "line",
        "polyline",
        "polygon",
        "rect",
        "circle",
        "ellipse",
    }:
        stroke = str(style.get("stroke") or "").strip().lower()
        width = _number(style.get("stroke-width"))
        if stroke and stroke != "none" and (width is None or width > 0.0):
            # The direct attribute intentionally wins in the converter's
            # style resolver even when Plotterfun put the colour in `style`.
            node.set("stroke", "#000000")
        fill = str(style.get("fill") or "").strip().lower()
        if fill and fill != "none" and not fill.startswith("url("):
            node.set("fill", "#000000")
    for child in list(node):
        _normalise_layer_paints(child, style)


def _add_registration_marks(root, layer: InkLayer) -> None:
    x, y, width, height = _page_box(root)
    shortest = min(width, height)
    inset = max(shortest * 0.025, shortest * 0.001)
    half = max(shortest * 0.008, shortest * 0.0005)
    stroke_width = max(shortest * 0.0015, shortest * 0.0001)
    group = ET.SubElement(
        root,
        f"{{{SVG_NS}}}g",
        {
            "id": "theta-registration",
            "data-theta-registration": "true",
            "data-theta-print-order": str(layer.order),
            "fill": "none",
            "stroke": "#000000",
            "stroke-width": f"{stroke_width:.6g}",
        },
    )
    crosses = (
        (x + inset, y + inset),
        (x + width - inset, y + inset),
        (x + inset, y + height - inset),
        (x + width - inset, y + height - inset),
    )
    for cx, cy in crosses:
        for x1, y1, x2, y2 in (
            (cx - half, cy, cx + half, cy),
            (cx, cy - half, cx, cy + half),
        ):
            ET.SubElement(
                group,
                f"{{{SVG_NS}}}line",
                {
                    "x1": f"{x1:.6g}",
                    "y1": f"{y1:.6g}",
                    "x2": f"{x2:.6g}",
                    "y2": f"{y2:.6g}",
                },
            )


def _serialize_svg(root) -> str:
    ET.register_namespace("", SVG_NS)
    body = ET.tostring(
        root,
        encoding="unicode",
        short_empty_elements=True,
    )
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + body + "\n"


def split_cmyk_svg(svg_text: str) -> dict[str, str]:
    """Return four standalone page-registered SVG documents in print order."""
    if not svg_text or "<svg" not in svg_text:
        raise CmykSplitError("The page has no SVG artwork to export.")
    try:
        root = ET.fromstring(svg_text)
    except ET.ParseError as exc:
        raise CmykSplitError(f"The captured SVG is not valid XML: {exc}") from exc
    if _local_tag(root) != "svg":
        raise CmykSplitError("The captured document is not an SVG.")

    channel_groups = [
        node
        for node in root.iter()
        if _channel_id(node) in CHANNEL_IDS
    ]
    if not channel_groups:
        raise CmykSplitError(
            "The SVG has no named CMYK channel groups. Choose CMYK output "
            "in Plotterfun Extended, then let the preview finish."
        )
    # Validate the page before writing any layer.  Refusing an unregistered
    # export is safer than producing four files that each auto-fit differently.
    _page_box(root)

    documents = {}
    for layer in PRINT_ORDER:
        layer_root = copy.deepcopy(root)
        _remove_other_channels(layer_root, layer.ink)
        for node in layer_root.iter():
            if _channel_id(node) == layer.ink:
                node.set("data-theta-ink", layer.ink)
                node.set("data-theta-print-order", str(layer.order))
                node.set("aria-label", f"{layer.label}, print {layer.order} of 4")
        _normalise_layer_paints(layer_root)
        _add_registration_marks(layer_root, layer)
        documents[layer.ink] = _serialize_svg(layer_root)
    return documents


def _channel_drawing_count(root, ink: str) -> int:
    drawable = {
        "path",
        "line",
        "polyline",
        "polygon",
        "rect",
        "circle",
        "ellipse",
    }
    count = 0
    for group in root.iter():
        if _channel_id(group) != ink:
            continue
        count += sum(
            1
            for node in group.iter()
            if _local_tag(node) in drawable
        )
    return count


def _registration_count(root) -> int:
    for group in root.iter():
        if group.get("data-theta-registration") == "true":
            return sum(
                1 for child in list(group) if _local_tag(child) == "line"
            )
    return 0


def write_cmyk_svg_set(
    svg_text: str,
    folder: Path,
    *,
    base_name: str = "plotterfun-extended",
    source_artwork: str = "",
    algorithm: str = "",
    created_utc: str | None = None,
) -> CmykExport:
    """Write four standalone SVGs and a manifest into *folder*."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    base_name = sanitize_base_name(base_name)
    documents = split_cmyk_svg(svg_text)
    layer_files = []
    page_root = ET.fromstring(svg_text)
    page_box = _page_box(page_root)

    for layer in PRINT_ORDER:
        document = documents[layer.ink]
        path = folder / layer_filename(base_name, layer)
        payload = document.encode("utf-8")
        path.write_bytes(payload)
        layer_root = ET.fromstring(document)
        layer_files.append(
            LayerFile(
                ink=layer.ink,
                label=layer.label,
                order=layer.order,
                path=path,
                sha256=hashlib.sha256(payload).hexdigest(),
                drawing_elements=_channel_drawing_count(
                    layer_root,
                    layer.ink,
                ),
                registration_elements=_registration_count(layer_root),
            )
        )

    created = created_utc or datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )
    manifest = {
        "kind": "theta-plotterfun-cmyk-svg-set",
        "version": 1,
        "created_utc": created,
        "base_name": base_name,
        "source_artwork": str(source_artwork or ""),
        "algorithm": str(algorithm or ""),
        "print_order": [layer.ink for layer in PRINT_ORDER],
        "print_instruction": (
            "Print files in numeric order on the same sheet without moving "
            "or re-registering the paper."
        ),
        "page": {
            "width": page_root.get("width"),
            "height": page_root.get("height"),
            "viewBox": page_root.get("viewBox"),
            "view_box_values": list(page_box),
        },
        "layers": [
            {
                "order": layer.order,
                "ink": layer.ink,
                "label": layer.label,
                "file": layer.path.name,
                "sha256": layer.sha256,
                "drawing_elements": layer.drawing_elements,
                "registration_elements": layer.registration_elements,
                "has_artwork": layer.has_artwork,
            }
            for layer in layer_files
        ],
    }
    manifest_path = folder / manifest_filename(base_name)
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return CmykExport(
        folder=folder,
        base_name=base_name,
        manifest_path=manifest_path,
        layers=tuple(layer_files),
    )
