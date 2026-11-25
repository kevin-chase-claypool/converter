"""Convert registered Plotterfun CMYK SVG layers into per-ink G-code."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import converter_core as converter

from ._plotterfun_cmyk import (
    CmykExport,
    InkLayer,
    PRINT_ORDER,
    sanitize_base_name,
)


ProgressCallback = Callable[[int, str], None]
Analyzer = Callable[[str, object, Callable[[], bool] | None], dict]


@dataclass(frozen=True)
class GcodeLayerFile:
    ink: str
    label: str
    order: int
    path: Path
    sha256: str
    gcode_lines: int
    contour_count: int
    svg_path: Path
    svg_sha256: str
    drawing_elements: int
    has_artwork: bool


@dataclass(frozen=True)
class CmykGcodeExport:
    folder: Path
    base_name: str
    manifest_path: Path
    layers: tuple[GcodeLayerFile, ...]
    intermediate_svg_folder: Path

    @property
    def missing_inks(self) -> tuple[str, ...]:
        return tuple(
            layer.label for layer in self.layers if not layer.has_artwork
        )


def gcode_filename(base_name: str, layer: InkLayer) -> str:
    return f"{sanitize_base_name(base_name)}-{layer.filename_part}.gcode"


def gcode_manifest_filename(base_name: str) -> str:
    return f"{sanitize_base_name(base_name)}-cmyk-set.json"


def planned_gcode_paths(folder: Path, base_name: str) -> tuple[Path, ...]:
    """Return every public destination path in Y/M/C/K order."""
    folder = Path(folder)
    return tuple(
        folder / gcode_filename(base_name, layer) for layer in PRINT_ORDER
    ) + (folder / gcode_manifest_filename(base_name),)


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def write_plotterfun_gcode_set(
    svg_export: CmykExport,
    folder: Path,
    settings,
    *,
    analyze_program: Analyzer,
    source_artwork: str = "",
    algorithm: str = "",
    created_utc: str | None = None,
    cancel_check: Callable[[], bool] | None = None,
    progress: ProgressCallback | None = None,
) -> CmykGcodeExport:
    """Write four registered G-code programs in physical print order.

    The SVG files stay in ``svg_export.folder`` as internal intermediates.
    Each layer is planned by the normal converter engine and staged completely
    before any final G-code file is replaced.
    """
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    base_name = sanitize_base_name(svg_export.base_name)
    staged = []
    for index, layer in enumerate(PRINT_ORDER, start=1):
        if cancel_check is not None and cancel_check():
            raise converter.OperationCancelled()
        if progress is not None:
            progress(
                index,
                f"Creating {layer.label} G-code ({index}/4)…",
            )
        svg_file = next(
            item for item in svg_export.layers if item.ink == layer.ink
        )
        analysis = analyze_program(
            str(svg_file.path),
            settings,
            cancel_check,
        )
        contours = list(analysis.get("contours") or [])
        gcode = str(analysis.get("gcode") or "")
        if not contours or not gcode:
            raise ValueError(
                f"The {layer.label} layer produced no drawable G-code."
            )
        payload = gcode.encode("utf-8")
        staging_path = (
            svg_export.folder
            / f"{layer.order:02d}-{layer.ink}.gcode.staging"
        )
        staging_path.write_bytes(payload)
        staged.append(
            {
                "ink": layer.ink,
                "label": layer.label,
                "order": layer.order,
                "path": folder / gcode_filename(base_name, layer),
                "payload": payload,
                "sha256": _sha256(payload),
                "gcode_lines": len(gcode.splitlines()),
                "contour_count": len(contours),
                "svg_file": svg_file,
                "staging_path": staging_path,
            }
        )

    written = []
    for record in staged:
        os.replace(record["staging_path"], record["path"])
        svg_file = record["svg_file"]
        written.append(
            GcodeLayerFile(
                ink=record["ink"],
                label=record["label"],
                order=record["order"],
                path=record["path"],
                sha256=record["sha256"],
                gcode_lines=record["gcode_lines"],
                contour_count=record["contour_count"],
                svg_path=svg_file.path,
                svg_sha256=svg_file.sha256,
                drawing_elements=svg_file.drawing_elements,
                has_artwork=svg_file.has_artwork,
            )
        )

    created = created_utc or datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    )
    manifest_path = folder / gcode_manifest_filename(base_name)
    manifest = {
        "kind": "theta-plotterfun-cmyk-gcode-set",
        "version": 1,
        "created_utc": created,
        "base_name": base_name,
        "source_artwork": str(source_artwork or ""),
        "algorithm": str(algorithm or ""),
        "print_order": [layer.ink for layer in PRINT_ORDER],
        "print_instruction": (
            "Run the files in numeric order on one sheet without moving or "
            "re-registering the paper."
        ),
        "intermediate_svg": {
            "folder": str(svg_export.folder),
            "manifest": str(svg_export.manifest_path),
        },
        "layers": [
            {
                "order": layer.order,
                "ink": layer.ink,
                "label": layer.label,
                "file": layer.path.name,
                "sha256": layer.sha256,
                "gcode_lines": layer.gcode_lines,
                "contour_count": layer.contour_count,
                "svg_file": layer.svg_path.name,
                "svg_sha256": layer.svg_sha256,
                "drawing_elements": layer.drawing_elements,
                "has_artwork": layer.has_artwork,
            }
            for layer in written
        ],
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return CmykGcodeExport(
        folder=folder,
        base_name=base_name,
        manifest_path=manifest_path,
        layers=tuple(written),
        intermediate_svg_folder=svg_export.folder,
    )
