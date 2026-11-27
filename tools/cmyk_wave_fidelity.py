"""Objective software-fidelity oracle for CMYK Variable-depth Wave artwork.

The oracle uses the production CMYK preprocessing and ``waves_fixed``
screening path, then evaluates the generated mark geometry and a white-paper
ink composite.  It deliberately does not claim to predict felt-tip spread,
paper loading, physical registration, or machine following error.

Run from the repository root:

    py -3 tools\\cmyk_wave_fidelity.py ^
      --image "C:\\Users\\jacks\\Downloads\\Golden Sunset Winter Family Selfie.png"

The default ``live-failed`` preset reproduces the owner's failing settings.
Use ``--recipe saved-sidecar`` to evaluate the recipe saved beside the image.
``100%`` depth intensity is compared with the selected recipe's high setting
on every other identical control.  Results are JSON on stdout.  Exit status is
0 for all gates passing, 1 for a fidelity failure, and 2 for an execution or
setup failure.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw


REPO_ROOT = Path(__file__).resolve().parent.parent
SOFTWARE_DIR = REPO_ROOT / "software"
if str(SOFTWARE_DIR) not in sys.path:
    sys.path.insert(0, str(SOFTWARE_DIR))

import converter_core as core  # noqa: E402
from converter_core import cmyk as converter  # noqa: E402


DEFAULT_IMAGE = Path(
    r"C:\Users\jacks\Downloads\Golden Sunset Winter Family Selfie.png"
)
DEFAULT_OUTPUT_DIR = REPO_ROOT / "tmp" / "wave-fidelity"

# Normalised source-image crops.  Faces carry the owner's lost-detail and wrong-
# colour complaints; the scene and clothing crops add different edge scales and
# Wave rows so a boundary-only pass cannot satisfy the gate.
REGIONS = {
    "family_portrait": (0.08, 0.10, 0.94, 0.92),
    "left_face": (0.15, 0.20, 0.50, 0.62),
    "child_face": (0.33, 0.38, 0.69, 0.80),
    "right_face": (0.56, 0.17, 0.92, 0.70),
    "winter_scene": (0.12, 0.03, 0.88, 0.42),
    "lower_clothing": (0.12, 0.62, 0.88, 0.94),
}

THRESHOLDS = {
    "detail_structure_correlation_min": 0.12,
    "detail_edge_correlation_min": 0.06,
    "detail_luminance_mae_max": 0.23,
    "color_rgb_mae_max": 0.24,
    "color_lightness_mae_max": 22.0,
    "color_chroma_mae_max": 30.0,
    "color_hue_error_deg_max": 50.0,
    "color_delta_e76_mean_max": 40.0,
    "ink_mean_absolute_bias_max": 0.20,
    "ink_coverage_mae_max": 0.18,
    "ink_coverage_correlation_min": 0.35,
    "wave_span_min_mm": 3.0,
    "wave_amplitude_min_mm": 0.10,
    "wave_cycles_min": 0.75,
    "wave_flat_span_fraction_max": 0.70,
    "wave_interior_amplitude_ratio_min": 0.55,
    "wave_region_rows_min": 4,
    "wave_region_span_median_min_mm": 20.0,
    "wave_region_amplitude_median_min_mm": 0.50,
    "wave_region_cycles_median_min": 0.75,
    "wave_region_flat_span_fraction_max": 0.50,
    "wave_region_interior_amplitude_ratio_min": 0.75,
    "depth_geometry_delta_min_mm": 0.05,
    "depth_geometry_ratio_min": 1.10,
}

WAVE_FLAT_THRESHOLD_MM = 0.05
MIN_WAVE_POINTS = 8
MIN_WAVE_SPAN_MM = 1.0

CHANNELS = ("c", "m", "y", "k")
CHANNEL_LABELS = {"c": "cyan", "m": "magenta", "y": "yellow", "k": "black"}


@dataclass(frozen=True)
class PageMapping:
    """Where the scaled source image lands in page millimetres."""

    page_w: float
    page_h: float
    x_mm: float
    y_mm: float
    width_mm: float
    height_mm: float

    def source_region_to_page(self, region):
        x0, y0, x1, y1 = region
        return (
            self.x_mm + x0 * self.width_mm,
            self.y_mm + y0 * self.height_mm,
            self.x_mm + x1 * self.width_mm,
            self.y_mm + y1 * self.height_mm,
        )


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _image_size(path):
    with Image.open(path) as image:
        return list(image.size)


def _sidecar_path(image_path):
    return Path(str(image_path) + ".theta-layout.json")


def _sibling_set_manifest(image_path):
    image = Path(image_path)
    candidates = (
        image.with_name(image.stem + "-cmyk-set.json"),
        image.with_name(image.stem + "-set.json"),
    )
    return next((path for path in candidates if path.is_file()), None)


def default_recipe():
    """Owner's live failed-state Variable-depth Wave recipe.

    This is deliberately separate from the image sidecar. The sidecar was
    saved with a different 2.0 mm pitch and does not reproduce the owner's
    reported straight-line failure. The live app state used a 1.15 mm source
    pitch at 110% scale, 150% depth intensity, and the failure-state image
    controls below. Select ``--recipe saved-sidecar`` to score the saved
    recipe instead.
    """
    return {
        "page_w": 200.0,
        "page_h": 200.0,
        "margin": 6.0,
        "scale": 1.10,
        "offset_x": 0.19,
        "offset_y": -1.62,
        "auto_levels": True,
        "saturation": 1.10,
        "contrast": 1.15,
        "brightness": 160.0,
        "sharpen": True,
        "sharpen_pct": 110.0,
        "sharpen_radius_mm": 1.5,
        "gamma": 1.35,
        "gcr": 0.25,
        "resolution": 10000,
        "weights": {"c": 0.90, "m": 0.85, "y": 1.15, "k": 1.00},
        "pitch": 1.15,
        "style": "waves_fixed",
        "dot_size": 1.0,
        "wave_period": 4.0,
        "wave_period_variation": 1.00,
        "wave_depth_intensity": 1.50,
        "wave_frequency_variation": converter.WAVE_FREQUENCY_VARIATION,
        "pen_width": 0.90,
        "path_tolerance": 0.05,
        "max_marks": 40000,
        "levels": 8,
        "overdraw": 1,
        "seed": 7,
        "offset_mm": {
            "c": (0.0, 0.0),
            "m": (0.0, 0.0),
            "y": (0.0, -0.04),
            "k": (0.0, -0.01),
        },
        # The live app capture passed its row guard and always supplied the
        # pen-plus-edge clearance to the screen. Keep the benchmark on that
        # contract so a broader pen-only allowance cannot make it look better.
        "row_clearance_mode": "pen-plus-edge",
        "ink_transmittances": None,
    }


def fidelity_recommended_recipe():
    """Starting recipe for the fidelity-oriented Variable-depth Wave mode.

    The owner's failed live state used a ``1.15 mm`` source pitch with a
    ``0.90 mm`` pen. At that pitch the pen-plus-edge clearance budget leaves
    almost no room for a sinusoidal carrier, so the slope cap flattens every
    row to a near-straight line (measured median peak-to-peak around
    ``0.25 mm``) and Depth intensity moves geometry by only ``~0.02 mm`` RMS.
    Raising the effective pitch to ``~1.5 mm`` restores visible waves
    (``~0.6 mm``) and a perceptible depth range, while deterministic row
    density keeps per-ink coverage on target. This preset is the verification
    anchor for the fidelity mode; it is not the owner's failed manual state.
    """
    recipe = default_recipe()
    recipe.update(
        {
            # Undo the washed-out manual image controls; keep a light unsharp
            # mask so facial detail survives the screen. Auto levels stays on
            # for exposure, and gamma/GCR return to neutral process values.
            "saturation": 1.05,
            "contrast": 1.05,
            "brightness": 100.0,
            "sharpen": True,
            "sharpen_pct": 60.0,
            "sharpen_radius_mm": 1.5,
            "gamma": 1.0,
            "gcr": 0.65,
            "weights": {"c": 1.00, "m": 1.00, "y": 1.00, "k": 1.00},
            # The pitch that makes the Wave carrier actually read as a wave.
            "pitch": 1.5,
            "style": "waves_fidelity",
            "wave_period": 2.0,
            "wave_period_variation": 0.35,
            "wave_depth_intensity": 1.50,
        }
    )
    return recipe


def load_recipe(image_path, recipe_mode="live-failed"):
    """Read the selected recipe profile and measured ink data when available."""
    if recipe_mode not in (
        "live-failed",
        "fidelity-recommended",
        "saved-sidecar",
    ):
        raise ValueError(
            "recipe_mode must be 'live-failed', 'fidelity-recommended', "
            "or 'saved-sidecar'"
        )
    if recipe_mode == "fidelity-recommended":
        recipe = fidelity_recommended_recipe()
    else:
        recipe = default_recipe()
    sidecar = _sidecar_path(image_path)
    sources = []
    if recipe_mode == "saved-sidecar" and sidecar.is_file():
        data = json.loads(sidecar.read_text(encoding="utf-8"))
        cmyk = data.get("generator_tabs", {}).get("cmyk", {})
        image = cmyk.get("image_options", {})
        screen = cmyk.get("screen", {})
        page = cmyk.get("page", {})
        offsets = cmyk.get("pen_offsets_mm", {})
        recipe.update(
            {
                "page_w": float(page.get("width_mm", recipe["page_w"])),
                "page_h": float(page.get("height_mm", recipe["page_h"])),
                "margin": float(page.get("margin_mm", recipe["margin"])),
                "scale": float(
                    page.get(
                        "artwork_scale_pct",
                        recipe["scale"] * 100.0,
                    )
                )
                / 100.0,
                "offset_x": float(
                    data.get("artwork_offset_x_mm", recipe["offset_x"])
                ),
                "offset_y": float(
                    data.get("artwork_offset_y_mm", recipe["offset_y"])
                ),
                "auto_levels": bool(
                    image.get("auto_levels", recipe["auto_levels"])
                ),
                "saturation": float(
                    image.get("saturation_pct", recipe["saturation"] * 100.0)
                )
                / 100.0,
                "contrast": float(
                    image.get("contrast_pct", recipe["contrast"] * 100.0)
                )
                / 100.0,
                "brightness": float(
                    image.get("brightness_pct", recipe["brightness"])
                ),
                "sharpen": bool(image.get("sharpen", recipe["sharpen"])),
                "sharpen_pct": float(
                    image.get("sharpen_pct", recipe["sharpen_pct"])
                ),
                "sharpen_radius_mm": float(
                    image.get("sharpen_radius_mm", recipe["sharpen_radius_mm"])
                ),
                "gamma": float(image.get("gamma", recipe["gamma"])),
                "gcr": float(image.get("gcr_pct", recipe["gcr"] * 100.0))
                / 100.0,
                "resolution": int(
                    image.get("resolution_px", recipe["resolution"])
                ),
                "pitch": float(
                    screen.get("dot_pitch_mm", recipe["pitch"])
                ),
                "style": str(screen.get("style", recipe["style"])),
                "dot_size": float(
                    screen.get("dot_size_pct", recipe["dot_size"] * 100.0)
                )
                / 100.0,
                "wave_period": float(
                    screen.get(
                        "wave_period_pitches",
                        recipe["wave_period"],
                    )
                ),
                "wave_period_variation": float(
                    screen.get(
                        "wave_period_variation_pct",
                        recipe["wave_period_variation"] * 100.0,
                    )
                )
                / 100.0,
                "wave_depth_intensity": float(
                    screen.get(
                        "wave_depth_intensity_pct",
                        recipe["wave_depth_intensity"] * 100.0,
                    )
                )
                / 100.0,
                "wave_frequency_variation": (
                    converter.WAVE_FREQUENCY_VARIATION
                    if screen.get("vary_wave_frequency", True)
                    else 0.0
                ),
                "pen_width": float(
                    screen.get("pen_width_mm", recipe["pen_width"])
                ),
                "path_tolerance": float(
                    screen.get(
                        "path_tolerance_mm",
                        recipe["path_tolerance"],
                    )
                ),
                "max_marks": int(
                    screen.get("max_marks", recipe["max_marks"])
                ),
                "levels": int(screen.get("levels", recipe["levels"])),
                "overdraw": int(
                    screen.get("overdraw", recipe["overdraw"])
                ),
                "seed": int(screen.get("seed", recipe["seed"])),
                "row_clearance_mode": "pen-plus-edge",
            }
        )
        weights = image.get("weights_pct")
        if isinstance(weights, dict):
            recipe["weights"] = {
                channel: float(weights.get(channel, 100.0)) / 100.0
                for channel in CHANNELS
            }
        if isinstance(offsets, dict):
            recipe["offset_mm"] = {
                channel: tuple(
                    float(value)
                    for value in offsets.get(channel, (0.0, 0.0))
                )
                for channel in CHANNELS
            }
        sources.append(
            {
                "path": str(sidecar),
                "sha256": _sha256(sidecar),
            }
        )

    manifest_path = _sibling_set_manifest(image_path)
    if manifest_path is not None:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        ink = manifest.get("ink_processing", {})
        transmittances = ink.get("ink_transmittances")
        if isinstance(transmittances, dict):
            recipe["ink_transmittances"] = {
                channel: tuple(
                    float(value)
                    for value in transmittances[channel]
                )
                for channel in CHANNELS
                if channel in transmittances
            }
        sources.append(
            {
                "path": str(manifest_path),
                "sha256": _sha256(manifest_path),
            }
        )

    if recipe["style"] not in ("waves_fixed", "waves_fidelity"):
        raise ValueError(
            "The image recipe does not select a production Variable-depth "
            f"Wave mode; found {recipe['style']!r}."
        )
    recipe["recipe_mode"] = recipe_mode
    return recipe, sources


def page_mapping(geometry, recipe):
    """Apply the CMYK tab's artwork scale and absolute offset."""
    scale = max(0.01, float(recipe["scale"]))
    centre_x = float(recipe["page_w"]) / 2.0
    centre_y = float(recipe["page_h"]) / 2.0
    return PageMapping(
        page_w=float(recipe["page_w"]),
        page_h=float(recipe["page_h"]),
        x_mm=centre_x
        + (float(geometry["off_x"]) - centre_x) * scale
        + float(recipe["offset_x"]),
        y_mm=centre_y
        + (float(geometry["off_y"]) - centre_y) * scale
        + float(recipe["offset_y"]),
        width_mm=float(geometry["width_mm"]) * scale,
        height_mm=float(geometry["height_mm"]) * scale,
    )


def prepare_tones(image_path, recipe):
    return converter.prepare_image_tones(
        str(image_path),
        recipe["page_w"],
        recipe["page_h"],
        margin_mm=recipe["margin"],
        brightness=recipe["brightness"],
        resolution_px=recipe["resolution"],
        saturation=recipe["saturation"],
        contrast=recipe["contrast"],
        gcr=recipe["gcr"],
        weights=recipe["weights"],
        gamma=recipe["gamma"],
        transmittances=recipe.get("ink_transmittances"),
        auto_levels=recipe["auto_levels"],
        sharpen_pct=(
            recipe["sharpen_pct"] if recipe["sharpen"] else 0.0
        ),
        sharpen_radius_mm=recipe["sharpen_radius_mm"] / recipe["scale"],
    )


def _screen_one_channel(payload):
    tones, geometry, recipe, channel, index, intensity = payload
    try:
        factor = max(0.01, float(recipe["scale"]))
        marks = converter.screen_channel(
            tones[channel],
            geometry,
            style=recipe["style"],
            spacing_mm=recipe["pitch"],
            dot_scale=recipe["dot_size"],
            angle_deg=converter.SCREEN_ANGLES_DEG[channel],
            seed=recipe["seed"] + index,
            max_marks=recipe["max_marks"],
            pen_diameter_mm=recipe["pen_width"],
            levels=recipe["levels"],
            overdraw=recipe["overdraw"],
            solid=False,
            path_tolerance_mm=recipe["path_tolerance"] / factor,
            depth_tone=(
                tones["depth"]
                if recipe["style"] == "waves_fidelity"
                else tones[channel]
            ),
            row_clearance_mm=(
                recipe["pen_width"] / factor
                if recipe.get("row_clearance_mode") == "pen-only-historical"
                else (
                    recipe["pen_width"] + converter.WAVE_MIN_EDGE_GAP_MM
                )
                / factor
            ),
            wave_frequency_variation=recipe["wave_frequency_variation"],
            wave_period_pitches=recipe["wave_period"],
            wave_period_variation=recipe["wave_period_variation"],
            wave_depth_intensity=intensity,
        )
        marks = [
            _scale_and_offset_mark(
                mark,
                factor,
                float(recipe["page_w"]),
                float(recipe["page_h"]),
                recipe["offset_mm"][channel],
            )
            for mark in marks
        ]
        return channel, marks, None
    except Exception as exc:  # noqa: BLE001 - record per-channel failures
        return channel, [], "%s: %s" % (type(exc).__name__, exc)


def build_layers(tones, geometry, recipe, depth_intensity=None, jobs=1):
    """Screen all four inks through the production ``waves_fixed`` path.

    Returns ``(layers, errors)``. A channel that raises during screening is
    recorded in ``errors`` and contributed as an empty layer, so the oracle
    can still score the remaining geometry and report the failure instead of
    crashing with a bare error.
    """
    intensity = (
        float(recipe["wave_depth_intensity"])
        if depth_intensity is None
        else float(depth_intensity)
    )
    payloads = [
        (tones, geometry, recipe, channel, index, intensity)
        for index, channel in enumerate(CHANNELS)
    ]
    worker_count = max(1, min(int(jobs), len(payloads)))
    if worker_count == 1:
        results = list(map(_screen_one_channel, payloads))
    else:
        with ProcessPoolExecutor(max_workers=worker_count) as executor:
            results = list(executor.map(_screen_one_channel, payloads))
    layers = {}
    errors = {}
    for channel, marks, error in results:
        layers[channel] = marks if marks is not None else []
        if error:
            errors[channel] = error
    return layers, errors


def _scale_and_offset_mark(mark, factor, width, height, offset):
    centre_x = width / 2.0
    centre_y = height / 2.0
    dx, dy = offset

    def transform(point):
        return (
            centre_x + (point[0] - centre_x) * factor + dx,
            centre_y + (point[1] - centre_y) * factor + dy,
        )

    return converter.retag_contour(
        mark,
        [transform(point) for point in mark],
        point_transform=transform,
    )


def _load_source_rgba(image_path):
    image = Image.open(image_path).convert("RGBA")
    white = Image.new("RGBA", image.size, (255, 255, 255, 255))
    white.alpha_composite(image)
    return white.convert("RGB")


def _art_placement_pixels(mapping, size):
    scale = size / mapping.page_w
    return (
        mapping.x_mm * scale,
        mapping.y_mm * scale,
        mapping.width_mm * scale,
        mapping.height_mm * scale,
    )


def _place_scaled_image(image, mapping, size):
    """Place an image at the scaled source bounds, clipping to the page."""
    target = Image.new(
        image.mode,
        (size, size),
        0 if image.mode == "L" else "white",
    )
    x, y, width, height = _art_placement_pixels(mapping, size)
    width_px = max(1, int(round(width)))
    height_px = max(1, int(round(height)))
    resized = image.resize((width_px, height_px), Image.Resampling.LANCZOS)

    left = max(0.0, x)
    top = max(0.0, y)
    right = min(float(size), x + width_px)
    bottom = min(float(size), y + height_px)
    if right <= left or bottom <= top:
        return target
    source_left = int(round(left - x))
    source_top = int(round(top - y))
    source_right = min(width_px, source_left + int(round(right - left)))
    source_bottom = min(height_px, source_top + int(round(bottom - top)))
    crop = resized.crop(
        (source_left, source_top, source_right, source_bottom)
    )
    target.paste(crop, (int(round(left)), int(round(top))))
    return target


def source_canvas(image_path, mapping, size):
    image = _load_source_rgba(image_path)
    return np.asarray(
        _place_scaled_image(image, mapping, size),
        dtype=np.float32,
    ) / 255.0


def target_ink_canvases(tones, mapping, size):
    canvases = {}
    for channel in CHANNELS:
        data = np.clip(np.asarray(tones[channel], dtype=np.float32), 0.0, 1.0)
        image = Image.fromarray((data * 255.0).astype(np.uint8))
        placed = _place_scaled_image(
            image.convert("L"),
            mapping,
            size,
        )
        canvases[channel] = np.asarray(placed, dtype=np.float32) / 255.0
    return canvases


def render_coverage(layers, recipe, size, supersample=2):
    """Rasterise each generated ink path at physical pen width."""
    page_w = float(recipe["page_w"])
    page_h = float(recipe["page_h"])
    render_size = max(size, int(size * supersample))
    scale_x = render_size / page_w
    scale_y = render_size / page_h
    width_px = max(1, int(round(recipe["pen_width"] * scale_x)))
    coverage = {}
    for channel in CHANNELS:
        image = Image.new("L", (render_size, render_size), 0)
        draw = ImageDraw.Draw(image)
        for mark in layers[channel]:
            if len(mark) < 2:
                continue
            points = [
                (point[0] * scale_x, point[1] * scale_y)
                for point in mark
            ]
            draw.line(
                points,
                fill=255,
                width=width_px,
                joint="curve",
            )
        if render_size != size:
            image = image.resize((size, size), Image.Resampling.LANCZOS)
        coverage[channel] = (
            np.asarray(image, dtype=np.float32) / 255.0
        )
    return coverage


def composite_rgb(coverage, transmittances=None):
    """Multiply measured or nominal CMYK ink transmittances on white paper."""
    if transmittances is None:
        matrix = converter.ink_transmittance_matrix()
        transmittances = {
            channel: tuple(matrix[index])
            for index, channel in enumerate(converter.CHANNELS)
        }
    result = np.ones((*coverage["c"].shape, 3), dtype=np.float32)
    for channel in CHANNELS:
        amount = coverage[channel][..., None]
        transmittance = np.asarray(
            transmittances[channel],
            dtype=np.float32,
        )
        result *= 1.0 - amount * (1.0 - transmittance)
    return np.clip(result, 0.0, 1.0)


def _luminance(rgb):
    return (
        rgb[..., 0] * 0.2126
        + rgb[..., 1] * 0.7152
        + rgb[..., 2] * 0.0722
    )


def _box_blur(array, radius):
    radius = max(0, int(radius))
    if radius == 0:
        return array.astype(np.float64, copy=False)
    width = 2 * radius + 1
    padded = np.pad(
        array.astype(np.float64, copy=False),
        ((radius, radius), (radius, radius)),
        mode="reflect",
    )
    integral = np.pad(
        np.cumsum(np.cumsum(padded, axis=0), axis=1),
        ((1, 0), (1, 0)),
    )
    height, original_width = array.shape
    rows = integral[
        width : width + height,
        width : width + original_width,
    ].copy()
    rows -= integral[:height, width : width + original_width]
    rows -= integral[width : width + height, :original_width]
    rows += integral[:height, :original_width]
    return rows / float(width * width)


def _pearson(first, second):
    first = np.array(
        first,
        dtype=np.float64,
        copy=True,
    ).ravel()
    second = np.array(
        second,
        dtype=np.float64,
        copy=True,
    ).ravel()
    first -= float(first.mean())
    second -= float(second.mean())
    denominator = float(np.linalg.norm(first) * np.linalg.norm(second))
    if denominator <= 1e-12:
        return 1.0 if np.allclose(first, second) else 0.0
    return float(np.dot(first, second) / denominator)


def _gradient_magnitude(luminance):
    gradient_y, gradient_x = np.gradient(
        luminance.astype(np.float64, copy=False)
    )
    return np.hypot(gradient_x, gradient_y)


def structure_metrics(source_rgb, rendered_rgb):
    """Multi-scale luminance structure plus edge correlation and error."""
    source_lum = _luminance(np.asarray(source_rgb, dtype=np.float32))
    rendered_lum = _luminance(np.asarray(rendered_rgb, dtype=np.float32))
    scale_correlations = {}
    for radius in (1, 4):
        source_scale = _box_blur(source_lum, radius)
        rendered_scale = _box_blur(rendered_lum, radius)
        scale_correlations[f"radius_{radius}px"] = _pearson(
            source_scale,
            rendered_scale,
        )

    source_edges = _gradient_magnitude(_box_blur(source_lum, 1))
    rendered_edges = _gradient_magnitude(_box_blur(rendered_lum, 1))
    source_edge_mean = float(source_edges.mean())
    rendered_edge_mean = float(rendered_edges.mean())
    return {
        "structure_correlation": min(scale_correlations.values()),
        "scale_correlations": scale_correlations,
        "edge_correlation": _pearson(source_edges, rendered_edges),
        "edge_magnitude_ratio": (
            rendered_edge_mean / max(source_edge_mean, 1e-12)
        ),
        "luminance_mae": float(np.mean(np.abs(source_lum - rendered_lum))),
    }


def _rgb_to_lab(rgb):
    rgb = np.asarray(rgb, dtype=np.float64)
    linear = np.where(
        rgb <= 0.04045,
        rgb / 12.92,
        np.power((rgb + 0.055) / 1.055, 2.4),
    )
    matrix = np.array(
        [
            [0.4124564, 0.3575761, 0.1804375],
            [0.2126729, 0.7151522, 0.0721750],
            [0.0193339, 0.1191920, 0.9503041],
        ],
        dtype=np.float64,
    )
    xyz = linear @ matrix.T
    xyz /= np.array([0.95047, 1.00000, 1.08883], dtype=np.float64)
    delta = 6.0 / 29.0
    f = np.where(
        xyz > delta ** 3,
        np.cbrt(xyz),
        xyz / (3.0 * delta * delta) + 4.0 / 29.0,
    )
    return np.stack(
        (
            116.0 * f[..., 1] - 16.0,
            500.0 * (f[..., 0] - f[..., 1]),
            200.0 * (f[..., 1] - f[..., 2]),
        ),
        axis=-1,
    )


def color_metrics(source_rgb, rendered_rgb):
    """RGB and CIELAB lightness, chroma, circular hue, and delta-E error."""
    source = np.asarray(source_rgb, dtype=np.float64)
    rendered = np.asarray(rendered_rgb, dtype=np.float64)
    rgb_delta = rendered - source
    source_lab = _rgb_to_lab(source)
    rendered_lab = _rgb_to_lab(rendered)
    source_chroma = np.hypot(source_lab[..., 1], source_lab[..., 2])
    rendered_chroma = np.hypot(rendered_lab[..., 1], rendered_lab[..., 2])
    source_hue = np.degrees(
        np.arctan2(source_lab[..., 2], source_lab[..., 1])
    )
    rendered_hue = np.degrees(
        np.arctan2(rendered_lab[..., 2], rendered_lab[..., 1])
    )
    hue_delta = np.abs(
        (rendered_hue - source_hue + 180.0) % 360.0 - 180.0
    )
    chromatic = (source_chroma >= 5.0) | (rendered_chroma >= 5.0)
    hue_error = (
        float(hue_delta[chromatic].mean())
        if np.any(chromatic)
        else 0.0
    )
    delta_e = np.linalg.norm(rendered_lab - source_lab, axis=-1)
    return {
        "rgb_mae": float(np.mean(np.abs(rgb_delta))),
        "rgb_rmse": float(np.sqrt(np.mean(rgb_delta ** 2))),
        "rgb_bias": [
            float(value) for value in rgb_delta.mean(axis=(0, 1))
        ],
        "lightness_mae": float(
            np.mean(np.abs(rendered_lab[..., 0] - source_lab[..., 0]))
        ),
        "lightness_bias": float(
            np.mean(rendered_lab[..., 0] - source_lab[..., 0])
        ),
        "chroma_mae": float(
            np.mean(np.abs(rendered_chroma - source_chroma))
        ),
        "chroma_bias": float(
            np.mean(rendered_chroma - source_chroma)
        ),
        "hue_error_deg": hue_error,
        "delta_e76_mean": float(delta_e.mean()),
        "delta_e76_p95": float(np.percentile(delta_e, 95.0)),
    }


def _pixel_region(mapping, region, size):
    left_mm, top_mm, right_mm, bottom_mm = mapping.source_region_to_page(
        region
    )
    left = max(0, int(math.floor(left_mm / mapping.page_w * size)))
    top = max(0, int(math.floor(top_mm / mapping.page_h * size)))
    right = min(size, int(math.ceil(right_mm / mapping.page_w * size)))
    bottom = min(size, int(math.ceil(bottom_mm / mapping.page_h * size)))
    if right - left < 8 or bottom - top < 8:
        return None
    return (left, top, right, bottom)


def region_metrics(
    source,
    rendered,
    coverage,
    target_coverage,
    mapping,
    size,
):
    results = {}
    for name, region in REGIONS.items():
        box = _pixel_region(mapping, region, size)
        if box is None:
            results[name] = {"error": "crop leaves the page"}
            continue
        left, top, right, bottom = box
        source_crop = source[top:bottom, left:right]
        rendered_crop = rendered[top:bottom, left:right]
        record = {
            "source_normalized_xyxy": list(region),
            "page_mm_xyxy": [
                round(value, 3)
                for value in mapping.source_region_to_page(region)
            ],
            "pixels_xyxy": list(box),
        }
        record["detail"] = structure_metrics(
            source_crop,
            rendered_crop,
        )
        record["color"] = color_metrics(source_crop, rendered_crop)
        record["ink"] = {}
        for channel in CHANNELS:
            actual = coverage[channel][top:bottom, left:right]
            target = target_coverage[channel][top:bottom, left:right]
            actual_mean = float(actual.mean())
            target_mean = float(target.mean())
            record["ink"][channel] = {
                "mean_coverage": actual_mean,
                "target_mean_coverage": target_mean,
                "coverage_bias": actual_mean - target_mean,
                "coverage_mae": float(np.mean(np.abs(actual - target))),
                "coverage_correlation": _pearson(actual, target),
            }
        results[name] = record
    return results


def coverage_fidelity_metrics(coverage, target_coverage):
    """Full-image per-ink coverage reproduction error.

    ``coverage`` is the rasterized ink laid down by the screen at pen width;
    ``target_coverage`` is the separation's requested ink coverage. A screen
    that only changes wave shape (constant density) scores a large MAE and a
    weak correlation; a screen whose density tracks tone scores near zero MAE
    and a strong correlation.
    """
    metrics = {}
    for channel in CHANNELS:
        actual = np.asarray(coverage[channel], dtype=np.float64)
        target = np.asarray(target_coverage[channel], dtype=np.float64)
        metrics[channel] = {
            "coverage_mae": float(np.mean(np.abs(actual - target))),
            "coverage_correlation": _pearson(actual, target),
        }
    return metrics


def _coverage_fidelity_checks(coverage_fidelity):
    """Release gates for full-image tone-to-coverage reproduction."""
    checks = []
    for channel in CHANNELS:
        label = CHANNEL_LABELS[channel]
        record = coverage_fidelity[channel]
        checks.append(
            _check(
                f"ink.{label}.coverage_mae_max",
                record["coverage_mae"]
                <= THRESHOLDS["ink_coverage_mae_max"],
                record["coverage_mae"],
                THRESHOLDS["ink_coverage_mae_max"],
                "<=",
            )
        )
        checks.append(
            _check(
                f"ink.{label}.coverage_correlation_min",
                record["coverage_correlation"]
                >= THRESHOLDS["ink_coverage_correlation_min"],
                record["coverage_correlation"],
                THRESHOLDS["ink_coverage_correlation_min"],
                ">=",
            )
        )
    return checks


def _row_groups(paths):
    groups = {}
    anonymous = 0
    for path in paths:
        if len(path) < MIN_WAVE_POINTS:
            continue
        row_index = getattr(path, "wave_row_index", None)
        if row_index is None:
            key = ("anonymous", anonymous)
            anonymous += 1
        else:
            key = ("row", int(row_index))
        group = groups.setdefault(
            key,
            {"points": [], "baselines": []},
        )
        group["points"].extend(path)
        baseline = getattr(path, "wave_baseline_mm", None)
        if baseline is not None:
            group["baselines"].append(tuple(baseline))
    return groups


def _row_metrics(points, angle_deg, pitch_mm, baseline_point=None):
    points = np.asarray(points, dtype=np.float64)
    if len(points) < MIN_WAVE_POINTS:
        return None
    angle = math.radians(float(angle_deg))
    cosine = math.cos(angle)
    sine = math.sin(angle)
    along = points[:, 0] * cosine + points[:, 1] * sine
    across = -points[:, 0] * sine + points[:, 1] * cosine
    order = np.argsort(along, kind="stable")
    along = along[order]
    across = across[order]
    span = float(along[-1] - along[0])
    if span < MIN_WAVE_SPAN_MM:
        return {
            "span_mm": span,
            "amplitude_peak_to_peak_mm": 0.0,
            "rms_mm": 0.0,
            "cycles": 0.0,
            "flat_span_fraction": 1.0,
            "interior_amplitude_mm": 0.0,
            "interior_amplitude_ratio": 0.0,
            "points": int(len(points)),
        }

    if baseline_point is None:
        slope, intercept = np.polyfit(along, across, 1)
        residual = across - (slope * along + intercept)
    else:
        baseline_across = (
            float(baseline_point[0]) * -sine
            + float(baseline_point[1]) * cosine
        )
        residual = across - baseline_across
    if len(residual) >= 3:
        residual = _box_blur(residual.reshape(1, -1), 1).ravel()
    amplitude = float(
        np.percentile(residual, 98.0) - np.percentile(residual, 2.0)
    )

    interior = (along >= np.percentile(along, 10.0)) & (
        along <= np.percentile(along, 90.0)
    )
    derivative = np.diff(residual[interior])
    derivative_deadband = max(0.001, 0.002 * float(pitch_mm))
    derivative_sign = np.sign(
        np.where(
            np.abs(derivative) < derivative_deadband,
            0.0,
            derivative,
        )
    )
    nonzero_derivative = derivative_sign[derivative_sign != 0.0]
    turning_points = (
        int(
            np.count_nonzero(
                nonzero_derivative[1:] != nonzero_derivative[:-1]
            )
        )
        if len(nonzero_derivative) > 1
        else 0
    )
    cycles = turning_points / 2.0

    interior_amplitude = (
        float(
            np.percentile(residual[interior], 98.0)
            - np.percentile(residual[interior], 2.0)
        )
        if np.count_nonzero(interior) >= 3
        else 0.0
    )

    # Bins expose long straight interiors even when a row begins or ends with
    # a visible hook.  Boundary-only variation therefore cannot pass.
    edges = np.linspace(along[0], along[-1], 21)
    flat_width = 0.0
    for low, high in zip(edges, edges[1:]):
        mask = (along >= low) & (along <= high)
        if np.count_nonzero(mask) < 2:
            continue
        local_range = float(
            np.percentile(residual[mask], 98.0)
            - np.percentile(residual[mask], 2.0)
        )
        if local_range < WAVE_FLAT_THRESHOLD_MM:
            flat_width += high - low
    flat_fraction = flat_width / max(span, 1e-12)
    return {
        "span_mm": span,
        "amplitude_peak_to_peak_mm": amplitude,
        "rms_mm": float(np.sqrt(np.mean(residual ** 2))),
        "cycles": float(cycles),
        "flat_span_fraction": float(flat_fraction),
        "interior_amplitude_mm": interior_amplitude,
        "interior_amplitude_ratio": interior_amplitude
        / max(amplitude, 1e-12),
        "points": int(len(points)),
    }


def _aggregate_rows(rows):
    if not rows:
        return {
            "rows": 0,
            "median_span_mm": 0.0,
            "median_amplitude_peak_to_peak_mm": 0.0,
            "median_rms_mm": 0.0,
            "median_cycles": 0.0,
            "median_flat_span_fraction": 1.0,
            "median_interior_amplitude_ratio": 0.0,
            "rows_with_amplitude": 0,
        }

    def median(key):
        return float(np.median([row[key] for row in rows]))

    return {
        "rows": len(rows),
        "median_span_mm": median("span_mm"),
        "median_amplitude_peak_to_peak_mm": median(
            "amplitude_peak_to_peak_mm"
        ),
        "median_rms_mm": median("rms_mm"),
        "p90_amplitude_peak_to_peak_mm": float(
            np.percentile(
                [row["amplitude_peak_to_peak_mm"] for row in rows],
                90.0,
            )
        ),
        "median_cycles": median("cycles"),
        "median_flat_span_fraction": median("flat_span_fraction"),
        "median_interior_amplitude_ratio": median(
            "interior_amplitude_ratio"
        ),
        "rows_with_amplitude": int(
            sum(
                row["amplitude_peak_to_peak_mm"]
                >= THRESHOLDS["wave_amplitude_min_mm"]
                for row in rows
            )
        ),
    }


def measure_wave_paths(
    paths,
    angle_deg,
    pitch_mm,
    page_w=None,
    page_h=None,
    page_region=None,
):
    selected = []
    if page_region is None:
        selected = paths
    else:
        left, top, right, bottom = page_region
        for path in paths:
            points = [
                point
                for point in path
                if left <= point[0] <= right and top <= point[1] <= bottom
            ]
            if len(points) >= MIN_WAVE_POINTS:
                selected.append(
                    converter.retag_contour(path, points)
                )
    rows = []
    for group in _row_groups(selected).values():
        baseline_point = (
            group["baselines"][0] if group["baselines"] else None
        )
        metrics = _row_metrics(
            group["points"],
            angle_deg,
            pitch_mm,
            baseline_point,
        )
        if metrics is not None:
            rows.append(metrics)
    return _aggregate_rows(rows)


def wave_metrics(layers, recipe, mapping):
    global_metrics = {}
    for channel in CHANNELS:
        global_metrics[channel] = measure_wave_paths(
            layers[channel],
            converter.SCREEN_ANGLES_DEG[channel],
            recipe["pitch"] * recipe["scale"],
        )

    region_metrics_by_name = {}
    for name, region in REGIONS.items():
        page_region = mapping.source_region_to_page(region)
        per_channel = {}
        for channel in CHANNELS:
            per_channel[channel] = measure_wave_paths(
                layers[channel],
                converter.SCREEN_ANGLES_DEG[channel],
                recipe["pitch"] * recipe["scale"],
                recipe["page_w"],
                recipe["page_h"],
                page_region,
            )
        region_metrics_by_name[name] = {
            "page_mm_xyxy": [
                round(value, 3) for value in page_region
            ],
            "inks": per_channel,
        }
    return {
        "inks": global_metrics,
        "regions": region_metrics_by_name,
    }


def depth_geometry_comparison(neutral, high):
    per_ink = {}
    for channel in CHANNELS:
        neutral_rms = neutral[channel]["median_rms_mm"]
        high_rms = high[channel]["median_rms_mm"]
        per_ink[channel] = {
            "neutral_median_rms_mm": neutral_rms,
            "high_median_rms_mm": high_rms,
            "rms_delta_mm": abs(high_rms - neutral_rms),
            "rms_ratio": high_rms / max(neutral_rms, 1e-12),
            "neutral_median_amplitude_mm": neutral[channel][
                "median_amplitude_peak_to_peak_mm"
            ],
            "high_median_amplitude_mm": high[channel][
                "median_amplitude_peak_to_peak_mm"
            ],
        }
    deltas = [record["rms_delta_mm"] for record in per_ink.values()]
    ratios = [
        record["rms_ratio"]
        for record in per_ink.values()
        if record["neutral_median_rms_mm"] > 1e-9
    ]
    material = (
        float(np.median(deltas))
        >= THRESHOLDS["depth_geometry_delta_min_mm"]
        and (
            not ratios
            or float(np.median(ratios))
            >= THRESHOLDS["depth_geometry_ratio_min"]
        )
    )
    return {
        "neutral_depth_intensity_pct": 100.0,
        "high_depth_intensity_pct": None,
        "per_ink": per_ink,
        "median_rms_delta_mm": float(np.median(deltas)),
        "median_rms_ratio": (
            float(np.median(ratios)) if ratios else None
        ),
        "material_geometry_change": material,
    }


def _wave_gcode_settings(recipe):
    settings = core.Settings(
        fit_mode="manual",
        scale=1.0,
        tolerance=min(float(recipe["path_tolerance"]), 0.05),
        pen_diameter_mm=float(recipe["pen_width"]),
        compensate_pen_width=False,
        hatch_spacing_mm=0.0,
        theta_mode="fixed",
        theta_offset=0.0,
        theta_center_hold_diameter_mm=0.0,
        bed_compensation_path="",
        row_locked_compensation=False,
        contour_order="rows_ascending",
        frame_center_mm=(
            float(recipe["page_w"]) / 2.0,
            float(recipe["page_h"]) / 2.0,
        ),
        fit_frame_mm=(
            0.0,
            0.0,
            float(recipe["page_w"]),
            float(recipe["page_h"]),
        ),
    )
    return settings


WORD = re.compile(r"([XYA])(-?\d+(?:\.\d+)?)", re.IGNORECASE)
ROW_COMMENT = re.compile(
    r"^\(wave row\s+(\d+)\s+baseline\s+(-?\d+(?:\.\d+)?)\s+mm\)"
)


def decode_gcode_wave_rows(gcode, ratio, centre):
    """Decode emitted fixed-bed G-code points back to page millimetres."""
    x = y = a = 0.0
    drawing = False
    current = []
    row_index = None
    baseline = None
    rows = []
    for raw_line in str(gcode).splitlines():
        line = raw_line.strip()
        row_match = ROW_COMMENT.match(line)
        if row_match:
            row_index = int(row_match.group(1))
            baseline = float(row_match.group(2))
            continue
        if line.startswith("(contour"):
            row_index = None
            baseline = None
            continue
        if line == "M3":
            drawing = True
            current = [_decode_machine_point(x, y, a, ratio, centre)]
            continue
        if line == "M5":
            if drawing and len(current) >= 2:
                trail = converter.WaveTrail(
                    current,
                    wave_row_index=row_index,
                )
                trail.wave_baseline_decoded_comment = baseline
                rows.append(trail)
            drawing = False
            current = []
            continue
        if not (line.startswith("G1 ") or line.startswith("G01 ")):
            continue
        words = {
            key.upper(): float(value)
            for key, value in WORD.findall(line)
        }
        next_x = words.get("X", x)
        next_y = words.get("Y", y)
        next_a = words.get("A", a)
        if drawing and any(key in words for key in ("X", "Y", "A")):
            current.append(
                _decode_machine_point(next_x, next_y, next_a, ratio, centre)
            )
        x, y, a = next_x, next_y, next_a
    return rows


def _decode_machine_point(machine_x, machine_y, motor_angle, ratio, centre):
    theta = math.radians(-float(motor_angle) / float(ratio))
    cosine = math.cos(theta)
    sine = math.sin(theta)
    return (
        machine_x * cosine - machine_y * sine + centre[0],
        machine_x * sine + machine_y * cosine + centre[1],
    )


def generate_gcode_witness(layers, recipe, mapping):
    """Generate compact fixed-bed G-code from the actual high-depth rows."""
    settings = _wave_gcode_settings(recipe)
    centre = settings.frame_center_mm
    programs = {}
    path_metrics = {}
    decoded_by_channel = {}
    for channel in CHANNELS:
        path = layers[channel]
        if not path:
            programs[channel] = ""
            decoded_by_channel[channel] = []
            path_metrics[channel] = _aggregate_rows([])
            continue
        plan = core.plan_program(path, settings)
        gcode = core.contours_to_gcode(
            path,
            settings,
            program_plan=plan,
        )
        programs[channel] = gcode
        decoded = decode_gcode_wave_rows(
            gcode,
            settings.theta_drive_ratio,
            centre,
        )
        decoded_by_channel[channel] = decoded
        path_metrics[channel] = measure_wave_paths(
            decoded,
            converter.SCREEN_ANGLES_DEG[channel],
            recipe["pitch"] * recipe["scale"],
        )
    region_metrics = {}
    for name, region in REGIONS.items():
        page_region = mapping.source_region_to_page(region)
        region_metrics[name] = {
            "page_mm_xyxy": [
                round(value, 3) for value in page_region
            ],
            "inks": {
                channel: measure_wave_paths(
                    decoded_by_channel[channel],
                    converter.SCREEN_ANGLES_DEG[channel],
                    recipe["pitch"] * recipe["scale"],
                    recipe["page_w"],
                    recipe["page_h"],
                    page_region,
                )
                for channel in CHANNELS
            },
        }
    return {
        "available": True,
        "settings": {
            "theta_mode": "fixed",
            "bed_compensation": "disabled for isolated software geometry",
            "purpose": "decode final Wave X/Y points without motion mixing",
        },
        "programs": programs,
        "metrics": path_metrics,
        "regions": region_metrics,
    }


def _check(name, passed, value, threshold, comparator):
    return {
        "name": name,
        "passed": bool(passed),
        "value": value,
        "threshold": threshold,
        "comparator": comparator,
    }


def _region_wave_values(region_metrics, metric):
    values = []
    for region_name in REGIONS:
        region = (region_metrics or {}).get(region_name, {})
        for channel in CHANNELS:
            record = region.get("inks", {}).get(channel)
            if record is None:
                continue
            values.append(
                (
                    region_name,
                    channel,
                    record.get(metric),
                    record.get("rows", 0),
                )
            )
    return values


def _worst_region_value(region_metrics, metric, maximum=False):
    values = [
        record
        for record in _region_wave_values(region_metrics, metric)
        if record[2] is not None
    ]
    if not values:
        return None
    record = (
        max(values, key=lambda item: item[2])
        if maximum
        else min(values, key=lambda item: item[2])
    )
    return {
        "region": record[0],
        "channel": record[1],
        "value": float(record[2]),
    }


def _append_region_wave_checks(checks, region_metrics, prefix):
    expected = len(REGIONS) * len(CHANNELS)
    populated = [
        record
        for record in _region_wave_values(region_metrics, "rows")
        if record[3] >= THRESHOLDS["wave_region_rows_min"]
    ]
    checks.append(
        _check(
            f"{prefix}.regions_with_rows",
            len(populated) == expected,
            len(populated),
            expected,
            ">=",
        )
    )
    for metric, threshold_key, maximum, comparator in (
        (
            "median_span_mm",
            "wave_region_span_median_min_mm",
            False,
            ">=",
        ),
        (
            "median_amplitude_peak_to_peak_mm",
            "wave_region_amplitude_median_min_mm",
            False,
            ">=",
        ),
        (
            "median_cycles",
            "wave_region_cycles_median_min",
            False,
            ">=",
        ),
        (
            "median_flat_span_fraction",
            "wave_region_flat_span_fraction_max",
            True,
            "<=",
        ),
        (
            "median_interior_amplitude_ratio",
            "wave_region_interior_amplitude_ratio_min",
            False,
            ">=",
        ),
    ):
        worst = _worst_region_value(
            region_metrics,
            metric,
            maximum=maximum,
        )
        value = None if worst is None else worst["value"]
        checks.append(
            _check(
                f"{prefix}.{metric}_worst",
                value is not None
                and (
                    value >= THRESHOLDS[threshold_key]
                    if comparator == ">="
                    else value <= THRESHOLDS[threshold_key]
                ),
                value,
                THRESHOLDS[threshold_key],
                comparator,
            )
        )


def build_checks(regions, wave, depth, gcode=None):
    checks = []
    valid_regions = [
        record for record in regions.values() if "detail" in record
    ]
    if not valid_regions:
        return [
            _check(
                "detail.valid_crops",
                False,
                0,
                len(REGIONS),
                ">=",
            )
        ]
    checks.append(
        _check(
            "detail.structure_correlation_min",
            min(
                record["detail"]["structure_correlation"]
                for record in valid_regions
            )
            >= THRESHOLDS["detail_structure_correlation_min"],
            min(
                record["detail"]["structure_correlation"]
                for record in valid_regions
            ),
            THRESHOLDS["detail_structure_correlation_min"],
            ">=",
        )
    )
    checks.append(
        _check(
            "detail.edge_correlation_min",
            min(
                record["detail"]["edge_correlation"]
                for record in valid_regions
            )
            >= THRESHOLDS["detail_edge_correlation_min"],
            min(
                record["detail"]["edge_correlation"]
                for record in valid_regions
            ),
            THRESHOLDS["detail_edge_correlation_min"],
            ">=",
        )
    )
    checks.append(
        _check(
            "detail.luminance_mae_max",
            max(
                record["detail"]["luminance_mae"]
                for record in valid_regions
            )
            <= THRESHOLDS["detail_luminance_mae_max"],
            max(
                record["detail"]["luminance_mae"]
                for record in valid_regions
            ),
            THRESHOLDS["detail_luminance_mae_max"],
            "<=",
        )
    )

    color_limits = (
        ("rgb_mae", "color_rgb_mae_max"),
        ("lightness_mae", "color_lightness_mae_max"),
        ("chroma_mae", "color_chroma_mae_max"),
        ("hue_error_deg", "color_hue_error_deg_max"),
        ("delta_e76_mean", "color_delta_e76_mean_max"),
    )
    for metric, threshold_key in color_limits:
        worst = max(
            record["color"][metric] for record in valid_regions
        )
        checks.append(
            _check(
                f"color.{metric}_max",
                worst <= THRESHOLDS[threshold_key],
                worst,
                THRESHOLDS[threshold_key],
                "<=",
            )
        )

    for channel in CHANNELS:
        worst_bias = max(
            abs(record["ink"][channel]["coverage_bias"])
            for record in valid_regions
        )
        checks.append(
            _check(
                f"ink.{CHANNEL_LABELS[channel]}.coverage_bias_abs_max",
                worst_bias <= THRESHOLDS["ink_mean_absolute_bias_max"],
                worst_bias,
                THRESHOLDS["ink_mean_absolute_bias_max"],
                "<=",
            )
        )

    for channel in CHANNELS:
        record = wave["inks"][channel]
        label = CHANNEL_LABELS[channel]
        checks.extend(
            [
                _check(
                    f"wave.{label}.span_median_mm_min",
                    record["median_span_mm"]
                    >= THRESHOLDS["wave_span_min_mm"],
                    record["median_span_mm"],
                    THRESHOLDS["wave_span_min_mm"],
                    ">=",
                ),
                _check(
                    f"wave.{label}.amplitude_median_mm_min",
                    record["median_amplitude_peak_to_peak_mm"]
                    >= THRESHOLDS["wave_amplitude_min_mm"],
                    record["median_amplitude_peak_to_peak_mm"],
                    THRESHOLDS["wave_amplitude_min_mm"],
                    ">=",
                ),
                _check(
                    f"wave.{label}.cycles_median_min",
                    record["median_cycles"]
                    >= THRESHOLDS["wave_cycles_min"],
                    record["median_cycles"],
                    THRESHOLDS["wave_cycles_min"],
                    ">=",
                ),
                _check(
                    f"wave.{label}.flat_span_fraction_max",
                    record["median_flat_span_fraction"]
                    <= THRESHOLDS["wave_flat_span_fraction_max"],
                    record["median_flat_span_fraction"],
                    THRESHOLDS["wave_flat_span_fraction_max"],
                    "<=",
                ),
                _check(
                    f"wave.{label}.interior_amplitude_ratio_min",
                    record["median_interior_amplitude_ratio"]
                    >= THRESHOLDS[
                        "wave_interior_amplitude_ratio_min"
                    ],
                    record["median_interior_amplitude_ratio"],
                    THRESHOLDS[
                        "wave_interior_amplitude_ratio_min"
                    ],
                    ">=",
                ),
            ]
        )

    checks.append(
        _check(
            "wave.depth_intensity_material_geometry_change",
            depth["material_geometry_change"],
            depth["median_rms_delta_mm"],
            THRESHOLDS["depth_geometry_delta_min_mm"],
            ">=",
        )
    )

    _append_region_wave_checks(
        checks,
        wave.get("regions"),
        "wave",
    )

    if gcode is not None and gcode.get("available", True) is False:
        checks.append(
            _check(
                "gcode.available",
                False,
                False,
                True,
                "==",
            )
        )
    elif gcode is not None:
        for channel in CHANNELS:
            record = gcode["metrics"][channel]
            label = CHANNEL_LABELS[channel]
            checks.extend(
                [
                    _check(
                        f"gcode.{label}.rows_min",
                        record["rows"] > 0,
                        record["rows"],
                        1,
                        ">=",
                    ),
                    _check(
                        f"gcode.{label}.span_median_mm_min",
                        record["median_span_mm"]
                        >= THRESHOLDS["wave_span_min_mm"],
                        record["median_span_mm"],
                        THRESHOLDS["wave_span_min_mm"],
                        ">=",
                    ),
                    _check(
                        f"gcode.{label}.amplitude_median_mm_min",
                        record["median_amplitude_peak_to_peak_mm"]
                        >= THRESHOLDS["wave_amplitude_min_mm"],
                        record["median_amplitude_peak_to_peak_mm"],
                        THRESHOLDS["wave_amplitude_min_mm"],
                        ">=",
                    ),
                    _check(
                        f"gcode.{label}.cycles_median_min",
                        record["median_cycles"]
                        >= THRESHOLDS["wave_cycles_min"],
                        record["median_cycles"],
                        THRESHOLDS["wave_cycles_min"],
                        ">=",
                    ),
                    _check(
                        f"gcode.{label}.flat_span_fraction_max",
                        record["median_flat_span_fraction"]
                        <= THRESHOLDS["wave_flat_span_fraction_max"],
                        record["median_flat_span_fraction"],
                        THRESHOLDS["wave_flat_span_fraction_max"],
                        "<=",
                    ),
                    _check(
                        f"gcode.{label}.interior_amplitude_ratio_min",
                        record["median_interior_amplitude_ratio"]
                        >= THRESHOLDS[
                            "wave_interior_amplitude_ratio_min"
                        ],
                        record["median_interior_amplitude_ratio"],
                        THRESHOLDS[
                            "wave_interior_amplitude_ratio_min"
                        ],
                        ">=",
                    ),
                ]
            )
            has_header = bool(
                gcode.get("programs", {})
                .get(channel, {})
                .get("has_fixed_baseline_header")
            )
            checks.append(
                _check(
                    f"gcode.{label}.fixed_baseline_header",
                    has_header,
                    has_header,
                    True,
                    "==",
                )
            )
        _append_region_wave_checks(
            checks,
            gcode.get("regions"),
            "gcode",
        )
    return checks


def _region_overlay(source, rendered, regions, mapping, size):
    canvas = np.concatenate((source, rendered), axis=1)
    image = Image.fromarray((canvas * 255.0).astype(np.uint8))
    draw = ImageDraw.Draw(image)
    for name, region in regions.items():
        box = _pixel_region(mapping, region, size)
        if box is None:
            continue
        left, top, right, bottom = box
        draw.rectangle(
            (left, top, right, bottom),
            outline=(255, 40, 40),
            width=2,
        )
        draw.text((left + 3, top + 3), name, fill=(255, 40, 40))
        draw.rectangle(
            (left + size, top, right + size, bottom),
            outline=(255, 40, 40),
            width=2,
        )
    return image


def _write_artifacts(
    output_dir,
    source,
    rendered,
    coverage,
    mapping,
    size,
    report,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = {}
    composite_path = output_dir / "composite.png"
    Image.fromarray((rendered * 255.0).astype(np.uint8)).save(composite_path)
    paths["composite"] = str(composite_path)
    source_path = output_dir / "source-mapped.png"
    Image.fromarray((source * 255.0).astype(np.uint8)).save(source_path)
    paths["source_mapped"] = str(source_path)
    comparison_path = output_dir / "source-vs-composite.png"
    _region_overlay(
        source,
        rendered,
        REGIONS,
        mapping,
        size,
    ).save(comparison_path)
    paths["comparison"] = str(comparison_path)
    for channel in CHANNELS:
        path = output_dir / f"ink-{channel}.png"
        Image.fromarray(
            (coverage[channel] * 255.0).astype(np.uint8)
        ).save(path)
        paths[f"ink_{channel}"] = str(path)
    metrics_path = output_dir / "metrics.json"
    metrics_path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths["metrics"] = str(metrics_path)
    return paths


def evaluate(
    image_path,
    neutral_depth=1.0,
    high_depth=None,
    render_pixels=512,
    run_gcode=False,
    recipe_mode="live-failed",
    style=None,
    jobs=1,
):
    image_path = Path(image_path)
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")
    recipe, recipe_sources = load_recipe(image_path, recipe_mode)
    if style is not None:
        style = str(style).strip().lower()
        if style not in ("waves_fixed", "waves_fidelity"):
            raise ValueError(
                "style must be 'waves_fixed' or 'waves_fidelity'"
            )
        recipe = dict(recipe)
        recipe["style"] = style
    if high_depth is None:
        high_depth = float(recipe["wave_depth_intensity"])
    if abs(float(neutral_depth) - float(high_depth)) < 1e-9:
        raise ValueError("Neutral and high depth intensity must differ.")

    tones, geometry = prepare_tones(image_path, recipe)
    mapping = page_mapping(geometry, recipe)
    neutral_layers, neutral_errors = build_layers(
        tones,
        geometry,
        recipe,
        depth_intensity=neutral_depth,
        jobs=jobs,
    )
    high_layers, high_errors = build_layers(
        tones,
        geometry,
        recipe,
        depth_intensity=high_depth,
        jobs=jobs,
    )

    neutral_wave = wave_metrics(neutral_layers, recipe, mapping)["inks"]
    high_wave = wave_metrics(high_layers, recipe, mapping)
    depth = depth_geometry_comparison(neutral_wave, high_wave["inks"])
    depth["high_depth_intensity_pct"] = float(high_depth) * 100.0

    coverage = render_coverage(high_layers, recipe, render_pixels)
    source = source_canvas(image_path, mapping, render_pixels)
    rendered = composite_rgb(
        coverage,
        recipe.get("ink_transmittances"),
    )
    target_coverage = target_ink_canvases(
        tones,
        mapping,
        render_pixels,
    )
    coverage_fidelity = coverage_fidelity_metrics(
        coverage,
        target_coverage,
    )
    regions = region_metrics(
        source,
        rendered,
        coverage,
        target_coverage,
        mapping,
        render_pixels,
    )

    gcode = None
    if run_gcode:
        try:
            witness = generate_gcode_witness(high_layers, recipe, mapping)
            programs = witness.pop("programs")
            gcode = {
                **witness,
                "programs": {
                    channel: {
                        "sha256": hashlib.sha256(
                            text.encode("utf-8")
                        ).hexdigest(),
                        "lines": len(text.splitlines()),
                        "drawing_moves": text.count("\nG1 "),
                        "has_fixed_baseline_header": (
                            "Wave fixed baselines" in text
                        ),
                    }
                    for channel, text in programs.items()
                },
            }
        except Exception as exc:  # noqa: BLE001 - report as a red gate
            gcode = {
                "available": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
            }

    checks = build_checks(regions, high_wave, depth, gcode)
    checks.extend(_coverage_fidelity_checks(coverage_fidelity))
    checks.append(
        _check(
            "wave.pen_plus_edge_clearance_contract",
            recipe["row_clearance_mode"] == "pen-plus-edge",
            recipe["row_clearance_mode"],
            "pen-plus-edge",
            "==",
        )
    )
    failed = [check for check in checks if not check["passed"]]
    report = {
        "kind": "cmyk-wave-fidelity-oracle",
        "version": 1,
        "status": "PASS" if not failed else "FAIL",
        "source": {
            "path": str(image_path),
            "sha256": _sha256(image_path),
        "pixel_size": _image_size(image_path),
        },
        "recipe": {
            "page_mm": [recipe["page_w"], recipe["page_h"]],
            "mapping_mm": {
                "x": mapping.x_mm,
                "y": mapping.y_mm,
                "width": mapping.width_mm,
                "height": mapping.height_mm,
            },
            "style": recipe["style"],
            "profile": recipe["recipe_mode"],
            "pitch_mm_source": recipe["pitch"],
            "artwork_scale": recipe["scale"],
            "effective_pitch_mm": recipe["pitch"] * recipe["scale"],
            "wave_period_pitches": recipe["wave_period"],
            "wave_period_variation": recipe["wave_period_variation"],
            "high_depth_intensity": high_depth,
            "neutral_depth_intensity": neutral_depth,
            "pen_width_mm": recipe["pen_width"],
            "row_clearance_mode": recipe["row_clearance_mode"],
            "ink_transmittances": recipe.get("ink_transmittances"),
            "recipe_sources": recipe_sources,
        },
        "crop_regions": {
            name: {
                "source_normalized_xyxy": list(region),
                "page_mm_xyxy": [
                    round(value, 3)
                    for value in mapping.source_region_to_page(region)
                ],
            }
            for name, region in REGIONS.items()
        },
        "regions": regions,
        "wave": {
            "inks": high_wave["inks"],
            "regions": high_wave["regions"],
            "regions_measured_from": "production screen mark points",
        },
        "coverage_fidelity": coverage_fidelity,
        "screen_errors": {
            "neutral_depth_intensity": neutral_errors,
            "high_depth_intensity": high_errors,
        },
        "depth_comparison": depth,
        "gcode": gcode,
        "thresholds": dict(THRESHOLDS),
        "checks": checks,
        "failed_checks": failed,
        "physical_uncertainty": [
            "The composite models measured ink transmittances with nominal "
            "multiplicative coverage; it does not model felt-tip bleed, "
            "pressure, paper absorption, or ink layering time.",
            "G-code is generated in fixed-bed mode to isolate Wave geometry; "
            "it does not validate rotating-bed following error or physical "
            "registration.",
            "Crops and thresholds describe software fidelity only, not a "
            "physical print acceptance result.",
        ],
    }
    return report, {
        "source": source,
        "rendered": rendered,
        "coverage": coverage,
        "mapping": mapping,
        "size": render_pixels,
    }


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--image",
        default=str(DEFAULT_IMAGE),
        help="source PNG/JPG (default: owner's Golden Sunset image)",
    )
    parser.add_argument(
        "--neutral-depth-pct",
        type=float,
        default=100.0,
        help="neutral depth intensity for the geometry A/B (default 100)",
    )
    parser.add_argument(
        "--high-depth-pct",
        type=float,
        default=None,
        help="high intensity; defaults to the selected recipe",
    )
    parser.add_argument(
        "--recipe",
        choices=("live-failed", "fidelity-recommended", "saved-sidecar"),
        default="live-failed",
        help=(
            "recipe preset: live failed state (default), fidelity-recommended "
            "pitch, or saved sidecar"
        ),
    )
    parser.add_argument(
        "--style",
        choices=("waves_fixed", "waves_fidelity"),
        default=None,
        help="override the selected production Wave screen style",
    )
    parser.add_argument(
        "--render-pixels",
        type=int,
        default=512,
        help="comparison render width in pixels (default 512)",
    )
    parser.add_argument(
        "--gcode",
        action="store_true",
        help="also generate and decode fixed-bed G-code witness programs",
    )
    parser.add_argument(
        "--no-gcode",
        dest="gcode",
        action="store_false",
        help=argparse.SUPPRESS,
    )
    parser.set_defaults(gcode=False)
    parser.add_argument(
        "--jobs",
        type=int,
        default=4,
        help="parallel ink-screening processes (default 4)",
    )
    parser.add_argument(
        "--out-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="ignored artifact directory",
    )
    parser.add_argument(
        "--json-out",
        default=None,
        help="optional additional path for the JSON report",
    )
    parser.add_argument(
        "--no-artifacts",
        action="store_true",
        help="do not write PNG/metrics artifacts",
    )
    return parser.parse_args(argv)


def main(argv=None):
    args = _parse_args(argv)
    try:
        report, data = evaluate(
            args.image,
            neutral_depth=args.neutral_depth_pct / 100.0,
            high_depth=(
                args.high_depth_pct / 100.0
                if args.high_depth_pct is not None
                else None
            ),
            render_pixels=args.render_pixels,
            run_gcode=args.gcode,
            recipe_mode=args.recipe,
            style=args.style,
            jobs=args.jobs,
        )
        if not args.no_artifacts:
            report["artifacts"] = _write_artifacts(
                Path(args.out_dir),
                data["source"],
                data["rendered"],
                data["coverage"],
                data["mapping"],
                data["size"],
                report,
            )
        if args.json_out:
            output = Path(args.json_out)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(
                json.dumps(report, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report["status"] == "PASS" else 1
    except Exception as exc:  # noqa: BLE001 - CLI setup/failure boundary
        print(
            json.dumps(
                {
                    "kind": "cmyk-wave-fidelity-oracle",
                    "status": "ERROR",
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
